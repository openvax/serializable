[![Tests](https://github.com/openvax/serializable/actions/workflows/tests.yml/badge.svg)](https://github.com/openvax/serializable/actions/workflows/tests.yml)
<a href="https://pypi.python.org/pypi/serializable/">
<img src="https://img.shields.io/pypi/v/serializable.svg?maxAge=1000" alt="PyPI" />
</a>
[![PyPI downloads](https://img.shields.io/pypi/dm/serializable.svg)](https://pypistats.org/packages/serializable)

# serializable

Base class with serialization methods for user-defined Python objects

## Install

```sh
python -m pip install serializable
```

## `DataclassSerializable` for `@dataclass` subclasses

If you're using `@dataclass` (e.g. in `vaxrank`, `pyensembl`, or `varcode`), inherit from `DataclassSerializable` instead of `Serializable`. It provides the same serialization surface — `to_dict` / `from_dict` / `to_json` / `from_json` — but leaves `__init__`, `__eq__`, `__repr__`, and `__hash__` to `@dataclass`, so you get dataclass-native equality and repr without conflicts.

```python
from dataclasses import dataclass
from serializable import DataclassSerializable

@dataclass
class Point(DataclassSerializable):
    x: float
    y: float

p = Point(1.0, 2.0)
assert Point.from_json(p.to_json()) == p
```

The on-wire JSON format is identical to `Serializable`, so mixed codebases interoperate: a `DataclassSerializable` instance can reference a legacy `Serializable` object (and vice versa) and still round-trip cleanly. The `_SERIALIZABLE_KEYWORD_ALIASES` hook works the same way for migrating field names across releases.

## Usage

Classes which inherit from `Serializable` are enabled with default implementations of
`to_json`, `from_json`, `__reduce__` (for pickling), and other serialization
helpers.

A derived class must either:

- have a member data matching the name of each positional argument to `__init__`
- provide a user-defined `to_dict()` method which returns a dictionary whose keys match the arguments to `__init__`

Keyword-only arguments to `__init__` (those after `*`) are left out of the default `to_dict()`, so they can be used for constructor options which aren't part of an object's serialized state.

Pickling goes through the same `to_dict()` / `from_dict()` pair, so pickles also survive renamed keywords (see below). Pickles written by versions before 1.2.0 can still be loaded.

If you change the keyword arguments to a class which derives from `Serializable` but would like to be able to deserialize older JSON representations then you can define a class-level dictionary called `_SERIALIZABLE_KEYWORD_ALIASES` which maps old keywords to new names (or `None` if a keyword was removed).

## Limitations

The format records Python classes and modules, which must remain importable when
loading data. Keys starting with two underscores are reserved. Nested Python
values require the serialization helpers rather than ordinary JSON encoding.

## Documentation

- [Save classes, files and nested objects](docs/guides/objects.md)
- [Migrate field names](docs/guides/migration.md)
- [API reference](docs/reference.md)
- [Writing and checking docs](docs/dev/documentation-style.md)

The site builds with `python -m pip install -r requirements-docs.txt` followed
by `./docs.sh`. Run `python scripts/check_docs_examples.py` to check the examples.
