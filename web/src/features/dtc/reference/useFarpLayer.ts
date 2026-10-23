import { useEffect, useRef } from 'react';
import L from 'leaflet';
import { useTranslation } from 'react-i18next';
import { labelNode } from '../../../lib/leafletNodes';
import type { Farp } from '../../../api/types';
import type { NamedPlace } from '../../../lib/dtc/reference';
import { placePopup } from './refPopups';
import type { RefPanes } from './refPanes';
import { farpIcon } from './refStyle';

/** Player-built FARPs of the reference server: an "H" square marker with name tooltip and the "Add as point" popup. */
export function useFarpLayer(map: L.Map | null, panes: RefPanes | null, farps: Farp[] | undefined, show: boolean, onAdd: ((p: NamedPlace) => void) | null) {
  const { t } = useTranslation();
  const add = useRef(onAdd);
  add.current = onAdd;
  const canAdd = onAdd !== null;
  const shown = show ? farps : undefined;

  useEffect(() => {
    if (!map || !panes || !shown) return;
    const group = L.layerGroup().addTo(map);
    for (const f of shown) {
      L.marker([f.lat, f.lon], { icon: farpIcon(), pane: panes.marks, title: f.name, alt: f.name, keyboard: true })
        .bindTooltip(labelNode(f.name), { direction: 'top', offset: [0, -10] })
        .bindPopup(() => placePopup(f, t('dtc.layers.farp'), t, map, canAdd ? (p) => add.current?.(p) : null))
        .addTo(group);
    }
    return () => void group.remove();
  }, [map, panes, shown, t, canAdd]);
}
