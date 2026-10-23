import { describe, expect, it } from 'vitest';
import type { DtcAircraft } from '../../api/types.dtc';
import { addPoint, newPoint, updatePoint } from './edit';
import { f14Model, f16Model } from './fixtures';
import type { ListRef } from './lists';
import { newModel } from './newModel';
import { blockingIssues, validateDraft } from './validate';

const f16: DtcAircraft = { id: 'F-16C_50', label: 'F-16C', enabled: true, supports: [], unsupported: [], limits: { waypoints: 25, lines: 4 }, notes: [] };
const keys = (m: Parameters<typeof validateDraft>[0], a: DtcAircraft | undefined = f16) => validateDraft(m, a).map((i) => i.key);
const wp: ListRef = { type: 'waypoints' };

describe('validateDraft', () => {
  it('accepts a complete F-16 draft', () => {
    expect(blockingIssues(validateDraft(f16Model(), f16))).toEqual([]);
  });

  it('requires an enabled aircraft and a terrain', () => {
    expect(validateDraft(f16Model(), undefined).map((i) => i.key)).toEqual(['noAircraft']);
    expect(keys({ ...f16Model(), terrain: null })).toContain('noTerrain');
  });

  it('flags more steerpoints than the limit', () => {
    let m = f16Model();
    for (let i = 0; i < 22; i += 1) m = addPoint(m, wp, newPoint(1, 1, wp));
    expect(keys(m)).not.toContain('tooManyWaypoints');  // 25 is allowed
    m = addPoint(m, wp, newPoint(1, 1, wp));
    const issue = validateDraft(m, f16).find((i) => i.key === 'tooManyWaypoints');
    expect(issue?.params).toEqual({ count: 26, limit: 25 });
    expect(blockingIssues(validateDraft(m, f16))).toContainEqual(issue);
  });

  it('flags out-of-range numbers and only warns about unknown elevations or empty drafts', () => {
    const bad = updatePoint(f16Model(), wp, 0, { lat: 95, elevation_m: null });
    const issues = validateDraft(bad, f16);
    expect(issues.find((i) => i.key === 'badLat')?.severity).toBe('error');
    expect(issues.find((i) => i.key === 'unknownElevation')?.severity).toBe('warning');
    const empty = validateDraft(newModel('F-14BU', 'Caucasus'), { ...f16, id: 'F-14BU', limits: { routes: 12 } });
    expect(empty.map((i) => i.key)).toContain('noPoints');
    expect(blockingIssues(empty)).toEqual([]);
  });

  it('applies the route limit', () => {
    const m = { ...f14Model(), routes: [...f14Model().routes, { name: '', points: [] }] };
    expect(keys(m, { ...f16, limits: { routes: 12 } })).toContain('tooManyRoutes');
  });
});
