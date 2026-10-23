/** localStorage/sessionStorage wrappers that never throw (private windows, blocked storage). */
type Kind = 'local' | 'session';

function store(kind: Kind): Storage | null {
  try {
    return kind === 'local' ? window.localStorage : window.sessionStorage;
  } catch {
    return null;
  }
}

export function readStored(key: string, kind: Kind = 'local'): string | null {
  try {
    return store(kind)?.getItem(key) ?? null;
  } catch {
    return null;
  }
}

export function writeStored(key: string, value: string | null, kind: Kind = 'local'): void {
  try {
    if (value === null) store(kind)?.removeItem(key);
    else store(kind)?.setItem(key, value);
  } catch {
    /* storage unavailable: the app still works without persistence */
  }
}
