import { describe, expect, it } from 'vitest';
import { addPoint, ensureIds, movePoint, newPoint, removePoint, updateExtra, updatePoint } from './edit';
import { addF14Line, lineRoute, removeF14Line, routeAsLine, setLineClosed, setRouteAsLine, setRouteName } from './f14';
import { ah64Model, f14Model, f16Model, pt } from './fixtures';
import { allLists, findPoint, getPoints, refKey, type ListRef } from './lists';
import { newModel } from './newModel';

const ids = (m: Parameters<typeof getPoints>[0], r: ListRef) => getPoints(m, r).map((p) => p.id);

describe('F-16 lists', () => {
  const wp: ListRef = { type: 'waypoints' };
  it('adds, removes and reorders steerpoints without touching lines or aircraft_extra', () => {
    const m = f16Model();
    const added = addPoint(m, wp, newPoint(1, 2, wp));
    expect(getPoints(added, wp)).toHaveLength(4);
    expect(added.lines).toBe(m.lines);
    expect(added.aircraft_extra).toBe(m.aircraft_extra);
    expect(added.threat_points).toBe(m.threat_points);
    expect(ids(removePoint(m, wp, 1), wp)).toEqual(['a', 'c']);
    expect(ids(movePoint(m, wp, 0, 2), wp)).toEqual(['b', 'c', 'a']);
    expect(ids(movePoint(m, wp, 2, 99), wp)).toEqual(['a', 'b', 'c']);
    expect(movePoint(m, wp, 1, 1)).toBe(m);
  });

  it('edits one line only', () => {
    const m = f16Model();
    const line: ListRef = { type: 'line', index: 1 };
    const next = addPoint(m, line, pt('x'));
    expect(ids(next, line)).toEqual(['l1', 'l2', 'x']);
    expect(next.lines[0]).toBe(m.lines[0]);
    expect(next.waypoints).toBe(m.waypoints);
  });

  it('updates a point and its extra keys immutably', () => {
    const m = f16Model();
    const moved = updatePoint(m, wp, 0, { lat: 1, elevation_m: null });
    expect(getPoints(moved, wp)[0]).toMatchObject({ lat: 1, elevation_m: null, id: 'a' });
    expect(getPoints(m, wp)[0]?.lat).toBe(40);
    const withExtra = updateExtra(m, wp, 0, 'spd', 300);
    expect(getPoints(withExtra, wp)[0]?.extra).toEqual({ spd: 300 });
    expect(getPoints(updateExtra(withExtra, wp, 0, 'spd', undefined), wp)[0]?.extra).toEqual({});
  });
});

describe('F-14 routes and lines', () => {
  it('starts with 12 empty slots and the f14 extra', () => {
    const m = newModel('F-14BU', null);
    expect(m.routes).toHaveLength(12);
    expect(m.routes.every((r) => r.name === '' && r.points.length === 0)).toBe(true);
    expect(m.aircraft_extra).toEqual({ f14: { route_as_line: Array<boolean>(12).fill(false), line_route: [] } });
  });

  it('edits one route slot only', () => {
    const m = f14Model();
    const r: ListRef = { type: 'route', index: 1 };
    const next = movePoint(addPoint(m, r, pt('r3')), r, 2, 0);
    expect(ids(next, r)).toEqual(['r3', 'r1', 'r2']);
    expect(next.routes[0]).toBe(m.routes[0]);
    expect(next.aircraft_extra).toBe(m.aircraft_extra);
  });

  it('keeps line_route in step with lines and edits route flags', () => {
    let m = addF14Line(addF14Line(f14Model(), 1), 4);
    expect(m.lines).toHaveLength(2);
    expect([lineRoute(m, 0), lineRoute(m, 1)]).toEqual([1, 4]);
    m = removeF14Line(m, 0);
    expect(m.lines).toHaveLength(1);
    expect(lineRoute(m, 0)).toBe(4);
    m = setRouteAsLine(m, 1, true);
    expect(routeAsLine(m, 1)).toBe(true);
    expect(routeAsLine(m, 0)).toBe(false);
    expect((m.aircraft_extra.f14 as { line_route: number[] }).line_route).toEqual([4]);
    expect(setRouteName(m, 3, 'X').routes[3]?.name).toBe('X');
    expect(setLineClosed(m, 0, true).lines[0]?.closed).toBe(true);
  });
});

describe('AH-64 groups', () => {
  it('addresses points by mission and kind', () => {
    const m = ah64Model();
    expect(ids(m, { type: 'ah64', mission: 1, kind: 'TGT' })).toEqual(['t1', 't2']);
    expect(ids(m, { type: 'ah64', mission: 2, kind: 'TGT' })).toEqual(['t3']);
  });

  it('edits one group and leaves the others and aircraft_extra alone', () => {
    const m = ah64Model();
    const g: ListRef = { type: 'ah64', mission: 1, kind: 'TGT' };
    const added = addPoint(m, g, newPoint(1, 1, g));
    expect(getPoints(added, g)).toHaveLength(3);
    expect(getPoints(added, g)[2]).toMatchObject({ kind: 'TGT', extra: { mission: 1 } });
    expect(ids(added, { type: 'ah64', mission: 1, kind: 'WPTHZ' })).toEqual(['w1']);
    expect(ids(added, { type: 'ah64', mission: 2, kind: 'TGT' })).toEqual(['t3']);
    expect(added.aircraft_extra).toBe(m.aircraft_extra);
    expect(ids(movePoint(m, g, 0, 1), g)).toEqual(['t2', 't1']);
    expect(ids(removePoint(m, g, 0), g)).toEqual(['t2']);
    expect(getPoints(m, g)[0]?.extra).toEqual({ mission: 1, id: 5 });
  });
});

describe('helpers', () => {
  it('lists every group per aircraft and finds points by id', () => {
    expect(allLists(f16Model()).map((l) => refKey(l.ref))).toEqual(['wp', 'l0', 'l1', 'l2', 'l3']);
    expect(allLists(ah64Model())).toHaveLength(6);
    expect(findPoint(f14Model(), 'r2')).toEqual({ ref: { type: 'route', index: 1 }, index: 1 });
    expect(findPoint(f14Model(), 'zzz')).toBeNull();
  });

  it('gives ids only to points that lack one and they are unique', () => {
    const m = ensureIds({ ...f14Model(), routes: [{ name: '', points: [{ lat: 1, lon: 2 }, { lat: 3, lon: 4 }, pt('keep')] }] });
    const got = getPoints(m, { type: 'route', index: 0 }).map((p) => p.id);
    expect(got[2]).toBe('keep');
    expect(new Set(got).size).toBe(3);
  });
});
