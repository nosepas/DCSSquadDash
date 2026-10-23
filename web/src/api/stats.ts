import { get, query } from './client';
import type { KillEvent, Overview, RankingRow, Zone } from './types';

export type RankingSort = 'points' | 'kills' | 'kd';

export const fetchOverview = (id: string, signal?: AbortSignal) => get<Overview>(`/servers/${id}/overview`, signal);
export const fetchObjectives = (id: string, signal?: AbortSignal) => get<Zone[]>(`/servers/${id}/objectives`, signal);

export const fetchRanking = (id: string, sort: RankingSort, limit = 50, signal?: AbortSignal) =>
  get<RankingRow[]>(`/servers/${id}/ranking${query({ sort, limit })}`, signal);

export const fetchKills = (id: string, limit: number, before?: string, signal?: AbortSignal) =>
  get<KillEvent[]>(`/servers/${id}/kills${query({ limit, before })}`, signal);
