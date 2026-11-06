#!/usr/bin/env python3
"""Inspect a Python project before migrating it to uv.

Usage: python3 inspect-project.py [PROJECT_DIR]

Prints one key=value line per fact (source, python, project_name, ...).
Exit codes: 0 report printed, 2 usage error.
Standard library only; Python 3.9 compatible (no tomllib, TOML read by regex).
"""
import functools
import os
import re
import shutil
import subprocess
import sys
from urllib.parse import urlparse
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

PYPROJECT = "pyproject.toml"
UNKNOWN = "unknown"
NONE = "none"
SKIP_DIRS = {"venv", "env", "node_modules", "build", "dist", "site-packages", "__pycache__",
             "vendor", "_vendor", "third_party"}
NUMBERED_VENV = re.compile(r"^\.?venv[\d.]*$")
SUBPROJECT_DEPTH = 4
FIXTURE_DIRS = {"tests", "test", "testing", "fixtures"}
NOT_SUBPROJECTS = FIXTURE_DIRS | {"examples", "example", "docs"}
REQUIREMENT_DIRS = (".", "requirements", "reqs")
LOCKFILES = ("poetry.lock", "Pipfile.lock", "pdm.lock", "conda-lock.yml", "uv.lock")
CONDA_ENV_FILES = ("environment.yml", "environment.yaml")
CONDA_FILES = CONDA_ENV_FILES + ("conda-lock.yml",)
CI_GLOBS = (".github/workflows/*.yml", ".github/workflows/*.yaml",
            ".github/actions/**/action.yml", ".github/actions/**/action.yaml", ".gitlab-ci.yml",
            "Jenkinsfile", "bitbucket-pipelines.yml", "azure-pipelines.yml",
            "Dockerfile*", "*.Dockerfile", "*/Dockerfile*", "*/*/Dockerfile*",
            ".buildkite/*.yml",
            "docker-compose*.yml", "docker-compose*.yaml", "compose*.yml", "compose*.yaml",
            ".gitlab/**/*.yml", ".travis.yml", ".circleci/config.yml", "appveyor.yml",
            ".readthedocs.yml", ".readthedocs.yaml",
            "Makefile", "tox.ini", "noxfile.py", ".pre-commit-config.yaml")
OLD_MANAGER_PATTERN = re.compile(
    r"pip3? install|python -m pip|\bpoetry(?=\s|$)|\bpipenv(?=\s|$)|\bconda |\b(?:micro)?mamba |pip-compile|pip-sync"
    r"|requirements[\w./-]*\.txt|setup-python|setup-miniconda|environment\.ya?ml|setup\.py (?:install|develop)",
    re.M)  # `pipx install poetry` at a line end too
RUNTIME_PYTHON_PATTERNS = (
    re.compile(r"(?:^|[\s/\"'])python:(\d+\.\d+)", re.M),
    re.compile(r"nox\.session\([^)]*python\s*=\s*(\[[^\]]*\]|[\"'][^\"']*[\"'])"),  # noxfile.py
    re.compile(r"^[ \t]*ARG[ \t]+PY(?:THON)?_?VERSION=[\"']?(\d+\.\d+)", re.M),  # FROM python:${PYTHON_VERSION}
    re.compile(r"python-version:[ \t]*\[?([^\n\]]*)", re.M),
    re.compile(r"^[ \t]*python:[ \t]*[\"']?(\d+\.\d+)[\"']?[ \t]*$", re.M),  # readthedocs build.tools
    re.compile(r"^[ \t]*python:[ \t]*\[([^\]\n]*)\]", re.M),  # a matrix key named python
    # a block list under python-version: or python: (Travis), version items only
    re.compile(r"(?:python-version|python):[ \t]*\n((?:[ \t]*-[ \t]*[\"']?\d+\.\d+[^\n]*\n?)+)"),
)
NESTED_DOCKERFILES = ("*/Dockerfile*", "*/*/Dockerfile*")  # placeholders: ci_paths() takes these depths from walk_tree()
CI_DOT_DIRS = {".github", ".gitlab", ".circleci", ".devcontainer", ".buildkite"}
NOT_REQUIREMENTS = ("readme", "license", "notes", "changelog")
CONDA_PYTHON_PATTERN = re.compile(
    r"^\s*-\s*(?:[\w-]+::)?python(?:\s*([=<>~!]=?\s*[^\s#]*)|\s+(\d[^\s#]*))", re.M)  # `python = 3.11` too
INDEX_LINE_PATTERN = re.compile(
    r"(^\s*-?\s*(--index-url|--extra-index-url|--find-links)\b|^\s*(?:-\s+)?-[if](?=[\s=./]|https?:)"  # `- -i URL` in a conda pip: list
    r"|^\s*(index-url|extra-index-url|find-links)\s*=|PIP_(EXTRA_)?INDEX_URL"
    r"|\s@\s*https?://)", re.M)  # `pkg @ https://host/pkg.whl` direct URLs too
CI_INDEX_PATTERN = re.compile(
    r"--index-url|--extra-index-url|--find-links|PIP_(?:EXTRA_)?INDEX_URL|PIP_FIND_LINKS"
    r"|UV_(?:EXTRA_)?INDEX_URL|UV_DEFAULT_INDEX|UV_INDEX\b|UV_FIND_LINKS"
    r"|pip3?\s+install\b[^\n]*\s-[if]\s")  # short -i/-f only on a pip install line
