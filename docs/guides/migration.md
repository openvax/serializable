# Change field names

Use `_SERIALIZABLE_KEYWORD_ALIASES` when constructor fields change. Both base
classes support this mapping: an old name maps to its replacement, or to
`None` when the field should be discarded. A value already provided under the
new name takes precedence.

```python
from dataclasses import dataclass
from typing import ClassVar
from serializable import DataclassSerializable

@dataclass
class Sample(DataclassSerializable):
    name: str
    _SERIALIZABLE_KEYWORD_ALIASES: ClassVar[dict] = {
        "label": "name",
        "obsolete": None,
    }

print(Sample.from_dict({"label": "tumor", "obsolete": 7}))
print(Sample.from_dict({"label": "old", "name": "new"}))
```

```text
Sample(name='tumor')
Sample(name='new')
```

The mapping changes constructor keywords; it does not migrate module names or
class names recorded in JSON. Keep the recorded class importable, or provide
an explicit application-level migration for stored representations.
