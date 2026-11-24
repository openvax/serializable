## Repo Info

- **Package**: `serializable` — base class with serialization helpers for user-defined Python objects.
- **GitHub**: https://github.com/openvax/serializable
- **PyPI**: https://pypi.org/project/serializable/
- **Author**: Alex Rubinsteyn <alex.rubinsteyn@unc.edu>
- **Primary branch**: `master`

---

## Golden Rules

1. **Never commit to `master`.** Always `git checkout -b <feature-branch>` before editing. Land via PR.
2. **Every PR bumps the version.** Even doc-only PRs — at minimum a patch bump. Edit `serializable/version.py`.
3. **"Done" means merged AND deployed to PyPI** — never stop at merge. After a PR merges, run `./deploy.sh` from a clean `master`. Skipping deploy = task not done.
4. **File problems as issues, don't silently work around them.** If you hit a bug here or in a sibling openvax repo, open a GitHub issue on the correct repo and link it from the PR.
5. **After a PR ships, look for the next block of work.** Read open issues across relevant openvax repos, group by dependency + urgency. Prefer *foundational* changes that unblock multiple downstream improvements; otherwise chain the smallest independent improvements.

---

## Before Completing Any Task

Before considering any code change complete, you MUST:

1. **Run `./format.sh`** — Auto-format all code
2. **Run `./lint.sh`** — Verify linting passes (runs both `ruff check` and `ruff format --check`)
3. **Run `./test.sh`** — Verify all tests pass

Do not tell the user you are "done" or that changes are "complete" until all three of these pass.

## Scripts

- `./format.sh` — Formats code with ruff (run this first)
- `./lint.sh` — Checks linting and formatting (must pass). **Always use this for linting if it exists.**
- `./test.sh` — Runs pytest with coverage (must pass)
- `./deploy.sh` — From a clean `master` that matches `origin`: gates on `lint.sh` and `test.sh`, builds, uploads to PyPI via `twine`, then tags `v<version>` and pushes the tag. `./deploy.sh --dry-run` stops before the upload. **Always use this for deploying if it exists.**
- `./develop.sh` — Installs package in development mode into `.venv`

## Code Style

- Use ruff for formatting and linting
- Configuration is in `pyproject.toml` under `[tool.ruff]`
- Line length: 100 characters
- Target Python version: 3.11+