VARIABLE_INDEX_PATTERN = re.compile(
    r"(?:--index-url|--extra-index-url|--find-links|\s-[if])[=\s]+[\"']?\$")
# tox `envlist` / tox 4 `env_list`, with continuation lines
TOX_ENVLIST_PATTERN = re.compile(r"^env_?list\s*=([^\n]*(?:\n[ \t]+[^\n]*)*)", re.M)
GIT_JUNK = re.compile(r"(^|/)(\.DS_Store|Thumbs\.db|desktop\.ini)$|\.sw[po]$|~$")
SUBPROCESS_TIMEOUT_SECONDS = 30
SELF_INSTALL = re.compile(r"^(-e\s+|--editable[\s=]+)?([\"']?)(file:)?\./?(\[[\w,\s-]*\])?/?\2$")  # . ./[dev] file:.
DEV_NAME_TOKENS = {"dev", "devel", "development", "qa", "test", "tests", "testing", "lint", "linting",
                   "typing", "style", "doc", "docs", "ci", "local"}  # local: cookiecutter-django
# a -c target with one of these names is a runtime file (pip-tools layers: dev.txt has `-c base.txt`)
RUNTIME_NAME_TOKENS = {"requirements", "base", "common", "main", "prod", "production", "runtime"}
PIN_NAME_TOKENS = {"lock", "locked", "pin", "pins", "pinned", "frozen"}  # requirements-lock.txt: a constraint
VCS_PATTERN = re.compile(r"(^|[\s@])(git|hg|svn|bzr)\+")
RELATIVE_PATH = re.compile(r"^[\w.-]+/[\w./-]*(\[[\w,-]+\])?$")
ARCHIVES = (".whl", ".tar.gz", ".zip")
UV_EXPORT_MARKER = "autogenerated by uv"
UV_EXPORT_COMMAND = re.compile(r"^#\s+uv export\b", re.M)  # `uv pip compile` writes the same marker
VENV_CFG = ".venv/pyvenv.cfg"
CONSTRAINT_OPTION = r"-c[ \t=]*|--constraint[ \t=]+"  # pip also accepts the joined `-cpins.txt`
CONSTRAINT_PATTERN = re.compile(r"^[ \t]*(?:" + CONSTRAINT_OPTION + r")(\S+)", re.M)
INCLUDE_PATTERN = re.compile(r"^[ \t]*(?:-r[ \t=]*|--requirement[ \t=]+|" + CONSTRAINT_OPTION + r")(\S+)", re.M)
URL_PATTERN = re.compile(r"https?://[^\s\"']+")
DEFAULT_SECRET_VALUES = {"postgres", "password", "changeme", "secret", "example", "admin",
                         "root", "test", "mysql", "redis", "guest", "dev", "local"}
# `settings.SECRET_KEY`: a code reference; short identifier segments (a JWT's are long base64)
ENV_VAR_NAME = re.compile(r"^[A-Z][A-Z0-9]*(_[A-Z0-9]+)+$")  # token = "GH_TOKEN": names the variable
ATTRIBUTE_REFERENCE = re.compile(r"^[A-Za-z_]\w{0,39}(\.[A-Za-z_]\w{0,39})+$")
PLACEHOLDER_WORDS = re.compile(r"change[-_]?me|your[-_]|replace[-_]?(me|with)|placeholder|dummy|xxxx", re.I)
PUBLIC_HOSTS = {"pypi.org", "test.pypi.org", "pypi.python.org", "files.pythonhosted.org", "download.pytorch.org",
                "github.com"}  # github.com: public release assets in direct URLs
NESTED_REQUIREMENT_DEPTH = 3
SECRET_FILES = (PYPROJECT, "Pipfile", "poetry.toml", "setup.cfg", "uv.toml", "pip.conf", "pip.ini",
                ".pypirc", "environment.yml", "environment.yaml")
SECRET_MIN_LENGTH = 8
VERSION_LITERAL = re.compile(r"^\d+(\.\d+)+([a-z]+\d*)?(\.(post|dev)\d*)*$", re.I)
URL_SECRET_PATTERN = re.compile(r"://[^/\s:@\"']*:([^/\s@\"']+)@")  # `redis://:pw@host` too
TOKEN_USERINFO_PATTERN = re.compile(r"://([^/\s:@\"'$]{20,})@")  # https://<PAT>@host; `git@` is too short
KEY_SECRET_PATTERN = re.compile(
    r"(?i)\b((?:[\w.]*[_.-])?(?:token|secret|password|passwd|api[_-]?key|access[_-]?key"
    r"|secret[_-]?key|private[_-]?key|reporter[_-]?id))[\"']?\s*(?::(?!=)|[?:+]?=(?!=))\s*(\"[^\"]*\"|'[^']*'|[^\s#,]+)")
VERSION_PATTERN = re.compile(r"(\d+)\.(\d+)")
MAJOR_ONLY = re.compile(r"^(>=|\^|~=|~|==)?\s*3(\.\*)?$")
LOWER_BOUND_PATTERN = re.compile(r"(>=|~=|==|\^|~|>)?\s*(\d+\.\d+)(\.\d+)?")


@functools.lru_cache(maxsize=None)  # several checks read the same files
def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def toml_section(text: str, header: str) -> str:
    """Return the body of a [header] table (until the next table header)."""
    match = re.search(r"^\[" + re.escape(header) + r"\][ \t]*(?:#[^\n]*)?$(.*?)(?=^\[|\Z)", text, re.M | re.S)
    return match.group(1) if match else ""


