# Scripts Guidelines

Read this when deciding whether logic belongs in a script or in SKILL.md prose, or when writing a new bash script for a skill.

## Why Scripts Are (Almost) Free

When the model runs `bash scripts/foo.sh`, only the **output** enters the context window — not the script source. Compare:

| Approach | Context cost |
|---|---|
| 50-line bash script | ~10 tokens (command line) + stdout |
| Same logic as prose in SKILL.md | ~400 tokens |
| Same logic as inline code block | ~350 tokens |

A script with a 5-line output costs ~60 tokens total. Equivalent SKILL.md prose costs 5-10× more.

## When to Prefer a Script

| Situation | Use script? |
|---|---|
| ≥ 5 if/else / case branches | Yes |
| Detect project language from 6+ file checks | Yes |
| Enumerate files matching a pattern | Yes |
| Run a tool and capture structured output | Yes |
| Static lookup table (>15 rows) | Yes |
| Command dispatch (run mvn / gradle / pytest based on context) | Yes |
| Single one-liner that fits in a sentence | No — inline in SKILL.md |
| Decision with 2-3 branches, no file I/O | No — prose is clearer |
| Human-readable explanation of a concept | No — keep in SKILL.md or references/ |

## Bash Portability (macOS + Linux)

Always target both macOS (BSD tools) and Linux (GNU tools):

```bash
# String length — portable
len=${#str}

# Regex match — use [[ ]] not [ ]
if [[ "$str" =~ ^[a-z][a-z0-9-]+$ ]]; then ...

# File existence
[[ -f "$path" ]] && [[ -d "$dir" ]]

# Count lines portably
wc -l < "$file" | tr -d ' '

# Word count
wc -w < "$file" | tr -d ' '

# grep -E for extended regex (both platforms)
grep -E "pattern" file

# Avoid GNU-only flags: --color=always, -P (Perl regex), etc.
# Use find -name, not find -iname when case doesn't matter
```

## Script Header Template

```bash
#!/usr/bin/env bash
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${1:-}"

if [[ -z "$TARGET" ]]; then
  echo "Usage: $0 <target-path>" >&2
  exit 1
fi
```

- `set -e` — exit on first error
- `set -u` — error on unset variables
- `set -o pipefail` — pipe failures propagate

## Exit Codes

| Exit code | Meaning |
|---|---|
| 0 | Success / PASS |
| 1 | Validation failure / FAIL |
| 2 | Usage error (wrong args) |
| 3+ | Tool-specific error |

Always write human-readable status to **stdout**, errors/warnings to **stderr**.

```bash
echo "PASS: description length OK (${len} chars)" 
echo "FAIL: SKILL.md exceeds 2000 words (${wc} found)" >&2
```

## Execute vs Read-as-Reference

Scripts should be **executed** (not read as text) when the output drives the next step. They should be read as reference only when you need to understand the logic before modifying it.

**Execute pattern:**
```
bash scripts/detect-language.sh
# → output: "java 17"
# Use this output to choose the right linter command
```

**Read pattern:**
```
# When user asks "what does detect-language.sh check?"
# → Read the file to explain it, do not execute
```
