import json
import random
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

from config import DB_PATH

COLOR_PALETTE = [
    {"fg": "#f8f8f2", "bg": "#1a1a2e"},
    {"fg": "#e0e0e0", "bg": "#0d3b66"},
    {"fg": "#f5f5dc", "bg": "#2d1b69"},
    {"fg": "#e8e8e8", "bg": "#1b4332"},
    {"fg": "#fff8e7", "bg": "#4a1942"},
    {"fg": "#f0f0f0", "bg": "#3d0c02"},
    {"fg": "#dcdcaa", "bg": "#1e1e3f"},
    {"fg": "#c8e6c9", "bg": "#0a2f1f"},
    {"fg": "#ffe0b2", "bg": "#3e1c00"},
    {"fg": "#b3e5fc", "bg": "#0a1929"},
    {"fg": "#f8bbd0", "bg": "#2a0a1b"},
    {"fg": "#d1c4e9", "bg": "#1a0a2e"},
    {"fg": "#ffccbc", "bg": "#1b0000"},
    {"fg": "#c5cae9", "bg": "#0d1b2a"},
    {"fg": "#dcedc8", "bg": "#1a2e05"},
]


class RepoGroupCreate(BaseModel):
    name: str
    repos: list[str]


class RepoGroupUpdate(BaseModel):
    name: str
    repos: list[str]


class RepoGroup(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    repos: list[str] = Field(default_factory=list)
    created_at: str = ""


class TaskTerminal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    pid: int
    kind: str = "original"  # "original" or "shell"
    created_at: str = ""


class TaskCreate(BaseModel):
    title: str
    repos: list[str]


class TaskStatusUpdate(BaseModel):
    status: str


class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    status: str = "not_started"
    repos: list[str] = Field(default_factory=list)
    par_label: str = ""
    tmux_session: Optional[str] = None
    ghostty_pid: Optional[int] = None
    color_fg: str = ""
    color_bg: str = ""
    created_at: str = ""
    updated_at: str = ""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'not_started',
            repos TEXT NOT NULL DEFAULT '[]',
            par_label TEXT NOT NULL,
            tmux_session TEXT,
            ghostty_pid INTEGER,
            color_fg TEXT NOT NULL,
            color_bg TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS task_terminals (
            id TEXT PRIMARY KEY,
            task_id TEXT NOT NULL,
            pid INTEGER NOT NULL,
            kind TEXT NOT NULL DEFAULT 'original',
            created_at TEXT NOT NULL,
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS repo_groups (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            repos TEXT NOT NULL DEFAULT '[]',
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


# --- Repo Groups ---

def _row_to_repo_group(row: sqlite3.Row) -> RepoGroup:
    d = dict(row)
    d["repos"] = json.loads(d["repos"])
    return RepoGroup(**d)


def create_repo_group(data: RepoGroupCreate) -> RepoGroup:
    now = _now()
    group = RepoGroup(name=data.name, repos=data.repos, created_at=now)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO repo_groups (id, name, repos, created_at) VALUES (?, ?, ?, ?)",
        (group.id, group.name, json.dumps(group.repos), group.created_at),
    )
    conn.commit()
    conn.close()
    return group


def get_all_repo_groups() -> list[RepoGroup]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM repo_groups ORDER BY name").fetchall()
    conn.close()
    return [_row_to_repo_group(r) for r in rows]


def update_repo_group(group_id: str, data: RepoGroupUpdate) -> Optional[RepoGroup]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        "UPDATE repo_groups SET name = ?, repos = ? WHERE id = ?",
        (data.name, json.dumps(data.repos), group_id),
    )
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        return None
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM repo_groups WHERE id = ?", (group_id,)).fetchone()
    conn.close()
    return _row_to_repo_group(row) if row else None


def delete_repo_group(group_id: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("DELETE FROM repo_groups WHERE id = ?", (group_id,))
    conn.commit()
    conn.close()
    return cur.rowcount > 0


# --- Tasks ---

def _row_to_task(row: sqlite3.Row) -> Task:
    d = dict(row)
    d["repos"] = json.loads(d["repos"])
    return Task(**d)


def _pick_color() -> dict:
    return random.choice(COLOR_PALETTE)


def create_task(data: TaskCreate) -> Task:
    color = _pick_color()
    label = data.title.lower().replace(" ", "-")
    # Ensure label uniqueness by appending short uuid suffix
    label = f"{label}-{uuid.uuid4().hex[:6]}"
    now = _now()
    task = Task(
        title=data.title,
        repos=data.repos,
        par_label=label,
        color_fg=color["fg"],
        color_bg=color["bg"],
        created_at=now,
        updated_at=now,
    )
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """INSERT INTO tasks (id, title, status, repos, par_label, tmux_session, ghostty_pid,
           color_fg, color_bg, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            task.id,
            task.title,
            task.status,
            json.dumps(task.repos),
            task.par_label,
            task.tmux_session,
            task.ghostty_pid,
            task.color_fg,
            task.color_bg,
            task.created_at,
            task.updated_at,
        ),
    )
    conn.commit()
    conn.close()
    return task


def get_all_tasks() -> list[Task]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()
    conn.close()
    return [_row_to_task(r) for r in rows]


def get_task(task_id: str) -> Optional[Task]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    return _row_to_task(row) if row else None


def update_task(task_id: str, **kwargs) -> Optional[Task]:
    kwargs["updated_at"] = _now()
    if "repos" in kwargs:
        kwargs["repos"] = json.dumps(kwargs["repos"])
    sets = ", ".join(f"{k} = ?" for k in kwargs)
    vals = list(kwargs.values()) + [task_id]
    conn = sqlite3.connect(DB_PATH)
    conn.execute(f"UPDATE tasks SET {sets} WHERE id = ?", vals)
    conn.commit()
    conn.close()
    return get_task(task_id)


def delete_task(task_id: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM task_terminals WHERE task_id = ?", (task_id,))
    cur = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return cur.rowcount > 0


# --- Task Terminals ---

def _row_to_terminal(row: sqlite3.Row) -> TaskTerminal:
    return TaskTerminal(**dict(row))


def create_terminal(task_id: str, pid: int, kind: str = "original") -> TaskTerminal:
    now = _now()
    term = TaskTerminal(task_id=task_id, pid=pid, kind=kind, created_at=now)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO task_terminals (id, task_id, pid, kind, created_at) VALUES (?, ?, ?, ?, ?)",
        (term.id, term.task_id, term.pid, term.kind, term.created_at),
    )
    conn.commit()
    conn.close()
    return term


def get_terminals_for_task(task_id: str) -> list[TaskTerminal]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM task_terminals WHERE task_id = ? ORDER BY created_at",
        (task_id,),
    ).fetchall()
    conn.close()
    return [_row_to_terminal(r) for r in rows]


def get_terminal(terminal_id: str) -> Optional[TaskTerminal]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM task_terminals WHERE id = ?", (terminal_id,)).fetchone()
    conn.close()
    return _row_to_terminal(row) if row else None


def delete_terminal(terminal_id: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("DELETE FROM task_terminals WHERE id = ?", (terminal_id,))
    conn.commit()
    conn.close()
    return cur.rowcount > 0