def toml_string(body: str, key: str) -> Optional[str]:
    match = re.search(r"^\s*" + re.escape(key) + r"\s*=\s*[\"']([^\"']*)[\"']", body, re.M)
    return match.group(1) if match else None


def version_key(version: str) -> Tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def lower_bound(spec: str) -> Optional[str]:
    """Lowest Python x.y a specifier allows: the highest bound inside each ``,`` group,
    the lowest across ``||`` (Poetry also: ``|``) alternatives; ignores <, <=, != clauses."""
    alternatives: List[str] = []
    for alternative in re.split(r"\|\|?", spec):
        bounds = []
        for clause in re.split(r",|\s+(?=[<>=!~^])", alternative):
            clause = clause.strip()
            if MAJOR_ONLY.match(clause):
                bounds.append("3.0")  # `>=3`, `^3`, `3.*`: a floor, so later files never override it
                continue
            match = None if clause.startswith(("<", "!")) else LOWER_BOUND_PATTERN.search(clause)
            if match and match.group(1) == ">" and not match.group(3):
                major, minor = version_key(match.group(2))
                bounds.append("{}.{}".format(major, minor + 1))  # uv rejects pin X.Y for ">X.Y"
            elif match:
                bounds.append(match.group(2))
        floor = max(bounds, key=version_key) if bounds else None
        if floor and version_key(floor)[0] >= 3:  # a Python 2-only alternative: uv cannot target it
            alternatives.append(floor)
    return min(alternatives, key=version_key) if alternatives else None


def major_minor(text: str) -> Optional[str]:
    match = VERSION_PATTERN.search(text)
    return "{}.{}".format(match.group(1), match.group(2)) if match else None


def requirement_files(root: Path) -> Tuple[List[str], List[str]]:
    txt: List[str] = []
    inputs: List[str] = []
    for folder in REQUIREMENT_DIRS:
        base = root / folder
        if not base.is_dir():
            continue
        for path in list_dir(base):
            name = path.name
            in_req_dir = folder != "."
            listed = in_req_dir or "requirements" in name.lower() or is_pip_tools_pair(path)
            listed = (listed and not name.lower().startswith(NOT_REQUIREMENTS)
                      and "constraint" not in name.lower())  # -c files are reached via req_options
            if not path.is_file() or not listed:
                continue
            rel = path.relative_to(root).as_posix()
            if name.endswith(".txt"):
                txt.append(rel)
            elif name.endswith(".in"):
                inputs.append(rel)
    constraints = {(root / rel).parent.joinpath(target).resolve()
                   for rel in txt + inputs for target in CONSTRAINT_PATTERN.findall(read(root / rel))}
    # a file only pulled in with -c (pins.txt) is a constraint, but `-c requirements.txt` or `-c base.txt`
    # in a dev file still leaves that file a runtime source
    def kept(rel: str) -> bool:
        return (root / rel).resolve() not in constraints or named(rel, RUNTIME_NAME_TOKENS | DEV_NAME_TOKENS)

    return [rel for rel in txt if kept(rel)], [rel for rel in inputs if kept(rel)]


def name_tokens(rel: str) -> Set[str]:
    """requirements-dev.txt → {requirements, dev, txt}."""
    return set(re.split(r"[-_.]", Path(rel).name.lower()))


def named(rel: str, words: Set[str]) -> bool:
    """base.txt / requirements.txt / dev.txt reached with `-c`: still a dependency list, unless pin-named."""
    tokens = name_tokens(rel)
    return bool(tokens & words) and not tokens & PIN_NAME_TOKENS


def is_pip_tools_pair(path: Path) -> bool:
    """dev.in + dev.txt at the root, the .txt compiled by pip-compile (MANIFEST.in never pairs)."""
    other = path.with_suffix(".txt" if path.suffix == ".in" else ".in")
    compiled = path if path.suffix == ".txt" else other
    return (path.suffix in (".in", ".txt") and path.name != "MANIFEST.in" and other.is_file()
            and re.search(r"pip-compile|uv pip compile", read(compiled)[:500]) is not None)


def strip_comments(text: str) -> str:
    return re.sub(r"#[^\n]*", "", text)


