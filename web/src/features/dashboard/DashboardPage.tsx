import { useTranslation } from 'react-i18next';
import { fetchOverview } from '../../api/stats';
import { Card, PageHeader } from '../../components/Card';
import { AsyncView } from '../../components/states/AsyncView';
import { useAsync } from '../../hooks/useAsync';
import { useServerLive } from '../../hooks/useServerLive';
import { RankingTable } from '../ranking/RankingTable';
import { ServerGate } from '../servers/ServerGate';
import { KillFeed } from './KillFeed';
import { KpiGrid } from './KpiGrid';
import { MiniMap } from './MiniMap';
import { NewsList } from './NewsList';
import { WeatherCard } from './WeatherCard';

function DashboardContent({ serverId }: { serverId: string }) {
  const { t } = useTranslation();
  const tick = useServerLive(serverId);
  const state = useAsync((signal) => fetchOverview(serverId, signal), [serverId, tick]);
  return (
    <AsyncView state={state}>
      {(o) => (
        <>
          <KpiGrid data={o} />
          <div className="grid grid-dash">
            <MiniMap serverId={serverId} tick={tick} />
            <div className="stack">
              <WeatherCard weather={o.weather} />
              <Card title={t('dashboard.topShooters')}>
                <RankingTable rows={o.top_shooters} compact />
              </Card>
            </div>
            <KillFeed serverId={serverId} tick={tick} />
            <NewsList items={o.news} />
          </div>
        </>
      )}
    </AsyncView>
  );
}

export default function DashboardPage() {
  const { t } = useTranslation();
  return (
    <>
      <PageHeader title={t('dashboard.title')} />
      <ServerGate footholdOnly>{(s) => <DashboardContent serverId={s.server_id} />}</ServerGate>
    </>
  );
}
