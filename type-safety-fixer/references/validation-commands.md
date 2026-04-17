# Type Check Validation Commands

Commands to verify type safety after fixes. Prefer `scripts/type-check.sh` which auto-dispatches; consult this file if the script cannot find a checker or the project uses a non-standard configuration.

## Primary Type Checkers

| Language   | Preferred                         | Fallback                             |
|------------|-----------------------------------|--------------------------------------|
| Python     | `pyright <files>` or `pyright .` | `mypy <files>` / `mypy --strict .` |
| TypeScript | `npx tsc --noEmit`                | `npx tsc --noEmit -p tsconfig.json`  |
| Java       | `mvn -q compile`                  | `./gradlew compileJava --quiet`      |
| Kotlin     | `./gradlew compileKotlin --quiet` | `kotlinc <files> -d /tmp/out`        |
| Go         | `go vet ./...`                    | `go build ./...`                     |
| C#         | `dotnet build --nologo -v q`      | `msbuild /v:q`                       |
| Rust       | `cargo check --quiet`             | `cargo clippy -q`                    |

## Python — Choosing the Checker

If both pyright and mypy are configured, prefer the one whose config file exists:

1. `pyrightconfig.json` → use `pyright`
2. `mypy.ini` / `pyproject.toml [tool.mypy]` → use `mypy`
3. `pyproject.toml [tool.pyright]` → use `pyright`
4. Otherwise default to `pyright` (matches PyCharm / VS Code default behaviour)

## Scoping the Check

Run the checker on **only the modified files** when possible — faster feedback and avoids noise from pre-existing unrelated warnings:

```bash
# Python - pyright on specific files
pyright src/app.py src/service.py

# Python - mypy on specific files
mypy src/app.py src/service.py

# TypeScript - tsc does not support file-scoped checks with tsconfig;
# use the project-level command and grep the relevant paths
npx tsc --noEmit | grep -E '^(src/app\.ts|src/service\.ts):'
```

## Differentiating Pre-existing vs New Warnings

After a fix, compare against the baseline:

```bash
pyright src/ > /tmp/after.txt
diff /tmp/before.txt /tmp/after.txt
```

A correct fix:
- Removes the targeted warning from `before.txt`
- Adds no new warnings to `after.txt`
- Introduces no secondary warnings such as `Cast may be a mistake...`

## Exit Codes to Expect

| Tool              | 0 means       | Non-zero means          |
|-------------------|---------------|-------------------------|
| pyright           | No errors     | Errors present          |
| mypy              | No errors     | Errors present          |
| tsc --noEmit      | No errors     | Errors present          |
| go vet            | No issues     | Issues present          |
| dotnet build      | Build success | Build failed            |
| cargo check       | Check success | Check failed            |
