#!/usr/bin/env python3
"""List lines of the original instruction file(s) that no new file contains.

Usage: python3 coverage.py <repo-root> <original-file> [...] [--also <new-file>]

Read-only. Compares every non-blank, non-heading line of the backed-up originals
with the current CLAUDE.md, .claude/CLAUDE.md, CLAUDE.local.md, AGENTS.md,
nested CLAUDE.md files, .claude/rules/**/*.md and .claude/settings.json. Each
printed line was rewritten, moved into a hook, or deleted: the mapping table
must account for it. Exit 0 = every line found, 1 = unmatched lines printed,
2 = usage error.
"""

import re
import sys
from pathlib import Path

SKIP = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "build",
    "dist",
    "target",
    "Pods",
    "worktrees",
}


def normalize(line):
    line = re.sub(r"^\s*(?:[-*+>]|\d+\.)\s+", "", line)
    line = re.sub(r"[*_`]", "", line).lower()
    return re.sub(r"\s+", " ", line).strip()


def current_files(root):
    for f in root.rglob("*"):
        if any(part in SKIP for part in f.relative_to(root).parts[:-1]):
            continue
        rel = f.relative_to(root).as_posix()
        if f.is_file() and (
            f.name in ("CLAUDE.md", "CLAUDE.local.md", "AGENTS.md")
            or (rel.startswith(".claude/rules/") and f.suffix == ".md")
            or rel == ".claude/settings.json"
        ):
            yield f


def main():
    args, also = [], []
    rest = sys.argv[1:]
    while rest:
        a = rest.pop(0)
        if a == "--also" and rest:
            also.append(Path(rest.pop(0)))
        else:
            args.append(a)
    sys.argv = [sys.argv[0]] + args
    if len(sys.argv) < 3 or not Path(sys.argv[1]).is_dir():
        print(
            "Usage: python3 coverage.py <repo-root> <original-file> [...] [--also <new-file>]",
            file=sys.stderr,
        )
        return 2
    root = Path(sys.argv[1]).resolve()
    corpus = "\n".join(
        normalize(line)
        for f in list(current_files(root)) + also
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines()
    )
    unmatched = 0
    for original in sys.argv[2:]:
        in_fence, ranges, prev = False, [], None
        for i, line in enumerate(
            Path(original).read_text(encoding="utf-8", errors="replace").splitlines(), 1
        ):
            if line.strip().startswith("```"):
                in_fence = not in_fence
                continue
            norm = normalize(line)
            if (
                not norm
                or norm.startswith(("#", "---", "|---", "<!--"))
                or re.fullmatch(r"[|\s:-]+", norm)
            ):
                continue
            if norm not in corpus:
                unmatched += 1
                if ranges and ranges[-1][1] == prev:
                    ranges[-1][1] = i
                else:
                    if not ranges:
                        print(f"\n{original}:")
                    else:
                        print()
                    ranges.append([i, i])
                print(f"  {i}: {line.strip()[:160]}")
                prev = i
            if norm:
                prev = i
        if ranges:
            print(
                "\nUnmatched ranges in "
                + original
                + ": "
                + ", ".join(f"{x}-{y}" if x != y else str(x) for x, y in ranges)
            )
    print(
        f"\n{unmatched} original line(s) not found verbatim in the new files.",
        file=sys.stderr,
    )
    return 1 if unmatched else 0


if __name__ == "__main__":
    sys.exit(main())
