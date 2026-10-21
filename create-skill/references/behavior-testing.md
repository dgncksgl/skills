# Behavior Testing

Read this when running Step 6 of the Create Workflow, or after editing an existing skill's instructions.

`validate-skill.sh` checks the format and `audit-skill.sh` scores structure and description elements; neither runs the skill. This test checks that an agent reading the skill does the right thing, and the trigger test checks that the description gets the skill picked.

## Baseline first

Before writing the skill, record what goes wrong without it. Best evidence, in order:

1. Past session transcripts where the user had to repeat or correct the same instructions.
2. One run of a representative task with no skill loaded, only if it costs nothing or the user agrees (no paid API calls without asking).

Write each failure as one line ("stops after the first review round", "re-applies findings rejected earlier"). Each failure becomes at least one scenario.

No baseline (the user wanted the skill anyway): build the scenarios from the user's description, and make the trap the most tempting shortcut you can name for the task. For an edit, the baseline is the problem that prompted the edit.

## Scenarios and answer key

At least three scenarios, each answerable from text alone:

| Type | Purpose |
|---|---|
| Normal | The main trigger phrase and the first actions the skill prescribes |
| Edge | A situation the steps cover only indirectly (empty input, cap reached, conflicting rules) |
| Trap | A situation that tempts the baseline failure (shortcut, skipped check, repeated mistake) |

Use real data from the baseline where you have it: real findings, real file names, real user wording. Mix the expected outcomes, so the right answer is not always the same verdict or action.

Before running anything, write the answer key: for each scenario, the expected actions and decisions, and what would count as a failure. Keep the scenarios and the key in the session scratchpad, never inside the skill folder, and keep the key in a different directory from the scenarios (or only in your own context); never name the key's path in the test prompt.

## Running the test

Write the scenarios to a file, then launch one fresh-context agent (a general-purpose subagent, no conversation history) with this prompt:

```
Read ONLY these files, fully:
- <skill-path>/SKILL.md
- <skill-path>/references/<every reference file, one line each>
- <scenarios-file>
Read nothing else and change nothing. Act as an agent that has just loaded this skill.
Answer each scenario as text: your exact next actions, each decision with a
one-line reason, and when you would stop. When the skill does not cover a
scenario, say so and say what you would do.
Finally, list everything in the skill that was ambiguous, contradictory or missing.
```

The final question matters most: the gaps it lists are the skill's bugs. When the skill will run on several models, repeat the run with each of them (for example Haiku, Sonnet and Opus).

## Trigger test

Run this when the description is new or changed. Give a fresh agent the `name: description` lines of the new skill and of its closest neighbours (skills whose topics overlap), plus 8–10 user messages: some that should pick the new skill, some that should pick a neighbour, and some that should pick none. Write the expected pick for each message first. The agent answers which skill, if any, it would load for each message. Every wrong pick is a description bug: sharpen the triggers or the "Do not use" clause, and re-run.

## Pass criteria

- Every expected behavior in the answer key is present in every scenario.
- The trap scenario does not reproduce the baseline failure.
- Each reported ambiguity is either fixed in the skill or judged harmless with a one-line reason.
- The trigger test, when run, has no wrong pick.

After fixing, run the test again with a new fresh agent. Repeat until a run passes with no new real ambiguity; if three rounds still find new real gaps, show the user the open points. Then run `validate-skill.sh` again, since the fixes changed the file.
