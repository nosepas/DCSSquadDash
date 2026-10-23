import { readStored, writeStored } from '../storage';

export interface LayerPrefs {
  airports: boolean;
  front: boolean;
  farps: boolean;
}

export const LAYER_PREFS_KEY = 'fox3.dtc.layers';
export const DEFAULT_LAYER_PREFS: LayerPrefs = { airports: true, front: true, farps: true };

/** Each flag falls back to its default when missing or not a boolean; garbage as a whole gives the defaults. */
export function parseLayerPrefs(raw: string | null): LayerPrefs {
  if (!raw) return DEFAULT_LAYER_PREFS;
  try {
    const v: unknown = JSON.parse(raw);
    if (typeof v !== 'object' || v === null || Array.isArray(v)) return DEFAULT_LAYER_PREFS;
    const o = v as Record<string, unknown>;
    const flag = (k: keyof LayerPrefs): boolean => (typeof o[k] === 'boolean' ? (o[k] as boolean) : DEFAULT_LAYER_PREFS[k]);
    return { airports: flag('airports'), front: flag('front'), farps: flag('farps') };
  } catch {
    return DEFAULT_LAYER_PREFS;
  }
}

export const loadLayerPrefs = (): LayerPrefs => parseLayerPrefs(readStored(LAYER_PREFS_KEY));
export const saveLayerPrefs = (p: LayerPrefs): void => writeStored(LAYER_PREFS_KEY, JSON.stringify(p));
