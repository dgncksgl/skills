# Naming Rules

Read this when composing the name in Step 4.

## Format

- English, lowercase, kebab-case: `a-z`, `0-9`, single hyphens. This matches the user's existing names (`anonymous-session-auth-review`, `nearby-county-revise`, `openai-independence-review-plan`).
- At most 40 characters; this is the hard limit. Aim for 2–5 content words. Joining words (`to`, `and`, `vs`) and a ticket ID (`ai-313`) do not count as words.
- Lowercase everything, proper names too (`graylog`, `ai-313`).
- Turkish session content is translated: "yakın ilçeler" → `nearby-districts`, "anonim kullanıcı" → `anonymous-user`. When the code already has an English name for the thing (`property_card`, `listing_cache`), use that word instead of your own translation. Keep product and tool names (`uv`, `pyright`, `homebrew`, `sse`); write a Turkish product name in plain a-z without apostrophes (`sosyal-turbo`, `ilanim-google`). When the code renamed something during the session, use the final name. CamelCase code names become separate words only where a reader would split them (`AdSet` → `adset`).
- Do not name things the session never stated: say `uv-migration`, not `pipenv-to-uv-migration`, unless the session said where it migrated from. File names, edited paths and replies count as stated.
- No dates, no session numbers, no emoji, no quotes.

## The stranger test

Someone who was not in the session reads only the name in the `/resume` list. They must understand what the session was about. So use the name of the system, feature or problem as people outside the session call it, never the session's own internal labels: phase or step numbers (`phase-zero`, `faz-5`), finding numbers (`k-1`, `bulgu-3`), or a nickname coined during the session (`ghost-listings` for "deleted listings still shown from cache").

## Shape: subject + what was done

| Part | Use | Example |
|---|---|---|
| Subject | The most concrete thing the work was about: a system, feature, tool or file family from the session | `pipenv-to-uv`, `sse-reconnect`, `anonymous-quota` |
| Action / outcome | What the session did to it; any fitting word, the list is only examples | `migration`, `fix`, `review`, `plan`, `setup`, `design`, `investigation`, `cleanup`, `implementation`, `comparison` |

Choose the outcome word from what actually happened. A session that only planned is `-plan`, not `-migration`. A session that hunted a bug without fixing it is `-investigation`, not `-fix`. A partial but real improvement (eval 63→86 of 112) still counts as `-fix`. When the outcome is unknown, or the session found the cause and another team fixed it, use the neutral word for the activity (`-investigation`, `-debug`). New behaviour is `-implementation` or `-support`, not `-fix`. A pure question session may use `-comparison`, `-questions` or no action word. Work that was done and then fully reverted is `-attempt`. The action word may be dropped when the subject already says what changed (`rental-nationwide-targeting`) or when it does not fit in 40 characters.

Project or service name: add it (`billing-api-uv-migration`) when it fits within 40 characters and the session edited files in more than one project, or when the subject alone would be vague. Projects that were only read do not count. When the edited projects belong to one product (`conversational-search-service` and `conversational-search-api`), use the product's short name once (`conversational-search-feedback`). Otherwise leave it out. A product name seen in the session does not have to appear; use it when it is the most concrete subject.

## Bad names and why

| Bad name | Problem | Better |
|---|---|---|
| `uv-means` | Named after a side question | `pipenv-to-uv-migration` |
| `fix-bug`, `code-changes`, `session-work` | Fits any session | `sse-gzip-timeout-fix` |
| `pr-description-request` | Named after the last prompt | `payment-retry-refactor` |
| `docker-build-error` | Opening goal, abandoned after two prompts while the rest went to a refactor | `payment-retry-refactor` |
| `rename-skill` | Copied the naming request that invoked this skill | name the work before it (if that work was building a naming skill, naming it after that skill is right) |
| `cleanup-phase-zero-tasks` | Internal phase label; a stranger cannot tell what was cleaned | `search-agent-dead-code-cleanup` |
| `ghost-listings` | Nickname coined in the session; no system, no action | `stale-listing-cache-fix` |
| `yakin-ilceler-duzeltme` | Turkish words | `nearby-districts-fix` |

## Ticket IDs

A ticket ID the user asks for in the request that invoked this skill always goes at the start of the main name; that request overrides the rest of this section. Otherwise include a ticket ID (`ai-314-...`), at the start of the name, only when the user's prompts use it as the main handle of the work (several prompts refer to the work by it). Do not add one that appears only in a branch name (also when a prompt mentions that branch), a compaction summary or a single log line; offer it as an alternative instead. PR numbers (`pr-71`) follow the same rule. Two IDs that are both main handles may both go in when the name still fits (`ai-401-402-favorites-fix`); otherwise leave both out and offer the ID version as an alternative.
