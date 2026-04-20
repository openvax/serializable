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


from serializable import Serializable

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
