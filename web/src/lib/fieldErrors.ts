import { ApiError } from '../api/client';

interface Detail {
  loc?: unknown;
  msg?: unknown;
}

/**
 * Turns a 422 into `{ "settings.dcsbot.rest_url": "message" }` (the leading "body" is dropped).
 * Accepts FastAPI's `detail` array; anything else yields an empty map.
 */
export function fieldErrors(err: unknown): Record<string, string> {
  if (!(err instanceof ApiError) || err.status !== 422 || !Array.isArray(err.details)) return {};
  const out: Record<string, string> = {};
  for (const d of err.details as Detail[]) {
    if (!Array.isArray(d?.loc) || typeof d.msg !== 'string') continue;
    const path = d.loc.filter((p, i) => !(i === 0 && p === 'body')).join('.');
    if (path && !(path in out)) out[path] = d.msg.replace(/^Value error, /, '');
  }
  return out;
}
