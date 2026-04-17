# Conda → uv

Read this when `scripts/detect-source.sh` reports `conda`.

## Input Files

- `environment.yml` (primary)
- `conda-lock.yml` (optional — do NOT copy; uv produces its own `uv.lock`)

## Splitting Dependencies

`environment.yml` mixes conda-channel packages and a pip section. Separate them:

```yaml
dependencies:
  - python=3.11
  - numpy=1.26       # conda-channel
  - scipy            # conda-channel
  - pytorch          # conda-channel (has PyPI equivalent)
  - pip
  - pip:
      - fastapi      # already pip
      - uvicorn
```

## Conversion Rules

| Source entry type                 | Destination                               |
|-----------------------------------|-------------------------------------------|
| `python=<ver>`                    | `[project] requires-python = ">=<ver>"`   |
| `pkg=<ver>` in conda-channel, **has PyPI equivalent** | `[project] dependencies` with `">=<ver>"` |
| `pkg` under `- pip:`              | `[project] dependencies`                  |
| Conda-only package (no PyPI equivalent) | Warn the user — see below            |

## Version Syntax Conversion

| Conda                  | uv                          |
|------------------------|-----------------------------|
| `pkg=1.2`              | `"pkg>=1.2"`                |
| `pkg=1.2.*`            | `"pkg>=1.2,<1.3"`           |
| `pkg>=1.2,<2`          | `"pkg>=1.2,<2"`             |
| `pkg` (no version)     | `"pkg"`                     |

## Warning Template for Conda-Only Packages

After inspection, if any package has no PyPI equivalent, emit:

```
WARNING: The following conda-only packages have no PyPI equivalent.
Install them separately via system package manager or find PyPI
alternatives:
- <package-name-1>
- <package-name-2>
```

Common conda-only packages to watch for: `mkl`, `libffi`, `openblas`, `hdf5-static`, proprietary bioinformatics builds.

## Files

- Rename `environment.yml` → `environment.yml.bak` (keep as reference, do not delete)
- `conda-lock.yml` can be removed
