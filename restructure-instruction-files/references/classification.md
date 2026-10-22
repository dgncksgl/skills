# Classifying Every Block

Read this when deciding where each line or block of the original instruction file goes (Step 3).

## How each destination loads

| Destination | Loads | Cost |
|---|---|---|
| Root `CLAUDE.md` (or `.claude/CLAUDE.md`) | Every session, re-injected after `/compact` | Every token, every session |
| `.claude/rules/<topic>.md` **with** `paths:` | When Claude reads, edits or writes a matching file (also `cat`/`head` of one file) | Only in sessions that touch those files |
| `.claude/rules/<topic>.md` **without** `paths:` | Every session | Same as root |
| `<subdir>/CLAUDE.md` | When Claude reads or edits any file in that subdirectory | Only in sessions that work there |
| `@path` import | At launch, together with the importing file | Same as root — organizes, never saves |
| `CLAUDE.local.md` (gitignored) | Every session, only for this person | Same as root |
| `~/.claude/CLAUDE.md`, `~/.claude/rules/` | Every session, every project of this person | Same as root, in all projects |
| Skill (`.claude/skills/<name>/SKILL.md`) | Description every session; body only when invoked | A line or two until used |
| Hook (`.claude/settings.json`) | Runs as a script; never enters context unless it prints | Zero tokens; deterministic |
| `<!-- HTML comment -->` in a CLAUDE.md | Stripped before injection | Zero tokens; human-only notes |

## Decision order

Ask these in order for each block; the first "yes" decides.

1. **Is it false today?** A path, file, tool, command or library that does not exist in the repo → delete candidate (evidence: the inventory line or a failed `ls`/grep). A missing path is not always stale: gitignored files (`local.properties`), folders created by the build (`app/schemas/`), files created later (`CHANGELOG.md`) and placeholders (`di/`, `<name>/`) are kept. A value that contradicts the code (the file says API 24, `build.gradle.kts` says `minSdk = 26`) is a **correct** candidate, not a delete: propose the code's value and let the user decide.
2. **Can Claude see it by reading the code?** A file-by-file tour, a list of classes, a dependency list that `package.json`/`pom.xml` already holds → delete candidate.
3. **Is it a default Claude already follows, or not a rule at all?** "Write clean code", "use meaningful names", standard language conventions, tutorials, a preamble that only shouts ("ALL RULES ARE MANDATORY"), time-bound facts (current sprint, next release date) → delete candidate. Reference material the team still wants (an API route table, a glossary) is not deleted: it moves to a docs file, created if needed, with a one-line pointer in root.
4. **Does it repeat another block?** Keep one copy at the narrowest place that still loads when needed; the others are delete candidates. If the copies differ in scope ("in every module" vs. one module), keep the wider one. A rule enforced by a test or linter keeps one short line naming the enforcer.
5. **Must it happen every time with zero exceptions, and can a script check it?** (package manager, formatter, forbidden folder, forbidden command) → hook candidate. Keep one line in root saying the hook exists, so Claude knows why a command was blocked.
6. **Is it a multi-step procedure used only sometimes?** For example a release, a deploy, or a migration run: five steps or more that are not needed in most sessions. → skill candidate. Until the user has the skill built, the procedure stays where it is; once the skill exists, root keeps at most one line naming it. A one- or two-line rule about where something goes is not a procedure; the timing trap keeps it in root.
7. **Is it personal, not team-wide?** (own sandbox URL, own editor) → suggest `CLAUDE.local.md` or `~/.claude/`; keep it where it is unless the user agrees. A credential (password, token, connection string with a password) is flagged on its own: it is already in git history, so recommend rotating it, whatever its destination.
8. **Does it apply only when certain files are touched?** → path-scoped rule. Check the timing trap below first. Scope each rule by the files it really governs, not by the section it sat in: "no data annotations on domain entities" under an EF Core heading governs Domain files.
9. **Does it apply only inside one self-contained module with its own build** (`android/`, `ios/`, `backend/` in a monorepo)? → `<module>/CLAUDE.md`, or a rule with `paths: ["<module>/**"]`. Prefer the rule unless the module is opened as its own working directory.
10. **Everything else** → root.

## The timing trap

A path-scoped rule is not in context until a matching file is read or edited (`cat`/`head` of that one file counts as a read). Creating a new file loads it only at the moment of writing, after the content is already decided. Keep a rule in root when Claude needs it **before** touching any matching file:

- Where a new file or module goes, and what it is named (layer map, package layout, `Entity`/`Dto`/`Test` suffixes when they name files).
- Which command to run (build, test, package manager, git and branch conventions): running a command does not load path rules.
- Working rules for every task (ask before X, phases, scope limits).

How to write the inside of a file (annotations, parameter order, patterns) goes to a path rule: by then Claude is editing a matching file. For rules about writing a **new** file, such as test conventions, add the source files Claude reads first to the pattern (`**/*.java` as well as `**/src/test/**`), or the rule loads only once the content is already written. Two rule files may share a pattern.

Example: "New screens go in `feature/<name>/ui/`" belongs in root; "Composables take a `Modifier` as their first optional parameter" belongs in `rules/compose.md` with `paths: ["**/*.kt"]`.

## What root keeps

Only what passes "Would removing this line cause Claude to make a mistake?":

- One or two sentences on what the project is and its non-obvious constraints (target device, offline, regulated data).
- Commands Claude cannot guess: build, test, single test, lint, run, with the exact tool (`./gradlew`, `uv run`, `dotnet test`, `xcodebuild -scheme X`).
- Working rules and repository etiquette (branches, commits, review, when to ask).
- Architecture: layer or module map and dependency direction, in a few lines.
- Environment quirks and gotchas: required env vars, generated code not to edit, slow or flaky steps.
- One pointer line to the rules folder.

## Delete candidates need evidence

Never delete silently. For each candidate, show the user: the original line, the reason (one of 1–4 above), and the evidence (missing path, the file that already states it, the test that enforces it). Delete only what the user approves. When unsure whether something is still true, keep it and ask.

## Conflicts

Two blocks that contradict each other, or a block that contradicts the code (two package managers, two locations for the same thing, a version the build file disagrees with), are never resolved by guessing: list them with their line numbers, say what the code shows, recommend an answer, and ask in Step 4.

## Commands you cannot run

If a command cannot be checked (no JDK, no simulator, a missing secret), keep it unchanged, mark it **not verified** in the plan with the reason, and do not build a hook on it.
