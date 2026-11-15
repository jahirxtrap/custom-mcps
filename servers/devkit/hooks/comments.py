"""Warn Claude Code when an edit it just made adds comments or docstrings that break the conventions."""
from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
comments = importlib.import_module("convkit.comments")

_SHOWN = 10
_HEAD = 48
_TAIL = 24
_GIT_TIMEOUT = 5
_LABELS = {
    "comment": "comment",
    "doc_lines": "docstring over one line",
    "doc_long": "docstring over 100 characters",
    "doc_repeats_name": "docstring that only repeats the name",
    "doc_rationale": "docstring carrying rationale",
}


def _lines(text: str) -> set[str]:
    return {line.strip() for line in text.splitlines() if line.strip()}


def _committed(path: Path) -> set[str]:
    try:
        shown = subprocess.run(
            ["git", "--no-pager", "show", f"HEAD:./{path.name}"],
            cwd=path.parent, capture_output=True, text=True, encoding="utf-8", errors="replace",
            stdin=subprocess.DEVNULL, timeout=_GIT_TIMEOUT,
        )
    except (OSError, subprocess.SubprocessError):
        return set()
    return _lines(shown.stdout) if shown.returncode == 0 else set()


def _changed(tool: str, tool_input: dict) -> tuple[str, str]:
    if tool == "Write":
        return "", tool_input.get("content", "")
    if tool == "MultiEdit":
        edits = tool_input.get("edits") or []
        return (
            "\n".join(edit.get("old_string", "") for edit in edits),
            "\n".join(edit.get("new_string", "") for edit in edits),
        )
    return tool_input.get("old_string", ""), tool_input.get("new_string", "")


def _span(finding: dict) -> int:
    return finding.get("lines", 1) if finding["kind"] == "comment" else 1


def _introduced(lines: list[str], finding: dict, fresh: set[str]) -> bool:
    start = finding["line"] - 1
    return any(line.strip() in fresh for line in lines[start : start + _span(finding)])


def _excerpt(lines: list[str], finding: dict) -> str:
    start = finding["line"] - 1
    block = " ".join(line.strip() for line in lines[start : start + _span(finding)])
    if len(block) <= _HEAD + _TAIL:
        return block
    head = block[:_HEAD] if block[_HEAD] == " " else block[:_HEAD].rsplit(" ", 1)[0]
    tail = block[-_TAIL:] if block[-_TAIL - 1] == " " else block[-_TAIL:].split(" ", 1)[-1]
    return f"{head.rstrip()} … {tail.lstrip()}"


def _where(finding: dict) -> str:
    span = _span(finding)
    return f"lines {finding['line']}-{finding['line'] + span - 1}" if span > 1 else f"line {finding['line']}"


def _message(path: Path, lines: list[str], findings: list[dict]) -> str:
    out = [f"devkit: the edit to {path.name} adds what the conventions forbid:"]
    for finding in findings[:_SHOWN]:
        label = _LABELS[finding["kind"]]
        if finding["kind"] == "doc_lines":
            label = f"docstring of {finding['lines']} lines"
        if finding["kind"] == "doc_long":
            label = f"docstring of {finding['chars']} characters"
        if finding["kind"] == "doc_repeats_name" and finding.get("name"):
            label += f" ({finding['name']})"
        out.append(f"- {_where(finding)}, {label}: {_excerpt(lines, finding)}")
    if len(findings) > _SHOWN:
        out.append(f"- and {len(findings) - _SHOWN} more")
    out.append(
        "Remove them: no comments, and a docstring is one descriptive line under 100 characters, only when needed."
    )
    return "\n".join(out)


def main() -> None:
    event = json.load(sys.stdin)
    tool = event.get("tool_name", "")
    tool_input = event.get("tool_input") or {}
    path = Path(str(tool_input.get("file_path") or ""))
    if tool not in ("Edit", "Write", "MultiEdit") or not comments.families(path.suffix) or not path.is_file():
        return
    old, new = _changed(tool, tool_input)
    fresh = _lines(new) - _lines(old) - _committed(path)
    if not fresh:
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    findings = [item for item in comments.review_text(text, path.suffix) if _introduced(lines, item, fresh)]
    if findings:
        sys.stdout.reconfigure(encoding="utf-8")
        print(json.dumps({"decision": "block", "reason": _message(path, lines, findings)}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
