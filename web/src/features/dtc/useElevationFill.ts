import { useCallback, useEffect, useRef, useState } from 'react';
import { fetchElevation } from '../../api/dtc';
import type { DtcModel } from '../../api/types.dtc';
import { allLists } from '../../lib/dtc/lists';

export interface Fill {
  id: string;
  lat: number;
  lon: number;
  elevation: number;
}

export type ElevationState = 'idle' | 'loading' | 'disabled' | 'failed';

const DELAY_MS = 600;
const BATCH = 100;

/**
 * Collects points whose elevation should be looked up and asks the backend once (debounced, in batches of 100).
 * `onFilled` receives the answers; the caller decides whether each one still applies.
 */
export function useElevationFill(getModel: () => DtcModel | null, onFilled: (fills: Fill[]) => void) {
  const [state, setState] = useState<ElevationState>('idle');
  const pending = useRef(new Set<string>());
  const timer = useRef<number>();
  const cb = useRef({ getModel, onFilled });
  cb.current = { getModel, onFilled };

  const flush = useCallback(async () => {
    const model = cb.current.getModel();
    const ids = [...pending.current];
    pending.current.clear();
    if (!model || ids.length === 0) return;
    const points = allLists(model).flatMap((l) => l.points).filter((p) => p.id && ids.includes(p.id));
    setState('loading');
    try {
      for (let i = 0; i < points.length; i += BATCH) {
        const chunk = points.slice(i, i + BATCH);
        const res = await fetchElevation(chunk.map((p) => ({ lat: p.lat, lon: p.lon })));
        if (!res.enabled) {
          setState('disabled');
          return;
        }
        const fills: Fill[] = [];
        chunk.forEach((p, j) => {
          const e = res.elevations[j];
          if (p.id && typeof e === 'number') fills.push({ id: p.id, lat: p.lat, lon: p.lon, elevation: Math.round(e) });
        });
        cb.current.onFilled(fills);
      }
      setState('idle');
    } catch {
      setState('failed');
    }
  }, []);

  const queue = useCallback((ids: string[]) => {
    ids.forEach((id) => pending.current.add(id));
    window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => void flush(), DELAY_MS);
  }, [flush]);

  useEffect(() => () => window.clearTimeout(timer.current), []);
  return { queue, state };
}
