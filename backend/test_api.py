"""Integration tests for the Droid Kanban API.

Run with: python -m pytest test_api.py -v
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

os.environ["REPOS_DIRECTORY"] = "/tmp/test-repos"
os.environ["DROID_AUTO_LEVEL"] = "medium"

sys.modules.setdefault("par_manager", MagicMock())
sys.modules.setdefault("ghostty_manager", MagicMock())

import par_manager
import ghostty_manager
from main import app
from models import init_db, DB_PATH

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
    yield par_manager


@pytest.fixture(autouse=True)
def mock_ghostty():
    ghostty_manager.launch = MagicMock(return_value=12345)
    ghostty_manager.launch_shell = MagicMock(return_value=12346)
    ghostty_manager.is_alive = MagicMock(return_value=True)
    ghostty_manager.focus_by_title = MagicMock()
    ghostty_manager.kill = MagicMock()
    yield ghostty_manager


def test_create_task():
    resp = client.post("/api/tasks", json={"title": "Add auth", "repos": ["backend"]})
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Add auth"
    assert data["status"] == "not_started"
    assert data["repos"] == ["backend"]
    assert data["color_fg"].startswith("#")
    assert data["color_bg"].startswith("#")


def test_list_tasks():
    client.post("/api/tasks", json={"title": "Task 1", "repos": ["a"]})
    client.post("/api/tasks", json={"title": "Task 2", "repos": ["b"]})
    resp = client.get("/api/tasks")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_move_not_started_to_in_progress(mock_par, mock_ghostty):
    resp = client.post("/api/tasks", json={"title": "Start me", "repos": ["repo1"]})
    task_id = resp.json()["id"]

    resp = client.patch(f"/api/tasks/{task_id}/status", json={"status": "in_progress"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"
    mock_par.workspace_start.assert_called_once()
    mock_ghostty.launch.assert_called_once()


def test_invalid_transition():
    resp = client.post("/api/tasks", json={"title": "Skip", "repos": ["x"]})
    task_id = resp.json()["id"]

    resp = client.patch(f"/api/tasks/{task_id}/status", json={"status": "done"})
    assert resp.status_code == 400


def test_move_to_done_kills_ghostty(mock_ghostty):
    resp = client.post("/api/tasks", json={"title": "Finish", "repos": ["r"]})
    task_id = resp.json()["id"]

    client.patch(f"/api/tasks/{task_id}/status", json={"status": "in_progress"})
    client.patch(f"/api/tasks/{task_id}/status", json={"status": "in_review"})
    resp = client.patch(f"/api/tasks/{task_id}/status", json={"status": "done"})
    assert resp.status_code == 200
    mock_ghostty.kill.assert_called()


def test_delete_task(mock_par, mock_ghostty):
    resp = client.post("/api/tasks", json={"title": "Delete me", "repos": ["r"]})
    task_id = resp.json()["id"]

    resp = client.delete(f"/api/tasks/{task_id}")
    assert resp.status_code == 200
    mock_par.workspace_rm.assert_called_once()

    resp = client.get("/api/tasks")
    assert len(resp.json()) == 0


def test_agent_status():
    resp = client.post("/api/tasks", json={"title": "Check", "repos": ["r"]})
    task_id = resp.json()["id"]
    client.patch(f"/api/tasks/{task_id}/status", json={"status": "in_progress"})

    resp = client.get(f"/api/tasks/{task_id}/agent-status")
    assert resp.status_code == 200
    assert resp.json()["running"] is True


def test_list_terminals_after_start(mock_ghostty):
    resp = client.post("/api/tasks", json={"title": "Terminals", "repos": ["r"]})
    task_id = resp.json()["id"]
    client.patch(f"/api/tasks/{task_id}/status", json={"status": "in_progress"})

    resp = client.get(f"/api/tasks/{task_id}/terminals")
    assert resp.status_code == 200
    terms = resp.json()
    assert len(terms) == 1
    assert terms[0]["kind"] == "original"


def test_focus_terminal(mock_ghostty):
    resp = client.post("/api/tasks", json={"title": "Focus", "repos": ["r"]})
    task_id = resp.json()["id"]
    client.patch(f"/api/tasks/{task_id}/status", json={"status": "in_progress"})

    terms = client.get(f"/api/tasks/{task_id}/terminals").json()
    term_id = terms[0]["id"]

    resp = client.post(f"/api/tasks/{task_id}/terminals/{term_id}/focus")
    assert resp.status_code == 200
    mock_ghostty.focus_by_title.assert_called()


def test_add_terminal(mock_ghostty, mock_par):
    par_manager.get_workspace_path = MagicMock(return_value="/tmp/ws")
    resp = client.post("/api/tasks", json={"title": "Add", "repos": ["r"]})
    task_id = resp.json()["id"]
    client.patch(f"/api/tasks/{task_id}/status", json={"status": "in_progress"})

    resp = client.post(f"/api/tasks/{task_id}/terminals")
    assert resp.status_code == 201
    assert resp.json()["kind"] == "shell"
    mock_ghostty.launch_shell.assert_called()

    terms = client.get(f"/api/tasks/{task_id}/terminals").json()
    assert len(terms) == 2


def test_delete_terminal_not_original(mock_ghostty, mock_par):
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


def test_cannot_delete_original_terminal(mock_ghostty):
    resp = client.post("/api/tasks", json={"title": "Orig", "repos": ["r"]})
    task_id = resp.json()["id"]
    client.patch(f"/api/tasks/{task_id}/status", json={"status": "in_progress"})

    terms = client.get(f"/api/tasks/{task_id}/terminals").json()
    orig_id = terms[0]["id"]

    resp = client.delete(f"/api/tasks/{task_id}/terminals/{orig_id}")
    assert resp.status_code == 400