def detect_source(root: Path, pyproject: str, txt: List[str], inputs: List[str], nested: List[str]) -> str:
    """nested: requirements files below the root, outside subprojects; they never route, but an
    otherwise empty [project] next to one must not pass as a finished pep621 project."""
    has_uv = (root / "uv.lock").is_file()
    managers = []
    if re.search(r"^\[tool\.poetry[\].]", pyproject, re.M) or (root / "poetry.lock").is_file():
        managers.append("poetry")
    if (root / "Pipfile").is_file() or (root / "Pipfile.lock").is_file():
        managers.append("pipenv")
    if any((root / name).is_file() for name in CONDA_FILES):
        managers.append("conda")
    # pdm-backend alone ([tool.pdm.version], [tool.pdm.build]) is build metadata, not the PDM manager
    if re.search(r"^\[tool\.pdm\.dev-dependencies\]", pyproject, re.M) or (root / "pdm.lock").is_file():
        managers.append("pdm")  # no converter supports it: never route it silently
    project_table = strip_comments(toml_section(pyproject, "project"))
    dynamic_deps = re.search(r"^\s*dynamic\s*=\s*\[[^\]]*[\"']dependencies[\"']", project_table, re.M)
    has_project = re.search(r"^\[project\]", pyproject, re.M) is not None
    poetry_deps = re.search(r"^\[tool\.poetry\.(?:dependencies|dev-dependencies|group\.|extras)", pyproject, re.M)
    if (has_project and "poetry" in managers and not (root / "poetry.lock").is_file()
            and (has_uv or not poetry_deps)):
        managers.remove("poetry")  # [tool.poetry] kept only for poetry-core's build metadata (packages, include)
    if has_uv and dynamic_deps and not managers:
        return "uv"  # the build backend reads the requirements files: they are not a second source
    if has_uv:
        old_requirements = [rel for rel in txt + inputs if not is_uv_export(read(root / rel)[:300])
                            and not adds_no_dependency(root / rel)]
        return "mixed" if managers or old_requirements else "uv"
    if len(managers) > 1:
        return "mixed"
    runtime_files = runtime_lists(root, txt + inputs)
    hand_written = [rel for rel in runtime_files if not looks_exported(root / rel)]
    if managers in (["poetry"], ["pipenv"]) and hand_written:
        return "mixed"  # a second runtime list, not an export: the user names the authoritative one
    if managers:
        return UNKNOWN if managers[0] == "pdm" else managers[0]
    setup_text = strip_comments(read(root / "setup.py") + "\n" + read(root / "setup.cfg"))
    # install_requires=open("requirements.txt")... or `file: requirements.txt`: one source, not two
    # a requirements *file* name or `file:`; a package such as requirements-parser is a real dependency
    reads_inline = (re.search(r"install_requires[ \t]*=(?![ \t]*\[)[^\n]*(requirements[\w./-]*\.(?:txt|in)\b|file:)",
                              setup_text)
                    or re.search(r"install_requires[ \t]*=[^\n]*open\([^)]*requirements", setup_text))
    # `install_requires=REQS` in setup.py only: in setup.cfg `install_requires = requests` is a package
    # `install_requires=REQS` or `=reqs()`, and the file setup.py opens is a runtime list (not requirements-dev.txt)
    opened = re.findall(r"(?:open|Path)\([^)]*?(requirements[\w.-]*)", setup_text, re.I)
    reads_via_name = (re.search(r"install_requires[ \t]*=[ \t]*[A-Za-z_]\w*(?:\([^)\n]*\))?[ \t]*[,)\n]",
                                strip_comments(read(root / "setup.py")))
                      and any(not is_dev_file(name) for name in opened))
    setup_reads_requirements = bool(reads_inline or reads_via_name)
    setup_packages = re.search(r"\b(packages|py_modules|entry_points|scripts|ext_modules|cmdclass)\s*=",
                               setup_text) is not None
    # `install_requires=[]` in setup.py, or an empty `install_requires =` key in setup.cfg
    empty_list = re.search(r"install_requires[ \t]*=[ \t]*(?:\[\s*\]|\n(?![ \t]+\S)|\Z)", setup_text) is not None
    setup_deps = "install_requires" in setup_text and not setup_reads_requirements and not empty_list
    project_deps = re.search(r"^\s*dependencies\s*=\s*\[\s*[^\]\s]", project_table, re.M) is not None
    if dynamic_deps:
        return "pep621"  # the build backend reads requirements files itself: one source, `uv lock`
    # [project] deps + dev-only files is the pip route (it adds them to the dev group)
    if runtime_files and (setup_deps or project_deps):
        return "mixed"
    if not runtime_files and not project_deps and not setup_deps and nested_runtime(root, nested):
        return "mixed"  # src/requirements.txt holds the only runtime list (root files, if any, are dev-only)
    if (txt or inputs) and setup_deps:
        return "setuptools"  # dev-only files: Manual Conversion adds them to the dev group
    # a setup.py shim (packages=) next to a [project] with deps: [project] is the source, not setup.py
    if (txt or inputs) and (setup_reads_requirements or (setup_packages and not (has_project and project_deps))):
        return "setuptools"  # setup.py builds the package; Manual Conversion keeps its metadata
    if any(not adds_no_dependency(root / rel) for rel in inputs):
        return "pip-tools"  # also dev-only .in next to [project] deps: --dev-requirements-file
    if any(not adds_no_dependency(root / rel) for rel in txt):
        return "pip"  # with [project] deps only dev files remain here: the pip route adds the dev group
    setup_cfg_project = re.search(r"^\[(metadata|options)\]", read(root / "setup.cfg"), re.M)  # not [flake8] only
    if (root / "setup.py").is_file() or setup_cfg_project:
        if has_project:  # a setup.py shim next to [project] is PEP 621; both declaring deps is two sources
            return "mixed" if setup_deps else "pep621"
        return "setuptools"
    return "pep621" if has_project else UNKNOWN


def requirement_lines(path: Path) -> List[str]:
    """Entries of a requirements file without comments (pip: `#` at the start or after whitespace)."""
    joined = re.sub(r"\\\r?\n", " ", read(path))  # `pkg==1 \` + `--hash=...` lines are one entry
    lines = [re.split(r"\s#", line)[0].strip() for line in joined.splitlines()]
    return [line for line in lines if line and not line.startswith("#")]


