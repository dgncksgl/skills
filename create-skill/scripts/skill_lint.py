#!/usr/bin/env python3
"""Shared parsing for validate-skill.sh, audit-skill.sh and scaffold.sh.

Usage:
  python3 skill_lint.py name <name> [<dir-name>]   -> one error per line, exit 1 if any
  python3 skill_lint.py frontmatter <SKILL.md>     -> JSON {errors, warnings, fields}
  python3 skill_lint.py stats <SKILL.md>           -> JSON body statistics
"""
import json
import os
import re
import sys

NAME_MAX = 64
DESCRIPTION_MAX = 1024
RESERVED_WORDS = ("anthropic", "claude")
NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
KEY_PATTERN = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):(?:[ \t]+(.*))?$")
BLOCK_HEADER = re.compile(r"^([|>])([+-]?)([1-9]?)[ \t]*(#.*)?$")
FENCE = re.compile(r"^[ \t]{0,3}(```+|~~~+)")
TABLE_SEPARATOR = re.compile(r"^\|?[ \t]*:?-+:?[ \t]*(\|[ \t]*:?-+:?[ \t]*)*\|?[ \t]*$")
BULLET = re.compile(r"^[ \t]{0,3}[-*+][ \t]+\S")
NUMBERED = re.compile(r"^[ \t]{0,3}\d+[.)][ \t]+\S")
LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)(?:[ \t]+\"[^\"]*\")?\)")
SCALAR_TYPES = re.compile(
    r"^(~|null|Null|NULL|true|True|TRUE|false|False|FALSE|yes|Yes|YES|no|No|NO|on|On|ON|off|Off|OFF"
    r"|[-+]?(0|[1-9][0-9_]*)|0o?[0-7]+|0x[0-9a-fA-F]+|[-+]?(\.[0-9]+|[0-9][0-9_]*(\.[0-9_]*)?)([eE][-+]?[0-9]+)?"
    r"|[-+]?\.(inf|Inf|INF)|\.(nan|NaN|NAN))$"
)
TURKISH_LETTERS = set("çğıöşüÇĞİÖŞÜ")
TURKISH_VERBS = re.compile(
    r"\b(yaz|yap|et|ver|al|geç|gider|çöz|düzelt|oluştur|üret|hazırla|denetle|uydur|anlat|açıkla|çalıştır|"
    r"uyarla|düzenle|taşı|çevir|kur|sil|ekle|bul|göster|incele|raporla|özetle|ara|oku|aç|bitir|başlat|"
    r"kontrol et|test et|review et|entegre et|migrate et)$",
    re.IGNORECASE,
)


def is_turkish_phrase(phrase):
    return bool(TURKISH_LETTERS & set(phrase)) or bool(TURKISH_VERBS.search(phrase.strip()))


def name_errors(name, dir_name=None):
    errors = []
    if not name:
        return ["name is empty"]
    if len(name) > NAME_MAX:
        errors.append(f"name is {len(name)} characters (max {NAME_MAX})")
    if not NAME_PATTERN.match(name):
        errors.append(
            f"name '{name}' must use only a-z, 0-9 and single hyphens, "
            "and must not start or end with a hyphen"
        )
    for word in RESERVED_WORDS:
        if word in name:
            errors.append(f"name '{name}' contains the reserved word '{word}'")
    if dir_name is not None and name != dir_name:
        errors.append(f"name '{name}' does not match directory name '{dir_name}'")
    return errors


def unescape_double(text):
    escapes = {"n": "\n", "t": "\t", '"': '"', "\\": "\\", "/": "/", "0": "\0", " ": " "}
    out, i = [], 0
    while i < len(text):
        ch = text[i]
        if ch != "\\":
            out.append(ch)
            i += 1
            continue
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if nxt in escapes:
            out.append(escapes[nxt])
            i += 2
        elif nxt in ("u", "x", "U"):
            width = {"x": 2, "u": 4, "U": 8}[nxt]
            out.append(chr(int(text[i + 2:i + 2 + width], 16)))
            i += 2 + width
        else:
            raise ValueError(f"unknown escape '\\{nxt}' in double-quoted string")
    return "".join(out)


def fold(lines):
    parts, blank_run = [], 0
    for line in lines:
        if line.strip():
            if parts and not blank_run:
                parts.append(" ")
            parts.append(line.strip())
            blank_run = 0
        else:
            parts.append("\n")
            blank_run += 1
    return "".join(parts)


