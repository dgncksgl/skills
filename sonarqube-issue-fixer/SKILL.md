---
name: sonarqube-issue-fixer
description: >-
  Scan project source code for SonarQube rule violations (bugs, vulnerabilities,
  code smells, security hotspots, cyclomatic / cognitive complexity) and fix
  them automatically. Language-agnostic: Java, Kotlin, Python, TypeScript,
  JavaScript, Go, C#, Ruby, PHP, Scala, Rust, Swift.
  Use when the user asks (in English or Turkish) to "fix sonar warnings",
  "resolve code smells", "clean up static analysis", "reduce cyclomatic or
  cognitive complexity", "improve code quality", "fix SonarQube issues",
  "sonar sorunlarını çöz", "sonar uyarılarını düzelt",
  "sonarqube issue'larını çöz", "kod kokularını gider",
  "statik analiz uyarılarını temizle", "kod kalitesini artır",
  "karmaşıklığı azalt", or references a Sonar rule ID such as S1854,
  S1192, S3776, S2095, S2068.
  Use proactively after a SonarQube / SonarCloud report is shared or after
  an implementation/refactor step completes.
  Do not use for pure formatting, import sorting, single-file typo fixes,
  or for editing config/markup files (XML, YAML, JSON, Markdown).
---

# SonarQube Issue Fixer

Detect and fix SonarQube rule violations across any programming language. Operate only on first-party source code; never modify generated code, config, markup, build output, or dependency directories.

## Workflow

```
- [ ] Step 1: Detect project language(s) and version
- [ ] Step 2: List scannable source files
- [ ] Step 3: Scan for violations (by category)
- [ ] Step 4: Apply fixes
- [ ] Step 5: Validate and report
```

---

## Step 1 — Detect Language and Version

Run:

```bash
bash scripts/detect-language.sh
```

Each output line is `<language> <version>`. Multiple lines indicate a polyglot repo — process each language independently.

If detection fails, prompts are unavailable, or the metadata is unusual, consult [references/language-detection.md](references/language-detection.md).

Version matters because rule applicability changes per version (e.g. Java 17 sealed classes, Python 3.10 `match`, TS `strict` mode). When unknown, assume the latest stable version's ruleset.

---

## Step 2 — List Scannable Source Files

Run:

```bash
bash scripts/scan-sources.sh
```

The script returns only first-party source files with relevant extensions, with all of the following excluded: build output, IDE state, virtual envs, `node_modules/`, `vendor/`, generated code, and any non-logic file (XML, YAML, JSON, Markdown, lockfiles, shell scripts, binary assets).

For the full include/exclude contract — and for adapting to non-standard layouts — see [references/scan-paths.md](references/scan-paths.md).

**Never** modify files that the scanner excludes. Dependency directories may be **read** (Step 4, Exception Narrowing) but never written to.

---

## Step 3 — Scan for Violations

Inspect each file for the five SonarQube categories. For the full rule catalog with rule IDs per language, see [references/rules-reference.md](references/rules-reference.md).

### 3.1 Bugs (Reliability)

Code that is demonstrably wrong or will misbehave:

- Null / None / nil dereferences
- Wrong equality (`==` vs `.equals()` in Java; `is` vs `==` in Python)
- Unclosed resources (streams, connections, files)
- Off-by-one errors
- Dead code after `return` / `break` / `throw`
- Conditions always true or always false
- Identical expressions on both sides of an operator

### 3.2 Vulnerabilities (Security)

- Hardcoded credentials or secrets
- SQL injection via string concatenation
- Unvalidated user input in dangerous operations
- Weak crypto (MD5 / SHA1 for security; DES; ECB)
- Disabled certificate validation
- Path traversal, SSRF, XSS, command injection

### 3.3 Code Smells (Maintainability)

- Cyclomatic complexity > 15
- Cognitive complexity > 15
- Too many parameters (> 7)
- Nesting depth > 3
- Duplicated string literals (≥ 3 occurrences)
- Unused imports / variables / parameters
- Empty `catch` / `except` blocks that swallow errors
- Over-broad catches (`catch (Exception)`, `except Exception`) — see **Exception Narrowing** below
- Methods longer than ~80 logical lines
- Boolean parameters that indicate the method should be split
- Mutable global / class-level state without synchronization

### 3.4 Security Hotspots

Flag for manual review (do not silently "fix"):

- Regex patterns (ReDoS risk)
- Cookie flags (`Secure`, `HttpOnly`, `SameSite`)
- CORS configuration
- Logging of sensitive data
- Pseudorandom number generators used for security

