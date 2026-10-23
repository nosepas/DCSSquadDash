import L from 'leaflet';
import type { TFunction } from 'i18next';
import type { DtcPoint } from '../../api/types.dtc';
import { formatElevation } from '../../lib/dtc/coords';

/** Numbered pin in the colour of its list; the active list gets bigger, draggable pins. */
export function pinIcon(n: number, color: string, active: boolean): L.DivIcon {
  const size = active ? 30 : 20;
  const el = document.createElement('span');
  el.className = `dtc-pin${active ? ' dtc-pin-active' : ''}`;
  el.style.setProperty('--pin', color);
  el.textContent = String(n);
  return L.divIcon({ html: el, className: 'dtc-pin-wrap', iconSize: [size, size], iconAnchor: [size / 2, size / 2] });
}

/** Popup with name, elevation and a delete button. Built with the DOM API so names from files are never parsed as HTML. */
export function popupContent(p: DtcPoint, n: number, t: TFunction, approx: boolean, onDelete: () => void): HTMLElement {
  const root = document.createElement('div');
  root.className = 'zone-popup';
  const title = document.createElement('b');
  title.textContent = `${n}. ${p.name || p.note || t('dtc.map.unnamed')}`;
  const elev = document.createElement('div');
  const e = formatElevation(p.elevation_m);
  elev.textContent = `${t('dtc.fields.elevation')}: ${e === '' ? t('dtc.map.noElevation') : `${e} m${approx ? ` (${t('dtc.fields.approx')})` : ''}`}`;
  const pos = document.createElement('div');
  pos.className = 'mono small';
  pos.textContent = `${p.lat.toFixed(5)}, ${p.lon.toFixed(5)}`;
  const del = document.createElement('button');
  del.type = 'button';
  del.className = 'btn btn-danger';
  del.textContent = t('dtc.points.delete');
  del.addEventListener('click', onDelete);
  root.append(title, elev, pos, del);
  return root;
}
