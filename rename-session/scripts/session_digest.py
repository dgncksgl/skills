#!/usr/bin/env python3
"""Print a compact, whole-session digest of a Claude Code transcript.

Every user prompt of the main thread is listed in order, together with the
work that followed it (tool calls, edited files, skills), so a session can be
named after its dominant work instead of its last prompt.

Usage: session_digest.py [TRANSCRIPT.jsonl] [--prompt-chars N]
Without a path, the transcript of the running session is located through
CLAUDE_CODE_SESSION_ID; failing that, the newest transcript of the current
working directory's project is used and a warning is printed.
Exit codes: 0 digest printed, 1 transcript not found or unreadable, 2 usage error.
"""
import argparse
import glob
import json
import os
import re
import sys
from collections import Counter

PROJECTS_DIR = os.path.expanduser("~/.claude/projects")
EDIT_TOOLS = {"Edit", "Write", "NotebookEdit", "MultiEdit"}
# User-role entries that are machine output, not something the user typed.
NOISE_PREFIXES = (
    "<local-command-stdout>", "<local-command-stderr>", "<bash-stdout>",
    "<bash-stderr>", "<task-notification>", "<system-reminder>", "Caveat:",
    "[Request interrupted", "Base directory for this skill:",
)
COMMAND_RE = re.compile(r"<command-name>\s*(/?[^<\s]+)\s*</command-name>")
COMMAND_ARGS_RE = re.compile(r"<command-args>(.*?)</command-args>", re.S)
TYPED_COMMAND_RE = re.compile(r"^/[\w:.-]+(\s[^\n]{0,200})?$")
BASH_INPUT_RE = re.compile(r"<bash-input>(.*?)</bash-input>", re.S)
PASTE_RE = re.compile(r"<pasted_content[^>]*>.*?</pasted_content>", re.S)
REMINDER_RE = re.compile(r"<system-reminder>.*?</system-reminder>", re.S)
SUMMARY_PREAMBLE = ("This session is being continued from a previous conversation that ran"
                    " out of context. The summary below covers the earlier portion of the"
                    " conversation.")
SCRATCH_PREFIXES = ("/tmp/", "/private/tmp/", "/var/folders/")


def locate_transcript():
    session_id = os.environ.get("CLAUDE_CODE_SESSION_ID", "").strip()
    if session_id:
        hits = glob.glob(os.path.join(PROJECTS_DIR, "*", session_id + ".jsonl"))
        if hits:
            return hits[0], None
    project_dir = os.path.join(PROJECTS_DIR, re.sub(r"[^A-Za-z0-9]", "-", os.getcwd()))
    candidates = glob.glob(os.path.join(project_dir, "*.jsonl"))
    if not candidates:
        return None, None
    newest = max(candidates, key=os.path.getmtime)
    return newest, "WARNING: session id unknown; using newest transcript of this project: " + newest


