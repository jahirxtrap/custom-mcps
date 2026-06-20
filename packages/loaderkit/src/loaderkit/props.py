"""Parse gradle.properties and the embedded Minecraft-version -> Java-version table."""
from __future__ import annotations

from pathlib import Path


def parse_properties(path: str | Path) -> dict[str, str]:
    """Parse a Java .properties file (key=value, # / ! comments) into a dict."""
    result: dict[str, str] = {}
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped[0] in "#!":
            continue
        if "=" in stripped:
            key, _, value = stripped.partition("=")
            result[key.strip()] = value.strip()
    return result


def parse_mc_version(version: str) -> tuple[int, ...]:
    """Turn a Minecraft version like '1.21.11' or '26.2' into a comparable int tuple."""
    parts: list[int] = []
    for piece in version.split("."):
        digits = "".join(ch for ch in piece if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def java_for_mc(version: str) -> int:
    """Return the Java major version expected for a Minecraft version."""
    v = parse_mc_version(version)
    if v >= (26, 1):
        return 25
    if v >= (1, 20, 5):
        return 21
    if v >= (1, 18):
        return 17
    if v >= (1, 17):
        return 16
    return 21
