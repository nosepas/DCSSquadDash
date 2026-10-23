import { useState } from 'react';
import { fetchAircraft } from '../../api/servers';
import { useAsync } from '../../hooks/useAsync';
import { useAuth } from '../auth/AuthContext';

export type Side = 'red' | 'blue';

/**
 * Friendly-aircraft data for a map. Anonymous visitors never trigger a request (the public map shows zones only);
 * the backend decides which coalitions a signed-in user may see. Admins can pick a side.
 */
export function useMapAircraft(serverId: string, tick: number) {
  const { status, isAdmin } = useAuth();
  const authed = status === 'authed';
  const [visible, setVisible] = useState(true);
  const [side, setSide] = useState<Side>();
  const requested = isAdmin ? side : undefined;
  const state = useAsync((signal) => fetchAircraft(serverId, requested, signal), [serverId, requested, tick], authed);
  const response = authed ? state.data : undefined;
  return {
    authed,
    isAdmin,
    visible,
    setVisible,
    side,
    setSide,
    response,
    shown: visible ? response?.aircraft : undefined,
  };
}

export type MapAircraft = ReturnType<typeof useMapAircraft>;
