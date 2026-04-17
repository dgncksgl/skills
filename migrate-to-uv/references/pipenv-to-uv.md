# Pipenv → uv

Read this when `scripts/detect-source.sh` reports `pipenv`.

## Input Files

- `Pipfile` (mandatory)
- `Pipfile.lock` (will be deleted after migration)

## Section Mapping

| Pipfile section                    | uv target                        |
|------------------------------------|----------------------------------|
| `[packages]`                       | `[project] dependencies`         |
| `[dev-packages]`                   | `[dependency-groups] dev`        |
| `[requires] python_version`        | `[project] requires-python`      |
| `[scripts]`                        | `[project.scripts]` (only for CLI entry points) |
| `[[source]] url`                   | `[tool.uv] index-url` / `extra-index-url` |

## Version Syntax Conversion

| Pipfile                              | uv                                |
|--------------------------------------|-----------------------------------|
| `"*"`                                | omit version specifier            |
| `"==1.2.3"`                          | `">=1.2.3"` (loosen unless exact pin requested) |
| `">=1.0"`                            | `">=1.0"` (unchanged)             |
| `{version = "*", extras = ["async"]}`| `"pkg[async]"`                    |
| `{git = "...", ref = "v1"}`          | `"pkg @ git+<url>@v1"`            |
| `{path = "../local", editable = true}` | `"pkg @ file:///absolute/../local"` |

## Generated `pyproject.toml` Skeleton

```toml
[project]
name = "<project-directory-name>"
version = "0.1.0"
requires-python = ">={DETECTED_PYTHON}"
dependencies = [
    "<pkg1>",
]

[dependency-groups]
dev = [
    "<dev-pkg1>",
]
```

## Files to Delete

- `Pipfile`
- `Pipfile.lock`
