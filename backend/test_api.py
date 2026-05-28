"""Integration tests for the Agent Kanban API.

Run with: python -m pytest test_api.py -v
"""

import os
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

os.environ["REPOS_DIRECTORY"] = "/tmp/test-repos"
os.environ["DROID_AUTO_LEVEL"] = "medium"

import par_manager  # noqa: E402
import terminal_manager  # noqa: E402
from main import app  # noqa: E402
from models import init_db  # noqa: E402

client = TestClient(app)


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    db = tmp_path / "kanban.db"
    monkeypatch.setattr("models.DB_PATH", db)
    init_db()
    yield


@pytest.fixture(autouse=True)
def mock_par():
    par_manager.workspace_start = MagicMock(return_value="par-ws-test-abc123")
    par_manager.workspace_rm = MagicMock()
    par_manager.send_command = MagicMock()
    par_manager.get_pane_command = MagicMock(return_value="droid")
    par_manager.is_tmux_session_alive = MagicMock(return_value=True)
    par_manager.ensure_tmux_session = MagicMock(return_value="par-ws-test-abc123")
    par_manager.standalone_session_start = MagicMock(return_value="kanban-test-abc123")
    par_manager.ensure_standalone_session = MagicMock(return_value="kanban-test-abc123")
    par_manager.kill_tmux_session = MagicMock()
    par_manager.configure_tmux_session = MagicMock()
    par_manager.get_workspace_path = MagicMock(return_value="/tmp/test-ws")
    yield par_manager


@pytest.fixture(autouse=True)
def mock_terminal():
    terminal_manager.launch = MagicMock(return_value=12345)
    terminal_manager.launch_shell = MagicMock(return_value=12346)
    terminal_manager.is_alive = MagicMock(return_value=True)
    terminal_manager.focus_by_pid = MagicMock()
    terminal_manager.kill = MagicMock()
    yield terminal_manager


def test_create_task():
    resp = client.post("/api/tasks", json={"title": "Add auth", "repos": ["backend"]})
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Add auth"
    assert data["status"] == "not_started"
    assert data["repos"] == ["backend"]
    assert data["color_fg"].startswith("#")
    assert data["color_bg"].startswith("#")


def test_create_task_no_repos():
    resp = client.post("/api/tasks", json={"title": "Triage inbox", "repos": []})
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Triage inbox"
    assert data["repos"] == []


