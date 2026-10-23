export type Coalition = 'red' | 'blue' | 'neutral';
export type MissionType = 'foothold' | 'generic';
export type Role = 'user' | 'admin';

export interface ServerSummary {
  server_id: string;
  name: string;
  mission_type: MissionType;
  online: boolean;
  /** DCS terrain id once the server reported one (null before). */
  terrain: string | null;
}

export interface Zone {
  name: string;
  coalition: Coalition;
  is_hq: boolean;
  at_risk: boolean;
  level: number | null;
  lat: number | null;
  lon: number | null;
}

export interface Connection {
  from: string;
  to: string;
}

export interface MapData {
  terrain: string | null;
  calibrated: boolean;
  zones: Zone[];
  connections: Connection[];
}

export interface Mission {
  name: string;
  terrain: string | null;
  mission_type: MissionType;
  current: boolean;
  started_at: string | null;
}

export interface Me {
  user_id: number;
  name: string;
  role: Role;
  csrf_token: string;
  linked_ucids: string[];
}

export interface AuthConfig {
  discord: boolean;
  demo: boolean;
}

export interface Weather {
  temperature_c?: number;
  qnh_hpa?: number;
  wind_dir_deg?: number;
  wind_speed_ms?: number;
  visibility_m?: number;
}

export interface RankingRow {
  ucid: string;
  name: string | null;
  kills: number;
  deaths: number;
  kd: number;
  points: number;
}

export type LatLon = [number, number];

export interface NewsItem {
  type: string;
  time_utc: string;
  zone: string | null;
  coalition: Coalition | null;
  actor: string | null;
}

export interface Overview {
  online: number;
  airborne: number;
  objectives: Record<Coalition, number>;
  at_risk: number;
  kills_1h: number;
  pilots: number;
  weather: Weather | null;
  front_line: [LatLon, LatLon][];
  top_shooters: RankingRow[];
  news: NewsItem[];
}

export interface KillEvent {
  id: number;
  time_utc: string;
  actor_ucid: string | null;
  actor_name: string | null;
  actor_coalition: Coalition | null;
  actor_unit: string | null;
  target_name: string | null;
  target_coalition: Coalition | null;
  target_unit: string | null;
  target_is_player: boolean;
  weapon: string | null;
  zone: string | null;
}

export interface PlayerHit {
  ucid: string;
  last_name: string;
  first_seen_at: string;
  last_seen_at: string;
}

export interface ProfileServer {
  server_id: string;
  server_name: string | null;
  kills: number;
  deaths: number;
  points: number;
}

export interface Profile {
  ucid: string;
  name: string;
  first_seen_at: string;
  last_seen_at: string;
  discord_linked: boolean;
  servers: ProfileServer[];
}

export interface LinkCode {
  code: string;
  expires_at: string;
}

export interface PairingCode {
  agent_id: string;
  pairing_code: string;
  expires_in_minutes: number;
}

export interface Agent {
  agent_id: string;
  server_id: string;
  name: string | null;
  revoked_at: string | null;
  last_seen_at: string | null;
  agent_version: string | null;
  pairing_expires_at: string | null;
}

export interface AdminUser {
  user_id: number;
  discord_name: string | null;
  role: Role;
  last_login_at: string | null;
}

/** Player-built FARP of a Foothold server (GET /servers/{id}/farps). */
export interface Farp {
  name: string;
  lat: number;
  lon: number;
}
