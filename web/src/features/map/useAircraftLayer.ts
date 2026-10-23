import { useEffect, useRef } from 'react';
import type L from 'leaflet';
import { useTranslation } from 'react-i18next';
import type { Aircraft } from '../../api/types.aircraft';
import { AircraftLayer } from './aircraftMarkers';

/** Mirrors `aircraft` onto the map; markers are reused and moved by ucid, never recreated wholesale. */
export function useAircraftLayer(map: L.Map | null, aircraft: readonly Aircraft[] | undefined): void {
  const { t } = useTranslation();
  const layer = useRef<AircraftLayer | null>(null);

  useEffect(() => {
    if (!map) return;
    const l = new AircraftLayer(map);
    layer.current = l;
    return () => {
      l.destroy();
      layer.current = null;
    };
  }, [map]);

  useEffect(() => {
    layer.current?.sync(aircraft ?? [], t);
  }, [map, aircraft, t]);
}
