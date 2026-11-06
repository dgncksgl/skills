# Conda to uv

Read this when `source=conda`. No converter supports Conda; convert by hand.

## Is uv right for this project?

uv installs only PyPI packages. Before converting, check each conda-channel package on PyPI: `curl -sf -o /dev/null https://pypi.org/pypi/<name>/json` succeeds only if it exists (use the PyPI name from step 4). Stop and ask the user if the project depends on conda-only binaries (`mkl`, R packages, compilers, `cudatoolkit` used by something other than PyTorch) or on packages whose PyPI version needs a system library (GDAL, PROJ, GEOS): uv cannot install those. Options to offer: keep conda for the system libraries and use uv inside that environment; install the system library with the OS package manager; or stay on conda.

`cudatoolkit` used only by PyTorch is not needed: PyTorch's CUDA wheels bring their own CUDA runtime (step 5).

## Steps

1. No `pyproject.toml` → `uv init --bare --name <suggested_name> --python <python>` (Python from `- python=3.x`). One without `[project]` → add `[project]` by hand (`name`, `version`, `requires-python`), keeping the other tables.
2. Packages under `- pip:` → `uv add --raw <spec>` exactly as written. `-r <file>`, `-e` and local-path lines are not specs: handle them as the pip route does (SKILL.md Step 3 and the [Converter Guide](converter-guide.md)). A file in `requirements` that no `-r` line here pulls in is a second list: migrate it the same way (`uv add --raw -r <file>`, dev files to `--group dev`), or its packages are lost when Step 7 removes it.
An `environment.yml` without versions records nothing the project really ran on, so a fresh resolve may pick a newer major that breaks it. Ask the user for `conda list --export` from the working environment; pass its PyPI packages, converted with the table below, as `-c <file>` on the `uv add` calls. Without one, report that versions were resolved fresh.

3. Conda-channel packages with a PyPI equivalent → `uv add --raw <pypi-name><spec>`, converting the spec. Skip the step 4 names (`python`, `pip`, ...) and add torch only after step 5's index:

| Conda | PyPI spec |
|---|---|
| `pkg=1.2` (conda means 1.2.*) | `pkg==1.2.*` |
| `pkg=1.2.3` (conda means 1.2.3.*) | `pkg==1.2.3.*` |
| `pkg=1.2.*` | `pkg==1.2.*` |
| `pkg==1.2.3` (exact in conda) | `pkg==1.2.3` |
| `pkg 1.2.3` (space, no operator: exact in conda) | `pkg==1.2.3` |
| `pkg>=1.2,<2` | `pkg>=1.2,<2` |
| `pkg` | `pkg` |
| `pkg=1.2.3=py311_0` (build string: conda treats the version as exact, as in `conda env export`) | `pkg==1.2.3` (drop the build string) |

4. Names that differ between conda and PyPI: `pytorch` → `torch`, `pytables` → `tables`, `msgpack-python` → `msgpack`, `py-opencv` / `opencv` → `opencv-python`, `pyqt` → `PyQt5`. Skip `python`, `pip`, `setuptools`, `wheel`.
5. PyTorch with CUDA: before `uv add torch`, add the index (`https://download.pytorch.org/whl/cu118` for CUDA 11.8, `cu121` etc.) as `[[tool.uv.index]]` with `explicit = true`, and pin it: `[tool.uv.sources] torch = { index = "<name>", marker = "sys_platform == 'linux'" }`. The marker keeps the lock working on macOS, where the CUDA index has no wheels and PyPI's torch is used.
6. List every conda-only package in the report with "not migrated: install via the system package manager or keep conda".
7. Continue with SKILL.md Steps 4–8 (supporting files, verify, CI, cleanup, report).

## Files

- Rename `environment.yml` → `environment.yml.bak` only with user consent; deleting it loses the record of conda-only packages.
- Remove `conda-lock.yml` with user consent; `uv.lock` replaces it.
