---
name: create-skill
description: "Creates, edits, validates and audits Claude skills (SKILL.md plus optional references/ and scripts/) so they stay lean, trigger reliably and are tested before use. Use when asked to create a skill, author a skill, scaffold a skill, write a new skill, edit or improve an existing skill, audit a skill, validate a skill, lint a SKILL.md, or when user says \"skill oluştur\", \"yeni skill yaz\", \"skill üret\", \"skill hazırla\", \"skill iskeletini oluştur\", \"skill'i denetle\", \"skill'i standartlara uydur\", \"mevcut skill'i kontrol et\", \"skill audit et\", \"skill uyumluluğunu kontrol et\", \"skill'i güncelle\". Use proactively when a user repeats multi-step instructions across sessions — that is a skill candidate. Do not use for editing ~/.cursor/skills-cursor/ (Cursor-reserved), generic documentation, single-file refactoring, or non-skill markdown."
---

# Create-Skill Meta-Skill

## Overview

This skill manages the lifecycle of Claude skills: **Create** (a new skill from scratch), **Edit** (change an existing skill), **Validate** (pass/fail format check) and **Audit** (0-100 score with refactor suggestions). It keeps skills lean, fast-triggering, token-efficient and tested.

All script paths below are relative to this skill's directory, `~/.claude/skills/create-skill/`; from any other working directory, call them by that absolute path.

## Three Core Principles

| Principle | Rule | Where excess content goes |
|---|---|---|
| Word budget | SKILL.md ≤ 2000 words (ideal: ≤ 1000) | `references/*.md` |
| Progressive disclosure | Tables >10 rows, lists >15 items, >3 code blocks → offload | `references/*.md` |
| Scripts are free | Deterministic logic ≥5 branches → script | `scripts/` |

See [Scripts Guidelines](references/scripts-guidelines.md) for the token-cost comparison and decision table.

## Workflow Router

- **Create**: user wants a new skill → Create Workflow
- **Edit**: user wants an existing skill changed or improved → read the whole skill, make the change following Steps 3–4, then Steps 5 and 6. The Step 6 baseline is the problem that prompted the edit; a description-only edit needs only the trigger test in Step 6
- **Validate**: user wants a pass/fail format check → Validate Workflow
- **Audit**: user wants a score and refactor suggestions → Audit Workflow

## Create Workflow

### Step 1: Gather Requirements

