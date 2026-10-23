import type { DtcModel } from '../../api/types.dtc';
import { isOutOfRange } from './radioRanges';
import type { Issue } from './validate';

interface Freq {
  radio: string;
  mhz: unknown;
}

const hasFreq = (s: unknown): s is { frequency_mhz?: unknown } => typeof s === 'object' && s !== null && 'frequency_mhz' in s;

function frequencies(model: DtcModel): Freq[] {
  const r = model.radios;
  if (!r) return [];
  const out: Freq[] = [];
  for (const radio of r.radios ?? []) for (const c of radio.channels ?? []) out.push({ radio: radio.id, mhz: c.frequency_mhz });
  for (const p of r.presets ?? []) for (const [id, s] of Object.entries(p.radios ?? {})) if (hasFreq(s)) out.push({ radio: id, mhz: s.frequency_mhz });
  const { HF, ...fixed } = r.initial ?? {};
  for (const [id, s] of Object.entries(fixed)) if (hasFreq(s)) out.push({ radio: id, mhz: s.frequency_mhz });
  for (const part of [HF?.rx, HF?.tx]) if (hasFreq(part)) out.push({ radio: 'HF', mhz: part.frequency_mhz });
  return out;
}

/** Hard: a frequency that is not a number > 0. Warning: outside the documented band (never blocks). */
export function radioIssues(model: DtcModel): Issue[] {
  const all = frequencies(model);
  const valid = (f: Freq): f is { radio: string; mhz: number } => typeof f.mhz === 'number' && Number.isFinite(f.mhz) && f.mhz > 0;
  const bad = all.filter((f) => !valid(f)).length;
  const range = all.filter(valid).filter((f) => isOutOfRange(model.aircraft, f.radio, f.mhz)).length;
  const out: Issue[] = [];
  if (bad > 0) out.push({ key: 'radioBadFrequency', severity: 'error', params: { count: bad } });
  if (range > 0) out.push({ key: 'radioRange', severity: 'warning', params: { count: range } });
  return out;
}

/** Fields whose current text is not valid yet (they revert on blur): the download waits. */
export const radioInputIssues = (invalid: number): Issue[] => (invalid > 0 ? [{ key: 'radioInvalidInput', severity: 'error', params: { count: invalid } }] : []);