### 3.5 Complexity

- **Cyclomatic:** count `if`, `for`, `while`, `case`, `catch`, `&&`, `||`, ternary. Fix when > 15.
- **Cognitive:** penalise nesting and breaks in linear flow. Fix when > 15.
- **Reduce by:** extracting methods, early returns / guard clauses, dispatch maps, polymorphism, intermediate named booleans.

---

## Step 4 — Fix Detected Issues

### Naming

- **Never** start a new identifier (function, variable, class, method, constant) with `_`.
- Use the language's idiomatic convention: `camelCase` (Java / Kotlin / C# / TS), `snake_case` (Python), exported `PascalCase` / unexported `camelCase` (Go).

### Fix Strategies

**Bugs** — add null / Optional handling; use `.equals()` or identity checks correctly; try-with-resources / context managers; remove dead code.

**Vulnerabilities** — replace hardcoded secrets with env / secret store lookups; parameterized queries; input validation; upgrade weak algorithms (→ SHA-256+, bcrypt / argon2 for passwords).

**Code Smells** — extract long methods; remove unused imports and variables; handle or rethrow in empty catches; replace magic literals with named constants; parameter objects for wide signatures; flatten nesting with guard clauses; narrow over-broad catches.

**Complexity** — early returns; extract predicates into well-named booleans; table-driven dispatch; split large `switch` / `match` via strategy or lookup map.

### Exception Narrowing

When a `catch (Exception)` / `except Exception` is encountered, **do not keep it as is**:

1. Identify external libraries called inside the `try` block.
2. Inspect the library's exception hierarchy — read-only — in the appropriate location:
   - Python: `.venv/lib/*/site-packages/<lib>/exceptions.py` (or `errors.py`, `_exceptions.py`)
   - Java: sources in the installed JAR or IDE-provided source
   - TS / JS: custom error classes under `node_modules/<lib>/`
   - Go: `errors.go` or sentinel errors under `vendor/` or the module cache
3. Find the library's base exception class (well-designed libraries define one).
4. Add the standard language exceptions that the `try` body's operations could actually raise (dict / list access → `KeyError` / `IndexError`; IO → `IOError`; conversions → `ValueError` / `TypeError`; etc.).
5. Replace the broad catch with `(LibraryBaseException, StandardException1, StandardException2)`.
6. Never catch unrecoverable errors — let them propagate.

Reading dependency directories for this purpose is explicitly allowed; modifying them is not.

### Fix Principles

1. Preserve observable behaviour.
2. Minimal change — only what resolves the issue.
3. One issue per focused edit.
4. Match surrounding style (indentation, quotes, braces).
5. A fix must not introduce a new SonarQube issue.

---

## Step 5 — Validate and Report

### 5.1 Compile / Lint

```bash
bash scripts/lint.sh
```

Dispatches to the project's build system (Maven, Gradle, tsc, py_compile, go vet, dotnet build, cargo check, …). If the script cannot find a build system, see [references/validation-commands.md](references/validation-commands.md) for manual commands.

### 5.2 Run Tests

```bash
bash scripts/run-tests.sh
```

Same dispatch logic for test runners (mvn test, gradle test, pytest, jest, go test, dotnet test, cargo test, …).

### 5.3 Re-inspect Modified Files

For each changed file verify:

- The original issue is gone.
- No new SonarQube-detectable issue has been introduced.
- The file still compiles and passes linting.
- **Cascade unused check:** when a variable, import, or assignment is removed, re-check the scope — any variable whose only reader was the deleted code is now unused and must be removed in the same pass. Repeat until stable.

### 5.4 Summary Report

Produce a final report:

```
## SonarQube Fix Report

Project: <name>
Language: <language> <version>
Files Scanned: <n>
Issues Found: <n>
Issues Fixed: <n>
Issues Skipped (manual review): <n>

### Fixed
| # | File | Rule | Severity | Description |
|---|------|------|----------|-------------|
| 1 | src/Service.java | S1854 | Major | Removed unused variable `temp` |

### Skipped (require manual review)
| # | File | Rule | Reason |
|---|------|------|--------|
| 1 | … | … | Behavioural change risk too high |
```

---

## Additional Resources

- Language & version detection table: [references/language-detection.md](references/language-detection.md)
- Scan include / exclude contract: [references/scan-paths.md](references/scan-paths.md)
- Full per-language rule catalog: [references/rules-reference.md](references/rules-reference.md)
- Manual lint / test commands per language: [references/validation-commands.md](references/validation-commands.md)
