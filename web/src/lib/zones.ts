import type { Connection, LatLon, Zone } from '../api/types';

export interface Segment {
  from: LatLon;
  to: LatLon;
  front: boolean;
}

export function hasPosition(z: Zone): z is Zone & { lat: number; lon: number } {
  return z.lat !== null && z.lon !== null;
}

/** Connections between located zones; `front` is true when the two sides are opposing coalitions. */
export function connectionSegments(zones: Zone[], connections: Connection[]): Segment[] {
  const byName = new Map(zones.filter(hasPosition).map((z) => [z.name, z]));
  const out: Segment[] = [];
  for (const c of connections) {
    const a = byName.get(c.from);
    const b = byName.get(c.to);
    if (!a || !b) continue;
    const front = a.coalition !== 'neutral' && b.coalition !== 'neutral' && a.coalition !== b.coalition;
    out.push({ from: [a.lat, a.lon], to: [b.lat, b.lon], front });
  }
  return out;
}

/** Identifies "which map this is" (the set of zone names): when it changes, the view must be re-fitted. */
export function zoneSetKey(zones: Zone[]): string {
  return zones.filter(hasPosition).map((z) => z.name).sort().join('|');
}

export function countByCoalition(zones: Zone[]): Record<Zone['coalition'], number> {
  const counts = { red: 0, blue: 0, neutral: 0 };
  for (const z of zones) counts[z.coalition] += 1;
  return counts;
}
