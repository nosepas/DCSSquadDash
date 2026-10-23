export interface Aircraft {
  ucid: string;
  name: string;
  coalition: 'red' | 'blue';
  aircraft: string;
  lat: number;
  lon: number;
  alt_m: number | null;
  in_air: boolean;
}

export type AircraftHint = 'link_account' | 'not_online' | null;

export interface AircraftResponse {
  viewer_coalition: 'red' | 'blue' | null;
  coalitions: ('red' | 'blue')[];
  hint: AircraftHint;
  aircraft: Aircraft[];
}
