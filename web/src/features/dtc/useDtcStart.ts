import { useCallback, useState } from 'react';
import { ApiError } from '../../api/client';
import { fetchDefaultModel } from '../../api/dtc';
import type { DtcModel } from '../../api/types.dtc';

/** Starts a draft for an aircraft from the server's default model (real default radios). The user's map is kept. */
export function useDtcStart(terrain: string | null, begin: (model: DtcModel) => void) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const start = useCallback(async (aircraft: string) => {
    setBusy(true);
    setError(null);
    try {
      const model = await fetchDefaultModel(aircraft, terrain);
      begin({ ...model, terrain: model.terrain ?? terrain });
    } catch (e) {
      setError(e instanceof ApiError ? e : new ApiError(0, 'unknown', 'error'));
    } finally {
      setBusy(false);
    }
  }, [terrain, begin]);

  return { busy, error, start };
}
