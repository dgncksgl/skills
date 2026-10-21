# Skill Structure

Read this when scaffolding a new skill directory or deciding where to place content.

## Canonical Directory Layout

```
~/.claude/skills/<skill-name>/
├── SKILL.md                    (spine — ≤2000 words, ideally ≤1000)
├── references/
│   ├── <topic-a>.md            (lookup tables, detailed examples, rule lists)
│   └── <topic-b>.md
└── scripts/                    (only when there is deterministic logic)
    ├── <task>.sh               (bash, executable)
    └── <parser>.py             (python3 stdlib, executable, when parsing needs it)
```

Storage locations are listed in SKILL.md.

## SKILL.md Skeleton

```markdown
---
name: <skill-name>
description: "<WHAT>. Use when <scenarios>. Do not use when <anti-scenarios>."
---

# <Skill Title>

## Overview
One paragraph. What it solves, primary languages/tools, when to reach for it.

## Workflow

### Step 1: ...
### Step 2: ...
### Step N: Verify
How to confirm the result is correct.

## Additional Resources
- [<Topic>](references/<topic>.md) — when to read it
```

## Reference File Skeleton

```markdown
# <Topic Title>

Read this when <specific situation that requires this file>.

## Section A
...tables, lists, examples...

## Section B
...
```

- Open with "Read this when..." to enable progressive disclosure.
- Prefer tables and bullet lists over prose — they scan faster.
- No word limit, but keep a single reference under ~400 lines.

## Script File Skeleton

```bash
#!/usr/bin/env bash
set -euo pipefail

# Usage: bash scripts/<name>.sh <arg> [options]
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${1:-}"

if [[ -z "$TARGET" ]]; then
  echo "Usage: $0 <target>" >&2
  exit 2
fi

# ... logic ...
```

## What Belongs Where

| Content type | Location |
|---|---|
| Workflow steps (5–10 lines each) | SKILL.md |
| Tables > 10 rows | `references/` |
| Lists > 15 items | `references/` |
| Detailed code examples | `references/` |
| If/else chains ≥ 5 branches | `scripts/` |
| Command dispatch (detect language, run tool) | `scripts/` |
| Lookup tables an agent reads (rule IDs) | `references/` |
| Static data a script consumes (file extensions) | inside the script |
| One-liner commands | SKILL.md inline |

## Word Budget for SKILL.md

| Section | Target words |
|---|---|
| Frontmatter description | as short as the mandatory elements allow (≤ 1024 chars) |
| Overview | ~80 words |
| Workflow steps (total) | ~500 words |
| Storage / config notes | ~100 words |
| Additional Resources list | ~50 words |
| **Total** | **≤ 1000 words (ideal)** |

Audit scores ≤ 1000 words 25/25, 1001–1500 20/25, 1501–2000 12/25. Validate fails above 2000 words.
