import { useDraggable } from '@dnd-kit/core';
import { useCallback, useEffect, useState } from 'react';
import { api } from '../api';
import type { Task, TaskTerminal } from '../types';

interface Props {
  task: Task;
  overlay?: boolean;
  onRefresh: () => void;
  onError: (msg: string) => void;
}

export function TaskTile({ task, overlay, onRefresh, onError }: Props) {
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({ id: task.id });
  const [agentRunning, setAgentRunning] = useState(false);
  const [terminals, setTerminals] = useState<TaskTerminal[]>([]);

  const isActive = task.status === 'in_progress' || task.status === 'in_review' || task.status === 'on_hold';
  const canDelete = task.status === 'done' || task.status === 'not_started';

  const refreshTerminals = useCallback(async () => {
    if (!isActive) return;
    try {
      setTerminals(await api.getTerminals(task.id));
    } catch { /* ignore */ }
  }, [task.id, isActive]);

  useEffect(() => {
    refreshTerminals();
  }, [refreshTerminals]);

  useEffect(() => {
    if (!isActive) return;
    let cancelled = false;
    const poll = async () => {
      try {
        const st = await api.getAgentStatus(task.id);
        if (!cancelled) setAgentRunning(st.running);
      } catch { /* ignore */ }
    };
    poll();
    const interval = setInterval(poll, 5000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [task.id, isActive]);

  async function handleFocusTerminal(termId: string) {
    try {
      await api.focusTerminal(task.id, termId);
      await refreshTerminals();
    } catch (e: any) {
      onError(e.message);
    }
  }

  async function handleAddTerminal() {
    try {
      await api.addTerminal(task.id);
      await refreshTerminals();
    } catch (e: any) {
      onError(e.message);
    }
  }

  async function handleDeleteTerminal(termId: string) {
    try {
      await api.deleteTerminal(task.id, termId);
      await refreshTerminals();
    } catch (e: any) {
      onError(e.message);
    }
  }

  async function handleDeleteTask() {
    if (!confirm(`Delete "${task.title}" and its par workspace?`)) return;
    try {
      await api.deleteTask(task.id);
      onRefresh();
    } catch (e: any) {
      onError(e.message);
    }
  }

  return (
    <div
      ref={overlay ? undefined : setNodeRef}
      {...(overlay ? {} : { ...attributes, ...listeners })}
      className={`relative rounded-lg border border-gray-700 bg-gray-800 p-3 cursor-grab active:cursor-grabbing transition-shadow hover:shadow-lg ${
        isDragging && !overlay ? 'opacity-30' : ''
      } ${overlay ? 'shadow-2xl rotate-2' : ''}`}
      style={{ borderLeftWidth: '4px', borderLeftColor: task.color_bg }}
    >
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-sm font-medium text-gray-100 leading-tight">{task.title}</h3>
        <div className="flex items-center gap-1.5 shrink-0">
          {isActive && (
            <span
              className={`w-2.5 h-2.5 rounded-full ${agentRunning ? 'bg-green-400 animate-pulse' : 'bg-gray-500'}`}
              title={agentRunning ? 'Agent running' : 'Agent stopped'}
            />
          )}
          {canDelete && (
            <button
              onClick={(e) => { e.stopPropagation(); handleDeleteTask(); }}
              className="text-gray-500 hover:text-red-400 transition-colors cursor-pointer"
              title="Delete task"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          )}
        </div>
      </div>

      <div className="flex flex-wrap gap-1.5 mt-2">
        {task.repos.map((repo) => (
          <span
            key={repo}
            className="text-xs px-2 py-0.5 rounded-full"
            style={{ backgroundColor: task.color_bg + '40', color: task.color_fg }}
          >
            {repo}
          </span>
        ))}
      </div>

      <div className="mt-2 text-xs text-gray-500 font-mono truncate" title={task.par_label}>
        {task.par_label}
      </div>

      {isActive && terminals.length > 0 && (
        <div className="mt-2 border-t border-gray-700 pt-2 space-y-1">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-medium text-gray-400">Terminals</span>
            <button
              onClick={(e) => { e.stopPropagation(); handleAddTerminal(); }}
              className="text-gray-400 hover:text-green-400 transition-colors cursor-pointer"
              title="New terminal"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
            </button>
          </div>
          {terminals.map((term, i) => {
            const alive = term.pid > 0;
            const label = term.kind === 'original' ? 'Main' : `Shell ${i}`;
            return (
              <div
                key={term.id}
                className="flex items-center justify-between group text-xs rounded px-1.5 py-1 hover:bg-gray-700/50"
              >
                <button
                  onClick={(e) => { e.stopPropagation(); handleFocusTerminal(term.id); }}
                  className="flex items-center gap-1.5 text-gray-300 hover:text-white cursor-pointer min-w-0"
                  title={alive ? 'Focus terminal' : 'Reopen terminal'}
                >
                  <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${alive ? 'bg-green-400' : 'bg-gray-600'}`} />
                  <span className="truncate">{label}</span>
                </button>
                {term.kind !== 'original' && (
                  <button
                    onClick={(e) => { e.stopPropagation(); handleDeleteTerminal(term.id); }}
                    className="text-gray-600 hover:text-red-400 transition-colors cursor-pointer opacity-0 group-hover:opacity-100"
                    title="Close terminal"
                  >
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
