import { get, post, query } from './client';
import type { LinkCode, PlayerHit, Profile } from './types';

export const searchPlayers = (q: string, signal?: AbortSignal) =>
  get<PlayerHit[]>(`/players${query({ q })}`, signal);
export const fetchProfile = (ucid: string, signal?: AbortSignal) =>
  get<Profile>(`/players/${encodeURIComponent(ucid)}`, signal);
export const startLink = () => post<LinkCode>('/link/start');