def runtime_lists(root: Path, rels: List[str]) -> List[str]:
    """Files among rels that hold runtime dependencies (not dev-named, not empty or self-install only)."""
    return [rel for rel in rels if not is_dev_file(rel) and not adds_no_dependency(root / rel)]


def nested_runtime(root: Path, rels: List[str]) -> List[str]:
    """Runtime lists below the root: not in docs/, tests/, examples/ or ci/, not notes, constraints or pins."""
    def plausible(rel: str) -> bool:
        name = Path(rel).name.lower()
        return (not any(part in NOT_SUBPROJECTS | {"ci"} for part in rel.split("/")[:-1])
                and not name.startswith(NOT_REQUIREMENTS) and "constraint" not in name
                and not name_tokens(rel) & PIN_NAME_TOKENS)
    return [rel for rel in runtime_lists(root, rels) if plausible(rel)]


def looks_exported(path: Path) -> bool:
    """`poetry export` / `pipenv requirements` output: every requirement pinned with ==."""
    entries = [line for line in requirement_lines(path) if not line.startswith("-")]
    # the specifier before `;` (a marker may say `python_version == "3.8"`); only `-r prod.txt`: judged itself
    return all("==" in line.split(";")[0] or " @ " in line for line in entries)  # exports keep `pkg @ git+...`


def adds_no_dependency(path: Path) -> bool:
    """A requirements file that installs only the project (`-e .` / `.`) or nothing (empty, comments):
    not a second dependency source."""
    return all(SELF_INSTALL.match(line) for line in requirement_lines(path))


def is_dev_file(rel: str) -> bool:
    """requirements-dev.txt, docs-requirements.txt, requirements.ci.txt; not -docker or -scipy."""
    return bool(name_tokens(rel) & DEV_NAME_TOKENS)


def is_uv_export(header: str) -> bool:
    """`uv export`, or `uv pip compile pyproject.toml`: both derived from the project, not a second source."""
    derived = UV_EXPORT_COMMAND.search(header) or re.search(r"^#\s+uv pip compile\b[^\n]*pyproject\.toml", header, re.M)
    return UV_EXPORT_MARKER in header and derived is not None


def detect_python(root: Path, pyproject: str, ci: List[str], subs: List[str]) -> Tuple[str, str]:
    """Return (x.y, file it came from); never falls back to the system Python."""
    pinned = [line.strip() for line in read(root / ".python-version").splitlines()
              if line.strip() and not line.strip().startswith("#")]
    version = major_minor(pinned[0]) if pinned else None
    if version:
        return version, ".python-version"
    candidates = [
        (toml_string(toml_section(pyproject, "project"), "requires-python"), PYPROJECT),
        (toml_string(toml_section(pyproject, "tool.poetry.dependencies"), "python") or poetry_python_table(pyproject),
         PYPROJECT),
    ]
    pipfile_requires = toml_section(read(root / "Pipfile"), "requires")
    for key in ("python_full_version", "python_version"):
        candidates.append((toml_string(pipfile_requires, key), "Pipfile"))
    for name in ("setup.cfg", "setup.py"):
        match = re.search(r"python_requires\s*=\s*[\"']?([^\"'\n]+)", strip_comments(read(root / name)))
        candidates.append((match.group(1) if match else None, name))
    for name in CONDA_ENV_FILES:
        match = CONDA_PYTHON_PATTERN.search(read(root / name))
        spec = (match.group(1) or match.group(2)) if match else None
        candidates.append((spec.lstrip("=").strip() if spec else None, name))
    runtime = read(root / "runtime.txt")
    is_heroku = runtime.strip().startswith("python-")  # runtime.txt of other buildpacks says nothing
    candidates.append((runtime.strip().replace("python-", "") if is_heroku else None, "runtime.txt"))
    for spec, origin in candidates:
        version = lower_bound(spec) if spec else None
        if version:
            return version, origin
    return runtime_python(root, ci, subs)


def tox_minors(envlist: str) -> List[str]:
    """Python 3 minors in a tox envlist: py38, py3.11, py{38,310}, py{3.9,3.10} and py3{9,10}."""
    minors = re.findall(r"\bpy3\.?(\d{1,2})\b", envlist)
    for items in re.findall(r"\bpy\{([\d.,\s]+)\}", envlist):  # tox 4 dotted: py{3.9,3.10}
        minors.extend(m for m in re.findall(r"\b3\.(\d{1,2})\b", items))
    for three, items in re.findall(r"\bpy(3?)\{([\d,\s]+)\}", envlist):
        for item in (i.strip() for i in items.split(",") if i.strip()):
            minor = item if three else item[1:]
            if three or item.startswith("3"):
                minors.append(minor)
    return [m for m in minors if m]


