export interface MapView {
  lat: number;
  lon: number;
  zoom: number;
}

/** Where to open the map for each DCS terrain id (approximate centre of the playable area). */
export const TERRAIN_VIEWS: Record<string, MapView> = {
  Caucasus: { lat: 42.5, lon: 42.0, zoom: 6 },
  Syria: { lat: 34.8, lon: 37.0, zoom: 6 },
  Nevada: { lat: 36.6, lon: -115.5, zoom: 7 },
  PersianGulf: { lat: 26.0, lon: 56.0, zoom: 6 },
  MarianaIslands: { lat: 14.5, lon: 145.5, zoom: 7 },
  Sinai: { lat: 29.5, lon: 33.5, zoom: 6 },
  Falklands: { lat: -51.7, lon: -59.0, zoom: 7 },
  Normandy: { lat: 49.2, lon: 0.0, zoom: 7 },
  TheChannel: { lat: 50.6, lon: 1.0, zoom: 7 },
  GermanyCW: { lat: 51.0, lon: 10.0, zoom: 6 },
  Kola: { lat: 68.5, lon: 33.0, zoom: 6 },
};

export const WORLD_VIEW: MapView = { lat: 30, lon: 20, zoom: 3 };

export const viewForTerrain = (terrain: string | null): MapView => (terrain ? TERRAIN_VIEWS[terrain] ?? WORLD_VIEW : WORLD_VIEW);
