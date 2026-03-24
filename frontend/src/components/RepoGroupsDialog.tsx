import { useEffect, useState } from 'react';
import { api } from '../api';
import type { RepoGroup } from '../types';

interface Props {
  onClose: () => void;
  onError: (msg: string) => void;
}

export function RepoGroupsDialog({ onClose, onError }: Props) {
  const [groups, setGroups] = useState<RepoGroup[]>([]);
  const [availableRepos, setAvailableRepos] = useState<string[]>([]);
  const [editingGroup, setEditingGroup] = useState<RepoGroup | null>(null);
  const [name, setName] = useState('');
  const [selectedRepos, setSelectedRepos] = useState<Set<string>>(new Set());
  const [saving, setSaving] = useState(false);
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    refresh();
    api.getRepos().then(setAvailableRepos).catch((e) => onError(e.message));
  }, [onError]);

  async function refresh() {
    try {
      setGroups(await api.getRepoGroups());
    } catch (e: any) {
      onError(e.message);
    }
  }

  function startEdit(group: RepoGroup) {
    setEditingGroup(group);
    setName(group.name);
    setSelectedRepos(new Set(group.repos));
    setShowForm(true);
  }

  function startNew() {
    setEditingGroup(null);
    setName('');
    setSelectedRepos(new Set());
    setShowForm(true);
  }

  function closeForm() {
    setEditingGroup(null);
    setName('');
    setSelectedRepos(new Set());
    setShowForm(false);
  }

  function toggleRepo(repo: string) {
    setSelectedRepos((prev) => {
      const next = new Set(prev);
      if (next.has(repo)) next.delete(repo);
      else next.add(repo);
      return next;
    });
  }

  async function handleSave() {
    if (!name.trim() || selectedRepos.size === 0) return;
    setSaving(true);
    try {
      if (editingGroup) {
        await api.updateRepoGroup(editingGroup.id, name.trim(), [...selectedRepos]);
      } else {
        await api.createRepoGroup(name.trim(), [...selectedRepos]);
      }
      closeForm();
      await refresh();
    } catch (e: any) {
      onError(e.message);
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: string) {
    try {
      await api.deleteRepoGroup(id);
      if (editingGroup?.id === id) {
        closeForm();
      }
      await refresh();
    } catch (e: any) {
      onError(e.message);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={onClose}>
      <div
        onClick={(e) => e.stopPropagation()}
        className="bg-gray-900 border border-gray-700 rounded-xl p-6 w-full max-w-lg shadow-2xl max-h-[80vh] overflow-y-auto"
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Repo Groups</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-300 cursor-pointer">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {groups.length > 0 && (
          <div className="space-y-2 mb-4">
            {groups.map((g) => (
              <div
                key={g.id}
                className="flex items-center justify-between p-3 bg-gray-800 rounded-lg border border-gray-700"
              >
                <div className="min-w-0">
                  <div className="text-sm font-medium text-gray-200">{g.name}</div>
                  <div className="text-xs text-gray-500 truncate">{g.repos.join(', ')}</div>
                </div>
                <div className="flex gap-2 shrink-0 ml-3">
                  <button
                    onClick={() => startEdit(g)}
                    className="text-xs text-indigo-400 hover:text-indigo-300 cursor-pointer"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleDelete(g.id)}
                    className="text-xs text-red-400 hover:text-red-300 cursor-pointer"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {!showForm && (
          <button
            onClick={startNew}
            className="w-full py-2 border border-dashed border-gray-600 rounded-lg text-sm text-gray-400 hover:text-gray-200 hover:border-gray-500 transition-colors cursor-pointer"
          >
            + New Group
          </button>
        )}

        {showForm && (
          <div className="border border-gray-700 rounded-lg p-4 mt-2">
            <label className="block text-sm text-gray-400 mb-1">Group Name</label>
            <input
              autoFocus
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 mb-3"
              placeholder="e.g. backend-services"
            />

            <label className="block text-sm text-gray-400 mb-2">Repositories</label>
            <div className="grid grid-cols-2 gap-2 mb-3 max-h-40 overflow-y-auto">
              {availableRepos.map((repo) => (
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

            <div className="flex justify-end gap-3">
              <button
                type="button"
                onClick={closeForm}
                className="px-3 py-1.5 text-sm text-gray-400 hover:text-gray-200 cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={saving || !name.trim() || selectedRepos.size === 0}
                className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 rounded-lg text-sm font-medium transition-colors cursor-pointer"
              >
                {saving ? 'Saving...' : editingGroup ? 'Update' : 'Create'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
