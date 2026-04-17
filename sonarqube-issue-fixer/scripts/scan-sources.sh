#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
cd "$ROOT"

EXCLUDE_DIRS=(
    ".idea" ".vscode" ".vs" ".fleet"
    ".venv" "venv" "env" ".env"
    "node_modules" "bower_components"
    "vendor" "__pycache__" ".mypy_cache" ".pytest_cache" ".tox"
    ".git" ".svn" ".hg"
    "build" "dist" "target" "out" "bin" "obj"
    ".gradle" ".mvn" ".settings" ".next" ".nuxt" ".output"
    "coverage" ".nyc_output" "htmlcov"
    "Pods" "DerivedData"
)

INCLUDE_EXTS=(
    "java" "kt" "kts"
    "py"
    "ts" "tsx" "js" "jsx" "mjs" "cjs"
    "go"
    "cs"
    "rb"
    "php"
    "scala"
    "rs"
    "swift"
)

prune_args=()
for d in "${EXCLUDE_DIRS[@]}"; do
    prune_args+=( -path "*/$d" -prune -o )
done

name_args=( -type f \( )
first=1
for ext in "${INCLUDE_EXTS[@]}"; do
    if [[ $first -eq 1 ]]; then
        name_args+=( -name "*.${ext}" )
        first=0
    else
        name_args+=( -o -name "*.${ext}" )
    fi
done
name_args+=( \) )

find . "${prune_args[@]}" "${name_args[@]}" -print \
    | grep -vE '\.pb\.go$|_generated\.|\.g\.dart$|_pb2\.py$|_grpc\.py$|\.freezed\.dart$|\.designer\.cs$|\.g\.cs$' \
    | sed 's|^\./||' \
    | sort
