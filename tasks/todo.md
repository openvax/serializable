# Round-trip bug fixes (1.5.0)

## Specification

Fix five cases where a value is written but can't be read back (or can't be
written at all), and reject at write time the values which could never be
loaded. JSON written by earlier versions must keep loading unchanged.

1. `DataclassSerializable`: fields declared `init=False` are not constructor
   arguments. Leave them out of `to_dict()`, and ignore them in `from_dict()`
   so data written by older versions loads.
2. Nested classes and functions: record `__qualname__` instead of `__name__`
   (identical for top-level definitions, so the format is unchanged for them).
3. Classes with a metaclass (e.g. `abc.ABC` subclasses) serialize as class
   values: test `isinstance(x, type)` rather than `type(x) is type`.
4. A class which inherits `object.__init__` (and `object.__new__`) has no
   constructor arguments, rather than being an error.
5. A decorated `__init__` (using `functools.wraps`) is unwrapped before its
   argument names are read.
6. Write-time `ValueError` for classes and functions which can't be looked up
   by name: defined inside a function (`<locals>`), lambdas, and builtin
   methods without a module.

Out of scope (separate PR): restricting what `from_json` may call; reserved
key collisions in user dictionaries; Enum and frozenset support.

## Plan

- [x] Implement 1–6 in `helpers.py` and `dataclass_serializable.py`.
- [x] Add tests for each; update docs limitations; bump version to 1.5.0.
- [x] Run `./format.sh`, `./lint.sh`, `./test.sh`.
- [ ] Open PR, pass CI, merge, deploy from clean master.
