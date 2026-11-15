"""Spelling and grammar through a local LanguageTool: a running server by URL, or its command line."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

from .markdown import plain_text

URL_VAR = "LANGUAGETOOL_URL"
HOME_VAR = "LANGUAGETOOL_HOME"
AUTO = "auto"
_JAR = "languagetool-commandline.jar"
_WRAPPER = "languagetool"
_CHECK = "/v2/check"
_TIMEOUT = 300
_REPLACEMENTS = 5


def backend() -> dict[str, Any]:
    url = os.environ.get(URL_VAR, "").strip()
    if url:
        return {"kind": "server", "url": url.rstrip("/")}
    home = os.environ.get(HOME_VAR, "").strip()
    java = shutil.which("java")
    if home and java and (Path(home) / _JAR).exists():
        return {"kind": "commandline", "command": [java, "-jar", str(Path(home) / _JAR)]}
    wrapper = shutil.which(_WRAPPER)
    if wrapper:
        return {"kind": "commandline", "command": [wrapper]}
    return {}


def _missing() -> str:
    home = os.environ.get(HOME_VAR, "").strip()
    if home and not shutil.which("java"):
        return f"{HOME_VAR} is set but java is not on PATH; LanguageTool needs Java 17 or later"
    if home:
        return f"{HOME_VAR} points to {home}, which has no {_JAR}"
    return (
        f"LanguageTool not found: set {URL_VAR} to a running server or {HOME_VAR} to its unzipped "
        "folder; see toolkit('grammar')"
    )


def _via_server(url: str, text: str, language: str) -> dict[str, Any]:
    data = urllib.parse.urlencode({"text": text, "language": language}).encode()
    with urllib.request.urlopen(urllib.request.Request(f"{url}{_CHECK}", data=data), timeout=_TIMEOUT) as response:
        return json.loads(response.read().decode("utf-8"))


def _via_commandline(command: list[str], text: str, language: str) -> dict[str, Any]:
    with tempfile.NamedTemporaryFile("w", suffix=".txt", encoding="utf-8", delete=False) as handle:
        handle.write(text)
        path = Path(handle.name)
    flags = ["-adl"] if language == AUTO else ["-l", language]
    try:
        done = subprocess.run(
            [*command, *flags, "--json", "--clean-overlapping", "-c", "utf-8", str(path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdin=subprocess.DEVNULL,
            timeout=_TIMEOUT,
        )
    finally:
        path.unlink(missing_ok=True)
    if done.returncode != 0:
        detail = done.stderr.strip().splitlines()
        raise RuntimeError(detail[-1] if detail else f"languagetool exited with {done.returncode}")
    return json.loads(done.stdout)


def _position(text: str, offset: int) -> tuple[int, int]:
    line_start = text.rfind("\n", 0, offset) + 1
    return text.count("\n", 0, offset) + 1, offset - line_start + 1


def hits(text: str, plain: str, origins: list[int], matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    kept: list[dict[str, Any]] = []
    covered = 0
    for match in sorted(matches, key=lambda item: (item["offset"], item["length"])):
        start, stop = match["offset"], match["offset"] + match["length"]
        if start < covered or stop <= start or stop > len(origins):
            continue
        covered = stop
        line, column = _position(text, origins[start])
        kept.append(
            {
                "line": line,
                "column": column,
                "text": plain[start:stop],
                "message": match["message"],
                "replacements": [item["value"] for item in match.get("replacements", [])][:_REPLACEMENTS],
                "rule": match["rule"]["id"],
                "category": match["rule"]["category"]["id"],
            }
        )
    return kept


def grammar_check(text: str, language: str) -> dict[str, Any]:
    found = backend()
    if not found:
        return {"available": False, "reason": _missing()}
    plain, origins = plain_text(text)
    try:
        if found["kind"] == "server":
            result = _via_server(found["url"], plain, language)
        else:
            result = _via_commandline(found["command"], plain, language)
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
        return {"available": True, "backend": found["kind"], "error": str(error)}
    findings = hits(text, plain, origins, result.get("matches", []))
    by_category = dict(Counter(hit["category"] for hit in findings))
    detected = result.get("language", {}).get("code", language)
    version = result.get("software", {}).get("version", "")
    return {
        "available": True,
        "backend": found["kind"],
        "language": detected,
        "languagetool": version,
        "total_hits": len(findings),
        "by_category": by_category,
        "summary": f"{len(findings)} findings across {len(by_category)} categories ({detected})",
        "hits": findings,
    }
