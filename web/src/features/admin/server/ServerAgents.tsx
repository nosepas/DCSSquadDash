import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { revokeAgent } from '../../../api/admin';
import type { Agent } from '../../../api/types';
import { ConfirmDialog } from '../../../components/ConfirmDialog';
import { ErrorState } from '../../../components/states/ErrorState';
import { useAction } from '../../../hooks/useAction';
import { formatDateTime } from '../../../lib/format';
import { agentState } from '../agentState';

interface Props {
  agents: Agent[];
  onChanged: () => void;
}

export function ServerAgents({ agents, onChanged }: Props) {
  const { t, i18n } = useTranslation();
  const [target, setTarget] = useState<Agent | null>(null);
  const action = useAction();
  const revoke = async () => {
    if (target && (await action.run(() => revokeAgent(target.agent_id)))) {
      setTarget(null);
      onChanged();
    }
  };
  const label = (a: Agent) => a.name ?? a.agent_id.slice(0, 8);
  return (
    <>
      <h3 className="section-title">{t('admin.server.connect.agents')}</h3>
      {action.error && <ErrorState error={action.error} />}
      {agents.length === 0 ? (
        <p className="muted">{t('admin.server.connect.noAgents')}</p>
      ) : (
        <ul className="list">
          {agents.map((a) => {
            const state = agentState(a);
            return (
              <li key={a.agent_id}>
                <span className="mono">{label(a)}</span>
                <span className={`tag ${state === 'active' ? 'tag-ok' : state === 'revoked' ? 'tag-warn' : ''}`}>{t(`admin.agents.${state}`)}</span>
                <span className="muted small">
                  {a.agent_version ?? '–'} · {formatDateTime(a.last_seen_at, i18n.language)}
                </span>
                {state !== 'revoked' && (
                  <button type="button" className="btn btn-danger" onClick={() => setTarget(a)}>{t('admin.agents.revoke')}</button>
                )}
              </li>
            );
          })}
        </ul>
      )}
      <ConfirmDialog
        open={target !== null}
        title={t('admin.agents.revokeTitle')}
        message={t('admin.server.connect.revokeConfirm', { name: target ? label(target) : '' })}
        confirmLabel={t('admin.agents.revoke')}
        busy={action.busy}
        onConfirm={() => void revoke()}
        onCancel={() => setTarget(null)}
      />
    </>
  );
}
