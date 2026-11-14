# Loading guards, enums and frozensets, reserved keys (1.6.0)

## Specification

Finish the bugs found in the 1.3.2 audit (#34, #26):

1. `from_json` / `from_serializable_repr` only construct classes: a function
   under `__class__` raises `ValueError` instead of being called, `__value__`
   is honoured only for `set`, `frozenset`, `tuple` and `Enum` classes, and a
   module/name reference must resolve to a class or function.
2. `enum.Enum` members and frozensets round-trip.
3. Plain dictionaries whose keys resemble the format's own (`__name__`,
   `__class__`, `__serialized_keys__...`) round-trip where that is
   unambiguous, and are rejected when writing where it isn't.
4. `_lookup_value` no longer skips a path component when the module path
   continues into a class.
5. `develop.sh` and the README use a strict editable install so downstream
   type checkers can see the package.

Out of scope: removing the unused `typechecks` dependency (#15) and dead
helpers (#30, #31).

## Plan

- [x] Implement and test 1–5; update docs; bump version to 1.6.0.
- [x] Independent code review; address findings.
- [x] Run `./format.sh`, `./lint.sh`, `./test.sh`.
- [ ] Compare sibling projects' serialization tests against 1.5.0.
- [ ] Open PR, pass CI, merge, deploy from clean master.
- [ ] Reinstall into the shared virtualenv and check its dependents import.
