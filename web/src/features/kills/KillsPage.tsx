import { useTranslation } from 'react-i18next';
import { Card, PageHeader } from '../../components/Card';
import { EmptyState } from '../../components/states/EmptyState';
import { ErrorState } from '../../components/states/ErrorState';
import { Loading } from '../../components/states/Loading';
import { useServerLive } from '../../hooks/useServerLive';
import { ServerGate } from '../servers/ServerGate';
import { KillSummary, KillTime } from './KillRow';
import { useKillLog } from './useKillLog';

function KillsContent({ serverId }: { serverId: string }) {
  const { t } = useTranslation();
  const tick = useServerLive(serverId);
  const log = useKillLog(serverId, tick);

  if (log.kills.length === 0) {
    if (log.loading) return <Loading />;
    if (log.error) return <ErrorState error={log.error} onRetry={log.reload} />;
    return <EmptyState message={t('dashboard.noKills')} />;
  }
  return (
    <>
      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th scope="col">{t('kills.time')}</th>
              <th scope="col">{t('kills.killer')} / {t('kills.victim')}</th>
              <th scope="col">{t('kills.weapon')}</th>
            </tr>
          </thead>
          <tbody>
            {log.kills.map((k) => (
              <tr key={k.id}>
                <td><KillTime iso={k.time_utc} /></td>
                <td><KillSummary kill={k} /></td>
                <td className="mono">{k.weapon ?? '–'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {log.error && <ErrorState error={log.error} />}
      <div className="load-more">
        {log.hasMore ? (
          <button type="button" className="btn" onClick={log.loadMore} disabled={log.loading}>
            {log.loading ? t('common.loading') : t('common.loadMore')}
          </button>
        ) : (
          <span className="muted">{t('common.noMore')}</span>
        )}
      </div>
    </>
  );
}

export default function KillsPage() {
  const { t } = useTranslation();
  return (
    <>
      <PageHeader title={t('kills.title')} />
      <Card>
        <ServerGate footholdOnly>{(s) => <KillsContent serverId={s.server_id} />}</ServerGate>
      </Card>
    </>
  );
}
