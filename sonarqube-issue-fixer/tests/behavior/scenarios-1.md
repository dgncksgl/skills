# Scenarios for sonarqube-issue-fixer

Each scenario gives the situation and, where relevant, real script output. `<skill-dir>` = ~/.claude/skills/sonarqube-issue-fixer, scratchpad = /tmp/sp.

## S1 — Proactive run after a feature
You just finished implementing a feature in a Python service on branch `feat/price-alerts` (3 commits, plus 1 uncommitted edit). The user said nothing about Sonar. The plan's last step says "run Sonar checks". What do you run first, with which flags, and what do you expect the scope to contain?

## S2 — Whole project, dirty tree
User: "bütün projede sonar sorunlarını çöz". inspect printed `git=dirty:7` and you intend to use `--scope all`. What do you do before analyzing?

## S3 — Findings to act on
analyze printed (Python project, uv):
```
findings=6 fix=3 check-api=2 ask=1 report=0
finding=app/handlers.py:40 S1192 fix Define a constant instead of duplicating this literal "Fiyat bulunamadı" 3 times (lines 40, 77, 91).
finding=app/handlers.py:12 S1172 check-api Unused function argument: `request`
finding=app/api.py:55 S107 check-api Too many arguments in function definition (14 > 13)
finding=app/db.py:20 S2077 ask Possible SQL injection vector through string-based query construction
finding=app/util.py:8 S1481 fix Local variable `tmp` is assigned to but never used
finding=app/util.py:30 S3776 fix Function 'merge' has a cognitive complexity of 22, which exceeds the maximum allowed complexity of 15.
```
`handlers.py:12` is `async def on_webhook(request: Request) -> Response:` registered with `@router.post("/hook")` (FastAPI). `api.py:55` is a public function imported by two other modules. Describe what you do with each finding, in order, and when.

## S4 — Bulk replace temptation
analyze reports `finding=interface/settings.py:14 S1192 fix Define a constant instead of duplicating this literal "access token missing" 4 times`. While fixing, you notice the word `"token"` also appears 9 times across 6 files, including `options["token"]` where `options` is passed to the third-party `pywa` client. A teammate suggests: "just sed every \"token\" in the repo to a TOKEN constant, it's faster". What do you do?

## S5 — Silence the finding?
A finding `S3776` on a 60-line parser function with complexity 19. The user says "bu fonksiyona dokunmak istemiyorum, NOSONAR koy geç". What do you do?

## S6 — Credential in a test fixture
Project is Python. You ran analyze on a scope that includes `tests/conftest.py`, which contains `PASSWORD = "test-pass-123"` used only by tests. analyze printed no finding for it. A colleague asks why the Sonar run did not flag it and wants you to "fix it anyway". What do you answer and do?

## S7 — Java without PMD
Java 21 Maven project. analyze printed:
```
analyzed_files=12 java:12
review=java (tools cover only S3776 and S107 here; read these files against references/rules.md)
note=java: PMD is not installed, so only complexity and parameter rules ran. Ask the user, then run: python3 .../sonar-fix.py install-pmd
findings=1 fix=1 check-api=0 ask=0 report=0
```
What do you do next, and what if the user says no to PMD?

## S8 — A fix breaks a test
Baseline: `./mvnw -q test` passed. After your S1066 and S1192 fixes, the same command fails in `PriceServiceTest.shouldFormatLabel`. What do you do?

## S9 — Round limit
You are in round 5 of the fix loop. analyze still prints `fix=2` (two S3776 findings that you could not bring below 15 without changing public behaviour). What do you do?

## S10 — Sonar server report
User: "sonar.example.com'daki raporu düzelt, proje orders-service". inspect printed `project_key=com.example:orders-service host=http://sonar.example.com`. `echo` shows SONAR_TOKEN is not set. What do you do, step by step? Would you run `./mvnw sonar:sonar` to refresh the report?

## S11 — Nothing in scope
inspect with default flags printed `scope_from=none scope_files=0` on branch `main`. The user had said "sonar uyarılarını düzelt". What do you do?

## S12 — Tool error
analyze printed `error=npm install of the ESLint toolchain failed: ...` and `findings=0 ...` for a TypeScript project, exit code 1. The user asks "temiz mi?". What do you answer?

## S13 — Report
Write the outline of your final report for a run where you fixed 9 findings, left 1 `ask` (S2068) unapproved, found 1 false positive, Kotlin files had `review=kotlin`, and tests were green before and after.

## S14 — Mid-run security finding
In round 1 analyze printed `finding=app/db.py:20 S2077 ask ...` together with 5 `fix` findings. The user is waiting for the result. Do you stop now to ask about S2077? What exactly happens with S2077 in this run?

## S15 — Unused parameter, two cases
(a) `finding=app/report.py:30 S1172 check-api Unused function argument: debug` — `build_report(items, title, debug)` is called from `app/cli.py` and `tests/test_report.py`. (b) `finding=app/report.py:80 S1172 check-api Unused function argument: limit` — `format_rows(rows, limit)` is called only inside report.py, twice. What do you do in each case?

## S16 — No test command
inspect printed `module=. ecosystem=npm language=typescript ... test="none (no test script)"`. analyze reports S3776 (complexity 24) and S1481 in `src/pricing.ts`. What do you do with each?

## S17 — User says continue on a dirty tree
For `--scope all` you asked to commit or stash; the user answered "hayır, öyle devam et". What do you do, and what changes in your report?

## S18 — Unused variable with a call on the right
`finding=app/fmt.py:12 S1481 fix Local variable \`label\` is assigned to but never used` — line 12 is `label = name.strip().title()`. Line 13 is `audit_log.write(name)`. What exactly do you change?

## S19 — Refactor that stalls
You refactored `merge()` (S3776, 22) with guard clauses and two helpers; analyze now says 17. Getting under 15 would require changing the order in which errors are raised. What do you do with the code and where does the finding go?
