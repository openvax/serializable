#!/usr/bin/env bash

set -e

SOURCES="serializable tests"

echo "Running ruff format..."
ruff format $SOURCES

echo "Formatting complete!"
