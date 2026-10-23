import { del, get, patch, post, put } from './client';
import type { AdminServer, AdminServerPatch } from './types.admin';
import type { AdminUser, Agent, MissionType, PairingCode, Role } from './types';

export const listServers = (signal?: AbortSignal) => get<AdminServer[]>('/admin/servers', signal);
export const getServer = (id: string, signal?: AbortSignal) => get<AdminServer>(`/admin/servers/${id}`, signal);
export const createServer = (name: string, mission_type: MissionType) =>
  post<AdminServer>('/admin/servers', { name, mission_type });
export const updateServer = (id: string, body: AdminServerPatch) => patch<AdminServer>(`/admin/servers/${id}`, body);
export const deleteServer = (id: string) => del<undefined>(`/admin/servers/${id}`);
export const createPairingCode = (id: string) => post<PairingCode>(`/admin/servers/${id}/pairing-code`);
export const listAgents = (signal?: AbortSignal) => get<Agent[]>('/admin/agents', signal);
export const revokeAgent = (id: string) => post<undefined>(`/admin/agents/${id}/revoke`);
export const listUsers = (signal?: AbortSignal) => get<AdminUser[]>('/admin/users', signal);
export const setUserRole = (id: number, role: Role) => put<undefined>(`/admin/users/${id}/role`, { role });
