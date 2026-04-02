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
}

export function Column({ id, label, tasks, onRefresh, onError, onDeleteAll }: Props) {
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
        <h2 className="text-sm font-semibold text-gray-600 dark:text-gray-300">{label}</h2>
        <div className="flex items-center gap-2">
          {onDeleteAll && tasks.length > 0 && (
            <button
              onClick={() => {
                if (window.confirm(`Delete all ${tasks.length} done task(s)?`)) {
                  onDeleteAll();
                }
              }}
              className="text-xs text-red-500 hover:text-red-600 bg-red-100 hover:bg-red-200 dark:text-red-400 dark:hover:text-red-300 dark:bg-red-900/30 dark:hover:bg-red-900/50 px-2 py-0.5 rounded-full transition-colors"
              title="Delete all done tasks"
            >
              Clear all
            </button>
          )}
          <span className="text-xs text-gray-500 bg-gray-200 dark:bg-gray-800 px-2 py-0.5 rounded-full">
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
