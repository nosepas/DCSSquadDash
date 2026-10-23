import { describe, expect, it } from 'vitest';
import type { ServerSummary } from '../../api/types';
import { matchingServers, pickReferenceServer, referencePoint } from './reference';

const s = (id: string, terrain: string | null, type: ServerSummary['mission_type'] = 'foothold'): ServerSummary => ({
  server_id: id, name: id, mission_type: type, online: true, terrain,
});
const list = [s('gen', 'Caucasus', 'generic'), s('a', 'Syria'), s('b', 'Caucasus'), s('c', 'Caucasus'), s('n', null)];

describe('reference server', () => {
  it('lists only Foothold servers with the exact terrain id', () => {
    expect(matchingServers(list, 'Caucasus').map((x) => x.server_id)).toEqual(['b', 'c']);
    expect(matchingServers(list, 'caucasus')).toEqual([]);
    expect(matchingServers(list, null)).toEqual([]);
  });

  it('prefers the user choice, then the header server, then the first match', () => {
    expect(pickReferenceServer(list, 'Caucasus', 'c')?.server_id).toBe('c');
    expect(pickReferenceServer(list, 'Caucasus', 'a')?.server_id).toBe('b');
    expect(pickReferenceServer(list, 'Caucasus', 'c', 'b')?.server_id).toBe('b');
    expect(pickReferenceServer(list, 'Caucasus', 'c', 'a')?.server_id).toBe('c');
  });

  it('ignores a header or chosen server that does not match, and gives none when nothing matches', () => {
    expect(pickReferenceServer(list, 'Syria', 'gen')?.server_id).toBe('a');
    expect(pickReferenceServer(list, 'Nevada', 'a')).toBeUndefined();
    expect(pickReferenceServer([], 'Syria')).toBeUndefined();
  });
});

describe('referencePoint', () => {
  const place = { name: 'Batumi', lat: 41.6, lon: 41.6 };

  it('builds a named point like a map click would, with an id and unknown elevation', () => {
    const p = referencePoint(place, { type: 'waypoints' }, []);
    expect(p).toMatchObject({ name: 'Batumi', lat: 41.6, lon: 41.6, elevation_m: null });
    expect(p.id).toBeTruthy();
    expect(p.note).toBeUndefined();
  });

  it('also fills the note when it is the only text column (F-16)', () => {
    expect(referencePoint(place, { type: 'waypoints' }, ['note']).note).toBe('Batumi');
    expect(referencePoint(place, { type: 'route', index: 0 }, ['name', 'spd']).note).toBeUndefined();
  });

  it('keeps the AH-64 kind and mission of the active list', () => {
    const p = referencePoint(place, { type: 'ah64', mission: 2, kind: 'TGT' }, ['name', 'note']);
    expect(p).toMatchObject({ kind: 'TGT', extra: { mission: 2 } });
  });
});
