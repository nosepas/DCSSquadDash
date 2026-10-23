import type L from 'leaflet';
import type { NamedPlace } from '../../../lib/dtc/reference';
import { useTick } from '../../../hooks/useTick';
import { LayersPanel } from './LayersPanel';
import { useAirfieldLayer } from './useAirfieldLayer';
import { useFarpLayer } from './useFarpLayer';
import { useLayerPrefs } from './useLayerPrefs';
import { useRefPanes } from './refPanes';
import { useReferenceData } from './useReferenceData';
import { useReferenceServer } from './useReferenceServer';
import { useZoneLayer } from './useZoneLayer';

export const REFRESH_MS = 30_000;

interface Props {
  map: L.Map | null;
  terrain: string | null;
  /** Appends a named point to the active list (like a map click); null while nothing can be added. */
  onAdd: ((place: NamedPlace) => void) | null;
}

/** Display-only reference layers (airports, front line + zones, FARPs) and their control. Never part of the DTC model. */
export function ReferenceLayers({ map, terrain, onAdd }: Props) {
  const { prefs, toggle } = useLayerPrefs();
  const tick = useTick(REFRESH_MS, terrain !== null);
  const server = useReferenceServer(terrain, tick);
  const data = useReferenceData(terrain, server.selected?.server_id, prefs, tick);
  const panes = useRefPanes(map);
  const active = terrain !== null;

  useAirfieldLayer(map, panes, data.airfields.data, active && prefs.airports, onAdd);
  useZoneLayer(map, panes, data.zones.data, active && prefs.front);
  useFarpLayer(map, panes, data.farps.data, active && prefs.farps, onAdd);

  const problems = [
    prefs.airports && data.airfields.error ? 'dtc.layers.airportsError' : '',
    (prefs.front && data.zones.error) || (prefs.farps && data.farps.error) ? 'dtc.layers.stateError' : '',
  ].filter(Boolean);

  if (!active) return null;
  return (
    <LayersPanel
      prefs={prefs} onToggle={toggle} matches={server.matches} selectedId={server.selected?.server_id}
      onPickServer={server.choose} problems={problems}
    />
  );
}
