#!/usr/bin/env bash
set -euo pipefail

PASS=0
FAIL=0

usage() {
  echo "Usage: $0 <skill-path>" >&2
  exit 2
}

TARGET="${1:-}"
[[ -z "$TARGET" ]] && usage

TARGET="${TARGET%/}"

pass() {
  echo "  PASS: $1"
  PASS=$((PASS + 1))
}

fail() {
  echo "  FAIL: $1"
  FAIL=$((FAIL + 1))
}

echo "=== Validating: $TARGET ==="
echo ""

if [[ -f "$TARGET/SKILL.md" ]]; then
  pass "SKILL.md exists"
else
  fail "SKILL.md not found"
  echo ""
  echo "RESULT: FAIL ($PASS passed, $FAIL failed)"
  exit 1
fi

SKILL_MD="$TARGET/SKILL.md"

FRONT_START=""
FRONT_END=""
FRONT_START=$(grep -n "^---$" "$SKILL_MD" 2>/dev/null | head -1 | cut -d: -f1 || true)
FRONT_END=$(grep -n "^---$" "$SKILL_MD" 2>/dev/null | awk 'NR==2{print $1}' FS=: || true)

if [[ -n "$FRONT_START" ]] && [[ -n "$FRONT_END" ]]; then
  pass "Frontmatter delimiters found (lines $FRONT_START to $FRONT_END)"
else
  fail "Frontmatter delimiters (---) missing or malformed"
fi

NAME_VAL=""
if grep -qE "^name:" "$SKILL_MD" 2>/dev/null; then
  NAME_VAL=$(grep -E "^name:" "$SKILL_MD" | head -1 | sed 's/^name:[[:space:]]*//')
  if [[ -n "$NAME_VAL" ]]; then
    pass "name field present: '$NAME_VAL'"
  else
    fail "name field present but empty"
  fi
else
  fail "name field missing from frontmatter"
fi

if [[ -n "$NAME_VAL" ]]; then
  NAME_CLEAN=$(echo "$NAME_VAL" | tr -d '"' | tr -d "'")
  if [[ "$NAME_CLEAN" =~ ^[a-z][a-z0-9-]{0,62}$ ]]; then
    pass "name matches regex ^[a-z][a-z0-9-]{0,62}$"
  else
    fail "name '$NAME_CLEAN' does not match regex ^[a-z][a-z0-9-]{0,62}$"
  fi
fi

DESC_RAW=""
if grep -qE "^description:" "$SKILL_MD" 2>/dev/null; then
  DESC_RAW=$(grep -E "^description:" "$SKILL_MD" | head -1 | sed 's/^description:[[:space:]]*//')
  DESC_LEN=${#DESC_RAW}
  if [[ $DESC_LEN -le 1024 ]]; then
    pass "description length OK ($DESC_LEN chars <= 1024)"
  else
    fail "description too long ($DESC_LEN chars > 1024)"
  fi
  if echo "$DESC_RAW" | grep -qi "use when"; then
    pass "description contains 'Use when' clause"
  else
    fail "description missing 'Use when' clause"
  fi
else
  fail "description field missing from frontmatter"
  fail "description missing 'Use when' clause (cannot check -- no description)"
fi

WORD_COUNT=$(wc -w < "$SKILL_MD" | tr -d ' ')
if [[ $WORD_COUNT -le 2000 ]]; then
  pass "SKILL.md word count OK ($WORD_COUNT words <= 2000)"
else
  fail "SKILL.md too long ($WORD_COUNT words > 2000)"
fi

BROKEN_REFS=0
while IFS= read -r line; do
  ref=$(echo "$line" | grep -oE '\(references/[^)]+\.md\)' | tr -d '()' || true)
  if [[ -n "$ref" ]]; then
    if [[ ! -f "$TARGET/$ref" ]]; then
      echo "  WARN: Broken reference link -> $ref"
      BROKEN_REFS=$((BROKEN_REFS + 1))
    fi
  fi
done < "$SKILL_MD"

if [[ $BROKEN_REFS -eq 0 ]]; then
  pass "No broken reference links"
else
  fail "$BROKEN_REFS broken reference link(s) found"
fi

SCRIPTS_DIR="$TARGET/scripts"
NON_EXEC=0
if [[ -d "$SCRIPTS_DIR" ]]; then
  while IFS= read -r script; do
    fname=$(basename "$script")
    [[ "$fname" == ".gitkeep" ]] && continue
    if [[ ! -x "$script" ]]; then
      echo "  WARN: Not executable -> $script"
      NON_EXEC=$((NON_EXEC + 1))
    fi
  done < <(find "$SCRIPTS_DIR" -maxdepth 1 -type f 2>/dev/null || true)
fi

if [[ $NON_EXEC -eq 0 ]]; then
  pass "All scripts are executable"
else
  fail "$NON_EXEC script(s) not executable (run: chmod +x $SCRIPTS_DIR/*.sh)"
fi

echo ""
if [[ $FAIL -eq 0 ]]; then
  echo "=== RESULT: PASS ($PASS passed, $FAIL failed) ==="
  exit 0
else
  echo "=== RESULT: FAIL ($PASS passed, $FAIL failed) ==="
  exit 1
fi
