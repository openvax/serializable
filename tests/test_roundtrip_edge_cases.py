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
Classes and functions which earlier versions either couldn't write or wrote
in a form which couldn't be read back.
"""

import abc
import functools
import pickle
from dataclasses import dataclass, field

import pytest

from serializable import (
    DataclassSerializable,
    Serializable,
    from_json,
    from_serializable_repr,
    to_json,
    to_serializable_repr,
)

from .common import eq_


class Outer:
    class Inner(Serializable):
        def __init__(self, x):
            self.x = x

    @staticmethod
    def static_fn():
        pass


class NoInit(Serializable):
    pass


class NewWithoutInit(Serializable):
    def __new__(cls, x):
        obj = super().__new__(cls)
        obj.x = x
        return obj


class Abstract(Serializable, abc.ABC):
    def __init__(self, x):
        self.x = x


def logged(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)

    return wrapper


class DecoratedInit(Serializable):
    @logged
    def __init__(self, x, y=2):
        self.x = x
        self.y = y


@dataclass
class Rectangle(DataclassSerializable):
    width: int
    height: int
    area: int = field(init=False)

    def __post_init__(self):
        self.area = self.width * self.height


def test_nested_class_instance_roundtrip():
    obj = Outer.Inner(1)
    eq_(obj, from_json(obj.to_json()))
    eq_(obj, pickle.loads(pickle.dumps(obj)))


def test_nested_class_as_value_roundtrip():
    class_repr = to_serializable_repr(Outer.Inner)
    eq_(class_repr["__name__"], "Outer.Inner")
    assert from_serializable_repr(class_repr) is Outer.Inner


def test_top_level_class_representation_unchanged():
    eq_(to_serializable_repr(NoInit), {"__module__": __name__, "__name__": "NoInit"})


def test_nested_function_roundtrip():
    assert from_json(to_json(Outer.static_fn)) is Outer.static_fn


def test_class_without_init():
    obj = NoInit()
    eq_(obj.to_dict(), {})
    eq_(obj, NoInit())
    eq_(str(obj), "NoInit()")
    eq_(obj, from_json(obj.to_json()))
    eq_(obj, pickle.loads(pickle.dumps(obj)))


def test_class_with_new_but_no_init_is_still_an_error():
    with pytest.raises(ValueError):
        NewWithoutInit(1).to_dict()


def test_class_with_metaclass_as_value_roundtrip():
    assert from_json(to_json({"cls": Abstract}))["cls"] is Abstract
    assert from_json(to_json(abc.ABC)) is abc.ABC


def test_decorated_init():
    obj = DecoratedInit(1, y=3)
    eq_(obj.to_dict(), {"x": 1, "y": 3})
    eq_(obj, from_json(obj.to_json()))


def test_dataclass_init_false_field_roundtrip():
    rect = Rectangle(2, 3)
    eq_(rect.to_dict(), {"width": 2, "height": 3})
    eq_(rect, from_json(rect.to_json()))
    eq_(rect, pickle.loads(pickle.dumps(rect)))


def test_dataclass_init_false_field_written_by_older_versions():
    # versions before 1.5.0 included init=False fields in to_dict()
    eq_(Rectangle(2, 3), Rectangle.from_dict({"width": 2, "height": 3, "area": 6}))


def test_local_class_rejected_when_writing():
    class Local(Serializable):
        def __init__(self, x):
            self.x = x

    with pytest.raises(ValueError, match="looked up by name"):
        to_json(Local(1))
    with pytest.raises(ValueError, match="looked up by name"):
        to_serializable_repr(Local)
    # only the import path is unavailable, the object itself still works
    eq_(Local(1), Local(1))


def test_lambda_and_local_function_rejected_when_writing():
    def local_fn():
        pass

    for fn in (lambda: None, local_fn):
        with pytest.raises(ValueError, match="looked up by name"):
            to_serializable_repr(fn)


def test_builtin_method_rejected_when_writing():
    with pytest.raises(ValueError, match="looked up by name"):
        to_serializable_repr([].append)
