---
name: restructure-instruction-files
description: "Turns a long, monolithic or messy CLAUDE.md into a lean root file plus path-scoped .claude/rules/*.md files, cleaning stale, duplicate and over-emphasized rules and proposing hooks for must-always rules, in any stack (Python, Java, Kotlin/Android, C#/.NET, Swift/iOS, TypeScript, Go, Rust). Use when CLAUDE.md is too long, bloated, hard to follow, or should be split into subfiles or rules, or when user says \"CLAUDE.md'yi böl\", \"CLAUDE.md'yi parçala\", \"CLAUDE.md'yi subfile'lara ayır\", \"CLAUDE.md çok uzun\", \"CLAUDE.md'yi best practice'e göre düzenle\", \"split CLAUDE.md\", \"restructure CLAUDE.md\". Do not use for creating a first CLAUDE.md in a repo without one (use /init), for editing a single rule, for auto-memory MEMORY.md, or for SKILL.md files."
---

# Restructure Instruction Files

## Overview

CLAUDE.md is loaded into every session. Every line costs context and competes for attention, so the longer the file, the less of it gets followed. This skill rebuilds the instruction files in four ways:

- Root keeps only what every session needs.
- Rules for specific files load only when matching files are touched.
- False, duplicate and obvious rules are removed, but only with the user's approval.
- Rules that must hold every time become hooks.

No rule changes meaning without approval. It works for any language. Below, `$SKILL` means `~/.claude/skills/restructure-instruction-files`; run the scripts by that absolute path with the system `python3` (standard library only), from any directory.

## Workflow

Phase 1 (Steps 1–4) changes nothing. Phase 2 (Steps 5–8) starts only after the user explicitly approves the plan.

### Step 1: Back up and inventory

1. Find every instruction file:
   - `CLAUDE.md` and `.claude/CLAUDE.md`
   - `CLAUDE.local.md`
   - `AGENTS.md`
   - `CLAUDE.md` files in subdirectories
   - everything under `.claude/rules/`
   - the hooks in `.claude/settings.json`
   - files pulled in with `@import` (they load every session too)
   - other agents' instruction files, if any: `.cursor/rules/`, `.github/copilot-instructions.md`, `.windsurfrules`
2. Copy them, keeping their relative paths, to a fresh directory outside the repo: the session scratchpad if one is given, otherwise `mktemp -d`. Note its path, and keep drafts and temporary test scripts there too. Git history is not a backup for edits that are not committed.
3. Run `python3 $SKILL/scripts/inventory.py <repo>`. Keep its output as the "before" snapshot.

### Step 2: Learn the project

Read the inventory output and every original file in full. Then read only what you need to check them:

- the build files: `pyproject.toml`, `pom.xml`, `build.gradle.kts`, `*.csproj`, `Package.swift`, `package.json`, `go.mod`
- the top-level folder layout
- every path the inventory flagged

Check each command against the build files (an `npm run X` needs an `X` script in `package.json`) and each tool name against this session's tool list.

If `AGENTS.md` exists, or the team also uses other agents (Cursor, Codex, Copilot), stop and ask now: the answer changes every destination ("Shared with other tools" in [Writing Rules](references/writing-rules.md)). If nothing says, ask it in Step 4. Collect all other questions, contradictions and commands the build files show are wrong for Step 4; never change a command without approval.

### Step 3: Classify every block

Go through the original from top to bottom and give every block exactly one destination:

- root CLAUDE.md
- a path-scoped rule file
- a CLAUDE.md in a subdirectory
- a hook candidate
- a skill candidate
- a personal file
- a delete candidate

Follow the decision order and the timing trap in [Classification](references/classification.md). A rule that Claude needs before it touches any file stays in root, for example where new files go, which command to run, or how to work.

Each delete candidate needs evidence: a path that does not exist, the file that already says the same thing, or the test that enforces it.

### Step 4: Present the plan and stop

Show the user, in their language:

