import type { Aircraft } from '../api/types.aircraft';

export interface AircraftDiff {
  added: Aircraft[];
  moved: Aircraft[];
  removed: string[];
}

const same = (a: Aircraft, b: Aircraft) =>
  a.lat === b.lat && a.lon === b.lon && a.alt_m === b.alt_m && a.name === b.name && a.aircraft === b.aircraft && a.coalition === b.coalition;

/** What to do to existing markers (keyed by ucid) so they match `next`: create, move/refresh, or remove. */
export function diffAircraft(prev: ReadonlyMap<string, Aircraft>, next: readonly Aircraft[]): AircraftDiff {
  const added: Aircraft[] = [];
  const moved: Aircraft[] = [];
  const seen = new Set<string>();
  for (const a of next) {
    seen.add(a.ucid);
    const old = prev.get(a.ucid);
    if (!old) added.push(a);
    else if (!same(old, a)) moved.push(a);
  }
  const removed = [...prev.keys()].filter((id) => !seen.has(id));
  return { added, moved, removed };
}

export const metersToFeet = (m: number): number => Math.round(m * 3.28084);
