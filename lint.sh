#!/usr/bin/env bash

set -e

SOURCES="serializable tests"

echo "Running ruff check..."
ruff check $SOURCES

echo "Running ruff format check..."
ruff format --check $SOURCES

echo "Running mypy..."
# Use the first of the active virtualenv, the project's .venv (see develop.sh)
# or python3 which has mypy installed: the active environment may not be this
# project's, e.g. when run from a git hook.
for PYTHON in ${VIRTUAL_ENV:+"$VIRTUAL_ENV/bin/python"} .venv/bin/python python3; do
    if "$PYTHON" -c "import mypy" 2>/dev/null; then
        break
    fi
done
"$PYTHON" -m mypy serializable

echo "All checks passed!"
