import { useCallback } from 'react';
import type { DtcModel, DtcPoint } from '../../api/types.dtc';
import type { Draft } from '../../lib/dtc/draft';
import { addPoint, movePoint, newPoint, removePoint, updateExtra, updatePoint } from '../../lib/dtc/edit';
import { addF14Line, removeF14Line, setLineClosed, setRouteAsLine, setRouteName } from '../../lib/dtc/f14';
import { columnsFor } from '../../lib/dtc/listInfo';
import { referencePoint, type NamedPlace } from '../../lib/dtc/reference';
import { findPoint, firstRef, getPoints, type ListRef } from '../../lib/dtc/lists';
import type { Fill } from './useElevationFill';

interface Deps {
  draft: Draft | null;
  update: (fn: (d: Draft) => Draft) => void;
  editModel: (fn: (m: DtcModel) => DtcModel) => void;
  queueElevation: (ids: string[]) => void;
}

const dropFlag = (d: Draft, id: string | undefined): Draft['approx'] => {
  if (!id || !d.approx[id]) return d.approx;
  return Object.fromEntries(Object.entries(d.approx).filter(([k]) => k !== id)) as Draft['approx'];
};

/** Every user edit of the draft. Elevations are only auto-filled while empty or still approximate. */
export function useDtcActions({ draft, update, editModel, queueElevation }: Deps) {
  const active = draft?.active;

  const setActive = useCallback((ref: ListRef) => update((d) => ({ ...d, active: ref })), [update]);

  const addAt = useCallback((lat: number, lon: number) => {
    if (!active) return;
    const p = newPoint(lat, lon, active);
    editModel((m) => addPoint(m, active, p));
    if (p.id) queueElevation([p.id]);
  }, [active, editModel, queueElevation]);

  /** Airfield/FARP "Add as point": same path as a map click, with the place name. */
  const addPlace = useCallback((place: NamedPlace) => {
    if (!active || !draft) return;
    const p = referencePoint(place, active, columnsFor(draft.model, active));
    editModel((m) => addPoint(m, active, p));
    if (p.id) queueElevation([p.id]);
  }, [active, draft, editModel, queueElevation]);

  const dragTo = useCallback((id: string, lat: number, lon: number) => {
    update((d) => {
      const at = findPoint(d.model, id);
      return at ? { ...d, model: updatePoint(d.model, at.ref, at.index, { lat, lon }) } : d;
    });
    const at = draft && findPoint(draft.model, id);
    const p = draft && at ? getPoints(draft.model, at.ref)[at.index] : undefined;
    if (p && (p.elevation_m == null || draft?.approx[id])) queueElevation([id]);
  }, [draft, update, queueElevation]);

  const patch = useCallback((ref: ListRef, index: number, change: Partial<DtcPoint>) => {
    update((d) => {
      const id = getPoints(d.model, ref)[index]?.id;
      const manual = 'elevation_m' in change;
      return { ...d, model: updatePoint(d.model, ref, index, change), approx: manual ? dropFlag(d, id) : d.approx };
    });
  }, [update]);

  const extra = useCallback((ref: ListRef, index: number, key: string, value: unknown) => editModel((m) => updateExtra(m, ref, index, key, value)), [editModel]);
  const move = useCallback((ref: ListRef, from: number, to: number) => editModel((m) => movePoint(m, ref, from, to)), [editModel]);
  const remove = useCallback((ref: ListRef, index: number) => editModel((m) => removePoint(m, ref, index)), [editModel]);

  const applyFills = useCallback((fills: Fill[]) => {
    update((d) => {
      let next = d;
      for (const f of fills) {
        const at = findPoint(next.model, f.id);
        const p = at && getPoints(next.model, at.ref)[at.index];
        if (!at || !p || p.lat !== f.lat || p.lon !== f.lon) continue;  // moved again meanwhile: a newer lookup is queued
        if (p.elevation_m != null && !next.approx[f.id]) continue;  // the user typed a value: never overwrite it
        next = { ...next, model: updatePoint(next.model, at.ref, at.index, { elevation_m: f.elevation }), approx: { ...next.approx, [f.id]: true } };
      }
      return next;
    });
  }, [update]);

  const setTerrain = useCallback((terrain: string) => editModel((m) => ({ ...m, terrain })), [editModel]);
  const setName = useCallback((name: string) => editModel((m) => ({ ...m, name })), [editModel]);
  const routeName = useCallback((i: number, name: string) => editModel((m) => setRouteName(m, i, name)), [editModel]);
  const routeAsLine = useCallback((i: number, v: boolean) => editModel((m) => setRouteAsLine(m, i, v)), [editModel]);
  const closed = useCallback((i: number, v: boolean) => editModel((m) => setLineClosed(m, i, v)), [editModel]);

  const addLine = useCallback(() => {
    if (!draft) return;
    const route = active?.type === 'route' ? active.index : 0;
    const count = draft.model.lines.length;
    editModel((m) => addF14Line(m, route));
    update((d) => ({ ...d, active: { type: 'line', index: count } }));
  }, [draft, active, editModel, update]);

  const removeLine = useCallback((index: number) => {
    editModel((m) => removeF14Line(m, index));
    update((d) => ({ ...d, active: firstRef(d.model) }));
  }, [editModel, update]);

  return { setActive, addAt, addPlace, dragTo, patch, extra, move, remove, applyFills, setTerrain, setName, routeName, routeAsLine, closed, addLine, removeLine };
}
