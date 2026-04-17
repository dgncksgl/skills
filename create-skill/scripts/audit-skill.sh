#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 <skill-path>" >&2
  exit 2
}

TARGET="${1:-}"
[[ -z "$TARGET" ]] && usage
TARGET="${TARGET%/}"

SKILL_MD="$TARGET/SKILL.md"

if [[ ! -f "$SKILL_MD" ]]; then
  echo "ERROR: SKILL.md not found at $TARGET" >&2
  exit 1
fi

TOTAL=0

# --- Section 1: Word Budget (25 pts) ---
WORD_COUNT=$(wc -w < "$SKILL_MD" | tr -d ' ')
if [[ $WORD_COUNT -le 1000 ]]; then
  WB_SCORE=25; WB_LABEL="ideal"
elif [[ $WORD_COUNT -le 1500 ]]; then
  WB_SCORE=20; WB_LABEL="good"
elif [[ $WORD_COUNT -le 2000 ]]; then
  WB_SCORE=12; WB_LABEL="acceptable"
else
  WB_SCORE=0; WB_LABEL="FAIL"
fi
TOTAL=$((TOTAL + WB_SCORE))

# --- Section 2: Progressive Disclosure (20 pts) ---
PD_SCORE=0
PD_TABLE_OK=true
PD_LIST_OK=true
PD_CODE_OK=true
PD_REFS_OK=true

TABLE_ROWS=0
TABLE_ROWS=$(grep -cE "^\|" "$SKILL_MD" 2>/dev/null) || true
if [[ $TABLE_ROWS -le 10 ]]; then
  PD_SCORE=$((PD_SCORE + 5))
else
  PD_TABLE_OK=false
fi

LIST_ITEMS=0
LIST_ITEMS=$(grep -cE "^[-*] " "$SKILL_MD" 2>/dev/null) || true
if [[ $LIST_ITEMS -le 15 ]]; then
  PD_SCORE=$((PD_SCORE + 5))
else
  PD_LIST_OK=false
fi

CODE_BLOCKS=0
CODE_BLOCKS=$(grep -cE "^\`\`\`" "$SKILL_MD" 2>/dev/null) || true
CODE_PAIRS=$((CODE_BLOCKS / 2))
if [[ $CODE_PAIRS -le 3 ]]; then
  PD_SCORE=$((PD_SCORE + 5))
else
  PD_CODE_OK=false
fi

