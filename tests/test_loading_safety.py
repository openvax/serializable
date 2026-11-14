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
What from_json is willing to construct, values added in 1.6.0 (enum members
and frozensets), and dictionaries whose keys look like the format's own.
"""

import enum
import json
import pickle

import pytest

from serializable import (
    Serializable,
    from_json,
    from_serializable_repr,
    to_json,
    to_serializable_repr,
)

from .common import eq_


class Color(enum.Enum):
    RED = 1
    GREEN = "green"
    PAIR = (1, 2)


class Permission(enum.Flag):
    READ = 1
    WRITE = 2


class Level(enum.IntEnum):
    LOW = 1


class Painted(Serializable):
    def __init__(self, color, tags):
        self.color = color
        self.tags = tags


class Outer:
    class Inner:
        pass


calls = []


def record_call(*args, **kwargs):
    calls.append((args, kwargs))


def _repr_of(obj):
    return {"__module__": obj.__module__, "__name__": obj.__qualname__}


@pytest.mark.parametrize(
    "payload",
    [
        {"__class__": _repr_of(record_call), "__value__": "x"},
        {"__class__": _repr_of(record_call)},
        {"__class__": _repr_of(record_call), "x": 1},
    ],
)
def test_function_as_class_is_not_called(payload):
    calls.clear()
    with pytest.raises(ValueError, match="to be a class"):
        from_json(json.dumps(payload))
    with pytest.raises(ValueError, match="to be a class"):
        from_serializable_repr(payload)
    eq_(calls, [])


def test_value_only_constructs_collections_and_enums():
    payload = {"__class__": _repr_of(Painted), "__value__": "x"}
    with pytest.raises(ValueError, match="__value__"):
        from_json(json.dumps(payload))
    payload = {"__class__": {"__module__": "builtins", "__name__": "bytearray"}, "__value__": 10}
    with pytest.raises(ValueError, match="__value__"):
        from_serializable_repr(payload)


@pytest.mark.parametrize("member", [Color.RED, Color.GREEN, Color.PAIR])
def test_enum_member_roundtrip(member):
    assert from_json(to_json(member)) is member
    assert from_serializable_repr(to_serializable_repr(member)) is member


def test_enum_flag_roundtrip():
    combined = Permission.READ | Permission.WRITE
    eq_(from_json(to_json(combined)), combined)


def test_int_enum_is_still_written_as_its_value():
    eq_(to_json(Level.LOW), "1")


def test_enum_inside_object_and_as_dict_key():
    obj = Painted(Color.RED, frozenset(["a", "b"]))
    eq_(obj, from_json(obj.to_json()))
    eq_(obj, pickle.loads(pickle.dumps(obj)))
    d = {Color.GREEN: [Color.PAIR]}
    eq_(d, from_json(to_json(d)))


def test_frozenset_roundtrip():
    value = {"a": frozenset([1, 2]), frozenset(["k"]): 3}
    restored = from_json(to_json(value))
    eq_(value, restored)
    assert type(restored["a"]) is frozenset


@pytest.mark.parametrize(
    "value",
    [
        {"__name__": "bob"},
        {"__class__": "bob"},
        {"__class__": None, "__name__": 1},
        {"nested": [{"__name__": "bob", "age": 3}]},
        {"__serialized_keys__element_0": "b"},
        {"__serialized_keys__": []},
        {"__serialized_keys__": [1]},
        {"__serialized_keys__": "abc"},
        {"__name__": "path", "__module__": "os", "extra": 1},
        {1: 2, "__serialized_keys__notes": 3},
    ],
)
def test_plain_dicts_with_format_like_keys_roundtrip(value):
    eq_(value, from_json(to_json(value)))
    eq_(value, from_serializable_repr(to_serializable_repr(value)))


def test_placeholder_key_collision_is_rejected_when_writing():
    with pytest.raises(ValueError, match="reserved string keys"):
        to_json({1: "a", "__serialized_keys__element_0": "b"})
    with pytest.raises(ValueError, match="reserved string keys"):
        to_json({1: "a", "__serialized_keys__": []})


def test_converting_a_representation_again_leaves_it_unchanged():
    value = {(1, 2): Painted(Color.RED, {3}), "cls": Painted}
    first = to_serializable_repr(value)
    eq_(first, to_serializable_repr(first))
    eq_(value, from_serializable_repr(to_serializable_repr(first)))


def test_module_path_which_continues_into_a_class():
    # as written by hand or by other tools: the class is part of the "module"
    class_repr = {"__module__": f"{__name__}.Outer", "__name__": "Inner"}
    assert from_serializable_repr(class_repr) is Outer.Inner
    assert from_json(json.dumps(class_repr)) is Outer.Inner


def test_dict_with_class_under_reserved_key_is_rejected_when_writing():
    for value in (Painted, len, record_call):
        with pytest.raises(ValueError, match="reserved key"):
            to_json({"__class__": value})


def test_value_does_not_construct_subclasses_of_collections():
    payload = {"__class__": {"__module__": "os", "__name__": "stat_result"}, "__value__": []}
    with pytest.raises(ValueError, match="__value__"):
        from_serializable_repr(payload)


def test_name_must_resolve_to_a_class_or_function():
    for name in ("environ", "path"):
        payload = {"__module__": "os", "__name__": name}
        with pytest.raises(ValueError, match="class or function"):
            from_json(json.dumps(payload))


def test_malformed_placeholder_indices_are_left_as_string_keys():
    payload = {
        "__serialized_keys__": ["1", "2"],
        "__serialized_keys__element_0": "a",
        "__serialized_keys__element_-1": "b",
        "__serialized_keys__element_5": "c",
    }
    expected = {1: "a", "__serialized_keys__element_-1": "b", "__serialized_keys__element_5": "c"}
    eq_(from_json(json.dumps(payload)), expected)
    eq_(from_serializable_repr(payload), expected)
