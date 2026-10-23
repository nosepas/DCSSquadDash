import { useCallback, useEffect, useRef, useState } from 'react';
import { getServer } from '../../../api/admin';
import { ApiError } from '../../../api/client';
import type { AdminServer } from '../../../api/types.admin';

export const STATUS_REFRESH_MS = 10_000;

/** Loads one server and refreshes it every ~10 s (status, warnings); `apply` swaps in a fresh copy after a save. */
export function useServerDetail(id: string) {
  const [data, setData] = useState<AdminServer>();
  const [error, setError] = useState<ApiError>();
  const [nonce, setNonce] = useState(0);
  const hasData = useRef(false);
  const loadedId = useRef(id);

  const apply = useCallback((server: AdminServer) => {
    hasData.current = true;
    setError(undefined);
    setData((old) => (JSON.stringify(old) === JSON.stringify(server) ? old : server));
  }, []);

  useEffect(() => {
    const ctrl = new AbortController();
    if (loadedId.current !== id) {
      loadedId.current = id;
      hasData.current = false;
      setData(undefined);
    }
    const load = () =>
      getServer(id, ctrl.signal)
        .then(apply)
        .catch((e: unknown) => {
          if (ctrl.signal.aborted || hasData.current) return; // a failed refresh keeps showing the last data
          setError(e instanceof ApiError ? e : new ApiError(0, 'unknown', 'error'));
        });
    void load();
    const timer = window.setInterval(() => void load(), STATUS_REFRESH_MS);
    return () => {
      ctrl.abort();
      window.clearInterval(timer);
    };
  }, [id, nonce, apply]);

  const reload = useCallback(() => {
    setError(undefined);
    setNonce((n) => n + 1);
  }, []);
  return { data, error, reload, apply };
}
