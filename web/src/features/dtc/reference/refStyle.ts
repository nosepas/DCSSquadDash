import L from 'leaflet';
import type { Zone } from '../../../api/types';
import type { RefPanes } from './refPanes';

const COALITION = { red: '#ff6b6b', blue: '#4da3ff', neutral: '#a3afc4' } as const;
const ACCENT = '#f5b942';
const CIVIL = '#7dd3fc';
const MILITARY = '#c4b5fd';

/** Airfield dot: civil = hollow ring, military = filled. Muted so the user's route stays the focus. */
export function airfieldStyle(civil: boolean, panes: RefPanes): L.CircleMarkerOptions {
  const color = civil ? CIVIL : MILITARY;
  return {
    renderer: panes.dots, pane: panes.dots.options.pane, radius: 5, color, weight: 1.5, opacity: 0.85,
    fillColor: color, fillOpacity: civil ? 0.12 : 0.7, bubblingMouseEvents: false,
  };
}

/** Zone dot coloured by coalition; HQ is bigger with an amber ring, at-risk zones get a dashed amber ring. */
export function zoneStyle(z: Zone, panes: RefPanes): L.CircleMarkerOptions {
  return {
    renderer: panes.dots, pane: panes.dots.options.pane, radius: z.is_hq ? 9 : 6,
    color: z.is_hq || z.at_risk ? ACCENT : '#e8eefb', weight: z.is_hq ? 3 : 1.5, opacity: z.at_risk || z.is_hq ? 0.95 : 0.6,
    dashArray: z.at_risk ? '3 3' : undefined, fillColor: COALITION[z.coalition], fillOpacity: 0.55, bubblingMouseEvents: false,
  };
}

export function farpIcon(): L.DivIcon {
  return L.divIcon({ className: 'ref-farp-wrap', html: '<span class="ref-farp" aria-hidden="true">H</span>', iconSize: [20, 20], iconAnchor: [10, 10] });
}

/** Written airfield name (decorative: the dot has the accessible tooltip). */
export function labelIcon(name: string): L.DivIcon {
  const el = document.createElement('span');
  el.className = 'ref-label';
  el.textContent = name;
  return L.divIcon({ html: el, className: 'ref-label-wrap', iconSize: [0, 0], iconAnchor: [-8, 5] });
}
