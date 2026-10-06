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


class WithKeywordOnlyOption(Serializable):
    def __init__(self, x, *, scale=1):
        # the keyword-only option isn't stored, so it can't be serialized
        self.x = x * scale


def test_keyword_only_args_excluded_from_default_to_dict():
    # keyword-only args are constructor options rather than serialized state
    # (varcode's SpliceOutcomeSet relies on this)
    obj = WithKeywordOnlyOption(10, scale=2)
    eq_(obj.to_dict(), {"x": 20})
    eq_(obj, WithKeywordOnlyOption.from_json(obj.to_json()))
