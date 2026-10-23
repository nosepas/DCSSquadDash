import { useTranslation } from 'react-i18next';
import { fetchMissions } from '../../api/servers';
import type { Mission } from '../../api/types';
import { Card, PageHeader } from '../../components/Card';
import { AsyncView } from '../../components/states/AsyncView';
import { useAsync } from '../../hooks/useAsync';
import { useServerLive } from '../../hooks/useServerLive';
import { formatDateTime } from '../../lib/format';
import { ServerGate } from '../servers/ServerGate';

function MissionCard({ mission }: { mission: Mission }) {
  const { t, i18n } = useTranslation();
  return (
    <Card title={mission.current ? t('missions.current') : undefined} className="mission-card">
      <h3 className="mission-name mono">{mission.name}</h3>
      <dl className="facts">
        <div>
          <dt>{t('missions.terrain')}</dt>
          <dd className="mono">{mission.terrain ?? '–'}</dd>
        </div>
        <div>
          <dt>{t('missions.type')}</dt>
          <dd>{t(`missionType.${mission.mission_type}`)}</dd>
        </div>
        <div>
          <dt>{t('missions.started')}</dt>
          <dd className="mono">{formatDateTime(mission.started_at, i18n.language)}</dd>
        </div>
      </dl>
    </Card>
  );
}

function MissionsContent({ serverId }: { serverId: string }) {
  const { t } = useTranslation();
  const tick = useServerLive(serverId);
  const state = useAsync((signal) => fetchMissions(serverId, signal), [serverId, tick]);
  return (
    <AsyncView state={state} isEmpty={(d) => d.length === 0} emptyMessage={t('missions.none')}>
      {(missions) => missions.map((m) => <MissionCard key={`${m.name}-${m.started_at}`} mission={m} />)}
    </AsyncView>
  );
}

export default function MissionsPage() {
  const { t } = useTranslation();
  return (
    <>
      <PageHeader title={t('missions.title')} />
      <ServerGate>{(s) => <MissionsContent serverId={s.server_id} />}</ServerGate>
    </>
  );
}
