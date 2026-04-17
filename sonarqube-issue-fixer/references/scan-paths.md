# Scannable vs Excluded Paths

This file defines which directories and file types are in scope for the SonarQube scan. Read it when `scripts/scan-sources.sh` cannot confidently decide, or when adapting to a non-standard project layout.

## Include — Source Directories

Scan only directories that contain first-party source logic.

| Language      | Typical Source Dirs                                            |
|---------------|----------------------------------------------------------------|
| Java          | `src/main/java`, `app/src/main/java` (Android)                 |
| Kotlin        | `src/main/kotlin`, `app/src/main/kotlin`                       |
| Python        | Top-level packages (dirs containing `__init__.py`), `src/<pkg>/`, `<pkg>/` |
| TypeScript    | `src/`, `lib/`, `app/`, `packages/*/src/` (monorepos)          |
| JavaScript    | `src/`, `lib/`, `app/`                                         |
| Go            | All `.go` files under the module root (excluding vendored)    |
| C#            | Directories containing `*.cs` outside `bin/`, `obj/`, `Test*/`|
| Ruby          | `lib/`, `app/`                                                 |
| PHP           | `src/`, `app/`, `lib/`                                         |
| Scala         | `src/main/scala`                                               |
| Rust          | `src/`                                                         |
| Generic       | Any directory containing source files for the detected language|

## Exclude — Never Scan, Never Modify

Skip these entirely. They contain third-party code, build output, IDE state, or non-source content.

### Directories

```
.idea/          .vscode/        .vs/            .fleet/
.venv/          venv/           env/            .env/
node_modules/   bower_components/
vendor/         __pycache__/    .mypy_cache/    .pytest_cache/    .tox/
.git/           .svn/           .hg/
build/          dist/           target/         out/          bin/          obj/
.gradle/        .mvn/           .settings/      .next/        .nuxt/        .output/
coverage/       .nyc_output/    htmlcov/
cmake-build-*/  .cmake/
Pods/           DerivedData/
```

### File Types (excluded from scanning AND from modification)

```
# Config / markup / data
*.xml       *.yaml      *.yml       *.json      *.toml      *.properties
*.conf      *.cfg       *.ini       *.env       *.env.*

# Docs / plain text
*.md        *.txt       *.rst       *.adoc      *.csv       *.tsv

# Web assets (not logic)
*.html      *.htm       *.css       *.scss      *.less      *.sass

# Query / schema
*.sql       *.graphql   *.gql       *.proto

# Shell / build scripts
*.sh        *.bash      *.zsh       *.bat       *.cmd       *.ps1
Dockerfile  docker-compose*  Makefile  Jenkinsfile  *.gradle  *.sbt

# Lock / manifest files
*.lock      package-lock.json   yarn.lock   poetry.lock   Gemfile.lock
Cargo.lock  composer.lock

# Generated code
*.pb.go     *_pb2.py    *_grpc.py   *_generated.*   *.g.dart
*.freezed.dart   *.g.cs   *.designer.cs

# Binary / media
*.png  *.jpg  *.jpeg  *.gif  *.svg  *.ico  *.pdf
*.jar  *.war  *.ear   *.class *.pyc  *.so   *.dll  *.dylib
*.zip  *.tar  *.gz    *.7z   *.rar
```

## Exception — Read-Only Inspection

Dependency directories (`.venv/`, `node_modules/`, `vendor/`) may be **read** to discover exception hierarchies or library contracts (see `SKILL.md` → Exception Narrowing). They must never be **modified** or included in the scan target list.
