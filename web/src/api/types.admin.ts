import type { Agent, MissionType } from './types';

export interface FootholdSettings {
  enabled: boolean;
  saves_dir: string | null;
}

export interface TacviewSettings {
  enabled: boolean;
  folder: string | null;
}

export interface MissionsSettings {
  folder: string | null;
}

export interface DcsBotSettings {
  rest_enabled: boolean;
  rest_url: string;
  rest_prefix: string;
  server_name: string | null;
  db_enabled: boolean;
}

export interface ServerSettings {
  foothold: FootholdSettings;
  tacview: TacviewSettings;
  missions: MissionsSettings;
  dcsbot: DcsBotSettings;
}

export type SettingsKey = keyof ServerSettings;

export interface AgentWarning {
  code: string;
  message: string;
}

export interface DetectedFolder {
  path: string;
  note: string;
}

export type DetectedKey = 'saved_games' | 'foothold_saves' | 'dcsserverbot' | 'tacview';
export type Detected = Partial<Record<DetectedKey, DetectedFolder[]>>;

export interface AgentHealth {
  version: string | null;
  last_seen: string | null;
  queue_depth: number | null;
  warnings: AgentWarning[];
  detected: Detected;
  last_success: Record<string, string>;
}

/** Shape returned by every /admin/servers endpoint. */
export interface AdminServer {
  server_id: string;
  name: string;
  mission_type: MissionType;
  terrain: string | null;
  address: string | null;
  description: string | null;
  enabled: boolean;
  settings: ServerSettings;
  online: boolean;
  agents: Agent[];
  agent: AgentHealth;
}

export interface GeneralFields {
  name: string;
  mission_type: MissionType;
  address: string | null;
  description: string | null;
  enabled: boolean;
}

export type AdminServerPatch = Partial<GeneralFields> & { settings?: ServerSettings };
