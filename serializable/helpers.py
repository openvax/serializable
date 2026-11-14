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

from __future__ import annotations

import inspect
import json
from enum import Enum
from functools import lru_cache
from types import BuiltinFunctionType, FunctionType
from typing import Any, Union

from .primitive_types import PRIMITIVE_TYPES


def init_arg_names(obj: Any) -> tuple[str, ...]:
    """
    Names of the positional arguments to the __init__ method of this
    object's class (excluding self).

    Keyword-only arguments are deliberately excluded, so a class can accept
    constructor options which aren't part of its serialized state.
    """
    # mypy doesn't consider classes Hashable
    return _class_init_arg_names(type(obj))  # type: ignore[arg-type]


# Cached per class since this is called on every to_dict/__eq__/__hash__ of
# a Serializable which doesn't override to_dict. Assumes a class's __init__
# isn't replaced after its first instance has been serialized.
@lru_cache(maxsize=1024)
def _class_init_arg_names(cls):
    # doing something wildly hacky by pulling out the arguments to
    # __init__ and hoping that they match fields defined on the object
    try:
        # look through decorators which used functools.wraps
        init_code = inspect.unwrap(cls.__init__).__code__
    except AttributeError as exc:
        # if object is a namedtuple then we can return its fields
        # as the required initial args
        if hasattr(cls, "_fields"):
            return cls._fields
        # a class which defines neither __init__ nor __new__ takes no args
        if cls.__init__ is object.__init__ and cls.__new__ is object.__new__:
            return ()
        raise ValueError(f"Cannot determine args to {cls.__qualname__}.__init__") from exc
    # drop self argument
    return init_code.co_varnames[1 : init_code.co_argcount]


def simple_object_to_dict(self: object) -> dict[str, Any]:
    """
    Map each positional __init__ argument name of an object's class to the
    attribute of the same name. This is Serializable's default to_dict.

    Raises AttributeError if the object has no attribute for an argument, and
    ValueError if its class's __init__ arguments can't be determined.
    """
    return {name: getattr(self, name) for name in init_arg_names(self)}


_MODULE_LOOKUP_CACHE: dict = {}


def _lookup_value(module_string, name):
    key = (module_string, name)
    if key in _MODULE_LOOKUP_CACHE:
        return _MODULE_LOOKUP_CACHE[key]

    module_parts = module_string.split(".")
    value = None
    n_imported = 0
    for i in range(1, len(module_parts) + 1):
        try:
            # try importing successively longer chains of
            # sub-modules but break when we hit something that's
            # not a module but actually data
            qualified_name = ".".join(module_parts[:i])
            value = __import__(qualified_name, fromlist=module_parts[: i - 1])
        except ImportError:
            break
        n_imported = i

    if value is None:
        raise ImportError(module_parts[0])
    # once we've imported as much as we can, continue with getattr
    # lookups
    for attribute_name in module_parts[n_imported:] + name.split("."):
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
    """
    Name of the module where a class or function is defined (its __module__).
    """
    module_name = obj.__module__
    return module_name


def _importable_representation(obj):
    """
    Module and qualified name from which a class or function can be looked up
    again. Raises ValueError for objects which can't be reached that way.
    """
    module_name = get_module_name(obj)
    qualified_name = obj.__qualname__
    if module_name is None or "<" in qualified_name:
        # e.g. "f.<locals>.C", "<lambda>" or a builtin method such as [].append
        raise ValueError(
            f"Can't serialize {obj}: only classes and functions which can be looked up by "
            f"name in a module are supported (got {module_name}.{qualified_name})"
        )
    return {"__module__": module_name, "__name__": qualified_name}


def class_to_serializable_representation(cls):
    """
    Given a class, return two strings:
        - fully qualified import path for its module
        - qualified name of the class (e.g. "Outer.Inner" for a nested class)

    The class can be reconstructed from these two strings by calling
    class_from_serializable_representation.

    Raises ValueError for a class defined inside a function, which can't be
    looked up by name.
    """
    return _importable_representation(cls)


def function_from_serializable_representation(fn_repr):
    """
    Given the name of a module and a function it contains, imports that module
    and gets the class object from it.
    """
    return _lookup_value(fn_repr["__module__"], fn_repr["__name__"])


def function_to_serializable_representation(fn):
    """
    Converts a Python function into a serializable representation. Does not
    currently work for methods, lambdas, functions defined inside another
    function or functions with closure data.
    """
    if type(fn) not in (FunctionType, BuiltinFunctionType):
        raise ValueError(f"Can't serialize {fn} : {type(fn)}, must be globally defined function")

    if hasattr(fn, "__closure__") and fn.__closure__ is not None:
        raise ValueError(f"No serializable representation for closure {fn}")

    return _importable_representation(fn)


# the only kinds of object which are written as a module and a name
_LOOKED_UP_BY_NAME = (type, FunctionType, BuiltinFunctionType)

# the builtin classes whose instances are written as
# {"__class__": ..., "__value__": [...]}, as are members of Enum classes
_COLLECTIONS_BUILT_FROM_VALUE = (set, frozenset, tuple)

SERIALIZED_DICTIONARY_KEYS_FIELD = "__serialized_keys__"
SERIALIZED_DICTIONARY_KEYS_ELEMENT_PREFIX = SERIALIZED_DICTIONARY_KEYS_FIELD + "element_"


