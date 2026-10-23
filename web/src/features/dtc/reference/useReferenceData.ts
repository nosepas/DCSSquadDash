import { fetchDtcAirfields } from '../../../api/dtc';
import { fetchFarps, fetchMap } from '../../../api/servers';
import { useAsync, type AsyncState } from '../../../hooks/useAsync';
import type { LayerPrefs } from '../../../lib/dtc/layerPrefs';
import type { DtcAirfield } from '../../../api/types.dtc';
import type { Farp, MapData } from '../../../api/types';

export interface ReferenceData {
  airfields: AsyncState<DtcAirfield[]>;
  zones: AsyncState<MapData>;
  farps: AsyncState<Farp[]>;
}

interface Keyed<T> {
  key: string;
  value: T;
}

/** useAsync keeps the previous data while refetching; for another map/server that would be wrong, so results carry their key. */
function useKeyed<T>(key: string | null, load: (signal: AbortSignal) => Promise<T>, tick: number, enabled: boolean): AsyncState<T> {
  const state = useAsync<Keyed<T>>(async (signal) => ({ key: key ?? '', value: await load(signal) }), [key, tick], enabled && key !== null);
  const fresh = state.data !== undefined && state.data.key === key;
  return { ...state, data: fresh && enabled ? state.data?.value : undefined, error: enabled ? state.error : undefined };
}

/** Airfields of the DTC map (static) plus zones/FARPs of the reference server, refreshed with `tick` without touching the map view. */
export function useReferenceData(terrain: string | null, serverId: string | undefined, prefs: LayerPrefs, tick: number): ReferenceData {
  const airfields = useKeyed(terrain, (s) => fetchDtcAirfields(terrain ?? '', s), 0, prefs.airports);
  const sid = serverId ?? null;
  const zones = useKeyed(sid, (s) => fetchMap(sid ?? '', s), tick, prefs.front);
  const farps = useKeyed(sid, (s) => fetchFarps(sid ?? '', s), tick, prefs.farps);
  return { airfields, zones, farps };
}
