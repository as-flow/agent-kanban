import { useCallback, useSyncExternalStore } from 'react';

type Theme = 'light' | 'dark';
const STORAGE_KEY = 'droid-kanban-theme';

function getSnapshot(): Theme {
  return (localStorage.getItem(STORAGE_KEY) as Theme) ?? 'dark';
}

function getServerSnapshot(): Theme {
  return 'dark';
}

let listeners: (() => void)[] = [];

function subscribe(cb: () => void) {
  listeners = [...listeners, cb];
  return () => {
    listeners = listeners.filter((l) => l !== cb);
  };
}

function applyTheme(theme: Theme) {
  document.documentElement.classList.toggle('dark', theme === 'dark');
}

applyTheme(getSnapshot());

export function useTheme() {
  const theme = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  const toggle = useCallback(() => {
    const next: Theme = getSnapshot() === 'dark' ? 'light' : 'dark';
    localStorage.setItem(STORAGE_KEY, next);
    applyTheme(next);
    listeners.forEach((l) => l());
  }, []);

  return { theme, toggle } as const;
}
