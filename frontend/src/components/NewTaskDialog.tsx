import { useEffect, useState } from 'react';
import { api } from '../api';
import type { RepoGroup } from '../types';
import { RepoGroupsDialog } from './RepoGroupsDialog';

interface Props {
  onClose: () => void;
  onCreated: () => void;
  onError: (msg: string) => void;
}

export function NewTaskDialog({ onClose, onCreated, onError }: Props) {
  const [title, setTitle] = useState('');
  const [availableRepos, setAvailableRepos] = useState<string[]>([]);
  const [groups, setGroups] = useState<RepoGroup[]>([]);
  const [selectedRepos, setSelectedRepos] = useState<Set<string>>(new Set());
  const [repoSearch, setRepoSearch] = useState('');
  const [loading, setLoading] = useState(false);
  const [showGroupsDialog, setShowGroupsDialog] = useState(false);

  useEffect(() => {
    api.getRepos().then(setAvailableRepos).catch((e) => onError(e.message));
    refreshGroups();
  }, [onError]);

  async function refreshGroups() {
    try {
      setGroups(await api.getRepoGroups());
    } catch (e: any) {
      onError(e.message);
    }
  }

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
      const allSelected = group.repos.every((r) => next.has(r));
      if (allSelected) {
        group.repos.forEach((r) => next.delete(r));
      } else {
        group.repos.forEach((r) => next.add(r));
      }
      return next;
    });
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim() || selectedRepos.size === 0) return;
    setLoading(true);
    try {
      await api.createTask(title.trim(), [...selectedRepos]);
      onCreated();
    } catch (err: any) {
      onError(err.message);
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
          className="bg-gray-900 border border-gray-700 rounded-xl p-6 w-full max-w-md shadow-2xl"
        >
          <h2 className="text-lg font-semibold mb-4">New Task</h2>

          <label className="block text-sm text-gray-400 mb-1">Title</label>
          <input
            autoFocus
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 mb-4"
            placeholder="e.g. Add auth middleware"
          />

          <div className="flex items-center justify-between mb-2">
            <label className="text-sm text-gray-400">Repositories</label>
            <button
              type="button"
              onClick={() => setShowGroupsDialog(true)}
              className="text-xs text-indigo-400 hover:text-indigo-300 cursor-pointer"
            >
              Manage Groups
            </button>
          </div>

          {groups.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-3">
              {groups.map((g) => {
                const allSelected = g.repos.every((r) => selectedRepos.has(r));
                return (
                  <button
                    key={g.id}
                    type="button"
                    onClick={() => toggleGroup(g)}
                    className={`text-xs px-3 py-1.5 rounded-full border transition-colors cursor-pointer ${
                      allSelected
                        ? 'border-indigo-500 bg-indigo-600/30 text-indigo-300'
                        : 'border-gray-600 bg-gray-800 text-gray-400 hover:border-gray-500'
                    }`}
                  >
                    {g.name}
                    <span className="ml-1 text-gray-500">({g.repos.length})</span>
                  </button>
                );
              })}
            </div>
          )}

          {availableRepos.length === 0 ? (
            <p className="text-xs text-gray-500 mb-4">
              No repos found. Check REPOS_DIRECTORY in .env
            </p>
          ) : (
            <>
            <input
              value={repoSearch}
              onChange={(e) => setRepoSearch(e.target.value)}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 mb-2"
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
                      ? 'border-indigo-500 bg-indigo-950/40 text-indigo-300'
                      : 'border-gray-700 bg-gray-800 text-gray-400 hover:border-gray-600'
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
              className="px-4 py-2 text-sm text-gray-400 hover:text-gray-200 transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !title.trim() || selectedRepos.size === 0}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-sm font-medium transition-colors cursor-pointer"
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
