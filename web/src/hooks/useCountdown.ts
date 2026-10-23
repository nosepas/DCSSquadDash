import { useEffect, useState } from 'react';
import { remainingSeconds } from '../lib/format';

/** Seconds left until an ISO timestamp, ticking every second. */
export function useCountdown(expiresAtIso: string | undefined): number {
  const [left, setLeft] = useState(() => (expiresAtIso ? remainingSeconds(expiresAtIso, Date.now()) : 0));
  useEffect(() => {
    if (!expiresAtIso) return;
    const tick = () => setLeft(remainingSeconds(expiresAtIso, Date.now()));
    tick();
    const id = window.setInterval(tick, 1000);
    return () => window.clearInterval(id);
  }, [expiresAtIso]);
  return left;
}
