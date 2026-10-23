import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiError, get, post, query, setCsrfToken } from './client';

function mockFetch(res: Response) {
  const fn = vi.fn().mockResolvedValue(res);
  vi.stubGlobal('fetch', fn);
  return fn;
}

afterEach(() => {
  vi.unstubAllGlobals();
  setCsrfToken(null);
});

describe('api client', () => {
  it('sends the CSRF header on mutations only', async () => {
    setCsrfToken('tok123');
    const fn = mockFetch(new Response(null, { status: 204 }));
    await post('/x', { a: 1 });
    const mutHeaders = (fn.mock.calls[0]?.[1] as RequestInit).headers as Record<string, string>;
    expect(mutHeaders['X-CSRF-Token']).toBe('tok123');
    expect(mutHeaders['Content-Type']).toBe('application/json');

    fn.mockResolvedValue(new Response('{}', { status: 200 }));
    await get('/y');
    const getInit = fn.mock.calls[1]?.[1] as RequestInit;
    expect((getInit.headers as Record<string, string>)['X-CSRF-Token']).toBeUndefined();
    expect(getInit.credentials).toBe('same-origin');
  });

  it('maps backend error bodies to ApiError', async () => {
    mockFetch(new Response(JSON.stringify({ error: { code: 'forbidden', message: 'invalid CSRF token' } }), { status: 403 }));
    const err = await get('/z').catch((e: unknown) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect(err).toMatchObject({ status: 403, code: 'forbidden', message: 'invalid CSRF token' });
  });

  it('falls back to http_<status> for non-JSON errors and maps network failures', async () => {
    mockFetch(new Response('boom', { status: 502 }));
    await expect(get('/z')).rejects.toMatchObject({ status: 502, code: 'http_502' });
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('failed')));
    await expect(get('/z')).rejects.toMatchObject({ status: 0, code: 'network' });
  });

  it('keeps FastAPI validation details on 422 errors', async () => {
    const detail = [{ loc: ['body', 'name'], msg: 'too short' }];
    mockFetch(new Response(JSON.stringify({ detail }), { status: 422 }));
    await expect(get('/z')).rejects.toMatchObject({ status: 422, code: 'http_422', details: detail });
  });

  it('builds query strings skipping empty values', () => {
    expect(query({ a: 1, b: undefined, c: '', d: 'x y' })).toBe('?a=1&d=x+y');
    expect(query({})).toBe('');
  });
});
