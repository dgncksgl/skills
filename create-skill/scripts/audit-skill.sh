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
LINT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/skill_lint.py"

if [[ ! -f "$SKILL_MD" ]]; then
  echo "ERROR: SKILL.md not found at $TARGET" >&2
  exit 1
fi

FM_JSON=$(python3 "$LINT" frontmatter "$SKILL_MD")
STATS_JSON=$(python3 "$LINT" stats "$SKILL_MD")

get() {
  local json="$1"
  shift
  python3 -c '
import json, sys
value = json.loads(sys.argv[1])
for key in sys.argv[2:]:
    value = value.get(key) if isinstance(value, dict) else None
if isinstance(value, bool):
    print("true" if value else "false")
elif isinstance(value, (dict, list)):
    print("<complex>")
elif value is not None:
    print(value)
' "$json" "$@"
}

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
TABLE_ROWS=$(get "$STATS_JSON" max_table_rows)
LIST_ITEMS=$(get "$STATS_JSON" max_list_items)
CODE_BLOCKS=$(get "$STATS_JSON" code_blocks)

PD_TABLE_OK=false
if [[ $TABLE_ROWS -le 10 ]]; then PD_SCORE=$((PD_SCORE + 5)); PD_TABLE_OK=true; fi
PD_LIST_OK=false
if [[ $LIST_ITEMS -le 15 ]]; then PD_SCORE=$((PD_SCORE + 5)); PD_LIST_OK=true; fi
PD_CODE_OK=false
if [[ $CODE_BLOCKS -le 3 ]]; then PD_SCORE=$((PD_SCORE + 5)); PD_CODE_OK=true; fi

