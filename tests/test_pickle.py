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

import copy
import datetime
import io
import pickle
from dataclasses import dataclass

import pytest

from serializable import (
    DataclassSerializable,
    Serializable,
    from_serializable_repr,
    to_serializable_repr,
)

from .common import eq_


class Point(Serializable):
    def __init__(self, x, y):
        self.x = x
        self.y = y


@dataclass(frozen=True)
class Pair(DataclassSerializable):
    left: object
    right: object


class Interned(Serializable):
    """from_dict returns a cached instance, like pyensembl's EnsemblRelease"""

    _instances = {}

    def __init__(self, name):
        self.name = name

    @classmethod
    def from_dict(cls, state_dict):
        name = state_dict["name"]
        if name not in cls._instances:
            cls._instances[name] = cls(name)
        return cls._instances[name]


nested = Point([Point(1, 2), (3, 4)], {(5, 6): {7, 8}, "pair": Pair("a", Point(9, 10))})


class Pre12Pickler(pickle.Pickler):
    """Pickles objects the way serializable < 1.2.0 did."""

    def reducer_override(self, obj):
        if isinstance(obj, (Serializable, DataclassSerializable)):
            return (from_serializable_repr, (to_serializable_repr(obj),))
        return NotImplemented


@pytest.mark.parametrize("protocol", range(pickle.HIGHEST_PROTOCOL + 1))
def test_pickle_roundtrip_all_protocols(protocol):
    eq_(nested, pickle.loads(pickle.dumps(nested, protocol=protocol)))
    pair = Pair(nested, "b")
    eq_(pair, pickle.loads(pickle.dumps(pair, protocol=protocol)))


def test_load_pickle_written_before_1_2():
    objects = [nested, Pair(1, nested)]
    buffer = io.BytesIO()
    Pre12Pickler(buffer).dump(objects)
    eq_(objects, pickle.loads(buffer.getvalue()))


def test_pickle_reconstructs_with_from_dict():
    obj = Interned.from_dict({"name": "a"})
    assert pickle.loads(pickle.dumps(obj)) is obj


def test_pickle_value_without_serializable_representation():
    # values in to_dict() are pickled natively, so they don't need a
    # JSON-compatible representation
    obj = Point(datetime.date(2026, 10, 6), None)
    with pytest.raises(ValueError):
        obj.to_json()
    eq_(obj, pickle.loads(pickle.dumps(obj)))


def test_deepcopy():
    copied = copy.deepcopy(nested)
    eq_(nested, copied)
    assert copied.x is not nested.x
