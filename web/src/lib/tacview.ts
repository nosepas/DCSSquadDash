/** Seconds from the start of a recording -> "HH:MM:SS" (hours may exceed 24, never negative). */
export function formatOffset(totalSeconds: number): string {
  const s = Math.max(0, Math.floor(Number.isFinite(totalSeconds) ? totalSeconds : 0));
  const p = (n: number) => String(n).padStart(2, '0');
  return `${p(Math.floor(s / 3600))}:${p(Math.floor((s % 3600) / 60))}:${p(s % 60)}`;
}

/** "2026-03-01T18:02:00Z" -> "2026-03-01 18:02:00" (always UTC, as stored). */
export function formatUtc(iso: string | null): string {
  if (!iso) return '–';
  const m = /^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2}:\d{2})/.exec(iso);
  return m ? `${m[1]} ${m[2]}` : iso;
}

/** i18n key (under `tacview.errors.`) for a failed download. */
export function downloadErrorKey(status: number, code: string): string {
  if (code === 'server_unreachable' || status === 504) return 'server_unreachable';
  if (code === 'transfer_busy' || status === 429) return 'transfer_busy';
  if (status === 404) return 'not_found';
  if (status === 401) return 'unauthorized';
  if (status === 0) return 'network';
  return 'generic';
}

/** File name from a Content-Disposition header, falling back to `fallback`. */
export function filenameFromDisposition(header: string | null, fallback: string): string {
  const m = header ? /filename\*?=(?:UTF-8'')?"?([^";]+)"?/i.exec(header) : null;
  return m?.[1] ? decodeURIComponent(m[1]) : fallback;
}
