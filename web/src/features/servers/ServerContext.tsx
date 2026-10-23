import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react';
import { fetchServers } from '../../api/servers';
import type { ServerSummary } from '../../api/types';
import { useAsync, type AsyncState } from '../../hooks/useAsync';
import { readStored, writeStored } from '../../lib/storage';

const STORAGE_KEY = 'fox3.server';

interface ServerValue {
  list: AsyncState<ServerSummary[]>;
  current: ServerSummary | undefined;
  select: (id: string) => void;
}

const ServerContext = createContext<ServerValue | null>(null);

export function ServerProvider({ children }: { children: ReactNode }) {
  const list = useAsync(fetchServers, []);
  const [selectedId, setSelectedId] = useState(() => readStored(STORAGE_KEY));

  const select = useCallback((id: string) => {
    setSelectedId(id);
    writeStored(STORAGE_KEY, id);
  }, []);

  const value = useMemo(() => {
    const servers = list.data ?? [];
    const current = servers.find((s) => s.server_id === selectedId) ?? servers[0];
    return { list, current, select };
  }, [list, selectedId, select]);

  return <ServerContext.Provider value={value}>{children}</ServerContext.Provider>;
}

export function useServers(): ServerValue {
  const ctx = useContext(ServerContext);
  if (!ctx) throw new Error('useServers must be used inside ServerProvider');
  return ctx;
}
