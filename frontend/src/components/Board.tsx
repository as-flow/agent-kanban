import {
  DndContext,
  DragOverlay,
  type DragEndEvent,
  type DragStartEvent,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import { useState } from 'react';
import { api } from '../api';
import type { Task, TaskStatus } from '../types';
import { COLUMNS } from '../types';
import { Column } from './Column';
import { TaskTile } from './TaskTile';

const STATUS_ORDER: TaskStatus[] = ['not_started', 'in_progress', 'in_review', 'done'];

interface Props {
  tasks: Task[];
  onRefresh: () => void;
  onError: (msg: string) => void;
}

export function Board({ tasks, onRefresh, onError }: Props) {
  const [activeTask, setActiveTask] = useState<Task | null>(null);
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }));

  function handleDragStart(event: DragStartEvent) {
    const task = tasks.find((t) => t.id === event.active.id);
    setActiveTask(task ?? null);
  }

  async function handleDragEnd(event: DragEndEvent) {
    setActiveTask(null);
    const { active, over } = event;
    if (!over) return;

    const task = tasks.find((t) => t.id === active.id);
    if (!task) return;

    const targetStatus = over.id as TaskStatus;
    if (task.status === targetStatus) return;

    const fromIdx = STATUS_ORDER.indexOf(task.status);
    const toIdx = STATUS_ORDER.indexOf(targetStatus);
    if (toIdx !== fromIdx + 1) {
      onError(`Can only move forward one column at a time`);
      return;
    }

    try {
      await api.updateStatus(task.id, targetStatus);
      onRefresh();
    } catch (e: any) {
      onError(e.message);
    }
  }

  return (
    <DndContext sensors={sensors} onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
      <div className="flex-1 flex gap-4 p-6 overflow-x-auto">
        {COLUMNS.map((col) => (
          <Column
            key={col.id}
            id={col.id}
            label={col.label}
            tasks={tasks.filter((t) => t.status === col.id)}
            onRefresh={onRefresh}
            onError={onError}
          />
        ))}
      </div>
      <DragOverlay>
        {activeTask ? <TaskTile task={activeTask} overlay onRefresh={onRefresh} onError={onError} /> : null}
      </DragOverlay>
    </DndContext>
  );
}
