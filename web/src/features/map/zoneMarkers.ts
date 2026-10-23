import L from 'leaflet';
import { labelNode } from '../../lib/leafletNodes';
import type { TFunction } from 'i18next';
import type { Zone } from '../../api/types';
import type { Segment } from '../../lib/zones';

type Located = Zone & { lat: number; lon: number };

export function zoneIcon(z: Zone): L.DivIcon {
  const cls = ['zone-dot', `zone-${z.coalition}`, z.is_hq ? 'hq' : '', z.at_risk ? 'at-risk' : ''].filter(Boolean).join(' ');
  const size = z.is_hq ? 26 : 18;
  return L.divIcon({
    className: 'zone-icon',
    html: `<span class="${cls}"></span>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -size / 2],
  });
}

function line(parent: HTMLElement, label: string, value: string): void {
  const row = document.createElement('div');
  row.className = 'popup-row';
  const k = document.createElement('span');
  k.textContent = label;
  const v = document.createElement('b');
  v.className = 'mono';
  v.textContent = value;
  row.append(k, v);
  parent.append(row);
}

/** Popup content built with DOM nodes + textContent so mission-provided names can never inject HTML. */
export function zonePopup(z: Zone, t: TFunction): HTMLElement {
  const root = document.createElement('div');
  root.className = 'zone-popup';
  const title = document.createElement('strong');
  title.textContent = z.name;
  root.append(title);
  line(root, t('objectives.coalition'), t(`coalition.${z.coalition}`));
  if (z.level !== null) line(root, t('map.level'), String(z.level));
  if (z.is_hq) line(root, t('map.hq'), t('common.yes'));
  if (z.at_risk) line(root, t('map.atRisk'), t('common.yes'));
  return root;
}

export function zoneMarker(z: Located, t: TFunction): L.Marker {
  const tip = labelNode(z.name);
  return L.marker([z.lat, z.lon], { icon: zoneIcon(z), title: z.name, alt: z.name, keyboard: true })
    .bindTooltip(tip, { direction: 'top', offset: [0, -10] })
    .bindPopup(zonePopup(z, t));
}

/** `extra` lets other maps restyle the line (e.g. muted, in another pane). */
export function segmentLine(s: Segment, extra: L.PolylineOptions = {}): L.Polyline {
  return L.polyline([s.from, s.to], {
    className: s.front ? 'conn conn-front' : 'conn',
    color: s.front ? '#f5b942' : '#5f7396',
    weight: s.front ? 3 : 1.5,
    opacity: s.front ? 0.95 : 0.6,
    dashArray: s.front ? '8 6' : undefined,
    interactive: false,
    ...extra,
  });
}
