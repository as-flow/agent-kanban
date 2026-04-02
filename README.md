# Agent Kanban

A visual Kanban board for managing AI agent tasks across [par](https://github.com/coplane/par) workspaces, with configurable terminal integration.

Each task gets its own isolated multi-repo workspace, a color-coded terminal window, and moves through four columns: **Not Started → In Progress → In Review → Done**.

## Features

- **4-column Kanban board** with drag-and-drop (forward-only transitions)
- **Par workspace management** — create multi-repo workspaces per task, cleaned up on delete
- **Multi-terminal support** — each task opens a color-coded, titled terminal window; supports multiple terminal windows per task via right-click context menu. Works with Ghostty, Kitty, Alacritty, WezTerm, iTerm2, and Terminal.app.
- **Repo groups** — save named collections of repos for quick selection when creating tasks
- **Parallel git pull** — pull all repos in one click
- **Agent status polling** — live running/stopped indicator on each tile
- **Searchable repo list** in the new task dialog

## Prerequisites

- An AI coding agent CLI (e.g. [Factory](https://docs.factory.ai/reference/cli-reference), [Claude Code](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview), etc.)
- [par](https://github.com/coplane/par) (`uv tool install par-cli`)
- A supported terminal emulator (macOS): [Ghostty](https://ghostty.org/), [Kitty](https://sw.kovidgoyal.net/kitty/), [Alacritty](https://alacritty.org/), [WezTerm](https://wezfurlong.org/wezterm/), [iTerm2](https://iterm2.com/), or Terminal.app
- tmux
- Python 3.12+
- Node.js 18+

## Setup

```bash
# Clone
git clone https://github.com/as-flow/agent-kanban.git
cd agent-kanban

# Configure
cp .env.example .env
# Edit .env to set REPOS_DIRECTORY to the directory containing your git repos

# Backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

## Running

Start both the backend and frontend:

```bash
# Terminal 1 — backend
cd backend
source .venv/bin/activate
python main.py
# Runs on http://localhost:8000

# Terminal 2 — frontend
cd frontend
npm run dev
# Runs on http://localhost:5173
```

Open http://localhost:5173 in your browser.

## Configuration

Create a `.env` file in the project root:

```
REPOS_DIRECTORY=/path/to/your/repos
TERMINAL_APP=ghostty
```

| Variable | Default | Description |
|---|---|---|
| `REPOS_DIRECTORY` | (required) | Directory containing your git repositories |
| `TERMINAL_APP` | `ghostty` | Terminal to use: `ghostty`, `kitty`, `alacritty`, `wezterm`, `iterm2`, `terminal` |
| `TERMINAL_PATH` | (auto-detected) | Override the terminal binary path |

## Usage

1. **Create a task** — click "+ New Task", enter a title, select repos (or a repo group)
2. **Start working** — drag the tile to "In Progress"; a par workspace is created and a terminal window opens
3. **Open terminals** — click a tile to focus its terminal, or right-click → "New Terminal" for additional windows
4. **Review** — drag to "In Review" (visual only)
5. **Complete** — drag to "Done"; terminal is closed
6. **Clean up** — click the delete icon (or right-click → Delete) to remove the par workspace

## Tech Stack

- **Frontend**: React, TypeScript, Vite, Tailwind CSS, dnd-kit
- **Backend**: Python, FastAPI, SQLite
- **External tools**: par, tmux, and a supported terminal emulator
