import { useTranslation } from 'react-i18next';
import { fetchKills } from '../../api/stats';
import { Card } from '../../components/Card';
import { AsyncView } from '../../components/states/AsyncView';
import { useAsync } from '../../hooks/useAsync';
import { KillSummary, KillTime } from '../kills/KillRow';

export function KillFeed({ serverId, tick }: { serverId: string; tick: number }) {
  const { t } = useTranslation();
  const state = useAsync((signal) => fetchKills(serverId, 10, undefined, signal), [serverId, tick]);
  return (
    <Card title={t('dashboard.feed')}>
      <AsyncView state={state} isEmpty={(d) => d.length === 0} emptyMessage={t('dashboard.noKills')}>
        {(kills) => (
          <ul className="feed">
            {kills.map((k) => (
              <li key={k.id} className="news">
                <KillTime iso={k.time_utc} />
                <KillSummary kill={k} />
                {k.weapon && <span className="tag mono">{k.weapon}</span>}
              </li>
            ))}
          </ul>
        )}
      </AsyncView>
    </Card>
  );
}
