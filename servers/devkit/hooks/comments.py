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
_GIT_TIMEOUT = 5
_LABELS = {
    "comment": "comment",
    "doc_lines": "docstring over one line",
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


def _message(path: Path, findings: list[dict]) -> str:
    lines = [f"devkit: the edit to {path.name} adds what the conventions forbid:"]
    for finding in findings[:_SHOWN]:
        label = _LABELS[finding["kind"]]
        if finding["kind"] == "doc_lines":
            label = f"docstring of {finding['lines']} lines"
        if finding.get("name") and finding["kind"] == "doc_repeats_name":
            label += f" ({finding['name']})"
        lines.append(f"- line {finding['line']}, {label}: {finding['text']}")
    if len(findings) > _SHOWN:
        lines.append(f"- and {len(findings) - _SHOWN} more")
    lines.append(
        "No comments; a docstring is one purely descriptive line, only when a constraint cannot be expressed "
        "in code. Remove them; the why belongs in the MR or the chat."
    )
    return "\n".join(lines)


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
    findings = [finding for finding in comments.review_text(text, path.suffix) if finding["text"] in fresh]
    if findings:
        sys.stdout.reconfigure(encoding="utf-8")
        print(json.dumps({"decision": "block", "reason": _message(path, findings)}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
