import type { DtcModel } from '../../api/types.dtc';

export const F14_ROUTE_SLOTS = 12;

interface F14Meta {
  route_as_line: boolean[];
  line_route: number[];
}

function meta(model: DtcModel): F14Meta {
  const raw = (model.aircraft_extra.f14 ?? {}) as Partial<F14Meta>;
  return { route_as_line: raw.route_as_line ?? [], line_route: raw.line_route ?? [] };
}

function withMeta(model: DtcModel, next: Partial<F14Meta>): DtcModel {
  const f14 = { ...(model.aircraft_extra.f14 as object | undefined), ...meta(model), ...next };
  return { ...model, aircraft_extra: { ...model.aircraft_extra, f14 } };
}

export const lineRoute = (model: DtcModel, lineIndex: number): number => meta(model).line_route[lineIndex] ?? 0;
export const routeAsLine = (model: DtcModel, route: number): boolean => meta(model).route_as_line[route] === true;

export function setRouteName(model: DtcModel, route: number, name: string): DtcModel {
  return { ...model, routes: model.routes.map((r, i) => (i === route ? { ...r, name } : r)) };
}

export function setRouteAsLine(model: DtcModel, route: number, value: boolean): DtcModel {
  const flags = Array.from({ length: Math.max(F14_ROUTE_SLOTS, model.routes.length) }, (_, i) => routeAsLine(model, i));
  flags[route] = value;
  return withMeta(model, { route_as_line: flags });
}

/** Appends an empty line that belongs to route slot `route`. */
export function addF14Line(model: DtcModel, route: number): DtcModel {
  const next = { ...model, lines: [...model.lines, { name: '', closed: false, points: [] }] };
  return withMeta(next, { line_route: [...meta(model).line_route, route] });
}

export function removeF14Line(model: DtcModel, index: number): DtcModel {
  const next = { ...model, lines: model.lines.filter((_, i) => i !== index) };
  return withMeta(next, { line_route: meta(model).line_route.filter((_, i) => i !== index) });
}

export function setLineClosed(model: DtcModel, index: number, closed: boolean): DtcModel {
  return { ...model, lines: model.lines.map((l, i) => (i === index ? { ...l, closed } : l)) };
}
