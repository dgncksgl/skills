# Triage Rules

Read this before the first triage of a review loop, and whenever a verdict is unclear.

## Verdict criteria

A finding is `FIX` only when all three hold:

1. **Real**: reading the current code (or running a free local check) shows the failure scenario can happen as written.
2. **Concrete cost**: a security hole, a wrong result, crash, data loss, misleading log/output, wasted paid call, a quoted project-rule violation, duplicated logic that must change in two places, or dead code (unused import, variable, branch) added by the change.
3. **Worth it**: the fix is proportionate to the cost and stays inside the review scope (the diff, or the target the user named).

`REJECT` when any of these hold (record which one):

| Reason | Example |
|---|---|
| False positive | The guard the finding asks for already exists two lines above |
| Speculative | Needs a trigger the real system does not produce: a microsecond timing window, or an input value that the actual config/callers never supply (check them) |
| Style preference | No project rule is quoted; only a taste difference |
| Out of scope | Code outside the review scope that the change does not re-expose |
| Conflicts with rules | The suggested fix breaks a CLAUDE.md rule or a decision the user made |
| Fix worse than defect | The change adds more risk or complexity than it removes |

`ASK` when the right answer depends on the user: a product or behaviour choice, two project rules that contradict each other, an external or paid call needed to verify, or a fix that would reverse an earlier round's fix. Before asking for a paid check, try the free ones (do the real callers or config ever produce the trigger?); if they settle it, decide yourself.

Precedence: a finding that is false, speculative or stale is `REJECT`, even if it touches an earlier fix. `ASK` is only for a real finding whose right answer needs the user, including a real rule violation whose every fix is a product choice (delete the feature, or redesign where it lives). When the whole change is unreferenced (no caller anywhere), "dead code" is `ASK`, never a `FIX` that deletes the user's feature.

## Repeat matching

Two findings are the same when they name the same defect for the same reason, even if the wording, line number or file differs (the same defect can surface where a value is read and where it is used). Match on the defect's gist, not on the summary text.

- Already `FIX`ed and the code still shows the defect: the fix was incomplete; treat it as a new `FIX`.
- Already `FIX`ed and the defect is gone: `REJECT` (stale).
- Already `REJECT`ed or `ASK`ed: `REPEAT` with the original verdict and the return count; the first reappearance is return 1 ("REJECT R1, return 1").

Within one round, separate instances are separate findings (two unused imports are two findings), but the reviewer listing the same defect twice is one finding: give the second `REPEAT` with "same as #k".

In the round header, count `REJECT (stale)` as `REJECT` and a same-round duplicate as `REPEAT`. `ASK` items are never re-asked mid-loop; their returns are only counted.

## Recurrence rule

A `REJECT`ed finding that reaches **return 3** (it reappeared in three later rounds, consecutive or not; read the count from its last `REPEAT` row) gets one fresh re-examination: read the code again without the earlier reasoning, and look for a fix that satisfies both the reviewer's concern and the reason for rejecting it. If such a fix exists, the verdict becomes `FIX`; if not, write the row as `REJECT (final)`. Either way, never reopen it again: later returns are `REPEAT` rows that say "REJECT final", with no further count.

## Ledger format

A Setup block first, then one table per round, appended to `code-review-until-clean-ledger.md`:

```markdown
## Setup
args: high src/auth | cap: 5 | tests: uv run pytest | lint: none
baseline: 496/498 pass (test_dates, test_locale already fail) | language: Turkish

## Round 3: 10 findings, 2 FIX, 3 REJECT, 4 REPEAT, 1 ASK; tests back to baseline (497/499, same 2 fail)

| # | Key (file: defect gist) | Verdict | Reason / change |
|---|---|---|---|
| 1 | logging_config.py: lowercase LOG_LEVEL crashes startup | FIX | normalise with .upper(); test added |
| 2 | use_case.py: switch-off at end logged as cancelled | REJECT | speculative: ms window, same check either way |
| 3 | player.py: retry delay not capped | REPEAT | REJECT R1, return 2 |
| 4 | market_reporter.py: stale price wording | ASK | product choice: show time or omit price |
```

Before each triage, read the whole ledger. The keys are what make repeat matching possible after context compaction.
