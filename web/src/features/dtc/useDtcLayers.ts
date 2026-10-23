import { useEffect, useRef } from 'react';
import L from 'leaflet';
import { useTranslation } from 'react-i18next';
import type { DtcModel } from '../../api/types.dtc';
import { allLists, sameRef, type ListRef } from '../../lib/dtc/lists';
import { listInfos } from '../../lib/dtc/listInfo';
import { pinIcon, popupContent } from './mapMarkers';

export interface LayerHandlers {
  onAdd: (lat: number, lon: number) => void;
  onDrag: (id: string, lat: number, lon: number) => void;
  onRemove: (ref: ListRef, index: number) => void;
  onActivate: (ref: ListRef) => void;
}

const round6 = (n: number) => Math.round(n * 1e6) / 1e6;

/** Draws every list (polyline + pins) and wires click-to-add, drag, right-click delete. Redraws on any model change. */
export function useDtcLayers(map: L.Map | null, model: DtcModel | null, active: ListRef | undefined, approx: Record<string, true>, canAdd: boolean, h: LayerHandlers) {
  const { t } = useTranslation();
  const handlers = useRef(h);
  handlers.current = h;

  useEffect(() => {
    if (!map || !canAdd) return;
    const onClick = (e: L.LeafletMouseEvent) => handlers.current.onAdd(round6(e.latlng.lat), round6(e.latlng.lng));
    map.on('click', onClick);
    return () => void map.off('click', onClick);
  }, [map, canAdd]);

  useEffect(() => {
    if (!map || !model) return;
    const group = L.layerGroup().addTo(map);
    const infos = listInfos(model);
    for (const { ref, points } of allLists(model)) {
      const info = infos.find((l) => sameRef(l.ref, ref));
      if (!info) continue;
      const isActive = !!active && sameRef(active, ref);
      const closed = ref.type === 'line' && model.lines[ref.index]?.closed === true;
      const path = points.map((p) => L.latLng(p.lat, p.lon));
      if (path.length > 1) {
        const opts = { color: info.color, weight: isActive ? 3 : 2, opacity: isActive ? 0.9 : 0.55, dashArray: info.dashed ? '6 6' : undefined, interactive: false };
        (closed && path.length > 2 ? L.polygon(path, { ...opts, fill: false }) : L.polyline(path, opts)).addTo(group);
      }
      points.forEach((p, i) => {
        const marker = L.marker([p.lat, p.lon], {
          icon: pinIcon(i + 1, info.color, isActive), draggable: isActive, keyboard: false, zIndexOffset: isActive ? 500 : 0,
        }).addTo(group);
        if (!isActive) {
          marker.on('click', () => handlers.current.onActivate(ref));
          return;
        }
        const del = () => handlers.current.onRemove(ref, i);
        marker.bindPopup(popupContent(p, i + 1, t, !!(p.id && approx[p.id]), del));
        marker.on('contextmenu', del);
        marker.on('dragend', () => {
          const ll = marker.getLatLng();
          if (p.id) handlers.current.onDrag(p.id, round6(ll.lat), round6(ll.lng));
        });
      });
    }
    return () => void group.remove();
  }, [map, model, active, approx, t]);
}
