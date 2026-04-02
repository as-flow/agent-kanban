export type TaskStatus = 'not_started' | 'in_progress' | 'in_review' | 'on_hold' | 'done';

export interface Task {
  id: string;
  title: string;
  status: TaskStatus;
  repos: string[];
  par_label: string;
  tmux_session: string | null;
  terminal_pid: number | null;
  color_fg: string;
  color_bg: string;
  created_at: string;
  updated_at: string;
}

export interface RepoGroup {
  id: string;
  name: string;
  repos: string[];
  created_at: string;
}

export interface AgentStatus {
  running: boolean;
  command: string;
}

export interface TaskTerminal {
  id: string;
  task_id: string;
  pid: number;
  kind: 'original' | 'shell';
  title: string;
  created_at: string;
}

export interface Settings {
  terminal_app: string;
  terminal_path: string;
  repos_directory: string;
}

export const SUPPORTED_TERMINALS = [
  'ghostty', 'kitty', 'alacritty', 'wezterm', 'iterm2', 'terminal',
] as const;

export const COLUMNS: { id: TaskStatus; label: string }[] = [
  { id: 'not_started', label: 'Not Started' },
  { id: 'in_progress', label: 'In Progress' },
  { id: 'in_review', label: 'In Review' },
  { id: 'on_hold', label: 'On Hold' },
  { id: 'done', label: 'Done' },
];
