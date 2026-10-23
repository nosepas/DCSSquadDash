import { useEffect, useRef } from 'react';
import L from 'leaflet';
import { useTranslation } from 'react-i18next';
import type { DtcModel } from '../../api/types.dtc';
import { allLists, type ListRef } from '../../lib/dtc/lists';
import { viewForTerrain } from '../../lib/dtc/terrainCenters';
import { useLeafletMap } from '../map/useLeafletMap';
import { ReferenceLayers } from './reference/ReferenceLayers';
import type { NamedPlace } from '../../lib/dtc/reference';
import { useDtcLayers, type LayerHandlers } from './useDtcLayers';

interface Props {
  model: DtcModel | null;
  active: ListRef | undefined;
  approx: Record<string, true>;
  /** Changes when the whole content was replaced (import): the view then fits the points. */
  revision: number;
  handlers: LayerHandlers;
  /** "Add as point" of an airfield/FARP popup. */
  onAddPlace: (place: NamedPlace) => void;
}

/** Big map: centred on the chosen DCS terrain, click to add a point to the active list. */
export function DtcMap({ model, active, approx, revision, handlers, onAddPlace }: Props) {
  const { t } = useTranslation();
  const ref = useRef<HTMLDivElement>(null);
  const map = useLeafletMap(ref, true);
  const terrain = model?.terrain ?? null;
  const canAdd = !!model && !!terrain;
  useDtcLayers(map, model, active, approx, canAdd, handlers);

  const modelRef = useRef(model);
  modelRef.current = model;

  // New terrain or new content: frame the points if there are any, otherwise the region of the terrain.
  useEffect(() => {
    if (!map) return;
    const points = modelRef.current ? allLists(modelRef.current).flatMap((l) => l.points) : [];
    if (points.length > 0) {
      map.fitBounds(L.latLngBounds(points.map((p) => [p.lat, p.lon] as L.LatLngTuple)), { padding: [40, 40], maxZoom: 11 });
      return;
    }
    const v = viewForTerrain(terrain);
    map.setView([v.lat, v.lon], v.zoom);
  }, [map, terrain, revision]);

  return (
    <>
      <ReferenceLayers map={map} terrain={terrain} onAdd={canAdd ? onAddPlace : null} />
      <div className="dtc-map-wrap">
        <div ref={ref} className="tmap dtc-map" role="region" aria-label={t('dtc.map.aria')} />
        {!canAdd && <p className="dtc-map-hint" role="status">{t(model ? 'dtc.map.needTerrain' : 'dtc.map.needAircraft')}</p>}
      </div>
    </>
  );
}
