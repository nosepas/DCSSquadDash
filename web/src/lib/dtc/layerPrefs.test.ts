import { beforeEach, describe, expect, it } from 'vitest';
import { DEFAULT_LAYER_PREFS, LAYER_PREFS_KEY, loadLayerPrefs, parseLayerPrefs, saveLayerPrefs } from './layerPrefs';

describe('layer preferences', () => {
  beforeEach(() => window.localStorage.clear());

  it('starts with every layer on', () => {
    expect(loadLayerPrefs()).toEqual({ airports: true, front: true, farps: true });
  });

  it('round-trips through localStorage', () => {
    saveLayerPrefs({ airports: false, front: true, farps: false });
    expect(loadLayerPrefs()).toEqual({ airports: false, front: true, farps: false });
  });

  it('falls back to the defaults on a corrupt value', () => {
    for (const raw of [null, '', 'not json', '[]', 'null', '42', '"x"']) expect(parseLayerPrefs(raw)).toEqual(DEFAULT_LAYER_PREFS);
    window.localStorage.setItem(LAYER_PREFS_KEY, '{oops');
    expect(loadLayerPrefs()).toEqual(DEFAULT_LAYER_PREFS);
  });

  it('keeps valid flags and defaults the rest', () => {
    expect(parseLayerPrefs('{"airports":false,"front":"yes"}')).toEqual({ airports: false, front: true, farps: true });
  });
});
