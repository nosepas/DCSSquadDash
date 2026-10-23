import type { AdminServer } from '../../../api/types.admin';
import { ServerAgents } from './ServerAgents';
import { AgentWizard } from './wizard/AgentWizard';

interface Props {
  server: AdminServer;
  apply: (server: AdminServer) => void;
  onChanged: () => void;
}

/** "Connect an agent": the guided installer wizard, then the list of this server's agents (with Revoke). */
export function ConnectSection({ server, apply, onChanged }: Props) {
  return (
    <>
      <AgentWizard server={server} apply={apply} />
      <div className="card wizard-agents">
        <ServerAgents agents={server.agents} onChanged={onChanged} />
      </div>
    </>
  );
}
