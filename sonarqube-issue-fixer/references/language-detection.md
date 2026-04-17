# Language & Version Detection

This file lists the metadata files used to identify the primary language and its version for a project. Read it only when automatic detection via `scripts/detect-language.sh` is insufficient or ambiguous.

## Detection Sources

| Language   | Detect From                                                                         |
|------------|-------------------------------------------------------------------------------------|
| Java       | `pom.xml` (`maven.compiler.source`, `maven.compiler.target`), `build.gradle` (`sourceCompatibility`, `targetCompatibility`) |
| Kotlin     | `build.gradle.kts` (`jvmTarget`, `kotlinOptions`), `pom.xml` Kotlin plugin          |
| Python     | `pyproject.toml` (`python_requires`, `[tool.poetry.dependencies] python`), `setup.cfg`, `.python-version`, `runtime.txt` |
| TypeScript | `tsconfig.json` (`target`, `lib`, `strict`), `package.json` (`engines.node`)        |
| JavaScript | `package.json` (`engines.node`), `.nvmrc`, `.node-version`                          |
| Go         | `go.mod` (`go` directive)                                                           |
| C#         | `*.csproj` (`TargetFramework`, `LangVersion`), `global.json` (`sdk.version`)        |
| Ruby       | `Gemfile`, `.ruby-version`, `gems.rb`                                               |
| PHP        | `composer.json` (`require.php`)                                                     |
| Scala      | `build.sbt` (`scalaVersion`), `project/build.properties`                            |
| Swift      | `Package.swift` (`swift-tools-version`)                                             |
| Rust       | `Cargo.toml` (`edition`, `rust-version`), `rust-toolchain.toml`                     |

If no version can be determined, use the latest stable version rules for the language.

## Why Version Matters

The detected version affects which SonarQube rules apply:

- **Python 3.10+** allows `match` statements — older syntactic patterns are not issues.
- **Java 17+** sealed classes change inheritance rules (S110, S2176).
- **Java 21+** virtual threads change blocking-call guidance.
- **TypeScript** `strict: true` enables additional null-safety checks.
- **C# 8+** nullable reference types change null-check rules.
- **Go 1.22+** loop variable scoping change affects closure-in-loop rules.

## Multi-Language Projects

For polyglot repos, detect each language independently and apply the matching ruleset per file:

1. Group files by extension.
2. Detect the version for each language using the table above.
3. Scan each group with the appropriate ruleset.
