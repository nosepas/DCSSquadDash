import { useEffect } from 'react';
import { getServer } from '../../../../api/admin';
import type { AdminServer } from '../../../../api/types.admin';
import { POLL_MS } from '../../../../lib/agentWizard';

/** While `active`, refreshes the server detail every 3 s (paused while the tab is hidden; stops on unmount). */
export function useAgentPoll(serverId: string, active: boolean, apply: (server: AdminServer) => void): void {
  useEffect(() => {
    if (!active) return;
    const ctrl = new AbortController();
    const tick = () => {
      if (document.hidden) return;
      getServer(serverId, ctrl.signal).then(apply).catch(() => undefined); // a failed poll just retries in 3 s
    };
    const id = window.setInterval(tick, POLL_MS);
    return () => {
      ctrl.abort();
      window.clearInterval(id);
    };
  }, [serverId, active, apply]);
}
