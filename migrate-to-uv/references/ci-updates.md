# CI/CD Workflow Updates

Apply these after a successful migration. Only run when the repository contains CI configuration.

## GitHub Actions (`.github/workflows/*.yml`)

### Replace pip install

```yaml
# Before
- run: pip install -r requirements.txt

# After
- uses: astral-sh/setup-uv@v4
- run: uv sync --frozen
```

### Replace Poetry steps

```yaml
# Before
- run: pip install poetry
- run: poetry install

# After
- uses: astral-sh/setup-uv@v4
- run: uv sync --frozen
```

### Replace test invocations

```yaml
# Before
- run: pytest
- run: poetry run pytest

# After
- run: uv run pytest
```

### Replace Python setup

```yaml
# Before
- uses: actions/setup-python@v5
  with:
    python-version: '3.11'

# After (uv handles Python too)
- uses: astral-sh/setup-uv@v4
  with:
    enable-cache: true
```

## GitLab CI (`.gitlab-ci.yml`)

```yaml
image: python:3.11

before_script:
  - curl -LsSf https://astral.sh/uv/install.sh | sh
  - source $HOME/.local/bin/env
  - uv sync --frozen

test:
  script:
    - uv run pytest
```

## Jenkins (`Jenkinsfile`)

```groovy
stage('Install') {
    steps {
        sh 'curl -LsSf https://astral.sh/uv/install.sh | sh'
        sh '. $HOME/.local/bin/env && uv sync --frozen'
    }
}
stage('Test') {
    steps {
        sh '. $HOME/.local/bin/env && uv run pytest'
    }
}
```

## Bitbucket Pipelines (`bitbucket-pipelines.yml`)

```yaml
image: python:3.11
pipelines:
  default:
    - step:
        caches: [uv]
        script:
          - curl -LsSf https://astral.sh/uv/install.sh | sh
          - source $HOME/.local/bin/env
          - uv sync --frozen
          - uv run pytest
definitions:
  caches:
    uv: ~/.cache/uv
```

## Docker

```dockerfile
FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY . .
CMD ["uv", "run", "python", "main.py"]
```

## General Rule

After any CI change, ensure `uv.lock` is committed to the repo — `--frozen` requires it to be present and up-to-date.
