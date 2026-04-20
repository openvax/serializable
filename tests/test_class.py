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


from serializable import from_serializable_repr, to_serializable_repr

from .common import eq_


class A:
    pass


def test_serialize_custom_class():
    A_reconstructed = from_serializable_repr(to_serializable_repr(A))
    eq_(A, A_reconstructed)


def test_serialize_builtin_class():
    int_reconstructed = from_serializable_repr(to_serializable_repr(int))
    eq_(int, int_reconstructed)
