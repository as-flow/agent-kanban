import logging
import subprocess
import uuid as _uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import config
import terminal_manager
import par_manager
from models import (
    RepoGroup,
    RepoGroupCreate,
    RepoGroupUpdate,
    Task,
    TaskCreate,
    TaskStatusUpdate,
    TaskTerminal,
    create_repo_group,
    create_task,
    create_terminal,
    delete_repo_group,
    delete_task,
    delete_terminal,
    get_all_repo_groups,
    get_all_tasks,
    get_task,
    get_terminal,
    get_terminals_for_task,
    init_db,
    update_repo_group,
    update_task,
)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    config.load_settings_from_db()
    yield


app = FastAPI(title="Agent Kanban", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

VALID_TRANSITIONS = {
    "not_started": ["in_progress"],
    "in_progress": ["in_review", "on_hold", "done"],
    "in_review": ["in_progress", "on_hold", "done"],
    "on_hold": ["in_progress", "in_review", "done"],
    "done": [],
}


@app.get("/api/repos")
def list_repos() -> list[str]:
    """List git repo directories inside the configured REPOS_DIRECTORY."""
    repos = _git_repos()
    if not repos and not Path(config.REPOS_DIRECTORY).is_dir():
        raise HTTPException(400, f"REPOS_DIRECTORY not found: {config.REPOS_DIRECTORY}")
    return [r.name for r in repos]


def _git_repos() -> list[Path]:
    base = Path(config.REPOS_DIRECTORY)
    if not base.is_dir():
        return []
    return sorted(d for d in base.iterdir() if d.is_dir() and (d / ".git").exists())


def _pull_one(repo_path: Path) -> dict:
    try:
        result = subprocess.run(
            ["git", "pull"], cwd=repo_path, capture_output=True, text=True, timeout=60,
        )
        return {
            "repo": repo_path.name,
            "ok": result.returncode == 0,
            "output": (result.stdout + result.stderr).strip(),
        }
    except Exception as exc:
        return {"repo": repo_path.name, "ok": False, "output": str(exc)}


@app.post("/api/repos/pull")
def pull_all_repos() -> list[dict]:
    repos = _git_repos()
    if not repos:
        raise HTTPException(400, f"No git repos found in {config.REPOS_DIRECTORY}")
    with ThreadPoolExecutor(max_workers=len(repos)) as pool:
        return list(pool.map(_pull_one, repos))


# --- Repo Groups ---

@app.get("/api/repo-groups")
def list_repo_groups() -> list[RepoGroup]:
    return get_all_repo_groups()


@app.post("/api/repo-groups", status_code=201)
def create_group(data: RepoGroupCreate) -> RepoGroup:
    return create_repo_group(data)


@app.put("/api/repo-groups/{group_id}")
def update_group(group_id: str, data: RepoGroupUpdate) -> RepoGroup:
    group = update_repo_group(group_id, data)
    if not group:
        raise HTTPException(404, "Repo group not found")
    return group


@app.delete("/api/repo-groups/{group_id}")
def remove_group(group_id: str):
    if not delete_repo_group(group_id):
        raise HTTPException(404, "Repo group not found")
    return {"ok": True}


# --- Settings ---

@app.get("/api/settings")
def get_settings():
    return config.get_settings()


@app.put("/api/settings")
def update_settings(data: dict):
    config.apply_settings(data)
    return config.get_settings()


# --- Tasks ---

@app.get("/api/tasks")
def list_tasks() -> list[Task]:
    return get_all_tasks()


@app.post("/api/tasks", status_code=201)
def create(data: TaskCreate) -> Task:
    return create_task(data)


@app.patch("/api/tasks/{task_id}/status")
def update_status(task_id: str, body: TaskStatusUpdate) -> Task:
    task = get_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")

    new_status = body.status
    if new_status not in VALID_TRANSITIONS.get(task.status, []):
        raise HTTPException(
            400,
            f"Cannot move from '{task.status}' to '{new_status}'. "
            f"Allowed: {VALID_TRANSITIONS.get(task.status, [])}",
        )

    if task.status == "not_started" and new_status == "in_progress":
        _transition_to_in_progress(task)
    elif new_status == "done":
        _transition_to_done(task)

    updated = update_task(task_id, status=new_status)
    if not updated:
        raise HTTPException(500, "Failed to update task")
    return updated


@app.delete("/api/tasks/done")
def remove_done_tasks():
    all_tasks = get_all_tasks()
    done_tasks = [t for t in all_tasks if t.status == "done"]
    for task in done_tasks:
        for term in get_terminals_for_task(task.id):
            terminal_manager.kill(term.pid)
        par_manager.workspace_rm(task.par_label)
        delete_task(task.id)
    return {"ok": True, "deleted": len(done_tasks)}


@app.delete("/api/tasks/{task_id}")
def remove_task(task_id: str):
    task = get_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    for term in get_terminals_for_task(task_id):
        terminal_manager.kill(term.pid)
    par_manager.workspace_rm(task.par_label)
    delete_task(task_id)
    return {"ok": True}


@app.get("/api/tasks/{task_id}/agent-status")
def agent_status(task_id: str) -> dict:
    task = get_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    session_name = par_manager.ensure_tmux_session(task.par_label, task.tmux_session, create=False)
    if not session_name or not par_manager.is_tmux_session_alive(session_name):
        return {"running": False, "command": ""}
    cmd = par_manager.get_pane_command(session_name)
    return {"running": "droid" in cmd.lower(), "command": cmd}


@app.get("/api/tasks/{task_id}/terminals")
def list_terminals(task_id: str) -> list[TaskTerminal]:
    task = get_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    terminals = get_terminals_for_task(task_id)
    for t in terminals:
        if not terminal_manager.is_alive(t.pid):
            t.pid = 0
    return terminals


@app.post("/api/tasks/{task_id}/terminals", status_code=201)
def add_terminal(task_id: str) -> TaskTerminal:
    task = get_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    ws_path = par_manager.get_workspace_path(task.par_label)
    if not ws_path:
        raise HTTPException(400, "Workspace directory not found")
    short_id = _uuid.uuid4().hex[:6]
    win_title = f"{task.title} [{short_id}]"
    pid = terminal_manager.launch_shell(ws_path, win_title, task.color_fg, task.color_bg)
    return create_terminal(task_id, pid, kind="shell", title=win_title)


@app.post("/api/tasks/{task_id}/terminals/{terminal_id}/focus")
def focus_terminal(task_id: str, terminal_id: str) -> dict:
    task = get_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    term = get_terminal(terminal_id)
    if not term or term.task_id != task_id:
        raise HTTPException(404, "Terminal not found")
    if terminal_manager.is_alive(term.pid):
        terminal_manager.focus_by_pid(term.pid)
    else:
        win_title = term.title or (f"{task.title} [main]" if term.kind == "original" else f"{task.title} [{term.id[:6]}]")
        if term.kind == "original":
            try:
                session_name = par_manager.ensure_tmux_session(
                    task.par_label, task.tmux_session, create=True,
                )
            except FileNotFoundError as exc:
                raise HTTPException(400, str(exc)) from exc
            if not session_name:
                raise HTTPException(400, "Task has no tmux session")
            if task.tmux_session != session_name:
                update_task(task.id, tmux_session=session_name)
            pid = terminal_manager.launch(
                session_name, win_title, task.color_fg, task.color_bg,
            )
        else:
            ws_path = par_manager.get_workspace_path(task.par_label)
            if not ws_path:
                raise HTTPException(400, "Workspace directory not found")
            pid = terminal_manager.launch_shell(ws_path, win_title, task.color_fg, task.color_bg)
        delete_terminal(terminal_id)
        create_terminal(task_id, pid, kind=term.kind, title=win_title)
    return {"ok": True}


@app.delete("/api/tasks/{task_id}/terminals/{terminal_id}")
def remove_terminal(task_id: str, terminal_id: str) -> dict:
    task = get_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    term = get_terminal(terminal_id)
    if not term or term.task_id != task_id:
        raise HTTPException(404, "Terminal not found")
    if term.kind == "original":
        raise HTTPException(400, "Cannot delete the original terminal")
    terminal_manager.kill(term.pid)
    delete_terminal(terminal_id)
    return {"ok": True}


def _transition_to_in_progress(task: Task):
    tmux_session = par_manager.workspace_start(task.par_label, task.repos)
    update_task(task.id, tmux_session=tmux_session)

    win_title = f"{task.title} [main]"
    pid = terminal_manager.launch(tmux_session, win_title, task.color_fg, task.color_bg)
    update_task(task.id, terminal_pid=pid)
    create_terminal(task.id, pid, kind="original", title=win_title)


def _transition_to_done(task: Task):
    for term in get_terminals_for_task(task.id):
        terminal_manager.kill(term.pid)
        delete_terminal(term.id)
    if task.terminal_pid:
        update_task(task.id, terminal_pid=None)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8420, reload=True)