def fold_keep_edges(lines):
    parts, pending_breaks = [lines[0]], 0
    for line in lines[1:]:
        if line:
            parts.append("\n" * pending_breaks if pending_breaks else " ")
            parts.append(line)
            pending_breaks = 0
        else:
            pending_breaks += 1
    if pending_breaks:
        parts.append("\n" * pending_breaks)
    return "".join(parts)


def parse_quoted(first, continuation, quote):
    text = "\n".join([first] + continuation)
    body = text[1:]
    if quote == '"':
        match = re.match(r'((?:[^"\\]|\\.)*)"(.*)$', body, re.DOTALL)
    else:
        match = re.match(r"((?:[^']|'')*)'(.*)$", body, re.DOTALL)
    if not match:
        raise ValueError(f"unclosed {quote} quote")
    inner, rest = match.group(1), match.group(2).strip()
    if rest and not rest.startswith("#"):
        raise ValueError(f"unexpected text after closing quote: '{rest[:30]}'")
    lines = inner.split("\n")
    if len(lines) > 1:
        lines = [lines[0].rstrip()] + [l.strip() for l in lines[1:-1]] + [lines[-1].lstrip()]
        folded = fold_keep_edges(lines)
    else:
        folded = lines[0]
    return unescape_double(folded) if quote == '"' else folded.replace("''", "'")


def parse_block(header, lines):
    match = BLOCK_HEADER.match(header)
    if not match:
        raise ValueError(f"invalid block scalar header '{header}'")
    style, chomp = match.group(1), match.group(2)
    content = list(lines)
    trailing_blanks = 0
    while content and not content[-1].strip():
        content.pop()
        trailing_blanks += 1
    indent = min((len(l) - len(l.lstrip(" ")) for l in content if l.strip()), default=0)
    stripped = [l[indent:] if l.strip() else "" for l in content]
    if style == "|":
        text = "\n".join(stripped)
    else:
        text = fold(stripped)
    if chomp != "-" and text:
        text += "\n"
    if chomp == "+" and text:
        text += "\n" * trailing_blanks
    return text


def parse_plain(first, continuation):
    value = first
    comment = re.search(r"[ \t]#", value)
    if comment:
        value = value[:comment.start()]
    value = value.strip()
    if value[:1] in ("@", "`", "%"):
        raise ValueError(f"plain value cannot start with '{value[0]}'; quote it")
    if value[:1] in ("[", "{"):
        raise ValueError("value is a YAML list/map, not a string; quote it")
    anchor = re.match(r"&\S+[ \t]+", value)
    if anchor:
        value = value[anchor.end():]
    if value[:1] in ("*", "!"):
        raise ValueError(f"value starts with YAML indicator '{value[0]}'; quote it")
    if value == "-" or value.startswith(("- ", "-\t")):
        raise ValueError("value starts with '- ' (a YAML list item); quote it")
    if continuation == [] and SCALAR_TYPES.match(value):
        raise ValueError(f"'{value}' is parsed as a number/boolean/null, not text; quote it")
    pieces = [value] + [c.strip() for c in continuation]
    for piece in pieces:
        if re.search(r":([ \t]|$)", piece):
            raise ValueError("unquoted value contains ': ' (invalid YAML); wrap it in quotes")
    return fold([p for p in pieces])


