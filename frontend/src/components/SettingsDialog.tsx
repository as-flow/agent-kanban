import { useEffect, useState } from 'react';
import { api } from '../api';
import type { Settings } from '../types';
import { SUPPORTED_TERMINALS } from '../types';

interface Props {
  onClose: () => void;
  onError: (msg: string) => void;
}

export function SettingsDialog({ onClose, onError }: Props) {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.getSettings().then(setSettings).catch((e) => onError(e.message));
  }, [onError]);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    if (!settings) return;
    setSaving(true);
    try {
      const updated = await api.updateSettings(settings);
      setSettings(updated);
      onClose();
    } catch (err: any) {
      onError(err.message);
    } finally {
      setSaving(false);
    }
  }

  if (!settings) {
    return (
      <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
        <div className="bg-white border border-gray-200 dark:bg-gray-900 dark:border-gray-700 rounded-xl p-6 w-full max-w-md shadow-2xl">
          <p className="text-sm text-gray-500 dark:text-gray-400">Loading settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={onClose}>
      <form
        onClick={(e) => e.stopPropagation()}
        onSubmit={handleSave}
        className="bg-white border border-gray-200 dark:bg-gray-900 dark:border-gray-700 rounded-xl p-6 w-full max-w-md shadow-2xl"
      >
        <h2 className="text-lg font-semibold mb-5">Settings</h2>

        <label className="block text-sm text-gray-500 dark:text-gray-400 mb-1">Terminal App</label>
        <select
          value={settings.terminal_app}
          onChange={(e) => setSettings({ ...settings, terminal_app: e.target.value })}
          className="w-full px-3 py-2 bg-gray-50 border border-gray-200 dark:bg-gray-800 dark:border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 mb-4 cursor-pointer"
        >
          {SUPPORTED_TERMINALS.map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>

        <label className="block text-sm text-gray-500 dark:text-gray-400 mb-1">Terminal Path</label>
        <input
          value={settings.terminal_path}
          onChange={(e) => setSettings({ ...settings, terminal_path: e.target.value })}
          className="w-full px-3 py-2 bg-gray-50 border border-gray-200 dark:bg-gray-800 dark:border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 mb-1"
          placeholder="Auto-detected if empty"
        />
        <p className="text-xs text-gray-500 mb-4">Optional override for the terminal binary path.</p>

        <label className="block text-sm text-gray-500 dark:text-gray-400 mb-1">Repos Directory</label>
        <input
          value={settings.repos_directory}
          onChange={(e) => setSettings({ ...settings, repos_directory: e.target.value })}
          className="w-full px-3 py-2 bg-gray-50 border border-gray-200 dark:bg-gray-800 dark:border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 mb-1"
          placeholder="/path/to/your/repos"
        />
        <p className="text-xs text-gray-500 mb-5">Directory containing your git repositories.</p>

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
            disabled={saving}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-sm font-medium text-white transition-colors cursor-pointer"
          >
            {saving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </form>
    </div>
  );
}
