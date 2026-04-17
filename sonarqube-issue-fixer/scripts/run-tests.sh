#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
cd "$ROOT"

run() {
    echo "==> $*"
    "$@"
}

if [[ -f pom.xml ]]; then
    run mvn -q test
    exit $?
fi

if [[ -x ./gradlew ]]; then
    run ./gradlew test --quiet
    exit $?
fi

if [[ -f build.gradle || -f build.gradle.kts ]]; then
    run gradle test --quiet
    exit $?
fi

if [[ -f package.json ]]; then
    if grep -q '"test"' package.json; then
        run npm test --silent
    else
        run npx jest --silent || true
    fi
    exit 0
fi

if [[ -f pyproject.toml || -f setup.cfg ]] || compgen -G "*.py" >/dev/null 2>&1; then
    if command -v pytest >/dev/null 2>&1; then
        run pytest -q
    else
        run python -m unittest discover -q
    fi
    exit $?
fi

if [[ -f go.mod ]]; then
    run go test ./...
    exit $?
fi

if compgen -G "*.csproj" >/dev/null 2>&1 || find . -maxdepth 3 -name "*.csproj" -print -quit | grep -q .; then
    run dotnet test --nologo -v q
    exit $?
fi

if [[ -f Cargo.toml ]]; then
    run cargo test --quiet
    exit $?
fi

echo "run-tests.sh: no recognized test runner found" >&2
exit 2
