import { ApiError, API_BASE, get, mutationHeaders, notifyUnauthorized, toApiError } from './client';
import { parseExpiryMinutes } from '../lib/agentWizard';
import { parseContentDisposition } from '../lib/contentDisposition';

export interface AgentPackageInfo {
  available: boolean;
  version: string | null;
  size_bytes: number | null;
  reason: 'not_built' | null;
}

export interface AgentPackageFile {
  blob: Blob;
  filename: string;
  expiresMinutes: number;
}

const LANGUAGES = ['es', 'ca', 'en', 'gl', 'eu'];
export const FALLBACK_FILENAME = 'FOX3-Agent.zip';

export const getAgentPackageInfo = (signal?: AbortSignal) => get<AgentPackageInfo>('/admin/agent-package', signal);

/** Asks the server for a personalised installer ZIP (this also mints a one-time pairing code). Rejects with ApiError. */
export async function requestAgentPackage(serverId: string, language: string, signal?: AbortSignal): Promise<AgentPackageFile> {
  const lang = LANGUAGES.includes(language) ? language : 'es';
  let res: Response;
  try {
    res = await fetch(`${API_BASE}/admin/servers/${encodeURIComponent(serverId)}/agent-package?language=${lang}`, {
      method: 'POST',
      headers: { Accept: 'application/zip', ...mutationHeaders() },
      credentials: 'same-origin',
      signal,
    });
  } catch (e) {
    if (e instanceof DOMException && e.name === 'AbortError') throw e;
    throw new ApiError(0, 'network', 'network error');
  }
  if (!res.ok) {
    const err = await toApiError(res);
    if (err.status === 401) notifyUnauthorized();
    throw err;
  }
  return {
    blob: await res.blob(),
    filename: parseContentDisposition(res.headers.get('Content-Disposition'), FALLBACK_FILENAME),
    expiresMinutes: parseExpiryMinutes(res.headers.get('X-Pairing-Expires-Minutes')),
  };
}

/** i18n key (under `admin.server.wizard.errors.`) for a failed info/download call. */
export function packageErrorKey(err: unknown): string {
  if (!(err instanceof ApiError)) return 'generic';
  if (err.code === 'agent_not_built' || err.status === 503) return 'agent_not_built';
  if (err.status === 0) return 'network';
  if (err.status === 401) return 'unauthorized';
  if (err.status === 404) return 'not_found';
  if (err.status === 429) return 'rate_limited';
  return 'generic';
}
