---
name: code-review-until-clean
description: "Drives Claude Code's bundled /code-review skill to convergence on the current changes, so one request replaces many manual review rounds. Use when the user wants every real code-review finding fixed in one go, wants review and fixing repeated until nothing worth changing remains, or says \"tek seferde code review yap\", \"code review yap ve bitene kadar düzelt\", \"gerçekten değiştirilmesi gereken bulgu kalmayana kadar code-review et\", \"finding'ler tükenene kadar review et\", \"review döngüsünü çalıştır\", \"review until clean\", \"keep reviewing until no real findings\". Do not use for a single report-only review (plain /code-review), for ultrareview or cloud review, for posting PR comments (--comment), or for security audits (/security-review)."
argument-hint: "[code-review args: level, --max-findings, target] [en fazla N tur]"
---

# Code Review Until Clean

## Overview

One `/code-review` run rarely empties the list, by design of its recipe: at `high` effort it returns at most 10 findings, targets at least 5, skips verification ("dedup (no verify)"), and remembers nothing from earlier runs. So each run shows a new top slice plus repeats of findings already rejected. The stop signal is therefore **a round with no new finding worth changing**, not a round with zero findings.

This skill runs that loop for the user: review, verify every finding yourself, fix only the real ones, review again. Running all rounds without pausing is what the user asked for; decisions that need them are collected for the final report.

## Core Rules

- The reviewer's findings are **candidates**, not facts. Verify each one against the current code before acting.
- Forward the user's own `/code-review` arguments (effort level, `--max-findings`, target) unchanged on every round, and add none of your own: level and `--max-findings` are remembered for the user's later manual runs. A target given in words ("sadece src/auth klasörüne bak") is forwarded as the path. Trigger phrases ("tek seferde") and the round cap are not arguments.
- Never pass `--fix`, `--comment` or `--post`: `--fix` applies unverified findings outside `/rewind` checkpoints, and `--comment`/`--post` publish unverified findings. If the user typed one, drop it and say why in one line; if posting PR comments is what they want, say this skill does not do that.
- Never pass `ultra`. If the user asks for ultra, do not start the loop: say ultra is a separate cloud review, and offer this loop at a local level or `/code-review ultra` run by the user.
- Follow the project's CLAUDE.md and its applicable skills (TDD, verification, commit rules) for every fix.
- Never commit or push. Never make a paid or external call to verify a finding without asking.

## Workflow

Copy this checklist into your reply and keep it updated:

```
Review until clean:
- [ ] Setup: ledger, round cap, test baseline
- [ ] Round N: review → triage → fix → verify → ledger
- [ ] Stop check
- [ ] Final report
```

### Step 1: Setup

1. Check there is something to review: a non-empty diff (`git status`, commits ahead of the base) or the target the user named. If there is none, say so and stop.
2. Create the ledger at `<scratchpad>/code-review-until-clean-ledger.md` (the session scratchpad; if there is none, a temp directory outside the repository). It survives context compaction; the conversation may not.
3. Round cap: the user's limit in any language ("en fazla N tur", "max N rounds") if given, else **10**. Never forward it.
4. Find the project's test and lint commands (CLAUDE.md, README, CI and package config); skip lint if there is none. If the documented command cannot run at all (for example an optional extra is missing), use the variant the project itself declares (such as `uv run --extra mac pytest`) and record it; ask before any other environment change. Run them once and record the baseline, including tests that already fail. "Back to baseline" means: nothing that passed at baseline fails, and every test added by this loop passes. With no test command, verify each fix with a free local check that shows the failure before and its absence after, and say so in the final report.
5. Start the ledger with a Setup block: forwarded args, round cap, test/lint commands, baseline, and the user's language (the language of their request; for a bare slash command, the conversation's language).

**Resuming after compaction:** read the whole ledger before anything else and continue from its last round. If that round is marked `review started` but has no table and you cannot tell whether its review is still running, launch it again: a duplicate review costs usage, not correctness. Ask the user only for what the ledger lacks.

### Step 2: Run one review

Append `## Round N: review started` to the ledger, then invoke the bundled skill with the Skill tool: `skill: "code-review"`, `args`: the forwarded arguments (or none). It runs as a background subagent. End the turn with one short line in the user's language ("Round N is running in the background."); the task notification resumes you. Do not poll, and do not start another review while one is running.

If the notification reports a failed review, note `review failed` under the round in the ledger and retry once; a failed run does not count toward the cap. If it fails again, stop and report.

### Step 3: Triage every finding

Read the whole ledger first. Then, for each finding, read the cited code as it is now (line numbers may be stale) and give exactly one verdict:

| Verdict | Meaning |
|---|---|
| `FIX` | Real, reproducible from the code, and worth its change cost |
| `REJECT` | False positive, speculative, stale, out of scope, or conflicts with project rules / a user decision (write the reason) |
| `REPEAT` | Matches a ledger entry already decided, or another finding in this round; reuse that verdict |
| `ASK` | Needs a product decision, conflicting rules, a paid/external check, or would undo an earlier round's fix |

Full criteria, repeat matching, the recurrence rule and the ledger format: [Triage Rules](references/triage-rules.md). Read it before the first triage.

### Step 4: Fix and verify

Fix every `FIX` finding with the smallest change that removes the failure, following the project's rules (red test first where the project uses TDD and the fix changes behaviour; a pure refactor relies on the existing tests). Then run the full test and lint commands; they must be back to baseline before the round ends. If two attempts cannot bring them back, stop (Step 6): record the round with the breaking fix marked, leave the tree as it is, and in the report name which fix broke which test and offer to revert that fix.

### Step 5: Record the round

Replace the round's `review started` line with its header and table, then post a short summary in the user's language: counts per verdict and one line per `FIX`.

### Step 6: Stop check

Check the rows top to bottom; the first match decides.

| Condition | Action |
|---|---|
| The user says to stop ("dur", "yeter", "stop") | Stop now; mark the round `stopped by user` in the ledger; stop a running review if possible and do not act on its findings |
| Tests cannot be returned to baseline | Stop; report the failing output |
| This round produced no `FIX` (a re-examination that ends in `FIX` is a `FIX`; an empty findings list counts) | Stop: converged, even on the cap round; the last test run is the final evidence |
| Round cap reached | Stop after this round's verified fixes; end the report by asking whether to continue |
| Otherwise | Go to Step 2 |

`ASK` items never block the loop. If the user asks to hurry, shorten the round summaries and offer a round cap; never skip verification.

### Step 7: Final report

In the user's language:
1. Outcome first: converged at round N, or why it stopped.
2. Fixed findings: what changed and how it was verified.
3. Rejected findings: one line each with the reason.
4. `ASK` items: each once, with the decision the user must make, however many rounds it returned.
5. Test and lint status (naming tests that already failed at baseline), and that nothing was committed.

## Common Mistakes

| Mistake | Correction |
|---|---|
| Applying all findings because the reviewer listed them | The high-effort reviewer does not verify; you must |
| Stopping because "the rest are small" | Size is not the test; a cheap real defect is `FIX` |
| Re-arguing a finding rejected in an earlier round | Use the ledger; reopen only per the recurrence rule |
| Waiting for a round with zero findings | Rarely comes: the recipe targets at least 5 |
| Starting the next review before tests are back to baseline | The next round would review a broken tree |

## Additional Resources

- [Triage Rules](references/triage-rules.md): verdict criteria, repeat matching, recurrence rule, ledger format