1. The new file tree: each file's purpose and its `paths:` patterns.
2. A mapping table: one row per block (a section or a group of bullets), giving its line range, destination and status: **kept** (word for word), **reworded** (any change, even emphasis only; show the new text), **hook**, or **delete** (proposed). Give reworded and deleted lines one row each. Lines you add (the rules pointer, the maintenance section) get rows marked **added**.
3. The delete candidates, each with its reason and evidence.
4. The hook candidates and skill candidates, each with what it would enforce or do.
5. The always-loaded lines and bytes before and after. To measure "after", draft the new files in a `draft/` folder inside the backup directory, keeping their repo-relative paths, and run the inventory on that folder.
6. Open questions, each with a recommended answer.

Wait for the user's answer to this plan. The user may approve some items and reject others. A rejected deletion means the rule stays, reworded if needed.

For an already lean file, a user who waives the plan ("just do it"), or a requested line count ("50 lines"), see [Special Cases](references/special-cases.md).

### Step 5: Write the files

Follow [Writing Rules](references/writing-rules.md):

- Root uses the skeleton given there.
- Each rule file covers one topic, and its `paths:` patterns are in quotes.
- Emphasis is calm.
- Examples use names that exist in this repo.
- The files stay in their original language.
- Root gets no hook line yet; Step 7 adds it once the hook is verified.

Take the glob patterns from [Ecosystems](references/ecosystems.md) and adapt them to the repo's real layout. Match folder names with their exact case (`Source/`, not `src/`). If `.claude/rules/` already exists, merge your files into it. Never overwrite a rule file you have not read. Existing rule files whose pattern matches nothing, consequences of a correction, personal lines and skill candidates: see [Special Cases](references/special-cases.md).

### Step 6: Verify

Run `python3 $SKILL/scripts/inventory.py <repo>` again. Check that:

- No path is missing, except placeholders you added on purpose.
- Every `paths:` pattern matches at least one file.
- There are no `@imports` you did not intend.
- Every line the inventory lists under "emphasis on lines" is either calmed or one the plan kept on purpose (an `IMPORTANT` on a rule that was skipped before).
- The always-loaded size is at or below the plan's figure, re-estimated after the user's answers (a rejected deletion adds its lines back). Count `CLAUDE.local.md` separately: it still loads for its owner, but leaves the team's file.

Run `python3 $SKILL/scripts/coverage.py <repo> <backup>/CLAUDE.md [other originals] [--also docs/api.md]`. It prints every original line not found in any new file (ignoring case and markup), so deleted and reworded lines print; `--also` adds a non-instruction file that received moved lines. Compare its "Unmatched ranges" line with the mapping table:

- a printed **kept** line is a mistake: restore it word for word (do not re-mark it as reworded);
- a printed **reworded** line must keep its full meaning, every qualifier included ("even in debug builds");
- a printed line missing from the table is a lost rule: put it back.

If the project has a fast offline test or build command, run it; otherwise say why you skipped it.

### Step 7: Hooks (only those approved)

Load the bundled `update-config` skill and follow its steps for building and checking a hook, together with the safety notes in [Ecosystems](references/ecosystems.md). Approving a hook covers creating `.claude/settings.json`. When the live proof cannot run, see [Special Cases](references/special-cases.md). Test both sides. A blocking hook must block what it should and let everything else through. A formatter hook must pass the test cases listed in Ecosystems. A blocking hook (PreToolUse) exits 2 to block. A formatter hook (PostToolUse) always exits 0, even when the formatter fails on a syntax error; the build or tests will surface that error. Then add one line to root saying the hook exists. A hook you could not verify is not installed: its rule stays as plain text, and root gets no hook line. After the hooks, run Step 6 again, because root changed.

### Step 8: Report

Tell the user:

- the before and after figures: lines, bytes, files, always-loaded size and emphasis count
- the deleted lines and why each was deleted
- the hooks you added
- where the backup is

Suggest they open a new session and run `/context` to see what loads at startup, and `/doctor prompt-audit` to look for conflicting rules. Do not commit unless the user asks.

## Additional Resources

- [Classification](references/classification.md): where each block goes, when it loads, the timing trap, what stays in root, evidence for deletions, conflicts
- [Writing Rules](references/writing-rules.md): rewording single lines, size limits, root and rule file skeletons, sharing with other tools, sources
- [Ecosystems](references/ecosystems.md): `paths:` patterns for each stack, hook candidates, hook safety notes
- [Special Cases](references/special-cases.md): lean files, waived plans, line-count requests, dead patterns, follow-on corrections, personal lines, skill candidates, hooks outside this project
