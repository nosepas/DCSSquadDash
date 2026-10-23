import { afterEach, describe, expect, it, vi } from 'vitest';
import en from '../i18n/en.json';
import { ApiError, setCsrfToken } from './client';
import { getAgentPackageInfo, packageErrorKey, requestAgentPackage } from './agentPackage';

const errorBody = (code: string, status: number) =>
  new Response(JSON.stringify({ error: { code, message: code } }), { status, headers: { 'Content-Type': 'application/json' } });

function mockFetch(res: Response) {
  const fn = vi.fn().mockResolvedValue(res);
  vi.stubGlobal('fetch', fn);
  return fn;
}

afterEach(() => {
  vi.unstubAllGlobals();
  setCsrfToken(null);
});

describe('agent package API', () => {
  it('reads the availability info', async () => {
    const info = { available: false, version: null, size_bytes: null, reason: 'not_built' };
    const fn = mockFetch(new Response(JSON.stringify(info), { status: 200 }));
    await expect(getAgentPackageInfo()).resolves.toEqual(info);
    expect(fn.mock.calls[0]?.[0]).toBe('/api/v1/admin/agent-package');
  });

  it('POSTs with the CSRF header and language, and returns the ZIP as a Blob', async () => {
    setCsrfToken('tok');
    const fn = mockFetch(
      new Response(new Uint8Array([80, 75, 3, 4]), {
        status: 200,
        headers: {
          'Content-Type': 'application/zip',
          'Content-Disposition': 'attachment; filename="FOX3-Agent-Demo.zip"',
          'X-Pairing-Expires-Minutes': '15',
        },
      }),
    );
    const file = await requestAgentPackage('srv 1', 'ca');
    const [url, init] = fn.mock.calls[0] as [string, RequestInit];
    expect(url).toBe('/api/v1/admin/servers/srv%201/agent-package?language=ca');
    expect(init.method).toBe('POST');
    expect((init.headers as Record<string, string>)['X-CSRF-Token']).toBe('tok');
    expect(file.filename).toBe('FOX3-Agent-Demo.zip');
    expect(file.expiresMinutes).toBe(15);
    expect(file.blob.size).toBe(4);
  });

  it('falls back to FOX3-Agent.zip, 15 minutes and Spanish for odd input', async () => {
    const fn = mockFetch(new Response(new Uint8Array([1]), { status: 200 }));
    const file = await requestAgentPackage('s', 'fr');
    expect(file.filename).toBe('FOX3-Agent.zip');
    expect(file.expiresMinutes).toBe(15);
    expect(fn.mock.calls[0]?.[0]).toContain('language=es');
  });

  it('maps 503/404/429/network failures to ApiError and translated messages', async () => {
    const cases: [Response, string][] = [
      [errorBody('agent_not_built', 503), 'agent_not_built'],
      [errorBody('not_found', 404), 'not_found'],
      [errorBody('rate_limited', 429), 'rate_limited'],
    ];
    for (const [res, key] of cases) {
      mockFetch(res);
      const err = await requestAgentPackage('s', 'en').catch((e: unknown) => e);
      expect(err).toBeInstanceOf(ApiError);
      expect(packageErrorKey(err)).toBe(key);
    }
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('x')));
    expect(packageErrorKey(await requestAgentPackage('s', 'en').catch((e: unknown) => e))).toBe('network');
    expect(packageErrorKey(new Error('boom'))).toBe('generic');
  });

  it('has a translation for every error key', () => {
    const keys = ['generic', 'network', 'unauthorized', 'not_found', 'rate_limited', 'agent_not_built'];
    for (const k of keys) expect(en.admin.server.wizard.errors).toHaveProperty(k);
    for (const status of [0, 401, 404, 429, 503, 500]) {
      expect(keys).toContain(packageErrorKey(new ApiError(status, 'x', 'm')));
    }
  });
});
