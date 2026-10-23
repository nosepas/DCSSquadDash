import type { DtcModel } from '../../api/types.dtc';
import { F14_ROUTE_SLOTS } from './f14';

/** Empty model for a fresh draft; shapes follow what each exporter expects (F-14: 12 slots, F-16: 4 lines). */
export function newModel(aircraft: string, terrain: string | null): DtcModel {
  const base: DtcModel = {
    model_version: 1, terrain, aircraft, dcs_version: null, waypoints: [], routes: [], lines: [], aircraft_extra: {},
  };
  if (aircraft === 'F-14BU') {
    return {
      ...base,
      routes: Array.from({ length: F14_ROUTE_SLOTS }, () => ({ name: '', points: [] })),
      aircraft_extra: { f14: { route_as_line: Array<boolean>(F14_ROUTE_SLOTS).fill(false), line_route: [] } },
    };
  }
  if (aircraft === 'F-16C_50') return { ...base, lines: [1, 2, 3, 4].map((n) => ({ name: `L${n}`, points: [] })) };
  return base;
}
