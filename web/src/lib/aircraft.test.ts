import { describe, expect, it } from 'vitest';
import type { Aircraft } from '../api/types.aircraft';
import { diffAircraft, metersToFeet } from './aircraft';

const plane = (ucid: string, lat = 43, lon = 41, alt_m: number | null = 1000): Aircraft => ({
  ucid, name: ucid, coalition: 'blue', aircraft: 'F-16C_50', lat, lon, alt_m, in_air: true,
});

describe('diffAircraft', () => {
  const prev = new Map([plane('a'), plane('b')].map((p) => [p.ucid, p]));

  it('adds new aircraft, moves changed ones, removes the missing and leaves unchanged alone', () => {
    const d = diffAircraft(prev, [plane('a'), plane('b', 44), plane('c')]);
    expect(d.added.map((p) => p.ucid)).toEqual(['c']);
    expect(d.moved.map((p) => p.ucid)).toEqual(['b']);
    expect(d.removed).toEqual([]);
    expect(diffAircraft(prev, [plane('b')]).removed).toEqual(['a']);
  });

  it('treats an altitude change as a move and an empty list as removing everything', () => {
    expect(diffAircraft(prev, [plane('a', 43, 41, 2000), plane('b')]).moved.map((p) => p.ucid)).toEqual(['a']);
    expect(diffAircraft(prev, []).removed.sort()).toEqual(['a', 'b']);
  });

  it('converts metres to feet', () => {
    expect(metersToFeet(1000)).toBe(3281);
  });
});
