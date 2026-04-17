# pip → uv

Read this when `scripts/detect-source.sh` reports `pip`.

## Input Files

- `requirements.txt` (mandatory)
- `requirements-dev.txt` (optional, becomes dev group)
- `setup.py` / `setup.cfg` / bare `pyproject.toml` (optional — extract metadata)

## Target `pyproject.toml`

```toml
[project]
name = "<project-directory-name>"
version = "0.1.0"
requires-python = ">={DETECTED_PYTHON}"
dependencies = [
    "<pkg1>",
    "<pkg2>>=<version>",
]

[dependency-groups]
dev = [
    "<dev-pkg1>",
]
```

## Conversion Rules

| `requirements.txt` line            | `pyproject.toml` entry                       |
|------------------------------------|----------------------------------------------|
| `pkg==1.2.3`                       | `"pkg>=1.2.3"` (loosen unless user wants exact pins) |
| `pkg>=1.0,<2.0`                    | `"pkg>=1.0,<2.0"` (preserve ranges)          |
| `pkg ~= 1.2`                       | `"pkg~=1.2"` (compatible release)            |
| `pkg[extras]==1.2`                 | `"pkg[extras]>=1.2"`                         |
| `-e .` / `--editable .`            | skip — uv handles the current project differently |
| `-r other.txt`                     | recurse into that file and merge lines       |
| Blank line / `# comment`           | skip                                         |
| `--index-url https://...`          | move to `[tool.uv] index-url`                |
| `--extra-index-url https://...`    | move to `[tool.uv] extra-index-url`          |
| `git+https://github.com/org/repo@tag` | `"repo @ git+https://github.com/org/repo@tag"` |
| `./path/to/local`                  | `"pkg @ file:///absolute/path"`              |

## Merging `setup.py` / `setup.cfg`

If one of these exists, extract and merge into `pyproject.toml`:

| setup.py / setup.cfg            | pyproject.toml                    |
|---------------------------------|-----------------------------------|
| `name=`                         | `[project] name`                  |
| `version=`                      | `[project] version`               |
| `description=`                  | `[project] description`           |
| `install_requires=[...]`        | `[project] dependencies`          |
| `python_requires=">=3.x"`       | `[project] requires-python`       |
| `extras_require={"dev": [...]}` | `[dependency-groups] dev`         |
| `entry_points={"console_scripts": ...}` | `[project.scripts]`       |

If both `setup.py`/`setup.cfg` AND `pyproject.toml` exist and disagree, the `pyproject.toml` values win.

## Files to Delete (after successful `uv sync`)

- `requirements.txt`
- `requirements-dev.txt`
- `setup.py`, `setup.cfg` (only if fully migrated — metadata preserved in `pyproject.toml`)
