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
Migrate renamed or removed constructor keywords when loading old data.

Both ``Serializable`` and ``DataclassSerializable`` let a class declare
``_SERIALIZABLE_KEYWORD_ALIASES``, a dict mapping an old keyword to its new
name, or to ``None`` if the keyword was removed.
"""

from __future__ import annotations

from typing import Any


def apply_keyword_aliases(cls: type, kwargs: dict[str, Any]) -> dict[str, Any]:
    """
    Rename or drop old keyword arguments using a class's declared aliases.

    Every class in ``cls``'s method resolution order contributes its
    ``_SERIALIZABLE_KEYWORD_ALIASES``. For each ``old_name -> new_name`` pair
    whose ``old_name`` is in ``kwargs``, the old entry is removed. Its value is
    stored under ``new_name`` unless ``new_name`` is ``None`` or empty (the
    keyword was removed) or ``kwargs`` already has a value for ``new_name``
    (the current name wins).

    Parameters
    ----------
    cls : type
        Class whose aliases apply, typically the class being reconstructed.

    kwargs : dict
        Keyword arguments for ``cls``'s constructor. Modified in place.

    Returns
    -------
    dict
        The same ``kwargs`` object, updated.
    """
    for klass in cls.__mro__:
        aliases = getattr(klass, "_SERIALIZABLE_KEYWORD_ALIASES", {})
        for old_name, new_name in aliases.items():
            if old_name in kwargs:
                value = kwargs.pop(old_name)
                if new_name and new_name not in kwargs:
                    kwargs[new_name] = value
    return kwargs
