import { get, query } from './client';
import type { Farp, MapData, Mission, ServerSummary } from './types';
import type { AircraftResponse } from './types.aircraft';

export const fetchServers = (signal?: AbortSignal) => get<ServerSummary[]>('/servers', signal);
export const fetchMap = (id: string, signal?: AbortSignal) => get<MapData>(`/servers/${id}/map`, signal);
export const fetchMissions = (id: string, signal?: AbortSignal) => get<Mission[]>(`/servers/${id}/missions`, signal);

export const fetchAircraft = (id: string, coalition: 'red' | 'blue' | undefined, signal?: AbortSignal) =>
  get<AircraftResponse>(`/servers/${id}/aircraft${query({ coalition })}`, signal);
export const fetchFarps = (id: string, signal?: AbortSignal) => get<Farp[]>(`/servers/${id}/farps`, signal);
