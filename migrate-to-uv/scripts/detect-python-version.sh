#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
cd "$ROOT"

extract() {
    grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -1 || true
}

if [[ -f .python-version ]]; then
    v=$(cat .python-version | extract)
    [[ -n "$v" ]] && { echo "$v"; exit 0; }
fi

if [[ -f pyproject.toml ]]; then
    v=$(grep -E '^requires-python' pyproject.toml 2>/dev/null | extract)
    [[ -n "$v" ]] && { echo "$v"; exit 0; }
    v=$(grep -A1 '\[tool\.poetry\.dependencies\]' pyproject.toml 2>/dev/null | grep -E '^python' | extract)
    [[ -n "$v" ]] && { echo "$v"; exit 0; }
fi

if [[ -f setup.cfg ]]; then
    v=$(grep -E 'python_requires' setup.cfg 2>/dev/null | extract)
    [[ -n "$v" ]] && { echo "$v"; exit 0; }
fi

if [[ -f setup.py ]]; then
    v=$(grep -E 'python_requires' setup.py 2>/dev/null | extract)
    [[ -n "$v" ]] && { echo "$v"; exit 0; }
fi

if [[ -f Pipfile ]]; then
    v=$(grep -A2 '\[requires\]' Pipfile 2>/dev/null | grep -E 'python_version' | extract)
    [[ -n "$v" ]] && { echo "$v"; exit 0; }
fi

if [[ -f environment.yml ]]; then
    v=$(grep -E '^\s*-\s*python' environment.yml 2>/dev/null | extract)
    [[ -n "$v" ]] && { echo "$v"; exit 0; }
fi

if [[ -f .venv/pyvenv.cfg ]]; then
    v=$(grep -E '^version' .venv/pyvenv.cfg 2>/dev/null | extract)
    [[ -n "$v" ]] && { echo "$v"; exit 0; }
fi

if command -v python3 >/dev/null 2>&1; then
    v=$(python3 --version 2>&1 | extract)
    [[ -n "$v" ]] && { echo "$v"; exit 0; }
fi

echo "unknown"
exit 1
