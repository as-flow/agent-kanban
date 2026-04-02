import { useCallback, useEffect, useState } from 'react';
import { Board } from './components/Board';
import { NewTaskDialog } from './components/NewTaskDialog';
import { SettingsDialog } from './components/SettingsDialog';
import { api } from './api';
import { useTheme } from './useTheme';
import type { Task } from './types';

export default function App() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [showDialog, setShowDialog] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pulling, setPulling] = useState(false);
  const [pullMsg, setPullMsg] = useState<string | null>(null);
  const { theme, toggle: toggleTheme } = useTheme();

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
    <div className="min-h-screen bg-gray-50 text-gray-900 dark:bg-gray-950 dark:text-gray-100 flex flex-col">
      <header className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-800">
        <h1 className="text-xl font-bold tracking-tight">Agent Kanban</h1>
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
            className="px-4 py-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 disabled:opacity-50 rounded-lg text-sm font-medium transition-colors cursor-pointer"
          >
            {pulling ? 'Pulling...' : 'Pull All'}
          </button>
          <button
            onClick={toggleTheme}
            className="p-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 rounded-lg transition-colors cursor-pointer"
            title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {theme === 'dark' ? (
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
                <path d="M10 2a.75.75 0 0 1 .75.75v1.5a.75.75 0 0 1-1.5 0v-1.5A.75.75 0 0 1 10 2ZM10 15a.75.75 0 0 1 .75.75v1.5a.75.75 0 0 1-1.5 0v-1.5A.75.75 0 0 1 10 15ZM10 7a3 3 0 1 0 0 6 3 3 0 0 0 0-6ZM15.657 5.404a.75.75 0 1 0-1.06-1.06l-1.061 1.06a.75.75 0 0 0 1.06 1.06l1.06-1.06ZM6.464 14.596a.75.75 0 1 0-1.06-1.06l-1.06 1.06a.75.75 0 0 0 1.06 1.06l1.06-1.06ZM18 10a.75.75 0 0 1-.75.75h-1.5a.75.75 0 0 1 0-1.5h1.5A.75.75 0 0 1 18 10ZM5 10a.75.75 0 0 1-.75.75h-1.5a.75.75 0 0 1 0-1.5h1.5A.75.75 0 0 1 5 10ZM14.596 15.657a.75.75 0 0 0 1.06-1.06l-1.06-1.061a.75.75 0 1 0-1.06 1.06l1.06 1.06ZM5.404 6.464a.75.75 0 0 0 1.06-1.06l-1.06-1.06a.75.75 0 1 0-1.06 1.06l1.06 1.06Z" />
              </svg>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
                <path fillRule="evenodd" d="M7.455 2.004a.75.75 0 0 1 .26.77 7 7 0 0 0 9.958 7.967.75.75 0 0 1 1.067.853A8.5 8.5 0 1 1 6.647 1.921a.75.75 0 0 1 .808.083Z" clipRule="evenodd" />
              </svg>
            )}
          </button>
          <button
            onClick={() => setShowSettings(true)}
            className="p-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 rounded-lg transition-colors cursor-pointer"
            title="Settings"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
              <path fillRule="evenodd" d="M7.84 1.804A1 1 0 0 1 8.82 1h2.36a1 1 0 0 1 .98.804l.331 1.652a6.993 6.993 0 0 1 1.929 1.115l1.598-.54a1 1 0 0 1 1.186.447l1.18 2.044a1 1 0 0 1-.205 1.251l-1.267 1.113a7.047 7.047 0 0 1 0 2.228l1.267 1.113a1 1 0 0 1 .206 1.25l-1.18 2.045a1 1 0 0 1-1.187.447l-1.598-.54a6.993 6.993 0 0 1-1.929 1.115l-.33 1.652a1 1 0 0 1-.98.804H8.82a1 1 0 0 1-.98-.804l-.331-1.652a6.993 6.993 0 0 1-1.929-1.115l-1.598.54a1 1 0 0 1-1.186-.447l-1.18-2.044a1 1 0 0 1 .205-1.251l1.267-1.114a7.05 7.05 0 0 1 0-2.227L1.821 7.773a1 1 0 0 1-.206-1.25l1.18-2.045a1 1 0 0 1 1.187-.447l1.598.54A6.992 6.992 0 0 1 7.51 3.456l.33-1.652ZM10 13a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z" clipRule="evenodd" />
            </svg>
          </button>
          <button
            onClick={() => setShowDialog(true)}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-medium transition-colors cursor-pointer text-white"
          >
            + New Task
          </button>
        </div>
      </header>

      {error && (
        <div className="mx-6 mt-4 p-3 bg-red-100 border border-red-300 text-red-700 dark:bg-red-900/50 dark:border-red-700 dark:text-red-200 rounded-lg text-sm">
          {error}
          <button onClick={() => setError(null)} className="ml-2 underline">dismiss</button>
        </div>
      )}

      {pullMsg && (
        <div className="mx-6 mt-4 p-3 bg-green-100 border border-green-300 text-green-700 dark:bg-green-900/50 dark:border-green-700 dark:text-green-200 rounded-lg text-sm">
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

      {showSettings && (
        <SettingsDialog
          onClose={() => setShowSettings(false)}
          onError={setError}
        />
      )}
    </div>
  );
}
