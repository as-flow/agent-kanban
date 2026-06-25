import {
  DndContext,
  DragOverlay,
  type DragEndEvent,
  type DragStartEvent,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import { useEffect, useMemo, useState } from 'react';
import { api } from '../api';
import { getErrorMessage } from '../errorMessage';
import type { Task, TaskStatus } from '../types';
import { COLUMNS } from '../types';
import { Column } from './Column';
import { TaskTile } from './TaskTile';

const VALID_TRANSITIONS: Record<TaskStatus, TaskStatus[]> = {
  not_started: ['in_progress'],
  in_progress: ['in_review', 'on_hold', 'done'],
  in_review: ['in_progress', 'on_hold', 'done'],
  on_hold: ['in_progress', 'in_review', 'done'],
  done: ['in_progress'],
};

interface Props {
  tasks: Task[];
  onRefresh: () => void;
  onError: (msg: string) => void;
}

export function Board({ tasks, onRefresh, onError }: Props) {
  const [activeTask, setActiveTask] = useState<Task | null>(null);
  const [clearingDone, setClearingDone] = useState(false);
  const [agentRunningByTask, setAgentRunningByTask] = useState<Record<string, boolean>>({});
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }));
  const activeTaskIds = useMemo(
    () => tasks
      .filter((task) => task.status === 'in_progress' || task.status === 'in_review' || task.status === 'on_hold')
      .map((task) => task.id),
    [tasks],
  );

  useEffect(() => {
    if (activeTaskIds.length === 0) {
      setAgentRunningByTask({});
      return;
    }

    let cancelled = false;
    const poll = async () => {
      try {
        const statuses = await api.getAgentStatuses(activeTaskIds);
        if (cancelled) return;
        setAgentRunningByTask(Object.fromEntries(
          Object.entries(statuses).map(([id, status]) => [id, status.running]),
        ));
      } catch { /* ignore */ }
    };

    poll();
    const interval = setInterval(poll, 5000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [activeTaskIds]);

  function handleDragStart(event: DragStartEvent) {
    const task = tasks.find((t) => t.id === event.active.id);
    setActiveTask(task ?? null);
  }

  async function handleDeleteAllDone() {
    setClearingDone(true);
    try {
      await api.deleteAllDone();
      onRefresh();
    } catch (error) {
      onError(getErrorMessage(error));
    } finally {
      setClearingDone(false);
    }
  }

  async function handleDragEnd(event: DragEndEvent) {
    setActiveTask(null);
    const { active, over } = event;
    if (!over) return;

    const task = tasks.find((t) => t.id === active.id);
    if (!task) return;

    const targetStatus = over.id as TaskStatus;
    if (task.status === targetStatus) return;

    const allowed = VALID_TRANSITIONS[task.status] ?? [];
    if (!allowed.includes(targetStatus)) {
      onError(`Cannot move from "${task.status}" to "${targetStatus}"`);
      return;
    }

    try {
      await api.updateStatus(task.id, targetStatus);
      onRefresh();
    } catch (error) {
      onError(getErrorMessage(error));
    }
  }

  return (
    <DndContext sensors={sensors} onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
      <div className="flex-1 flex gap-4 p-6 overflow-x-auto min-h-0 w-full">
        {COLUMNS.map((col) => (
          <Column
            key={col.id}
            id={col.id}
            label={col.label}
            tasks={tasks.filter((t) => t.status === col.id)}
            agentRunningByTask={agentRunningByTask}
            onRefresh={onRefresh}
            onError={onError}
            {...(col.id === 'done' ? { onDeleteAll: handleDeleteAllDone, isClearingAll: clearingDone } : {})}
          />
        ))}
      </div>
      <DragOverlay>
        {activeTask ? (
          <TaskTile
            task={activeTask}
            overlay
            agentRunning={agentRunningByTask[activeTask.id] ?? false}
            onRefresh={onRefresh}
            onError={onError}
          />
        ) : null}
      </DragOverlay>
    </DndContext>
  );
}
