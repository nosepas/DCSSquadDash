import { useEffect } from 'react';
import L from 'leaflet';
import { useTranslation } from 'react-i18next';
import type { MapData } from '../../../api/types';
import { labelNode } from '../../../lib/leafletNodes';
import { connectionSegments, hasPosition } from '../../../lib/zones';
import { segmentLine, zonePopup } from '../../map/zoneMarkers';
import type { RefPanes } from './refPanes';
import { zoneStyle } from './refStyle';

/** Front line (opposing-coalition connections), the other connections and the zones of the reference server, muted. */
export function useZoneLayer(map: L.Map | null, panes: RefPanes | null, data: MapData | undefined, show: boolean) {
  const { t } = useTranslation();
  const shown = show ? data : undefined;

  useEffect(() => {
    if (!map || !panes || !shown) return;
    const group = L.layerGroup().addTo(map);
    for (const s of connectionSegments(shown.zones, shown.connections)) {
      segmentLine(s, { renderer: panes.lines, pane: panes.lines.options.pane, opacity: s.front ? 0.85 : 0.35 }).addTo(group);
    }
    for (const z of shown.zones.filter(hasPosition)) {
      const dot = L.circleMarker([z.lat, z.lon], zoneStyle(z, panes)).addTo(group);
      dot.bindTooltip(labelNode(z.name), { direction: 'top', offset: [0, -4] });
      dot.bindPopup(() => zonePopup(z, t));
      dot.on('click', (e) => L.DomEvent.stopPropagation(e.originalEvent));
    }
    return () => void group.remove();
  }, [map, panes, shown, t]);
}
