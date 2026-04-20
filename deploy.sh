#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

./lint.sh
./test.sh

PYTHON_BIN="${DEPLOY_PYTHON:-python3}"
"$PYTHON_BIN" -m pip install --upgrade build twine
rm -rf dist build ./*.egg-info
"$PYTHON_BIN" -m build
"$PYTHON_BIN" -m twine check dist/*
"$PYTHON_BIN" -m twine upload dist/*
