import type { DtcModel, DtcPoint } from '../../api/types.dtc';
import { newModel } from './newModel';

export const pt = (id: string, lat = 40, lon = 2, extra?: Record<string, unknown>): DtcPoint => ({ id, lat, lon, elevation_m: 10, ...(extra ? { extra } : {}) });

export function f16Model(): DtcModel {
  const m = newModel('F-16C_50', 'Syria');
  return { ...m, waypoints: [pt('a'), pt('b'), pt('c')], lines: m.lines.map((l, i) => (i === 1 ? { ...l, points: [pt('l1'), pt('l2')] } : l)), aircraft_extra: { keep: { x: 1 } }, threat_points: [pt('t')] };
}

export function f14Model(): DtcModel {
  const m = newModel('F-14BU', 'Caucasus');
  return { ...m, routes: m.routes.map((r, i) => (i === 1 ? { name: 'PL2', points: [pt('r1'), pt('r2')] } : r)) };
}

export function ah64Model(): DtcModel {
  const m = newModel('AH-64D_BLK_II', 'Caucasus');
  const a = (id: string, kind: string, mission: number): DtcPoint => ({ ...pt(id), kind, extra: { mission, id: 5 } });
  return { ...m, waypoints: [a('t1', 'TGT', 1), a('w1', 'WPTHZ', 1), a('t2', 'TGT', 1), a('t3', 'TGT', 2)], aircraft_extra: { ah64: { enabled: { '1': { TGT: true } } } } };
}
