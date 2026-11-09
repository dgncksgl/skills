---
name: sonarqube-issue-fixer
description: "Finds and fixes SonarQube issues in Python, Java, Kotlin, JavaScript, TypeScript and more, from a SonarQube report or pinned local analyzers, without changing behaviour. Use when the user asks to fix Sonar warnings or SonarQube/SonarCloud issues, clean up static analysis, reduce cognitive complexity, shares a Sonar report, names a rule ID such as S1192, S3776, S2068 or S1481, or says \"sonar sorunlarını çöz\", \"sonar uyarılarını düzelt\", \"sonarqube issue'larını çöz\", \"kod kokularını gider\", \"statik analiz uyarılarını temizle\", \"karmaşıklığı azalt\", \"bütün projede sonar'ı düzelt\". Use proactively after an implementation or refactor step, on the changed files only. Do not use for a general code-quality request that names no Sonar rule, report or warning, for pure formatting or import ordering, for IDE type warnings (type-safety-fixer), for a security audit of pending changes (/security-review), or for editing config or markup files (sonar-project.properties, XML, YAML, JSON, Markdown)."
---

# SonarQube Issue Fixer

## Overview

Fixes Sonar findings that a SonarQube report or a pinned analyzer produced. Code is read for findings only through the manual checklist, for languages the tools do not cover. `<skill-dir>` is this skill's base directory. Invoked only to edit Sonar configuration? Make that edit without this workflow. Invoked for a request naming no Sonar rule, report or warning? Offer this workflow instead of running it.

## Core Rules

- Evidence first: a rule not in the analyzer output, the Sonar report or your checklist notes is not a finding.
- Preserve behaviour: same inputs, outputs, exceptions, log text, and the names and signatures that code outside the file uses. The one planned exception is S5754 (bare `except:` or `except BaseException:` → `except Exception:`), see Fix Recipes. Minimal change, one finding per edit, match the file's style, no new finding.
- Never silence a finding (`NOSONAR`, `# noqa`, `@SuppressWarnings`, `eslint-disable`, renaming to dodge a detector), even when the user asks: explain, leave the code, and report the finding as not fixed by the user's decision. A false positive goes in the report with its reason.
- No bulk find-and-replace: read each site before editing it. One constant per meaning, not per spelling.
- `check-api` findings: grep the whole project for the name (tests count as callers). Fix only when no caller outside the file, no framework and no override depends on it; a signature a framework or base class requires (pytest fixture, interface method, a handler parameter the framework fills) is a false positive; anything else is a decision.
- Decisions: blocking questions are asked when they arise, before any edit (dirty tree for `--scope all`, PMD install when analyze asks for it, missing `SONAR_TOKEN`). All other decisions (`ask` findings, `check-api` decisions, fixes that would change behaviour) are collected and asked once, in the Step 7 report; approved items are fixed in a follow-up run of Steps 3–6.
- Edit only files in the scope (for a Sonar report: the report's files). Dependency directories may be read, never written.
- Never commit, push, stash or reset. Never run an analysis that uploads to a shared SonarQube server (`mvn sonar:sonar`, `sonar-scanner`); reading its Web API is fine.
- `SONAR_TOKEN` comes from the environment; never print it, write it to a file or ask for it in chat. Report `credential=` lines from inspect by location only.

## Workflow

### Step 1: Inspect and choose the scope

Run `python3 <skill-dir>/scripts/sonar-fix.py inspect <project-dir> <flags> --out <scratchpad>/scope.txt`:

| The user said | Flags |
|---|---|
| Nothing (proactive run, "fix sonar issues") | none: `--scope changed`, uncommitted files plus branch commits since the default branch (`default_branch=unknown` or another base such as `develop` → add `--base <branch>`, a local or remote name such as `origin/develop`) |
| "Whole project", "bütün projede", "tüm proje" | `--scope all` |
| Named files or folders | `--paths <p> ...` |

Test files inside the scope are kept; `analyze` applies only the rules Sonar runs on tests. `scope_files=0` → say there is nothing to fix and offer `--scope all`. `error=` (no git) → ask for `--scope all` or `--paths`. `git=dirty:<n>` with `--scope all` → ask the user to commit or stash first; if they decline, save `git diff HEAD` and `git status --porcelain --untracked-files=all` to the scratchpad before editing, and report your edits apart from theirs. Each `module=` line holds that module's `build` and `test` commands, run inside its directory. `generated_files=` and `guessed_build_files=` list files left out on a guess; append a clearly hand-written one to the scope list.

### Step 2: Collect findings

- **Sonar report given:** API or JSON export → fetch and convert it per [Tools](references/tools.md); a list pasted from the UI → use it as the findings list. Then run inspect again with `--paths <the report's files>`: that list, with any report file it leaves out appended (the server analyzed it), is the scope for Steps 3–6. No token, or the server is unreachable → say so and offer the local `analyze` instead.
- **No report:** run `python3 <skill-dir>/scripts/sonar-fix.py analyze <project-dir> --files-from <scratchpad>/scope.txt --out <scratchpad>/findings.json`.
  - `note=java: PMD is not installed` → ask once per session; yes → `sonar-fix.py install-pmd` and analyze again; no → continue.
  - `review=<language>` (and Java without PMD) → read those scope files once against the checklist in [Rules](references/rules.md); record each hit with file, line and rule, marked "found by reading".
  - `error=` → that tool's files were not analyzed: never report them as clean; say so, and offer the checklist or a retry.

Each finding has an `action`: `fix`, `check-api` (see Core Rules), `ask` (any rule with a security impact, including former hotspots such as S1313: a decision), `report` (TODO/FIXME: list only).

### Step 3: Baseline

Before editing, run the `build`, `test` and (when printed) `typecheck` commands of every module that holds scope files. Failures are pre-existing: record them; a fix must not add one. A command ending in `(missing: <tool>)` cannot run: do not run it, treat it like `none`, and name the missing tool in the report (ask before installing it). A module with `test=none (...)` or a missing test tool has no safety net: put non-trivial restructurings (S3776, S107) on the decisions list instead of doing them.

### Step 4: Fix

Order: bugs, then `fix` code smells, then `check-api` items that pass the Core Rules test. A fix that cannot be done without changing behaviour (for example S3776 that stays above 15) is edited back and becomes a decision. `SYNTAX` findings: fix only when the module's own build also fails on that file (build `none` → parse the file with the interpreter the module's `test` command uses, for example `uv run --frozen python -c "import ast,sys; ast.parse(open(sys.argv[1]).read())" <file>` or `.venv/bin/python -c …`, or `node --check <file>`); otherwise report it without editing: either the analyzer is older than the syntax, or the file uses syntax newer than the project's declared minimum version (for example `match` with `requires-python >= 3.9`). Follow [Fix Recipes](references/fix-recipes.md). After removing code, remove what only it used.

