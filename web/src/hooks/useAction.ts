import { useCallback, useState } from 'react';
import { ApiError } from '../api/client';

/** Wraps a mutation with busy/error state. `run` resolves true on success, false on failure. */
export function useAction() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<ApiError>();

  const run = useCallback(async (fn: () => Promise<unknown>): Promise<boolean> => {
    setBusy(true);
    setError(undefined);
    try {
      await fn();
      return true;
    } catch (e) {
      setError(e instanceof ApiError ? e : new ApiError(0, 'unknown', 'error'));
      return false;
    } finally {
      setBusy(false);
    }
  }, []);

  const clear = useCallback(() => setError(undefined), []);
  return { busy, error, run, clear };
}
