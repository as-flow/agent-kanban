import importlib
import json
import subprocess

import pytest

import par_manager


@pytest.fixture(autouse=True)
def reload_par_manager():
    importlib.reload(par_manager)
    yield


def _write_state(state_path, label: str, workspace_path: str, session_name: str):
    state_path.write_text(json.dumps({
        "sessions": {
            label: {
                "label": label,
                "session_type": "workspace",
                "repository_path": workspace_path,
                "worktree_path": workspace_path,
                "tmux_session_name": session_name,
            }
        }
    }))


def test_ensure_tmux_session_recreates_dead_workspace_session(tmp_path, monkeypatch):
    label = "magic-mode"
    workspace_path = tmp_path / "workspace"
    workspace_path.mkdir()
    state_path = tmp_path / "global_state.json"
    _write_state(state_path, label, str(workspace_path), "par-ws-saved")

    calls = []

    def fake_run(cmd: list[str], check: bool = True):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(par_manager, "_par_state_path", lambda: state_path)
    monkeypatch.setattr(par_manager, "discover_tmux_session", lambda _label: "par-ws-discovered")
    monkeypatch.setattr(par_manager, "is_tmux_session_alive", lambda _session_name: False)
    monkeypatch.setattr(par_manager, "_run", fake_run)

    session_name = par_manager.ensure_tmux_session(label, "par-ws-stale", create=True)

    assert session_name == "par-ws-saved"
    assert calls == [["tmux", "new-session", "-d", "-s", "par-ws-saved", "-c", str(workspace_path)]]


def test_ensure_tmux_session_returns_live_session_without_recreating(tmp_path, monkeypatch):
    label = "magic-mode"
    workspace_path = tmp_path / "workspace"
    workspace_path.mkdir()
    state_path = tmp_path / "global_state.json"
    _write_state(state_path, label, str(workspace_path), "par-ws-saved")

    monkeypatch.setattr(par_manager, "_par_state_path", lambda: state_path)
    monkeypatch.setattr(par_manager, "discover_tmux_session", lambda _label: "par-ws-discovered")
    monkeypatch.setattr(par_manager, "is_tmux_session_alive", lambda session_name: session_name == "par-ws-saved")

    def fail_run(cmd: list[str], check: bool = True):
        raise AssertionError(f"_run should not be called: {cmd}")

    monkeypatch.setattr(par_manager, "_run", fail_run)

    session_name = par_manager.ensure_tmux_session(label, "par-ws-stale", create=True)

    assert session_name == "par-ws-saved"


def test_ensure_tmux_session_raises_when_workspace_missing(tmp_path, monkeypatch):
    label = "magic-mode"
    state_path = tmp_path / "global_state.json"
    _write_state(state_path, label, str(tmp_path / "missing-workspace"), "par-ws-saved")

    monkeypatch.setattr(par_manager, "_par_state_path", lambda: state_path)
    monkeypatch.setattr(par_manager, "discover_tmux_session", lambda _label: "par-ws-discovered")
    monkeypatch.setattr(par_manager, "is_tmux_session_alive", lambda _session_name: False)

    with pytest.raises(FileNotFoundError, match="Workspace directory not found"):
        par_manager.ensure_tmux_session(label, "par-ws-stale", create=True)
