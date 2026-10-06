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

import inspect
import typing
from dataclasses import dataclass

import pytest

from serializable import DataclassSerializable, Serializable, helpers


class Point(Serializable):
    def __init__(self, x):
        self.x = x


@dataclass
class DataclassPoint(DataclassSerializable):
    x: int


def annotated_objects():
    yield Point
    yield DataclassPoint
    for cls in (Serializable, DataclassSerializable):
        for _, method in inspect.getmembers(cls, callable):
            if (getattr(method, "__module__", None) or "").startswith("serializable"):
                yield method
    for _, function in inspect.getmembers(helpers, inspect.isfunction):
        if function.__module__ == helpers.__name__:
            yield function


@pytest.mark.parametrize("obj", list(annotated_objects()), ids=lambda obj: obj.__qualname__)
def test_annotations_evaluate_at_runtime(obj):
    # annotations must stay evaluable on the oldest supported Python (no
    # `X | Y` unions before 3.10) for tools which call get_type_hints
    typing.get_type_hints(obj)
