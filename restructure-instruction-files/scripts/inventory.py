#!/usr/bin/env python3
"""Inventory of a repository's Claude Code instruction files.

Usage: python3 inventory.py <repo-root>

Read-only. Prints, for CLAUDE.md, .claude/CLAUDE.md, CLAUDE.local.md, AGENTS.md,
nested CLAUDE.md/AGENTS.md and .claude/rules/**/*.md: size, emphasis words,
@imports, paths globs and how many files each matches, backticked paths that do
not exist, tool names mentioned, lines repeated across files, and the detected
stacks. Exit 0 = report printed, 2 = usage error.
"""

import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

SKIP_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    "build",
    "dist",
    "target",
    "bin",
    "obj",
    "out",
    "Pods",
    "DerivedData",
    ".gradle",
    ".idea",
    "vendor",
    ".next",
    ".nuxt",
    "coverage",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    "worktrees",
    ".dart_tool",
    ".build",
}
ACRONYMS = {
    "HTTP", "HTTPS", "JSON", "YAML", "HTML", "REST", "UUID", "TODO", "FIXME", "README",
    "CLAUDE", "AGENTS", "MEMORY", "SKILL", "CHANGELOG", "LICENSE", "ASCII", "OAUTH", "CORS",
    "CSRF", "GDPR", "KVKK", "GPIO", "MVVM", "MVC", "CRUD", "GRPC", "AJAX", "JDBC", "JWT",
    "SDK", "UTF", "ARIA", "POST", "PATCH", "DELETE", "HEAD", "OPTIONS", "WCAG", "SQLITE", "MYSQL", "XML", "PDF", "IDE", "LLM", "TOML",
}
CAPS_TOKEN = re.compile(r"(?<!\w)(DO NOT|DON'T|[^\W\d_]{4,})(?!\w)")


class Emphasis:
    @staticmethod
    def findall(text):
        text = re.sub(r"`[^`\n]*`", "", text)
        return [t for t in CAPS_TOKEN.findall(text) if t.isupper() and t not in ACRONYMS]

    @staticmethod
    def search(line):
        return bool(Emphasis.findall(line))


EMPHASIS = Emphasis
FILE_EXT = re.compile(
    r"\.(md|py|java|kt|kts|cs|csproj|sln|swift|ts|tsx|js|jsx|mjs|cjs|json|toml|yaml|yml|xml|"
    r"gradle|go|rs|rb|php|sh|cfg|ini|txt|lock|env|properties|plist|html|css|scss|sql|dart|"
    r"vue|svelte|c|h|cpp|hpp|m|mm|xcconfig|pbxproj)$"
)
TOOL_MENTION = re.compile(
    r"`([A-Z][A-Za-z]+)`(?=[^\n]{0,20}\btool)|\b([A-Z][A-Za-z]+) tool\b"
)
MARKERS = [
    (
        "python",
        [
            "pyproject.toml",
            "requirements.txt",
            "setup.py",
            "Pipfile",
            "uv.lock",
            "poetry.lock",
        ],
    ),
    ("java/kotlin (maven)", ["pom.xml"]),
    (
        "java/kotlin (gradle)",
        ["build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts"],
    ),
    ("android", ["AndroidManifest.xml"]),
    ("c#/.net", ["*.csproj", "*.sln", "global.json", "Directory.Build.props"]),
    ("swift/ios", ["Package.swift", "*.xcodeproj", "*.xcworkspace", "Podfile"]),
    (
        "node/typescript",
        ["package.json", "tsconfig.json", "pnpm-lock.yaml", "yarn.lock"],
    ),
    ("go", ["go.mod"]),
    ("rust", ["Cargo.toml"]),
    ("ruby", ["Gemfile"]),
    ("php", ["composer.json"]),
    ("flutter/dart", ["pubspec.yaml"]),
]


def walk(root):
    stack = [root]
    while stack:
        d = stack.pop()
        try:
            entries = list(d.iterdir())
        except OSError:
            continue
        for e in entries:
            if e.is_dir() and not e.is_symlink():
                if e.name not in SKIP_DIRS and not (
                    e.name.startswith(".") and e.name != ".claude"
                ):
                    stack.append(e)
            elif e.is_file():
                yield e


def glob_to_regex(pattern):
    i, out = 0, []
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            out.append("[^/]")
            i += 1
        elif pattern[i] == "[":
            j = pattern.find("]", i)
            if j == -1:
                return None
            out.append(pattern[i : j + 1])
            i = j + 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return re.compile("^" + "".join(out) + "$")


