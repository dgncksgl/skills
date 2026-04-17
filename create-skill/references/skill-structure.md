# Skill Structure

Read this when scaffolding a new skill directory or deciding where to place content.

## Canonical Directory Layout

```
~/.claude/skills/<skill-name>/
├── SKILL.md                    (spine — ≤2000 words, ideally ~1000-1200)
├── references/
│   ├── <topic-a>.md            (lookup tables, detailed examples, rule lists)
│   └── <topic-b>.md
└── scripts/
    ├── <task>.sh               (deterministic logic, executables)
    └── <other>.sh
```

**Storage locations:**

| Location | Purpose | Editable by skill? |
|---|---|---|
| `~/.claude/skills/<name>/` | Personal Claude skills | Yes |
| `~/.cursor/skills-cursor/<name>/` | Cursor-reserved skills | **Never touch** |
| `<project>/.claude/skills/<name>/` | Project-scoped skills | Yes |

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
### Step N: Validate
Run `bash scripts/validate.sh` (or equivalent) and confirm output.

## Additional Resources
- [Description Patterns](references/description-patterns.md) — trigger phrase examples
- [Structure Guide](references/skill-structure.md) — directory layout
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
  exit 1
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
| Static lookup tables (rule IDs, file extensions) | `scripts/` or `references/` |
| One-liner commands | SKILL.md inline |

## Word Budget for SKILL.md

| Section | Target words |
|---|---|
| Frontmatter description | ~80 words |
| Overview | ~80 words |
| Workflow steps (total) | ~500 words |
| Storage / config notes | ~100 words |
| Additional Resources list | ~50 words |
| **Total** | **~810–1000 words** |

Exceeding 1500 words is a warning. Exceeding 2000 words is a hard fail.
