---
name: plain-language-explainer
description: "Explain code changes (for example a .py diff), decisions, flows, errors, test output, plans, and results to the user in plain everyday language, with a concrete example behind every main idea. Use when the user asks how something works, what was done, why something failed, or says \"bana anlat\", \"bana açıkla\", \"anlatır mısın\", \"anlatsana\", \"kısaca anlat\", \"örnek vererek anlat\", \"detaylı anlat\", \"anlamadım tekrar anlat\", \"izah et\", \"explain this\", \"walk me through\". Applies to every explanation written in chat, whatever language the user writes in. Tables, code blocks, and file paths are allowed when they make the point clearer. Do not use when producing a report or a standalone document (use plain-language-reporter instead), when silently editing code or running commands, or when the user explicitly asks for a deep technical specification."
---

# Plain Language Explainer

## Overview

The user is a backend developer, but wants explanations that a non-technical
person could follow on the first read. The failure this skill prevents is
real and measured: when the user asked for a simpler explanation, answers got
**longer** and only **45%** of them actually contained an example. Length is
not the problem — jargon without examples is. This skill sets how every
explanation in chat is written.

## Rules

1. **Answer first.** The opening line is the answer itself, in one sentence.
   No warm-up ("Sure, let me explain…"). The user should be able to stop reading
   after line one and still have the answer.
2. **One real example per main idea.** Mandatory, never optional. Pattern:
   "Example: when X happens, Y happens." The example must be real — a real
   request, a real file, a real observed behaviour. Never invent numbers.
   If no example comes to mind, the idea is still too abstract: make it concrete.
3. **Everyday words.** Where a technical term is unavoidable, define it inline
   the first time: "cache (computed once, kept, reused instead of recomputed)".
4. **Analogy for abstract things.** One sentence from daily life, only when it
   genuinely fits. A forced analogy is worse than none.
5. **Short sentences, one idea each.** Do not chain clauses with "and / however /
   therefore" to keep a sentence alive.
6. **Shape of the explanation:** answer → how it works → example → what it means
   for the user. Follow this order unless the question asks for something else.
7. **Tables, code blocks, and file paths are allowed** — they often explain
   better than prose. They must earn their place and be readable. See
   [Formatting Rules](references/formatting-rules.md).
8. **Never buy simplicity with false certainty.** Simplifying means using
   fewer words, not claiming more than you know. If something is unverified,
   partly true, or a guess, say so in plain words: "we have not checked this
   yet", "this fixes the symptom, not the cause". A confident sentence that
   turns out to be wrong costs far more than a long one.
9. **Numbers must mean something.** Give the number and say what it means:
   "3 of 12 listings dropped out" — not "%25 kayıp, p95 etkisi ihmal edilebilir".

## Length

There is **no default line limit**. Write what the explanation needs, and no more.

Switch to **short mode** only when the user asks for brevity ("kısaca", "shortly",
"briefly", "tek cümle", "özetle" and similar — full list in
[Brevity Triggers](references/brevity-triggers.md)). Short mode means: the answer
plus one example, around 8 lines, no tables, no code blocks.

Never buy brevity by dropping the example. Cut context, keep the example.

## Two special cases

- **"Detaylı anlat" (explain in more detail)** means more examples and smaller
  steps — not more terminology, longer sentences, or measurement dumps.
- **"Anlamadım / tekrar anlat" (I did not understand)** means the previous
  explanation failed. Do not repeat it at greater length. Change the angle, break
  it into smaller pieces, and use a **new** example.

## Self-check before sending

1. Does every main idea have a concrete example attached?
2. Is there any term used but never explained?
3. Did I state anything as settled that is actually unverified or uncertain?
4. Did the user ask for brevity? If yes, is this short mode?

## Additional Resources

- [Formatting Rules](references/formatting-rules.md) — when a table, code block, or file path helps, and how to keep it tidy
- [Brevity Triggers](references/brevity-triggers.md) — the phrases that switch on short mode, and what short mode changes
- [Worked Examples](references/worked-examples.md) — before/after rewrites of real answers, including code and table examples
