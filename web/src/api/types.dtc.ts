import type { DtcRadios } from './types.radios';

/** Neutral DTC model (contracts/schemas/dtc_mission.json) and the /dtc endpoints' payloads. */
export interface DtcPoint {
  id?: string;
  name?: string;
  note?: string;
  lat: number;
  lon: number;
  elevation_m?: number | null;
  kind?: string;
  extra?: Record<string, unknown>;
}

export interface DtcRoute {
  name: string;
  points: DtcPoint[];
}

export interface DtcLine {
  name?: string;
  closed?: boolean;
  points: DtcPoint[];
}

/** Unknown top-level parts (threat_points, zones...) travel untouched thanks to the index signature. */
export interface DtcModel {
  model_version: number;
  terrain: string | null;
  aircraft: string;
  dcs_version?: string | null;
  name?: string;
  waypoints: DtcPoint[];
  routes: DtcRoute[];
  lines: DtcLine[];
  aircraft_extra: Record<string, unknown>;
  /** Absent for the F-14; read from the file on import and edited only value by value. */
  radios?: DtcRadios;
  [key: string]: unknown;
}

export interface DtcAircraft {
  id: string;
  label: string;
  enabled: boolean;
  supports: string[];
  unsupported: string[];
  limits: Record<string, number | null>;
  notes: string[];
}

export type Calibration = 'exact' | 'plausible' | 'airports';

export interface DtcTerrain {
  id: string;
  calibration: Calibration | null;
  note: string;
}

export interface ElevationResponse {
  enabled: boolean;
  elevations: (number | null)[];
  attribution: string;
}

export interface DtcImport {
  model: DtcModel;
  warnings: string[];
  template_id: string;
}

export interface DtcGenerated {
  blob: Blob;
  filename: string;
  warnings: string[];
}

/** Airfield of a DCS map (GET /dtc/airfields). */
export interface DtcAirfield {
  name: string;
  lat: number;
  lon: number;
  civil: boolean;
}
