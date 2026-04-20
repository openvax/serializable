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

from serializable import (
    Serializable,
    from_serializable_repr,
    to_serializable_repr,
)

from .common import eq_


class A(Serializable):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def to_dict(self):
        return {"x": self.x, "y": self.y}


instance = A(1, 2)


def test_serialize_object_with_helpers():
    instance_reconstructed = from_serializable_repr(to_serializable_repr(instance))
    eq_(instance, instance_reconstructed)


def test_object_to_json():
    eq_(instance, A.from_json(instance.to_json()))


def test_object_pickle():
    eq_(instance, pickle.loads(pickle.dumps(instance)))
