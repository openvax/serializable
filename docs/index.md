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

## Save and reload an object

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

`to_dict()` describes constructor fields. `to_json()` also records the class
and its module so `from_json()` can reconstruct it. The dataclass keeps its
normal generated constructor, equality, representation and hashing.

## Choose a representation

| Your task | Interface |
| --- | --- |
| Serialize a dataclass | `DataclassSerializable` |
| Serialize a constructor-based class | `Serializable` |
| Serialize a nested collection of supported objects | `to_json()` / `from_json()` helpers |
| Obtain constructor fields | `to_dict()` / `from_dict()` |

Both base classes write the same JSON format, so a dataclass can hold a
`Serializable` object, or the reverse, and the whole object still round-trips.

See [save existing classes and files](guides/objects.md), then
[change field names](guides/migration.md). The [API reference](reference.md)
lists the complete interfaces.

## Format and limitations

This is a Python object round-trip format, rather than a language-independent
application schema. Deserialization imports the recorded module and looks up
the class, so that module and class must remain available in the loading
environment. Load representations from sources you trust: reconstruction
imports modules and calls constructors.

Supported values include primitive values, dictionaries, lists, tuples, sets
and objects implementing the serialization interface. Dictionary keys beginning
with two underscores are reserved by the format. `to_dict()` is the object's
field mapping; it does not by itself guarantee an ordinary JSON-compatible
mapping when those fields contain nested Python objects.

Classes and functions are recorded by module and qualified name, so nested
classes work, while `to_json()` raises `ValueError` for anything which can't be
looked up that way: classes or functions defined inside a function, lambdas and
bound builtin methods. Dataclass fields declared with `init=False` are not
stored, since the class computes them itself.

Floats must be finite: `to_json()` raises `ValueError` for NaN or infinity,
which standard JSON can't represent. `from_json()` still reads the `NaN` and
`Infinity` literals which older versions wrote.