def runtime_python(root: Path, ci: List[str], subs: List[str]) -> Tuple[str, str]:
    """Lowest Python 3 x.y the project's own Dockerfile or CI files run on; a last resort.
    Files inside a subproject belong to that subproject."""
    found: List[Tuple[Tuple[int, ...], str, str]] = []
    pypy: List[Tuple[Tuple[int, ...], str, str]] = []  # used only when no CPython version is found
    for rel in outside(ci, subs):
        if any(part in NOT_SUBPROJECTS for part in rel.split("/")[:-1]):
            continue  # examples/, tests/, docs/ images say nothing about the project's Python
        text = re.sub(r"(?m)^[ \t]*#[^\n]*\n", "", read(root / rel))  # whole comment lines
        text = re.sub(r"\s#[^\n]*", "", text)  # trailing YAML/Docker comments
        for pattern in RUNTIME_PYTHON_PATTERNS:
            for span in pattern.findall(text):
                for prefix, version in re.findall(r"(?<![\d.])(pypy-?)?(\d+\.\d+)", span):
                    if version_key(version)[0] >= 3:
                        (pypy if prefix else found).append((version_key(version), version, rel))
        if rel.endswith("tox.ini"):
            for envlist in TOX_ENVLIST_PATTERN.findall(text):
                for minor in tox_minors(envlist):
                    found.append(((3, int(minor)), "3." + minor, rel))
    if found or pypy:
        _, version, origin = min(found or pypy)
        return version, origin
    venv = re.search(r"^version(?:_info)?\s*=\s*(\d+\.\d+)", read(root / VENV_CFG), re.M)
    return (venv.group(1), VENV_CFG) if venv else (UNKNOWN, NONE)


def project_name(pyproject: str) -> str:
    for table in ("project", "tool.poetry"):
        name = toml_string(toml_section(pyproject, table), "name")
        if name:
            return name
    return "missing"


def suggested_name(root: Path) -> str:
    return re.sub(r"[^a-z0-9]+", "-", root.name.lower()).strip("-") or "app"


def walk_tree(root: Path) -> Tuple[List[str], List[str], List[str]]:
    """One pruned walk: (subproject markers, requirements files, Dockerfiles) below the root.
    Subprojects skip test/example/doc folders, requirements skip only test fixtures, and
    only Dockerfiles are collected inside the top-level CI dot folders (.devcontainer)."""
    subs: List[str] = []
    requirements: List[str] = []
    dockerfiles: List[str] = []
    for folder, dirs, files in os.walk(root):  # unreadable folders are skipped by os.walk
        parts = Path(folder).relative_to(root).parts
        depth = len(parts)
        dirs[:] = [] if depth >= SUBPROJECT_DEPTH else sorted(
            d for d in dirs if d not in SKIP_DIRS and not NUMBERED_VENV.match(d)
            and (not d.startswith(".") or (depth == 0 and d in CI_DOT_DIRS)))
        if depth == 0:
            continue
        rel_folder = "/".join(parts)
        if depth <= 2:
            dockerfiles.extend(rel_folder + "/" + name for name in sorted(files)
                               if (name.startswith("Dockerfile") or name.endswith(".Dockerfile"))
                               and not name.endswith(".dockerignore"))
        if parts[0].startswith("."):
            continue
        if not any(part in NOT_SUBPROJECTS for part in parts):
            subs.extend([rel_folder + "/" + m for m in (PYPROJECT, "setup.py", "setup.cfg") if m in files][:1])
        if depth <= NESTED_REQUIREMENT_DEPTH and not any(part in FIXTURE_DIRS for part in parts):
            requirements.extend(rel_folder + "/" + name for name in sorted(files)
                                if name.endswith((".txt", ".in"))
                                and ("requirements" in name.lower() or parts[-1] in REQUIREMENT_DIRS))
    return subs, requirements, dockerfiles


def list_dir(folder: Path) -> List[Path]:
    try:
        return sorted(folder.iterdir())
    except OSError:
        return []


def ci_paths(root: Path, dockerfiles: List[str]) -> List[str]:
    """CI, Docker and task files; nested Dockerfiles come from walk_tree's pruned walk."""
    found: List[str] = []
    for pattern in CI_GLOBS:
        if pattern in NESTED_DOCKERFILES:
            paths = [root / rel for rel in dockerfiles if rel.count("/") == pattern.count("/")]
        else:
            paths = list(root.glob(pattern))
        for path in sorted(paths):
            parts = path.relative_to(root).parts
            folders = [p for p in parts[:-1] if p not in CI_DOT_DIRS]
            in_ci_dir = parts[0] in CI_DOT_DIRS  # .github/actions/build/ is config, not build output
            if (path.is_file() and not path.name.endswith(".dockerignore")
                    and not any((p in SKIP_DIRS and not in_ci_dir) or p.startswith(".") for p in folders)
                    and "/".join(parts) not in found):
                found.append("/".join(parts))
    return found


def ci_files(root: Path, ci: List[str]) -> List[str]:
    return [rel for rel in ci if OLD_MANAGER_PATTERN.search(read(root / rel))]