def expand_braces(pattern):
    m = re.search(r"\{([^{}]*)\}", pattern)
    if not m:
        return [pattern]
    result = []
    for part in m.group(1).split(","):
        result.extend(expand_braces(pattern[: m.start()] + part + pattern[m.end() :]))
    return result


def frontmatter_paths(text):
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    lines = text[3:end].splitlines()
    paths, collecting = [], False
    for line in lines:
        if re.match(r"^paths\s*:", line):
            value = line.split(":", 1)[1].strip()
            if value:
                paths.extend(
                    p.strip().strip("\"'") for p in value.strip("[]").split(",")
                )
                collecting = False
            else:
                collecting = True
        elif collecting and re.match(r"^\s*-\s*", line):
            paths.append(re.sub(r"^\s*-\s*", "", line).strip().strip("\"'"))
        elif collecting and line.strip() and not line.startswith(" "):
            collecting = False
    return [p for p in paths if p]


def strip_code(text):
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    return text


def imports(text):
    body = re.sub(r"`[^`\n]*`", "", strip_code(text))
    return re.findall(r"(?:^|\s)@([\w./~-][^\s]*)", body)


def path_tokens(text):
    found = set()
    for span in re.findall(r"`([^`\n]+)`", text):
        for token in span.split():
            token = token.strip("\"'()[],;:").rstrip(".")
            if (
                not token
                or token.startswith(("http", "~", "/", "$", "-", "@"))
                or any(c in token for c in "<>*{}=|")
            ):
                continue
            if ("/" in token or FILE_EXT.search(token)) and not re.fullmatch(r"\.\w+", token):
                found.add(token)
    return found


def normalize(line):
    line = re.sub(r"^\s*(?:[-*+]|\d+\.)\s+", "", line)
    line = re.sub(r"[*_`]", "", line).lower()
    return re.sub(r"\s+", " ", line).strip()


