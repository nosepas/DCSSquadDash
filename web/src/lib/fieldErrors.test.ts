import { describe, expect, it } from 'vitest';
import { ApiError } from '../api/client';
import { fieldErrors } from './fieldErrors';

describe('fieldErrors', () => {
  it('maps FastAPI 422 details to dotted field paths without the body prefix', () => {
    const err = new ApiError(422, 'http_422', 'Unprocessable', [
      { loc: ['body', 'settings', 'dcsbot', 'rest_url'], msg: 'Value error, must be a http(s) URL' },
      { loc: ['body', 'name'], msg: 'String should have at least 1 character' },
    ]);
    expect(fieldErrors(err)).toEqual({
      'settings.dcsbot.rest_url': 'must be a http(s) URL',
      name: 'String should have at least 1 character',
    });
  });

  it('returns nothing for other errors or malformed details', () => {
    expect(fieldErrors(new Error('x'))).toEqual({});
    expect(fieldErrors(new ApiError(500, 'x', 'x', []))).toEqual({});
    expect(fieldErrors(new ApiError(422, 'x', 'x', 'nope'))).toEqual({});
    expect(fieldErrors(new ApiError(422, 'x', 'x', [{ loc: 'x' }, null]))).toEqual({});
  });
});
