#!/usr/bin/env python3
"""Builds the three live-run projects (fresh git repos) under $WORK (default: <tmp>/sonarqube-issue-fixer-live).
Usage: python3 build.py   Needs git, uv and node."""
import json
import os
import tempfile
import shutil
import subprocess
import textwrap
from pathlib import Path

HERE = Path(os.environ.get("WORK", str(Path(tempfile.gettempdir()) / "sonarqube-issue-fixer-live")))
ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com",
       "PATH": "/usr/bin:/bin:/opt/homebrew/bin:" + str(Path.home() / ".local/bin")}


def make(name, files):
    root = HERE / name
    if root.exists():
        shutil.rmtree(root)
    for relative, text in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(text).lstrip("\n"), encoding="utf-8")
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=root, check=True)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=root, check=True, env=ENV)
    return root


ORDERS_SERVICE = '''
import json
import orders.signals

from orders.models import Order

NOT_USED_MARKER = 1  # noqa


def lookup(store, key):
    if key not in store:
        return "order not found"
    value = store[key]
    if value is None:
        return "order not found"
    return value


def describe(store, key):
    leftover = key.strip()
    return "order not found" if key not in store else str(store[key])


def classify(order):
    if order.total < 0:
        return "invalid"
    if order.items:
        for item in order.items:
            if item > 100:
                if order.express:
                    return "priority-heavy"
                else:
                    if order.total > 1000:
                        return "heavy-large"
                    else:
                        return "heavy"
            elif item < 0:
                if order.express or order.total > 50 and order.total < 60:
                    return "odd-express"
                return "odd"
    else:
        if order.express:
            return "empty-express"
    return "normal"


def create(customer, street, city, zip_code, country, phone, email, note, total, items, express, coupon, channel, source):
    return Order(total=total, items=items, express=express)


async def fetch(client):
    try:
        return await client.get()
    except:
        return None


def parse_amount(value):
    try:
        return int(value)
    except:
        return 0


DB_PASSWORD = "s3cr3t-value"
# TODO: move pricing rules to a table
'''

ORDERS_TESTS = '''
import asyncio

import pytest

from orders import Order
from orders.registry import REGISTRY
from orders.service import classify, create, describe, fetch, lookup, parse_amount
from orders.api import build


CASES = [
    (Order(total=-1, items=[], express=False), "invalid"),
    (Order(total=10, items=[150], express=True), "priority-heavy"),
    (Order(total=2000, items=[150], express=False), "heavy-large"),
    (Order(total=10, items=[150], express=False), "heavy"),
    (Order(total=55, items=[-5], express=False), "odd-express"),
    (Order(total=10, items=[-5], express=True), "odd-express"),
    (Order(total=10, items=[-5], express=False), "odd"),
    (Order(total=10, items=[], express=True), "empty-express"),
    (Order(total=10, items=[], express=False), "normal"),
    (Order(total=10, items=[5, 6], express=False), "normal"),
]


@pytest.mark.parametrize("order,expected", CASES)
def test_classify(order, expected):
    assert classify(order) == expected


def test_lookup_and_describe():
    store = {"a": 1, "b": None}
    assert lookup(store, "a") == 1
    assert lookup(store, "b") == "order not found"
    assert lookup(store, "c") == "order not found"
    assert describe(store, " a ") == "order not found"
    assert describe(store, "a") == "1"


def test_parse_amount():
    assert parse_amount("12") == 12
    assert parse_amount("x") == 0


class Broken:
    async def get(self):
        raise asyncio.CancelledError()


class Works:
    async def get(self):
        return 5


def test_fetch_swallows_everything():
    assert asyncio.run(fetch(Works())) == 5
    assert asyncio.run(fetch(Broken())) is None


def test_create_and_api():
    order = create("c", "s", "x", "1", "TR", "p", "e", "n", 3, [1], False, None, "web", "ads")
    assert order.total == 3
    assert build().total == 7


def test_signals_registered_on_import():
    import orders.service  # noqa: F401
    assert "orders" in REGISTRY
'''


