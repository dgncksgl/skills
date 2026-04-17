#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
cd "$ROOT"

detect_java() {
    if [[ -f pom.xml ]]; then
        local v
        v=$(grep -oE '<maven\.compiler\.(source|target|release)>[^<]+' pom.xml 2>/dev/null | head -1 | grep -oE '[0-9.]+' || true)
        [[ -z "$v" ]] && v=$(grep -oE '<java\.version>[^<]+' pom.xml 2>/dev/null | head -1 | grep -oE '[0-9.]+' || true)
        echo "java ${v:-unknown}"
        return 0
    fi
    if [[ -f build.gradle || -f build.gradle.kts ]]; then
        local v
        v=$(grep -oE '(source|target)Compatibility[[:space:]]*=?[[:space:]]*.?[0-9.]+' build.gradle* 2>/dev/null | head -1 | grep -oE '[0-9.]+' || true)
        [[ -z "$v" ]] && v=$(grep -oE 'jvmTarget[[:space:]]*=[[:space:]]*"[0-9.]+"' build.gradle* 2>/dev/null | head -1 | grep -oE '[0-9.]+' || true)
        echo "java ${v:-unknown}"
        return 0
    fi
    return 1
}

detect_kotlin() {
    if [[ -f build.gradle.kts ]] && grep -q "kotlin" build.gradle.kts 2>/dev/null; then
        local v
        v=$(grep -oE 'kotlinOptions[[:space:]]*\{[^}]*jvmTarget[[:space:]]*=[[:space:]]*"[0-9.]+"' build.gradle.kts 2>/dev/null | grep -oE '[0-9.]+$' || true)
        echo "kotlin ${v:-unknown}"
        return 0
    fi
    return 1
}

detect_python() {
    if [[ -f pyproject.toml ]]; then
        local v
        v=$(grep -oE 'python[[:space:]]*=[[:space:]]*"[^"]+' pyproject.toml | head -1 | grep -oE '[0-9.]+' || true)
        [[ -z "$v" ]] && v=$(grep -oE 'requires-python[[:space:]]*=[[:space:]]*"[^"]+' pyproject.toml | head -1 | grep -oE '[0-9.]+' || true)
        echo "python ${v:-unknown}"
        return 0
    fi
    if [[ -f .python-version ]]; then
        echo "python $(head -1 .python-version | grep -oE '[0-9.]+' || echo unknown)"
        return 0
    fi
    if [[ -f setup.cfg ]] && grep -q "python_requires" setup.cfg 2>/dev/null; then
        local v
        v=$(grep "python_requires" setup.cfg | grep -oE '[0-9.]+' | head -1 || true)
        echo "python ${v:-unknown}"
        return 0
    fi
    if compgen -G "*.py" >/dev/null 2>&1 || find . -maxdepth 3 -name "*.py" -not -path "*/.venv/*" -not -path "*/venv/*" -print -quit 2>/dev/null | grep -q .; then
        echo "python unknown"
        return 0
    fi
    return 1
}

detect_ts_js() {
    if [[ -f tsconfig.json ]]; then
        local v
        v=$(grep -oE '"target"[[:space:]]*:[[:space:]]*"[^"]+' tsconfig.json | head -1 | grep -oE '[a-zA-Z0-9]+$' || true)
        echo "typescript ${v:-unknown}"
        return 0
    fi
    if [[ -f package.json ]]; then
        local v
        v=$(grep -oE '"node"[[:space:]]*:[[:space:]]*"[^"]+' package.json | head -1 | grep -oE '[0-9.]+' || true)
        echo "javascript ${v:-unknown}"
        return 0
    fi
    return 1
}

detect_go() {
    if [[ -f go.mod ]]; then
        local v
        v=$(grep -E '^go[[:space:]]+[0-9.]+' go.mod | head -1 | grep -oE '[0-9.]+' || true)
        echo "go ${v:-unknown}"
        return 0
    fi
    return 1
}

detect_csharp() {
    if compgen -G "*.csproj" >/dev/null 2>&1 || find . -maxdepth 3 -name "*.csproj" -print -quit 2>/dev/null | grep -q .; then
        local file
        file=$(find . -maxdepth 3 -name "*.csproj" -print -quit)
        local v
        v=$(grep -oE '<TargetFramework>[^<]+' "$file" 2>/dev/null | head -1 | sed 's/<TargetFramework>//' || true)
        echo "csharp ${v:-unknown}"
        return 0
    fi
    return 1
}

detect_rust() {
    if [[ -f Cargo.toml ]]; then
        local v
        v=$(grep -oE 'edition[[:space:]]*=[[:space:]]*"[0-9]+"' Cargo.toml | head -1 | grep -oE '[0-9]+' || true)
        echo "rust edition-${v:-unknown}"
        return 0
    fi
    return 1
}

detected=()
capture() {
    local out
    if out=$("$1" 2>/dev/null); then
        detected+=("$out")
    fi
}

capture detect_java
capture detect_kotlin
capture detect_python
capture detect_ts_js
capture detect_go
capture detect_csharp
capture detect_rust

if [[ ${#detected[@]} -eq 0 ]]; then
    echo "unknown unknown"
    exit 0
fi

printf '%s\n' "${detected[@]}"
