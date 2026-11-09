# Tests

Read this when you change `scripts/sonar-fix.py`, `scripts/data/rules.json`, `SKILL.md` or the references, and need to show the skill still works. Nothing here is loaded when the skill runs.

## Automated layers

Run all of them with `bash tests/run_all.sh` (about 5 minutes; needs python3, uv, node/npm and git). It runs each layer with `python3` and, when present, macOS's `/usr/bin/python3` (3.9, the oldest supported).

| Layer | File | What it proves |
|---|---|---|
| Unit | `unit/test_sonar_fix.py` | Each helper on small inputs: scope rules, Sonar settings, test classification, S5754 decisions, suppression markers, import mapping |
| End to end | `e2e/e2e.sh` | The CLI on the fixture projects in `e2e/fixtures` and on generated git repos |
| PMD | `e2e/e2e_pmd.sh` | Java through PMD; runs only when PMD is cached (`sonar-fix.py install-pmd`) |
| Matrix | `matrix/run_matrix.py` | 20 project types (uv, poetry, plain scripts, Maven single and multi-module, Gradle Kotlin, npm, bun, pnpm, Go, C#, Sonar settings, git states, report import, odd paths, 300 files) with expectations written before the first run |

Work folders go to `$WORK` or the system temp folder, never into the repository. Point `SONARFIX_SCRIPT` at another copy of the script to test it instead.

## Live runs (by hand, with agents)

These check that an agent following SKILL.md fixes real projects without breaking them.

1. `python3 tests/live/build.py` builds three git projects with seeded issues and traps: `orders` (Python, uv), `pricing` (JavaScript, `node --test`) and `reportfix` (Python, fixed from a SonarQube export).
2. Give each project to a fresh agent with the skill, one model per project, with this prompt:

   > You are acting as Claude Code helping a developer. The project is at `<path>`. The user's message is: "bütün projede sonar sorunlarını çöz" (for `reportfix`: "SonarQube raporunu indirdim, şu dosyalarda: `<work>/reportfix-issues.json` ve `<work>/reportfix-hotspots.json`. Bu rapordaki sorunları düzelt."). A skill applies to this request: `~/.claude/skills/sonarqube-issue-fixer`. Read its SKILL.md first and follow it exactly. Work only inside the project folder and your own scratch folder. The user is away until you finish; anything the skill says to collect for the user goes into your final report. Never commit, push, stash or reset. Reply with the final report the skill describes, in Turkish.

3. `python3 tests/live/check.py <orders|pricing|reportfix>` checks the result: no commit, tests still pass, only the expected file changed, no suppression added, every `fix` finding gone, every decision (passwords, SQL, `eval`, async bare `except`, side-effect import, public signatures) left untouched. On an untouched project it must fail.

## Behaviour scenarios (by hand, with agents)

`behavior/scenarios-1.md` (S1–S19) and `behavior/scenarios-2.md` (S20–S28) are situations an agent meets while using the skill; `key-1.md` and `key-2.md` are the answers, written before any run. Give a fresh agent the skill and one scenario file, never the key, and ask for its actions in order with the skill sentences it relies on and any ambiguity it sees. Score against the key; a real ambiguity that two models resolve differently is a gap in the skill text.
