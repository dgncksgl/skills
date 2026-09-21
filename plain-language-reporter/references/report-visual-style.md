# Report Visual Style

Read this before publishing a report, to decide what the page looks like.

A report that reads well and looks like a wall of grey text still fails: the
reader skims it, misses the severity, and asks for a summary you already wrote.
Design is not decoration here — it is the second reading order.

## The one rule

> A report is published as a **hand-written HTML artifact**. Not a raw Markdown
> dump, not a plain document page.

A document-type artifact (Claude Docs and similar) renders plain text and plain
tables only: no severity colour, no cards, no badges, and wide tables run off
the screen. Use one **only when the user asks for a document** they will comment
on or co-edit, and say what is lost.

Load the **artifact-design** skill before writing the page. If the report
carries a chart, load **dataviz** too. This file adds the report-specific part
on top of those.

## Colour carries meaning, nothing else

Pick one accent and three status colours, define them as tokens on `:root`, and
redefine them for dark mode. Never colour something that has no status.

| Token | Means | Used on |
|---|---|---|
| `--crit` | Something is broken or user-visible | Finding border, badge |
| `--warn` | A risk or a limit, not broken yet | Finding border, badge |
| `--ok` | Verified, fixed, or no action needed | Finding border, badge, tick |
| `--accent` | Navigation and emphasis | Title rule, links, counters |

Every status colour needs a soft twin (`--crit-soft`) for badge backgrounds, and
every status must also be readable without colour — the badge carries a word
("Kritik", "Risk", "Temiz"), not just a hue.

## Page shape

1. **Header** — title, one-line subject, date.
2. **Summary strip** — the Result in a tinted panel, plus a small tally of
   findings by severity. This is what a manager reads.
3. **Finding cards** — one card per finding, a coloured left border by severity,
   the four lines inside with their labels as small caps.
4. **Decisions** — numbered blocks, the recommended option visibly marked.
5. **Appendix** — a sunk panel at the bottom, smaller type, mono for paths.

## Keeping it readable

| Element | Rule |
|---|---|
| Content width | ~760px, centred. Long lines are the main readability killer |
| Tables | 4 columns max; wrap in a scroll container so the page never scrolls sideways |
| Long lists | A list of 10+ rows becomes cards or a definition list, not a wide table |
| Paths, commands | Mono font, `--surface-sunk` background, never bold body text |
| Type scale | 3 sizes: heading, body, meta. More sizes make it look like a form |
| Phone width | Must work at 360px with a 16px gutter and no horizontal scroll |

## Skeleton

```html
<style>
  :root{
    --bg:#f5f6f8; --surface:#fff; --surface-sunk:#eef0f3;
    --ink:#1b1f26; --muted:#68717d; --border:#dde1e6;
    --accent:#0f6e8c; --accent-soft:#e2eff4;
    --crit:#a8202c; --crit-soft:#fae9ea;
    --warn:#8a5a00; --warn-soft:#faf0dd;
    --ok:#1c6e47;   --ok-soft:#e5f2ea;
  }
  @media (prefers-color-scheme: dark){
    :root:not([data-theme="light"]){ /* dark values for every token above */ }
  }
  :root[data-theme="dark"]{ /* same dark values */ }
  body{background:var(--bg); color:var(--ink); margin:0;}
  .wrap{max-width:760px; margin:0 auto; padding:32px 16px;}
  .finding{background:var(--surface); border:1px solid var(--border);
           border-left:4px solid var(--border); border-radius:8px;
           padding:16px 18px; margin:14px 0;}
  .finding.sev-crit{border-left-color:var(--crit);}
  .finding.sev-warn{border-left-color:var(--warn);}
  .finding.sev-ok  {border-left-color:var(--ok);}
  .badge{font-size:12px; padding:2px 8px; border-radius:999px;}
  .badge.crit{background:var(--crit-soft); color:var(--crit);}
  .label{font-size:11px; letter-spacing:.06em; text-transform:uppercase;
         color:var(--muted);}
</style>
```

## Self-check on the page

1. Can the severity of each finding be seen without reading a word?
2. Does anything scroll sideways at phone width?
3. Is every colour on the page carrying a meaning?
4. Does it look right in both light and dark mode?
