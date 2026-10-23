import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { listServers } from '../../api/admin';
import { Card } from '../../components/Card';
import { AsyncView } from '../../components/states/AsyncView';
import { useAsync } from '../../hooks/useAsync';
import { useServers } from '../servers/ServerContext';
import { NewServerDialog } from './NewServerDialog';
import { OnlineBadge } from './OnlineBadge';

export default function ServersAdmin() {
  const { t } = useTranslation();
  const state = useAsync(listServers, []);
  const publicList = useServers().list;
  const [creating, setCreating] = useState(false);

  return (
    <Card
      actions={
        <button type="button" className="btn btn-primary" onClick={() => setCreating(true)}>
          {t('admin.servers.new')}
        </button>
      }
    >
      <AsyncView state={state} isEmpty={(d) => d.length === 0} emptyMessage={t('admin.servers.empty')}>
        {(servers) => (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th scope="col">{t('common.name')}</th>
                  <th scope="col">{t('common.status')}</th>
                  <th scope="col">{t('admin.servers.type')}</th>
                  <th scope="col">{t('admin.servers.address')}</th>
                  <th scope="col">{t('admin.servers.enabled')}</th>
                  <th scope="col">{t('common.actions')}</th>
                </tr>
              </thead>
              <tbody>
                {servers.map((s) => (
                  <tr key={s.server_id}>
                    <th scope="row"><Link to={`/admin/servers/${s.server_id}`}>{s.name}</Link></th>
                    <td><OnlineBadge online={s.online} /></td>
                    <td>{t(`missionType.${s.mission_type}`)}</td>
                    <td className="mono">{s.address ?? '–'}</td>
                    <td>{s.enabled ? t('common.yes') : t('common.no')}</td>
                    <td className="row-actions">
                      <Link className="btn" to={`/admin/servers/${s.server_id}`}>{t('admin.servers.configure')}</Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </AsyncView>
      <NewServerDialog open={creating} onClose={() => setCreating(false)} onCreated={publicList.reload} />
    </Card>
  );
}
