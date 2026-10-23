const MAX_LENGTH = 512;
const BACKSLASH = '\\';

function hasControlChar(s: string): boolean {
  for (let i = 0; i < s.length; i++) {
    const c = s.charCodeAt(i);
    if (c < 0x20 || c === 0x7f) return true;
  }
  return false;
}

/** Only same-origin absolute paths are accepted as a post-login destination; anything else becomes "/". */
export function safeNext(raw: string | null | undefined): string {
  if (typeof raw !== 'string' || raw.length === 0 || raw.length > MAX_LENGTH) return '/';
  if (raw[0] !== '/' || raw[1] === '/' || raw[1] === BACKSLASH) return '/';
  if (raw.includes(BACKSLASH) || hasControlChar(raw)) return '/';
  try {
    return new URL(raw, window.location.origin).origin === window.location.origin ? raw : '/';
  } catch {
    return '/';
  }
}
