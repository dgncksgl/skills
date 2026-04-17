#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
cd "$ROOT"
shift || true

FILES=("$@")

run() {
    echo "==> $*" >&2
    "$@"
}

have() { command -v "$1" >/dev/null 2>&1; }

if [[ -f tsconfig.json ]]; then
    if have npx; then
        run npx --no -- tsc --noEmit
        exit $?
    fi
fi

if [[ -f pyrightconfig.json ]] || ( [[ -f pyproject.toml ]] && grep -q '\[tool\.pyright\]' pyproject.toml 2>/dev/null ); then
    if have pyright; then
        if [[ ${#FILES[@]} -gt 0 ]]; then run pyright "${FILES[@]}"; else run pyright .; fi
        exit $?
    fi
fi

if [[ -f mypy.ini ]] || ( [[ -f pyproject.toml ]] && grep -q '\[tool\.mypy\]' pyproject.toml 2>/dev/null ); then
    if have mypy; then
        if [[ ${#FILES[@]} -gt 0 ]]; then run mypy "${FILES[@]}"; else run mypy .; fi
        exit $?
    fi
fi

if [[ -f pyproject.toml || -f setup.py || -f setup.cfg ]] || compgen -G "*.py" >/dev/null 2>&1; then
    if have pyright; then
        if [[ ${#FILES[@]} -gt 0 ]]; then run pyright "${FILES[@]}"; else run pyright .; fi
        exit $?
    fi
    if have mypy; then
        if [[ ${#FILES[@]} -gt 0 ]]; then run mypy "${FILES[@]}"; else run mypy .; fi
        exit $?
    fi
    echo "type-check.sh: no python type checker (pyright/mypy) installed" >&2
    exit 2
fi

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

if [[ -f go.mod ]]; then
    run go vet ./...
    exit $?
fi

if compgen -G "*.csproj" >/dev/null 2>&1 || find . -maxdepth 3 -name "*.csproj" -print -quit 2>/dev/null | grep -q .; then
    run dotnet build --nologo -v q
    exit $?
fi

if [[ -f Cargo.toml ]]; then
    run cargo check --quiet
    exit $?
fi

echo "type-check.sh: no recognized type checker configuration found" >&2
exit 2
