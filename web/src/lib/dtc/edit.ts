import type { DtcModel, DtcPoint } from '../../api/types.dtc';
import { getPoints, setPoints, type ListRef } from './lists';

let counter = 0;
/** Unique, UI-assigned point id. The exporters ignore the top-level `id`, so it never reaches the .dtc. */
export const newPointId = (): string => `ui-${Date.now().toString(36)}-${(counter++).toString(36)}`;

export function newPoint(lat: number, lon: number, ref: ListRef): DtcPoint {
  const p: DtcPoint = { id: newPointId(), lat, lon, elevation_m: null };
  if (ref.type === 'ah64') {
    p.kind = ref.kind;
    p.extra = { mission: ref.mission };
  }
  return p;
}

export const addPoint = (model: DtcModel, ref: ListRef, p: DtcPoint): DtcModel =>
  setPoints(model, ref, [...getPoints(model, ref), p]);

export const removePoint = (model: DtcModel, ref: ListRef, index: number): DtcModel =>
  setPoints(model, ref, getPoints(model, ref).filter((_, i) => i !== index));

/** Moves the point at `from` to position `to` (clamped); a no-op returns the same model. */
export function movePoint(model: DtcModel, ref: ListRef, from: number, to: number): DtcModel {
  const pts = getPoints(model, ref);
  const target = Math.max(0, Math.min(pts.length - 1, to));
  if (from === target || from < 0 || from >= pts.length) return model;
  const next = [...pts];
  const [moved] = next.splice(from, 1);
  if (moved) next.splice(target, 0, moved);
  return setPoints(model, ref, next);
}

export const updatePoint = (model: DtcModel, ref: ListRef, index: number, patch: Partial<DtcPoint>): DtcModel =>
  setPoints(model, ref, getPoints(model, ref).map((p, i) => (i === index ? { ...p, ...patch } : p)));

/** Sets or removes (undefined) one key of the point's `extra`, e.g. the F-14 `spd`/`tot`. */
export function updateExtra(model: DtcModel, ref: ListRef, index: number, key: string, value: unknown): DtcModel {
  const p = getPoints(model, ref)[index];
  if (!p) return model;
  const rest = Object.entries(p.extra ?? {}).filter(([k]) => k !== key);
  const extra = Object.fromEntries(value === undefined ? rest : [...rest, [key, value]]);
  return updatePoint(model, ref, index, { extra });
}

/** Gives every point without an id a unique one (imported F-14/AH-64 points have none). Existing ids are kept. */
export function ensureIds(model: DtcModel): DtcModel {
  const fix = (pts: DtcPoint[]) => pts.map((p) => (p.id ? p : { ...p, id: newPointId() }));
  return {
    ...model,
    waypoints: fix(model.waypoints),
    routes: model.routes.map((r) => ({ ...r, points: fix(r.points) })),
    lines: model.lines.map((l) => ({ ...l, points: fix(l.points) })),
  };
}
