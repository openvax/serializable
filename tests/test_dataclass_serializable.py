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

from __future__ import annotations

import pickle
from dataclasses import dataclass, field
from typing import ClassVar

import pytest

from serializable import DataclassSerializable, Serializable, from_json, to_json

from .common import eq_


@dataclass
class Point(DataclassSerializable):
    x: float
    y: float


@dataclass
class Person(DataclassSerializable):
    name: str
    age: int
    tags: list[str] = field(default_factory=list)


class LegacyTag(Serializable):
    def __init__(self, name):
        self.name = name


@dataclass
class Tagged(DataclassSerializable):
    label: str
    tag: LegacyTag = None


@dataclass
class Inner(DataclassSerializable):
    n: int


@dataclass
class Outer(DataclassSerializable):
    name: str
    inner: Inner


def test_to_dict_returns_field_values():
    p = Point(1.0, 2.0)
    eq_(p.to_dict(), {"x": 1.0, "y": 2.0})


def test_from_dict_reconstructs_instance():
    reconstructed = Point.from_dict({"x": 3.0, "y": 4.0})
    eq_(reconstructed, Point(3.0, 4.0))


def test_json_roundtrip_simple():
    p = Point(1.0, 2.0)
    eq_(Point.from_json(p.to_json()), p)


def test_json_roundtrip_with_collection_field():
    person = Person(name="Ada", age=36, tags=["mathematician", "engineer"])
    eq_(Person.from_json(person.to_json()), person)


def test_module_level_to_json_accepts_dataclass_serializable():
    p = Point(1.0, 2.0)
    # Calling the module-level helpers directly should still work since
    # to_serializable_repr dispatches on obj.to_dict().
    eq_(from_json(to_json(p)), p)


def test_pickle_roundtrip():
    p = Point(1.0, 2.0)
    eq_(pickle.loads(pickle.dumps(p)), p)


def test_dataclass_eq_and_repr_not_overridden_by_mixin():
    # @dataclass generates __eq__ and __repr__ — the mixin must not shadow them.
    a = Point(1.0, 2.0)
    b = Point(1.0, 2.0)
    c = Point(1.0, 3.0)
    assert a == b
    assert a != c
    assert repr(a) == "Point(x=1.0, y=2.0)"


def test_frozen_dataclass_is_hashable():
    @dataclass(frozen=True)
    class FrozenPoint(DataclassSerializable):
        x: float
        y: float

    p1 = FrozenPoint(1.0, 2.0)
    p2 = FrozenPoint(1.0, 2.0)
    # Equal, hashable, and usable as a set member.
    assert p1 == p2
    assert hash(p1) == hash(p2)
    assert {p1, p2} == {p1}


def test_keyword_aliases_rename():
    @dataclass
    class Renamed(DataclassSerializable):
        new_name: str
        _SERIALIZABLE_KEYWORD_ALIASES: ClassVar[dict[str, str | None]] = {"old_name": "new_name"}

    # Old wire format still loads.
    obj = Renamed.from_dict({"old_name": "hello"})
    eq_(obj, Renamed(new_name="hello"))


def test_keyword_aliases_drop():
    @dataclass
    class Dropped(DataclassSerializable):
        kept: int
        _SERIALIZABLE_KEYWORD_ALIASES: ClassVar[dict[str, str | None]] = {"removed": None}

    # Old wire format with an extra field that has since been dropped.
    obj = Dropped.from_dict({"kept": 5, "removed": "ignored"})
    eq_(obj, Dropped(kept=5))


def test_from_dict_rejects_unknown_field_without_alias():
    with pytest.raises(TypeError):
        Point.from_dict({"x": 1.0, "y": 2.0, "z": 3.0})


def test_interop_with_legacy_serializable():
    # A legacy Serializable instance referenced from a DataclassSerializable
    # field should round-trip through the shared wire format.
    t = Tagged(label="x", tag=LegacyTag("demo"))
    restored = Tagged.from_json(t.to_json())
    eq_(restored.label, "x")
    eq_(restored.tag.name, "demo")


def test_nested_dataclass_serializable_roundtrip():
    o = Outer(name="parent", inner=Inner(n=7))
    eq_(Outer.from_json(o.to_json()), o)
