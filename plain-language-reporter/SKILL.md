---
name: plain-language-reporter
description: "Write reports, findings lists, analyses, and standalone Markdown (.md) documents in plain everyday language, with the conclusion on top, a concrete example inside every finding, and technical detail (file paths such as .py modules, line numbers, measurements) kept in an appendix. Use when the user asks for a report, asks to document findings or an investigation, asks for a written summary, or says \"bana rapor ver\", \"rapor oluştur\", \"rapor hazırla\", \"rapor yaz\", \"raporla\", \"bulguları raporla\", \"raporu güncelle\", \"doküman hazırla\", \"write a report\", \"document the findings\". Also covers how a long report is published as a designed HTML artifact (status colours, finding cards, light and dark mode) and kept up to date as decisions are made. Inherits every language rule from the plain-language-explainer skill. Do not use for a short answer inside chat (use plain-language-explainer), for commit messages, pull request descriptions, code comments, or docstrings."
---

# Plain Language Reporter

## Overview

A report is read by people who were not in the conversation, often by people who
do not work in the code. It has to answer "what did we find and what should we
do" before it proves anything. This skill defines the structure and the look;
the writing style comes from **plain-language-explainer**, which applies in full.

## Language

Read the rules in `~/.claude/skills/plain-language-explainer/SKILL.md` and apply
them to every line of the report: answer first, everyday words, an example behind
every claim, short sentences.

Two differences from chat:

- **A brevity trigger shortens the report itself.** When the user says "kısaca",
  "shortly", "kısa tut" or similar (the list lives in the explainer's
  [Brevity Triggers](../plain-language-explainer/references/brevity-triggers.md)),
  write the short form: the Result, the findings in their four-line shape with
  nothing added around them, and the open decisions. Drop the appendix and every
  extra paragraph, and keep the whole thing to about one screen. Examples and
  caveats are the two things brevity never buys — cut everything else first.
- **Technical detail is not banned, it is relocated.** Paths, line numbers, and
  measurements belong in the appendix, where the reader who wants them goes.

## Structure

Write these sections in this order.

### 1. Result

Three sentences at most: what was investigated, what was found, what should
happen. Someone who reads only this section must know the decision.

### 2. Findings

Every finding uses the same four lines:

- **What happened** — one sentence, in plain words
- **Why it matters** — the effect on the user or the business, not on the code
- **Example** — one real, concrete case: a real search, a real screen, a real result
- **Recommendation** — one sentence saying what to do. If it treats the
  symptom rather than the cause, or holds only up to some limit, say that here

**Every number must be traceable to the source data.** Never turn a rate into a
count, or a count into a rate, when the other figure was not measured; if a
figure is derived, say what it was derived from. A made-up number destroys the
trust the rest of the report is asking for.

**Never drop a caveat to keep a finding short.** Known risks, limits, and open
questions belong in the finding itself, in plain words — not in the appendix and
not left out. Shortening a report means cutting background, never cutting doubt.

One finding covers one problem. Over about eight lines, it is two findings.

### 3. Decisions needed

Only if something has to be decided. Number the questions, give the options,
mark the recommended one, and put a one-line shortcut at the top so the reader
can answer everything at once: "If you agree with all: 1A 2B".

### 4. Appendix

File paths, line numbers, measurements, verification steps, raw output. Nothing
above this section needs them.

## Formatting

Tables, code blocks, and images are all allowed and often the fastest way to make
a finding land. The rules for keeping them readable are in
[Formatting Rules](../plain-language-explainer/references/formatting-rules.md).

Add a **screenshot, diagram, or before/after image** whenever prose is doing
poorly — a picture of the wrong output explains more than a paragraph about it.

## Delivery

A report is finished when it is also easy to look at.

- A long report is **published as a hand-written HTML artifact** and the link is
  given — never a raw Markdown dump, and never a plain document-type artifact
  (no status colour, no cards, tables that run off the screen). Use a document
  type only when the user asks for one to comment on or co-edit.
- **Load `artifact-design` before writing the page**, and `dataviz` too if the
  report carries a chart. The visual contract is in
  [Report Visual Style](references/report-visual-style.md).
- The chat message carries a four-line summary and the link, never a copy.
- On an update: republish to the same URL, move answered questions into a
  "Decided" section, renumber the rest, and update the plan in the same turn.

## Self-check before sending

0. Did the user ask for a short report? If yes, is this the short form?
1. Does every finding contain a real example?
2. Can someone who reads only "Result" say what should happen next?
3. Does every recommendation say honestly whether it fixes the cause or only
   the symptom, and does every known risk or open question appear in writing?
4. Can every number in the report be pointed back to the evidence it came from?
5. Did any path, line number, or measurement leak out of the appendix?
6. On the published page: can the severity of each finding be seen without
   reading a word, does nothing scroll sideways on a phone, and does it read
   correctly in both light and dark mode?

## Additional Resources

- [Report Template](references/report-template.md) — the skeleton to copy, section by section
- [Report Visual Style](references/report-visual-style.md) — how the published page looks: status colours, finding cards, table limits, HTML skeleton
- [Example Report](references/example-report.md) — a full short report written to these rules, with weak-version comparisons
