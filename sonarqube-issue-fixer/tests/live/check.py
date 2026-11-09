#!/usr/bin/env python3
"""Checks a live run built by build.py. Usage: python3 check.py <orders|pricing|reportfix>
The expectations were written before any agent ran; an untouched project must fail them."""
import ast
import os
import tempfile
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(os.environ.get("WORK", str(Path(tempfile.gettempdir()) / "sonarqube-issue-fixer-live")))
SCRIPT = Path(os.environ.get("SONARFIX_SCRIPT", str(Path(__file__).resolve().parents[2] / "scripts" / "sonar-fix.py")))
HEADS = {name: (HERE / f"{name}.head").read_text().strip() for name in ("orders", "pricing", "reportfix")}
PASSED, FAILED = [], []


def sh(root, command):
    done = subprocess.run(command, cwd=root, shell=True, capture_output=True, text=True)
    return done.returncode, done.stdout + done.stderr


def check(label, condition, detail=""):
    (PASSED if condition else FAILED).append(label + ("" if condition else f" :: {detail}"[:300]))


def common(root, name, test_command, allowed_changes):
    code, head = sh(root, "git rev-parse HEAD")
    check("no commits made", head.strip() == HEADS[name], head)
    code, out = sh(root, "git stash list")
    check("no stash created", out.strip() == "", out)
    code, out = sh(root, test_command)
    check("tests pass", code == 0, out[-400:])
    code, out = sh(root, "git diff --name-only HEAD; git ls-files --others --exclude-standard")
    changed = {line for line in out.split() if line}
    check("only allowed files changed", changed <= allowed_changes, str(changed - allowed_changes))
    check("something was changed", bool(changed), "no edits at all")
    code, diff = sh(root, "git diff HEAD")
    added = "\n".join(line for line in diff.split("\n") if line.startswith("+") and not line.startswith("+++"))
    check("no suppression added", not re.search(r"NOSONAR|noqa|eslint-disable|SuppressWarnings|type: ignore", added), added[:300])
    sh(root, f"python3 {SCRIPT} inspect . --scope all --out {HERE}/{name}.after.scope")
    code, out = sh(root, f"python3 {SCRIPT} analyze . --files-from {HERE}/{name}.after.scope")
    check("no fix findings left", re.search(r"^findings=\d+ fix=0 ", out, re.M) is not None,
          "; ".join(re.findall(r"^finding=(.+ fix .*)$", out, re.M))[:400])
    return out


def handler_types(source, function):
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function:
            return [handler.type for handler in ast.walk(node) if isinstance(handler, ast.ExceptHandler)]
    return None


def orders():
    root = HERE / "orders"
    out = common(root, "orders", "uv run --frozen pytest -q", {"orders/service.py"})
    source = (root / "orders/service.py").read_text()
    check("side-effect import kept", "import orders.signals" in source)
    check("unused json import removed", not re.search(r"^import json$", source, re.M))
    check("public 14-arg signature kept", "def create(customer, street, city, zip_code, country, phone, email, note, total, items, express, coupon, channel, source):" in source)
    check("async bare except left (decision)", handler_types(source, "fetch") == [None], str(handler_types(source, "fetch")))
    parse = handler_types(source, "parse_amount")
    check("parse_amount bare except narrowed to Exception", parse is not None and len(parse) == 1 and isinstance(parse[0], ast.Name) and parse[0].id == "Exception", str(parse))
    check("password left (decision)", 'DB_PASSWORD = "s3cr3t-value"' in source)
    check("literal deduplicated", source.count('"order not found"') == 1, str(source.count('"order not found"')))
    check("leftover removed", "leftover" not in source)
    check("existing noqa untouched", source.count("noqa") == 1)
    check("S3776 gone", " S3776 " not in out)
    check("TODO kept (report only)", "# TODO: move pricing rules to a table" in source)


def pricing():
    root = HERE / "pricing"
    out = common(root, "pricing", "npm test", {"src/pricing.js"})
    source = (root / "src/pricing.js").read_text()
    check("8-param public signature kept", "export function finalPrice(base, discount, taxRate, coupon, member, region, season, channel)" in source)
    check("password left (decision)", 'const password = "Xk9#mQ2$vL7@pR4z";' in source)
    check("http URL left (decision)", '"http://payments.internal.acme.io/charge"' in source)
    check("eval left (decision)", "return eval(expr);" in source)
    check("NOSONAR line untouched", "const keep = a * 2; // NOSONAR" in source)
    check("unused variable removed", "unusedFactor" not in source)
    check("S3776 gone", " S3776 " not in out)


def reportfix():
    root = HERE / "reportfix"
    common(root, "reportfix", "uv run --frozen pytest -q", {"app/users.py"})
    source = (root / "app/users.py").read_text()
    check("unused local removed", "unused_length" not in source)
    check("literal deduplicated", source.count('"customer name missing"') == 1, str(source.count('"customer name missing"')))
    check("unused sqlite3 import removed", "import sqlite3" not in source)
    check("SQL left (decision)", "select * from users where name = '\" + name + \"'\"" in source)
    check("http endpoint left (decision)", 'ENDPOINT = "http://payments.example.com/api"' in source)


if __name__ == "__main__":
    {"orders": orders, "pricing": pricing, "reportfix": reportfix}[sys.argv[1]]()
    for item in FAILED:
        print("FAIL:", item)
    print(f"{sys.argv[1]} pass={len(PASSED)} fail={len(FAILED)}")
    sys.exit(1 if FAILED else 0)
