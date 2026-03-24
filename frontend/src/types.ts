export type TaskStatus = 'not_started' | 'in_progress' | 'in_review' | 'done';

export interface Task {
  id: string;
  title: string;
  status: TaskStatus;
  repos: string[];
  par_label: string;
  tmux_session: string | null;
  ghostty_pid: number | null;
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

export const COLUMNS: { id: TaskStatus; label: string }[] = [
  { id: 'not_started', label: 'Not Started' },
  { id: 'in_progress', label: 'In Progress' },
  { id: 'in_review', label: 'In Review' },
  { id: 'done', label: 'Done' },
];