def test_list_tasks():
    client.post("/api/tasks", json={"title": "Task 1", "repos": ["a"]})
    client.post("/api/tasks", json={"title": "Task 2", "repos": ["b"]})
    resp = client.get("/api/tasks")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_move_not_started_to_in_progress(mock_par, mock_terminal):
    resp = client.post("/api/tasks", json={"title": "Start me", "repos": ["repo1"]})
    task_id = resp.json()["id"]

    resp = client.patch(f"/api/tasks/{task_id}/status", json={"status": "in_progress"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"
    mock_par.workspace_start.assert_called_once()
    mock_par.configure_tmux_session.assert_called_once_with("par-ws-test-abc123")
    mock_terminal.launch.assert_called_once_with(
        "par-ws-test-abc123",
        "Start me [main]",
        resp.json()["color_fg"],
        resp.json()["color_bg"],
    )


def test_move_not_started_to_in_progress_no_repos(mock_par, mock_terminal):
    resp = client.post("/api/tasks", json={"title": "Start no repos", "repos": []})
    task = resp.json()

    resp = client.patch(f"/api/tasks/{task['id']}/status", json={"status": "in_progress"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"
    assert resp.json()["tmux_session"] == "kanban-test-abc123"
    mock_par.workspace_start.assert_not_called()
    mock_par.standalone_session_start.assert_called_once_with(task["par_label"], "/tmp/test-repos")
    mock_par.configure_tmux_session.assert_called_once_with("kanban-test-abc123")
    mock_terminal.launch.assert_called_once_with(
        "kanban-test-abc123",
        "Start no repos [main]",
        task["color_fg"],
        task["color_bg"],
    )


def test_invalid_transition():
    resp = client.post("/api/tasks", json={"title": "Skip", "repos": ["x"]})
    task_id = resp.json()["id"]

    resp = client.patch(f"/api/tasks/{task_id}/status", json={"status": "done"})
    assert resp.status_code == 400


def test_move_to_done_kills_terminal(mock_terminal):
    resp = client.post("/api/tasks", json={"title": "Finish", "repos": ["r"]})
    task_id = resp.json()["id"]

    client.patch(f"/api/tasks/{task_id}/status", json={"status": "in_progress"})
    client.patch(f"/api/tasks/{task_id}/status", json={"status": "in_review"})
    resp = client.patch(f"/api/tasks/{task_id}/status", json={"status": "done"})
    assert resp.status_code == 200
    mock_terminal.kill.assert_called()


def test_move_done_to_in_progress_restores_session(mock_par, mock_terminal):
    resp = client.post("/api/tasks", json={"title": "Restore", "repos": ["r"]})
    task = resp.json()
    task_id = task["id"]

    client.patch(f"/api/tasks/{task_id}/status", json={"status": "in_progress"})
    client.patch(f"/api/tasks/{task_id}/status", json={"status": "in_review"})
    client.patch(f"/api/tasks/{task_id}/status", json={"status": "done"})

    mock_par.ensure_tmux_session.return_value = "par-ws-restored"
    mock_terminal.launch.reset_mock()
    mock_par.configure_tmux_session.reset_mock()

    resp = client.patch(f"/api/tasks/{task_id}/status", json={"status": "in_progress"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"
    assert resp.json()["tmux_session"] == "par-ws-restored"
    mock_par.ensure_tmux_session.assert_called_with(task["par_label"], "par-ws-test-abc123", create=True)
    mock_par.configure_tmux_session.assert_called_once_with("par-ws-restored")
    mock_terminal.launch.assert_called_once_with(
        "par-ws-restored",
        "Restore [main]",
        task["color_fg"],
        task["color_bg"],
    )


def test_delete_task(mock_par, mock_terminal):
    resp = client.post("/api/tasks", json={"title": "Delete me", "repos": ["r"]})
    task_id = resp.json()["id"]

    resp = client.delete(f"/api/tasks/{task_id}")
    assert resp.status_code == 200
    mock_par.workspace_rm.assert_called_once()

    resp = client.get("/api/tasks")
    assert len(resp.json()) == 0


def test_delete_task_no_repos(mock_par, mock_terminal):
    resp = client.post("/api/tasks", json={"title": "Delete no repos", "repos": []})
    task_id = resp.json()["id"]
    client.patch(f"/api/tasks/{task_id}/status", json={"status": "in_progress"})

    resp = client.delete(f"/api/tasks/{task_id}")
    assert resp.status_code == 200
    mock_terminal.kill.assert_called()
    mock_par.workspace_rm.assert_not_called()
    mock_par.kill_tmux_session.assert_called_once_with("kanban-test-abc123")


def test_agent_status():
    resp = client.post("/api/tasks", json={"title": "Check", "repos": ["r"]})
    task_id = resp.json()["id"]
    client.patch(f"/api/tasks/{task_id}/status", json={"status": "in_progress"})

    resp = client.get(f"/api/tasks/{task_id}/agent-status")
    assert resp.status_code == 200
    assert resp.json()["running"] is True


def test_list_terminals_after_start(mock_terminal):
    resp = client.post("/api/tasks", json={"title": "Terminals", "repos": ["r"]})
    task_id = resp.json()["id"]
    client.patch(f"/api/tasks/{task_id}/status", json={"status": "in_progress"})

    resp = client.get(f"/api/tasks/{task_id}/terminals")
    assert resp.status_code == 200
    terms = resp.json()
    assert len(terms) == 1
    assert terms[0]["kind"] == "original"


def test_focus_terminal(mock_terminal):
    resp = client.post("/api/tasks", json={"title": "Focus", "repos": ["r"]})
    task_id = resp.json()["id"]
    client.patch(f"/api/tasks/{task_id}/status", json={"status": "in_progress"})

    terms = client.get(f"/api/tasks/{task_id}/terminals").json()
    term_id = terms[0]["id"]

    resp = client.post(f"/api/tasks/{task_id}/terminals/{term_id}/focus")
    assert resp.status_code == 200
    mock_terminal.focus_by_pid.assert_called()


def test_focus_terminal_recovers_dead_original_terminal(mock_terminal, mock_par):
    resp = client.post("/api/tasks", json={"title": "Recover", "repos": ["r"]})
    task = resp.json()
    task_id = task["id"]
    client.patch(f"/api/tasks/{task_id}/status", json={"status": "in_progress"})

    mock_terminal.is_alive.return_value = False
    mock_par.ensure_tmux_session.return_value = "par-ws-recovered"
    mock_par.configure_tmux_session.reset_mock()

    terms = client.get(f"/api/tasks/{task_id}/terminals").json()
    term_id = terms[0]["id"]

    resp = client.post(f"/api/tasks/{task_id}/terminals/{term_id}/focus")
    assert resp.status_code == 200
    mock_par.ensure_tmux_session.assert_called_with(task["par_label"], "par-ws-test-abc123", create=True)
    mock_par.configure_tmux_session.assert_called_once_with("par-ws-recovered")
    mock_terminal.launch.assert_called_with(
        "par-ws-recovered",
        "Recover [main]",
        task["color_fg"],
        task["color_bg"],
    )


def test_add_terminal(mock_terminal, mock_par):
    par_manager.get_workspace_path = MagicMock(return_value="/tmp/ws")
    resp = client.post("/api/tasks", json={"title": "Add", "repos": ["r"]})
    task_id = resp.json()["id"]
    client.patch(f"/api/tasks/{task_id}/status", json={"status": "in_progress"})

    resp = client.post(f"/api/tasks/{task_id}/terminals")
    assert resp.status_code == 201
    assert resp.json()["kind"] == "shell"
    mock_terminal.launch_shell.assert_called()

    terms = client.get(f"/api/tasks/{task_id}/terminals").json()
    assert len(terms) == 2


def test_focus_shell_terminal_reopens_from_workspace(mock_terminal, mock_par):
    par_manager.get_workspace_path = MagicMock(return_value="/tmp/ws")
    resp = client.post("/api/tasks", json={"title": "Shell reopen", "repos": ["r"]})
    task = resp.json()
    task_id = task["id"]
    client.patch(f"/api/tasks/{task_id}/status", json={"status": "in_progress"})
    client.post(f"/api/tasks/{task_id}/terminals")

    mock_terminal.is_alive.return_value = False

    terms = client.get(f"/api/tasks/{task_id}/terminals").json()
    shell_term = [t for t in terms if t["kind"] == "shell"][0]

    resp = client.post(f"/api/tasks/{task_id}/terminals/{shell_term['id']}/focus")
    assert resp.status_code == 200
    mock_terminal.launch_shell.assert_called_with(
        "/tmp/ws",
        shell_term["title"],
        task["color_fg"],
        task["color_bg"],
    )


def test_focus_terminal_returns_400_when_workspace_missing(mock_terminal, mock_par):
    resp = client.post("/api/tasks", json={"title": "Missing ws", "repos": ["r"]})
    task_id = resp.json()["id"]
    client.patch(f"/api/tasks/{task_id}/status", json={"status": "in_progress"})

    mock_terminal.is_alive.return_value = False
    mock_par.ensure_tmux_session.side_effect = FileNotFoundError("Workspace directory not found")

    terms = client.get(f"/api/tasks/{task_id}/terminals").json()
    term_id = terms[0]["id"]

    resp = client.post(f"/api/tasks/{task_id}/terminals/{term_id}/focus")
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Workspace directory not found"


def test_delete_terminal_not_original(mock_terminal, mock_par):
    par_manager.get_workspace_path = MagicMock(return_value="/tmp/ws")
    resp = client.post("/api/tasks", json={"title": "Del", "repos": ["r"]})
    task_id = resp.json()["id"]
    client.patch(f"/api/tasks/{task_id}/status", json={"status": "in_progress"})

    client.post(f"/api/tasks/{task_id}/terminals")
    terms = client.get(f"/api/tasks/{task_id}/terminals").json()
    shell_term = [t for t in terms if t["kind"] == "shell"][0]

    resp = client.delete(f"/api/tasks/{task_id}/terminals/{shell_term['id']}")
    assert resp.status_code == 200

    terms = client.get(f"/api/tasks/{task_id}/terminals").json()
    assert len(terms) == 1
    assert terms[0]["kind"] == "original"


def test_cannot_delete_original_terminal(mock_terminal):
    resp = client.post("/api/tasks", json={"title": "Orig", "repos": ["r"]})
    task_id = resp.json()["id"]
    client.patch(f"/api/tasks/{task_id}/status", json={"status": "in_progress"})

    terms = client.get(f"/api/tasks/{task_id}/terminals").json()
    orig_id = terms[0]["id"]

    resp = client.delete(f"/api/tasks/{task_id}/terminals/{orig_id}")
    assert resp.status_code == 400


def test_get_settings():
    resp = client.get("/api/settings")
    assert resp.status_code == 200
    data = resp.json()
    assert "terminal_app" in data
    assert "terminal_path" in data
    assert "repos_directory" in data


def test_update_settings():
    resp = client.put("/api/settings", json={"terminal_app": "kitty", "repos_directory": "/tmp/repos"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["terminal_app"] == "kitty"
    assert data["repos_directory"] == "/tmp/repos"

    resp = client.get("/api/settings")
    assert resp.json()["terminal_app"] == "kitty"


def test_update_settings_partial():
    resp = client.put("/api/settings", json={"terminal_path": "/usr/local/bin/ghostty"})
    assert resp.status_code == 200
    assert resp.json()["terminal_path"] == "/usr/local/bin/ghostty"
