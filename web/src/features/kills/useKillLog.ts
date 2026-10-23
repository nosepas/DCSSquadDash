import { useCallback, useEffect, useState } from 'react';
import { ApiError } from '../../api/client';
import { fetchKills } from '../../api/stats';
import type { KillEvent } from '../../api/types';

export const PAGE_SIZE = 50;

interface KillLog {
  kills: KillEvent[];
  loading: boolean;
  error: ApiError | undefined;
  hasMore: boolean;
  loadMore: () => void;
  reload: () => void;
}

/** Kill log with "load more" pagination through the API's `before` cursor (time of the oldest loaded kill). */
export function useKillLog(serverId: string, liveTick: number): KillLog {
  const [kills, setKills] = useState<KillEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError>();
  const [hasMore, setHasMore] = useState(true);
  const [nonce, setNonce] = useState(0);

  // First page (re)loads on server change, live update or manual retry; extra pages stay as loaded.
  useEffect(() => {
    const ctrl = new AbortController();
    fetchKills(serverId, PAGE_SIZE, undefined, ctrl.signal)
      .then((first) => {
        setKills((old) => {
          const seen = new Set(first.map((k) => k.id));
          return [...first, ...old.filter((k) => !seen.has(k.id) && k.time_utc < (first.at(-1)?.time_utc ?? ''))];
        });
        setHasMore((h) => h && first.length === PAGE_SIZE);
        setError(undefined);
      })
      .catch((e: unknown) => {
        if (!ctrl.signal.aborted) setError(e instanceof ApiError ? e : new ApiError(0, 'unknown', 'error'));
      })
      .finally(() => !ctrl.signal.aborted && setLoading(false));
    return () => ctrl.abort();
  }, [serverId, liveTick, nonce]);

  useEffect(() => {
    setKills([]);
    setHasMore(true);
    setLoading(true);
  }, [serverId]);

  const loadMore = useCallback(() => {
    const last = kills.at(-1);
    if (!last) return;
    setLoading(true);
    fetchKills(serverId, PAGE_SIZE, last.time_utc)
      .then((page) => {
        setKills((old) => {
          const seen = new Set(old.map((k) => k.id));
          return [...old, ...page.filter((k) => !seen.has(k.id))];
        });
        setHasMore(page.length === PAGE_SIZE);
      })
      .catch((e: unknown) => setError(e instanceof ApiError ? e : new ApiError(0, 'unknown', 'error')))
      .finally(() => setLoading(false));
  }, [kills, serverId]);

  const reload = useCallback(() => setNonce((n) => n + 1), []);
  return { kills, loading, error, hasMore, loadMore, reload };
}
