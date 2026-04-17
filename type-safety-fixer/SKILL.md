---
name: type-safety-fixer
description: >-
  Fix IDE type checking warnings ("Expected type X, got Y") across any
  programming language. Inspects library source code to find the correct types,
  then applies minimal fixes such as type annotations, casts, constructors,
  or narrowing. Use when the user asks (in English or Turkish) to fix type
  warnings, type mismatches, "Expected type" errors, type annotation issues,
  type safety problems, "tip uyarılarını gider", "tip hatalarını düzelt",
  "type annotation sorunlarını çöz", "tip güvenliği problemlerini çöz",
  "tip anotasyonlarını düzelt", or "beklenen tip" hataları.
---

# Type Safety Fixer

Fix "Expected type X, got Y" warnings reported by IDE type checkers (Pyright, mypy, tsc, IntelliJ, Roslyn, gopls, rustc, …). Operate only on first-party source code; read library sources to discover the correct types, but never modify them.

## Workflow

```
- [ ] Step 1: Detect language and type checker
- [ ] Step 2: Scope the source files under review
- [ ] Step 3: Collect current type warnings
- [ ] Step 4: Research the correct type from library source
- [ ] Step 5: Apply the minimal fix
- [ ] Step 6: Validate and report
```

---

## Step 1 — Detect Language and Type Checker

Run:

```bash
bash scripts/detect-type-checker.sh
```

Each line is `<language> <checker>`. Polyglot repos emit multiple lines; handle each group independently. If the output is `unknown unknown` or the configuration is unusual, map the project manually using the table in [references/validation-commands.md](references/validation-commands.md).

