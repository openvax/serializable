[![Tests](https://github.com/openvax/serializable/actions/workflows/tests.yml/badge.svg?branch=master)](https://github.com/openvax/serializable/actions/workflows/tests.yml)
[![Documentation](https://github.com/openvax/serializable/actions/workflows/documentation.yml/badge.svg?branch=master)](https://openvax.github.io/serializable/)
[![PyPI](https://img.shields.io/pypi/v/serializable.svg)](https://pypi.org/project/serializable/)
[![PyPI downloads](https://img.shields.io/pypi/dm/serializable.svg)](https://pypistats.org/packages/serializable)

# serializable

serializable saves Python objects as JSON or pickles and reconstructs the same
classes, including nested objects. Subclass `DataclassSerializable` for a
dataclass, or `Serializable` for a class whose constructor arguments describe
its state. It is the serialization layer of the OpenVax libraries:
[varcode](https://github.com/openvax/varcode) and
[vaxrank](https://github.com/openvax/vaxrank) results,
[pyensembl](https://github.com/openvax/pyensembl) genomes and
[sercol](https://github.com/openvax/sercol) collections all save and reload
through it.

## Install

```sh
python -m pip install serializable
```

Python 3.11 or later is required.

## Quick start

```python
from dataclasses import dataclass
from serializable import DataclassSerializable

@dataclass
class Point(DataclassSerializable):
    x: float
    y: float

point = Point(1.0, 2.0)
restored = Point.from_json(point.to_json())
print(point.to_dict())
print(restored)
print(restored == point)
```

```text
{'x': 1.0, 'y': 2.0}
Point(x=1.0, y=2.0)
True
```

`to_dict()` gives the constructor fields; `to_json()` also records the class
and its module so `from_json()` can rebuild it. The dataclass keeps its own
generated constructor, equality and representation. The recorded module and
class must be importable when loading, so load data only from sources you
trust.

## Documentation

The [documentation](https://openvax.github.io/serializable/) covers, in
reading order:

1. [Getting started](https://openvax.github.io/serializable/): the example
   above, choosing a base class, and the format's limits.
2. [Save classes and files](https://openvax.github.io/serializable/guides/objects/):
   constructor-based classes, JSON files, pickles and nested containers.
3. [Change field names](https://openvax.github.io/serializable/guides/migration/):
   read data written before a constructor argument was renamed.
4. [API reference](https://openvax.github.io/serializable/reference/).

## Development

```sh
python -m pip install -e ".[dev]"   # or ./develop.sh, which uses .venv
./format.sh   # ruff format
./lint.sh     # ruff check, ruff format --check and mypy
./test.sh     # pytest with coverage
python -m pip install -r requirements-docs.txt
./docs.sh     # mkdocs build --strict, then a rendered-link check
python scripts/check_docs_examples.py   # run docs examples, compare output
```

Every PR bumps `serializable/version.py`. Maintainers release with
`./deploy.sh` from a clean `master`.

## License

Apache 2.0; see [LICENSE](https://github.com/openvax/serializable/blob/master/LICENSE).
