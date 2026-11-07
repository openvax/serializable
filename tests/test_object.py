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


class A(Serializable):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def to_dict(self):
        return {"x": self.x, "y": self.y}


class B(A):
    pass


class Other(Serializable):
    def __init__(self, x):
        self.x = x


instance = A(1, 2)


def test_serialize_object_with_helpers():
    instance_reconstructed = from_serializable_repr(to_serializable_repr(instance))
    eq_(instance, instance_reconstructed)


def test_object_to_json():
    eq_(instance, A.from_json(instance.to_json()))


def test_object_pickle():
    eq_(instance, pickle.loads(pickle.dumps(instance)))


def test_object_json_file(tmp_path):
    path = tmp_path / "instance.json"
    instance.write_json_file(path)
    eq_(instance, A.read_json_file(path))


def test_from_json_returns_subclass_named_in_json():
    derived = B(1, 2)
    restored = A.from_json(derived.to_json())
    eq_(type(restored), B)
    eq_(restored, derived)


def test_from_json_rejects_other_class():
    other_json = Other(1).to_json()
    with pytest.raises(ValueError, match="holds Other, not A"):
        A.from_json(other_json)
    eq_(from_json(other_json), Other(1))


def test_from_json_rejects_json_without_class():
    with pytest.raises(ValueError, match="holds dict, not A"):
        A.from_json(to_json({"x": 1, "y": 2}))


def test_read_json_file_rejects_other_class(tmp_path):
    path = tmp_path / "other.json"
    Other(1).write_json_file(path)
    with pytest.raises(ValueError, match="holds Other, not A"):
        A.read_json_file(path)
