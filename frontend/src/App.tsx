import { useCallback, useEffect, useState } from 'react';
import { Board } from './components/Board';
import { NewTaskDialog } from './components/NewTaskDialog';
import { api } from './api';
import type { Task } from './types';

export default function App() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [showDialog, setShowDialog] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pulling, setPulling] = useState(false);
  const [pullMsg, setPullMsg] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setTasks(await api.getTasks());
    } catch (e: any) {
      setError(e.message);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 flex flex-col">
      <header className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
        <h1 className="text-xl font-bold tracking-tight">Droid Kanban</h1>
        <div className="flex items-center gap-3">
          <button
            disabled={pulling}
            onClick={async () => {
              setPulling(true);
              setPullMsg(null);
              try {
                const results = await api.pullAllRepos();
                const ok = results.filter((r) => r.ok).length;
                const total = results.length;
                const msg = ok === total
                  ? `${total}/${total} repos pulled`
                  : `${ok}/${total} repos pulled -- ${total - ok} failed`;
                setPullMsg(msg);
                setTimeout(() => setPullMsg(null), 5000);
              } catch (e: any) {
                setError(e.message);
              } finally {
                setPulling(false);
              }
            }}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 rounded-lg text-sm font-medium transition-colors cursor-pointer"
          >
            {pulling ? 'Pulling...' : 'Pull All'}
          </button>
          <button
            onClick={() => setShowDialog(true)}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-medium transition-colors cursor-pointer"
          >
            + New Task
          </button>
        </div>
      </header>

      {error && (
        <div className="mx-6 mt-4 p-3 bg-red-900/50 border border-red-700 rounded-lg text-sm text-red-200">
          {error}
          <button onClick={() => setError(null)} className="ml-2 underline">dismiss</button>
        </div>
      )}

      {pullMsg && (
        <div className="mx-6 mt-4 p-3 bg-green-900/50 border border-green-700 rounded-lg text-sm text-green-200">
          {pullMsg}
          <button onClick={() => setPullMsg(null)} className="ml-2 underline">dismiss</button>
        </div>
      )}

      <Board tasks={tasks} onRefresh={refresh} onError={setError} />

      {showDialog && (
        <NewTaskDialog
          onClose={() => setShowDialog(false)}
          onCreated={() => {
            setShowDialog(false);
            refresh();
          }}
          onError={setError}
        />
      )}
    </div>
  );
}
