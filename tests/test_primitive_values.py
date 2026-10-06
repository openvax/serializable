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

import math

import pytest

from serializable import from_json, from_serializable_repr, to_json, to_serializable_repr

from .common import eq_


def test_int():
    eq_(1, from_serializable_repr(to_serializable_repr(1)))


def test_float():
    eq_(1.4, from_serializable_repr(to_serializable_repr(1.4)))


def test_bool():
    eq_(False, from_serializable_repr(to_serializable_repr(False)))


def test_str():
    eq_("waffles", from_serializable_repr(to_serializable_repr("waffles")))


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_to_json_rejects_non_finite_floats(value):
    # NaN and infinities have no standard JSON representation
    with pytest.raises(ValueError, match="Out of range float values"):
        to_json([value])


def test_from_json_accepts_non_finite_literals():
    # serializable used to write these (with simplejson < 3.19)
    values = from_json("[NaN, Infinity, -Infinity]")
    assert math.isnan(values[0])
    eq_(values[1:], [math.inf, -math.inf])
