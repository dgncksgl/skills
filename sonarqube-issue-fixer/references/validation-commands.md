# Validation Commands per Language

Reference for Step 5 (Validate Fixes). Prefer running `scripts/lint.sh` and `scripts/run-tests.sh` which auto-dispatch; consult this file only if a command fails or the build system is non-standard.

## Compile / Lint

| Language      | Primary Command                         | Fallback                        |
|---------------|-----------------------------------------|---------------------------------|
| Java (Maven)  | `mvn -q compile`                        | `javac -d /tmp/out <files>`     |
| Java (Gradle) | `./gradlew compileJava --quiet`         | `gradle compileJava`            |
| Kotlin        | `./gradlew compileKotlin --quiet`       | `kotlinc <files> -d /tmp/out`   |
| Python        | `python -m py_compile <file>` per file  | `python -m compileall -q <dir>` |
| TypeScript    | `npx tsc --noEmit`                      | `npx tsc -p tsconfig.json --noEmit` |
| JavaScript    | `npx eslint <files>`                    | `node --check <file>`           |
| Go            | `go vet ./...`                          | `go build ./...`                |
| C#            | `dotnet build --nologo -v q`            | `msbuild /v:q`                  |
| Ruby          | `ruby -c <file>`                        | `rubocop <file>` (if configured) |
| Scala         | `sbt compile`                           | —                               |
| Rust          | `cargo check --quiet`                   | `cargo clippy -q`               |
| PHP           | `php -l <file>`                         | `./vendor/bin/phpstan analyse`  |

## Run Tests

| Language      | Primary Command                         | Fallback                        |
|---------------|-----------------------------------------|---------------------------------|
| Java (Maven)  | `mvn -q test`                           | `mvn surefire:test`             |
| Java (Gradle) | `./gradlew test --quiet`                | `gradle test`                   |
| Kotlin        | `./gradlew test --quiet`                | —                               |
| Python        | `pytest -q`                             | `python -m unittest discover -q`|
| TypeScript/JS | `npm test --silent`                     | `npx jest --silent`             |
| Go            | `go test ./...`                         | —                               |
| C#            | `dotnet test --nologo -v q`             | —                               |
| Ruby          | `bundle exec rspec --format progress`   | `ruby -Ilib -Itest test/*.rb`   |
| Scala         | `sbt test`                              | —                               |
| Rust          | `cargo test --quiet`                    | —                               |
| PHP           | `./vendor/bin/phpunit`                  | —                               |

## Notes

- Respect the project's existing build system; prefer `./gradlew`/`./mvnw` wrappers if present.
- If neither `pom.xml` nor `build.gradle` exists for a Java/Kotlin project, fall back to direct compiler invocation.
- For monorepos, run the commands at the package level, not the repo root.
