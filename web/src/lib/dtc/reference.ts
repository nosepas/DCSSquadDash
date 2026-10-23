import type { ServerSummary } from '../../api/types';
import type { DtcPoint } from '../../api/types.dtc';
import { newPoint } from './edit';
import type { Column } from './listInfo';
import type { ListRef } from './lists';

/** Foothold servers currently playing exactly this DCS map (their state is what the reference layers draw). */
export function matchingServers(servers: readonly ServerSummary[], terrain: string | null): ServerSummary[] {
  if (!terrain) return [];
  return servers.filter((s) => s.mission_type === 'foothold' && s.terrain === terrain);
}

/** Reference server: the user's explicit choice, else the header's server, else the first match, else none. */
export function pickReferenceServer(
  servers: readonly ServerSummary[], terrain: string | null, headerId?: string, chosenId?: string,
): ServerSummary | undefined {
  const matches = matchingServers(servers, terrain);
  return matches.find((s) => s.server_id === chosenId) ?? matches.find((s) => s.server_id === headerId) ?? matches[0];
}

export interface NamedPlace {
  name: string;
  lat: number;
  lon: number;
}

/**
 * Point for an airfield/FARP, built exactly like a map click (so it joins the active list and gets its elevation looked up).
 * Aircraft whose only text column is the note (F-16) get the name there too, because that is what its file stores.
 */
export function referencePoint(place: NamedPlace, ref: ListRef, columns: readonly Column[]): DtcPoint {
  const p = newPoint(place.lat, place.lon, ref);
  p.name = place.name;
  if (columns.includes('note') && !columns.includes('name')) p.note = place.name;
  return p;
}
