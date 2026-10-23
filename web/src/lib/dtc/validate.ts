import type { DtcAircraft, DtcModel, DtcPoint } from '../../api/types.dtc';
import { allLists, type ListRef } from './lists';
import { radioIssues } from './radioValidate';

export interface Issue {
  /** i18n key under `dtc.issues.` */
  key: string;
  params?: Record<string, string | number>;
  severity: 'error' | 'warning';
  ref?: ListRef;
  pointId?: string;
}

const isNum = (v: unknown): v is number => typeof v === 'number' && Number.isFinite(v);

function pointIssues(p: DtcPoint, ref: ListRef, position: number): Issue[] {
  const where = { ref, pointId: p.id, params: { n: position + 1 } };
  const out: Issue[] = [];
  if (!isNum(p.lat) || Math.abs(p.lat) > 90) out.push({ ...where, key: 'badLat', severity: 'error' });
  if (!isNum(p.lon) || Math.abs(p.lon) > 180) out.push({ ...where, key: 'badLon', severity: 'error' });
  if (p.elevation_m !== null && p.elevation_m !== undefined && !isNum(p.elevation_m)) out.push({ ...where, key: 'badElevation', severity: 'error' });
  return out;
}

function limitIssues(model: DtcModel, limits: Record<string, number | null>): Issue[] {
  const checks: [string, number, string][] = [
    ['waypoints', model.waypoints.length, 'tooManyWaypoints'],
    ['routes', model.routes.length, 'tooManyRoutes'],
    ['lines', model.lines.length, 'tooManyLines'],
  ];
  const out: Issue[] = [];
  for (const [name, count, key] of checks) {
    const limit = limits[name];
    if (typeof limit === 'number' && count > limit) {
      out.push({ key, severity: 'error', params: { count, limit }, ref: name === 'waypoints' ? { type: 'waypoints' } : undefined });
    }
  }
  return out;
}

/** Live checks before download: limits from /dtc/aircraft, map chosen, numbers sane. Warnings do not block. */
export function validateDraft(model: DtcModel, info: DtcAircraft | undefined): Issue[] {
  const issues: Issue[] = [];
  if (!info || !info.enabled) return [{ key: 'noAircraft', severity: 'error' }];
  if (!model.terrain) issues.push({ key: 'noTerrain', severity: 'error' });
  issues.push(...limitIssues(model, info.limits));
  let total = 0;
  let unknownElevation = 0;
  for (const { ref, points } of allLists(model)) {
    points.forEach((p, i) => {
      issues.push(...pointIssues(p, ref, i));
      if (p.elevation_m === null || p.elevation_m === undefined) unknownElevation += 1;
    });
    total += points.length;
  }
  issues.push(...radioIssues(model));
  if (total === 0) issues.push({ key: 'noPoints', severity: 'warning' });
  if (unknownElevation > 0) issues.push({ key: 'unknownElevation', severity: 'warning', params: { count: unknownElevation } });
  return issues;
}

export const blockingIssues = (issues: Issue[]): Issue[] => issues.filter((i) => i.severity === 'error');
