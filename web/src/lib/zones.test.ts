import { describe, expect, it } from 'vitest';
import type { Zone } from '../api/types';
import { connectionSegments, countByCoalition, zoneSetKey } from './zones';

const z = (name: string, coalition: Zone['coalition'], lat: number | null = 1, lon: number | null = 2): Zone => ({
  name, coalition, is_hq: false, at_risk: false, level: 1, lat, lon,
});

describe('zones helpers', () => {
  const zones = [z('A', 'red'), z('B', 'blue'), z('C', 'red'), z('D', 'neutral'), z('E', 'blue', null, null)];

  it('marks only opposing-coalition connections as front and skips unlocated zones', () => {
    const segs = connectionSegments(zones, [
      { from: 'A', to: 'B' }, { from: 'A', to: 'C' }, { from: 'A', to: 'D' }, { from: 'A', to: 'E' }, { from: 'A', to: 'X' },
    ]);
    expect(segs.map((s) => s.front)).toEqual([true, false, false]);
  });

  it('counts zones per coalition', () => {
    expect(countByCoalition(zones)).toEqual({ red: 2, blue: 2, neutral: 1 });
  });

  it('zoneSetKey ignores order, coalition changes and unlocated zones, but changes with another map', () => {
    const key = zoneSetKey([z('B', 'blue'), z('A', 'red'), z('X', 'red', null, null)]);
    expect(zoneSetKey([z('A', 'blue'), z('B', 'red')])).toBe(key);
    expect(zoneSetKey([z('A', 'red'), z('Hmeimim', 'blue')])).not.toBe(key);
  });
});