REF_COUNT=0
if [[ -d "$TARGET/references" ]]; then
  REF_COUNT=$(find "$TARGET/references" -maxdepth 1 -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
fi
if [[ $REF_COUNT -ge 1 ]]; then
  PD_SCORE=$((PD_SCORE + 5))
else
  PD_REFS_OK=false
fi

TOTAL=$((TOTAL + PD_SCORE))

# --- Section 3: Scripts Token Efficiency (20 pts) ---
SE_SCORE=0
SE_DIR_OK=false
SE_EXEC_OK="n/a"
SE_LOGIC_OK=true
SCRIPTS_DIR="$TARGET/scripts"

if [[ -d "$SCRIPTS_DIR" ]]; then
  SE_SCORE=$((SE_SCORE + 5))
  SE_DIR_OK=true
fi

EXEC_COUNT=0
SCRIPT_COUNT=0
if [[ -d "$SCRIPTS_DIR" ]]; then
  while IFS= read -r script; do
    fname=$(basename "$script")
    [[ "$fname" == ".gitkeep" ]] && continue
    SCRIPT_COUNT=$((SCRIPT_COUNT + 1))
    [[ -x "$script" ]] && EXEC_COUNT=$((EXEC_COUNT + 1))
  done < <(find "$SCRIPTS_DIR" -maxdepth 1 -type f -name "*.sh" 2>/dev/null || true)
fi

if [[ $SCRIPT_COUNT -gt 0 ]]; then
  if [[ $EXEC_COUNT -eq $SCRIPT_COUNT ]]; then
    SE_SCORE=$((SE_SCORE + 5)); SE_EXEC_OK=true
  else
    SE_EXEC_OK=false
  fi
fi

IF_CHAINS=0
IF_CHAINS=$(grep -cE "^\s*(if |elif |case )" "$SKILL_MD" 2>/dev/null) || true
if [[ $IF_CHAINS -lt 5 ]]; then
  SE_SCORE=$((SE_SCORE + 10))
else
  SE_LOGIC_OK=false
fi
TOTAL=$((TOTAL + SE_SCORE))

# --- Section 4: Description Quality (35 pts) ---
DQ_SCORE=0
DQ_EXISTS=false
DQ_LEN_OK=false
DQ_USE_WHEN=false
DQ_NEG=false
DQ_TR=false
DQ_EN=false
DQ_DOMAIN=false

DESC_RAW=""
DESC_LEN=0

DESC_RAW=$(python3 - "$SKILL_MD" << 'PYEOF'
import re, sys

path = sys.argv[1]
try:
    content = open(path, encoding='utf-8').read()
except Exception:
    sys.exit(0)

fm_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
if not fm_match:
    sys.exit(0)
fm = fm_match.group(1)

# Block scalar (>- or > or |- or |)
m = re.search(r'^description:\s*[>|][+-]?\s*\n((?:[ \t]+.+\n?)+)', fm, re.MULTILINE)
if m:
    block = m.group(1)
    lines = [l.strip() for l in block.splitlines() if l.strip()]
    print(' '.join(lines))
    sys.exit(0)

# Inline (quoted or unquoted)
m = re.search(r'^description:\s*(.+)$', fm, re.MULTILINE)
if m:
    val = m.group(1).strip()
    # Strip surrounding quotes
    if (val.startswith('"') and val.endswith('"')) or \
       (val.startswith("'") and val.endswith("'")):
        val = val[1:-1]
    print(val)
PYEOF
) || true

if [[ -n "$DESC_RAW" ]]; then
  DQ_SCORE=$((DQ_SCORE + 5)); DQ_EXISTS=true
fi

DESC_LEN=${#DESC_RAW}
if [[ $DESC_LEN -gt 0 ]] && [[ $DESC_LEN -le 1024 ]]; then
  DQ_SCORE=$((DQ_SCORE + 5)); DQ_LEN_OK=true
fi

if echo "$DESC_RAW" | grep -qi "use when" 2>/dev/null; then
  DQ_SCORE=$((DQ_SCORE + 5)); DQ_USE_WHEN=true
fi

if echo "$DESC_RAW" | grep -qi "do not use" 2>/dev/null; then
  DQ_SCORE=$((DQ_SCORE + 5)); DQ_NEG=true
fi

TR_FOUND=$(python3 -c "
import sys
desc = sys.stdin.read()
tr_chars = set('çğışöüÇĞİŞÖÜ')
print('yes' if any(c in tr_chars for c in desc) else 'no')
" <<< "$DESC_RAW" 2>/dev/null || echo "no")

if [[ "$TR_FOUND" == "yes" ]]; then
  DQ_SCORE=$((DQ_SCORE + 5)); DQ_TR=true
fi

if echo "$DESC_RAW" | grep -qiE "(use when|when asked|when the user)" 2>/dev/null; then
  DQ_SCORE=$((DQ_SCORE + 5)); DQ_EN=true
fi

if echo "$DESC_RAW" | grep -qiE "\.(xml|toml|json|ts|py|go|java|kt|gradle|yaml|yml|sh)|pom\.xml|tsconfig|pyproject|go\.mod|sonar|junit|pytest|mypy|eslint|SKILL\.md|rule.ID|S[0-9]{4}" 2>/dev/null; then
  DQ_SCORE=$((DQ_SCORE + 5)); DQ_DOMAIN=true
fi

TOTAL=$((TOTAL + DQ_SCORE))

# --- Output Report ---
fmt_check() {
  local ok="$1"
  local msg="$2"
  if [[ "$ok" == "true" ]]; then
    echo "  OK  : $msg"
  elif [[ "$ok" == "n/a" ]]; then
    echo "  N/A : $msg"
  else
    echo "  MISS: $msg"
  fi
}

echo "=============================================="
echo " Skill Audit: $(basename "$TARGET")"
echo " Path: $TARGET"
echo "=============================================="
echo ""
echo "1. WORD BUDGET           [$WB_SCORE/25] -- $WORD_COUNT words ($WB_LABEL)"
echo "2. PROGRESSIVE DISCLOSE  [$PD_SCORE/20]"
fmt_check "$PD_TABLE_OK" "Table rows <=10 in SKILL.md ($TABLE_ROWS rows)"
fmt_check "$PD_LIST_OK"  "List items <=15 in SKILL.md ($LIST_ITEMS items)"
fmt_check "$PD_CODE_OK"  "Code block pairs <=3 in SKILL.md ($CODE_PAIRS pairs)"
fmt_check "$PD_REFS_OK"  "references/ has .md files ($REF_COUNT files)"
echo "3. SCRIPTS EFFICIENCY    [$SE_SCORE/20]"
fmt_check "$SE_DIR_OK"   "scripts/ directory exists"
fmt_check "$SE_EXEC_OK"  "All .sh scripts executable ($EXEC_COUNT/$SCRIPT_COUNT)"
fmt_check "$SE_LOGIC_OK" "No inline if-chains >=5 in SKILL.md ($IF_CHAINS found)"
echo "4. DESCRIPTION QUALITY   [$DQ_SCORE/35]"
fmt_check "$DQ_EXISTS"   "description field exists"
fmt_check "$DQ_LEN_OK"   "description <=1024 chars ($DESC_LEN chars)"
fmt_check "$DQ_USE_WHEN" "description contains 'Use when'"
fmt_check "$DQ_NEG"      "description contains 'Do not use'"
fmt_check "$DQ_TR"       "description has Turkish triggers (c/g/i/o/s/u with diacritics)"
fmt_check "$DQ_EN"       "description has English triggers"
fmt_check "$DQ_DOMAIN"   "description has domain nouns (tool/file type/rule ID)"
echo ""
echo "----------------------------------------------"
echo " TOTAL SCORE: $TOTAL / 100"

if [[ $TOTAL -ge 90 ]]; then
  GRADE="Excellent"
elif [[ $TOTAL -ge 75 ]]; then
  GRADE="Good"
elif [[ $TOTAL -ge 50 ]]; then
  GRADE="Needs Work"
else
  GRADE="Failing"
fi

echo " GRADE: $GRADE"
echo "----------------------------------------------"
echo ""
echo "Top 3 Refactor Suggestions:"

SUGG_COUNT=0
print_suggestion() {
  SUGG_COUNT=$((SUGG_COUNT + 1))
  [[ $SUGG_COUNT -le 3 ]] && echo "  $SUGG_COUNT. $1"
}

[[ $WB_SCORE -lt 20 ]] && \
  print_suggestion "[PRIORITY: HIGH] Word budget: $WORD_COUNT words. Move tables/lists/code examples to references/ files."

[[ "$DQ_TR" == false ]] && \
  print_suggestion "[PRIORITY: HIGH] Turkish triggers missing. Add phrases like: 'skill olustur', 'yeni skill yaz'."

[[ "$DQ_NEG" == false ]] && \
  print_suggestion "[PRIORITY: HIGH] No negative trigger. Add: 'Do not use when <anti-scenario>'."

[[ "$DQ_DOMAIN" == false ]] && \
  print_suggestion "[PRIORITY: MEDIUM] No domain nouns. Name specific tools, file types, or rule IDs in description."

[[ "$PD_REFS_OK" == false ]] && \
  print_suggestion "[PRIORITY: MEDIUM] No reference files. Create references/<topic>.md for lookup tables and examples."

[[ "$SE_LOGIC_OK" == false ]] && \
  print_suggestion "[PRIORITY: MEDIUM] Inline if-chains in SKILL.md. Move to scripts/<task>.sh."

[[ "$DQ_USE_WHEN" == false ]] && \
  print_suggestion "[PRIORITY: HIGH] Description missing 'Use when' clause."

if [[ $SUGG_COUNT -eq 0 ]]; then
  echo "  None -- skill is fully compliant!"
fi

echo ""
