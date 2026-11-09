# Tools

Read this when fetching a SonarQube report, when a tool fails (`error=`), or when asked which analyzers ran.

## Analyzers

Pinned in `scripts/sonar-fix.py` (versions as of 2026-11-09). Nothing is installed into the project. The uvx and npm tools below download automatically on first use; PMD is the only one that waits for the user's yes.

| Tool | How it runs | Needs |
|---|---|---|
| ruff 0.17.4, complexipy 8.3.0, lizard 1.25.1 | `uvx <tool>@<version>` (downloaded once by uv) | `uv` |
| eslint 10.14.0 + eslint-plugin-sonarjs 4.2.2 + typescript-eslint 8.72.1 + typescript 6.0.3 | installed once with `npm install --prefix ~/.cache/sonarqube-issue-fixer/eslint-sonarjs-4.2.2` | `node`, `npm` |
| PMD 7.29.0 | `sonar-fix.py install-pmd`, only after the user agrees: downloads about 135 MB from GitHub, checks SHA-256, unpacks to `~/.cache/sonarqube-issue-fixer/pmd-bin-7.29.0` | `java` |

Suppression comments follow SonarQube, not the tools: a finding on a line with a `NOSONAR` comment, or inside a declaration annotated for that rule (Java `@SuppressWarnings("java:Sxxxx")`, `"all"` or a javac key such as `"unused"` that SonarJava maps to rules; Kotlin `@Suppress("kotlin:Sxxxx")` on the function itself; class-level and `@file:Suppress` are not read), is dropped; `// NOPMD`, `@SuppressWarnings("PMD…")` and `eslint-disable` are ignored, and Java locals named `unused…`/`ignored…` are reported (PMD skips them; SonarJava does not). In Python, as in SonarQube, a bare `# noqa` hides the line, while `# noqa: S1481` and `# NOSONAR(S1481)` hide only the listed Sonar rules; ruff codes (`# noqa: E722`) and file-level `# flake8: noqa` / `# ruff: noqa` hide nothing.

The npm install pins only the four packages named above; their own dependencies resolve at install time, so a cache rebuilt later can differ slightly. Compare before/after findings from the same cache, never across a reinstall.

The cache follows `$XDG_CACHE_HOME` when set. Delete the cache folder to force a clean reinstall. To move to newer analyzer versions, change the version constants at the top of `scripts/sonar-fix.py` (PMD also needs its new SHA-256) and re-check the rule mapping in `scripts/data/rules.json`.

## Fetching a SonarQube report

Use this when the user points at a SonarQube server (for example `host=` from inspect) and has a token.

1. Check `test -n "$SONAR_TOKEN" && echo set` (never `echo $SONAR_TOKEN`: it prints the token). Nothing printed → ask the user to set `SONAR_TOKEN` in the shell profile and restart Claude Code. Never ask for the token in the chat.
2. `host` starting with `http://` → try the same URL with `https://` first; send the token over plain `http://` only after the user agrees (it travels unencrypted).
3. Issues of the project (add `&branch=<name>` or `&pullRequest=<id>` when not on the main branch):
   `curl -sS -w '%{http_code}\n' -H "Authorization: Bearer $SONAR_TOKEN" "<host>/api/issues/search?componentKeys=<project_key>&resolved=false&ps=500&p=1" -o <scratchpad>/sonar-p1.json` (prints the HTTP status; only 200 means the file holds issues)
   HTTP 401 with a token that works in the browser → the server is older than SonarQube 10 and wants the token as the user name: replace the header with `-u "$SONAR_TOKEN:"`.
   Repeat with `p=2, 3, …` while `paging.total` is larger than `p × 500`; the API returns at most 10 000 results, so filter with `&types=BUG,VULNERABILITY,CODE_SMELL` or by file (`&components=<project_key>:<path>`) when larger.
4. Security hotspots: `<host>/api/hotspots/search?projectKey=<project_key>&status=TO_REVIEW&ps=500&p=1` (same `&branch=` or `&pullRequest=`) into `<scratchpad>/sonar-hotspots-p1.json`, paged the same way.
5. Convert: `python3 <skill-dir>/scripts/sonar-fix.py import <project-dir> <scratchpad>/sonar-*.json --out <scratchpad>/findings.json`. A `note=` about missing files means the report is for another branch or root. Issues on the project itself (no file) show as `(project)`: report them, and leave them out of `--paths`.

HTTP status 401 → token (see the retry above), 403 → permission, 404 → project key or host. An unreachable host usually means VPN. SonarQube Cloud also needs `&organization=<org>`.

A server's report reflects its last analysis, not the working tree: after fixing, verify with `analyze`, never by re-running the server analysis.

Script exit codes: 0 = done (with or without findings), 1 = a step failed and `error=` lines say which files were not analyzed, 2 = wrong arguments.

## Troubleshooting

| Output | Meaning | Do |
|---|---|---|
| `error=ruff exit 2` | ruff could not run (bad Python target, uv offline) | Check `uvx ruff@0.17.4 --version`; offline → ask the user |
| `error=npm install of the ESLint toolchain failed` | No network or npm registry blocked | Report JS/TS as not analyzed |
| `finding=… SYNTAX` | The parser could not read the file | Fix only if the project's own build fails too; otherwise report it: the analyzer is older than the syntax, or the file uses syntax newer than the project's declared minimum version |
| `error=pmd could not parse …` | Java syntax newer than PMD supports | Review that file by hand (checklist in Rules) |
| `error=java not found` | No JDK on PATH | Lizard results only; say so |
| `note=… S1192 and S5754 checks skipped, this Python cannot parse it` | The project uses syntax newer than the `python3` running the script | Run the script with a Python at least as new as the project's syntax, without touching the project: `uv run --no-project --python <version> python3 <skill-dir>/scripts/sonar-fix.py …` (`uv python list` shows what is available) or review S1192 and S5754 by hand |
