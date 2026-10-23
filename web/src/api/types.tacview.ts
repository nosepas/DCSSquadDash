import type { Coalition } from './types';

export interface TacviewHit {
  file_id: number;
  server_id: string;
  server_name: string;
  file: string;
  pilot: string;
  aircraft: string;
  coalition: Coalition | null;
  complete: boolean;
  first_utc: string | null;
  last_utc: string | null;
  first_offset_s: number;
  last_offset_s: number;
}