def parse_frontmatter(path):
    result = {"errors": [], "warnings": [], "fields": {}, "body_start": 0}
    raw = open(path, encoding="utf-8", newline="").read()
    if "\r\n" in raw:
        result["warnings"].append("file uses CRLF line endings; convert to LF")
        raw = raw.replace("\r\n", "\n")
    lines = raw.split("\n")
    if not lines or lines[0].strip() != "---":
        result["errors"].append("frontmatter must start with '---' on line 1")
        return result
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        result["errors"].append("frontmatter has no closing '---'")
        return result
    result["body_start"] = end + 1
    entries, current = [], None
    for line in lines[1:end]:
        if not line.strip():
            if current is not None:
                current[2].append(line)
            continue
        if line.startswith("#"):
            continue
        if line[0] in (" ", "\t"):
            if current is None:
                result["errors"].append(f"indented line before any key: '{line.strip()[:40]}'")
            else:
                current[2].append(line)
            continue
        match = KEY_PATTERN.match(line)
        if not match:
            result["errors"].append(f"line is not 'key: value': '{line[:40]}'")
            current = None
            continue
        current = [match.group(1), (match.group(2) or "").rstrip(), []]
        entries.append(current)
    seen = set()
    for key, first, continuation in entries:
        if key in seen:
            result["errors"].append(f"duplicate key '{key}'")
        seen.add(key)
        raw_continuation = list(continuation)
        while continuation and not continuation[-1].strip():
            continuation.pop()
        try:
            if first[:1] in ('"', "'"):
                value = parse_quoted(first, continuation, first[0])
            elif first[:1] in ("|", ">"):
                value = parse_block(first, raw_continuation)
            elif not first and continuation:
                nested = all(
                    re.match(r"^[ \t]+(- |[A-Za-z_][\w-]*:([ \t]|$))", l) for l in continuation if l.strip()
                )
                value = {"nested": True} if nested else parse_plain(continuation[0].strip(), continuation[1:])
            else:
                value = parse_plain(first, continuation) if first else ""
        except ValueError as error:
            result["errors"].append(f"{key}: {error}")
            continue
        result["fields"][key] = value
    return result


def body_stats(path, body_start):
    lines = open(path, encoding="utf-8").read().replace("\r\n", "\n").split("\n")[body_start:]
    stats = {"max_table_rows": 0, "max_list_items": 0, "code_blocks": 0, "links": [], "if_chains": 0}
    fence, table_rows, list_items = None, 0, 0

    def close_table():
        nonlocal table_rows
        stats["max_table_rows"] = max(stats["max_table_rows"], max(table_rows - 1, 0))
        table_rows = 0

    def close_list():
        nonlocal list_items
        stats["max_list_items"] = max(stats["max_list_items"], list_items)
        list_items = 0

    for line in lines:
        fence_match = FENCE.match(line)
        if fence:
            if fence_match and fence_match.group(1)[0] == fence[0] and len(fence_match.group(1)) >= len(fence):
                fence = None
            elif re.match(r"^\s*(if |elif |case )", line):
                stats["if_chains"] += 1
            continue
        if fence_match:
            close_table()
            close_list()
            fence = fence_match.group(1)
            stats["code_blocks"] += 1
            continue
        stripped = line.strip()
        if stripped.startswith("|"):
            if not TABLE_SEPARATOR.match(stripped):
                table_rows += 1
            continue
        close_table()
        if BULLET.match(line) or NUMBERED.match(line):
            list_items += 1
        elif stripped and not line.startswith((" ", "\t")):
            close_list()
        for target in LINK.findall(line):
            stats["links"].append(target)
    close_table()
    close_list()
    return stats


def main(argv):
    if len(argv) < 3:
        print(__doc__, file=sys.stderr)
        return 2
    command, target = argv[1], argv[2]
    if command == "name":
        errors = name_errors(target, argv[3] if len(argv) > 3 else None)
        for error in errors:
            print(error)
        return 1 if errors else 0
    if command == "frontmatter":
        result = parse_frontmatter(target)
        description = result["fields"].get("description")
        if isinstance(description, str):
            result["description_length"] = len(description)
            quoted = re.findall(r"\"([^\"]+)\"", description)
            result["turkish_phrases"] = sum(1 for q in quoted if is_turkish_phrase(q))
            result["english_phrases"] = sum(
                1 for q in quoted if re.fullmatch(r"[A-Za-z][A-Za-z0-9 '/.,-]*", q) and not is_turkish_phrase(q)
            )
            use_when = re.search(r"use when(.*?)(\"|$)", description, re.IGNORECASE | re.DOTALL)
            scenario_words = re.findall(r"[A-Za-z]{2,}", use_when.group(1)) if use_when else []
            result["english_trigger"] = result["english_phrases"] > 0 or len(scenario_words) >= 5
            procedure = re.search(r" then |→|->|\bstep [0-9]|\bönce\b|\bsonra\b|\bardından\b", description, re.IGNORECASE)
            result["procedure_hint"] = procedure.group(0).strip() if procedure else ""
        print(json.dumps(result, ensure_ascii=False))
        return 0
    if command == "stats":
        start = parse_frontmatter(target)["body_start"]
        print(json.dumps(body_stats(target, start), ensure_ascii=False))
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
