# Special Cases

Read this when the plan meets one of the situations below (Steps 4, 5 and 7).

## Already lean file

Moving a block that is not needed in every session into a path rule is a real saving, even in a short file. Do not create a file that saves nothing, for example a rule without `paths:`, or a split that keeps everything loaded at startup. If nothing can move, say the file is already lean. Then propose only the concrete fixes you found: stale paths, wrong tool names, inflated emphasis.

## The user waives the plan ("just do it", "planı gösterme")

Do not skip Step 4. Shrink it to one short message:

- the delete list, with evidence;
- the contradictions, with what the code shows and your recommendation;
- the items you cannot verify and will keep;
- any hook or skill candidates.

Moves and calmer wording need no separate listing. Wait for the answer, then continue.

## The user asks for a line count ("50 satır", "max 100 lines")

Ask whether they mean root only or everything that loads at startup. Say whether the number is reachable without deleting valid rules, and show what the restructure reaches. Let them choose any further cuts line by line. There is no sourced 50-line limit; the documented target is under 200 lines per file.

## Existing rule file whose `paths:` matches nothing

The rule has never loaded. Treat its content like any original line, because it may be stale and has never been tested in practice. Put the pattern fix in the plan, because it changes behavior. Match folder names with their exact case (`Source/`, not `src/`).

## Follow-on corrections

A consequence of an approved correction is part of that correction. For example, API 24 → 26 also turns "Android 7.0" into "Android 8.0". Apply it and list it in the report.

## Personal lines

An approved personal line goes to `CLAUDE.local.md`, and `CLAUDE.local.md` is added to `.gitignore`. In the size figures, count it apart from the team's files: it still loads for its owner.

## Skill candidates

Build a skill only if the user asked for it to be built, using the skill-authoring skill if one is available. Until then, root keeps a one-line pointer, or the procedure stays where it is.

## Root file that is only an import (`@AGENTS.md`)

The imported file is the real content: restructure it, count its size as always loaded, and pass it to `coverage.py`. For a file shared with other tools, keep "Maintaining This File" and Claude-only notes out of it: they would mislead the other tool's users.

## An import that is removed

Removing `@docs/x.md` from root does not delete `docs/x.md`. Leave the file in place unless the user asks; say in the plan that it stays.

## Notes such as "not verified"

They belong in the plan and the report, not inside the instruction files, where they would go stale.

## Monorepo with several stacks

Build and test commands stay in root, one line per module (`cd android && ./gradlew test`), because running a command does not load path rules. Each module's coding rules go to a rule file scoped to `<module>/**`, or to the module's own CLAUDE.md or AGENTS.md.

## Line cap and the hook line

The one-line hook note in root counts toward a line cap the user set. Say so before installing the hook, and let the user choose.

## Hooks for a repo that is not this session's project

The live in-session proof cannot run there. Do the pipe-test and the `jq -e` check, say that the live proof was skipped and why, and tell the user to open `/hooks` in a new session in that repo.

## Pipe-test strings trip this session's own hooks

A test command line that contains the blocked text (`pip install x`) can be blocked by a hook of the current session before it runs. Write the cases to a script file in the backup directory and run that file.
