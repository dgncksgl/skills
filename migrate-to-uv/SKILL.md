---
name: migrate-to-uv
description: >-
  Migrate any Python project from pip, Poetry, Pipenv, or Conda to the uv
  package manager. Detects the current source, converts dependency
  configuration to a PEP 621 `pyproject.toml`, installs with `uv sync`,
  verifies the project still runs, and updates CI workflows.
  Use when the user asks (in English or Turkish) to "migrate to uv",
  "switch to uv", "convert to uv", "set up uv",
  "poetry'den uv'ye geç", "pip'ten uv'ye geç", "pipenv'den uv'ye geç",
  "conda'dan uv'ye geç", "paket yöneticisini uv'ye çevir",
  "uv'ye geçiş yap", "uv package manager'a geçir",
  "dependency yönetimini uv'ye taşı".
  Do not use for creating a brand-new Python project from scratch (use
  `uv init` directly), for upgrading an already-uv project, or for
  migrating to tools other than uv (rye, pdm, hatch).
---

# Migrate Python Project to uv

Detect the current package manager, convert all dependency configuration to a uv-compatible `pyproject.toml` (PEP 621), install dependencies with `uv sync`, and verify the project still runs.

## Workflow

```
- [ ] Step 1: Detect current package manager
- [ ] Step 2: Detect Python version
- [ ] Step 3: Install uv (if missing)
- [ ] Step 4: Convert dependencies
- [ ] Step 5: Create supporting files
- [ ] Step 6: uv sync
- [ ] Step 7: Clean up old files
- [ ] Step 8: Verify
- [ ] Step 9: Update CI (if applicable)
- [ ] Step 10: Report summary
```

---

## Step 1 — Detect Current Package Manager

```bash
bash scripts/detect-source.sh
```

Output is one of: `uv`, `poetry`, `pipenv`, `conda`, `pip`, `unknown`.

- `uv` → Already migrated. Inform the user and stop.
- `unknown` → Ask the user which manager is in use, or manually inspect the repo.

## Step 2 — Detect Python Version

```bash
bash scripts/detect-python-version.sh
```

Output is a version string like `3.13`. Store as `DETECTED_PYTHON`. If `unknown`, ask the user which Python version to target.

## Step 3 — Install uv

```bash
uv --version 2>/dev/null || {
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source "$HOME/.local/bin/env"
}
uv --version
```

## Step 4 — Convert Dependencies

Open only the reference that matches the detected source. Each reference contains full section mapping, version syntax conversion, and the list of files to delete in Step 7:

| Detected source | Reference |
|-----------------|-----------|
| `pip`           | [references/pip-to-uv.md](references/pip-to-uv.md)     |
| `poetry`        | [references/poetry-to-uv.md](references/poetry-to-uv.md) |
| `pipenv`        | [references/pipenv-to-uv.md](references/pipenv-to-uv.md) |
| `conda`         | [references/conda-to-uv.md](references/conda-to-uv.md)   |

Apply the conversion to produce a target `pyproject.toml`.

## Step 5 — Create Supporting Files

**`.python-version`** (create or overwrite with the detected version):

```
{DETECTED_PYTHON}
```

**`.gitignore`** — ensure these entries exist (append if missing, do not duplicate):

```
.venv/
__pycache__/
*.pyc
.env
.env.*
!.env.example
```

`uv.lock` must **not** appear in `.gitignore` — it is committed for reproducible builds.

## Step 6 — Install Dependencies

```bash
rm -rf .venv
uv sync
```

If `uv sync` fails, read the error and apply one of:

- Package not found → verify the name on PyPI; adjust in `pyproject.toml`.
- Version conflict → loosen constraints.
- Python version mismatch → update `requires-python`, or install the correct Python: `uv python install {DETECTED_PYTHON}`.

Re-run `uv sync` until it succeeds. Verify the lock file was produced:

```bash
ls -la uv.lock
```

## Step 7 — Clean Up Old Files

Delete the files listed under "Files to Delete" in the reference used in Step 4. Do not delete files until Step 6 succeeded.

## Step 8 — Verify

Run an import smoke test using the project's top-level dependencies:

```bash
uv run python -c "import <main_dep_1>; import <main_dep_2>; print('imports OK')"
```

Replace `<main_dep_*>` with the actual top-level import names from the dependency list.

If the project has an entry point (e.g. `main.py`):

```bash
uv run python main.py --help 2>/dev/null \
    || uv run python -c "import main; print('entry point OK')"
```

## Step 9 — Update CI (if applicable)

If the repo contains `.github/workflows/`, `Jenkinsfile`, `.gitlab-ci.yml`, `bitbucket-pipelines.yml`, or a `Dockerfile`, update them. See [references/ci-updates.md](references/ci-updates.md) for per-system templates.

## Step 10 — Report Summary

```
Migration Complete: {SOURCE} → uv

Files created:
  - pyproject.toml (created/updated)
  - .python-version
  - uv.lock
  - .venv/

Files deleted:
  - {list}

Packages installed: {count}
Python version: {DETECTED_PYTHON}

Quick reference:
  uv sync                    - install / update dependencies
  uv add <package>           - add a dependency
  uv add --group dev <pkg>   - add a dev dependency
  uv remove <package>        - remove a dependency
  uv run python <script>     - run a script
  uv run pytest              - run tests
  uv lock --upgrade          - upgrade all packages
```

---

## Edge Cases

- **Monorepo / workspace** — If multiple `pyproject.toml` files exist, ask the user which project to migrate before proceeding.
- **Private PyPI** — `--index-url` / `--extra-index-url` go into `[tool.uv]`:

  ```toml
  [tool.uv]
  index-url = "https://private.pypi.org/simple/"
  extra-index-url = ["https://pypi.org/simple/"]
  ```

- **Git / URL dependencies** — `"pkg @ git+https://github.com/org/repo.git@tag"` in `dependencies`.
- **Python not installed** — `uv python install {DETECTED_PYTHON}` before Step 6.

---

## Additional Resources

- Per-source conversion rules: [references/pip-to-uv.md](references/pip-to-uv.md), [references/poetry-to-uv.md](references/poetry-to-uv.md), [references/pipenv-to-uv.md](references/pipenv-to-uv.md), [references/conda-to-uv.md](references/conda-to-uv.md)
- CI / Docker updates: [references/ci-updates.md](references/ci-updates.md)
