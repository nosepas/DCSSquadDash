import { ApiError } from '../api/client';

/** i18n key (under `errors.`) describing an API error to the user. */
export function errorKey(err: unknown): string {
  if (!(err instanceof ApiError)) return 'generic';
  if (err.status === 0) return 'network';
  if (err.status === 401) return 'unauthorized';
  if (err.status === 403) return 'forbidden';
  if (err.status === 404) return 'not_found';
  if (err.status === 429) return 'rate_limited';
  if (err.status >= 500) return 'server';
  return 'generic';
}
