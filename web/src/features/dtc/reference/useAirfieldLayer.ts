import { useEffect, useRef } from 'react';
import L from 'leaflet';
import { useTranslation } from 'react-i18next';
import type { DtcAirfield } from '../../../api/types.dtc';
import { labelNode } from '../../../lib/leafletNodes';
import { labelCandidates } from '../../../lib/dtc/labels';
import type { NamedPlace } from '../../../lib/dtc/reference';
import { placePopup } from './refPopups';
import type { RefPanes } from './refPanes';
import { airfieldStyle, labelIcon } from './refStyle';

/** Written names for the airfields in view, only from a moderate zoom and capped; rebuilt on pan/zoom, never per render. */
function useLabels(map: L.Map | null, panes: RefPanes | null, airfields: DtcAirfield[] | undefined) {
  useEffect(() => {
    if (!map || !panes || !airfields) return;
    const group = L.layerGroup().addTo(map);
    const draw = () => {
      group.clearLayers();
      const b = map.getBounds();
      const box = { south: b.getSouth(), west: b.getWest(), north: b.getNorth(), east: b.getEast() };
      for (const a of labelCandidates(airfields, box, map.getZoom())) {
        L.marker([a.lat, a.lon], { icon: labelIcon(a.name), interactive: false, keyboard: false, pane: panes.marks }).addTo(group);
      }
    };
    draw();
    map.on('moveend', draw);
    return () => {
      map.off('moveend', draw);
      group.remove();
    };
  }, [map, panes, airfields]);
}

/** One canvas dot per airfield (hover = name, click = popup with "Add as point"); redrawn only when data or the toggle change. */
export function useAirfieldLayer(
  map: L.Map | null, panes: RefPanes | null, airfields: DtcAirfield[] | undefined, show: boolean, onAdd: ((p: NamedPlace) => void) | null,
) {
  const { t } = useTranslation();
  const add = useRef(onAdd);
  add.current = onAdd;
  const canAdd = onAdd !== null;
  const shown = show ? airfields : undefined;
  useLabels(map, panes, shown);

  useEffect(() => {
    if (!map || !panes || !shown) return;
    const group = L.layerGroup().addTo(map);
    for (const a of shown) {
      const place = { name: a.name, lat: a.lat, lon: a.lon };
      const dot = L.circleMarker([a.lat, a.lon], airfieldStyle(a.civil, panes)).addTo(group);
      dot.bindTooltip(labelNode(a.name), { direction: 'top', offset: [0, -4] });
      dot.bindPopup(() => placePopup(place, t(a.civil ? 'dtc.layers.civil' : 'dtc.layers.military'), t, map, canAdd ? (p) => add.current?.(p) : null));
      dot.on('click', (e) => L.DomEvent.stopPropagation(e.originalEvent));
    }
    return () => void group.remove();
  }, [map, panes, shown, t, canAdd]);
}
