import { useCallback, useEffect, useRef, useState } from 'react';
import { ApiError } from '../../../api/client';
import { fetchDefaultModel } from '../../../api/dtc';
import type { Draft } from '../../../lib/dtc/draft';
import { radioFillMode, withDefaultRadios, type RadioFill } from '../../../lib/dtc/radioDefaults';

type Update = (fn: (d: Draft) => Draft) => void;

/** Loads the default radios into a draft that has none: automatically for old drafts, on request for imported files. */
export function useRadioDefaults(draft: Draft | null, supported: boolean, update: Update) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const triedFor = useRef<string | null>(null);
  const mode: RadioFill = radioFillMode(draft, supported);
  const aircraft = draft?.model.aircraft ?? null;
  const terrain = draft?.model.terrain ?? null;

  const load = useCallback(async () => {
    if (!aircraft) return;
    setBusy(true);
    setError(null);
    try {
      const defaults = await fetchDefaultModel(aircraft, terrain);
      update((d) => withDefaultRadios(d, defaults));
    } catch (e) {
      setError(e instanceof ApiError ? e : new ApiError(0, 'unknown', 'error'));
    } finally {
      setBusy(false);
    }
  }, [aircraft, terrain, update]);

  useEffect(() => {
    if (mode === 'auto' && aircraft && triedFor.current !== aircraft) {  // once per aircraft: a failure leaves the manual button
      triedFor.current = aircraft;
      void load();
    }
  }, [mode, aircraft, load]);

  return { mode, busy, error, load };
}

export type RadioDefaults = ReturnType<typeof useRadioDefaults>;
