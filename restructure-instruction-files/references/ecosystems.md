# Stack-Specific Globs and Hook Candidates

Read this when choosing `paths:` patterns for a stack (Step 5) or proposing hooks (Step 7). Treat every pattern and command here as a starting point: confirm it against the repo's real layout and the way the project actually runs its tools.

## `paths:` patterns by stack

| Stack | Source | Tests | Build / config |
|---|---|---|---|
| Python | `**/*.py` | `tests/**/*.py`, `**/test_*.py` | `pyproject.toml` |
| Java | `**/*.java` | `**/src/test/**/*.java` | `**/pom.xml`, `**/build.gradle*` |
| Kotlin / Android | `**/*.{kt,kts}` | `**/src/test/**`, `**/src/androidTest/**` | `**/build.gradle.kts`, `gradle/libs.versions.toml` |
| Android resources | `**/src/main/res/**/*.xml`, `**/AndroidManifest.xml` | — | — |
| C# / .NET | `**/*.cs` | `**/*Tests/**/*.cs`, `**/*.Tests/**` | `**/*.csproj`, `*.sln`, `Directory.Build.props` |
| Swift / iOS | `**/*.swift` | `**/*Tests/**/*.swift` | `Package.swift`, `**/*.xcconfig` |
| SwiftUI views (if folder exists) | `**/Views/**/*.swift` | — | — |
| TypeScript / JS | `**/*.{ts,tsx,js,jsx}` | `**/*.{test,spec}.{ts,tsx}` | `package.json`, `tsconfig*.json` |
| React components | `src/components/**/*.tsx` | — | — |
| Go | `**/*.go` | `**/*_test.go` | `go.mod` |
| Rust | `**/*.rs` | `tests/**/*.rs` | `**/Cargo.toml` |
| Flutter / Dart | `lib/**/*.dart` | `test/**/*.dart` | `pubspec.yaml` |
| SQL migrations | `**/migrations/**`, `**/db/migrate/**` | — | — |
| Django / Alembic migrations | `**/migrations/*.py`, `alembic/versions/*.py` | — | — |
| CI | `.github/workflows/*.yml`, `.gitlab-ci.yml` | — | — |

Split by **topic**, not by line count: language style → `<language>.md`; architecture details → `architecture.md`; tests → `testing.md`; UI layer → `ui.md`; database → `database.md`; CI and release → `ci.md`. A monorepo module gets its own file scoped to `<module>/**`.

## Hook candidates

A rule becomes a hook only when it must hold every time and a script can check it. The formatter cells show only the command core: wrap each one as the notes below say (extension and existence guards, `|| true; exit 0`). Propose; install only after approval, following the bundled `update-config` skill (pipe-test, `jq -e` check, live proof).

| Rule in the text | Hook | Example command core |
|---|---|---|
| "Use only pnpm / uv / poetry / yarn" | `PreToolUse`, matcher `Bash`, exit 2 blocks | see the command below the table |
| "Format after editing" (Python) | `PostToolUse`, matcher `Edit\|Write\|MultiEdit` | `uv run black -q "$f"` or `ruff format "$f"` |
| Format (TS/JS) | same | `npx prettier --write "$f"` |
| Format (Go / Rust) | same | `gofmt -w "$f"` / `rustfmt "$f"` |
| Format (C#) | same | `dotnet format --include "$f"` |
| Format (Kotlin / Java) | same | `ktlint -F "$f"` or `google-java-format -i "$f"`. A build-tool goal (Gradle `spotlessApply`/`ktlintFormat`, Maven `spotless:apply`) formats the whole project and touches files Claude did not edit: propose it only as a `Stop` hook with that caveat, or not at all |
| Format (Swift) | same | `swiftformat "$f"` or `swift format -i "$f"` |
| "Never edit generated code / `Pods/`" (no exceptions) | `PreToolUse`, matcher `Edit\|Write` | path check on `.tool_input.file_path`, exit 2. It does not see Bash writes (`sed -i`, `>`); say so. A rule with a condition a script cannot see ("never edit an *applied* migration") stays a path rule |
| "Run tests before finishing" | `Stop` | the project's test command; mind the block cap |

Package-manager block, for example "pnpm only":

```bash
jq -r '.tool_input.command // empty' | grep -qE '(^[[:space:]]*|[;&|][[:space:]]*)(npm|yarn)([[:space:]]|$)' && { echo "Blocked: use pnpm." >&2; exit 2; } || exit 0
```

For uv only, the pattern also needs `python -m pip`:

```bash
jq -r '.tool_input.command // empty' | grep -qE '(^[[:space:]]*|[;&|][[:space:]]*|-m[[:space:]]+)(pip3?|poetry|pipenv)([[:space:]]|$)' && { echo "Blocked: use uv." >&2; exit 2; } || exit 0
```

## Hook rules learned the hard way

- Read the file path with `jq -r '.tool_input.file_path // .tool_response.filePath // empty'` and loop with `{ read -r f; …; }`, never unquoted `xargs`.
- Guard by extension (`case "$f" in *.py) … ;; esac`) and by existence (`[ ! -f "$f" ] || …`).
- A formatter hook always ends with exit 0 (`… || true; exit 0`). Some CLIs exit 2 on a syntax or usage error (`gofmt`, `black` on a missing file), and exit 2 from a hook is treated as a blocking error.
- A blocking regex must not catch harmless commands: test both sides, e.g. block `pip install x`, `cd a && pip install x`, `python -m pip …`, but allow `uv pip …`, `grep pip README.md`, `git commit -m "remove pip"`, `pipx`.
- Run the tool the way the project runs it (`uv run`, `npx`, `./gradlew`, `dotnet`), and check it is installed (`command -v`) and actually runs before proposing it. A hook you cannot test here is proposed as "not installed: cannot verify", never installed blind.
- Run commands from `"${CLAUDE_PROJECT_DIR:-.}"` so the project's config file is found.
- Formatter hook test cases. Each one must exit 0, and only the target file may change:
  - a valid but badly formatted target file: it gets formatted;
  - a target file with a syntax error: it is left unchanged;
  - a file of another type: it is left untouched;
  - a path that does not exist;
  - empty input;
  - a path with spaces.
- Project hooks go in `.claude/settings.json` (shared); personal ones in `.claude/settings.local.json`. Read the file first and merge; never replace existing hooks.
