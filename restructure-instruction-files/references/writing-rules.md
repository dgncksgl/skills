# Writing the New Files

Read this when writing the root CLAUDE.md and rule files (Step 5), or when rewording a line.

## Line-level rules

| Rule | Before | After |
|---|---|---|
| Concrete and checkable | "Format code properly" | "Use 4-space indentation; `./gradlew spotlessApply` fixes it" |
| Real names from this repo | "e.g. `UserRepository`" (no such class) | "e.g. `OrderRepository` in `data/order/`" (verified) |
| Calm emphasis | "CRITICAL: You MUST NEVER…" | "Never …" — keep one marked line (`IMPORTANT`) only for a rule that was actually skipped before |
| Reason when not obvious | "Don't use `Thread.sleep` in tests" | "Don't use `Thread.sleep` in tests; CI runners are slow and it makes them flaky" |
| Measurable instead of vague | "Be ≥95% confident" | "Change something only when you can show it is right; otherwise ask" |
| Correct tool names | "the `Task` tool" | the name in the current session's tool list (for example `Agent`) |
| One rule, one place | the same layer rule in three files | one copy; others removed or replaced by a pointer |

Keep the original language of the file unless the user asks for another. Keep project terms exactly as the team spells them. Never change a rule's meaning while rewording; a meaning change is a decision for the user.

## Size

- The official target is under 200 lines per CLAUDE.md file; longer files consume context and reduce adherence. 200 is a ceiling, not a goal.
- There is no sourced "50 lines" limit. Do not pad or cut to hit any number: each line stays only if removing it would cause a mistake. When the user asks for a number anyway, ask whether they mean root only or everything that is always loaded. Show what the restructure reaches, then let them pick further cuts line by line.
- Every rule file and `@import` counts as a separate file in Claude Code's size warnings, and unconditional ones add to the startup total.
- A rule file over ~150 lines usually holds two topics; split it.

## Root CLAUDE.md skeleton

Sections in this order, skipping any with nothing real to say. Existing project sections that pass the removal test (a glossary, a tool policy, a language rule) stay, under their own heading, in a sensible place in this order:

```markdown
# CLAUDE.md

<One or two sentences: what this is, and the constraint that shapes decisions.>

## Working Rules
- <how to work: phases, when to ask, scope>

## Commands
- Build: `<exact command>`
- Test: `<exact command>`; single test: `<exact command>`
- <hook note, e.g. "A hook blocks `npm`; use `pnpm`.">

## Architecture
<module/layer map, 5–15 lines> 
- <dependency direction>
Details: `.claude/rules/` (loaded automatically for matching files).

## Gotchas
- <non-obvious things that caused mistakes>

## Maintaining This File
- When a fact here becomes false, fix it in the same change.
- Add a rule only after the same mistake happens twice. Rules for one area of the code go to `.claude/rules/` with `paths:`.
```

## Rule file skeleton

```markdown
---
paths:
  - "src/**/*.{ts,tsx}"
---

# <Topic> Rules

<One line: what this covers; what lives in root instead.>

## <Subtopic>
- <rule>
```

- One topic per file; descriptive filename (`testing.md`, `compose-ui.md`, `api-design.md`). Subfolders are allowed (`frontend/`, `backend/`).
- `paths` patterns are relative to the directory that holds `.claude/`. Quote every pattern. A YAML list or a comma-separated string both work; brace expansion works (`**/*.{kt,kts}`).
- Every pattern must match at least one existing file (`inventory.py` prints the count). A pattern that matches nothing means the rule never loads.
- A literal `[` in a pattern must be escaped as `\[`.
- A rule file without `paths:` loads every session: use one only for a cross-cutting topic when root would otherwise pass 200 lines.

## Pointers, not copies

Point to the source of truth instead of copying it: "Formatting settings: `.editorconfig`", "API reference: `docs/api.md`". A pointer replaces a line only when the target file states every value the line gave; otherwise keep the values. Use a plain backticked path (not `@path`) so nothing is imported at launch.

## Shared with other tools

Path-scoped rules, hooks and skills are Claude Code features. If the team also uses Cursor, Codex, Copilot or another agent through `AGENTS.md` or the same CLAUDE.md, ask the user before moving shared rules into `.claude/rules/`, because those tools will stop seeing them. A common answer: keep `AGENTS.md` as the shared base, have `CLAUDE.md` start with `@AGENTS.md`, and move only Claude-specific or file-specific detail into rules.

An `@AGENTS.md` import still loads every session. If the shared file is over 200 lines, propose splitting it by folder: `apps/web/AGENTS.md`, `apps/api/AGENTS.md`. Claude Code reads a subdirectory's `AGENTS.md` when it opens a file there and that folder has no CLAUDE.md of its own. Before recommending it, confirm with the user that their other tool also reads nested files.

## Sources

- Claude Code docs, "How Claude remembers your project" (code.claude.com/docs/en/memory): 200-line target, path-scoped rules, imports don't reduce context, subdirectory loading, HTML comments stripped, `/doctor prompt-audit`.
- Claude Code docs, "Best practices" (code.claude.com/docs/en/best-practices): include/exclude table, "would removing this cause mistakes", emphasis on one line only, hooks for zero-exception rules, skills for occasional knowledge.
- Anthropic, "Effective context engineering for AI agents": smallest set of high-signal tokens; context rot.
- Claude prompting best practices (platform.claude.com): newer models over-trigger on aggressive language; give the reason.
- Research: Chroma "Context Rot" (2025); Liu et al. "Lost in the Middle" (TACL 2023); Jaroslawicz et al. "IFScale" (arXiv 2507.11538) — adherence drops as instruction count grows.
