import type L from 'leaflet';
import type { TFunction } from 'i18next';
import type { NamedPlace } from '../../../lib/dtc/reference';

/** Popup of an airfield/FARP: name, kind, position and (when points can be added) the "Add as point" button. DOM API only: names are data. */
export function placePopup(place: NamedPlace, kind: string, t: TFunction, map: L.Map, onAdd: ((p: NamedPlace) => void) | null): HTMLElement {
  const root = document.createElement('div');
  root.className = 'zone-popup';
  const title = document.createElement('b');
  title.textContent = place.name;
  const sub = document.createElement('div');
  sub.className = 'muted small';
  sub.textContent = kind;
  const pos = document.createElement('div');
  pos.className = 'mono small';
  pos.textContent = `${place.lat.toFixed(5)}, ${place.lon.toFixed(5)}`;
  root.append(title, sub, pos);
  if (onAdd) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'btn btn-primary';
    btn.textContent = t('dtc.layers.addPoint');
    btn.addEventListener('click', () => {
      onAdd(place);
      map.closePopup();
    });
    root.append(btn);
  }
  return root;
}