REF_COUNT=0
if [[ -d "$TARGET/references" ]]; then
  REF_COUNT=$(find "$TARGET/references" -maxdepth 1 -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
fi
PD_REFS_OK=false
if [[ $REF_COUNT -ge 1 ]]; then
  PD_SCORE=$((PD_SCORE + 5)); PD_REFS_OK=true
elif [[ $WORD_COUNT -le 1000 && "$PD_TABLE_OK" == true && "$PD_LIST_OK" == true && "$PD_CODE_OK" == true ]]; then
  PD_SCORE=$((PD_SCORE + 5)); PD_REFS_OK="n/a"
fi
TOTAL=$((TOTAL + PD_SCORE))

# --- Section 3: Scripts Token Efficiency (20 pts) ---
SE_SCORE=0
SE_DIR_OK=false
SE_EXEC_OK="n/a"
SE_LOGIC_OK=true
SCRIPTS_DIR="$TARGET/scripts"

EXEC_COUNT=0
SCRIPT_COUNT=0
if [[ -d "$SCRIPTS_DIR" ]]; then
  while IFS= read -r script; do
    [[ "$(basename "$script")" == ".gitkeep" ]] && continue
    SCRIPT_COUNT=$((SCRIPT_COUNT + 1))
    [[ -x "$script" ]] && EXEC_COUNT=$((EXEC_COUNT + 1))
  done < <(find "$SCRIPTS_DIR" -maxdepth 1 -type f 2>/dev/null || true)
fi

IF_CHAINS=$(get "$STATS_JSON" if_chains)
if [[ $IF_CHAINS -lt 5 ]]; then
  SE_SCORE=$((SE_SCORE + 10))
else
  SE_LOGIC_OK=false
fi

if [[ $SCRIPT_COUNT -gt 0 ]]; then
  SE_SCORE=$((SE_SCORE + 5)); SE_DIR_OK=true
  if [[ $EXEC_COUNT -eq $SCRIPT_COUNT ]]; then
    SE_SCORE=$((SE_SCORE + 5)); SE_EXEC_OK=true
  else
    SE_EXEC_OK=false
  fi
elif [[ "$SE_LOGIC_OK" == true ]]; then
  SE_SCORE=$((SE_SCORE + 10)); SE_DIR_OK="n/a"
fi
TOTAL=$((TOTAL + SE_SCORE))

# --- Section 4: Description Quality (35 pts) ---
DQ_SCORE=0
DESC_RAW=$(get "$FM_JSON" fields description)
[[ "$DESC_RAW" == "<complex>" ]] && DESC_RAW=""
DESC_LEN=0
TR_COUNT=0
EN_OK=false
PROCEDURE=""
if [[ -n "$DESC_RAW" ]]; then
  DESC_LEN=$(get "$FM_JSON" description_length)
  TR_COUNT=$(get "$FM_JSON" turkish_phrases)
  EN_OK=$(get "$FM_JSON" english_trigger)
  PROCEDURE=$(get "$FM_JSON" procedure_hint)
fi

check_desc() {
  local ok="$1"
  if [[ "$ok" == true ]]; then DQ_SCORE=$((DQ_SCORE + 5)); fi
  echo "$ok"
}

DQ_EXISTS=$(check_desc "$([[ -n "$DESC_RAW" ]] && echo true || echo false)")
DQ_LEN_OK=$(check_desc "$([[ $DESC_LEN -gt 0 && $DESC_LEN -le 1024 ]] && echo true || echo false)")
DQ_USE_WHEN=$(check_desc "$(grep -qi "use when" <<< "$DESC_RAW" && echo true || echo false)")
DQ_NEG=$(check_desc "$(grep -qi "do not use" <<< "$DESC_RAW" && echo true || echo false)")
DQ_TR=$(check_desc "$([[ $TR_COUNT -ge 3 ]] && echo true || echo false)")
DQ_EN=$(check_desc "$EN_OK")
DQ_DOMAIN=$(check_desc "$(grep -qiE "\.(xml|toml|json|ts|py|go|java|kt|gradle|yaml|yml|sh|md|docx|xlsx|pdf|csv)\b|pom\.xml|tsconfig|pyproject|go\.mod|sonar|junit|pytest|mypy|eslint|rule.ID|S[0-9]{4}|(^|[ (\"'])/[a-z][a-z0-9-]+|(^|[ (\"'])--[a-z][a-z0-9-]+|~/\.[a-z]|\`[^\`]+\`" <<< "$DESC_RAW" && echo true || echo false)")
DQ_SCORE=0
for ok in "$DQ_EXISTS" "$DQ_LEN_OK" "$DQ_USE_WHEN" "$DQ_NEG" "$DQ_TR" "$DQ_EN" "$DQ_DOMAIN"; do
  [[ "$ok" == true ]] && DQ_SCORE=$((DQ_SCORE + 5))
done
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
fmt_check "$PD_TABLE_OK" "Largest table <=10 data rows in SKILL.md ($TABLE_ROWS rows)"
fmt_check "$PD_LIST_OK"  "Largest list <=15 items in SKILL.md ($LIST_ITEMS items)"
fmt_check "$PD_CODE_OK"  "Code blocks <=3 in SKILL.md ($CODE_BLOCKS blocks)"
fmt_check "$PD_REFS_OK"  "Offloaded content lives in references/ ($REF_COUNT .md files; n/a: SKILL.md has nothing to offload)"
echo "3. SCRIPTS EFFICIENCY    [$SE_SCORE/20]"
fmt_check "$SE_LOGIC_OK" "No inline if-chains >=5 in SKILL.md code blocks ($IF_CHAINS found)"
fmt_check "$SE_DIR_OK"   "scripts/ has scripts (n/a when SKILL.md has no deterministic logic)"
fmt_check "$SE_EXEC_OK"  "All scripts executable ($EXEC_COUNT/$SCRIPT_COUNT)"
echo "4. DESCRIPTION QUALITY   [$DQ_SCORE/35]"
fmt_check "$DQ_EXISTS"   "description field exists and is text"
fmt_check "$DQ_LEN_OK"   "description <=1024 chars ($DESC_LEN chars)"
fmt_check "$DQ_USE_WHEN" "description contains 'Use when'"
fmt_check "$DQ_NEG"      "description contains 'Do not use'"
fmt_check "$DQ_TR"       "description has >=3 quoted Turkish trigger phrases ($TR_COUNT found)"
fmt_check "$DQ_EN"       "description has English triggers (quoted phrase or >=5-word 'Use when' scenarios)"
fmt_check "$DQ_DOMAIN"   "description has domain nouns (tool/file type/rule ID//command/--flag)"
[[ -n "$PROCEDURE" ]] && \
  echo "  WARN: description may summarize the workflow (found '$PROCEDURE'); keep steps in the body"
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
  if [[ $SUGG_COUNT -le 3 ]]; then echo "  $SUGG_COUNT. $1"; fi
}

if [[ "$DQ_EXISTS" != true ]]; then
  print_suggestion "[PRIORITY: HIGH] Description missing or not text. Run validate-skill.sh for the parse error."
fi
if [[ $WB_SCORE -lt 20 ]]; then
  print_suggestion "[PRIORITY: HIGH] Word budget: $WORD_COUNT words. Move tables/lists/code examples to references/ files."
fi
if [[ "$DQ_USE_WHEN" != true ]]; then
  print_suggestion "[PRIORITY: HIGH] Description missing 'Use when' clause."
fi
if [[ "$DQ_TR" != true ]]; then
  print_suggestion "[PRIORITY: HIGH] Only $TR_COUNT quoted Turkish trigger(s). Add >=3, e.g. \"skill oluştur\", \"yeni skill yaz\"."
fi
if [[ "$DQ_NEG" != true ]]; then
  print_suggestion "[PRIORITY: HIGH] No negative trigger. Add: 'Do not use when <anti-scenario>'."
fi
if [[ "$DQ_EN" != true ]]; then
  print_suggestion "[PRIORITY: MEDIUM] No English triggers. Add quoted English phrases or concrete 'Use when' scenarios."
fi
if [[ "$DQ_DOMAIN" != true ]]; then
  print_suggestion "[PRIORITY: MEDIUM] No domain nouns. Name specific tools, file types, commands or rule IDs in description."
fi
if [[ "$PD_TABLE_OK" != true || "$PD_LIST_OK" != true || "$PD_CODE_OK" != true ]]; then
  print_suggestion "[PRIORITY: MEDIUM] Large tables, lists or code blocks in SKILL.md. Move them to references/ files."
fi
if [[ "$PD_REFS_OK" == false ]]; then
  print_suggestion "[PRIORITY: LOW] No reference files. Create references/<topic>.md if SKILL.md has lookup tables or examples."
fi
if [[ "$SE_LOGIC_OK" != true ]]; then
  print_suggestion "[PRIORITY: MEDIUM] Inline if-chains in SKILL.md. Move to scripts/<task>.sh."
fi
if [[ "$SE_EXEC_OK" == false ]]; then
  print_suggestion "[PRIORITY: MEDIUM] Scripts not executable. Run chmod +x on scripts/*."
fi

if [[ $SUGG_COUNT -eq 0 ]]; then
  echo "  None -- skill is fully compliant!"
fi

echo ""
