# Converter Guide

Read this when running `uvx migrate-to-uv` (Poetry, Pipenv, pip-tools), when `req_options` is not `none`, when the pip route meets `-e` lines, or when `uv lock` / `uv sync` fails. Behaviour below was verified with migrate-to-uv 0.12.0 and uv 0.13.7. migrate-to-uv is a community project (osprey-oss), not Astral's; the skill pins `@0.12.0`, so re-check flags with `--help` before changing the pin.

## Converter flags

Pass the same flags to the `--dry-run` preview and to the real run.

| Situation | Flag |
|---|---|
| Always first | `--dry-run` (prints the new pyproject.toml, changes nothing) |
| Always on the real run | `--keep-current-data` (the skill deletes old data itself in Step 7, after consent) |
| `source=mixed`, user chose Poetry, Pipenv or pip-tools | `--package-manager poetry\|pipenv\|pip-tools`, plus `--skip-uv-checks` if `uv.lock` exists (a chosen pip takes the `uv add -r` route) |
| pip-tools files not at the default names (`requirements/base.in`) | `--requirements-file <f>` and `--dev-requirements-file <f>` (one file each) |
| Only a dev `.in` (runtime deps already in `[project]`) | `--package-manager pip-tools --dev-requirements-file <f>`: keeps `[project]` and the compiled pins (verified) |
| Published Poetry library, or the user wants zero packaging risk | `--keep-current-build-backend` (see Build backend) |
| Lock fails on a stale old lock, and the user agrees | `--ignore-locked-versions` (versions may change: say so) |
| Poetry optional or extra groups | `--dependency-groups-strategy` (default keeps groups and sets `default-groups = "all"`; `merge-into-dev` folds them into `dev`) |

The converter refuses a project that has `uv.lock` ("Project is already using uv"). It aborts atomically: on any error the project is left unchanged.

## What it would delete without `--keep-current-data`

With `--keep-current-data` all of this stays; it is part of the Step 7 cleanup list.

| Source | Would delete |
|---|---|
| Poetry | `poetry.lock`, `poetry.toml`, the `[tool.poetry*]` tables |
| Pipenv | `Pipfile`, `Pipfile.lock` |
| pip-tools | `requirements*.in` and their compiled `requirements*.txt` |

## Known gaps (all reproduced)

| Gap | Fix |
|---|---|
| No `[project] name` → `Not a valid package or extra name: ""`, lock aborts | Add the `[project]` table first (SKILL.md Step 3) |
| An existing `dependencies = []` (for example from `uv init`) is kept, so runtime dependencies vanish with no error | Remove the empty `dependencies` key before running; check the preview lists every runtime dependency |
| Option lines dropped silently: `-r`, `-c`, `-e`, `-i`, `--extra-index-url`, `-f` | Apply the `req_options` table below, then `uv lock` |
| Warning `"<lock>" could not be parsed, so dependencies were not kept to their previous locked versions` | Tell the user versions were re-resolved; Step 5 lists the differences |
| Warning `Build backend was migrated to uv` | See Build backend |

## pip route: option lines

`-r`, `-c` and `--extra-index-url` lines inside the file do not break `uv add --raw -r` (verified), so leave them; only `-e` and local-path lines need the steps below. Exception: a dev file that pulls in a runtime file with `-r` anywhere (`-r requirements.txt`, `-r base.txt`) would copy every runtime dependency into the dev group; use a temporary copy without that line. The `-c` and index settings still go into pyproject.toml by hand, before the first `uv add` (SKILL.md Step 3): `uv add` does not copy them, and without the index the first resolve fails.

## pip route: `-e` and local-path lines

`uv add --raw -r` fails on them ("is included as a workspace member, but is missing an entry in `tool.uv.sources`"). `-e .` installs the project itself: leave it out of the copy and do not add it back. Without `--raw` it writes a machine-specific absolute `file://` path. Instead:

1. Copy the file next to the original (for example `requirements.no-editable.txt`, so its `-r` paths still resolve) without the `-e` and local-path lines.
2. `uv add --raw -r requirements.no-editable.txt`, then delete that temporary copy.
3. For each removed line: `uv add --editable --no-workspace ./path` (drop `--editable` for a non-editable path). Verified: it writes `pkg` plus `[tool.uv.sources] pkg = { path = "path", editable = true }`. Without `--no-workspace`, a path inside the project becomes a uv workspace member: do that only if the user chose a workspace.

The temporary copy is the skill's own file; deleting it needs no consent.

## Fixing `req_options` lines

