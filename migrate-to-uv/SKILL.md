---
name: migrate-to-uv
description: "Migrates an existing Python project from pip, pip-tools, Poetry, Pipenv, setuptools or Conda to the uv package manager without losing pinned versions, private indexes or CI setup. Use when the user asks to migrate, switch or convert a project to uv, replace requirements.txt, poetry.lock or Pipfile with pyproject.toml and uv.lock, or says \"uv'ye geç\", \"uv'ye geçiş yap\", \"poetry'den uv'ye geç\", \"pip'ten uv'ye geç\", \"pipenv'den uv'ye geç\", \"conda'dan uv'ye geç\", \"paket yöneticisini uv'ye çevir\", \"dependency yönetimini uv'ye taşı\", \"migrate to uv\", \"switch to uv\". Do not use for a brand-new project (run uv init), for upgrading or fixing a project already on uv, or for migrating to rye, pdm or hatch."
---

# Migrate to uv

## Overview

Moves a project to uv with deterministic tools (Step 3); hand conversion only where none fits.

## Core Rules

- Keep versions: never loosen a pin; never pass `--ignore-locked-versions` unless the user agrees after a lock failure.
- Ask first before: installing or updating uv, migrating with a dirty git tree, deleting any file or pyproject table (except the skill's temp files), adding a dependency the old setup did not declare, changing the target Python, and choosing between managers or a workspace layout.
- Never commit or push. Git is the undo; with no git, copy pyproject.toml and the old manager files to the session scratchpad before Step 3.
- Never copy a credential into a file. Report each `credentials` hit (`file:line`) without its value; if git tracks that file, the user must rotate it.
- One project per run: the named directory, else the current one. `subprojects` not `none` → ask which project, and whether to use a uv workspace.

## Workflow

### Step 1: Inspect

Run `python3 <skill-dir>/scripts/inspect-project.py <project-dir>` (`<skill-dir>`: this skill's base directory, usually `~/.claude/skills/migrate-to-uv`). Route on its `key=value` facts. Re-run after Step 3: `mixed` or `uv` is expected; continue without asking.

### Step 2: Preconditions

- `uv` missing → ask; offer `brew install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh` (then `source $HOME/.local/bin/env`).
- `uv` older than 0.13.7 (tested, not a known minimum) → note it; do not ask. A uv command fails on an unknown option → ask to update (`uv self update`, Homebrew: `brew upgrade uv`), retry.
- `git=dirty` → ask: commit, stash or back up.
- `python=unknown` → ask which Python to target; never assume the system one. `python_from` is a Dockerfile, CI file or `.venv` → propose that version and ask.
- `uv python list <python>` prints nothing → uv has no build for it: ask for a newer target.

### Step 3: Convert (route on `source`)

| `source` | Action |
|---|---|
| `uv` | Already migrated: stop |
| `mixed` | Ask which manager is authoritative, then take its row (converter managers: `--package-manager <name>`; PDM: unsupported) |
| `poetry`, `pipenv`, `pip-tools` | Converter: `uvx migrate-to-uv@0.12.0 --dry-run <flags> <dir>`, then `uvx migrate-to-uv@0.12.0 --keep-current-data <same flags> <dir>` (deletes nothing) |
| `pip` | `uv add --raw -r` route below |
| `pep621` | Fix `req_options`; `dev_requirements` → dev group; `uv lock` |
| `setuptools` | [Manual Conversion](references/manual-conversion.md) |
| `conda` | [Conda to uv](references/conda-to-uv.md) |
| `unknown` | Ask the user what manages dependencies (PDM lands here: unsupported) |

**Project table first:** pip route with no `pyproject.toml` → `uv init --bare --name <suggested_name> --python <python>`. A `pyproject.toml` without `[project]` (tool settings only; `uv init` refuses it), or the converter route with `project_name=missing` → write `[project]` by hand with only `name = "<suggested_name>"`, `version = "0.1.0"`, `requires-python = ">=<python>"`. No `uv init`, no `dependencies` key: the converter keeps `dependencies = []` and silently drops all runtime dependencies.

**pip route:** first write the `-c` constraints and index lines from `req_options` into pyproject.toml (first resolve needs them; `private_index=yes` with no index or `-f` line there → take it from pip.conf, uv.toml or the CI's `PIP_INDEX_URL`), then `uv add --raw -r <file>` for runtime files and `uv add --raw --group dev -r <file>` for files in `dev_requirements`. Skip a file another listed file pulls in with `-r` (`uv add -r` follows it). A `pip freeze` file (every line `==`, transitive packages too) → ask which packages are direct, then `uv add --raw <them> -c <file>` (pins kept, the rest stay transitive). A dev file that `-r`s a runtime file, or a file with `-e` or local-path lines (they break `--raw`): follow the [Converter Guide](references/converter-guide.md).

**Converter route:** Poetry with a `[build-system]`: read Build backend in the Converter Guide first. Check the preview: all dependencies and groups present, no range wider. After hand-fixing `req_options`, `uv lock` again. Files in `dev_requirements` the converter did not read (Poetry, Pipenv; pip-tools without `--dev-requirements-file`) → `uv add --raw --group dev -r <file>` (a pip-tools `.in`: add `-c <its compiled .txt>`), or Step 7 loses them. Flags, fixes, warnings, lock errors: [Converter Guide](references/converter-guide.md).

### Step 4: Supporting files

- No `.python-version` → `uv python pin <python>`; refused (patch floor like `>=3.8.1`) → pin the newest patch from `uv python list <python>`.
- `.gitignore` has `.venv/` (add it if missing), never `uv.lock`.

### Step 5: Install and verify

1. `uv sync`; failures: Converter Guide (pins stay).
2. Compare direct-dependency versions in `uv.lock` with the old ones.
3. `uv run <test command>`; with no tests, import each top-level dependency and run console scripts with `--help`.
4. A missing import in the old lock → the migration lost it: fix it. Not in it → pre-existing gap: ask before adding. Step 5 passes when nothing the migration caused fails.

### Step 6: CI and Docker

For each file in `ci` (skip files inside a subproject this run does not migrate), replace the old manager's steps per [CI Updates](references/ci-updates.md): project's Python, pinned uv, same extras and groups; show the diff. A Dockerfile takes the whole template, `ENV` line included (`UV_NO_DEV=1` keeps dev tools out of the image). Then README, docs and scripts: `git grep -n -e pipenv -e poetry -e "pip install" -e "requirements.*\.txt"`, and update each hit per Other files in CI Updates. Project in a subfolder of a git repo: `ci` covers only that folder, so also update the repo root's CI files that name the folder (from the project folder: `git grep -l <folder>/ -- ':/.github/*' ':/.gitlab-ci.yml'`).

### Step 7: Clean up (only after Step 5 passed)

List the old files (`lockfiles` except `uv.lock`, `Pipfile`, `poetry.toml`, every file in `requirements` and their `-r`/`-c` files; Conda: `environment.yml` per the Conda guide) and `[tool.poetry*]` tables. Ask; delete exactly what the user approves (all, some or none). `uv export --no-hashes -o requirements.txt` regenerates one. With a `[build-system]`, follow Build backend in the Converter Guide before touching `[tool.poetry*]`: poetry-core < 2 needs them all. Keep files the build reads (`[tool.setuptools.dynamic]`, a kept `setup.py`). Declined → both remain. Step 5 failed → delete nothing.

### Step 8: Report

In the user's language:
1. `<source> → uv`, Python, packages in `uv.lock`.
2. Files created, changed, deleted and kept, CI included.
3. Version differences, hand-carried `req_options`, converter warnings, `credentials` hits (`none` only means no pattern matched in the scanned files; say so).
4. Test result and pre-existing failures.
5. Each Ask-first decision, its answer, and whether it was asked or given up front.
6. Open decisions; nothing committed; commit `uv.lock` for `--locked`.

## Additional Resources

- [Converter Guide](references/converter-guide.md): flags, build backend, errors
- [Manual Conversion](references/manual-conversion.md): setuptools, converter failures
- [Conda to uv](references/conda-to-uv.md): environment.yml, conda-only packages
- [CI Updates](references/ci-updates.md): CI systems, Docker, index secrets
