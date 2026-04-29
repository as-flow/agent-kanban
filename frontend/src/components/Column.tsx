import { useDroppable } from '@dnd-kit/core';
import type { Task, TaskStatus } from '../types';
import { TaskTile } from './TaskTile';

interface Props {
  id: TaskStatus;
  label: string;
  tasks: Task[];
  onRefresh: () => void;
  onError: (msg: string) => void;
  onDeleteAll?: () => void;
  isClearingAll?: boolean;
}

export function Column({ id, label, tasks, onRefresh, onError, onDeleteAll, isClearingAll }: Props) {
  const { setNodeRef, isOver } = useDroppable({ id });

  return (
    <div
      ref={setNodeRef}
      className={`flex-1 min-w-[280px] flex flex-col rounded-xl border transition-colors ${
        isOver
          ? 'border-indigo-500 bg-indigo-50/50 dark:bg-indigo-950/20'
          : 'border-gray-200 bg-gray-100/50 dark:border-gray-800 dark:bg-gray-900/50'
      }`}
    >
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-800">
        <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300">{label}</h2>
        <div className="flex items-center gap-2">
          {onDeleteAll && (tasks.length > 0 || isClearingAll) && (
            <button
              type="button"
              disabled={!!isClearingAll}
              aria-busy={isClearingAll || undefined}
              aria-label={isClearingAll ? 'Clearing done tasks' : 'Delete all done tasks'}
              onClick={() => {
                if (window.confirm(`Delete all ${tasks.length} done task(s)?`)) {
                  onDeleteAll();
                }
              }}
              className="inline-flex items-center gap-1.5 text-xs text-red-500 hover:text-red-600 bg-red-100 hover:bg-red-200 dark:text-red-400 dark:hover:text-red-300 dark:bg-red-900/30 dark:hover:bg-red-900/50 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-red-100 dark:disabled:hover:bg-red-900/30 px-2 py-0.5 rounded-full transition-colors"
              title={isClearingAll ? 'Clearing…' : 'Delete all done tasks'}
            >
              {isClearingAll && (
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  className="w-3.5 h-3.5 shrink-0 animate-spin"
                  aria-hidden
                >
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
              )}
              {isClearingAll ? 'Clearing…' : 'Clear all'}
            </button>
          )}
          <span className="text-xs text-gray-700 dark:text-gray-300 bg-gray-200 dark:bg-gray-800 px-2 py-0.5 rounded-full">
            {tasks.length}
          </span>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {tasks.map((task) => (
          <TaskTile key={task.id} task={task} onRefresh={onRefresh} onError={onError} />
        ))}
      </div>
    </div>
  );
}
