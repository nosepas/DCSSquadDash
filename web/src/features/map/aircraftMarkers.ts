import L from 'leaflet';
import type { TFunction } from 'i18next';
import type { Aircraft } from '../../api/types.aircraft';
import { labelNode } from '../../lib/leafletNodes';
import { diffAircraft, metersToFeet } from '../../lib/aircraft';

/** Top-down plane silhouette (points north); colour comes from CSS via currentColor. */
export const PLANE_SVG =
  '<svg viewBox="0 0 24 24" width="26" height="26" aria-hidden="true" focusable="false">' +
  '<path d="M12 1.5l1.9 7.1 8.6 5.4v2.3l-8.6-2.4-.9 5.6 2.6 1.9v1.4L12 21.8l-3.6 1 0-1.4 2.6-1.9-.9-5.6-8.6 2.4v-2.3l8.6-5.4z" ' +
  'fill="currentColor" stroke="#070b12" stroke-width="1.1" stroke-linejoin="round"/></svg>';

function planeIcon(a: Aircraft): L.DivIcon {
  return L.divIcon({
    className: `plane-icon plane-${a.coalition} ${a.in_air ? '' : 'plane-ground'}`,
    html: PLANE_SVG,
    iconSize: [26, 26],
    iconAnchor: [13, 13],
    popupAnchor: [0, -12],
  });
}

function row(parent: HTMLElement, label: string, value: string): void {
  const r = document.createElement('div');
  r.className = 'popup-row';
  const k = document.createElement('span');
  k.textContent = label;
  const v = document.createElement('b');
  v.className = 'mono';
  v.textContent = value;
  r.append(k, v);
  parent.append(r);
}

/** Popup built with DOM nodes + textContent: pilot names come from players and must never inject HTML. */
export function aircraftPopup(a: Aircraft, t: TFunction): HTMLElement {
  const root = document.createElement('div');
  root.className = 'zone-popup';
  const title = document.createElement('strong');
  title.textContent = a.name;
  root.append(title);
  row(root, t('aircraft.type'), a.aircraft);
  row(root, t('objectives.coalition'), t(`coalition.${a.coalition}`));
  if (a.alt_m !== null) row(root, t('aircraft.altitude'), t('aircraft.altValue', { m: Math.round(a.alt_m), ft: metersToFeet(a.alt_m) }));
  if (!a.in_air) row(root, t('aircraft.altitude'), t('aircraft.onGround'));
  return root;
}

/** Keeps one marker per aircraft (keyed by ucid): new ones are created, existing ones moved, vanished ones removed. */
export class AircraftLayer {
  private readonly group: L.LayerGroup;
  private readonly markers = new Map<string, L.Marker>();
  private known = new Map<string, Aircraft>();

  constructor(map: L.Map) {
    this.group = L.layerGroup().addTo(map);
  }

  sync(list: readonly Aircraft[], t: TFunction): void {
    const diff = diffAircraft(this.known, list);
    for (const id of diff.removed) {
      this.markers.get(id)?.remove();
      this.markers.delete(id);
    }
    for (const a of diff.added) {
      const m = L.marker([a.lat, a.lon], { icon: planeIcon(a), title: a.name, alt: a.name, keyboard: true, zIndexOffset: 500 });
      m.bindTooltip(labelNode(`${a.name} · ${a.aircraft}`), { direction: 'top', offset: [0, -10] });
      m.bindPopup(aircraftPopup(a, t));
      m.addTo(this.group);
      this.markers.set(a.ucid, m);
    }
    for (const a of diff.moved) {
      const m = this.markers.get(a.ucid);
      if (!m) continue;
      m.setLatLng([a.lat, a.lon]).setIcon(planeIcon(a)).setTooltipContent(labelNode(`${a.name} · ${a.aircraft}`)).setPopupContent(aircraftPopup(a, t));
    }
    this.known = new Map(list.map((a) => [a.ucid, a]));
  }

  get size(): number {
    return this.markers.size;
  }

  destroy(): void {
    this.group.remove();
    this.markers.clear();
    this.known.clear();
  }
}