def main():
    if len(sys.argv) != 2 or not Path(sys.argv[1]).is_dir():
        print("Usage: python3 inventory.py <repo-root>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve()
    files = list(walk(root))
    rel_files = [f.relative_to(root).as_posix() for f in files]
    names = Counter(f.name for f in files)

    instruction = []
    for f in files:
        rel = f.relative_to(root).as_posix()
        if f.name in ("CLAUDE.md", "CLAUDE.local.md", "AGENTS.md") or (
            rel.startswith(".claude/rules/") and f.suffix == ".md"
        ):
            instruction.append(f)
    instruction.sort(
        key=lambda f: (
            f.relative_to(root).as_posix().count("/"),
            f.relative_to(root).as_posix(),
        )
    )

    print(f"# Instruction file inventory: {root}\n")
    stacks = []
    for stack, markers in MARKERS:
        hits = [
            r
            for r in rel_files
            if any(Path(r).match(m) for m in markers) and r.count("/") <= 3
        ]
        hits += [
            d.relative_to(root).as_posix()
            for d in root.glob("*")
            if d.is_dir() and any(d.match(m) for m in markers)
        ]
        if hits:
            stacks.append(f"{stack}: {', '.join(sorted(set(hits))[:4])}")
    print("## Detected stacks")
    print("\n".join(f"- {s}" for s in stacks) or "- none detected")
    ext = Counter(Path(r).suffix for r in rel_files if Path(r).suffix)
    print("- top extensions: " + ", ".join(f"{e} {n}" for e, n in ext.most_common(10)))

    if not instruction:
        print("\nNo instruction files found.")
        return 0

    print("\n## Files")
    print("| file | lines | bytes | ≈tokens | emphasis | @imports | loads |")
    print("|---|---|---|---|---|---|---|")
    total_always, import_bytes, counted = 0, 0, set()
    details, line_places = [], defaultdict(set)
    for f in instruction:
        rel = f.relative_to(root).as_posix()
        text = f.read_text(encoding="utf-8", errors="replace")
        n_lines, n_bytes = len(text.splitlines()), len(text.encode())
        emph = len(EMPHASIS.findall(strip_code(text)))
        imps = imports(text)
        paths = frontmatter_paths(text) if rel.startswith(".claude/rules/") else None
        if rel.startswith(".claude/rules/"):
            loads = "when paths match" if paths else "every session (no paths:)"
        elif "/" in rel and not rel.startswith(".claude/"):
            loads = "on demand (subdirectory)"
        elif f.name == "AGENTS.md":
            loads = "only if no CLAUDE.md (default setting)"
        else:
            loads = "every session"
        if loads.startswith("every session"):
            total_always += n_bytes
            counted.add(f.resolve())
            for imp in imps:
                target = (Path(imp).expanduser() if imp.startswith("~") else f.parent / imp).resolve()
                if target.is_file() and target not in counted:
                    counted.add(target)
                    import_bytes += len(target.read_bytes())
        print(
            f"| {rel} | {n_lines} | {n_bytes} | {n_bytes // 4} | {emph} | {len(imps)} | {loads} |"
        )
        body_start = 0
        if text.startswith("---"):
            end = text.find("\n---", 3)
            body_start = text[:end].count("\n") + 2 if end != -1 else 0
        for i, line in enumerate(text.splitlines(), 1):
            if i <= body_start:
                continue
            norm = re.sub(r"\d+", "#", normalize(line))
            if len(norm) >= 30 and not norm.startswith(("#", "|", "---", "```")):
                line_places[norm].add(f"{rel}:{i}")
        details.append((rel, f, text, imps, paths))
    print(
        f"\nLoaded at every session start (bytes): {total_always + import_bytes} (≈{(total_always + import_bytes) // 4} tokens),"
        f" of which @imports: {import_bytes}. Nested @imports are not followed."
    )

    print("\n## Per-file findings")
    for rel, f, text, imps, paths in details:
        notes = []
        n_lines = len(text.splitlines())
        if n_lines > 200:
            notes.append(f"{n_lines} lines: over the documented 200-line target")
        if imps:
            notes.append(
                "@imports (load at launch, do not save context): " + ", ".join(imps)
            )
        if rel.startswith(".claude/rules/"):
            if paths is None:
                notes.append("no paths: frontmatter, so it loads every session")
            else:
                for p in paths:
                    regexes = [glob_to_regex(x) for x in expand_braces(p)]
                    count = sum(
                        1
                        for r in rel_files
                        if any(rx and rx.match(r) for rx in regexes)
                    )
                    notes.append(
                        f"paths '{p}' matches {count} file(s)"
                        + ("  <-- matches nothing" if count == 0 else "")
                    )
        missing, unknown_names = [], []
        for token in sorted(path_tokens(text)):
            candidates = [root / token, f.parent / token]
            if any(c.exists() for c in candidates):
                continue
            if "/" not in token.rstrip("/") and names.get(token):
                continue
            if "/" in token and any(
                r.endswith("/" + token.rstrip("/"))
                or ("/" + token.rstrip("/") + "/") in ("/" + r)
                for r in rel_files
            ):
                continue
            first = token.split("/")[0]
            if "/" in token.rstrip("/") and (root / first).is_dir():
                missing.append(token)
            else:
                unknown_names.append(token)
        if missing:
            notes.append(
                "paths not found (stale? first rule out gitignored, build-generated, future or placeholder): "
                + ", ".join(missing)
            )
        if unknown_names:
            notes.append(
                "names not found in the repo (often module imports, framework file names or future files; check before calling stale): "
                + ", ".join(unknown_names)
            )
        tools = sorted({a or b for a, b in TOOL_MENTION.findall(text)})
        if tools:
            notes.append(
                "tool names mentioned (compare with the session's real tool list): "
                + ", ".join(tools)
            )
        emph_lines = [
            str(i)
            for i, line in enumerate(text.splitlines(), 1)
            if EMPHASIS.search(line)
        ]
        if emph_lines:
            notes.append("emphasis on lines: " + ", ".join(emph_lines[:40]))
        print(f"\n### {rel}")
        print("\n".join(f"- {n}" for n in notes) or "- nothing flagged")

    dups = {k: v for k, v in line_places.items() if len(v) > 1}
    print("\n## Lines repeated in more than one place")
    if dups:
        for k, v in sorted(dups.items(), key=lambda kv: sorted(kv[1])):
            places = sorted(v, key=lambda x: (x.rsplit(":", 1)[0], int(x.rsplit(":", 1)[1])))
            shown = ", ".join(places[:4]) + (f", … ({len(places)} places)" if len(places) > 4 else "")
            print(f"- {shown}: {k[:100]}")
    else:
        print(
            "- none (only exact repeats are detected; reworded duplicates need a manual read)"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
