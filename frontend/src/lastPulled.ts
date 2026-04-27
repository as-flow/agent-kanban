const LAST_PULLED_KEY = 'agent-kanban-last-pulled';

export function readLastPulledAt(): string | null {
  try {
    return localStorage.getItem(LAST_PULLED_KEY);
  } catch {
    return null;
  }
}

export const LAST_PULLED_EVENT = 'agent-kanban-last-pulled';

export function writeLastPulledNow(): void {
  try {
    localStorage.setItem(LAST_PULLED_KEY, new Date().toISOString());
    window.dispatchEvent(new CustomEvent(LAST_PULLED_EVENT));
  } catch {
    /* ignore */
  }
}

function formatRelative(iso: string): string {
  const t = new Date(iso).getTime();
  if (Number.isNaN(t)) return iso;
  const diffMs = Date.now() - t;
  const pastMs = diffMs >= 0 ? diffMs : 0;
  const sec = Math.floor(pastMs / 1000);
  const min = Math.floor(sec / 60);
  const hr = Math.floor(min / 60);
  const day = Math.floor(hr / 24);
  if (sec < 60) return 'just now';
  if (min < 60) return `${min}m ago`;
  if (hr < 24) return `${hr}h ago`;
  if (day < 7) return `${day}d ago`;
  return new Date(iso).toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    year: t < Date.now() - 365 * 24 * 60 * 60 * 1000 ? 'numeric' : undefined,
    hour: 'numeric',
    minute: '2-digit',
  });
}

export function formatLastPulledLabel(iso: string | null): string {
  if (!iso) return 'Never';
  return formatRelative(iso);
}
