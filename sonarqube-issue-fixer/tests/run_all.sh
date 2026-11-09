#!/usr/bin/env bash
# Runs every automated test layer of sonarqube-issue-fixer. Usage: bash tests/run_all.sh
# Needs python3, uv, node/npm and git; PMD checks run only when PMD is cached (sonar-fix.py install-pmd).
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
SKILL=$(cd "$HERE/.." && pwd)
STATUS=0
step() { echo "== $1"; shift; "$@" || STATUS=1; }
PYTHONS=(python3)
[ -x /usr/bin/python3 ] && [ "$(command -v python3)" != /usr/bin/python3 ] && PYTHONS+=(/usr/bin/python3)
for P in "${PYTHONS[@]}"; do
  step "unit ($P)" "$P" "$HERE/unit/test_sonar_fix.py"
  step "e2e ($P)" env PY="$P" bash "$HERE/e2e/e2e.sh"
  step "matrix ($P)" env PY="$P" "$P" "$HERE/matrix/run_matrix.py"
done
if [ -x "${XDG_CACHE_HOME:-$HOME/.cache}/sonarqube-issue-fixer/pmd-bin-7.29.0/bin/pmd" ]; then
  step "e2e PMD" bash "$HERE/e2e/e2e_pmd.sh"
else
  echo "== e2e PMD skipped: PMD is not cached"
fi
VALIDATE="$SKILL/../create-skill/scripts/validate-skill.sh"
[ -f "$VALIDATE" ] && step "validate" bash "$VALIDATE" "$SKILL"
rm -rf "$SKILL/scripts/__pycache__"
echo "== RESULT: $([ $STATUS -eq 0 ] && echo PASS || echo FAIL)"
exit $STATUS
