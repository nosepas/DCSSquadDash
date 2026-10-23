import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { fetchMap } from '../../api/servers';
import { Card } from '../../components/Card';
import { AsyncView } from '../../components/states/AsyncView';
import { useAsync } from '../../hooks/useAsync';
import { AircraftHint } from '../map/AircraftHint';
import { TacticalMap } from '../map/TacticalMap';
import { useMapAircraft } from '../map/useMapAircraft';

/** Non-interactive tactical map; the front line is the highlighted opposing-coalition connections. */
export function MiniMap({ serverId, tick }: { serverId: string; tick: number }) {
  const { t } = useTranslation();
  const state = useAsync((signal) => fetchMap(serverId, signal), [serverId, tick]);
  const air = useMapAircraft(serverId, tick);
  return (
    <Card title={t('dashboard.frontMap')} actions={<Link to="/map">{t('dashboard.openMap')}</Link>}>
      <AsyncView state={state} isEmpty={(d) => d.zones.length === 0} emptyMessage={t('map.noZones')}>
        {(data) =>
          data.calibrated ? (
            <>
              <AircraftHint hint={air.response?.hint} />
              <TacticalMap key={serverId} data={data} aircraft={air.shown} interactive={false} className="tmap-mini" />
            </>
          ) : (
            <p className="notice notice-warn">{t('map.notCalibrated')}</p>
          )
        }
      </AsyncView>
    </Card>
  );
}
