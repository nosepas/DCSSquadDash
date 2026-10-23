import type { DtcModel, DtcPoint } from '../../api/types.dtc';

/** Identifies one editable list of points inside the neutral model. */
export type ListRef =
  | { type: 'waypoints' }
  | { type: 'route'; index: number }
  | { type: 'line'; index: number }
  | { type: 'ah64'; mission: number; kind: string };

export const AH64_KINDS = ['TGT', 'WPTHZ', 'CTRLM'] as const;
export const AH64_MISSIONS = [1, 2] as const;

export const refKey = (r: ListRef): string => {
  switch (r.type) {
    case 'waypoints': return 'wp';
    case 'route': return `r${r.index}`;
    case 'line': return `l${r.index}`;
    case 'ah64': return `a${r.mission}${r.kind}`;
  }
};

export const sameRef = (a: ListRef, b: ListRef): boolean => refKey(a) === refKey(b);

export const missionOf = (p: DtcPoint): number => {
  const m = p.extra?.mission;
  return typeof m === 'number' ? m : 1;
};

const inAh64 = (p: DtcPoint, r: { mission: number; kind: string }): boolean => p.kind === r.kind && missionOf(p) === r.mission;

const EMPTY: DtcPoint[] = [];

export function getPoints(model: DtcModel, ref: ListRef): DtcPoint[] {
  switch (ref.type) {
    case 'waypoints': return model.waypoints;
    case 'route': return model.routes[ref.index]?.points ?? EMPTY;
    case 'line': return model.lines[ref.index]?.points ?? EMPTY;
    case 'ah64': return model.waypoints.filter((p) => inAh64(p, ref));
  }
}

function at<T>(arr: T[], i: number, fn: (x: T) => T): T[] {
  return arr.map((x, j) => (j === i ? fn(x) : x));
}

/** Replaces one list's points. Every other list and `aircraft_extra` keep their identity (not copied). */
export function setPoints(model: DtcModel, ref: ListRef, points: DtcPoint[]): DtcModel {
  switch (ref.type) {
    case 'waypoints': return { ...model, waypoints: points };
    case 'route': return { ...model, routes: at(model.routes, ref.index, (r) => ({ ...r, points })) };
    case 'line': return { ...model, lines: at(model.lines, ref.index, (l) => ({ ...l, points })) };
    case 'ah64': return { ...model, waypoints: [...model.waypoints.filter((p) => !inAh64(p, ref)), ...points] };
  }
}

/** Every list of the model with its points (map drawing, elevation fill, error lookup). */
export function allLists(model: DtcModel): { ref: ListRef; points: DtcPoint[] }[] {
  const out: { ref: ListRef; points: DtcPoint[] }[] = [];
  if (model.aircraft === 'AH-64D_BLK_II') {
    for (const mission of AH64_MISSIONS) {
      for (const kind of AH64_KINDS) {
        const ref: ListRef = { type: 'ah64', mission, kind };
        out.push({ ref, points: getPoints(model, ref) });
      }
    }
    return out;
  }
  if (model.aircraft === 'F-14BU') model.routes.forEach((r, index) => out.push({ ref: { type: 'route', index }, points: r.points }));
  else out.push({ ref: { type: 'waypoints' }, points: model.waypoints });
  model.lines.forEach((l, index) => out.push({ ref: { type: 'line', index }, points: l.points }));
  return out;
}

export function findPoint(model: DtcModel, id: string): { ref: ListRef; index: number } | null {
  for (const { ref, points } of allLists(model)) {
    const index = points.findIndex((p) => p.id === id);
    if (index >= 0) return { ref, index };
  }
  return null;
}

/** First list the user can see (AH-64 CTRLM lists are hidden while empty). */
export const firstRef = (model: DtcModel): ListRef =>
  allLists(model).find((l) => !(l.ref.type === 'ah64' && l.ref.kind === 'CTRLM' && l.points.length === 0))?.ref ?? { type: 'waypoints' };