def build_orders():
    make("orders", {
        "pyproject.toml": '''
            [project]
            name = "orders"
            version = "0.1.0"
            requires-python = ">=3.11"
            dependencies = []

            [dependency-groups]
            dev = ["pytest>=8"]

            [build-system]
            requires = ["hatchling"]
            build-backend = "hatchling.build"
        ''',
        "orders/__init__.py": "from orders.models import Order\n",
        "orders/models.py": '''
            from dataclasses import dataclass, field


            @dataclass
            class Order:
                total: int = 0
                items: list = field(default_factory=list)
                express: bool = False
        ''',
        "orders/registry.py": "REGISTRY = []\n",
        "orders/signals.py": "from orders.registry import REGISTRY\n\nREGISTRY.append(\"orders\")\n",
        "orders/service.py": ORDERS_SERVICE,
        "orders/api.py": '''
            from orders.service import create


            def build():
                return create("c", "s", "x", "1", "TR", "p", "e", "n", 7, [], False, None, "web", "ads")
        ''',
        "orders/proto/orders_pb2.py": "# Generated by the protocol buffer compiler.  DO NOT EDIT!\n# source: orders.proto\n\n\ndef unused_helper():\n    value = 1\n    return None\n",
        "tests/test_service.py": ORDERS_TESTS,
        ".gitignore": ".venv/\n__pycache__/\n.pytest_cache/\n",
    })
    subprocess.run(["uv", "lock", "-q"], cwd=HERE / "orders", check=True)
    subprocess.run(["git", "add", "-A"], cwd=HERE / "orders", check=True)
    subprocess.run(["git", "commit", "-q", "-m", "lock"], cwd=HERE / "orders", check=True, env=ENV)


PRICING_JS = '''
export function finalPrice(base, discount, taxRate, coupon, member, region, season, channel) {
  let result = base;
  const unusedFactor = 3;
  if (discount > 0) {
    if (member) {
      if (season === "summer") {
        result = base - discount * 2;
      } else if (season === "winter" && region === "north") {
        result = base - discount * 3;
      } else {
        result = base - discount;
      }
    } else if (coupon) {
      if (coupon.startsWith("X") || coupon.startsWith("Y") && channel === "web") {
        result = base - discount / 2;
      }
    }
  }
  if (channel === "web") {
    for (const ch of region) {
      if (ch === "x") {
        result -= 1;
      }
    }
  }
  result = result * (1 + taxRate);
  return Math.round(result * 100) / 100;
}

export function label(price) {
  let text = "unknown";
  text = price > 100 ? "expensive" : "cheap";
  return text;
}

const password = "Xk9#mQ2$vL7@pR4z";

export const PAYMENT_URL = "http://payments.internal.acme.io/charge";

export function evaluate(expr) {
  return eval(expr);
}

export function connect(user) {
  return { user, password };
}

export function legacy(a) {
  const keep = a * 2; // NOSONAR
  return a;
}
'''

PRICING_TEST = '''
import { test } from "node:test";
import assert from "node:assert/strict";
import { finalPrice, label, connect, legacy, evaluate, PAYMENT_URL } from "../src/pricing.js";
import { run } from "../src/cli.js";

test("final price paths", () => {
  assert.equal(finalPrice(100, 10, 0, null, true, "south", "summer", "web"), 80);
  assert.equal(finalPrice(100, 10, 0, null, true, "north", "winter", "web"), 70);
  assert.equal(finalPrice(100, 10, 0, null, true, "south", "winter", "web"), 90);
  assert.equal(finalPrice(100, 10, 0, "X1", false, "south", "spring", "app"), 95);
  assert.equal(finalPrice(100, 10, 0, "Y1", false, "south", "spring", "web"), 95);
  assert.equal(finalPrice(100, 10, 0, "Y1", false, "south", "spring", "app"), 100);
  assert.equal(finalPrice(100, 0, 0.18, null, false, "south", "spring", "app"), 118);
  assert.equal(finalPrice(100, 10, 0, "Z", false, "south", "spring", "web"), 100);
});

test("label", () => {
  assert.equal(label(150), "expensive");
  assert.equal(label(50), "cheap");
});

test("connect and legacy", () => {
  assert.deepEqual(connect("u"), { user: "u", password: "Xk9#mQ2$vL7@pR4z" });
  assert.equal(evaluate("1+2"), 3);
  assert.ok(PAYMENT_URL.startsWith("http://"));
  assert.equal(legacy(3), 3);
  assert.equal(run(), 80);
});
'''


def build_pricing():
    make("pricing", {
        "package.json": '{\n  "name": "pricing",\n  "version": "1.0.0",\n  "type": "module",\n  "scripts": {\n    "test": "node --test"\n  }\n}\n',
        "package-lock.json": '{\n  "name": "pricing",\n  "version": "1.0.0",\n  "lockfileVersion": 3,\n  "requires": true,\n  "packages": {"": {"name": "pricing", "version": "1.0.0"}}\n}\n',
        "src/pricing.js": PRICING_JS,
        "src/cli.js": 'import { finalPrice } from "./pricing.js";\n\nexport function run() {\n  return finalPrice(100, 10, 0, null, true, "south", "summer", "web");\n}\n',
        "test/pricing.test.js": PRICING_TEST,
    })


