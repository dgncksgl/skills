---
name: create-skill
description: "Create new Claude skills (scaffold SKILL.md + references/ + scripts/), validate existing skills for compliance, or audit skills with a 0-100 score and refactor suggestions. Enforces three principles: ≤2000 word budget, progressive disclosure via references/, and token-free scripts. Use when asked to create a skill, author a skill, scaffold a skill, write a new skill, audit a skill, validate a skill, lint a SKILL.md, or when user says \"skill oluştur\", \"yeni skill yaz\", \"skill üret\", \"skill hazırla\", \"skill iskeletini oluştur\", \"skill'i denetle\", \"skill'i standartlara uydur\", \"mevcut skill'i kontrol et\", \"skill audit et\", \"skill uyumluluğunu kontrol et\". Use proactively when a user repeats multi-step instructions across sessions — that is a skill candidate. Do not use for editing ~/.cursor/skills-cursor/ (Cursor-reserved), generic documentation, single-file refactoring, or non-skill markdown."
---

# Create-Skill Meta-Skill

## Overview

This skill manages the full lifecycle of Claude skills: **Create** (scaffold a new skill from scratch), **Validate** (quick pass/fail compliance check), and **Audit** (deep 0-100 score with refactor suggestions). It enforces three core principles that keep skills lean, fast-triggering, and token-efficient.

## Three Core Principles

| Principle | Rule | Where excess content goes |
|---|---|---|
| Word budget | SKILL.md ≤ 2000 words (ideal: ~1000) | `references/*.md` |
| Progressive disclosure | Tables >10 rows, lists >15 items, code examples → offload | `references/*.md` |
| Scripts are free | Deterministic logic ≥5 branches → script | `scripts/*.sh` |

See [Scripts Guidelines](references/scripts-guidelines.md) for the token-cost comparison and decision table.

## Workflow Router

Determine the user's intent before proceeding:

- **"Create"** — user wants a new skill from scratch → follow Create Workflow
- **"Validate"** — user wants a quick pass/fail on an existing skill → follow Validate Workflow
- **"Audit"** — user wants a detailed score and refactor suggestions → follow Audit Workflow

## Create Workflow

### Step 1: Gather Requirements

Ask (or infer from context):
- What does the skill do? (one sentence)
- Where will it live? (`~/.claude/skills/` for personal, project dir for project-scoped)
- What are the trigger scenarios in English AND Turkish?
- Are there anti-scenarios (when NOT to use)?

### Step 2: Scaffold Directory

```
bash scripts/scaffold.sh <skill-name> [--location PATH] [--force]
```

This creates:
- `SKILL.md` with frontmatter skeleton and TODO placeholders
- `references/.gitkeep`
- `scripts/.gitkeep`

### Step 3: Write the Description

The description is the #1 factor in whether a skill triggers. Follow this structure:

```
<WHAT in one sentence>. Use when <EN scenarios>, or when user says "<TR trigger 1>", "<TR trigger 2>". Do not use when <anti-scenario>.
```

Mandatory elements: WHAT · "Use when" · Turkish triggers (≥3, correct diacritics) · English triggers · "Do not use" negative · At least one domain noun (tool name, file type, rule ID).

See [Description Patterns](references/description-patterns.md) for 6 full examples and an anti-pattern table.

### Step 4: Fill Content

Distribute content across three layers:

| Layer | What goes here |
|---|---|
| `SKILL.md` | Workflow steps, routing logic, one-liner commands |
| `references/<topic>.md` | Tables, long lists, detailed examples, rule catalogs |
| `scripts/<task>.sh` | Detect language, run tools, enumerate files, ≥5-branch dispatch |

Each reference file should open with "Read this when…" to enable progressive disclosure. Each script must start with `#!/usr/bin/env bash` and `set -euo pipefail`.

See [Skill Structure](references/skill-structure.md) for full skeletons.

### Step 5: Self-Validate

```
bash scripts/validate-skill.sh <skill-path>
```

Fix every FAIL before considering the skill done.

## Validate Workflow

```
bash scripts/validate-skill.sh <skill-path>
```

**Checks performed (9 total):**

1. SKILL.md exists
2. Frontmatter `---` delimiters parseable
3. `name` field present and non-empty
4. `name` matches `^[a-z][a-z0-9-]{0,62}$`
5. `description` field present
6. `description` ≤ 1024 characters
7. `description` contains "Use when"
8. SKILL.md word count ≤ 2000
9. All scripts are executable

Output: `PASS` or `FAIL` per check + final summary. Exit code 0 = all pass, 1 = at least one failure.

## Audit Workflow

```
bash scripts/audit-skill.sh <skill-path>
```

Produces a 0-100 compliance score across four dimensions:

| Dimension | Points |
|---|---|
| Word Budget | 25 |
| Progressive Disclosure | 20 |
| Scripts Token Efficiency | 20 |
| Description Quality | 35 |

Output: per-check detail, total score, grade (Excellent/Good/Needs Work/Failing), and the top 3 prioritized refactor suggestions.

See [Audit Checklist](references/audit-checklist.md) for the full scoring rubric and refactor suggestion templates.

## Storage Locations

| Location | Purpose | Editable by skill? |
|---|---|---|
| `~/.claude/skills/<name>/` | Personal Claude skills | Yes |
| `~/.cursor/skills-cursor/<name>/` | Cursor-reserved | **Never** |
| `<project>/.claude/skills/<name>/` | Project-scoped skills | Yes |

## Additional Resources

- [Description Patterns](references/description-patterns.md) — TR/EN trigger examples, anti-patterns, character guidance
- [Skill Structure](references/skill-structure.md) — directory layout, SKILL.md/reference/script skeletons, word budget table
- [Scripts Guidelines](references/scripts-guidelines.md) — when to prefer a script, bash portability, exit codes
- [Audit Checklist](references/audit-checklist.md) — full scoring rubric, refactor suggestion templates
