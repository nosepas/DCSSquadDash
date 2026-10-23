/** Pure formatting helpers. */

export function formatKd(kd: number): string {
  return Number.isFinite(kd) ? kd.toFixed(2) : '–';
}

export function kdRatio(kills: number, deaths: number): number {
  return deaths > 0 ? kills / deaths : kills;
}

export function formatNumber(n: number, locale: string): string {
  return new Intl.NumberFormat(locale, { maximumFractionDigits: 1 }).format(n);
}

/** Seconds -> "mm:ss" (never negative). */
export function formatClock(totalSeconds: number): string {
  const s = Math.max(0, Math.floor(totalSeconds));
  const mm = String(Math.floor(s / 60)).padStart(2, '0');
  const ss = String(s % 60).padStart(2, '0');
  return `${mm}:${ss}`;
}

export function remainingSeconds(expiresAtIso: string, nowMs: number): number {
  const t = Date.parse(expiresAtIso);
  return Number.isNaN(t) ? 0 : Math.max(0, Math.ceil((t - nowMs) / 1000));
}

export function formatDateTime(iso: string | null | undefined, locale: string): string {
  if (!iso) return '–';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '–';
  return new Intl.DateTimeFormat(locale, { dateStyle: 'short', timeStyle: 'medium' }).format(d);
}

export function formatTime(iso: string, locale: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '–';
  return new Intl.DateTimeFormat(locale, { timeStyle: 'medium' }).format(d);
}

export function msToKnots(ms: number): number {
  return Math.round(ms * 1.94384);
}

/** Share of `part` in `total`, 0..100. */
export function percent(part: number, total: number): number {
  return total > 0 ? (part / total) * 100 : 0;
}
