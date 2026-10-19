# Python 3.11 support floor (#24)

## Specification

Require Python 3.11 or newer without adding an upper bound. Advertise the
tested 3.11–3.14 range, remove 3.9/3.10 from CI, and align Ruff and mypy's
language targets. Keep runtime serialization behavior and dependencies as they
are. Bump the patch version for the release.

## Plan

- [x] Read issue, packaging, CI, repository guidance, and existing tests.
- [x] Check plan before implementation: this is a metadata/tooling policy change;
  the current test matrix already covers all four retained versions.
- [x] Update metadata, CI, type-check targets, and version.
- [x] Run `./format.sh`, `./lint.sh`, and `./test.sh` in an isolated environment.
- [x] Verify installation metadata and dependency resolution on Python 3.11 and
  3.14; review the diff.
- [ ] Open PR, pass CI, merge, deploy from clean master, and verify publication.

## Review

`./format.sh` left all 21 source/test files unchanged. `./lint.sh` passed
Ruff, formatter, and mypy checks. `./test.sh` passed all 100 tests on both
Python 3.11.12 and 3.14.6. Isolated dependency checks passed at both endpoints;
installed metadata reports version 1.3.2 and `Requires-Python: >=3.11`.
