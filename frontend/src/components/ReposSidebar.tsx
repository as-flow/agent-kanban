import { useCallback, useEffect, useState } from 'react';
import { api } from '../api';
import { writeLastPulledNow } from '../lastPulled';
import type { RepoInfo } from '../types';

const SIDEBAR_COLLAPSED_KEY = 'agent-kanban-sidebar-collapsed';

function readSidebarCollapsed(): boolean {
  try {
    return localStorage.getItem(SIDEBAR_COLLAPSED_KEY) === '1';
  } catch {
    return false;
  }
}

function writeSidebarCollapsed(collapsed: boolean): void {
  try {
    localStorage.setItem(SIDEBAR_COLLAPSED_KEY, collapsed ? '1' : '0');
  } catch {
    /* ignore */
  }
}

interface Props {
  onError: (msg: string) => void;
}

export function ReposSidebar({ onError }: Props) {
  const [collapsed, setCollapsed] = useState(readSidebarCollapsed);
  const [repos, setRepos] = useState<RepoInfo[]>([]);
  const [pulling, setPulling] = useState(false);
  const [pullMsg, setPullMsg] = useState<string | null>(null);

  const loadRepos = useCallback(() => {
    api.getRepos().then(setRepos).catch((e) => onError(e.message));
  }, [onError]);

  useEffect(() => {
    loadRepos();
  }, [loadRepos]);

  function toggleCollapsed() {
    setCollapsed((c) => {
      const next = !c;
      writeSidebarCollapsed(next);
      return next;
    });
  }

  async function handlePullAll() {
    setPulling(true);
    setPullMsg(null);
    try {
      const results = await api.pullAllRepos();
      writeLastPulledNow();
      const ok = results.filter((r) => r.ok).length;
      const total = results.length;
      const failedRepos = results.filter((r) => !r.ok).map((r) => r.repo);
      const msg =
        ok === total
          ? `${total}/${total} repos pulled`
          : `${ok}/${total} repos pulled -- failed: ${failedRepos.join(', ')}`;
      setPullMsg(msg);
      if (failedRepos.length === 0) {
        setTimeout(() => setPullMsg(null), 5000);
      }
      loadRepos();
    } catch (e: any) {
      onError(e.message);
    } finally {
      setPulling(false);
    }
  }

  return (
    <aside
      className={`shrink-0 border-r border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 flex flex-col transition-[width] duration-200 ${
        collapsed ? 'w-12' : 'w-64'
      }`}
    >
      <div className="flex items-center justify-between gap-1 p-2 border-b border-gray-200 dark:border-gray-800 min-h-[3rem]">
        {collapsed ? (
          <button
            type="button"
            onClick={toggleCollapsed}
            className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-300 mx-auto"
            title="Expand repos"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5" aria-hidden>
              <path
                fillRule="evenodd"
                d="M7.22 3.22a.75.75 0 0 1 1.06 0l5.5 5.5a.75.75 0 0 1 0 1.06l-5.5 5.5a.75.75 0 0 1-1.06-1.06L12.19 10l-4.97-4.97a.75.75 0 0 1 0-1.06Z"
                clipRule="evenodd"
              />
            </svg>
          </button>
        ) : (
          <>
            <span className="text-sm font-semibold text-gray-800 dark:text-gray-100 pl-1 truncate">Repos</span>
            <button
              type="button"
              onClick={toggleCollapsed}
              className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-300 shrink-0"
              title="Collapse sidebar"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5" aria-hidden>
                <path
                  fillRule="evenodd"
                  d="M12.78 3.22a.75.75 0 0 1 0 1.06L7.81 10l4.97 4.97a.75.75 0 0 1-1.06 1.06l-5.5-5.5a.75.75 0 0 1 0-1.06l5.5-5.5a.75.75 0 0 1 1.06 0Z"
                  clipRule="evenodd"
                />
              </svg>
            </button>
          </>
        )}
      </div>

      {!collapsed && (
        <div className="p-2 flex flex-col flex-1 min-h-0 gap-2">
          <button
            type="button"
            disabled={pulling}
            onClick={handlePullAll}
            className="w-full px-3 py-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 disabled:opacity-50 rounded-lg text-sm font-medium transition-colors cursor-pointer"
          >
            {pulling ? 'Pulling...' : 'Pull All'}
          </button>

          {pullMsg && (
            <p className="text-xs text-green-700 dark:text-green-300 bg-green-100/80 dark:bg-green-900/40 border border-green-300 dark:border-green-800 rounded-lg px-2 py-1.5">
              {pullMsg}
              <button type="button" onClick={() => setPullMsg(null)} className="ml-1 underline text-left">
                dismiss
              </button>
            </p>
          )}

          <ul className="text-sm flex-1 overflow-y-auto min-h-0 space-y-1 -mx-0.5 px-0.5">
            {repos.length === 0 ? (
              <li className="text-xs text-gray-500 dark:text-gray-400 px-1">No git repos in directory</li>
            ) : (
              repos.map((r) => (
                <li
                  key={r.name}
                  className="px-2 py-1.5 rounded-md border border-gray-200 dark:border-gray-700 bg-gray-50/80 dark:bg-gray-800/50"
                >
                  <div className="font-medium text-gray-900 dark:text-gray-100 truncate" title={r.name}>
                    {r.name}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 font-mono truncate" title={r.branch}>
                    {r.branch}
                  </div>
                </li>
              ))
            )}
          </ul>
        </div>
      )}

      {collapsed && (
        <div className="flex flex-col items-center py-2 gap-2">
          <button
            type="button"
            disabled={pulling}
            onClick={handlePullAll}
            className="p-2 rounded-lg bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 disabled:opacity-50 text-gray-800 dark:text-gray-100"
            title="Pull all repos"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5" aria-hidden>
              <path
                fillRule="evenodd"
                d="M10 3a.75.75 0 0 1 .75.75v5.19l1.72-1.72a.75.75 0 1 1 1.06 1.06l-3.25 3.25a.75.75 0 0 1-1.06 0L5.47 8.28a.75.75 0 1 1 1.06-1.06l1.72 1.72V3.75A.75.75 0 0 1 10 3Z"
                clipRule="evenodd"
              />
              <path d="M3.75 14.5a.75.75 0 0 1 .75-.75h11a.75.75 0 0 1 0 1.5h-11a.75.75 0 0 1-.75-.75Z" />
            </svg>
          </button>
        </div>
      )}
    </aside>
  );
}