REPORT_SERVICE = '''
import sqlite3

GREETING_PREFIX = "Hello"


def greet(name):
    unused_length = len(name or "")
    if not name:
        return "customer name missing"
    if name.strip() == "":
        return "customer name missing"
    return GREETING_PREFIX + " " + name


def farewell(name):
    return "customer name missing" if not name else "Bye " + name


def find(conn, name):
    return conn.execute("select * from users where name = '" + name + "'").fetchall()


ENDPOINT = "http://payments.example.com/api"
'''


def build_report():
    root = make("reportfix", {
        "pyproject.toml": '[project]\nname = "reportfix"\nversion = "0.1.0"\nrequires-python = ">=3.11"\ndependencies = []\n\n[dependency-groups]\ndev = ["pytest>=8"]\n\n[tool.pytest.ini_options]\npythonpath = ["."]\n',
        "app/__init__.py": "",
        "app/users.py": REPORT_SERVICE,
        "tests/test_users.py": '''
            import sqlite3

            from app.users import farewell, find, greet


            def test_greet():
                assert greet("Ann") == "Hello Ann"
                assert greet("") == "customer name missing"
                assert greet("  ") == "customer name missing"
                assert greet(None) == "customer name missing"


            def test_farewell():
                assert farewell("") == "customer name missing"
                assert farewell("Bo") == "Bye Bo"


            def test_find():
                conn = sqlite3.connect(":memory:")
                conn.execute("create table users (name text)")
                conn.execute("insert into users values ('Ann')")
                assert find(conn, "Ann") == [("Ann",)]
        ''',
        ".gitignore": ".venv/\n__pycache__/\n.pytest_cache/\n",
    })
    subprocess.run(["uv", "lock", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "lock"], cwd=root, check=True, env=ENV)
    users = (root / "app/users.py").read_text().split("\n")
    def line(snippet):
        return next(number for number, text in enumerate(users, 1) if snippet in text)
    comp = "acme:reportfix:app/users.py"
    issues = {"total": 4, "p": 1, "ps": 100, "paging": {"pageIndex": 1, "pageSize": 100, "total": 4}, "issues": [
        {"key": "I1", "rule": "python:S1192", "component": comp, "project": "acme:reportfix", "line": line('"customer name missing"'),
         "message": 'Define a constant instead of duplicating this literal "customer name missing" 3 times.', "type": "CODE_SMELL", "status": "OPEN"},
        {"key": "I2", "rule": "python:S1481", "component": comp, "project": "acme:reportfix", "line": line("unused_length"),
         "message": 'Remove the unused local variable "unused_length".', "type": "CODE_SMELL", "status": "OPEN"},
        {"key": "I3", "rule": "python:S3649", "component": comp, "project": "acme:reportfix", "line": line("select * from"),
         "message": "Change this code to not construct SQL queries directly from user-controlled data.", "type": "VULNERABILITY",
         "impacts": [{"softwareQuality": "SECURITY", "severity": "HIGH"}], "status": "OPEN"},
        {"key": "I4", "rule": "python:S1128", "component": comp, "project": "acme:reportfix", "line": line("import sqlite3"),
         "message": 'Remove this unused import.', "type": "CODE_SMELL", "status": "OPEN"},
    ], "components": [{"key": comp, "path": "app/users.py"}]}
    hotspots = {"paging": {"pageIndex": 1, "pageSize": 100, "total": 1}, "hotspots": [
        {"key": "H1", "component": comp, "project": "acme:reportfix", "securityCategory": "insecure-conf", "vulnerabilityProbability": "LOW",
         "status": "TO_REVIEW", "line": line("http://payments"), "message": 'Using http protocol is insecure. Use https instead.', "ruleKey": "python:S5332"},
    ], "components": [{"key": comp, "path": "app/users.py"}]}
    (HERE / "reportfix-issues.json").write_text(json.dumps(issues, indent=1))
    (HERE / "reportfix-hotspots.json").write_text(json.dumps(hotspots, indent=1))


if __name__ == "__main__":
    build_orders()
    build_pricing()
    build_report()
    for name in ("orders", "pricing", "reportfix"):  # check.py compares against these to prove no commit was made
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=HERE / name, capture_output=True, text=True, check=True).stdout
        (HERE / f"{name}.head").write_text(head)
    print(f"built in {HERE}")
