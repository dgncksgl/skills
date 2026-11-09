# Tests

Read this when you change `scripts/sonar-fix.py`, `scripts/data/rules.json`, `SKILL.md` or the references, and need to show the skill still works. Nothing here is loaded when the skill runs.

## Automated layers (no tokens)

`bash tests/run_all.sh` (about 5 minutes; needs python3, uv, node/npm and git) runs each layer with `python3` and, when present, macOS's `/usr/bin/python3` (3.9, the oldest supported).

| Layer | File | What it proves |
|---|---|---|
| Unit | `unit/test_sonar_fix.py` | Each helper on small inputs: scope rules, Sonar settings, test classification, S5754 decisions, suppression markers, import mapping |
| End to end | `e2e/e2e.sh` | The CLI on the fixture projects in `e2e/fixtures` and on generated git repos |
| PMD | `e2e/e2e_pmd.sh` | Java through PMD; runs only when PMD is cached (`sonar-fix.py install-pmd`) |
| Matrix | `matrix/run_matrix.py` | 20 project types (uv, poetry, plain scripts, Maven single and multi-module, Gradle Kotlin, npm, bun, pnpm, Go, C#, Sonar settings, git states, report import, odd paths, 300 files) with expectations written before the first run |

Work folders go to `$WORK` or the system temp folder, never into the repository. Point `SONARFIX_SCRIPT` at another copy of the script to test it instead.

## Agent layers (spend tokens)

`bash tests/agents/run_agents.sh <triggers|scenarios|live|all> [model]` runs headless Claude Code (`claude -p`, default model `sonnet`). User settings and their hooks are left out (`--setting-sources project,local`) so they cannot steer the answers; skills come from a sandbox copy of the sibling skills. Results and the agents' answers stay in `$WORK` (printed at the end).

| Layer | Files | What it proves |
|---|---|---|
| `triggers` | `behavior/triggers.json` | For 16 messages (8 Sonar requests, 8 near misses such as type warnings, formatting, a security review, a config edit), whether the model picks this skill |
| `scenarios` | `behavior/scenarios-1.md` (S1–S19), `behavior/scenarios-2.md` (S20–S30) | An agent given only the skill (never the keys) answers each situation; a second call grades it against `key-1.md` / `key-2.md`, written before any run |
| `live` | `live/build.py`, `live/check.py` | An agent follows the skill end to end on three seeded git projects: `orders` (Python, uv), `pricing` (JavaScript, `node --test`), `reportfix` (Python, fixed from a SonarQube export); `check.py` then demands no commit, green tests, only the expected file changed, no suppression, no `fix` finding left and every decision (passwords, SQL, `eval`, async bare `except`, side-effect import, public signatures) untouched |

The live layer lets the agent run shell commands and edit files inside its temp project (`--permission-mode acceptEdits --allowedTools "Bash Read Edit Write Grep Glob"`); run it yourself, not from an unattended job. `python3 tests/live/check.py <name>` on an untouched project must fail, which is how the checker itself is tested.

Results on 2026-11-09: triggers 16/16 on sonnet and opus, 14/16 on haiku (it still picks this skill for "kod kalitesini artır" and a `sonar-project.properties` edit; the skill's first paragraph then tells it to offer the workflow or make the plain edit instead, scenarios S29–S30); scenarios 30/30 on haiku, sonnet and opus (the grader gave 0/11 to a set of deliberately wrong answers); live 3/3 projects passed when run as Claude Code subagents (orders on opus, pricing on sonnet, reportfix on haiku).
