import { useTranslation } from 'react-i18next';
import { fetchMap } from '../../api/servers';
import { Card, PageHeader } from '../../components/Card';
import { AsyncView } from '../../components/states/AsyncView';
import { useAsync } from '../../hooks/useAsync';
import { useServerLive } from '../../hooks/useServerLive';
import { ServerGate } from '../servers/ServerGate';
import { AircraftHint } from './AircraftHint';
import { AircraftLegend } from './AircraftLegend';
import { MapLegend } from './MapLegend';
import { TacticalMap } from './TacticalMap';
import { useMapAircraft } from './useMapAircraft';

function MapContent({ serverId }: { serverId: string }) {
  const { t } = useTranslation();
  const tick = useServerLive(serverId);
  const state = useAsync((signal) => fetchMap(serverId, signal), [serverId, tick]);
  const air = useMapAircraft(serverId, tick);
  return (
    <AsyncView state={state} isEmpty={(d) => d.zones.length === 0 && (air.shown?.length ?? 0) === 0} emptyMessage={t('map.noZones')}>
      {(data) => (
        <>
          {!data.calibrated && (
            <div className="notice notice-warn" role="note">
              {t('map.notCalibrated')}
            </div>
          )}
          <p className="muted small">
            {data.terrain && <span>{t('map.terrain')}: <b className="mono">{data.terrain}</b>{data.zones.length > 0 && ' · '}</span>}
            {data.zones.length > 0 && t('map.zones', { count: data.zones.length })}
          </p>
          <AircraftHint hint={air.response?.hint} />
          <div className="map-wrap">
            <TacticalMap key={serverId} data={data} aircraft={air.shown} className="tmap-full" />
          </div>
          <MapLegend>
            <AircraftLegend air={air} />
          </MapLegend>
        </>
      )}
    </AsyncView>
  );
}

export default function MapPage() {
  const { t } = useTranslation();
  return (
    <>
      <PageHeader title={t('map.title')} />
      <Card>
        <ServerGate>{(s) => <MapContent serverId={s.server_id} />}</ServerGate>
      </Card>
    </>
  );
}