def private_index(root: Path, pyproject: str, requirements: List[str], ci: List[str]) -> str:
    index_tables = r"^\[\[tool\.(?:poetry\.source|uv\.index)\]\]\s*$(.*?)(?=^\[|\Z)"
    urls = [toml_string(table, "url") or "" for table in re.findall(index_tables, pyproject, re.M | re.S)]
    # `pkg @ https://host/pkg.whl` in any dependency list, Poetry `{ url = "https://..." }`
    urls += [url for pair in re.findall(r"@\s*(https?://[^\s\"';]+)|\{[^}\n]*\burl\s*=\s*[\"'](https?://[^\"']+)",
                                       pyproject) for url in pair]
    tool_uv = dict(re.findall(r"^\s*(index-url|extra-index-url|find-links)\s*=\s*(\[[^\]]*\]|[^\n]+)",
                              toml_section(pyproject, "tool.uv"), re.M))
    if any(not v.startswith("http") for v in re.findall(r"[\"']([^\"']+)[\"']", tool_uv.get("find-links", ""))):
        return "yes"  # a local find-links dir, like `-f ./wheels` in requirements
    tool_uv_values = list(tool_uv.values())
    tool_uv_values += re.findall(r"(?:^|\s)(?:url|index-url|extra-index-url|find-links)\s*=\s*(\[[^\]]*\]|[^\n]+)",
                                 read(root / "uv.toml"))  # arrays too
    urls += [url for value in tool_uv_values for url in URL_PATTERN.findall(value)]
    urls += re.findall(r"(?:url|file)\s*=\s*[\"']([^\"']+)", read(root / "Pipfile"))  # sources, `{file = "https://..."}`
    if any(url and not is_public(url) for url in urls):
        return "yes"  # an empty url: a Poetry source without url is the built-in PyPI
    sources = [(rel, INDEX_LINE_PATTERN) for rel in requirements + ["pip.conf", "pip.ini", *CONDA_ENV_FILES]]
    sources += [(rel, CI_INDEX_PATTERN) for rel in ci]  # CI: -f/-i count only on a pip install line
    for rel, pattern in sources:
        for line in re.sub(r"\\\r?\n", " ", read(root / rel)).splitlines():  # `RUN pip install \` + `-i URL`
            if line.lstrip().startswith("#") or not pattern.search(line):
                continue  # a commented-out install line is not in use
            line_urls = URL_PATTERN.findall(line)  # no URL: a local -f dir or a $VARIABLE, so private
            if not line_urls or not all(is_public(url) for url in line_urls) or VARIABLE_INDEX_PATTERN.search(line):
                return "yes"
    return "no"


def is_secret_value(value: str) -> bool:
    """A literal that looks like a secret, not a ${VAR}/$VAR/<placeholder>/boolean."""
    value = value.strip("\"'")
    if value.startswith(("<", ">", "=", "!", "~", "^")) or VERSION_LITERAL.match(value):
        return False  # a version, e.g. a dependency named *-token
    return (len(value) >= SECRET_MIN_LENGTH and not value.startswith(("$", "{"))
            and not any(char in value for char in "()[]")
            and value.lower() not in ("true", "false", "null", "none")
            and value.lower() not in DEFAULT_SECRET_VALUES
            and not PLACEHOLDER_WORDS.search(value)
            and not ATTRIBUTE_REFERENCE.match(value)
            and not ENV_VAR_NAME.match(value))


def credentials(root: Path, requirements: List[str], ci: List[str]) -> str:
    """file:line of plain-text secrets; the value itself is never printed."""
    candidates = requirements + list(SECRET_FILES) + ci
    hits: List[str] = []
    for rel in dict.fromkeys(candidates):
        for number, line in enumerate(read(root / rel).splitlines(), start=1):
            found = [m.group(1) for m in URL_SECRET_PATTERN.finditer(line)]
            found += [m.group(1) for m in TOKEN_USERINFO_PATTERN.finditer(line)]
            found += [m.group(2) for m in KEY_SECRET_PATTERN.finditer(line)]
            if any(is_secret_value(value) for value in found):
                hits.append("{}:{}".format(rel, number))
    return ",".join(hits) or NONE


def is_public(url: str) -> bool:
    return (urlparse(url).hostname or "") in PUBLIC_HOSTS


def outside(paths: List[str], subs: List[str]) -> List[str]:
    """paths that do not belong to a subproject (one project per run)."""
    sub_dirs = tuple(sub.rsplit("/", 1)[0] + "/" for sub in subs)
    return [rel for rel in paths if not (sub_dirs and rel.startswith(sub_dirs))]


def with_includes(root: Path, files: List[str]) -> List[str]:
    """files plus every file they pull in with -r/-c, recursively, in discovery order."""
    found = list(dict.fromkeys(files))
    for rel in found:  # grows while iterating; each file is visited once
        for target in INCLUDE_PATTERN.findall(read(root / rel)):
            path = ((root / rel).parent / target).resolve()
            try:
                included = path.relative_to(root).as_posix()
            except ValueError:  # outside the project
                continue
            if path.is_file() and included not in found:
                found.append(included)
    return found


def is_local_path(line: str) -> bool:
    """./lib, /abs, file:..., `pkg @ file:...`, libs/x, wheels/x.whl; never a URL or a spec."""
    if line.startswith((".", "/", "file:")) or " @ file:" in line:
        return True
    return "://" not in line and (RELATIVE_PATH.match(line) is not None or line.endswith(ARCHIVES))


def poetry_python_table(pyproject: str) -> Optional[str]:
    """`python = {version = "^3.10"}` in [tool.poetry.dependencies]."""
    match = re.search(r"^\s*python\s*=\s*\{[^}\n]*\bversion\s*=\s*[\"']([^\"']+)",
                      toml_section(pyproject, "tool.poetry.dependencies"), re.M)
    return match.group(1) if match else None


def option_name(line: str) -> str:
    """`--index-url=URL` → --index-url, `-ihttps://u:pw@host` → -i: never print the value (it may hold a password)."""
    word = line.split()[0].split("=")[0]
    return word if word.startswith("--") else word[:2]


