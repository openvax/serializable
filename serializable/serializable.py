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


from typing import ClassVar

from .helpers import from_json, simple_object_to_dict, to_json


class Serializable:
    """
    Base class for user-defined objects which provides default
    methods such as to_json, from_json, __reduce__, and from_dict

    Relies on the keys of to_dict() matching the arguments to __init__.
    """

    def __str__(self):
        fields = ", ".join(f"{k}={v}" for (k, v) in self.to_dict().items())
        return f"{self.__class__.__name__}({fields})"

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return self.__class__ is other.__class__ and self.to_dict() == other.to_dict()

    def to_dict(self):
        """
        Returns a dictionary which can be used to reconstruct an instance
        of a derived class (typically by matching args to __init__). The values
        of the returned dictionary must be primitive atomic types
        (bool, string, int, float), primitive collections
        (int, list, tuple, set) or instances of Serializable.

        The default implementation is to assume all the positional arguments
        to __init__ have fields of the same name on a serializable object.
        Keyword-only arguments are excluded, so they can be used for
        constructor options which aren't part of the serialized state.
        """
        return simple_object_to_dict(self)

    def __hash__(self):
        return hash(tuple(sorted(self.to_dict().items())))

    @classmethod
    def _reconstruct_nested_objects(cls, state_dict):
        """
        Nested serializable objects will be represented as dictionaries so we
        allow manual reconstruction of those objects in this method.

        By default just returns the state dictionary unmodified.
        """
        return state_dict

    # dictionary mapping old keywords to either new names or
    # None if the keyword has been removed from a class
    _SERIALIZABLE_KEYWORD_ALIASES: ClassVar[dict] = {}

    @classmethod
    def _update_kwargs(cls, kwargs):
        """
        Rename any old keyword arguments to preserve backwards compatibility
        """
        # check every class in the inheritance chain for its own
        # definition of _SERIALIZABLE_KEYWORD_ALIASES
        for klass in cls.mro():
            keyword_rename_dict = getattr(klass, "_SERIALIZABLE_KEYWORD_ALIASES", {})
            for old_name, new_name in keyword_rename_dict.items():
                if old_name in kwargs:
                    old_value = kwargs.pop(old_name)
                    if new_name and new_name not in kwargs:
                        kwargs[new_name] = old_value
        return kwargs

    @classmethod
    def from_dict(cls, state_dict):
        """
        Given a dictionary of flattened fields (result of calling to_dict()),
        returns an instance. Does not modify `state_dict`.
        """
        state_dict = cls._reconstruct_nested_objects(dict(state_dict))
        return cls(**cls._update_kwargs(state_dict))

    def to_json(self):
        """
        Returns a string containing a JSON representation of this object.
        """
        return to_json(self)

    @classmethod
    def from_json(cls, json_string):
        """
        Reconstruct an instance from a JSON string.
        """
        return from_json(json_string)

    def write_json_file(self, path):
        """
        Serialize this object to JSON and write it to the text file at `path`.
        """
        with open(path, "w") as f:
            f.write(self.to_json())

    @classmethod
    def read_json_file(cls, path):
        """
        Construct an instance of this class from the JSON file at `path`.
        """
        with open(path) as f:
            json_string = f.read()
        return cls.from_json(json_string)

    def __reduce__(self):
        """
        Overriding this method directs the default pickler to reconstruct
        this object using our from_dict method, so pickles survive the same
        changes to a class (e.g. renamed keywords) as JSON does. Values in
        to_dict() are pickled natively.

        Pickles written before serializable 1.2.0 call from_serializable_repr
        instead, which remains supported.
        """
        return (type(self).from_dict, (self.to_dict(),))
