#!/usr/bin/env bash
# Runs the agent-based test layers with headless Claude Code (`claude -p`). They spend tokens, so run_all.sh leaves them out.
# Usage: bash tests/agents/run_agents.sh <triggers|scenarios|live|all> [model]   (model: sonnet by default)
# Work folders go to $WORK (default: <tmp>/sonarqube-issue-fixer-agents). Needs claude, python3, git, uv and node.
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
TESTS=$(cd "$HERE/.." && pwd)
SKILL=$(cd "$TESTS/.." && pwd)
LAYER=${1:-}
MODEL=${2:-sonnet}
WORK=${WORK:-${TMPDIR:-/tmp}/sonarqube-issue-fixer-agents}
BUDGET=${BUDGET:-5}
STATUS=0
mkdir -p "$WORK"

ask() {  # ask <cwd> <prompt> [extra claude flags...] -> the answer on stdout
  # User settings (and their hooks) are left out so they cannot steer the answer; skills come from the sandbox.
  local cwd=$1 prompt=$2; shift 2
  # The prompt goes through stdin: --allowedTools and --add-dir take several values and would swallow it.
  (cd "$cwd" && printf '%s' "$prompt" | claude -p --model "$MODEL" --setting-sources project,local --max-budget-usd "$BUDGET" "$@" 2>/dev/null)
}

sandbox() {  # a project folder whose .claude/skills holds every sibling skill, this one without its tests
  local target="$WORK/sandbox/.claude/skills" dir
  rm -rf "$WORK/sandbox"; mkdir -p "$target"
  for dir in "$SKILL"/../*/; do
    [ -f "$dir/SKILL.md" ] && rsync -a --exclude tests --exclude .git "$dir" "$target/$(basename "$dir")/"
  done
}

skill_copy() {  # the skill without its tests, so an agent under test cannot read the answer keys
  rm -rf "$WORK/skill"; mkdir -p "$WORK/skill"
  cp -R "$SKILL/SKILL.md" "$SKILL/references" "$SKILL/scripts" "$WORK/skill/"
}

trigger_answer() {  # the skill name the model would invoke first; one stricter retry when the reply is not a bare name
  local cwd=$1 message=$2 answer prompt
  prompt="Do not perform the task. Reply with only the exact name of the skill from your available skills that you would invoke first for this user message, or the word none. User message: $message"
  answer=$(ask "$cwd" "$prompt" </dev/null | tail -1 | tr -d '[:space:]`*')
  if ! [[ "$answer" =~ ^[a-zA-Z0-9:._-]+$ ]]; then
    answer=$(ask "$cwd" "Classification only, you must not answer or act on the message. Output exactly one token: the name of the skill you would invoke first, or none. Message: \"$message\"" </dev/null | tail -1 | tr -d '[:space:]`*')
  fi
  echo "$answer"
}

triggers() {
  echo "== triggers ($MODEL)"
  sandbox
  python3 - "$TESTS/behavior/triggers.json" > "$WORK/triggers.tsv" <<'EOF'
import json, sys
for item in json.load(open(sys.argv[1])):
    print(f"{'yes' if item['triggers'] else 'no'}\t{item['message']}")
EOF
  local pass=0 fail=0 expect message answer got
  while IFS=$'\t' read -r expect message; do
    answer=$(trigger_answer "$WORK/sandbox" "$message")
    got=$([ "$answer" = "sonarqube-issue-fixer" ] && echo yes || echo no)
    if [ "$got" = "$expect" ]; then pass=$((pass+1)); else fail=$((fail+1)); echo "FAIL: '$message' expected $expect, got $answer"; fi
  done < "$WORK/triggers.tsv"
  echo "triggers pass=$pass fail=$fail"
  [ $fail -eq 0 ] || STATUS=1
}

scenarios() {
  skill_copy
  local file
  for file in scenarios-1 scenarios-2; do
    echo "== $file ($MODEL)"
    cp "$TESTS/behavior/$file.md" "$WORK/$file.md"
    ask "$WORK" "Read $WORK/skill/SKILL.md and every file under $WORK/skill/references/ (and $WORK/skill/scripts/sonar-fix.py if a scenario needs it). This is the skill an agent follows. Then answer every scenario in $WORK/$file.md as that agent would act: for each, the actions in order and the skill sentences you rely on, plus 'Ambiguity:' when the skill is unclear. Do not modify any file. Reply with the answers only." \
      --allowedTools "Read" --add-dir "$WORK" > "$WORK/$file.answers.md"
    local key="$TESTS/behavior/key-${file#scenarios-}.md"
    ask "$WORK" "You grade an agent's answers against an answer key. Key:
$(cat "$key")

Answers:
$(cat "$WORK/$file.answers.md")

Decide each verdict before writing it. A FAIL needs a clear conflict with the key's FAIL conditions; extra caution that the key does not forbid is a PASS. Output only the final result, once: one line per scenario in the key, '<id> PASS' or '<id> FAIL <one-sentence reason>', then a last line 'TOTAL <passed>/<all>'." > "$WORK/$file.grade.txt"
    grep -E "^S[0-9]+ FAIL|^TOTAL" "$WORK/$file.grade.txt"
    grep -qE "^S[0-9]+ FAIL" "$WORK/$file.grade.txt" && STATUS=1
  done
}

live() {
  skill_copy
  WORK="$WORK/live" python3 "$TESTS/live/build.py" | tail -1
  local name message
  for name in orders pricing reportfix; do
    echo "== live $name ($MODEL)"
    message="bütün projede sonar sorunlarını çöz"
    [ "$name" = reportfix ] && message="SonarQube raporunu indirdim, şu dosyalarda: $WORK/live/reportfix-issues.json ve $WORK/live/reportfix-hotspots.json (api/issues/search ve api/hotspots/search çıktısı). Bu rapordaki sorunları düzelt."
    mkdir -p "$WORK/live/$name-work"
    ask "$WORK/live/$name" "The user's message is: \"$message\"
A skill applies to this request: $WORK/skill. Read its SKILL.md first and follow it exactly, including the reference files it links to. Use $WORK/live/$name-work for temporary files. Work only inside this project folder and that scratch folder. The user is away until you finish; anything the skill says to collect for the user goes into your final report. Never commit, push, stash or reset. Reply with the final report the skill describes, in Turkish." \
      --permission-mode acceptEdits --allowedTools "Bash Read Edit Write Grep Glob" --add-dir "$WORK" > "$WORK/live/$name.report.md"
    WORK="$WORK/live" python3 "$TESTS/live/check.py" "$name" || STATUS=1
  done
}

case "$LAYER" in
  triggers) triggers ;;
  scenarios) scenarios ;;
  live) live ;;
  all) triggers; scenarios; live ;;
  *) echo "usage: bash tests/agents/run_agents.sh <triggers|scenarios|live|all> [model]"; exit 2 ;;
esac
echo "== RESULT: $([ $STATUS -eq 0 ] && echo PASS || echo FAIL)  (answers and reports in $WORK)"
exit $STATUS