def requirement_options(root: Path, files: List[str]) -> str:
    """List non-plain lines per file: migrate-to-uv drops them silently."""
    report: List[str] = []
    for rel in files:
        kinds: List[str] = []
        for line in requirement_lines(root / rel):
            line_kinds: List[str] = []
            if line.startswith("-"):
                line_kinds.append(option_name(line))
            elif " --hash" in line:
                line_kinds.append("--hash")  # joined `pkg==1 \` + `--hash=...`: hashed file, the guide drops them
            if VCS_PATTERN.search(line):
                line_kinds.append("git+")  # also for `-e git+...`: it needs a git source, not a path
            elif not line.startswith("-") and is_local_path(line) and not SELF_INSTALL.match(line):
                line_kinds.append("local-path")
            elif re.match(r"(-e|--editable)[\s=]", line) and not SELF_INSTALL.match(line):
                if is_local_path(re.split(r"[\s=]+", line, maxsplit=1)[1].strip("\"'")):
                    line_kinds.append("local-path")  # `-e ./libs/x`, unlike `-e .` (the project itself)
            kinds.extend(kind for kind in line_kinds if kind not in kinds)
        if kinds:
            report.append("{}({})".format(rel, ",".join(kinds)))
    return ";".join(report) or NONE


def git_state(root: Path) -> str:
    if not shutil.which("git"):
        return NONE
    try:
        result = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "--", "."],
                                capture_output=True, text=True, check=False,
                                env=dict(os.environ, LC_ALL="C"),  # English errors, whatever the locale
                                timeout=SUBPROCESS_TIMEOUT_SECONDS)
    except OSError:
        return NONE
    except subprocess.TimeoutExpired:
        return "dirty"  # a repo too slow to check: Step 2 asks instead of assuming a clean tree
    if result.returncode != 0:  # no repo → none; any other git error (dubious ownership) → ask
        return NONE if "not a git repository" in result.stderr else "dirty"
    for line in result.stdout.splitlines():
        path = line[3:].strip('"')
        if not line.startswith("?? ") or (path.endswith("/") and has_real_file(root, path)):
            return "dirty"
        if not path.endswith("/") and not GIT_JUNK.search(path):
            return "dirty"
    return "clean"


def has_real_file(root: Path, folder: str) -> bool:
    """An untracked folder holds a non-junk file. `folder` is relative to the repository root
    (porcelain output), hence the `:/` pathspec. A git error or time-out counts as a real file: Step 2 asks."""
    command = ["git", "-C", str(root), "ls-files", "--others", "--exclude-standard", "--", ":/" + folder]
    try:
        listing = subprocess.run(command, capture_output=True, text=True, check=False,
                                 timeout=SUBPROCESS_TIMEOUT_SECONDS)
    except (OSError, subprocess.TimeoutExpired):
        return True
    return listing.returncode != 0 or any(not GIT_JUNK.search(name) for name in listing.stdout.splitlines())


def uv_version() -> str:
    if not shutil.which("uv"):
        return "missing"
    try:
        result = subprocess.run(["uv", "--version"], capture_output=True, text=True, check=False,
                                timeout=SUBPROCESS_TIMEOUT_SECONDS)
    except (OSError, subprocess.TimeoutExpired):
        return "missing"
    match = re.search(r"\d+\.\d+\.\d+", result.stdout)
    return match.group(0) if match else "missing"


def inspect(root: Path) -> Dict[str, str]:
    pyproject = read(root / PYPROJECT)
    txt, inputs = requirement_files(root)
    every_requirement = with_includes(root, txt + inputs)
    subs, below_root, dockerfiles = walk_tree(root)
    nested = with_includes(root, [rel for rel in below_root if rel not in every_requirement])
    scanned = every_requirement + [rel for rel in nested if rel not in every_requirement]
    ci = ci_paths(root, dockerfiles)
    python, python_from = detect_python(root, pyproject, ci, subs)
    lockfiles = [n for n in LOCKFILES if (root / n).is_file()]
    nested_own = [rel for rel in outside(below_root, subs) if rel not in every_requirement]
    source = detect_source(root, pyproject, txt, inputs, nested_own)
    # the only dependency list sits below the root (src/requirements.txt): name it, so `mixed` is answerable
    nested_only = nested_runtime(root, nested_own) if source == "mixed" else []
    return {
        "source": source,
        "python": python,
        "python_from": python_from,
        "project_name": project_name(pyproject),
        "suggested_name": suggested_name(root),
        "requirements": ",".join(txt + inputs + nested_only) or NONE,
        # a compiled dev.txt next to its dev.in is a lock, not a list: `-r` it and every pin becomes direct
        "dev_requirements": ",".join(rel for rel in txt + inputs if is_dev_file(rel)
                                     and not (rel.endswith(".txt") and rel[:-4] + ".in" in inputs)) or NONE,
        "req_options": requirement_options(root, every_requirement + with_includes(root, nested_only)),
        "lockfiles": ",".join(lockfiles) or NONE,
        "subprojects": ",".join(subs) or NONE,
        "ci": ",".join(ci_files(root, ci)) or NONE,
        "private_index": private_index(root, pyproject, outside(scanned, subs), outside(ci, subs)),
        "credentials": credentials(root, scanned, ci),
        "git": git_state(root),
        "uv": uv_version(),
    }


def main(argv: List[str]) -> int:
    if len(argv) > 2:
        print("Usage: inspect-project.py [PROJECT_DIR]", file=sys.stderr)
        return 2
    root = Path(argv[1] if len(argv) == 2 else ".").resolve()
    if not root.is_dir():
        print("Not a directory: {}".format(root), file=sys.stderr)
        return 2
    for key, value in inspect(root).items():
        print("{}={}".format(key, value))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
