export type Axis = 'lat' | 'lon';
export type CoordResult = { ok: true; value: number } | { ok: false; reason: 'required' | 'invalid' | 'range' };

const RANGE: Record<Axis, number> = { lat: 90, lon: 180 };
const DECIMAL = /^[+-]?(\d+([.,]\d*)?|[.,]\d+)$/;

export function parseDecimal(text: string): number | null {
  const s = text.trim();
  if (!DECIMAL.test(s)) return null;
  const n = Number(s.replace(',', '.'));
  return Number.isFinite(n) ? n : null;
}

/** Decimal degrees ("41.5", "-2,3"), within [-90, 90] for latitude and [-180, 180] for longitude. */
export function parseCoord(text: string, axis: Axis): CoordResult {
  if (text.trim() === '') return { ok: false, reason: 'required' };
  const n = parseDecimal(text);
  if (n === null) return { ok: false, reason: 'invalid' };
  if (Math.abs(n) > RANGE[axis]) return { ok: false, reason: 'range' };
  return { ok: true, value: n };
}

/** Empty = unknown elevation (null); otherwise a finite number in metres. */
export function parseElevation(text: string): { ok: true; value: number | null } | { ok: false } {
  if (text.trim() === '') return { ok: true, value: null };
  const n = parseDecimal(text);
  return n === null ? { ok: false } : { ok: true, value: n };
}

/** Six decimals (~0.1 m) without trailing noise. */
export const formatCoord = (n: number): string => String(Math.round(n * 1e6) / 1e6);

export const formatElevation = (n: number | null | undefined): string => (n === null || n === undefined ? '' : String(Math.round(n * 10) / 10));

/** "HH:MM:SS" (the F-14 time over target) or empty. */
export const isTimeOfDay = (s: string): boolean => s === '' || /^([01]\d|2[0-3]):[0-5]\d:[0-5]\d$/.test(s);
