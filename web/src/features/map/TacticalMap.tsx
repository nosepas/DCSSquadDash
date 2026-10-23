import { useEffect, useRef } from 'react';
import L from 'leaflet';
import { useTranslation } from 'react-i18next';
import type { MapData } from '../../api/types';
import type { Aircraft } from '../../api/types.aircraft';
import { connectionSegments, hasPosition, zoneSetKey } from '../../lib/zones';
import { segmentLine, zoneMarker } from './zoneMarkers';
import { useAircraftLayer } from './useAircraftLayer';
import { useLeafletMap } from './useLeafletMap';

interface Props {
  data: MapData;
  /** Friendly aircraft to draw as an extra layer (undefined/empty = none). */
  aircraft?: readonly Aircraft[];
  interactive?: boolean;
  className?: string;
}

/** Leaflet map of zones and connections. Redraws on every data change; re-fits the view only when the set of zones changes. */
export function TacticalMap({ data, aircraft, interactive = true, className = '' }: Props) {
  const { t } = useTranslation();
  const ref = useRef<HTMLDivElement>(null);
  const map = useLeafletMap(ref, interactive);
  const fittedFor = useRef<string | null>(null);
  const aircraftRef = useRef(aircraft);
  aircraftRef.current = aircraft;
  useAircraftLayer(map, aircraft);

  useEffect(() => {
    if (!map) return;
    const group = L.layerGroup().addTo(map);
    const located = data.zones.filter(hasPosition);
    connectionSegments(data.zones, data.connections).forEach((s) => segmentLine(s).addTo(group));
    located.forEach((z) => zoneMarker(z, t).addTo(group));
    // Missions without zones (e.g. a training server) are framed on the aircraft instead.
    const planes = aircraftRef.current ?? [];
    const key = zoneSetKey(data.zones) || (planes.length > 0 ? 'aircraft-only' : '');
    const points: L.LatLngTuple[] = located.length > 0 ? located.map((z) => [z.lat, z.lon]) : planes.map((a) => [a.lat, a.lon]);
    if (key && fittedFor.current !== key) {  // first load, or the user switched to another server/map
      map.fitBounds(L.latLngBounds(points), { padding: [30, 30], maxZoom: 9 });
      fittedFor.current = key;
    }
    return () => {
      group.remove();
    };
  }, [map, data, t]);

  return <div ref={ref} className={`tmap ${className}`} role="region" aria-label={t('map.aria')} />;
}
