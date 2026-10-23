import { API_BASE, get, query } from './client';
import type { TacviewHit } from './types.tacview';

export const searchTacview = (pilot: string, serverId: string | undefined, signal?: AbortSignal) =>
  get<TacviewHit[]>(`/tacview/search${query({ pilot, server_id: serverId })}`, signal);

export const tacviewDownloadUrl = (fileId: number): string => `${API_BASE}/tacview/files/${fileId}/download`;
