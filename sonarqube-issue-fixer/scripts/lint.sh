#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
cd "$ROOT"

run() {
    echo "==> $*"
    "$@"
}

if [[ -f pom.xml ]]; then
    run mvn -q compile
    exit $?
fi

if [[ -x ./gradlew ]]; then
    run ./gradlew compileJava --quiet || true
    run ./gradlew compileKotlin --quiet || true
    exit 0
fi

if [[ -f build.gradle || -f build.gradle.kts ]]; then
    run gradle compileJava --quiet || true
    run gradle compileKotlin --quiet || true
    exit 0
fi

if [[ -f tsconfig.json ]]; then
    run npx tsc --noEmit
    exit $?
fi

if [[ -f package.json ]] && command -v npx >/dev/null 2>&1; then
    if npx --no eslint --version >/dev/null 2>&1; then
        run npx eslint . || true
    else
        find . -path ./node_modules -prune -o -type f \( -name "*.js" -o -name "*.mjs" \) -print \
            | xargs -I {} node --check {} || true
    fi
    exit 0
fi

if [[ -f pyproject.toml || -f setup.cfg || -f setup.py ]] || compgen -G "*.py" >/dev/null 2>&1; then
    find . \
        -path ./.venv -prune -o \
        -path ./venv  -prune -o \
        -path ./__pycache__ -prune -o \
        -type f -name "*.py" -print \
        | xargs -I {} python -m py_compile {}
    exit $?
fi

if [[ -f go.mod ]]; then
    run go vet ./...
    exit $?
fi

if compgen -G "*.csproj" >/dev/null 2>&1 || find . -maxdepth 3 -name "*.csproj" -print -quit | grep -q .; then
    run dotnet build --nologo -v q
    exit $?
fi

if [[ -f Cargo.toml ]]; then
    run cargo check --quiet
    exit $?
fi

echo "lint.sh: no recognized build system found" >&2
exit 2
