# Remaining review findings from #36 (1.7.0)

## Specification

1. Enum members are written by name (`__member__`), so a member's value needn't
   be serializable or comparable. Combinations of flags, which have no name,
   and data written by 1.6.0 keep using `__value__`.
2. For classes other than set, frozenset, tuple and enums, `__value__` is an
   ordinary field passed to `from_dict`, so a class using that key in its own
   `to_dict()` round-trips.
3. CI installs with the same strict editable mode that `develop.sh` documents.

## Plan

- [x] Implement and test; update docs; bump version to 1.7.0.
- [x] Run `./format.sh`, `./lint.sh`, `./test.sh`.
- [ ] Open PR, pass CI, merge, deploy, refresh the shared virtualenv.