Infer from context what you can; ask the user only for what you cannot infer:
- What does the skill do? (one sentence)
- Where will it live? (`~/.claude/skills/` for personal, `<project>/.claude/skills/` for project-scoped)
- Trigger scenarios in English AND Turkish, and anti-scenarios (when NOT to use)
- **Baseline:** what goes wrong today without the skill? Collect real evidence (past session transcripts, the user's repeated instructions); run the task once without the skill only if that costs nothing or the user agrees. Write down each failure; Step 6 tests against them. No observed failure → tell the user no skill is needed; if they still want one, build it and take Step 6 scenarios from their description.
- **Name:** 1–64 chars of `a-z`, `0-9` and single hyphens, no leading or trailing hyphen, no "claude" or "anthropic". It must not already exist in `~/.claude/skills/`, the project's `.claude/skills/`, or the available-skills list. A personal or project skill with a bundled skill's name (for example `code-review`) replaces that bundled skill; warn the user and propose another name.

### Step 2: Scaffold Directory

Run `bash scripts/scaffold.sh <skill-name> [--location PARENT_DIR] [--force]`. `PARENT_DIR` is the directory that will contain the skill folder (default `~/.claude/skills`). `--force` rewrites only SKILL.md of an existing skill and keeps its other files: read the old SKILL.md first, make sure it is in git or backed up, get the user's consent, and afterwards relink or remove the kept files.

This creates `SKILL.md` with frontmatter skeleton and `TODO:` placeholders, and `references/.gitkeep` (delete it once a real reference exists, or delete the empty `references/` if none is needed). Create `scripts/` only when Step 4 puts a script in it.

### Step 3: Write the Description

The description is the #1 factor in whether a skill triggers. Write it in English with quoted Turkish trigger phrases:

```
<WHAT in one sentence>. Use when <EN scenarios>, or when user says "<TR trigger 1>", "<TR trigger 2>", "<TR trigger 3>". Do not use when <anti-scenario>.
```

Mandatory elements: WHAT · "Use when" · Turkish triggers (≥3, correct diacritics where the word has them) · English triggers · "Do not use" negative · at least one domain noun (tool name, file type, command, rule ID). Keep it ≤ 1024 characters and as short as these elements allow.

**WHAT names the capability, never the procedure.** One short sentence saying what the skill achieves. Steps, their order and their loops belong only in the body: an agent that finds a workflow summary in the description follows the summary and skips the body. If the user dictates a step-by-step description, explain this, propose a capability sentence, and move the steps to the body.

**YAML quoting:** wrap the description in double quotes and escape inner quotes as `\"`. An unquoted value must not contain `: `.

**Language:** if the user wants the description in another language, explain that validate requires the literal "Use when" and the audit expects English triggers; with their consent, keep those phrases in English and write the rest in their language.

See [Description Patterns](references/description-patterns.md) for examples and an anti-pattern table.

### Step 4: Fill Content

| Layer | What goes here |
|---|---|
| `SKILL.md` | Workflow steps, routing logic, one-liner commands (inline code, not blocks) |
| `references/<topic>.md` | Tables, long lists, detailed examples, rule catalogs |
| `scripts/<task>` | Detect language, run tools, enumerate files, ≥5-branch dispatch |

Each reference file opens with "Read this when…". Bash scripts start with `#!/usr/bin/env bash` and `set -euo pipefail`; use `python3` (standard library only) when parsing needs it. Every script is executable.

See [Skill Structure](references/skill-structure.md) for skeletons.

### Step 5: Self-Validate

Run `bash scripts/validate-skill.sh <skill-path>`. Fix every FAIL; report every WARN to the user. A PASS proves only the format, not that the skill works.

### Step 6: Test Behavior

Write an answer key first, then give a fresh-context agent the skill and at least three scenarios built from the Step 1 baseline (a normal case, an edge case, and a trap that tempts the baseline failure). It answers from the skill files alone and never sees the key. Score it against the key, fix each real gap it reports, re-run with a new agent until a run passes with no new real ambiguity, then run Step 5 again. When the description changed, also run the trigger test. Repeat on each model the skill will run on; after three rounds that still find new real gaps, show the user the open points instead of looping.

See [Behavior Testing](references/behavior-testing.md) for the prompt template and pass criteria.

## Validate Workflow

Run `bash scripts/validate-skill.sh <skill-path>`; it never modifies files. Checks:

1. SKILL.md exists
2. Frontmatter starts on line 1, closes, and parses as YAML (CRLF line endings are a WARN)
3. `name`: 1–64 chars, `a-z 0-9` and single hyphens, no leading/trailing hyphen, no "anthropic"/"claude", equals the directory name
4. `description`: a non-empty string, ≤ 1024 characters, no XML tags
5. `description` contains "Use when"
6. No scaffold `TODO:` placeholders remain
7. SKILL.md word count ≤ 2000
8. Every relative link resolves (a link outside the skill directory is a WARN)
9. All files in `scripts/` are executable

Parsing and name rules live in `scripts/skill_lint.py`, shared by all three scripts. WARNs do not fail the check. When validating a skill you did not write in this task, report FAILs and WARNs and change nothing without the user's consent. Exit code 0 = all pass, 1 = at least one failure, 2 = usage error.

## Audit Workflow

Run `bash scripts/audit-skill.sh <skill-path>`. It never modifies files and exits 0 whenever it produced a report (1 = no SKILL.md, 2 = usage error). It scores four dimensions: Word Budget (25), Progressive Disclosure (20), Scripts Token Efficiency (20), Description Quality (35), and lists the top 3 refactor suggestions. The audit scores the mandatory description elements that validate does not check.

Raise a score only with real improvements: never pad the description with invented triggers or add empty folders. See [Audit Checklist](references/audit-checklist.md) for the rubric.

## Storage Locations

| Location | Purpose | Editable by skill? |
|---|---|---|
| `~/.claude/skills/<name>/` | Personal Claude skills | Yes |
| `~/.cursor/skills-cursor/<name>/` | Cursor-reserved | **Never** (reading is fine) |
| `<project>/.claude/skills/<name>/` | Project-scoped skills | Yes |

## Additional Resources

- [Description Patterns](references/description-patterns.md) — TR/EN trigger examples, anti-patterns, character guidance
- [Skill Structure](references/skill-structure.md) — directory layout, SKILL.md/reference/script skeletons, word budget
- [Scripts Guidelines](references/scripts-guidelines.md) — when to prefer a script, portability, exit codes
- [Audit Checklist](references/audit-checklist.md) — scoring rubric, refactor suggestion templates
- [Behavior Testing](references/behavior-testing.md) — baseline, prompt template, pass criteria
