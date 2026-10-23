import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { listAgents, listServers, revokeAgent } from '../../api/admin';
import type { Agent } from '../../api/types';
import { Card } from '../../components/Card';
import { ConfirmDialog } from '../../components/ConfirmDialog';
import { AsyncView } from '../../components/states/AsyncView';
import { ErrorState } from '../../components/states/ErrorState';
import { useAction } from '../../hooks/useAction';
import { useAsync } from '../../hooks/useAsync';
import { formatDateTime } from '../../lib/format';
import { agentState } from './agentState';


export default function AgentsAdmin() {
  const { t, i18n } = useTranslation();
  const agents = useAsync(listAgents, []);
  const servers = useAsync(listServers, []);
  const [target, setTarget] = useState<Agent | null>(null);
  const action = useAction();
  const serverName = (id: string) => servers.data?.find((s) => s.server_id === id)?.name ?? id.slice(0, 8);

  const revoke = async () => {
    if (!target) return;
    if (await action.run(() => revokeAgent(target.agent_id))) {
      setTarget(null);
      agents.reload();
    }
  };

  return (
    <Card>
      {action.error && <ErrorState error={action.error} />}
      <AsyncView state={agents} isEmpty={(d) => d.length === 0} emptyMessage={t('admin.agents.empty')}>
        {(list) => (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th scope="col">{t('admin.agents.agent')}</th>
                  <th scope="col">{t('admin.agents.server')}</th>
                  <th scope="col">{t('admin.agents.version')}</th>
                  <th scope="col">{t('admin.agents.lastSeen')}</th>
                  <th scope="col">{t('admin.agents.state')}</th>
                  <th scope="col">{t('common.actions')}</th>
                </tr>
              </thead>
              <tbody>
                {list.map((a) => {
                  const state = agentState(a);
                  return (
                    <tr key={a.agent_id}>
                      <th scope="row" className="mono">{a.name ?? a.agent_id.slice(0, 8)}</th>
                      <td>{serverName(a.server_id)}</td>
                      <td className="mono">{a.agent_version ?? '–'}</td>
                      <td className="mono">{formatDateTime(a.last_seen_at, i18n.language)}</td>
                      <td><span className={`tag ${state === 'active' ? 'tag-ok' : state === 'revoked' ? 'tag-warn' : ''}`}>{t(`admin.agents.${state}`)}</span></td>
                      <td>
                        {state !== 'revoked' && (
                          <button type="button" className="btn btn-danger" onClick={() => setTarget(a)}>
                            {t('admin.agents.revoke')}
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </AsyncView>
      <ConfirmDialog
        open={target !== null}
        title={t('admin.agents.revokeTitle')}
        message={t('admin.agents.revokeConfirm', { name: target?.name ?? target?.agent_id ?? '' })}
        confirmLabel={t('admin.agents.revoke')}
        busy={action.busy}
        onConfirm={() => void revoke()}
        onCancel={() => setTarget(null)}
      />
    </Card>
  );
}
