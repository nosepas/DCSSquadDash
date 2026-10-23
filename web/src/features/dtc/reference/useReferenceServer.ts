import { useEffect, useMemo, useState } from 'react';
import type { ServerSummary } from '../../../api/types';
import { matchingServers, pickReferenceServer } from '../../../lib/dtc/reference';
import { useServers } from '../../servers/ServerContext';

/**
 * The Foothold server whose state the reference layers show: the user's pick, else the header's server, else the first
 * one playing this map. The server list is reloaded on every `tick` so a server that just reported its map shows up.
 */
export function useReferenceServer(terrain: string | null, tick: number) {
  const { list, current } = useServers();
  const [chosen, setChosen] = useState<string>();
  const { reload } = list;
  useEffect(() => {
    if (tick > 0) reload();
  }, [tick, reload]);

  const servers = list.data;
  const matches = useMemo<ServerSummary[]>(() => matchingServers(servers ?? [], terrain), [servers, terrain]);
  const selected = useMemo(() => pickReferenceServer(servers ?? [], terrain, current?.server_id, chosen), [servers, terrain, current, chosen]);
  return { matches, selected, choose: setChosen };
}
