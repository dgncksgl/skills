#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
cd "$ROOT"

if [[ -f uv.lock ]]; then
    echo "uv"
    exit 0
fi

if [[ -f pyproject.toml ]] && grep -q '^\[tool\.poetry\]' pyproject.toml 2>/dev/null; then
    echo "poetry"
    exit 0
fi

if [[ -f Pipfile ]] || [[ -f Pipfile.lock ]]; then
    echo "pipenv"
    exit 0
fi

if [[ -f environment.yml ]] || [[ -f conda-lock.yml ]]; then
    echo "conda"
    exit 0
fi

if [[ -f requirements.txt ]] || [[ -f requirements-dev.txt ]] \
   || [[ -f setup.py ]] || [[ -f setup.cfg ]] \
   || [[ -f pyproject.toml ]]; then
    echo "pip"
    exit 0
fi

echo "unknown"
exit 1
