from __future__ import annotations

import json
import tomllib
from importlib import util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PIN_SPEC = util.spec_from_file_location("pin", ROOT / "scripts" / "pin.py")
PIN = util.module_from_spec(PIN_SPEC)
PIN_SPEC.loader.exec_module(PIN)
AUTHOR = "jahirtrap"
REPOSITORY = "https://github.com/jahirxtrap/custom-mcps"
SERVERS = sorted(path.name for path in (ROOT / "servers").iterdir() if (path / "pyproject.toml").is_file())
MARKETPLACE = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))


def _project(name: str) -> dict:
    return tomllib.loads((ROOT / "servers" / name / "pyproject.toml").read_text(encoding="utf-8"))["project"]


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _entry(name: str) -> dict:
    return next(plugin for plugin in MARKETPLACE["plugins"] if plugin["name"] == name)


def test_marketplace_lists_every_server_once():
    assert sorted(plugin["name"] for plugin in MARKETPLACE["plugins"]) == SERVERS
    assert MARKETPLACE["name"] == "custom-mcps"
    assert MARKETPLACE["owner"]["name"] == AUTHOR


@pytest.mark.parametrize("name", SERVERS)
def test_plugin_manifest_matches_its_server(name):
    manifest = _read_json(ROOT / "servers" / name / ".claude-plugin" / "plugin.json")
    entry = _entry(name)

    assert manifest["name"] == name
    assert manifest["version"] == entry["version"] == _project(name)["version"]
    assert manifest["description"] == entry["description"]
    assert manifest["keywords"] == entry["tags"]
    assert manifest["author"]["name"] == AUTHOR
    assert manifest["repository"] == REPOSITORY
    assert manifest["homepage"] == f"{REPOSITORY}/tree/master/servers/{name}"
    assert entry["source"] == f"./servers/{name}"


@pytest.mark.parametrize("name", SERVERS)
def test_plugin_launches_its_installed_copy(name):
    launched = _read_json(ROOT / "servers" / name / ".mcp.json")["mcpServers"]
    script = next(iter(_project(name)["scripts"]))
    installed = "${CLAUDE_PLUGIN_ROOT}"

    constraints = f"{installed}/{PIN.CONSTRAINTS}"

    assert launched == {name: {"command": "uvx", "args": ["--from", installed, "--constraints", constraints, script]}}


@pytest.mark.parametrize("name", SERVERS)
def test_plugin_needs_nothing_outside_its_folder(name):
    server = ROOT / "servers" / name
    tool = tomllib.loads((server / "pyproject.toml").read_text(encoding="utf-8"))["tool"]

    assert "sources" not in tool.get("uv", {})
    assert all((server / package).is_dir() for package in tool["hatch"]["build"]["targets"]["wheel"]["packages"])


@pytest.mark.parametrize("name", SERVERS)
def test_plugin_pins_what_the_lock_pins(name):
    server = ROOT / "servers" / name

    assert (server / PIN.CONSTRAINTS).read_text(encoding="utf-8") == PIN.pinned(server)