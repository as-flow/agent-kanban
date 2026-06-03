import { useCallback, useEffect, useMemo, useState } from 'react';
import { api } from '../api';
import { formatLastPulledLabel, LAST_PULLED_EVENT, readLastPulledAt } from '../lastPulled';
import type { RepoGroup } from '../types';
import { RepoGroupsDialog } from './RepoGroupsDialog';

interface Props {
  onClose: () => void;
  onCreated: () => void;
  onError: (msg: string) => void;
}

function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

export function NewTaskDialog({ onClose, onCreated, onError }: Props) {
  const [title, setTitle] = useState('');
  const [availableRepos, setAvailableRepos] = useState<string[]>([]);
  const [groups, setGroups] = useState<RepoGroup[]>([]);
  const [selectedRepos, setSelectedRepos] = useState<Set<string>>(new Set());
  const [repoSearch, setRepoSearch] = useState('');
  const [loading, setLoading] = useState(false);
  const [showGroupsDialog, setShowGroupsDialog] = useState(false);
  const [lastPulledLabel, setLastPulledLabel] = useState(() =>
    formatLastPulledLabel(readLastPulledAt()),
  );
  const availableRepoSet = useMemo(() => new Set(availableRepos), [availableRepos]);

  const refreshGroups = useCallback(async () => {
    try {
      setGroups(await api.getRepoGroups());
    } catch (e: unknown) {
      onError(getErrorMessage(e));
    }
  }, [onError]);

  useEffect(() => {
    function syncLabel() {
      setLastPulledLabel(formatLastPulledLabel(readLastPulledAt()));
    }
    window.addEventListener(LAST_PULLED_EVENT, syncLabel);
    window.addEventListener('storage', syncLabel);
    return () => {
      window.removeEventListener(LAST_PULLED_EVENT, syncLabel);
      window.removeEventListener('storage', syncLabel);
    };
  }, []);

  useEffect(() => {
    api
      .getRepos()
      .then((rows) => setAvailableRepos(rows.map((r) => r.name)))
      .catch((e: unknown) => onError(getErrorMessage(e)));
    refreshGroups();
  }, [onError, refreshGroups]);

  function toggleRepo(repo: string) {
    setSelectedRepos((prev) => {
      const next = new Set(prev);
      if (next.has(repo)) next.delete(repo);
      else next.add(repo);
      return next;
    });
  }

  function toggleGroup(group: RepoGroup) {
    setSelectedRepos((prev) => {
      const next = new Set(prev);
      const selectableRepos = group.repos.filter((repo) => availableRepoSet.has(repo));
      const allSelected = selectableRepos.length > 0 && selectableRepos.every((r) => next.has(r));
      if (allSelected) {
        selectableRepos.forEach((r) => next.delete(r));
      } else {
        selectableRepos.forEach((r) => next.add(r));
      }
      return next;
    });
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;
    setLoading(true);
    try {
      await api.createTask(title.trim(), [...selectedRepos]);
      onCreated();
    } catch (err: unknown) {
      onError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={onClose}>
        <form
          onClick={(e) => e.stopPropagation()}
          onSubmit={handleSubmit}
          className="bg-white border border-gray-200 dark:bg-gray-900 dark:border-gray-700 rounded-xl p-6 w-full max-w-md shadow-2xl"
        >
          <h2 className="text-lg font-semibold mb-1">New Task</h2>
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-4">Last pulled: {lastPulledLabel}</p>

          <label className="block text-sm text-gray-500 dark:text-gray-400 mb-1">Title</label>
          <input
            autoFocus
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full px-3 py-2 bg-gray-50 border border-gray-200 dark:bg-gray-800 dark:border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 mb-4"
            placeholder="e.g. Add auth middleware"
          />

          <div className="flex items-center justify-between mb-2">
            <label className="text-sm text-gray-500 dark:text-gray-400">Repositories</label>
            <button
              type="button"
              onClick={() => setShowGroupsDialog(true)}
              className="text-xs text-indigo-500 hover:text-indigo-400 dark:text-indigo-400 dark:hover:text-indigo-300 cursor-pointer"
            >
              Manage Groups
            </button>
          </div>

          {groups.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-3">
              {groups.map((g) => {
                const selectableRepos = g.repos.filter((repo) => availableRepoSet.has(repo));
                const allSelected = selectableRepos.length > 0 && selectableRepos.every((r) => selectedRepos.has(r));
                return (
                  <button
                    key={g.id}
                    type="button"
                    onClick={() => toggleGroup(g)}
                    className={`text-xs px-3 py-1.5 rounded-full border transition-colors cursor-pointer ${
                      allSelected
                        ? 'border-indigo-500 bg-indigo-50 text-indigo-600 dark:bg-indigo-600/30 dark:text-indigo-300'
                        : 'border-gray-300 bg-gray-50 text-gray-500 hover:border-gray-400 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-400 dark:hover:border-gray-500'
                    }`}
                  >
                    {g.name}
                    <span className="ml-1 text-gray-400 dark:text-gray-500">({g.repos.length})</span>
                  </button>
                );
              })}
            </div>
          )}

          {availableRepos.length === 0 ? (
            <p className="text-xs text-gray-500 mb-4">
              No repos found in REPOS_DIRECTORY. You can still create a task; it will open there when started.
            </p>
          ) : (
            <>
            <input
              value={repoSearch}
              onChange={(e) => setRepoSearch(e.target.value)}
              className="w-full px-3 py-2 bg-gray-50 border border-gray-200 dark:bg-gray-800 dark:border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 mb-2"
              placeholder="Search repos..."
            />
            <div className="grid grid-cols-2 gap-2 mb-4 max-h-48 overflow-y-auto">
              {availableRepos.filter((r) => r.toLowerCase().includes(repoSearch.toLowerCase())).map((repo) => (
                <button
                  key={repo}
                  type="button"
                  onClick={() => toggleRepo(repo)}
                  className={`text-left text-sm px-3 py-2 rounded-lg border transition-colors cursor-pointer ${
                    selectedRepos.has(repo)
                      ? 'border-indigo-500 bg-indigo-50 text-indigo-600 dark:bg-indigo-950/40 dark:text-indigo-300'
                      : 'border-gray-200 bg-gray-50 text-gray-500 hover:border-gray-300 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-400 dark:hover:border-gray-600'
                  }`}
                >
                  {repo}
                </button>
              ))}
            </div>
            </>
          )}

          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-sm font-medium text-white transition-colors cursor-pointer"
            >
              {loading ? 'Creating...' : 'Create Task'}
            </button>
          </div>
        </form>
      </div>

      {showGroupsDialog && (
        <RepoGroupsDialog
          onClose={() => {
            setShowGroupsDialog(false);
            refreshGroups();
          }}
          onError={onError}
        />
      )}
    </>
  );
}