Version matters (e.g. Python 3.10 `match`, TS `strict`, C# 8+ NRT). When unclear, assume the latest stable version's rules.

---

## Step 2 — Scope Source Files

Limit the work to first-party source code. Never modify:

- Dependency directories (`.venv/`, `node_modules/`, `vendor/`, module cache, JARs)
- Build output (`build/`, `dist/`, `target/`, `bin/`, `obj/`, `out/`)
- IDE / VCS state (`.idea/`, `.vscode/`, `.git/`)
- Generated code (`*_pb2.py`, `*.pb.go`, `*_generated.*`, `*.g.cs`, `*.freezed.dart`, …)

**Exception — read-only inspection is allowed:** dependency directories may (and usually must) be **read** to discover the correct type definitions in Step 4. Read, never write.

---

## Step 3 — Collect Type Warnings

A type warning reduces to three pieces:

1. **Expected type** — what the API requires
2. **Actual type** — what the code supplied
3. **Location** — file + line

The full set of warning formats per checker (Pyright, mypy, tsc, javac, kotlinc, gopls, Roslyn, rustc, …) is in [references/warning-formats.md](references/warning-formats.md). Extract the triplet from each warning before moving to Step 4.

---

## Step 4 — Research the Correct Type (Critical)

**Do not guess types. Look them up.**

### 4.1 Find the Expected Type Definition

Given a warning "Expected 'Foo', got 'Bar'":

1. **Locate `Foo`** in the library's source inside the dependency directory:
   - Python → `.venv/lib/*/site-packages/<library>/` — search for `class Foo`, `Foo = TypedDict(...)`, `Foo: TypeAlias = ...`
   - TypeScript → `node_modules/<library>/` or `node_modules/@types/<library>/` — `.d.ts` definitions
   - Java → JAR sources, IDE-provided decompiled class, or Maven Central sources JAR
   - Go → module cache (`~/go/pkg/mod/...`) or `vendor/`
   - Rust → `~/.cargo/registry/src/.../<crate>/src/`
   - C# → NuGet package cache or reference assemblies

2. **Classify `Foo`:**

   | Kind             | What the fix must produce                        |
   |------------------|--------------------------------------------------|
   | Class / dataclass| An instance via the constructor                  |
   | `TypedDict`      | A dict-shaped literal using `Foo(...)` or `{ ... }` matching required/optional keys |
   | Pydantic model   | `Foo(**kwargs)` or `Foo.model_validate(...)`     |
   | Union            | A value of **one** of the member types           |
   | Protocol / interface | An object exposing the required members      |
   | Generic          | Supply the correct type parameter                |
   | Literal          | One of the literal values                        |

3. **Classify why `Bar` is incompatible** — missing keys, wrong container shape, nullable vs non-nullable, literal mismatch, subtype vs supertype.

### 4.2 Fix Strategy Selection

Pick the **least invasive** strategy that preserves runtime behaviour:

| Mismatch                                | Fix |
|-----------------------------------------|-----|
| `dict` → `TypedDict`                    | Construct the TypedDict using the library's own type |
| `list[dict]` → `list[TypedDict]`        | Construct TypedDict objects inside the list |
| `None` → non-None                       | Narrow with `isinstance` / `assert is not None` / default value |
| Mixed-union → specific type             | Extract to a local and `assert isinstance(...)` |
| `Any` → specific                        | Add explicit annotation; convert at the boundary |
| Supertype → subtype                     | Narrow with `isinstance` |
| Subtype where supertype is expected     | Widen the annotation |
| Optional → non-optional parameter       | Default value, narrowing, or `assert` |
| Literal mismatch                        | `assert value in (...)` to narrow |

### 4.3 Forbidden: `cast()` Between Unrelated Types

Type checkers emit a secondary warning:

> `Cast may be a mistake because X and Y are not in the same inheritance hierarchy.`

This applies across all languages — Python `typing.cast`, TS `as`, Java `(X)`, C# `(X)`. For any mismatch that is **not** a supertype↔subtype relationship, use a constructor, narrowing, or a default value — never a cast.

---

## Step 5 — Apply the Fix

### Constraints

- **Only touch lines that produce a type warning.** Do not refactor unrelated code.
- **Every new type must come from the library source or the standard library** — never invent a type name.
- **Preserve runtime behaviour.**
- **Never start a new identifier with `_`.** Follow the language's idiomatic convention (`camelCase` / `snake_case` / `PascalCase`).
- **Never silence with `# type: ignore` / `@ts-ignore` / `@SuppressWarnings` without a one-line justification comment.**

### Pattern Catalog

Concrete code examples per language (Python, TypeScript, Java, Kotlin, Go, C#) — including the forbidden anti-patterns — are in [references/fix-patterns.md](references/fix-patterns.md). Open it when you need to reproduce a pattern.

---

## Step 6 — Validate and Report

### 6.1 Run the Type Checker

```bash
bash scripts/type-check.sh <optional files...>
```

Dispatches to the correct checker (pyright / mypy / tsc / mvn / gradle / go vet / dotnet build / cargo check). Manual fallback commands and scoping tricks (e.g. checking only modified files, diffing against a baseline) are in [references/validation-commands.md](references/validation-commands.md).

### 6.2 Re-inspect Modified Files

For each file you touched:

- The targeted warning is gone.
- No new type warnings appeared (especially the `Cast may be a mistake...` secondary warning — if it did, the fix used a cast and must be redone with a constructor or narrowing).
- Runtime behaviour is preserved (no early returns added, no exceptions swallowed).

### 6.3 Cascade Check

Adding a type annotation or importing a new type can create new warnings upstream (callers) or downstream (methods using the value). After every file-level fix, re-check its immediate neighbours:

- Files that import the modified symbol
- Files imported by the modified file if types flowed inward

### 6.4 Summary Report

```
## Type Safety Fix Report

Project: <name>
Language: <language> <version>
Type Checker: <pyright|mypy|tsc|…>
Files Scanned: <n>
Warnings Found: <n>
Warnings Fixed: <n>
Warnings Skipped: <n>

### Fixed
| # | File | Line | Warning | Fix Applied |
|---|------|------|---------|-------------|
| 1 | src/app.py | 12 | Expected 'Prompt', got 'dict' | Constructed Prompt TypedDict |

### Skipped (require manual review)
| # | File | Line | Reason |
|---|------|------|--------|
| 1 | … | … | Requires architectural change beyond a type fix |
```

---

## Additional Resources

- Warning formats per IDE / checker: [references/warning-formats.md](references/warning-formats.md)
- Fix patterns per language (with code): [references/fix-patterns.md](references/fix-patterns.md)
- Manual type-check commands and scoping: [references/validation-commands.md](references/validation-commands.md)
