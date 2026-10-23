import { describe, expect, it } from 'vitest';
import { ApiError } from '../api/client';
import { errorKey } from './errors';

describe('errorKey', () => {
  it('maps HTTP statuses to i18n keys', () => {
    const k = (status: number) => errorKey(new ApiError(status, 'x', 'm'));
    expect([k(0), k(401), k(403), k(404), k(429), k(503), k(400)]).toEqual([
      'network', 'unauthorized', 'forbidden', 'not_found', 'rate_limited', 'server', 'generic',
    ]);
  });

  it('falls back to generic for unknown errors', () => {
    expect(errorKey(new Error('boom'))).toBe('generic');
  });
});
