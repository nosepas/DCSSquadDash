import L from 'leaflet';
import { describe, expect, it } from 'vitest';
import { labelNode, textNode } from './leafletNodes';
import { AircraftLayer } from '../features/map/aircraftMarkers';
import { placePopup } from '../features/dtc/reference/refPopups';

const EVIL = ['<img src=x onerror=alert(1)>', '"><script>alert(1)</script>'];
const t = ((k: string) => k) as never;

describe('leafletNodes', () => {
  it.each(EVIL)('renders %s as text', (name) => {
    for (const el of [labelNode(name), textNode(name, 'b', 'x')]) {
      expect(el.textContent).toBe(name);
      expect(el.children.length).toBe(0);
    }
  });

  it.each(EVIL)('tooltips/popups built from %s create no elements', (name) => {
    const div = document.createElement('div');
    document.body.append(div);
    const map = L.map(div).setView([0, 0], 3);
    const layer = new AircraftLayer(map);
    layer.sync([{ ucid: 'u', name, aircraft: 'F-16', coalition: 'blue', lat: 0, lon: 0, alt_m: null, in_air: true } as never], t);
    const marker = Object.values((map as never as { _layers: Record<string, L.Marker> })._layers).find((l) => l instanceof L.Marker) as L.Marker;
    marker.openTooltip();
    marker.openPopup();
    expect(div.querySelectorAll('img, script').length).toBe(0);
    expect(div.querySelector('.leaflet-tooltip')?.textContent).toContain(name);
    expect(placePopup({ name, lat: 1, lon: 2 }, 'k', t, map, null).querySelectorAll('img, script').length).toBe(0);
    map.remove();
  });
});
