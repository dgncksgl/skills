# Scenarios for sonarqube-issue-fixer (round 2)

Answer each scenario from the skill's files only (`~/.claude/skills/sonarqube-issue-fixer/SKILL.md` and the files it links). Say what you do, in order, and why, citing the skill text. Keep each answer under 120 words.

## S20 — Hand-written file listed as generated
`inspect --scope all` printed `excluded=generated:1` and `generated_files=src/billing/report_builder.py`. You open it: the first line is `# The file is generated nightly by cron.sh from this script's output` and the rest is clearly hand-written business logic. What do you do with this file?

## S21 — Bare except around an await
`finding=app/client.py:41 S5754 ask Specify an exception class to catch or reraise the exception`. Lines 38–42 are `try: return await session.get(url)` / `except: return None` inside an `async def`. The user said "fix everything you can". What happens to this finding in this run?

## S22 — SYNTAX on match
Python project, `requires-python = ">=3.9"`, inspect printed `build="none (analyze reports syntax errors)"` and a uv test command. analyze printed `finding=app/route.py:7 SYNTAX fix Cannot use match statement on Python 3.9`. `uv run --frozen python -c "import ast,sys; ast.parse(open(sys.argv[1]).read())" app/route.py` succeeds. What do you do?

## S23 — Side-effect import
`finding=shop/app.py:3 S1128 check-api 'shop.signals' imported but unused`. `shop/signals.py` registers Django signal handlers at import time, and nothing else imports it. What do you do?

## S24 — Unused len()
`finding=api/upload.py:20 S1481 fix Local variable 'size' is assigned to but never used`. Line 20 is `size = len(payload)`. `payload` comes straight from the request body and can be `None` (callers rely on the TypeError being raised and turned into a 400 response). What exactly do you change?

## S25 — noqa with a ruff code
The project has `except:  # noqa: E722` on line 55 of `jobs/worker.py` (no await, no exit call in the try body). analyze still prints `finding=jobs/worker.py:55 S5754 fix`. The user asks: "orada noqa var, neden hâlâ çıkıyor? NOSONAR ekleyip geç". What do you answer and do?

## S26 — Bun project baseline
inspect printed `module=web ecosystem=bun language=typescript ... build="npx --no-install tsc --noEmit -p tsconfig.json" test="bun run test"`. Before your first edit, what exactly do you run, where, and what do you record?

## S27 — Bare except, exit happens deeper
`finding=cli/run.py:30 S5754 fix`. The try body calls `main()`, and `main()` (in another file) calls `sys.exit(2)` on bad arguments. The try body itself contains no `sys.exit`, `exit()` or `raise SystemExit`. What do you change, and what do you say in the report?

## S29 — Generic request
This skill was invoked for the user message "kod kalitesini artır" in a Python repository; no Sonar rule, report or warning was mentioned. What do you do first?

## S30 — Config edit
This skill was invoked for "sonar-project.properties dosyasına legacy/ klasörü için exclusion ekle". What do you do?

## S28 — Server report with a file inspect drops
The user shared an `api/issues/search` export. You ran `import`, then `inspect --paths <the report's files>`; it printed `excluded=outside-sonar.sources:1` for `tools/migrate.py`, which the report has an S1481 `fix` finding for. Is `tools/migrate.py` part of the scope for Steps 3–6?
