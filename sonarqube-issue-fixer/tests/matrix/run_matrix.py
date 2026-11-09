#!/usr/bin/env python3
"""Broad matrix test for sonarqube-issue-fixer's sonar-fix.py.

Every expectation below was written before the run, from SKILL.md, the references and SonarQube's documented
behaviour. Each case builds a fresh project under WORK and checks inspect / analyze / import output.
Usage: python3 run_matrix.py [case-name ...]
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
from pathlib import Path

SCRIPT = Path(os.environ.get("SONARFIX_SCRIPT", str(Path(__file__).resolve().parents[2] / "scripts" / "sonar-fix.py")))
WORK = Path(os.environ.get("WORK", str(Path(tempfile.gettempdir()) / "sonarqube-issue-fixer-matrix")))
PY = os.environ.get("PY", sys.executable)
RESULTS = []
GIT_ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com"}


# ---------------------------------------------------------------- helpers

def write(root, files):
    for relative, text in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(text).lstrip("\n"), encoding="utf-8")


def project(name, files):
    root = WORK / name
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    write(root, files)
    return root


def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, env=GIT_ENV, capture_output=True, text=True, check=True).stdout


def commit_all(root, message):
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", message)


def run(root, *args, timeout=600):
    started = time.time()
    done = subprocess.run([PY, str(SCRIPT), *args], cwd=root, capture_output=True, text=True, timeout=timeout)
    return done.stdout + done.stderr, done.returncode, time.time() - started


def line_of(root, relative, snippet, occurrence=1):
    seen = 0
    for number, line in enumerate((root / relative).read_text(encoding="utf-8").split("\n"), 1):
        if snippet in line:
            seen += 1
            if seen == occurrence:
                return number
    raise AssertionError(f"{snippet!r} not in {relative}")


def findings(out):
    return {tuple(match.groups()) for match in re.finditer(r"^finding=(.+?):(\d+) (\S+) (\S+)", out, re.M)}


class Case:
    def __init__(self, name):
        self.name, self.passed, self.failed = name, 0, []

    def check(self, label, condition, detail=""):
        if condition:
            self.passed += 1
        else:
            self.failed.append(f"{label}" + (f" :: {detail}" if detail else ""))

    def has(self, out, relative, line, rule, action):
        self.check(f"has {relative}:{line} {rule} {action}", (relative, str(line), rule, action) in findings(out),
                   self.near(out, relative, rule))

    def lacks(self, out, relative, line, rule):
        hit = [item for item in findings(out) if item[0] == relative and item[1] == str(line) and item[2] == rule]
        self.check(f"lacks {relative}:{line} {rule}", not hit, str(hit))

    def lacks_rule(self, out, relative, rule):
        hit = [item for item in findings(out) if item[0] == relative and item[2] == rule]
        self.check(f"lacks {relative} {rule}", not hit, str(hit))

    def grep(self, label, out, pattern, present=True):
        found = re.search(pattern, out, re.M) is not None
        self.check(label, found == present, f"pattern {pattern!r} {'missing' if present else 'present'}")

    @staticmethod
    def near(out, relative, rule):
        return "; ".join(sorted(f"{f[0]}:{f[1]} {f[2]} {f[3]}" for f in findings(out) if f[0] == relative))[:400]


CASES = {}


def case(function):
    CASES[function.__name__] = function
    return function


def analyze_scope(root, scope_args=("--scope", "all")):
    scope_file = root.parent / f"{root.name}.scope"
    inspect_out, code, _ = run(root, "inspect", ".", *scope_args, "--out", str(scope_file))
    analyze_out, analyze_code, _ = run(root, "analyze", ".", "--files-from", str(scope_file))
    return inspect_out, analyze_out, analyze_code


# ---------------------------------------------------------------- Python

PRICING = '''
import os
import json


def price_label(price, currency):
    unused = currency.upper()
    if price is None:
        return "price not found"
    if price < 0:
        return "price not found"
    return f"{price}"


def describe(price):
    return "price not found" if price is None else str(price)


def risky():
    try:
        return int("x")
    except:
        return None


def many(a, b, c, d, e, f, g, h, i, j, k, l, m, n):
    return a


def grade(rows):
    out = []
    for r in rows:
        if r:
            for c in r:
                if c > 1:
                    if c % 2:
                        out.append(c)
                    elif c % 3:
                        out.append(-c)
                    else:
                        if c > 10:
                            out.append(0)
                elif c < 0 and c != -1 or c == -5:
                    continue
    return out


API_PASSWORD = "hunter2-secret-value"
# TODO: remove later
'''


@case
def p1_python_uv_feature_branch(c):
    root = project("p1", {
        "pyproject.toml": '[project]\nname = "shop"\nversion = "0.1"\nrequires-python = ">=3.11"\n\n[tool.pytest.ini_options]\ntestpaths = ["tests"]\n',
        "uv.lock": "version = 1\n",
        "app/__init__.py": "",
        "app/core.py": "def total(items):\n    return sum(items)\n",
        "tests/test_core.py": "from app.core import total\n\n\ndef test_total():\n    assert total([1, 2]) == 3\n",
    })
    git(root, "init", "-q", "-b", "main")
    commit_all(root, "base")
    git(root, "checkout", "-q", "-b", "feat/pricing")
    write(root, {"app/pricing.py": PRICING})
    commit_all(root, "pricing")
    write(root, {"app/core.py": "def total(items):\n    tmp = 1\n    return sum(items)\n", "app/new.py": "VALUE = 1\n"})
    inspect_out, out, code = analyze_scope(root, ())
    c.grep("module line uv pytest", inspect_out, r'^module=\. ecosystem=python .*test="uv run --frozen pytest -q')
    c.grep("branch facts", inspect_out, r"^branch=feat/pricing default_branch=main")
    c.grep("dirty count", inspect_out, r"^git=dirty:2")
    c.grep("changed scope 3 files", inspect_out, r"scope=changed .*scope_files=3 test_files=0")
    c.check("analyze exit 0", code == 0, out[-300:])
    f = "app/pricing.py"
    c.has(out, f, line_of(root, f, "import os"), "S1128", "check-api")
    c.has(out, f, line_of(root, f, "unused = "), "S1481", "fix")
    c.has(out, f, line_of(root, f, '"price not found"'), "S1192", "fix")
    c.has(out, f, line_of(root, f, "except:"), "S5754", "fix")
    c.lacks(out, f, line_of(root, f, "except:"), "BROAD-EXCEPT")
    c.has(out, f, line_of(root, f, "def many"), "S107", "check-api")
    c.has(out, f, line_of(root, f, "def grade"), "S3776", "fix")
    c.has(out, f, line_of(root, f, "API_PASSWORD"), "S2068", "ask")
    c.has(out, f, line_of(root, f, "TODO"), "S1135", "report")
    c.has(out, "app/core.py", 2, "S1481", "fix")
    c.grep("S1192 message lists lines once", out, r"S1192 fix .*3 times \(lines \d+, \d+, \d+\)")


@case
def p2_python_poetry_test_scope(c):
    literal = '"customer record missing"'
    root = project("p2", {
        "pyproject.toml": '[tool.poetry]\nname = "svc"\nversion = "0.1"\n\n[tool.poetry.dependencies]\npython = "^3.10"\n\n[tool.poetry.group.dev.dependencies]\npytest = "*"\n',
        "poetry.lock": "",
        "src/svc/__init__.py": "",
        "src/svc/messages.py": f"def a():\n    return {literal}\n\n\ndef b():\n    return {literal}\n\n\ndef c():\n    return {literal}\n",
        "tests/test_messages.py": f'PASSWORD = "test-pass-123"\n\n\ndef test_a():\n    assert {literal} == {literal} == {literal}\n',
        "tests/conftest.py": "def helper():\n    leftover = 1\n    return 2\n",
    })
    inspect_out, out, _ = analyze_scope(root)
    c.grep("poetry runner", inspect_out, r'test="poetry run pytest -q')
    c.grep("test files counted", inspect_out, r"scope_files=4 test_files=2")
    c.has(out, "src/svc/messages.py", 2, "S1192", "fix")
    c.lacks_rule(out, "tests/test_messages.py", "S1192")
    c.lacks_rule(out, "tests/test_messages.py", "S2068")
    c.has(out, "tests/conftest.py", 2, "S1481", "fix")


@case
def p3_plain_scripts_without_packaging(c):
    root = project("p3", {"tools/scripts/build.py": "def main():\n    return 1\n"})
    inspect_out, _, _ = run(root, "inspect", ".", "--scope", "all")
    c.grep("fallback python module", inspect_out, r'^module=\. ecosystem=python .*test="none \(no test files found\)"')
    root = project("p3b", {"app.py": "def f():\n    return 1\n", "tests/test_app.py": "from app import f\n\n\ndef test_f():\n    assert f() == 1\n"})
    inspect_out, _, _ = run(root, "inspect", ".", "--scope", "all")
    c.grep("fallback module finds pytest tests", inspect_out, r'^module=\. ecosystem=python .*test="\S*\s?\S* ?pytest -q')


S5754_CASES = '''
import sys
from sys import exit


async def awaiting(client):
    try:
        await client.get()
    except:
        pass


def plain():
    try:
        work()
    except:
        pass


def base():
    try:
        work()
    except BaseException:
        log()


def reraised():
    try:
        work()
    except:
        log()
        raise


def system_exit():
    try:
        work()
    except SystemExit:
        pass


def exits_itself():
    try:
        sys.exit(1)
    except:
        pass


def imported_exit():
    try:
        exit(2)
    except:
        pass


def nested_coroutine():
    try:
        async def cb():
            await x()
        register(cb)
    except:
        pass


def multiline():
    try:
        work()
    except (
        ValueError,
        BaseException,
    ):
        pass


def narrow():
    try:
        work()
    except Exception:
        log()
'''


@case
def p4_s5754_semantics(c):
    root = project("p4", {"m.py": S5754_CASES})
    out, _, _ = run(root, "analyze", ".", "m.py")
    def at(snippet, occurrence=1):
        return line_of(root, "m.py", snippet, occurrence)
    c.has(out, "m.py", at("except:", 1), "S5754", "ask")            # awaiting
    c.has(out, "m.py", at("except:", 2), "S5754", "fix")            # plain
    c.has(out, "m.py", at("except BaseException:"), "S5754", "fix")
    c.lacks(out, "m.py", at("except BaseException:"), "BROAD-EXCEPT")
    c.lacks(out, "m.py", at("except:", 3), "S5754")                 # re-raised
    c.has(out, "m.py", at("except SystemExit:"), "S5754", "ask")
    c.has(out, "m.py", at("except:", 4), "S5754", "ask")            # sys.exit in body
    c.has(out, "m.py", at("except:", 5), "S5754", "ask")            # exit() from sys
    c.has(out, "m.py", at("except:", 6), "S5754", "fix")            # nested coroutine only defined
    c.has(out, "m.py", at("except ("), "S5754", "fix")
    c.lacks(out, "m.py", at("BaseException,"), "BROAD-EXCEPT")
    c.has(out, "m.py", at("except Exception:"), "BROAD-EXCEPT", "ask")


@case
def p5_suppression_markers(c):
    root = project("p5", {
        "m.py": '''
            def f():
                a = 1  # noqa
                b = 2  # noqa: S1481
                c = 3  # noqa: E722
                d = "x y z w" + "x y z w" + "x y z w"  # NOSONAR(S1192)
                e = 5  # NOSONAR
                s = '# NOSONAR'
                return s


            def g():
                try:
                    work()
                except:  # noqa: E722
                    pass
        ''',
        "filelevel.py": "# flake8: noqa\nimport os\n",
    })
    out, _, _ = run(root, "analyze", ".", "m.py", "filelevel.py")
    f = "m.py"
    c.lacks(out, f, line_of(root, f, "a = 1"), "S1481")
    c.lacks(out, f, line_of(root, f, "b = 2"), "S1481")
    c.has(out, f, line_of(root, f, "c = 3"), "S1481", "fix")
    c.lacks(out, f, line_of(root, f, "d = "), "S1192")
    c.has(out, f, line_of(root, f, "d = "), "S1481", "fix")
    c.lacks(out, f, line_of(root, f, "e = 5"), "S1481")
    c.has(out, f, line_of(root, f, "except:"), "S5754", "fix")
    c.has(out, "filelevel.py", 2, "S1128", "check-api")


@case
def p6_generated_files(c):
    root = project("p6", {
        "api_pb2.py": "# Generated by the protocol buffer compiler.  DO NOT EDIT!\nx = 1\n",
        "client.py": "# Code generated by tool. DO NOT EDIT.\ndef f():\n    unused = 1\n",
        "app.py": "VALUE = 1\n",
    })
    inspect_out, _, _ = run(root, "inspect", ".", "--scope", "all")
    c.grep("only app.py in scope", inspect_out, r"scope_files=1 ")
    c.grep("generated counted", inspect_out, r"^excluded=.*generated:2")
    c.grep("generated files named", inspect_out, r"^generated_files=(api_pb2\.py,client\.py|client\.py,api_pb2\.py)$")
    out, _, _ = run(root, "analyze", ".", "client.py")
    c.has(out, "client.py", 3, "S1481", "fix")


@case
def p7_syntax_newer_than_declared(c):
    root = project("p7", {
        "pyproject.toml": '[project]\nname = "x"\nversion = "0"\nrequires-python = ">=3.9"\n',
        "a.py": "def f(v):\n    match v:\n        case 1:\n            return 1\n    return 0\n",
    })
    out, _, _ = run(root, "analyze", ".", "a.py")
    c.grep("SYNTAX reported for match on 3.9", out, r"^finding=a\.py:2 SYNTAX ")


# ---------------------------------------------------------------- Java / Kotlin

JAVA_SVC = '''
package a;

import java.io.FileInputStream;
import java.io.IOException;
import java.util.List;
import java.util.Map;

public class Svc {
    public String run(List<String> list, boolean flag, boolean other) throws IOException {
        int temp = 5;
        String a = "order not found";
        String b = "order not found";
        String c = "order not found";
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
        return a;
    }

    @SuppressWarnings("java:S1192")
    String hidden() {
        return "hidden literal" + "hidden literal" + "hidden literal";
    }

    @SuppressWarnings("unused")
    void unusedOk() {
        int quiet = 1;
    }

    void param(@SuppressWarnings("unused") int p) {
        int loud = 1;
    }

    void markers() {
        int sonarHidden = 1; // NOSONAR
        int pmdMarker = 2; // NOPMD
    }
}
'''


@case
def j1_maven_with_pmd(c):
    root = project("j1", {
        "pom.xml": "<project><properties><java.version>21</java.version></properties></project>",
        "src/main/java/a/Svc.java": JAVA_SVC,
        "src/test/java/a/SvcTest.java": 'package a;\n\nclass SvcTest {\n    void t() {\n        int spareInTest = 1;\n        String x = "test literal one";\n        String y = "test literal one";\n        String z = "test literal one";\n    }\n}\n',
    })
    inspect_out, out, _ = analyze_scope(root)
    c.grep("maven module", inspect_out, r'^module=\. ecosystem=maven language=java version=21')
    c.grep("pmd cached", inspect_out, r"pmd:cached")
    f = "src/main/java/a/Svc.java"
    c.has(out, f, line_of(root, f, "int temp"), "S1481", "fix")
    c.has(out, f, line_of(root, f, '"order not found"'), "S1192", "fix")
    c.has(out, f, line_of(root, f, "if (other)"), "S1066", "fix")  # Sonar and PMD flag the inner if
    c.has(out, f, line_of(root, f, "catch (NumberFormatException"), "S108", "fix")
    c.has(out, f, line_of(root, f, "list.size() == 0"), "S1155", "fix")
    c.has(out, f, line_of(root, f, "import java.util.Map"), "S1128", "check-api")
    c.lacks(out, f, line_of(root, f, '"hidden literal"'), "S1192")
    c.lacks(out, f, line_of(root, f, "int quiet"), "S1481")
    c.has(out, f, line_of(root, f, "int loud"), "S1481", "fix")
    c.lacks(out, f, line_of(root, f, "sonarHidden"), "S1481")
    c.has(out, f, line_of(root, f, "pmdMarker"), "S1481", "fix")
    t = "src/test/java/a/SvcTest.java"
    c.has(out, t, line_of(root, t, "spareInTest"), "S1481", "fix")
    c.lacks_rule(out, t, "S1192")


@case
def j2_maven_multi_module_test_inclusions(c):
    root = project("j2", {
        "pom.xml": "<project><modules><module>mod</module></modules><properties><sonar.test.inclusions>src/test/**/*Test.java</sonar.test.inclusions></properties></project>",
        "mod/pom.xml": "<project/>",
        "mod/src/main/java/a/A.java": "package a;\nclass A {}\n",
        "mod/src/test/java/a/ATest.java": "package a;\nclass ATest {}\n",
        "mod/src/test/java/a/Helper.java": "package a;\nclass Helper {}\n",
    })
    inspect_out, _, _ = run(root, "inspect", ".", "--scope", "all")
    c.grep("module test file kept as test", inspect_out, r"scope_files=2 test_files=1")
    c.grep("helper excluded by inclusions", inspect_out, r"^excluded=.*outside-sonar\.test\.inclusions:1")


@case
def k1_gradle_kotlin(c):
    root = project("k1", {
        "settings.gradle.kts": 'rootProject.name = "k"\n',
        "build.gradle.kts": 'plugins { kotlin("jvm") version "2.1.0" }\n',
        "src/main/kotlin/K.kt": '''
            class K {
                @Suppress("kotlin:S107")
                fun quiet(a: Int, b: Int, c: Int, d: Int, e: Int, f: Int, g: Int, h: Int): Int = a

                fun loud(a: Int, b: Int, c: Int, d: Int, e: Int, f: Int, g: Int, h: Int): Int = a
            }
        ''',
    })
    inspect_out, out, _ = analyze_scope(root)
    c.grep("gradle module", inspect_out, r"^module=\. ecosystem=gradle ")
    f = "src/main/kotlin/K.kt"
    c.lacks(out, f, line_of(root, f, "fun quiet"), "S107")
    c.has(out, f, line_of(root, f, "fun loud"), "S107", "check-api")
    c.grep("kotlin partial review line", out, r"^review=kotlin")


# ---------------------------------------------------------------- JavaScript / TypeScript

PRICE_TS = '''
export function label(price: number, previous: number): string {
  const unused = price * 2;
  if (price > previous) {
    return "price is not available";
  }
  if (price === previous) {
    return "price is not available";
  }
  return "price is not available";
}

export function grade(rows: number[][]): number[] {
  const out: number[] = [];
  for (const r of rows) {
    if (r) {
      for (const c of r) {
        if (c > 1) {
          if (c % 2) {
            out.push(c);
          } else if (c % 3) {
            out.push(-c);
          } else {
            if (c > 10) {
              out.push(0);
            }
          }
        } else if ((c < 0 && c !== -1) || c === -5) {
          continue;
        }
      }
    }
  }
  return out;
}
'''


@case
def t1_typescript_npm(c):
    root = project("t1", {
        "package.json": '{"name": "web", "scripts": {"test": "vitest run"}, "devDependencies": {"typescript": "5.6.3"}}',
        "package-lock.json": "{}",
        "tsconfig.json": '{"compilerOptions": {"strict": true}}',
        "src/price.ts": PRICE_TS,
        "src/price.test.ts": 'import { label } from "./price";\nconst x = label(1, 2);\n',
        "node_modules/lib/index.js": "var a = 1;\n",
        "dist/out.js": "var b = 1;\n",
    })
    inspect_out, out, code = analyze_scope(root)
    c.grep("npm module typescript", inspect_out, r'^module=\. ecosystem=npm language=typescript version=5\.6 .*test="npm test')
    c.grep("build output excluded", inspect_out, r"^excluded=.*dependency-or-build-dir:\d")
    c.grep("two scope files, one test", inspect_out, r"scope_files=2 test_files=1")
    c.check("analyze exit 0", code == 0, out[-400:])
    f = "src/price.ts"
    c.has(out, f, line_of(root, f, "const unused"), "S1481", "fix")
    c.lacks_rule(out, f, "S1192")  # not in JS Sonar way
    c.has(out, f, line_of(root, f, "export function grade"), "S3776", "fix")


@case
def t2_bun_and_pnpm(c):
    root = project("t2", {"package.json": '{"name": "b", "scripts": {"test": "vitest run"}}', "bun.lock": "", "index.js": "export const a = 1;\n"})
    inspect_out, _, _ = run(root, "inspect", ".", "--scope", "all")
    c.grep("bun runs the test script", inspect_out, r'ecosystem=bun .*test="bun run test')
    root = project("t2b", {
        "package.json": '{"name": "mono", "private": true, "scripts": {"test": "pnpm -r test"}}',
        "pnpm-workspace.yaml": "packages:\n  - packages/*\n",
        "pnpm-lock.yaml": "",
        "packages/a/package.json": '{"name": "a", "scripts": {"test": "vitest"}}',
        "packages/a/index.js": "export const a = 1;\n",
    })
    inspect_out, _, _ = run(root, "inspect", ".", "--scope", "all")
    c.check("pnpm workspace is one module", len(re.findall(r"^module=", inspect_out, re.M)) == 1, inspect_out[:600])
    c.grep("pnpm test command", inspect_out, r'ecosystem=pnpm .*test="pnpm test')


# ---------------------------------------------------------------- Sonar configuration

@case
def s1_sonar_properties(c):
    root = project("s1", {
        "sonar-project.properties": "sonar.projectKey=demo\nsonar.sources=src\nsonar.tests=tests\nsonar.exclusions=src/legacy/**\n",
        "src/app.py": "VALUE = 1\n",
        "src/legacy/old.py": "VALUE = 2\n",
        "tests/test_app.py": "def test_a():\n    assert True\n",
        "scripts/tool.py": "VALUE = 3\n",
    })
    inspect_out, _, _ = run(root, "inspect", ".", "--scope", "all")
    c.grep("project key", inspect_out, r"project_key=demo")
    c.grep("sources+tests in scope", inspect_out, r"scope_files=2 test_files=1")
    c.grep("exclusion counted", inspect_out, r"sonar\.exclusions:1")
    c.grep("outside sources counted", inspect_out, r"outside-sonar\.sources:1")
    root = project("s2", {
        "sonar-project.properties": "sonar.projectKey=demo2\nsonar.sources=.\n",
        "app.py": "VALUE = 1\n",
        "tests/test_app.py": "def test_a():\n    assert True\n",
        "examples/java-client/pom.xml": "<project/>",
    })
    inspect_out, _, _ = run(root, "inspect", ".", "--scope", "all")
    c.grep("no sonar.tests: every file is main", inspect_out, r"scope_files=2 test_files=0")


# ---------------------------------------------------------------- git states

@case
def g1_git_states(c):
    root = project("g1", {"a.py": "VALUE = 1\n"})
    out, code, _ = run(root, "inspect", ".")
    c.grep("no git: error for changed scope", out, r"^error=")
    git(root, "init", "-q", "-b", "feature")
    out, _, _ = run(root, "inspect", ".", "--scope", "all")
    c.grep("unborn branch named", out, r"^branch=feature ")
    commit_all(root, "one")
    write(root, {"b.py": "VALUE = 2\n"})
    commit_all(root, "two")
    first = git(root, "rev-list", "--max-parents=0", "HEAD").strip()
    git(root, "branch", "-q", "base", first)
    git(root, "checkout", "-q", "--detach", "HEAD")
    out, _, _ = run(root, "inspect", ".", "--base", "base")
    c.grep("detached HEAD with --base finds the branch commit", out, r"scope_files=1 ")
    git(root, "checkout", "-q", "feature")
    write(root, {"bin/new_tool.py": "VALUE = 3\n"})
    out, _, _ = run(root, "inspect", ".", "--base", "base")
    c.grep("new untracked bin/ folder guessed as build output", out, r"scope_files=1 .*\n.*\nexcluded=dependency-or-build-dir:1")


# ---------------------------------------------------------------- import

@case
def i1_import_report(c):
    root = project("i1", {
        "app/db.py": "def q(c, name):\n    return c.execute('select * from t where n = ' + name)\n",
        "app/msg.py": 'A = "x"\n',
        "app/worker.py": "async def run(c):\n    try:\n        await c.get()\n    except:\n        pass\n",
    })
    issues = {"total": 6, "p": 1, "ps": 100, "issues": [
        {"key": "1", "rule": "python:S1192", "component": "k:app/msg.py", "line": 1, "message": "dup", "type": "CODE_SMELL", "project": "k"},
        {"key": "2", "rule": "python:S2077", "component": "k:app/db.py", "line": 2, "message": "sql", "project": "k", "type": "SECURITY_HOTSPOT",
         "impacts": [{"softwareQuality": "SECURITY", "severity": "HIGH"}]},
        {"key": "3", "rule": "python:S1135", "component": "k:app/msg.py", "line": 1, "message": "todo", "project": "k", "type": "CODE_SMELL"},
        {"key": "4", "rule": "python:S5754", "component": "k:app/worker.py", "line": 4, "message": "bare", "project": "k", "type": "CODE_SMELL"},
        {"key": "5", "rule": "python:S1192", "component": "k:app/gone.py", "line": 3, "message": "dup", "type": "CODE_SMELL", "project": "k"},
        {"key": "6", "rule": "common-python:DuplicatedBlocks", "component": "k", "message": "proj", "project": "k", "type": "CODE_SMELL"},
    ], "components": [{"key": "k:app/msg.py", "path": "app/msg.py"}, {"key": "k:app/db.py", "path": "app/db.py"},
                      {"key": "k:app/worker.py", "path": "app/worker.py"}, {"key": "k:app/gone.py", "path": "app/gone.py"}]}
    (WORK / "i1-issues.json").write_text(json.dumps(issues))
    out, code, _ = run(root, "import", ".", str(WORK / "i1-issues.json"))
    c.check("import exit 0", code == 0, out[-300:])
    c.has(out, "app/msg.py", 1, "S1192", "fix")
    c.has(out, "app/db.py", 2, "S2077", "ask")
    c.has(out, "app/msg.py", 1, "S1135", "report")
    c.has(out, "app/worker.py", 4, "S5754", "ask")
    c.grep("missing file note", out, r"^note=1 files from the report do not exist.*app/gone\.py$")
    c.grep("project-level issue kept", out, r"^finding=\(project\)")


# ---------------------------------------------------------------- paths, other languages, scale

@case
def x1_odd_paths(c):
    root = project("x1/My Proj ü,1", {"süper modül/a b.py": "def f():\n    unused = 1\n", "pom.xml": "<project/>",
                                      "src/main/java/a,b/D.java": "package a;\nclass D {\n    int f() {\n        int temp = 1;\n        return 0;\n    }\n}\n"})
    inspect_out, out, code = analyze_scope(root)
    c.check("analyze exit 0", code == 0, out[-400:])
    c.has(out, "süper modül/a b.py", 2, "S1481", "fix")
    c.has(out, "src/main/java/a,b/D.java", 4, "S1481", "fix")


@case
def l1_lizard_languages(c):
    params = ", ".join(f"p{i} int" for i in range(8))
    root = project("l1", {
        "go.mod": "module x\n\ngo 1.22\n",
        "g.go": f"package x\n\nfunc F({params}) int {{\n\treturn p0\n}}\n",
        "C.cs": "class C {\n    int F(int a, int b, int c, int d, int e, int f, int g, int h) { return a; }\n}\n",
    })
    out, _, _ = run(root, "analyze", ".", "g.go", "C.cs")
    c.has(out, "g.go", 3, "S107", "check-api")
    c.has(out, "C.cs", 2, "S107", "check-api")
    c.grep("go review line", out, r"^review=go")
    c.grep("csharp review line", out, r"^review=csharp")


@case
def r1_scale(c):
    files = {f"pkg{i // 50}/m{i}.py": f'def f{i}(x):\n    unused = x\n    return "same text here" + "same text here" + "same text here"\n' for i in range(300)}
    files["pyproject.toml"] = '[project]\nname = "big"\nversion = "0"\nrequires-python = ">=3.10"\n'
    root = project("r1", files)
    scope_file = WORK / "r1.scope"
    run(root, "inspect", ".", "--scope", "all", "--out", str(scope_file))
    out, code, seconds = run(root, "analyze", ".", "--files-from", str(scope_file))
    c.check(f"300 files analyzed in {seconds:.0f}s (< 120s)", seconds < 120)
    c.grep("all findings present", out, r"^findings=600 ")  # S1481 + one S1192 per file


@case
def z1_self_analysis(c):
    out, _, _ = run(SCRIPT.parent.parent, "analyze", ".", "scripts/sonar-fix.py")
    c.grep("skill's own script is clean", out, r"^findings=0 ")


def main():
    selected = sys.argv[1:] or list(CASES)
    WORK.mkdir(parents=True, exist_ok=True)
    total_pass = total_fail = 0
    for name in selected:
        current = Case(name)
        try:
            CASES[name](current)
        except Exception as error:  # a crash in a case is a failure of that case, the rest still run
            current.failed.append(f"crashed: {error!r}")
        total_pass += current.passed
        total_fail += len(current.failed)
        status = "PASS" if not current.failed else "FAIL"
        print(f"{status} {name}: {current.passed} ok, {len(current.failed)} failed")
        for failure in current.failed:
            print(f"    - {failure}")
    print(f"MATRIX pass={total_pass} fail={total_fail}")
    return 0 if total_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
