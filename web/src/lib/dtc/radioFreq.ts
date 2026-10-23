import { parseDecimal } from './coords';

export type FreqResult = { ok: true; value: number } | { ok: false; reason: 'required' | 'invalid' | 'positive' };

/** MHz typed with a dot or a comma, rounded to 3 decimals (kHz); must be a number greater than 0. */
export function parseFrequency(text: string): FreqResult {
  if (text.trim() === '') return { ok: false, reason: 'required' };
  const n = parseDecimal(text);
  if (n === null) return { ok: false, reason: 'invalid' };
  const value = Math.round(n * 1000) / 1000;
  return value > 0 ? { ok: true, value } : { ok: false, reason: 'positive' };
}

/** At most 3 decimals, no trailing zeros ("251", "127.5"). */
export const formatFrequency = (n: number | undefined): string => (typeof n === 'number' && Number.isFinite(n) ? String(Math.round(n * 1000) / 1000) : '');

export type IntResult = { ok: true; value: number } | { ok: false };

/** Whole number within [min, max] (raw DCS codes, preset numbers). */
export function parseWhole(text: string, min: number, max = Number.MAX_SAFE_INTEGER): IntResult {
  const s = text.trim();
  if (!/^\d+$/.test(s)) return { ok: false };
  const n = Number(s);
  return n >= min && n <= max ? { ok: true, value: n } : { ok: false };
}
