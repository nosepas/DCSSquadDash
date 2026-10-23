import { afterEach, describe, expect, it, vi } from 'vitest';
import { createPairingCode, updateServer } from './admin';
import { setCsrfToken } from './client';
import { fetchAircraft, fetchFarps, fetchServers } from './servers';
import { searchTacview, tacviewDownloadUrl } from './tacview';

function mockFetch(body: unknown = {}, status = 200) {
  const fn = vi.fn().mockResolvedValue(new Response(JSON.stringify(body), { status }));
  vi.stubGlobal('fetch', fn);
  return fn;
}
const initOf = (fn: ReturnType<typeof vi.fn>) => fn.mock.calls[0]?.[1] as RequestInit;

afterEach(() => {
  vi.unstubAllGlobals();
  setCsrfToken(null);
});

describe('new endpoints', () => {
  it('searches tacview with pilot and optional server filter', async () => {
    const fn = mockFetch([]);
    await searchTacview('Viper', 's1');
    expect(fn.mock.calls[0]?.[0]).toBe('/api/v1/tacview/search?pilot=Viper&server_id=s1');
    fn.mockResolvedValue(new Response('[]'));
    await searchTacview('Viper', undefined);
    expect(fn.mock.calls[1]?.[0]).toBe('/api/v1/tacview/search?pilot=Viper');
    expect(tacviewDownloadUrl(7)).toBe('/api/v1/tacview/files/7/download');
  });

  it('asks for aircraft with an optional coalition', async () => {
    const fn = mockFetch({ aircraft: [] });
    await fetchAircraft('s1', 'red');
    expect(fn.mock.calls[0]?.[0]).toBe('/api/v1/servers/s1/aircraft?coalition=red');
    fn.mockResolvedValue(new Response('{}'));
    await fetchAircraft('s1', undefined);
    expect(fn.mock.calls[1]?.[0]).toBe('/api/v1/servers/s1/aircraft');
  });

  it('reads the FARPs of a server and the terrain of the server list', async () => {
    const fn = mockFetch([{ name: 'FARP 1', lat: 1, lon: 2 }]);
    expect(await fetchFarps('s1')).toEqual([{ name: 'FARP 1', lat: 1, lon: 2 }]);
    expect(fn.mock.calls[0]?.[0]).toBe('/api/v1/servers/s1/farps');
    fn.mockResolvedValue(new Response(JSON.stringify([{ server_id: 's1', name: 'A', mission_type: 'foothold', terrain: 'Syria', online: true }])));
    expect((await fetchServers())[0]?.terrain).toBe('Syria');
  });

  it('PATCHes the server with CSRF and posts pairing codes', async () => {
    setCsrfToken('tok');
    const fn = mockFetch({});
    await updateServer('s1', { name: 'X' });
    expect(initOf(fn).method).toBe('PATCH');
    expect(JSON.parse(initOf(fn).body as string)).toEqual({ name: 'X' });
    expect((initOf(fn).headers as Record<string, string>)['X-CSRF-Token']).toBe('tok');
    fn.mockResolvedValue(new Response('{}', { status: 201 }));
    await createPairingCode('s1');
    expect(fn.mock.calls[1]?.[0]).toBe('/api/v1/admin/servers/s1/pairing-code');
  });

  it('surfaces 504 server_unreachable errors with their code', async () => {
    mockFetch({ error: { code: 'server_unreachable', message: 'agent did not answer' } }, 504);
    await expect(searchTacview('abc', undefined)).rejects.toMatchObject({ status: 504, code: 'server_unreachable' });
  });
});
