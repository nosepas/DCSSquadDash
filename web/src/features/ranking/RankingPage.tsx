import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { fetchRanking, type RankingSort } from '../../api/stats';
import { Card, PageHeader } from '../../components/Card';
import { AsyncView } from '../../components/states/AsyncView';
import { useAsync } from '../../hooks/useAsync';
import { useServerLive } from '../../hooks/useServerLive';
import { ServerGate } from '../servers/ServerGate';
import { RankingTable } from './RankingTable';

const SORTS: RankingSort[] = ['points', 'kills', 'kd'];

function RankingContent({ serverId }: { serverId: string }) {
  const { t } = useTranslation();
  const [sort, setSort] = useState<RankingSort>('points');
  const tick = useServerLive(serverId);
  const state = useAsync((signal) => fetchRanking(serverId, sort, 50, signal), [serverId, sort, tick]);
  return (
    <>
      <div className="segmented" role="group" aria-label={t('ranking.sortBy')}>
        {SORTS.map((s) => (
          <button key={s} type="button" aria-pressed={sort === s} className={sort === s ? 'active' : ''} onClick={() => setSort(s)}>
            {t(`ranking.${s}`)}
          </button>
        ))}
      </div>
      <AsyncView state={state} isEmpty={(d) => d.length === 0}>{(rows) => <RankingTable rows={rows} />}</AsyncView>
    </>
  );
}

export default function RankingPage() {
  const { t } = useTranslation();
  return (
    <>
      <PageHeader title={t('ranking.title')} />
      <Card>
        <ServerGate footholdOnly>{(s) => <RankingContent serverId={s.server_id} />}</ServerGate>
      </Card>
    </>
  );
}
