import type { AgentStatus, RepoGroup, Settings, Task, TaskStatus, TaskTerminal } from './types';

const BASE = '/api';

async function request<T>(path: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || res.statusText);
  }
  return res.json();
}

export const api = {
  getTasks: () => request<Task[]>('/tasks'),

  getRepos: () => request<string[]>('/repos'),

  createTask: (title: string, repos: string[]) =>
    request<Task>('/tasks', {
      method: 'POST',
      body: JSON.stringify({ title, repos }),
    }),

  updateStatus: (id: string, status: TaskStatus) =>
    request<Task>(`/tasks/${id}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    }),

  deleteTask: (id: string) =>
    request<{ ok: boolean }>(`/tasks/${id}`, { method: 'DELETE' }),

  deleteAllDone: () =>
    request<{ ok: boolean; deleted: number }>('/tasks/done', { method: 'DELETE' }),

  getAgentStatus: (id: string) =>
    request<AgentStatus>(`/tasks/${id}/agent-status`),

  getTerminals: (taskId: string) =>
    request<TaskTerminal[]>(`/tasks/${taskId}/terminals`),

  addTerminal: (taskId: string) =>
    request<TaskTerminal>(`/tasks/${taskId}/terminals`, { method: 'POST' }),

  focusTerminal: (taskId: string, terminalId: string) =>
    request<{ ok: boolean }>(`/tasks/${taskId}/terminals/${terminalId}/focus`, { method: 'POST' }),

  deleteTerminal: (taskId: string, terminalId: string) =>
    request<{ ok: boolean }>(`/tasks/${taskId}/terminals/${terminalId}`, { method: 'DELETE' }),

  pullAllRepos: () =>
    request<{ repo: string; ok: boolean; output: string }[]>('/repos/pull', { method: 'POST' }),

  getRepoGroups: () => request<RepoGroup[]>('/repo-groups'),

  createRepoGroup: (name: string, repos: string[]) =>
    request<RepoGroup>('/repo-groups', {
      method: 'POST',
      body: JSON.stringify({ name, repos }),
    }),

  updateRepoGroup: (id: string, name: string, repos: string[]) =>
    request<RepoGroup>(`/repo-groups/${id}`, {
      method: 'PUT',
      body: JSON.stringify({ name, repos }),
    }),

  deleteRepoGroup: (id: string) =>
    request<{ ok: boolean }>(`/repo-groups/${id}`, { method: 'DELETE' }),

  getSettings: () => request<Settings>('/settings'),

  updateSettings: (data: Partial<Settings>) =>
    request<Settings>('/settings', {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
};
