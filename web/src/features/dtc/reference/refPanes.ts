import { useMemo } from 'react';
import L from 'leaflet';

/** Reference panes sit between the tiles (200) and the user's route lines (overlay pane, 400) and pins (marker pane, 600). */
const LINES = 'fox-ref-lines';
const DOTS = 'fox-ref-dots';
const MARKS = 'fox-ref-marks';

export interface RefPanes {
  lines: L.SVG;
  dots: L.Canvas;
  /** Pane name for DOM markers (FARPs and airfield labels). */
  marks: string;
}

function pane(map: L.Map, name: string, z: number): void {
  if (!map.getPane(name)) map.createPane(name).style.zIndex = String(z);
}

/** Panes and renderers for the reference layers: canvas for the many dots, SVG for the few lines. */
export function useRefPanes(map: L.Map | null): RefPanes | null {
  return useMemo(() => {
    if (!map) return null;
    pane(map, LINES, 360);
    pane(map, DOTS, 370);
    pane(map, MARKS, 380);
    return { lines: L.svg({ pane: LINES }), dots: L.canvas({ pane: DOTS, padding: 0.3 }), marks: MARKS };
  }, [map]);
}
