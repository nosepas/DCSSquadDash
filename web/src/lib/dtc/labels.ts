/** Airfield names are only written on the map from this zoom level; below it hovering a dot shows the name. */
export const LABEL_MIN_ZOOM = 8;
/** Labels drawn at once are capped so a dense map never creates hundreds of DOM nodes. */
export const LABEL_CAP = 60;

export const labelsVisible = (zoom: number): boolean => zoom >= LABEL_MIN_ZOOM;

export interface Box {
  south: number;
  west: number;
  north: number;
  east: number;
}

/** The places that get a written label: none while zoomed out, otherwise those inside the view (first `cap` of them). */
export function labelCandidates<T extends { lat: number; lon: number }>(items: readonly T[], box: Box, zoom: number, cap = LABEL_CAP): T[] {
  if (!labelsVisible(zoom)) return [];
  const out: T[] = [];
  for (const it of items) {
    if (it.lat < box.south || it.lat > box.north || it.lon < box.west || it.lon > box.east) continue;
    out.push(it);
    if (out.length >= cap) break;
  }
  return out;
}
