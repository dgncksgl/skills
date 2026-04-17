# Poetry → uv

Read this when `scripts/detect-source.sh` reports `poetry`.

## Input Files

- `pyproject.toml` with `[tool.poetry]` sections (mandatory)
- `poetry.lock` (will be deleted after migration)

## Section Mapping

| Poetry section                         | uv target                         |
|----------------------------------------|-----------------------------------|
| `[tool.poetry] name`                   | `[project] name`                  |
| `[tool.poetry] version`                | `[project] version`               |
| `[tool.poetry] description`            | `[project] description`           |
| `[tool.poetry] authors`                | `[project] authors`               |
| `[tool.poetry] readme`                 | `[project] readme`                |
| `[tool.poetry.dependencies] python`    | `[project] requires-python`       |
| `[tool.poetry.dependencies] <pkg>`     | `[project] dependencies`          |
| `[tool.poetry.group.dev.dependencies]` | `[dependency-groups] dev`         |
| `[tool.poetry.group.<name>.dependencies]` | `[dependency-groups] <name>`   |
| `[tool.poetry.scripts]`                | `[project.scripts]` (only if a `[build-system]` is kept) |
| `[tool.poetry.extras]`                 | `[project.optional-dependencies]` |

## Version Syntax Conversion

| Poetry                                              | uv                                   |
|-----------------------------------------------------|--------------------------------------|
| `^1.2`                                              | `">=1.2,<2.0"`                       |
| `^1.2.3`                                            | `">=1.2.3,<2.0"`                     |
| `^0.3.1`                                            | `">=0.3.1,<0.4"` (major 0 → bump minor) |
| `~1.2`                                              | `">=1.2,<1.3"`                       |
| `~1.2.3`                                            | `">=1.2.3,<1.3"`                     |
| `">=1.0,<2.0"`                                      | `">=1.0,<2.0"` (unchanged)           |
| `"*"` or `"^*"`                                     | omit version specifier               |
| `{version = "^1.0", extras = ["async"]}`            | `"pkg[async]>=1.0,<2.0"`             |
| `{version = "^1.0", optional = true}`               | move to `[project.optional-dependencies]` |
| `{git = "...", tag = "v1"}`                         | `"pkg @ git+<url>@v1"`               |
| `{path = "../local"}`                               | `"pkg @ file:///absolute/../local"`  |

## Sections to Remove from `pyproject.toml`

After migration, delete these sections completely:

- `[tool.poetry]`
- `[tool.poetry.dependencies]`
- `[tool.poetry.group.*]`
- `[tool.poetry.extras]`
- `[tool.poetry.scripts]` (after moving to `[project.scripts]`)
- `[build-system]` (only if it references `poetry-core`)

## Files to Delete

- `poetry.lock`
