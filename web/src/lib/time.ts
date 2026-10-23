/** "3 minutes ago" style text for an ISO timestamp; falls back to the dash for missing/invalid values. */
export function relativeTime(iso: string | null | undefined, nowMs: number, locale: string): string {
  const t = iso ? Date.parse(iso) : Number.NaN;
  if (Number.isNaN(t)) return '–';
  const diffS = Math.round((t - nowMs) / 1000);
  const rtf = new Intl.RelativeTimeFormat(locale, { numeric: 'auto' });
  const abs = Math.abs(diffS);
  if (abs < 60) return rtf.format(diffS, 'second');
  if (abs < 3600) return rtf.format(Math.round(diffS / 60), 'minute');
  if (abs < 86400) return rtf.format(Math.round(diffS / 3600), 'hour');
  return rtf.format(Math.round(diffS / 86400), 'day');
}