| Line in requirements | Target |
|---|---|
| `-r other.txt` | Pip route: `uv add -r` follows it; do not add `other.txt` separately. Converter route: `uv add --raw -r other.txt` |
| `-c constraints.txt` | `[tool.uv] constraint-dependencies = ["kombu<5.4", ...]` |
| `-e .`, `.` (the project itself) | Drop the line: uv installs the project; never `uv add` it |
| `-e ./path`, `./path`, `libs/x`, `wheels/x.whl` | Section above |
| `-e git+https://host/org/repo@v1#egg=pkg` | Same as the `git+` row: a git source has no editable form in uv |
| `git+https://host/org/repo@v1#egg=pkg` | `"pkg"` in dependencies + `[tool.uv.sources] pkg = { git = "https://host/org/repo", tag = "v1" }` (`rev` for a commit, `branch` for a branch). A private git host is not an index (`private_index` ignores it): CI needs git credentials for `uv sync`, for example a token in `git config --global url."https://oauth2:${TOKEN}@host/".insteadOf "https://host/"` |
| `-i URL`, `--index-url URL` | `[[tool.uv.index]]` with `name`, `url`, `default = true` |
| `--extra-index-url URL` | `[[tool.uv.index]]` with `name`, `url` |
| `-f DIR`, `--find-links DIR` | `[tool.uv] find-links = ["DIR"]` |
| `--hash=...`, `--require-hashes` | Drop: `uv.lock` stores hashes |
| `--no-binary pkg`, `--only-binary` | `[tool.uv] no-binary-package = ["pkg"]` / `no-build-package` |

`[tool.uv] index-url` and `extra-index-url` are deprecated; always write `[[tool.uv.index]]`. After hand edits, run `uv lock`.

**Private indexes:** uv uses the first index that has a package (`first-index`), unlike pip, which compares all indexes. Ask which packages must come only from the private index; for those mark the index `explicit = true` and pin them with `[tool.uv.sources] pkg = { index = "<name>" }`. Strip `user:password@` from the URL; credentials go in `UV_INDEX_<NAME>_USERNAME` / `UV_INDEX_<NAME>_PASSWORD` (name upper-cased, `-` → `_`), which the user sets before the first `uv add` or `uv lock` (both resolve). Verified: `uv add -r` does not copy an index URL or its credentials into pyproject.toml or uv.lock.

## Build backend (Poetry libraries)

The converter switches poetry-core to uv_build by default. Before converting a published package, build a baseline: `uv build --out-dir <scratchpad>/before`.

Is it published? A Poetry project with a `[build-system]` and no `package-mode = false` may be a library: ask. If yes, keep the backend unless the user wants uv_build.

- Which poetry-core builds the package is decided by the build, not by the floor: an uncapped `poetry-core>=1.1.0` builds with 2.x on Python 3.9+ (it reads `[project]`) and with 1.9 on 3.8 (verified). Treat an uncapped 1.x floor as < 2 below (keep the tables), and build before and after with the release job's Python (`uv build --python <v>`), or the comparison mixes two backends.
- `--keep-current-build-backend`, poetry-core < 2 (check `[build-system] requires`): poetry-core 1.x ignores `[project]` and builds the wheel's `Requires-Dist` from `[tool.poetry.dependencies]`. Verified: deleting that table publishes a wheel with no dependencies. Step 7 keeps every `[tool.poetry*]` table and deletes only `poetry.lock` and `poetry.toml`; tell the user dependencies now live in two places, and offer raising poetry-core to `>=2` (then the ≥ 2 rule applies).
- `--keep-current-build-backend`, poetry-core ≥ 2: it reads `[project]`. Step 7 may remove `[tool.poetry.dependencies]`, `[tool.poetry.group.*]` and `[tool.poetry.extras]`; keep `[tool.poetry]` keys `packages`, `include`, `exclude` and `[tool.poetry.build]`; ask about any other `[tool.poetry]` key.
- After every cleanup or backend change: `uv build --out-dir <scratchpad>/after`, then compare with the baseline: `tar tzf` of the sdists, `unzip -l` of the wheels, and `Requires-Dist` lines in the wheel `METADATA` (`unzip -p <wheel> '*/METADATA'`). Compare files and meaning, not text: uv_build also lists directory entries (`acme/`) and writes `Requires-Dist: six (>=1.16,<2.0)` as `six>=1.16,<2`; both are the same. Check that the same packages appear with equivalent ranges. A missing file or dependency → restore pyproject.toml (`git checkout -- pyproject.toml`, or the scratchpad backup) and ask.

## Common `uv lock` / `uv sync` errors

| Error | Fix |
|---|---|
| `No solution found` on `requires-python` | Ask, then raise the lower bound in `requires-python` to the version the old project really ran on (changing the target Python is ask-first) |
| A locked version has no wheel for the target Python | Ask, offering: target the Python the old lock was made for; refresh the old lock with the old manager (`poetry lock`, `pipenv lock`; pins may move) and convert again; or `--ignore-locked-versions` |
| Package not found | Name differs on PyPI or comes from a private index: check `private_index` |
| Python version not installed | `uv python install <python>` |
| `No download found for request: cpython-3.6` (uv ships no build that old; on macOS arm64 3.8 is the oldest) | Ask which newer Python to target (changing the target Python needs consent); old pins may lack wheels for it: then the no-wheel row above |
| Certificate / TLS error on a private index | Corporate CA: `--system-certs` or `SSL_CERT_FILE`; never disable verification |
| Build failure of an sdist | Missing system library or old package; try the locked version from the old lock before touching pins |
