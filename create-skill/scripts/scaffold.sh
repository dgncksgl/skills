#!/usr/bin/env bash
set -euo pipefail

SKILLS_DEFAULT_DIR="$HOME/.claude/skills"
CURSOR_RESERVED="$HOME/.cursor/skills-cursor"

usage() {
  echo "Usage: $0 <skill-name> [--location PATH] [--force]" >&2
  echo "" >&2
  echo "  skill-name   Lowercase, hyphens allowed, e.g. my-new-skill" >&2
  echo "  --location   Parent directory (default: ~/.claude/skills/)" >&2
  echo "  --force      Overwrite if skill already exists" >&2
  exit 2
}

SKILL_NAME=""
LOCATION="$SKILLS_DEFAULT_DIR"
FORCE=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --location)
      shift
      LOCATION="${1:-}"
      [[ -z "$LOCATION" ]] && { echo "ERROR: --location requires a path" >&2; usage; }
      ;;
    --force)
      FORCE=true
      ;;
    -*)
      echo "ERROR: Unknown option: $1" >&2
      usage
      ;;
    *)
      if [[ -z "$SKILL_NAME" ]]; then
        SKILL_NAME="$1"
      else
        echo "ERROR: Unexpected argument: $1" >&2
        usage
      fi
      ;;
  esac
  shift
done

[[ -z "$SKILL_NAME" ]] && usage

if ! [[ "$SKILL_NAME" =~ ^[a-z][a-z0-9-]{0,62}$ ]]; then
  echo "ERROR: Skill name must match ^[a-z][a-z0-9-]{0,62}$ — got: '$SKILL_NAME'" >&2
  exit 1
fi

LOCATION="${LOCATION%/}"
SKILL_PATH="$LOCATION/$SKILL_NAME"

RESOLVED_CURSOR="$(cd "$CURSOR_RESERVED" 2>/dev/null && pwd || echo "$CURSOR_RESERVED")"
RESOLVED_SKILL="$(cd "$LOCATION" 2>/dev/null && echo "$LOCATION/$SKILL_NAME" || echo "$SKILL_PATH")"

if [[ "$RESOLVED_SKILL" == "$RESOLVED_CURSOR"* ]]; then
  echo "ERROR: Cannot create skills inside Cursor-reserved directory: $CURSOR_RESERVED" >&2
  exit 1
fi

if [[ -d "$SKILL_PATH" ]] && [[ "$FORCE" == false ]]; then
  echo "ERROR: '$SKILL_PATH' already exists. Use --force to overwrite." >&2
  exit 1
fi

mkdir -p "$SKILL_PATH/references" "$SKILL_PATH/scripts"

cat > "$SKILL_PATH/SKILL.md" << SKILLMD
---
name: $SKILL_NAME
description: "TODO: <WHAT it does in one sentence>. Use when <trigger scenarios>, or when user says \"<TR trigger>\", \"<EN trigger>\". Do not use when <anti-scenario>."
---

# $(echo "$SKILL_NAME" | sed 's/-/ /g' | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) substr($i,2)}1')

## Overview

TODO: One paragraph describing what this skill solves, primary languages/tools, and when to reach for it.

## Workflow

### Step 1: Gather Requirements

TODO: What information do you need before starting?

### Step 2: Detect Context

TODO: What should be inspected or detected first (language, build system, existing config)?

### Step 3: Execute

TODO: Main steps.

### Step 4: Validate

Run validation and confirm output is correct.

## Additional Resources

TODO: Link reference files once created.
- [Description Patterns](../create-skill/references/description-patterns.md)
- [Skill Structure](../create-skill/references/skill-structure.md)
SKILLMD

touch "$SKILL_PATH/references/.gitkeep"
touch "$SKILL_PATH/scripts/.gitkeep"

echo "SUCCESS: Skill scaffolded at $SKILL_PATH"
echo ""
echo "Next steps:"
echo "  1. Edit $SKILL_PATH/SKILL.md — replace all TODO placeholders"
echo "  2. Add reference files under $SKILL_PATH/references/"
echo "  3. Add scripts under $SKILL_PATH/scripts/ (chmod +x each)"
echo "  4. bash $(dirname "$0")/validate-skill.sh $SKILL_PATH"
