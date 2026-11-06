# CI Updates

Read this in Step 6, for each file listed in `ci`. Pin uv everywhere: an unpinned image or installer changes uv under the project without a commit. Versions below were current on 2026-11-06 (uv 0.13.7, setup-uv v10.3.3); use `uv --version` locally to choose the pin. The Docker and GitHub Actions templates also pass with uv 0.10.9 (verified), so an older local uv may be pinned as is. `--locked` fails if `uv.lock` is out of date with `pyproject.toml`, or not committed; use it in CI.

Adapt every template: replace `3.13` with the project's Python (a matrix entry uv has no build for, where `uv python list <v>` prints nothing, such as 3.7: ask whether to drop it), and install the same extras and groups the old CI installed (`--extra <name>`, `--all-extras`, `--group <name>`, `--no-dev`, `--no-default-groups`). `uv sync` installs the default groups: `dev`, or every group when the converter wrote `default-groups = "all"`.

## GitHub Actions

setup-uv has no floating `v10` tag: pin the full tag or a commit SHA.

```yaml
- uses: actions/checkout@v4
- uses: astral-sh/setup-uv@v10.3.3
  with:
    version: "0.13.7"
    enable-cache: true
    python-version: "3.13"      # replaces actions/setup-python
- run: uv sync --locked
- run: uv run pytest
```

Replace: `pip install -r ...`, `pip install poetry` + `poetry install`, `pipenv install` → `uv sync --locked`; `poetry run X`, `pipenv run X` → `uv run X`.

## GitLab CI

```yaml
variables:
  UV_VERSION: "0.13.7"
  PYTHON_VERSION: "3.13"
  BASE_LAYER: trixie-slim
  UV_CACHE_DIR: .uv-cache
test:
  image: ghcr.io/astral-sh/uv:$UV_VERSION-python$PYTHON_VERSION-$BASE_LAYER
  cache:
    key: { files: [uv.lock] }
    paths: [$UV_CACHE_DIR]
  script:
    - uv sync --locked
    - uv run pytest
    - uv cache prune --ci
```

Versioned uv images use Debian trixie; `<version>-python3.x-bookworm-slim` tags do not exist, and the unversioned `python3.x-bookworm-slim` tags are frozen at uv 0.9.30.

## Bitbucket Pipelines

```yaml
image: ghcr.io/astral-sh/uv:0.13.7-python3.13-trixie-slim
definitions:
  caches:
    uv: ~/.cache/uv
pipelines:
  default:
    - step:
        caches: [uv]
        script:
          - uv sync --locked
          - uv run pytest
          - uv cache prune --ci
```

## Jenkins, Travis CI, CircleCI, others

Use the uv image as the agent, or install a pinned version: `curl -LsSf https://astral.sh/uv/0.13.7/install.sh | sh`, then `uv sync --locked` and `uv run pytest`.

## Docker

```dockerfile
FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_NO_DEV=1
WORKDIR /app
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-local
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked
ENV PATH="/app/.venv/bin:$PATH"
CMD ["python", "main.py"]
```

Keep the project's existing `CMD`/entrypoint; with `.venv/bin` on `PATH` it runs as written. Use the base image that matches `.python-version`: otherwise the second `uv sync` downloads that Python and rebuilds `.venv` (verified). Do not bind-mount `.python-version` in the first `RUN`: a project that does not commit it (some `.gitignore` it) then fails to build. Add `.venv` to `.dockerignore`. Verified with Docker 29 (all three were real failures before the fix):

- `UV_NO_DEV=1` also covers `uv run` at container start; without it `uv run` installs the dev group then, and fails with no network.
- Each local path source in `[tool.uv.sources]` (`shared = { path = "libs/shared" }`) needs one more bind line in the first `RUN` (`--mount=type=bind,source=libs/shared,target=libs/shared`): `--locked` reads its metadata even though `--no-install-local` skips installing it.
- A stale `uv.lock` fails the build at the first `uv sync --locked`.

## Private-index credentials

- CI: store `UV_INDEX_<NAME>_USERNAME` / `UV_INDEX_<NAME>_PASSWORD` as masked CI secrets and expose them as environment variables to the `uv sync` step.
- Docker: never pass them as `ARG`/`ENV` (they stay in image layers). Use BuildKit secrets on both `uv sync` lines: add `--mount=type=secret,id=uv_index_password,env=UV_INDEX_<NAME>_PASSWORD` (the username the same way) to each `RUN`, and build with `docker build --secret id=uv_index_password,env=UV_INDEX_<NAME>_PASSWORD .`. Verified against a password-protected index: the build without `--secret` gets 401, with it succeeds, and the password appears in no image layer, history or config.

## Other files

- `tox.ini`: add `tox-uv`, or replace tox envs with `uv run --python 3.x pytest`.
- `Makefile`, scripts, README: replace `pip install`, `poetry install`, `poetry run`, `pipenv run` with `uv sync` / `uv run`; `poetry build` → `uv build`; `poetry publish` → `uv publish` (same flags such as `--dry-run`; token in `UV_PUBLISH_TOKEN`). Leave no command of the old manager behind: after deleting its lock it fails.
- `.readthedocs.yaml` with `python: install: - requirements: <file>`: keep `<file>` out of the Step 7 deletion, or regenerate it from the docs group (`uv export --only-group docs --no-hashes -o <file>`) and tell the user to re-run that export when docs dependencies change.
- Pre-commit hooks pinned to Poetry (`poetry-check`, `poetry-lock`) → `uv-lock` from `astral-sh/uv-pre-commit`.
