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


class A(Serializable):
    def __init__(self, x, y=1):
        self.x = x
        self.y = y


def test_serializable_default_to_dict():
    a = A(10, 1)
    eq_(a, A.from_dict(a.to_dict()))
