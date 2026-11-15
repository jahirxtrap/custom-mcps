from __future__ import annotations

import json
from importlib import util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SETUP_SPEC = util.spec_from_file_location("study_setup", ROOT / "servers" / "study" / "setup.py")
SETUP = util.module_from_spec(SETUP_SPEC)
SETUP_SPEC.loader.exec_module(SETUP)


def test_workspace_registers_no_server_of_its_own(tmp_path):
    SETUP.write_mcp_json(tmp_path)
    assert not (tmp_path / ".mcp.json").exists()


def test_workspace_mcp_json_lists_only_the_cloned_video_audio(tmp_path):
    server = tmp_path / "external" / "video-audio-mcp" / "server.py"
    server.parent.mkdir(parents=True)
    server.write_text("", encoding="utf-8")
    SETUP.write_mcp_json(tmp_path)
    servers = json.loads((tmp_path / ".mcp.json").read_text(encoding="utf-8"))["mcpServers"]
    assert list(servers) == ["video-audio"]
    assert servers["video-audio"]["args"][-1] == "server.py"


def test_warming_starts_each_bundled_server_once_and_skips_the_plugin_own(monkeypatch):
    started = []

    def fake_run(command, **kwargs):
        started.append(command)
        assert kwargs["stdin"] is SETUP.subprocess.DEVNULL

    monkeypatch.setattr(SETUP.subprocess, "run", fake_run)
    monkeypatch.setattr(SETUP.shutil, "which", lambda name: f"/usr/bin/{name}")
    SETUP.warm_bundled_servers()
    assert [command[0] for command in started] == ["/usr/bin/npx", "/usr/bin/uvx"]
    assert not any(SETUP.PLUGIN_ROOT_VAR in arg for command in started for arg in command)


def test_env_file_keeps_only_recorded_values(tmp_path):
    path = tmp_path / ".env"
    SETUP.write_env(path, {"CHROME_PATH": "/opt/chrome", "EMPTY": ""})
    assert SETUP.read_env(path) == {"CHROME_PATH": "/opt/chrome"}
    assert path.read_text(encoding="utf-8").startswith("# Values the study setup records")
