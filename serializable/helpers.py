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
from __future__ import print_function, division, absolute_import
from types import FunctionType, BuiltinFunctionType

import simplejson as json
from six import string_types

from .primtive_types import return_primitive


def _lookup_value(module_string, name, _cache={}):
    key = (module_string, name)
    if key in _cache:
        value = _cache[key]
    else:
        module_parts = module_string.split(".")
        attribute_list = module_parts[1:] + name.split(".")
        # traverse the chain of imports and nested classes to get to the
        # actual class value
        value = __import__(module_parts[0])
        for attribute_name in attribute_list:
            value = getattr(value, attribute_name)
        _cache[key] = value
    return value


def class_from_serializable_representation(class_repr):
    """
    Given the name of a module and a class it contains, imports that module
    and gets the class object from it.
    """
    return _lookup_value(class_repr["__module__"], class_repr["__name__"])

def class_to_serializable_representation(cls):
    """
    Given a class, return two strings:
        - fully qualified import path for its module
        - name of the class

    The class can be reconstructed from these two strings by calling
    class_from_serializable_representation.
    """
    return {"__module__": cls.__module__, "__name__": cls.__name__}

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
        raise ValueError(
            "Can't serialize %s : %s, must be globally defined function" % (
                fn, type(fn),))

    if hasattr(fn, "__closure__") and fn.__closure__ is not None:
        raise ValueError("No serializable representation for closure %s" % (fn,))

    return {"__module__": fn.__module__, "__name__": fn.__name__}

SERIALIZED_DICTIONARY_KEYS_FIELD = "__serialized_keys__"
SERIALIZED_DICTIONARY_KEYS_ELEMENT_PREFIX = (
    SERIALIZED_DICTIONARY_KEYS_FIELD + "element_")

def index_to_serialized_key_name(index):
    return "%s%d" % (SERIALIZED_DICTIONARY_KEYS_ELEMENT_PREFIX, index)

def parse_serialized_keys_index(name):
    """
    Given a field name such as __serialized_keys__element_10 returns the integer 10
    but returns None for other strings.
    """
    if name.startswith(SERIALIZED_DICTIONARY_KEYS_ELEMENT_PREFIX):
        try:
            return int(name[len(SERIALIZED_DICTIONARY_KEYS_ELEMENT_PREFIX):])
        except:
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
    for (k, v) in x.items():
        if not isinstance(k, string_types):
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

def dict_from_serializable_repr(x):
    """
    Reconstruct a dictionary by recursively reconstructing all its keys and
    values.

    This is the most hackish part since we rely on key names such as
    __name__, __class__, __module__ as metadata about how to reconstruct
    an object.

    TODO: It would be cleaner to always wrap each object in a layer of type
    metadata and then have an inner dictionary which represents the flattened
    result of to_dict() for user-defined objects.
    """
    if "__name__" in x:
        return _lookup_value(x.pop("__module__"), x.pop("__name__"))
    non_string_key_objects = [
        from_json(serialized_key)
        for serialized_key
        in x.pop(SERIALIZED_DICTIONARY_KEYS_FIELD, [])
    ]
    converted_dict = type(x)()
    for k, v in x.items():
        serialized_key_index = parse_serialized_keys_index(k)
        if serialized_key_index is not None:
            k = non_string_key_objects[serialized_key_index]

        converted_dict[k] = from_serializable_repr(v)
    if "__class__" in converted_dict:
        class_object = converted_dict.pop("__class__")
        if "__value__" in converted_dict:
            return class_object(x["__value__"])
        elif hasattr(class_object, "from_dict"):
            return class_object.from_dict(converted_dict)
        else:
            return class_object(**converted_dict)
    return converted_dict

def list_to_serializable_repr(x):
    return type(x)([to_serializable_repr(element) for element in x])

@return_primitive
def to_serializable_repr(x):
    """
    Convert an instance of Serializable or a primitive collection containing
    such instances into serializable types.
    """
    t = type(x)
    if isinstance(x, list):
        return list_to_serializable_repr(x)
    elif t is tuple:
        return {
            "__class__": class_to_serializable_representation(tuple),
            "__value__": list_to_serializable_repr(x)
        }
    elif isinstance(x, dict):
        return dict_to_serializable_repr(x)
    elif isinstance(x, (FunctionType, BuiltinFunctionType)):
        return function_to_serializable_representation(x)
    elif type(x) is type:
        return class_to_serializable_representation(x)

    # if value wasn't a primitive scalar or collection then it needs to
    # either implement to_dict (instances of Serializable) or _asdict
    # (named tuples)

    state_dictionary = None

    if hasattr(x, "to_dict"):
        state_dictionary = x.to_dict()
    elif hasattr(x, "_asdict"):
        state_dictionary = x._asdict()

    if state_dictionary is None:
        raise ValueError(
            "Cannot convert %s : %s to serializable representation" % (
                x, type(x)))
    state_dictionary = to_serializable_repr(state_dictionary)
    state_dictionary["__class__"] = class_to_serializable_representation(x.__class__)
    return state_dictionary


@return_primitive
def from_serializable_repr(x):
    t = type(x)
    if isinstance(x, list):
        return t([from_serializable_repr(element) for element in x])
    elif t is tuple:
        return tuple([from_serializable_repr(element) for element in x])
    elif isinstance(x, dict):
        return dict_from_serializable_repr(x)
    else:
        raise TypeError(
            "Cannot convert %s : %s from serializable representation to object" % (
                x, type(x)))

def to_json(x):
    """
    Returns JSON representation of a given Serializable instance or
    other primitive object.
    """
    return json.dumps(to_serializable_repr(x))

def from_json(json_string):
    return from_serializable_repr(json.loads(json_string))
