import { ApiError, get, mutationHeaders, notifyUnauthorized, post, query, toApiError, API_BASE } from './client';
import type { DtcAircraft, DtcAirfield, DtcGenerated, DtcImport, DtcModel, DtcTerrain, ElevationResponse } from './types.dtc';
import { filenameFromDisposition } from '../lib/tacview';

export const fetchDtcAircraft = (signal?: AbortSignal) => get<DtcAircraft[]>('/dtc/aircraft', signal);
export const fetchDtcTerrains = (signal?: AbortSignal) => get<DtcTerrain[]>('/dtc/terrains', signal);

/** A new model for the aircraft: empty navigation and the real default radios of the template. */
export const fetchDefaultModel = (aircraft: string, terrain: string | null, signal?: AbortSignal) =>
  get<DtcModel>(`/dtc/default-model${query({ aircraft, terrain: terrain ?? undefined })}`, signal);

export const fetchElevation = (points: { lat: number; lon: number }[]) =>
  post<ElevationResponse>('/dtc/elevation', { points });

async function send(path: string, init: RequestInit): Promise<Response> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, { ...init, credentials: 'same-origin' });
  } catch {
    throw new ApiError(0, 'network', 'network error');
  }
  if (!res.ok) {
    const err = await toApiError(res);
    if (err.status === 401) notifyUnauthorized();
    throw err;
  }
  return res;
}

/** The raw bytes of a .dtc file are the request body (not JSON-wrapped). */
export async function importDtc(file: Blob): Promise<DtcImport> {
  const res = await send('/dtc/import', {
    method: 'POST',
    headers: { Accept: 'application/json', 'Content-Type': 'application/octet-stream', ...mutationHeaders() },
    body: file,
  });
  return (await res.json()) as DtcImport;
}

/** `X-DTC-Warnings` is a URL-encoded JSON array of strings; anything unreadable gives no warnings. */
export function decodeWarnings(header: string | null): string[] {
  if (!header) return [];
  try {
    const parsed: unknown = JSON.parse(decodeURIComponent(header));
    return Array.isArray(parsed) ? parsed.filter((w): w is string => typeof w === 'string') : [];
  } catch {
    return [];
  }
}

export async function generateDtc(model: DtcModel, templateId: string | null, fallbackName: string): Promise<DtcGenerated> {
  const res = await send('/dtc/generate', {
    method: 'POST',
    headers: { Accept: 'application/json', 'Content-Type': 'application/json', ...mutationHeaders() },
    body: JSON.stringify(templateId ? { model, template_id: templateId } : { model }),
  });
  return {
    blob: await res.blob(),
    filename: filenameFromDisposition(res.headers.get('Content-Disposition'), fallbackName),
    warnings: decodeWarnings(res.headers.get('X-DTC-Warnings')),
  };
}

export const fetchDtcAirfields = (terrain: string, signal?: AbortSignal) =>
  get<DtcAirfield[]>(`/dtc/airfields${query({ terrain })}`, signal);
