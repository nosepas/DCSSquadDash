import { useEffect, useState, type RefObject } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

/** Esri dark-gray basemap by default (no key needed); override with VITE_TILE_URL (e.g. a keyed or self-hosted tile server). */
export const TILE_URL: string =
  (import.meta.env.VITE_TILE_URL as string | undefined) ??
  'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}';
const ATTRIBUTION = 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ';

/** Creates a Leaflet map with the dark basemap inside `ref` and tears it down on unmount. */
export function useLeafletMap(ref: RefObject<HTMLDivElement>, interactive: boolean): L.Map | null {
  const [map, setMap] = useState<L.Map | null>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const m = L.map(el, {
      center: [44, 40],
      zoom: 6,
      zoomControl: interactive,
      dragging: interactive,
      scrollWheelZoom: interactive,
      doubleClickZoom: interactive,
      touchZoom: interactive,
      boxZoom: interactive,
      keyboard: interactive,
      attributionControl: true,
    });
    L.tileLayer(TILE_URL, { attribution: ATTRIBUTION, maxZoom: 16 }).addTo(m);
    setMap(m);
    return () => {
      m.remove();
      setMap(null);
    };
  }, [ref, interactive]);

  return map;
}
