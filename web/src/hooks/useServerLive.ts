import { useEffect, useRef, useState } from 'react';
import { API_BASE } from '../api/client';
import { useAuth } from '../features/auth/AuthContext';

export const POLL_INTERVAL_MS = 15_000;

/**
 * Returns a counter that increments whenever the server's data changed.
 * Logged-in users get SSE (EventSource reconnects by itself); anonymous visitors, and any moment SSE is
 * not connected, fall back to polling every 15 s. Put the counter in the deps of your useAsync.
 */
export function useServerLive(serverId: string | undefined): number {
  const { status } = useAuth();
  const [tick, setTick] = useState(0);
  const sseOpen = useRef(false);

  useEffect(() => {
    if (!serverId) return;
    const bump = () => setTick((t) => t + 1);
    let es: EventSource | null = null;
    sseOpen.current = false;
    if (status === 'authed' && typeof EventSource !== 'undefined') {
      es = new EventSource(`${API_BASE}/servers/${serverId}/stream`, { withCredentials: true });
      es.onopen = () => {
        sseOpen.current = true;
      };
      es.onerror = () => {
        sseOpen.current = false;
      };
      es.addEventListener('update', bump);
    }
    const poll = window.setInterval(() => {
      if (!sseOpen.current) bump();
    }, POLL_INTERVAL_MS);
    return () => {
      window.clearInterval(poll);
      es?.close();
    };
  }, [serverId, status]);

  return tick;
}
