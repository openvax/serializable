#!/usr/bin/env bash

set -e

VENV_DIR=".venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment at $VENV_DIR..."
    python -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# A strict editable install puts a plain directory on sys.path, which type
# checkers in projects depending on this one can follow. The default install
# uses an import hook which mypy can't see through (#26). The tradeoff: rerun
# this script after adding or renaming a file in serializable/, or after
# deleting build/, where the installed link tree lives.
EDITABLE_MODE=(-C editable_mode=strict)

# Check if UV is installed and available in the PATH
if command -v uv &> /dev/null; then
    echo "Using uv to install package with development dependencies..."
    uv pip install "${EDITABLE_MODE[@]}" -e ".[dev]"
else
    echo "uv not found, falling back to regular pip..."
    pip install "${EDITABLE_MODE[@]}" -e ".[dev]"
fi