def index_to_serialized_key_name(index):
    """
    Placeholder key, such as __serialized_keys__element_3, that stands for the
    non-string dictionary key at this index of the serialized key list.
    Inverse of parse_serialized_keys_index.
    """
    return f"{SERIALIZED_DICTIONARY_KEYS_ELEMENT_PREFIX}{index:d}"


def parse_serialized_keys_index(name):
    """
    Given a field name such as __serialized_keys__element_10 returns the integer 10
    but returns None for other strings.
    """
    if name.startswith(SERIALIZED_DICTIONARY_KEYS_ELEMENT_PREFIX):
        index = name[len(SERIALIZED_DICTIONARY_KEYS_ELEMENT_PREFIX) :]
        if index.isascii() and index.isdigit():
            return int(index)
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
    # string keys of x which look like our own placeholders
    reserved_string_keys = []
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
        elif k == SERIALIZED_DICTIONARY_KEYS_FIELD or parse_serialized_keys_index(k) is not None:
            reserved_string_keys.append(k)
        elif k == "__class__" and isinstance(v, _LOOKED_UP_BY_NAME):
            # would be read back as an instance of v, rather than as this dictionary
            raise ValueError(
                f"Can't serialize a dictionary whose reserved key '__class__' holds {v}"
            )
        result[k] = to_serializable_repr(v)
    if len(serialized_key_list) > 0:
        if reserved_string_keys:
            # the placeholders would overwrite, or be mistaken for, these keys
            raise ValueError(
                f"Can't serialize a dictionary which has both non-string keys and the "
                f"reserved string keys {reserved_string_keys}"
            )
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
    name, module_name = x.get("__name__"), x.get("__module__")
    if len(x) == 2 and isinstance(name, str) and isinstance(module_name, str):
        value = _lookup_value(module_name, name)
        if not isinstance(value, _LOOKED_UP_BY_NAME):
            raise ValueError(
                f"Expected {module_name}.{name} to be a class or function but got {type(value)}"
            )
        return value

    # anything other than a list of JSON strings is the caller's own data
    serialized_keys = x.get(SERIALIZED_DICTIONARY_KEYS_FIELD)
    if (
        isinstance(serialized_keys, list)
        and serialized_keys
        and all(isinstance(serialized_key, str) for serialized_key in serialized_keys)
    ):
        non_string_key_objects = [from_json(serialized_key) for serialized_key in serialized_keys]
        converted_dict = type(x)()
        for k, v in x.items():
            if k == SERIALIZED_DICTIONARY_KEYS_FIELD:
                continue
            serialized_key_index = parse_serialized_keys_index(k)
            if serialized_key_index is not None and serialized_key_index < len(
                non_string_key_objects
            ):
                k = non_string_key_objects[serialized_key_index]
            converted_dict[k] = v
        x = converted_dict

    class_object = x.get("__class__")
    if not isinstance(class_object, type):
        if callable(class_object):
            # only classes are ever written here, so a function is either a
            # mistake or an attempt to have us call it
            raise ValueError(f"Expected __class__ to be a class but got {class_object}")
        # a dictionary which isn't an object, even if it has a "__class__" key
        return x
    del x["__class__"]
    if "__value__" in x:
        if class_object not in _COLLECTIONS_BUILT_FROM_VALUE and not issubclass(class_object, Enum):
            raise ValueError(
                f"Can't construct {class_object.__qualname__} from __value__, "
                f"only sets, frozensets, tuples and enums are represented that way"
            )
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
    """
    Convert each element of a list (or other iterable) with to_serializable_repr,
    returning a new list.
    """
    return [to_serializable_repr(element) for element in x]


def to_dict(obj: Any) -> dict[str, Any]:
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


def to_serializable_repr(x: Any) -> Any:
    """
    Convert an instance of Serializable or a primitive collection containing
    such instances into serializable types.
    """
    if isinstance(x, PRIMITIVE_TYPES):
        return x
    t = type(x)
    if isinstance(x, list):
        return list_to_serializable_repr(x)
    if t in _COLLECTIONS_BUILT_FROM_VALUE:
        return {
            "__class__": class_to_serializable_representation(t),
            "__value__": list_to_serializable_repr(x),
        }
    if isinstance(x, dict):
        return dict_to_serializable_repr(x)
    if isinstance(x, (FunctionType, BuiltinFunctionType)):
        return function_to_serializable_representation(x)
    if isinstance(x, type):
        return class_to_serializable_representation(x)
    if isinstance(x, Enum) and not hasattr(x, "to_dict"):
        # members are looked up by value, they can't be constructed from fields
        return {
            "__class__": class_to_serializable_representation(t),
            "__value__": to_serializable_repr(x.value),
        }
    state_dictionary = to_serializable_repr(to_dict(x))
    state_dictionary["__class__"] = class_to_serializable_representation(x.__class__)
    return state_dictionary


def from_serializable_repr(x: Any) -> Any:
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


def to_json(x: Any) -> str:
    """
    Returns JSON representation of a given Serializable instance or
    other primitive object.

    Raises ValueError for NaN or infinite floats, which have no standard
    JSON representation.
    """
    return json.dumps(to_serializable_repr(x), allow_nan=False)


def from_json(json_string: Union[str, bytes]) -> Any:
    """
    Inverse of to_json. Objects are reconstructed bottom-up while parsing,
    equivalent to (but faster than) from_serializable_repr(json.loads(...)).

    Accepts the NaN and Infinity literals which older versions of
    serializable wrote.
    """
    return json.loads(json_string, object_hook=_from_reconstructed_dict)
