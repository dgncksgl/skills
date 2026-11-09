#!/usr/bin/env bash
set -uo pipefail
PY=${PY:-python3}
HERE=$(cd "$(dirname "$0")" && pwd)
SP=${WORK:-${TMPDIR:-/tmp}/sonarqube-issue-fixer-e2e}
S=${SONARFIX_SCRIPT:-$(cd "$HERE/../../scripts" && pwd)/sonar-fix.py}
R=$SP/e2e-pmd/proj
rm -rf $SP/e2e-pmd; mkdir -p $R/src/main/java/a $R/src/test/java/a
cat > $R/src/main/java/a/Svc.java <<'JAVA'
package a;

import java.io.FileInputStream;
import java.io.IOException;
import java.util.List;
import java.util.Map;

public class Svc {
    public String run(List<String> list, boolean flag, boolean other) throws IOException {
        int temp = 5;
        String a = "five5";
        String b = "five5";
        String c = "five5";
        String d = "four";
        String e = "four";
        String f = "four";
        if (flag) {
            if (other) {
                a = b;
            }
        }
        try {
            Integer.parseInt(c);
        } catch (NumberFormatException ex) {
        }
        if (list.size() == 0) {
            throw new RuntimeException("empty");
        }
        FileInputStream in = new FileInputStream("x");
        in.read();
        return a + d + e + f;
    }

    private void neverCalled() {
        System.out.println("x");
    }
}
JAVA
sed -e 's/class Svc/class SvcTest/' $R/src/main/java/a/Svc.java > $R/src/test/java/a/SvcTest.java
cd $R && $PY $S inspect . --scope all --out $R.scope >/dev/null 2>&1 && $PY $S analyze . --files-from $R.scope --out $R.json >/dev/null 2>&1
main=$($PY -c "import json;print(' '.join(sorted({f['rule'] for f in json.load(open('$R.json')) if f['file'].startswith('src/main')})))")
test=$($PY -c "import json;print(' '.join(sorted({f['rule'] for f in json.load(open('$R.json')) if f['file'].startswith('src/test')})))")
F=0
[ "$main" = "S1066 S108 S112 S1128 S1144 S1155 S1192 S1481 S2095" ] || { echo "FAIL main: $main"; F=1; }
[ "$test" = "S1066 S108 S1128 S1144 S1481" ] || { echo "FAIL test: $test"; F=1; }
grep -q '"four"' $R.json && { echo "FAIL: 4-char literal reported"; F=1; }
printf 'package a;\nclass Broken { void f( { }\n' > $R/src/main/java/a/Broken.java
O=$(cd $R && $PY $S analyze . src/main/java/a/Svc.java src/main/java/a/Broken.java 2>&1)
grep -q ' S1481 ' <<<"$O" || { echo "FAIL: one unparsable file dropped all Java findings"; F=1; }
grep -q '^error=pmd could not parse .*Broken.java' <<<"$O" || { echo "FAIL: parse error not reported per file"; F=1; }
grep -q 'WARN' <<<"$O" && { echo "FAIL: PMD warnings leak into output"; F=1; }
printf 'package a;\nclass Marks {\n    int f() {\n        int kept = 1; // NOPMD\n        int hidden = 2; // NOSONAR\n        return 0;\n    }\n}\n' > $R/src/main/java/a/Marks.java
O=$(cd $R && $PY $S analyze . src/main/java/a/Marks.java 2>&1)
grep -q 'Marks.java:4 S1481' <<<"$O" || { echo "FAIL: // NOPMD hid a finding Sonar still reports"; F=1; }
grep -q 'Marks.java:5 ' <<<"$O" && { echo "FAIL: // NOSONAR line reported"; F=1; }
printf 'package a;\nclass Ann {\n    @SuppressWarnings("PMD")\n    int f() {\n        int temp = 1;\n        return 0;\n    }\n}\n' > $R/src/main/java/a/Ann.java
O=$(cd $R && $PY $S analyze . src/main/java/a/Ann.java 2>&1)
grep -q 'Ann.java:5 S1481' <<<"$O" || { echo "FAIL: @SuppressWarnings(\"PMD\") hid a finding Sonar still reports"; F=1; }
grep -q '^finding=src/main/java/a/Ann.java' <<<"$O" && (cd $R && git status >/dev/null 2>&1); grep -q 'SuppressWarnings("PMD")' $R/src/main/java/a/Ann.java || { echo "FAIL: source file was modified"; F=1; }
C="$SP/e2e-pmd/My Proj,x"; mkdir -p "$C/src/main/java/a"; printf 'package a;\nclass C {\n    int f() {\n        int temp = 1;\n        return 0;\n    }\n}\n' > "$C/src/main/java/a/C.java"
O=$(cd "$C" && $PY $S analyze . src/main/java/a/C.java 2>&1)
grep -q 'C.java:4 S1481' <<<"$O" || { echo "FAIL: PMD skipped a project whose path has a comma"; F=1; }
mkdir -p "$C/src/main/java/a,b"; printf 'package a;\nclass D {\n    int f() {\n        int temp = 1;\n        return 0;\n    }\n}\n' > "$C/src/main/java/a,b/D.java"
O=$(cd "$C" && $PY $S analyze . "src/main/java/a,b/D.java" 2>&1)
grep -q 'a,b/D.java:4 S1481' <<<"$O" || { echo "FAIL: PMD skipped a file whose folder has a comma"; F=1; }
printf 'package a;\nclass Names {\n    int f() {\n        int unusedLocal = 1;\n        int ignored = 2;\n        return 0;\n    }\n}\n' > $R/src/main/java/a/Names.java
O=$(cd $R && $PY $S analyze . src/main/java/a/Names.java 2>&1)
grep -q "Names.java:4 S1481 fix .*'unusedLocal'" <<<"$O" || { echo "FAIL: PMD skipped a local named unused* that SonarJava reports"; F=1; }
grep -q "Names.java:5 S1481 fix .*'ignored'" <<<"$O" || { echo "FAIL: PMD skipped a local named ignored* that SonarJava reports"; F=1; }
grep -q 'int unusedLocal = 1;' $R/src/main/java/a/Names.java || { echo "FAIL: source file was modified"; F=1; }
echo "PMD e2e fail=$F"; exit $F
