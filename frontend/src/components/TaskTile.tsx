import { useDraggable } from '@dnd-kit/core';
import { useCallback, useEffect, useRef, useState } from 'react';
import { api } from '../api';
import type { Task } from '../types';

interface Props {
  task: Task;
  overlay?: boolean;
  onRefresh: () => void;
  onError: (msg: string) => void;
}

export function TaskTile({ task, overlay, onRefresh, onError }: Props) {
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({ id: task.id });
  const [agentRunning, setAgentRunning] = useState(false);
  const [ctxMenu, setCtxMenu] = useState<{ x: number; y: number } | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (task.status !== 'in_progress' && task.status !== 'in_review') return;
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
  }, [task.id, task.status]);

  const closeMenu = useCallback(() => setCtxMenu(null), []);

  useEffect(() => {
    if (!ctxMenu) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') closeMenu();
    };
    window.addEventListener('click', closeMenu);
    window.addEventListener('scroll', closeMenu, true);
    window.addEventListener('keydown', handleKey);
    return () => {
      window.removeEventListener('click', closeMenu);
      window.removeEventListener('scroll', closeMenu, true);
      window.removeEventListener('keydown', handleKey);
    };
  }, [ctxMenu, closeMenu]);

  function handleContextMenu(e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    setCtxMenu({ x: e.clientX, y: e.clientY });
  }

  async function handleClick() {
    if (task.status === 'in_progress' || task.status === 'in_review') {
      try {
        await api.focusTask(task.id);
      } catch (e: any) {
        onError(e.message);
      }
    }
  }

  async function handleNewTerminal() {
    closeMenu();
    try {
      await api.newTerminal(task.id);
    } catch (e: any) {
      onError(e.message);
    }
  }

  async function handleFocus() {
    closeMenu();
    try {
      await api.focusTask(task.id);
    } catch (e: any) {
      onError(e.message);
    }
  }

  async function handleDelete() {
    closeMenu();
    if (!confirm(`Delete "${task.title}" and its par workspace?`)) return;
    try {
      await api.deleteTask(task.id);
      onRefresh();
    } catch (e: any) {
      onError(e.message);
    }
  }

  const isActive = task.status === 'in_progress' || task.status === 'in_review';
  const canDelete = task.status === 'done' || task.status === 'not_started';

  return (
    <div
      ref={overlay ? undefined : setNodeRef}
      {...(overlay ? {} : { ...attributes, ...listeners })}
      onClick={handleClick}
      onContextMenu={overlay ? undefined : handleContextMenu}
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
              onClick={(e) => { e.stopPropagation(); handleDelete(); }}
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

      {ctxMenu && (
        <div
          ref={menuRef}
          className="fixed z-[100] min-w-[160px] bg-gray-900 border border-gray-700 rounded-lg shadow-2xl py-1"
          style={{ left: ctxMenu.x, top: ctxMenu.y }}
          onClick={(e) => e.stopPropagation()}
        >
          {isActive && (
            <>
              <button
                onClick={handleNewTerminal}
                className="w-full text-left px-4 py-2 text-sm text-gray-200 hover:bg-gray-800 cursor-pointer"
              >
                New Terminal
              </button>
              <button
                onClick={handleFocus}
                className="w-full text-left px-4 py-2 text-sm text-gray-200 hover:bg-gray-800 cursor-pointer"
              >
                Focus Terminal
              </button>
            </>
          )}
          {canDelete && (
            <button
              onClick={handleDelete}
              className="w-full text-left px-4 py-2 text-sm text-red-400 hover:bg-gray-800 cursor-pointer"
            >
              Delete
            </button>
          )}
          {!isActive && !canDelete && (
            <div className="px-4 py-2 text-sm text-gray-500">No actions</div>
          )}
        </div>
      )}
    </div>
  );
}
