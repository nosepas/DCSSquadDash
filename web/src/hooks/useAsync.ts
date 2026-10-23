import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ApiError } from '../api/client';

export interface AsyncState<T> {
  data: T | undefined;
  error: ApiError | undefined;
  loading: boolean;
  reload: () => void;
}

function toApiError(e: unknown): ApiError {
  return e instanceof ApiError ? e : new ApiError(0, 'unknown', e instanceof Error ? e.message : 'error');
}

/** Polled endpoints often return identical payloads; keeping the old reference avoids pointless redraws. */
function sameJson(a: unknown, b: unknown): boolean {
  return a !== undefined && JSON.stringify(a) === JSON.stringify(b);
}

/** Runs `fn` on mount and whenever `deps` change. Keeps the previous data while refetching (no flicker). */
export function useAsync<T>(fn: (signal: AbortSignal) => Promise<T>, deps: readonly unknown[], enabled = true): AsyncState<T> {
  const [state, setState] = useState<{ data?: T; error?: ApiError; loading: boolean }>({ loading: enabled });
  const [nonce, setNonce] = useState(0);
  const fnRef = useRef(fn);
  fnRef.current = fn;

  useEffect(() => {
    if (!enabled) return;
    const ctrl = new AbortController();
    setState((s) => ({ ...s, loading: true }));
    fnRef
      .current(ctrl.signal)
      .then((data) => setState((s) => ({ data: sameJson(s.data, data) ? s.data : data, loading: false })))
      .catch((e: unknown) => {
        if (ctrl.signal.aborted) return;
        setState((s) => ({ data: s.data, error: toApiError(e), loading: false }));
      });
    return () => ctrl.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, nonce, ...deps]);

  const reload = useCallback(() => setNonce((n) => n + 1), []);
  return useMemo(
    () => ({ data: state.data, error: state.error, loading: state.loading, reload }),
    [state.data, state.error, state.loading, reload],
  );
}
