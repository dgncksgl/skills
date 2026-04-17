#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
cd "$ROOT"

emit() { echo "$1 $2"; }

detect_python() {
    local found=0
    if [[ -f pyrightconfig.json ]]; then
        emit python pyright
        found=1
    fi
    if [[ -f pyproject.toml ]] && grep -q '\[tool\.pyright\]' pyproject.toml 2>/dev/null; then
        if [[ $found -eq 0 ]]; then emit python pyright; found=1; fi
    fi
    if [[ -f mypy.ini ]]; then
        emit python mypy
        found=1
    fi
    if [[ -f pyproject.toml ]] && grep -q '\[tool\.mypy\]' pyproject.toml 2>/dev/null; then
        emit python mypy
        found=1
    fi
    if [[ $found -eq 0 ]]; then
        if [[ -f pyproject.toml || -f setup.py || -f setup.cfg ]] || compgen -G "*.py" >/dev/null 2>&1; then
            emit python pyright
            found=1
        fi
    fi
    return $(( 1 - found ))
}

detect_typescript() {
    if [[ -f tsconfig.json ]]; then
        emit typescript tsc
        return 0
    fi
    return 1
}

detect_javascript() {
    if [[ -f package.json ]] && ! [[ -f tsconfig.json ]]; then
        emit javascript none
        return 0
    fi
    return 1
}

detect_java() {
    if [[ -f pom.xml ]]; then
        emit java javac-maven
        return 0
    fi
    if [[ -f build.gradle || -f build.gradle.kts ]]; then
        if grep -qE '(kotlin|org\.jetbrains\.kotlin)' build.gradle* 2>/dev/null; then
            emit kotlin kotlinc-gradle
        else
            emit java javac-gradle
        fi
        return 0
    fi
    return 1
}

detect_go() {
    if [[ -f go.mod ]]; then
        emit go govet
        return 0
    fi
    return 1
}

detect_csharp() {
    if compgen -G "*.csproj" >/dev/null 2>&1 || find . -maxdepth 3 -name "*.csproj" -print -quit 2>/dev/null | grep -q .; then
        emit csharp roslyn
        return 0
    fi
    return 1
}

detect_rust() {
    if [[ -f Cargo.toml ]]; then
        emit rust rustc
        return 0
    fi
    return 1
}

found=0
detect_python     && found=1 || true
detect_typescript && found=1 || true
detect_javascript && found=1 || true
detect_java       && found=1 || true
detect_go         && found=1 || true
detect_csharp     && found=1 || true
detect_rust       && found=1 || true

if [[ $found -eq 0 ]]; then
    echo "unknown unknown"
fi
