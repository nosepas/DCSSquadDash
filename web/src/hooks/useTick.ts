import { useEffect, useState } from 'react';

/** Counter that goes up every `ms` while `enabled`; put it in the deps of a useAsync to poll. */
export function useTick(ms: number, enabled = true): number {
  const [tick, setTick] = useState(0);
  useEffect(() => {
    if (!enabled) return;
    const id = window.setInterval(() => setTick((n) => n + 1), ms);
    return () => window.clearInterval(id);
  }, [ms, enabled]);
  return tick;
}
