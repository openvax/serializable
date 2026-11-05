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


from dataclasses import dataclass
from typing import ClassVar

from serializable import DataclassSerializable, Serializable
from serializable.keyword_aliases import apply_keyword_aliases

from .common import eq_


class TestClassWithKeywordAliases(Serializable):
    _SERIALIZABLE_KEYWORD_ALIASES = {"old_x": "x", "old_gone": None}

    def __init__(self, x):
        self.x = x


class DerivedClassWithMoreKeywordAliases(TestClassWithKeywordAliases):
    _SERIALIZABLE_KEYWORD_ALIASES = {"old_y": "y"}

    def __init__(self, x, y):
        self.x = x
        self.y = y


class DerivedClassWithoutMoreKeywordAliases(TestClassWithKeywordAliases):
    def __init__(self, x, y):
        self.x = x
        self.y = y


def test_normal_keywords():
    # testing that nothing got screwed in the normal logic of object
    # serialization/deserialization by the addition of keyword aliases
    obj1 = TestClassWithKeywordAliases.from_json(TestClassWithKeywordAliases(x=1).to_json())
    eq_(obj1.x, 1)

    obj2 = DerivedClassWithMoreKeywordAliases.from_json(
        DerivedClassWithMoreKeywordAliases(x=10, y=20).to_json()
    )
    eq_(obj2.x, 10)
    eq_(obj2.y, 20)

    obj3 = DerivedClassWithoutMoreKeywordAliases.from_json(
        DerivedClassWithoutMoreKeywordAliases(x=100, y=200).to_json()
    )
    eq_(obj3.x, 100)
    eq_(obj3.y, 200)


def test_removed_keyword():
    d = TestClassWithKeywordAliases(x=1).to_dict()
    d["old_gone"] = "WILL BE ERASED"
    obj = TestClassWithKeywordAliases.from_dict(d)
    eq_(obj.x, 1)
    assert not hasattr(obj, "old_gone")


def test_removed_keyword_inheritance():
    d = DerivedClassWithoutMoreKeywordAliases(x=1, y=2).to_dict()
    d["old_gone"] = "WILL BE REMOVED"

    obj = DerivedClassWithoutMoreKeywordAliases.from_dict(d)
    eq_(obj.x, 1)
    eq_(obj.y, 2)
    assert not hasattr(obj, "old_gone")


def test_renamed_keyword():
    d = TestClassWithKeywordAliases(x=1).to_dict()
    x = d.pop("x")
    d["old_x"] = x
    obj = TestClassWithKeywordAliases.from_dict(d)
    eq_(obj.x, 1)
    assert not hasattr(obj, "old_x")


def test_renamed_keyword_inheritance():
    d = DerivedClassWithMoreKeywordAliases(x=1, y=2).to_dict()
    x = d.pop("x")
    y = d.pop("y")

    d["old_x"] = x
    d["old_y"] = y

    obj = DerivedClassWithMoreKeywordAliases.from_dict(d)
    eq_(obj.x, 1)
    eq_(obj.y, 2)
    assert not hasattr(obj, "old_x")
    assert not hasattr(obj, "old_y")


def test_from_dict_does_not_modify_input():
    d = {"old_x": 1, "old_gone": 2}
    obj = TestClassWithKeywordAliases.from_dict(d)
    eq_(obj.x, 1)
    eq_(d, {"old_x": 1, "old_gone": 2})


def test_apply_keyword_aliases_renames_drops_and_returns_same_dict():
    kwargs = {"old_x": 1, "old_gone": 2}
    result = apply_keyword_aliases(TestClassWithKeywordAliases, kwargs)
    assert result is kwargs
    eq_(result, {"x": 1})


def test_apply_keyword_aliases_prefers_current_name():
    kwargs = {"old_x": "old", "x": "new"}
    eq_(apply_keyword_aliases(TestClassWithKeywordAliases, kwargs), {"x": "new"})


def test_apply_keyword_aliases_uses_every_class_in_the_mro():
    kwargs = {"old_x": 1, "old_y": 2, "old_gone": 3}
    eq_(apply_keyword_aliases(DerivedClassWithMoreKeywordAliases, kwargs), {"x": 1, "y": 2})


def test_apply_keyword_aliases_without_aliases_is_a_no_op():
    eq_(apply_keyword_aliases(object, {"a": 1}), {"a": 1})


@dataclass
class DataclassWithEmptyAlias(DataclassSerializable):
    _SERIALIZABLE_KEYWORD_ALIASES: ClassVar[dict[str, str | None]] = {"legacy": ""}
    x: int


class SerializableWithEmptyAlias(Serializable):
    _SERIALIZABLE_KEYWORD_ALIASES = {"legacy": ""}

    def __init__(self, x):
        self.x = x


def test_both_base_classes_treat_an_empty_alias_as_removed():
    # Serializable always dropped these; DataclassSerializable used to pass
    # them to the constructor under the keyword "", which raised TypeError.
    assert SerializableWithEmptyAlias.from_dict(
        {"x": 1, "legacy": 2}
    ) == SerializableWithEmptyAlias(x=1)
    assert DataclassWithEmptyAlias.from_dict({"x": 1, "legacy": 2}) == DataclassWithEmptyAlias(x=1)


class ClassOverridingUpdateKwargs(TestClassWithKeywordAliases):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    @classmethod
    def _update_kwargs(cls, kwargs):
        kwargs = super()._update_kwargs(kwargs)
        kwargs.setdefault("y", "filled in by override")
        return kwargs


def test_from_dict_still_calls_an_overridden_update_kwargs():
    # _update_kwargs is kept as a hook: an override runs in from_dict and can
    # still apply the inherited aliases through super().
    obj = ClassOverridingUpdateKwargs.from_dict({"old_x": 1})
    eq_(obj.x, 1)
    eq_(obj.y, "filled in by override")