### Step 5: Verify

1. Run `analyze` again on the same scope list: each fixed finding is gone and the touched files have no new one (the BROAD-EXCEPT that an S5754 fix creates is expected: it goes to the decisions list). A report finding no local tool covers: re-read the code; the server's next analysis confirms it.
2. Run the Step 3 commands again: no new failure.
3. A new failure → undo this round's fixes one at a time, newest first, by editing them back (never `git checkout`: it also drops other edits), re-running the failing test after each. Re-apply the innocent ones and run the full test command again; record the culprit as skipped with the failing test as the reason.

### Step 6: Loop until clean

Repeat Steps 4–5 until `analyze` shows no `fix` finding you still intend to fix, at most 5 rounds. False positives, user-declined findings and fixes that would change behaviour are out of the loop. Do not ask whether to continue. Findings that would need a behaviour change are decisions; other `fix` findings still open after round 5 go to the report as left at the round limit.

### Step 7: Report

In the user's language:
1. Scope (`scope_from`, file count, tests included), source of findings (Sonar report, or local analyzers with versions), languages analyzed only partly or not at all.
2. Fixed findings: file, rule, what changed; one concrete before/after example. `[not in Sonar way]` items listed apart.
3. Not fixed: false positives with the reason, skipped fixes, findings left at the round limit, user-declined findings, `report` items (TODO/FIXME).
4. Decisions needed: every `ask`, open `check-api` and behaviour-changing item, each with the risk and the proposed change.
5. Build and test results against the baseline; pre-existing failures.
6. Local analyzers approximate SonarQube; the server's next analysis is the final word. Nothing committed.

## Additional Resources

- [Rules](references/rules.md): coverage per language, thresholds, rule scopes, manual checklist
- [Fix Recipes](references/fix-recipes.md): how to fix each rule family without changing behaviour
- [Tools](references/tools.md): analyzer versions, cache, PMD, Sonar Web API, troubleshooting
