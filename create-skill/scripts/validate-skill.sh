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
LINT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/skill_lint.py"

pass() {
  echo "  PASS: $1"
  PASS=$((PASS + 1))
}

fail() {
  echo "  FAIL: $1"
  FAIL=$((FAIL + 1))
}

finish() {
  echo ""
  if [[ $FAIL -eq 0 ]]; then
    echo "=== RESULT: PASS ($PASS passed, $FAIL failed) ==="
    exit 0
  fi
  echo "=== RESULT: FAIL ($PASS passed, $FAIL failed) ==="
  exit 1
}

field() {
  python3 -c '
import json, sys
value = json.load(sys.stdin)
for key in sys.argv[1:]:
    value = value.get(key) if isinstance(value, dict) else None
if isinstance(value, list):
    print("\n".join(str(v) for v in value))
elif isinstance(value, dict):
    print("<map>")
elif value is not None:
    print(value)
' "$@" <<< "$FM_JSON"
}

echo "=== Validating: $TARGET ==="
echo ""

if [[ -f "$TARGET/SKILL.md" ]]; then
  pass "SKILL.md exists"
else
  fail "SKILL.md not found"
  finish
fi

SKILL_MD="$TARGET/SKILL.md"
SKILL_ROOT="$(cd "$TARGET" && pwd)"
FM_JSON=$(python3 "$LINT" frontmatter "$SKILL_MD")

while IFS= read -r warning; do
  [[ -n "$warning" ]] && echo "  WARN: $warning"
done < <(field warnings)

FM_ERRORS=$(field errors)
if [[ -z "$FM_ERRORS" ]]; then
  pass "Frontmatter starts on line 1 and parses as YAML"
else
  while IFS= read -r error; do
    fail "Frontmatter: $error"
  done <<< "$FM_ERRORS"
fi

NAME_VAL=$(field fields name)
if [[ -z "$NAME_VAL" ]]; then
  fail "name field missing or empty"
else
  NAME_ERRORS=$(python3 "$LINT" name "$NAME_VAL" "$(basename "$SKILL_ROOT")" || true)
  if [[ -z "$NAME_ERRORS" ]]; then
    pass "name '$NAME_VAL' is valid and matches the directory"
  else
    while IFS= read -r error; do
      fail "$error"
    done <<< "$NAME_ERRORS"
  fi
fi

DESC_VAL=$(field fields description)
if [[ -z "$DESC_VAL" || "$DESC_VAL" == "<map>" ]]; then
  fail "description field missing, empty, or not a string"
else
  DESC_LEN=$(field description_length)
  if [[ $DESC_LEN -le 1024 ]]; then
    pass "description length OK ($DESC_LEN chars <= 1024)"
  else
    fail "description too long ($DESC_LEN chars > 1024)"
  fi
  if grep -qE "<[A-Za-z/][^>]*>" <<< "$DESC_VAL"; then
    fail "description contains XML/HTML tags"
  else
    pass "description has no XML tags"
  fi
  if grep -qi "use when" <<< "$DESC_VAL"; then
    pass "description contains 'Use when' clause"
  else
    fail "description missing 'Use when' clause"
  fi
fi

if grep -qE "^TODO:|TODO: <" "$SKILL_MD"; then
  fail "scaffold TODO placeholders remain"
else
  pass "No scaffold TODO placeholders"
fi

WORD_COUNT=$(wc -w < "$SKILL_MD" | tr -d ' ')
if [[ $WORD_COUNT -le 2000 ]]; then
  pass "SKILL.md word count OK ($WORD_COUNT words <= 2000)"
else
  fail "SKILL.md too long ($WORD_COUNT words > 2000)"
fi

BROKEN_REFS=0
while IFS= read -r ref; do
  [[ -z "$ref" ]] && continue
  [[ "$ref" =~ ^(https?:|mailto:|#) ]] && continue
  path="${ref%%#*}"
  if [[ ! -e "$SKILL_ROOT/$path" ]]; then
    echo "  WARN: Broken link -> $ref"
    BROKEN_REFS=$((BROKEN_REFS + 1))
  elif [[ "$(cd "$(dirname "$SKILL_ROOT/$path")" && pwd)/" != "$SKILL_ROOT/"* ]]; then
    echo "  WARN: Link points outside the skill directory (breaks if the skill is moved alone) -> $ref"
  fi
done < <(python3 "$LINT" stats "$SKILL_MD" | python3 -c 'import json, sys; print("\n".join(json.load(sys.stdin)["links"]))')

if [[ $BROKEN_REFS -eq 0 ]]; then
  pass "All relative links resolve"
else
  fail "$BROKEN_REFS broken link(s) found"
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
  fail "$NON_EXEC script(s) not executable (run: chmod +x $SCRIPTS_DIR/*)"
fi

finish