def one_line(text, limit):
    text = PASTE_RE.sub("[pasted text]", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


def text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(p.get("text", "") for p in content
                         if isinstance(p, dict) and p.get("type") == "text")
    return ""


def classify_user_entry(entry):
    """Return (kind, text): kind is prompt, command, shell, summary or None."""
    if entry.get("isCompactSummary"):
        return "summary", text_of((entry.get("message") or {}).get("content"))
    if entry.get("isMeta"):
        return None, ""
    text = text_of((entry.get("message") or {}).get("content")).strip()
    if not text:
        return None, ""  # tool results only
    command = COMMAND_RE.search(text) if text.startswith(("<command-message>", "<command-name>")) else None
    if command:
        name = command.group(1)
        if not name.startswith("/"):
            name = "/" + name
        args = COMMAND_ARGS_RE.search(text)
        return "command", (name + " " + args.group(1).strip()).strip() if args else name
    shell = BASH_INPUT_RE.search(text)
    if shell:
        return "shell", "! " + shell.group(1).strip()
    if text.startswith(NOISE_PREFIXES):
        return None, ""
    if TYPED_COMMAND_RE.match(text):
        return "command", text
    return "prompt", text


def new_segment(kind, text):
    return {"kind": kind, "text": text, "tools": 0, "edits": [], "skills": [],
            "agents": 0, "reply": ""}


def read_entries(path):
    with open(path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(entry, dict):
                yield entry


def build(path):
    segments, titles, summaries = [], {}, []
    current = None
    for entry in read_entries(path):
        kind = entry.get("type")
        if kind in ("custom-title", "ai-title"):
            titles[kind] = entry.get("customTitle") or entry.get("aiTitle")
            continue
        if entry.get("isSidechain"):
            continue
        attachment = entry.get("attachment") if kind == "attachment" else None
        if isinstance(attachment, dict) and attachment.get("type") == "queued_command":
            # a prompt typed while Claude was still working
            if attachment.get("commandMode") != "prompt" or attachment.get("isMeta"):
                continue
            kind, entry = "user", {"message": {"content": attachment.get("prompt")}}
        if kind == "user":
            ukind, text = classify_user_entry(entry)
            if ukind == "summary":
                summaries.append(text)
                current = new_segment("summary", "")
                segments.append(current)
            elif ukind:
                last = next((s for s in reversed(segments) if s["kind"] != "summary"), None)
                if last and last["kind"] == ukind and last["text"] == text and last["tools"] == 0:
                    continue  # the same prompt resent, or a typed command echoed as an entry
                current = new_segment(ukind, text)
                segments.append(current)
        elif kind == "assistant" and current is not None:
            content = (entry.get("message") or {}).get("content")
            for part in content if isinstance(content, list) else []:
                if not isinstance(part, dict):
                    continue
                if part.get("type") == "text" and part.get("text", "").strip():
                    current["reply"] = part["text"]
                if part.get("type") != "tool_use":
                    continue
                current["tools"] += 1
                name, args = part.get("name", ""), part.get("input") or {}
                edited = args.get("file_path") or args.get("notebook_path")
                if name in EDIT_TOOLS and edited:
                    current["edits"].append(edited)
                elif name == "Skill" and args.get("skill"):
                    current["skills"].append(args["skill"])
                elif name in ("Agent", "Task"):
                    current["agents"] += 1
    return segments, titles, summaries


def short_path(path):
    home = os.path.expanduser("~")
    return "~" + path[len(home):] if path.startswith(home) else path


def render(path, segments, titles, summaries, prompt_chars):
    out = ["# Session digest", "transcript: " + short_path(path)]
    prompts = [s for s in segments if s["kind"] == "prompt"]
    total_tools = sum(s["tools"] for s in segments)
    all_edits = [p for s in segments for p in s["edits"]]
    edit_counter = Counter(p for p in all_edits if not p.startswith(SCRATCH_PREFIXES))
    scratch_edits = len({p for p in all_edits if p.startswith(SCRATCH_PREFIXES)})
    skill_counter = Counter(k for s in segments for k in s["skills"])
    out.append("user prompts: %d | tool calls: %d | files edited: %d (+%d scratch files)"
               % (len(prompts), total_tools, len(edit_counter), scratch_edits))
    if titles:
        out.append("existing titles (reference only, may be stale): "
                   + ", ".join("%s=%r" % kv for kv in sorted(titles.items())))
    if edit_counter:
        out.append("most edited files: " + ", ".join(
            "%s x%d" % (short_path(p), n) for p, n in edit_counter.most_common(12)))
    if skill_counter:
        out.append("skills used: " + ", ".join(
            "%s x%d" % kv for kv in skill_counter.most_common()))
    if summaries:
        latest = REMINDER_RE.sub("", summaries[-1]).replace(SUMMARY_PREAMBLE, "")
        out.append("latest compaction summary (%d in total): %s"
                   % (len(summaries), one_line(latest, 1200)))
    out.append("")
    out.append("## Timeline (#, work after the prompt, prompt; last line = the request that invoked this skill)")
    number = marker = 0
    for index, seg in enumerate(segments):
        if seg["kind"] == "summary":
            marker += 1
            where = ("its summary recaps the lines above" if index
                     else "this transcript starts here; its summary covers work done before it")
            work = " (work after it: tools=%d)" % seg["tools"] if seg["tools"] else ""
            out.append("--- compaction %d of %d: %s%s ---" % (marker, len(summaries), where, work))
            continue
        number += 1
        work = "tools=%d" % seg["tools"]
        if seg["edits"]:
            names = sorted({os.path.basename(p) for p in seg["edits"]})
            work += " edits=%d[%s]" % (len(seg["edits"]), ", ".join(names[:4])
                                       + (", …" if len(names) > 4 else ""))
        if seg["agents"]:
            work += " agents=%d" % seg["agents"]
        if seg["skills"]:
            work += " skills=[%s]" % ", ".join(sorted(set(seg["skills"])))
        label = {"prompt": "", "command": "cmd ", "shell": "shell "}[seg["kind"]]
        out.append("%d. (%s) %s%s" % (number, work, label, one_line(seg["text"], prompt_chars)))
        if seg["reply"] and seg["kind"] == "prompt":
            out.append("    ↳ " + one_line(seg["reply"], 120))
    return "\n".join(out)


def main(argv):
    parser = argparse.ArgumentParser(description="Print a whole-session digest of a Claude Code transcript.")
    parser.add_argument("transcript", nargs="?")
    parser.add_argument("--prompt-chars", type=int, default=200)
    args = parser.parse_args(argv)
    if args.prompt_chars < 40:
        parser.error("--prompt-chars must be at least 40")
    path, warning = (args.transcript, None) if args.transcript else locate_transcript()
    if not path or not os.path.isfile(path):
        print("ERROR: transcript not found" + (": " + path if path else ""), file=sys.stderr)
        return 1
    try:
        segments, titles, summaries = build(path)
    except OSError as error:
        print("ERROR: cannot read transcript: %s" % error, file=sys.stderr)
        return 1
    if warning:
        print(warning)
    print(render(path, segments, titles, summaries, args.prompt_chars))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
