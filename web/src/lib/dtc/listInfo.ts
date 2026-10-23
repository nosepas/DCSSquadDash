import type { DtcModel } from '../../api/types.dtc';
import { lineRoute } from './f14';
import { allLists, type ListRef } from './lists';

/** Distinguishable on the dark basemap; index = position of the list in `allLists`. */
export const PALETTE = [
  '#f5b942', '#4da3ff', '#ff6b6b', '#4ade80', '#c084fc', '#22d3ee',
  '#fb923c', '#f472b6', '#a3e635', '#94a3b8', '#e879f9', '#facc15',
] as const;

export interface ListInfo {
  ref: ListRef;
  /** i18n key under `dtc.lists.` and its params. */
  labelKey: string;
  params: Record<string, string | number>;
  count: number;
  color: string;
  dashed: boolean;
}

function describe(model: DtcModel, ref: ListRef): Pick<ListInfo, 'labelKey' | 'params' | 'dashed'> {
  switch (ref.type) {
    case 'waypoints': return { labelKey: 'steerpoints', params: {}, dashed: false };
    case 'route': {
      const name = model.routes[ref.index]?.name ?? '';
      return { labelKey: name ? 'routeNamed' : 'route', params: { n: ref.index + 1, name }, dashed: false };
    }
    case 'ah64': return { labelKey: `ah64.${ref.kind}`, params: { mission: ref.mission }, dashed: ref.kind === 'WPTHZ' };
    case 'line':
      return model.aircraft === 'F-14BU'
        ? { labelKey: 'f14line', params: { n: ref.index + 1, route: lineRoute(model, ref.index) + 1 }, dashed: true }
        : { labelKey: 'line', params: { n: ref.index + 1 }, dashed: true };
  }
}

/** All lists the user can pick, with a colour each. AH-64 CTRLM lists only show when the file already has such points. */
export function listInfos(model: DtcModel): ListInfo[] {
  const infos = allLists(model).map(({ ref, points }, i) => ({
    ref, count: points.length, color: PALETTE[i % PALETTE.length] ?? '#fff', ...describe(model, ref),
  }));
  return infos.filter((l) => !(l.ref.type === 'ah64' && l.ref.kind === 'CTRLM' && l.count === 0));
}

export type Column = 'name' | 'note' | 'spd' | 'tot';

/** Text fields worth editing per aircraft: only those whose meaning is known and written to the file. */
export function columnsFor(model: DtcModel, ref: ListRef): Column[] {
  switch (model.aircraft) {
    case 'F-16C_50': return ['note'];
    case 'F-14BU': return ref.type === 'route' ? ['name', 'spd', 'tot'] : [];
    case 'AH-64D_BLK_II': return ['name', 'note'];
    default: return [];
  }
}
