import { useTranslation } from 'react-i18next';
import { fetchObjectives } from '../../api/stats';
import { Card, PageHeader } from '../../components/Card';
import { CoalitionBadge } from '../../components/Coalition';
import { AsyncView } from '../../components/states/AsyncView';
import { useAsync } from '../../hooks/useAsync';
import { useServerLive } from '../../hooks/useServerLive';
import { ServerGate } from '../servers/ServerGate';

function ObjectivesTable({ serverId }: { serverId: string }) {
  const { t } = useTranslation();
  const tick = useServerLive(serverId);
  const state = useAsync((signal) => fetchObjectives(serverId, signal), [serverId, tick]);
  return (
    <AsyncView state={state} isEmpty={(d) => d.length === 0}>
      {(zones) => (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th scope="col">{t('objectives.zone')}</th>
                <th scope="col">{t('objectives.coalition')}</th>
                <th scope="col" className="num">{t('objectives.level')}</th>
                <th scope="col">{t('objectives.state')}</th>
              </tr>
            </thead>
            <tbody>
              {zones.map((z) => (
                <tr key={z.name}>
                  <th scope="row">
                    {z.name} {z.is_hq && <span className="tag">{t('objectives.hq')}</span>}
                  </th>
                  <td><CoalitionBadge coalition={z.coalition} /></td>
                  <td className="num mono">{z.level ?? '–'}</td>
                  <td>
                    {z.at_risk ? <span className="tag tag-warn">{t('objectives.atRisk')}</span> : <span className="muted">{t('objectives.safe')}</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </AsyncView>
  );
}

export default function ObjectivesPage() {
  const { t } = useTranslation();
  return (
    <>
      <PageHeader title={t('objectives.title')} />
      <Card>
        <ServerGate footholdOnly>{(s) => <ObjectivesTable serverId={s.server_id} />}</ServerGate>
      </Card>
    </>
  );
}
