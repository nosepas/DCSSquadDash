import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiError, setCsrfToken } from './client';
import { decodeWarnings, fetchDtcAircraft, fetchDefaultModel, fetchDtcAirfields, fetchDtcTerrains, fetchElevation, generateDtc, importDtc } from './dtc';
import type { DtcModel } from './types.dtc';

const model: DtcModel = { model_version: 1, terrain: 'Syria', aircraft: 'F-16C_50', waypoints: [], routes: [], lines: [], aircraft_extra: {} };
const mock = (res: Response) => {
  const fn = vi.fn().mockResolvedValue(res);
  vi.stubGlobal('fetch', fn);
  return fn;
};
const initOf = (fn: ReturnType<typeof vi.fn>, call = 0) => fn.mock.calls[call]?.[1] as RequestInit;
const headersOf = (fn: ReturnType<typeof vi.fn>) => initOf(fn).headers as Record<string, string>;

afterEach(() => {
  vi.unstubAllGlobals();
  setCsrfToken(null);
});

describe('dtc api', () => {
  it('reads the aircraft and terrain tables', async () => {
    const fn = mock(new Response('[]'));
    await fetchDtcAircraft();
    expect(fn.mock.calls[0]?.[0]).toBe('/api/v1/dtc/aircraft');
    fn.mockResolvedValue(new Response('[]'));
    await fetchDtcTerrains();
    expect(fn.mock.calls[1]?.[0]).toBe('/api/v1/dtc/terrains');
  });

  it('reads the airfields of a map for the terrain id', async () => {
    const fn = mock(new Response(JSON.stringify([{ name: 'Batumi', lat: 41.6, lon: 41.6, civil: true }])));
    const res = await fetchDtcAirfields('PersianGulf');
    expect(res[0]?.name).toBe('Batumi');
    expect(fn.mock.calls[0]?.[0]).toBe('/api/v1/dtc/airfields?terrain=PersianGulf');
  });

  it('asks for the default model of an aircraft with the chosen map (radios included)', async () => {
    const fn = mock(new Response(JSON.stringify({ ...model, radios: { radios: [] } })));
    const res = await fetchDefaultModel('F-16C_50', 'Syria');
    expect(res.radios).toEqual({ radios: [] });
    expect(fn.mock.calls[0]?.[0]).toBe('/api/v1/dtc/default-model?aircraft=F-16C_50&terrain=Syria');
  });

  it('leaves the map out of the default-model request when none is chosen yet', async () => {
    const fn = mock(new Response(JSON.stringify(model)));
    await fetchDefaultModel('F-14BU', null);
    expect(fn.mock.calls[0]?.[0]).toBe('/api/v1/dtc/default-model?aircraft=F-14BU');
  });

  it('surfaces a 422 for an aircraft that cannot start a DTC', async () => {
    mock(new Response(JSON.stringify({ error: { code: 'invalid', message: 'no', details: [] } }), { status: 422 }));
    await expect(fetchDefaultModel('FA-18C_hornet', null)).rejects.toMatchObject({ status: 422 });
  });

  it('surfaces a 404 for an unknown map', async () => {
    mock(new Response(JSON.stringify({ error: { code: 'not_found', message: 'unknown map' } }), { status: 404 }));
    await expect(fetchDtcAirfields('Mars')).rejects.toMatchObject({ status: 404 });
  });

  it('posts elevation batches as JSON with the CSRF header', async () => {
    setCsrfToken('tok');
    const fn = mock(new Response(JSON.stringify({ enabled: true, elevations: [12, null], attribution: 'x' })));
    const res = await fetchElevation([{ lat: 1, lon: 2 }, { lat: 3, lon: 4 }]);
    expect(res.elevations).toEqual([12, null]);
    expect(headersOf(fn)['X-CSRF-Token']).toBe('tok');
    expect(JSON.parse(initOf(fn).body as string)).toEqual({ points: [{ lat: 1, lon: 2 }, { lat: 3, lon: 4 }] });
  });

  it('imports the raw file as the body, not wrapped in JSON', async () => {
    setCsrfToken('tok');
    const fn = mock(new Response(JSON.stringify({ model, warnings: ['w'], template_id: 't1' })));
    const file = new Blob(['{"type":"F-16C_50"}']);
    const res = await importDtc(file);
    expect(res.template_id).toBe('t1');
    expect(fn.mock.calls[0]?.[0]).toBe('/api/v1/dtc/import');
    expect(initOf(fn).body).toBe(file);
    expect(headersOf(fn)['X-CSRF-Token']).toBe('tok');
    expect(headersOf(fn)['Content-Type']).toBe('application/octet-stream');
  });

  it('generates a blob with filename and decoded warnings, sending template_id only when present', async () => {
    setCsrfToken('tok');
    const warnings = encodeURIComponent(JSON.stringify(['waypoint 1: elevation unknown, 0 written']));
    const fn = mock(new Response('{"type":"F-16C_50"}', { headers: { 'Content-Disposition': 'attachment; filename="F-16C_50_Strike_1.dtc"', 'X-DTC-Warnings': warnings } }));
    const out = await generateDtc(model, 'tpl', 'fallback.dtc');
    expect(out.filename).toBe('F-16C_50_Strike_1.dtc');
    expect(out.warnings).toEqual(['waypoint 1: elevation unknown, 0 written']);
    expect(out.blob.size).toBe('{"type":"F-16C_50"}'.length);
    expect(JSON.parse(initOf(fn).body as string)).toEqual({ model, template_id: 'tpl' });
    expect(headersOf(fn)['X-CSRF-Token']).toBe('tok');
    fn.mockResolvedValue(new Response('{}'));
    const plain = await generateDtc(model, null, 'fallback.dtc');
    expect(plain.filename).toBe('fallback.dtc');
    expect(plain.warnings).toEqual([]);
    expect(JSON.parse(initOf(fn, 1).body as string)).toEqual({ model });
  });

  it('raises ApiError with the 422 details', async () => {
    mock(new Response(JSON.stringify({ error: { code: 'invalid', message: 'bad', details: ['waypoints[0]: lat'] } }), { status: 422 }));
    const err = await generateDtc(model, null, 'x.dtc').catch((e: unknown) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect(err).toMatchObject({ status: 422, details: ['waypoints[0]: lat'] });
  });

  it('maps a dropped connection to a network error', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('failed')));
    await expect(importDtc(new Blob(['x']))).rejects.toMatchObject({ status: 0, code: 'network' });
  });

  it('decodes the warnings header defensively', () => {
    expect(decodeWarnings(null)).toEqual([]);
    expect(decodeWarnings('%5B%22a%22%2C1%5D')).toEqual(['a']);
    expect(decodeWarnings('%E0%A4%A')).toEqual([]);
    expect(decodeWarnings(encodeURIComponent('{"a":1}'))).toEqual([]);
  });
});
