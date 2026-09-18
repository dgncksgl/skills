# Worked Examples

Read this when you want to see the rules applied to a real answer, or when an
explanation you drafted feels heavy and you are unsure why.

All examples below are rewrites of answers actually given in this project.

---

## Example 1 — "What does this change do?"

Context: the LLM provider was moved behind a port so the project is not tied to
one vendor.

### Weak version

> The refactor achieves dependency inversion by placing the LLM provider behind
> a port in the application layer; the infrastructure adapter becomes
> substitutable, wiring happens through `config/settings.py`, and the p95
> latency impact is roughly 2%.

Why it fails: five terms in one sentence, no example, a number nobody asked for,
and the reader still does not know what changed for them.

### Strong version

> **In short: we can now switch to an AI provider other than OpenAI.**
>
> The code used to call OpenAI directly. Now there is a socket in between: the
> application asks for "an AI provider", and only one small piece decides which
> one that is.
>
> Example: if we move to another provider tomorrow, we change what is plugged
> into that socket. The rest of the application keeps working untouched.
>
> The wiring lives in `config/settings.py` if you want to look.

Why it works: answer first, everyday words, one real example, path offered at
the end instead of dropped in the middle.

---

## Example 2 — When a code block is the right answer

Context: the user asks why a test started failing after a rename.

### Weak version

> The assertion compares against the previous camelCase serialization contract,
> which no longer matches post-rename snake_case field emission.

### Strong version

> **In short: the test still expects the old field name.**
>
> We renamed the field, but the test was not updated, so it looks for something
> that no longer exists.
>
> Only the line that matters:
>
> ```python
> # the response now sends user_avatar, not userAvatar
> assert body["userAvatar"] == "..."   # <- fails here
> ```
>
> Example: the response now contains `user_avatar`, so this comparison can never
> be true. Fixing the test means renaming it in the same way we renamed the field.

Why it works: the code block is three lines, labelled, with one comment on the
one line that matters.

---

## Example 3 — The user said "I did not understand"

Never re-send the same explanation with more words. Change the angle.

### First attempt (failed)

> The guardrail runs before the agent call and short-circuits the workflow when
> the input matches a PII pattern, returning a refusal message downstream.

### Second attempt (right approach)

> Let me try from a different side.
>
> Think of it as a doorman standing in front of the assistant.
>
> The doorman reads the message before the assistant ever sees it. If the message
> contains a phone number or an ID number, the doorman does not let it through
> and answers the user directly instead.
>
> Example: the user writes "call me at 0532...". The assistant never receives that
> message; the user gets a reply saying we cannot process personal details.

Why it works: new angle (a doorman), smaller steps, and a brand new example —
not the first explanation stretched longer.

---

## Example 4 — Short mode

The user wrote: "kısaca anlat, bu değişiklik neyi bozar?"

> **In short: nothing user-facing — only the tests that name the old field break.**
>
> Example: the listing search returns exactly the same results; two tests that
> still look for `userAvatar` fail until they are renamed.

Two lines, one example, no table, no code, no paths. That is short mode.
