#!/usr/bin/env python3
"""Check proposed session names: lowercase a-z/0-9 kebab-case, at most 40 characters.

Usage: check_names.py NAME [NAME ...]
Prints one line per name (OK or FAIL with the reason and length).
Exit codes: 0 all names valid, 1 at least one invalid, 2 usage error.
"""
import re
import sys

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MAX_LEN = 40


def problem(name):
    if len(name) > MAX_LEN:
        return "too long: %d characters, limit %d" % (len(name), MAX_LEN)
    if not NAME_RE.fullmatch(name):
        return "not lowercase a-z/0-9 kebab-case"
    return None


def main(argv):
    if not argv:
        print("usage: check_names.py NAME [NAME ...]", file=sys.stderr)
        return 2
    failed = False
    for name in argv:
        reason = problem(name)
        if reason:
            failed = True
            print("FAIL  %s  (%s)" % (name, reason))
        else:
            print("OK    %s  (%d)" % (name, len(name)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
