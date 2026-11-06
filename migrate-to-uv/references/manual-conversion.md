# Manual Conversion

Read this when `source=setuptools`, or when the converter failed and the user agreed to convert by hand. Prefer uv commands (`uv init --bare`, `uv add --raw`) over writing TOML: they validate names and keep specifiers as written.

## setuptools (`setup.py` / `setup.cfg`)

1. No `pyproject.toml` → `uv init --bare --name <name> --python <python>`. One without `[project]` (`uv init` refuses an existing file) → add `[project]` by hand with `name`, `version` and `requires-python`, keeping the other tables.
2. Copy metadata into `[project]`:

| setup.py / setup.cfg | pyproject.toml |
|---|---|
| `name`, `version`, `description` | same keys in `[project]` |
| `license="MIT"` | `license = {text = "MIT"}`: the plain-string form (PEP 639) needs `setuptools>=77` in `[build-system]` |
| `author` + `author_email` | `authors = [{ name = "...", email = "..." }]` |
| `python_requires` | `requires-python` |
| `install_requires` | `uv add --raw <each requirement>` |
| `extras_require = {"dev": [...]}` used only for development | `uv add --raw --group dev ...` |
| `requirements.txt` (or a lone `requirements.in`) next to a `setup.py` without `install_requires` | `uv add --raw -r <that file>` |
| pip-tools pair (`requirements.in` + compiled `requirements.txt`) next to `setup.py` | `uv add --raw -r requirements.in -c requirements.txt`: direct dependencies from the `.in`, versions held by the compiled pins (verified: they survive `uv lock`). Never `-r` the compiled file: every transitive pin would become a direct dependency |
| `requirements-dev.txt` and similar files next to `setup.py` | `uv add --raw --group dev -r <file>` (follow the pip route rules for `-r`/`-e` lines) |
| `extras_require` for users (`pip install pkg[x]`) | `uv add --raw --optional <extra> ...` |
| `entry_points["console_scripts"]` | `[project.scripts]` |
| dynamic `version` read from a file | keep it dynamic: `dynamic = ["version"]` plus `[tool.setuptools.dynamic]` |

3. Keep the setuptools build backend: `[build-system] requires = ["setuptools>=61"]`, `build-backend = "setuptools.build_meta"`. Switching backends changes what gets packaged; do it only when asked.
4. Delete `setup.py` / `setup.cfg` only when nothing in them remains (custom build steps, `cmdclass`, C extensions must stay) and the user agrees.

## Fallback: Poetry by hand

| Poetry | uv |
|---|---|
| `[tool.poetry]` name, version, description, readme | `[project]` same keys |
| `authors = ["A <a@b.c>"]` | `authors = [{ name = "A", email = "a@b.c" }]` |
| `python = "^3.11"` | `requires-python = ">=3.11,<4"` |
| `^1.2.3` / `^0.3.1` / `^0.0.3` | `>=1.2.3,<2` / `>=0.3.1,<0.4` / `>=0.0.3,<0.0.4` |
| `~1.2.3` | `>=1.2.3,<1.3` |
| `{ version = "^1.0", extras = ["x"] }` | `"pkg[x]>=1.0,<2"` |
| `{ version = "^1.0", optional = true }` + `[tool.poetry.extras]` | `[project.optional-dependencies]` |
| `{ git = URL, tag = "v1" }` | `[tool.uv.sources] pkg = { git = URL, tag = "v1" }` |
| `{ path = "../lib", develop = true }` | `[tool.uv.sources] pkg = { path = "../lib", editable = true }` |
| `[tool.poetry.group.<g>.dependencies]` | `[dependency-groups] <g>` |
| `[[tool.poetry.source]]` | `[[tool.uv.index]]` (see converter-guide.md) |
| `package-mode = false` | `[tool.uv] package = false` |
| `[tool.poetry.scripts]` | `[project.scripts]`, which needs a `[build-system]` |

Replace a `poetry-core` `[build-system]` only together with its scripts and package settings; otherwise keep it.

## Fallback: Pipenv by hand

| Pipfile | uv |
|---|---|
| `[packages]` | `uv add --raw` each entry; `"*"` → name only |
| `[dev-packages]` | `uv add --raw --group dev` |
| `[requires] python_version` | `requires-python = ">=<version>"` |
| `{ version = "==1.0", extras = ["x"] }` | `"pkg[x]==1.0"` |
| `{ git = URL, ref = "v1" }` | `[tool.uv.sources] pkg = { git = URL, rev = "v1" }` |
| `{ path = "../lib", editable = true }` | `[tool.uv.sources] pkg = { path = "../lib", editable = true }` |
| `[[source]]` other than pypi.org | `[[tool.uv.index]]` |
| `[scripts]` | No uv equivalent: move to a Makefile or document `uv run <cmd>` |

Locked versions are not carried by hand. Tell the user that versions were re-resolved, and pin the ones they care about.
