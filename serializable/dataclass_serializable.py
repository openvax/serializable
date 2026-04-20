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

"""Serialization mixin for classes decorated with ``@dataclass``.

``Serializable`` (the original base class) supplies its own ``__init__``
introspection plus ``__eq__`` / ``__repr__`` / ``__hash__``, which clashes
with the methods ``@dataclass`` generates. ``DataclassSerializable`` is a
lightweight alternative that contributes only the serialization surface —
``to_dict`` / ``from_dict`` / ``to_json`` / ``from_json`` — and leaves
equality, repr, hashing, and ``__init__`` to ``@dataclass``.

Wire format parity with ``Serializable`` is preserved: the underlying
``to_serializable_repr`` helper dispatches on ``obj.to_dict()`` regardless
of which base the class inherits from, so a mixed codebase — some classes
migrated, some still on ``Serializable`` — round-trips JSON cleanly.

Example::

    from dataclasses import dataclass
    from serializable import DataclassSerializable

    @dataclass
    class Point(DataclassSerializable):
        x: float
        y: float

    p = Point(1.0, 2.0)
    assert Point.from_json(p.to_json()) == p
"""

from __future__ import annotations

from dataclasses import fields
from typing import Any, ClassVar

from .helpers import from_json, from_serializable_repr, to_json, to_serializable_repr


class DataclassSerializable:
    """Mixin providing ``to_dict`` / ``from_dict`` / ``to_json`` / ``from_json``
    for ``@dataclass``-decorated subclasses, without overriding the dunder
    methods that ``@dataclass`` generates.

    Subclasses may set ``_SERIALIZABLE_KEYWORD_ALIASES`` to migrate old
    field names across releases: map an old name to the new name, or to
    ``None`` to drop it on load. This mirrors the same hook on
    ``Serializable``.
    """

    _SERIALIZABLE_KEYWORD_ALIASES: ClassVar[dict[str, str | None]] = {}

    def to_dict(self) -> dict[str, Any]:
        """Return a dict mapping each dataclass field name to its current
        value. Keys match the ``__init__`` keyword arguments, so
        ``cls(**obj.to_dict())`` reconstructs an equal instance."""
        return {f.name: getattr(self, f.name) for f in fields(self)}

    @classmethod
    def from_dict(cls, state_dict: dict[str, Any]):
        """Reconstruct an instance from a ``to_dict``-shaped dictionary,
        applying ``_SERIALIZABLE_KEYWORD_ALIASES`` for backwards compat."""
        kwargs = dict(state_dict)
        for klass in cls.__mro__:
            aliases = getattr(klass, "_SERIALIZABLE_KEYWORD_ALIASES", {})
            for old_name, new_name in aliases.items():
                if old_name in kwargs:
                    value = kwargs.pop(old_name)
                    if new_name is not None and new_name not in kwargs:
                        kwargs[new_name] = value
        return cls(**kwargs)

    def to_json(self) -> str:
        return to_json(self)

    @classmethod
    def from_json(cls, json_string: str):
        return from_json(json_string)

    def __reduce__(self):
        """Pickle via the same to_dict / from_dict path used for JSON so
        pickled objects round-trip even when field order or internal
        representation changes between releases."""
        return (from_serializable_repr, (to_serializable_repr(self),))
