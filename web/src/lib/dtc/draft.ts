import type { DtcModel } from '../../api/types.dtc';
import type { DtcRadios } from '../../api/types.radios';
import { ensureIds } from './edit';
import { readStored, writeStored } from '../storage';
import { AH64_KINDS, AH64_MISSIONS, firstRef, type ListRef } from './lists';

export const DRAFT_KEY = 'fox3.dtc.draft.v1';

export interface Draft {
  model: DtcModel;
  /** From /dtc/import; null when the draft started from the built-in template. */
  templateId: string | null;
  /** Ids of points whose elevation was filled in automatically (approximate). */
  approx: Record<string, true>;
  active: ListRef;
  fileName: string | null;
  /** Radios as first loaded (defaults or imported file): reset target and "changed" markers. */
  radiosBase?: DtcRadios;
}

/** A fresh draft around a model that came from the server; the radios it carries become the baseline. */
export function newDraft(model: DtcModel, templateId: string | null = null, fileName: string | null = null): Draft {
  const withIds = ensureIds(model);
  return { model: withIds, templateId, approx: {}, active: firstRef(withIds), fileName, radiosBase: withIds.radios };
}

const isObj = (v: unknown): v is Record<string, unknown> => typeof v === 'object' && v !== null && !Array.isArray(v);

const isList = (v: unknown): boolean => Array.isArray(v) && v.every((x) => isObj(x) && Array.isArray(x.points));

/** The saved active list if it still exists in this model, else the first list (old or corrupt drafts must never crash the page). */
export function validActive(model: DtcModel, active: unknown): ListRef {
  if (isObj(active)) {
    const i = active.index;
    const inRange = (n: number) => typeof i === 'number' && Number.isInteger(i) && i >= 0 && i < n;
    if (active.type === 'waypoints') return { type: 'waypoints' };
    if (active.type === 'route' && inRange(model.routes.length)) return { type: 'route', index: i as number };
    if (active.type === 'line' && inRange(model.lines.length)) return { type: 'line', index: i as number };
    if (active.type === 'ah64' && model.aircraft === 'AH-64D_BLK_II' && AH64_MISSIONS.some((m) => m === active.mission)
        && AH64_KINDS.some((k) => k === active.kind)) return { type: 'ah64', mission: active.mission as number, kind: active.kind as string };
  }
  return firstRef(model);
}

/** Returns the draft only if it has the shape the editor relies on; anything else is discarded. */
export function parseDraft(raw: string | null): Draft | null {
  if (!raw) return null;
  try {
    const d: unknown = JSON.parse(raw);
    if (!isObj(d) || !isObj(d.model)) return null;
    const m = d.model;
    const ok = typeof m.aircraft === 'string' && Array.isArray(m.waypoints) && isList([{ points: m.waypoints }]) && isList(m.routes)
      && isList(m.lines) && isObj(m.aircraft_extra);
    if (!ok) return null;
    return {
      model: m as DtcModel,
      templateId: typeof d.templateId === 'string' ? d.templateId : null,
      approx: isObj(d.approx) ? (d.approx as Record<string, true>) : {},
      active: validActive(m as unknown as DtcModel, d.active),
      fileName: typeof d.fileName === 'string' ? d.fileName : null,
      ...(isObj(d.radiosBase) ? { radiosBase: d.radiosBase as DtcRadios } : {}),
    };
  } catch {
    return null;
  }
}

export const loadDraft = (): Draft | null => parseDraft(readStored(DRAFT_KEY));
export const saveDraft = (d: Draft | null): void => writeStored(DRAFT_KEY, d ? JSON.stringify(d) : null);
