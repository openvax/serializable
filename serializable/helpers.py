# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Helper functions for deconstructing classes, functions, and user-defined
objects into serializable types.
"""

from functools import lru_cache
from types import BuiltinFunctionType, FunctionType

import simplejson as json

from .primitive_types import PRIMITIVE_TYPES


def init_arg_names(obj):
    """
    Names of the positional arguments to the __init__ method of this
    object's class (excluding self).

    Keyword-only arguments are deliberately excluded, so a class can accept
    constructor options which aren't part of its serialized state.
    """
    return _class_init_arg_names(type(obj))


# Cached per class since this is called on every to_dict/__eq__/__hash__ of
# a Serializable which doesn't override to_dict. Assumes a class's __init__
# isn't replaced after its first instance has been serialized.
@lru_cache(maxsize=1024)
def _class_init_arg_names(cls):
    # doing something wildly hacky by pulling out the arguments to
    # __init__ and hoping that they match fields defined on the object
    try:
        init_code = cls.__init__.__code__
    except AttributeError as exc:
        # if object is a namedtuple then we can return its fields
        # as the required initial args
        if hasattr(cls, "_fields"):
            return cls._fields
        raise ValueError(f"Cannot determine args to {cls.__qualname__}.__init__") from exc
    # drop self argument
    return init_code.co_varnames[1 : init_code.co_argcount]


def simple_object_to_dict(self):
    return {name: getattr(self, name) for name in init_arg_names(self)}


_MODULE_LOOKUP_CACHE: dict = {}


def _lookup_value(module_string, name):
    key = (module_string, name)
    if key in _MODULE_LOOKUP_CACHE:
        return _MODULE_LOOKUP_CACHE[key]

    module_parts = module_string.split(".")
    value = None
    i = 0
    for i in range(1, len(module_parts) + 1):
        try:
            # try importing successively longer chains of
            # sub-modules but break when we hit something that's
            # not a module but actually data
            qualified_name = ".".join(module_parts[:i])
            value = __import__(qualified_name, fromlist=module_parts[: i - 1])
        except ImportError:
            break

    if value is None:
        raise ImportError(module_parts[0])
    # once we've imported as much as we can, continue with getattr
    # lookups
    for attribute_name in module_parts[i:] + name.split("."):
        value = getattr(value, attribute_name)
    _MODULE_LOOKUP_CACHE[key] = value
    return value


def class_from_serializable_representation(class_repr):
    """
    Given the name of a module and a class it contains, imports that module
    and gets the class object from it.
    """
    return _lookup_value(class_repr["__module__"], class_repr["__name__"])


def get_module_name(obj):
    module_name = obj.__module__
    return module_name


def class_to_serializable_representation(cls):
    """
    Given a class, return two strings:
        - fully qualified import path for its module
        - name of the class

    The class can be reconstructed from these two strings by calling
    class_from_serializable_representation.
    """
    return {"__module__": get_module_name(cls), "__name__": cls.__name__}


def function_from_serializable_representation(fn_repr):
    """
    Given the name of a module and a function it contains, imports that module
    and gets the class object from it.
    """
    return _lookup_value(fn_repr["__module__"], fn_repr["__name__"])


def function_to_serializable_representation(fn):
    """
    Converts a Python function into a serializable representation. Does not
    currently work for methods or functions with closure data.
    """
    if type(fn) not in (FunctionType, BuiltinFunctionType):
        raise ValueError(f"Can't serialize {fn} : {type(fn)}, must be globally defined function")

    if hasattr(fn, "__closure__") and fn.__closure__ is not None:
        raise ValueError(f"No serializable representation for closure {fn}")

    return {"__module__": get_module_name(fn), "__name__": fn.__name__}


SERIALIZED_DICTIONARY_KEYS_FIELD = "__serialized_keys__"
SERIALIZED_DICTIONARY_KEYS_ELEMENT_PREFIX = SERIALIZED_DICTIONARY_KEYS_FIELD + "element_"


def index_to_serialized_key_name(index):
    return f"{SERIALIZED_DICTIONARY_KEYS_ELEMENT_PREFIX}{index:d}"


def parse_serialized_keys_index(name):
    """
    Given a field name such as __serialized_keys__element_10 returns the integer 10
    but returns None for other strings.
    """
    if name.startswith(SERIALIZED_DICTIONARY_KEYS_ELEMENT_PREFIX):
        try:
            return int(name[len(SERIALIZED_DICTIONARY_KEYS_ELEMENT_PREFIX) :])
        except ValueError:
            pass
    return None


def dict_to_serializable_repr(x):
    """
    Recursively convert values of dictionary to serializable representations.
    Convert non-string keys to JSON representations and replace them in the
    dictionary with indices of unique JSON strings (e.g. __1, __2, etc..).
    """
    # list of JSON representations of hashable objects which were
    # used as keys in this dictionary
    serialized_key_list = []
    serialized_keys_to_names = {}
    # use the class of x rather just dict since we might want to convert
    # derived classes such as OrderedDict
    result = type(x)()
    for k, v in x.items():
        if not isinstance(k, str):
            # JSON does not support using complex types such as tuples
            # or user-defined objects with implementations of __hash__ as
            # keys in a dictionary so we must keep the serialized
            # representations of such values in a list and refer to indices
            # in that list
            serialized_key_repr = to_json(k)
            if serialized_key_repr in serialized_keys_to_names:
                k = serialized_keys_to_names[serialized_key_repr]
            else:
                k = index_to_serialized_key_name(len(serialized_key_list))
                serialized_keys_to_names[serialized_key_repr] = k
                serialized_key_list.append(serialized_key_repr)
        result[k] = to_serializable_repr(v)
    if len(serialized_key_list) > 0:
        # only include this list of serialized keys if we had any non-string
        # keys
        result[SERIALIZED_DICTIONARY_KEYS_FIELD] = serialized_key_list
    return result


def _from_reconstructed_dict(x):
    """
    Given a dictionary from a serializable representation whose values have
    already been reconstructed, return the object it represents: a class or
    function, an instance of a user-defined class, or a dictionary (restoring
    any non-string keys). May modify `x`.

    This is the most hackish part since we rely on key names such as
    __name__, __class__, __module__ as metadata about how to reconstruct
    an object.

    TODO:
        It would be cleaner to always wrap each object in a layer of type
        metadata and then have an inner dictionary which represents the
        flattened result of to_dict() for user-defined objects.
    """
    if "__name__" in x:
        return _lookup_value(x["__module__"], x["__name__"])

    serialized_keys = x.pop(SERIALIZED_DICTIONARY_KEYS_FIELD, None)
    if serialized_keys:
        non_string_key_objects = [from_json(serialized_key) for serialized_key in serialized_keys]
        converted_dict = type(x)()
        for k, v in x.items():
            serialized_key_index = parse_serialized_keys_index(k)
            if serialized_key_index is not None:
                k = non_string_key_objects[serialized_key_index]
            converted_dict[k] = v
        x = converted_dict

    if "__class__" not in x:
        return x
    class_object = x.pop("__class__")
    if "__value__" in x:
        return class_object(x["__value__"])
    if hasattr(class_object, "from_dict"):
        return class_object.from_dict(x)
    return class_object(**x)


def from_serializable_dict(x):
    """
    Reconstruct a dictionary, or the object it represents, by recursively
    reconstructing all its keys and values. Does not modify `x`.
    """
    converted_dict = type(x)()
    for k, v in x.items():
        converted_dict[k] = from_serializable_repr(v)
    return _from_reconstructed_dict(converted_dict)


def list_to_serializable_repr(x):
    return [to_serializable_repr(element) for element in x]


def to_dict(obj):
    """
    If value isn't a primitive scalar or collection then it needs to
    either implement to_dict (instances of Serializable) or have member
    data matching each required arg of __init__.
    """
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    try:
        return simple_object_to_dict(obj)
    except Exception as exc:
        raise ValueError(f"Cannot convert {obj} : {type(obj)} to dictionary") from exc


def to_serializable_repr(x):
    """
    Convert an instance of Serializable or a primitive collection containing
    such instances into serializable types.
    """
    if isinstance(x, PRIMITIVE_TYPES):
        return x
    t = type(x)
    if isinstance(x, list):
        return list_to_serializable_repr(x)
    if t in (set, tuple):
        return {
            "__class__": class_to_serializable_representation(t),
            "__value__": list_to_serializable_repr(x),
        }
    if isinstance(x, dict):
        return dict_to_serializable_repr(x)
    if isinstance(x, (FunctionType, BuiltinFunctionType)):
        return function_to_serializable_representation(x)
    if type(x) is type:
        return class_to_serializable_representation(x)
    state_dictionary = to_serializable_repr(to_dict(x))
    state_dictionary["__class__"] = class_to_serializable_representation(x.__class__)
    return state_dictionary


def from_serializable_repr(x):
    """
    Inverse of to_serializable_repr. Does not modify `x`.
    """
    if isinstance(x, PRIMITIVE_TYPES):
        return x
    t = type(x)
    if isinstance(x, list):
        return t([from_serializable_repr(element) for element in x])
    if isinstance(x, dict):
        return from_serializable_dict(x)
    raise TypeError(f"Cannot convert {x} : {type(x)} from serializable representation to object")


def to_json(x):
    """
    Returns JSON representation of a given Serializable instance or
    other primitive object.
    """
    return json.dumps(to_serializable_repr(x))


def from_json(json_string):
    """
    Inverse of to_json. Objects are reconstructed bottom-up while parsing,
    equivalent to (but faster than) from_serializable_repr(json.loads(...)).
    """
    return json.loads(json_string, object_hook=_from_reconstructed_dict)
