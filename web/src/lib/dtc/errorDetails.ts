import type { DtcModel } from '../../api/types.dtc';
import { allLists, type ListRef } from './lists';

export interface ServerIssue {
  message: string;
  /** Point the message talks about, when it can be located. */
  pointId?: string;
  ref?: ListRef;
}

function textOf(detail: unknown): string {
  if (typeof detail === 'string') return detail;
  if (detail && typeof detail === 'object') {
    const d = detail as { msg?: unknown; message?: unknown; loc?: unknown };
    const msg = typeof d.msg === 'string' ? d.msg : typeof d.message === 'string' ? d.message : JSON.stringify(detail);
    return Array.isArray(d.loc) ? `${d.loc.join('.')}: ${msg}` : msg;
  }
  return String(detail);
}

/** `waypoints[2]: ...`, `routes[1].points[0]: ...`, `lines/0/points/1/lat: ...` -> the point they talk about. */
function locate(model: DtcModel, text: string): Pick<ServerIssue, 'pointId' | 'ref'> {
  const path = (text.split(':')[0] ?? '').replace(/\[(\d+)\]/g, '.$1').split(/[./]/);
  const [part, first, , second] = path;
  if (first === undefined || !/^\d+$/.test(first)) return {};
  const i = Number(first);
  const lists = allLists(model);
  if (part === 'waypoints') {
    const p = model.waypoints[i];
    const ref = lists.find((l) => p !== undefined && l.points.includes(p))?.ref;
    return { pointId: p?.id, ref };
  }
  const type = part === 'routes' ? 'route' : part === 'lines' ? 'line' : null;
  const hit = lists.find((l) => l.ref.type === type && 'index' in l.ref && l.ref.index === i);
  const p = second === undefined ? undefined : hit?.points[Number(second)];
  return { ref: hit?.ref, pointId: p?.id };
}

/** The backend's `error.details` (strings, or objects as FastAPI sends them) as plain messages. */
export function detailTexts(details: unknown): string[] {
  const list = Array.isArray(details) ? details : details === undefined || details === null ? [] : [details];
  return list.map(textOf);
}

/** Same messages, tied to the point they talk about when the path in the message allows it. */
export function mapDetails(details: unknown, model: DtcModel): ServerIssue[] {
  return detailTexts(details).map((message) => ({ message, ...locate(model, message) }));
}
