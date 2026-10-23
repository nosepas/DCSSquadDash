import { useTranslation } from 'react-i18next';
import type { Weather } from '../../api/types';
import { Card } from '../../components/Card';
import { msToKnots } from '../../lib/format';

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd className="mono">{value}</dd>
    </div>
  );
}

export function WeatherCard({ weather }: { weather: Weather | null }) {
  const { t } = useTranslation();
  const w = weather ?? {};
  const has = Object.values(w).some((v) => v !== undefined);
  return (
    <Card title={t('dashboard.weather')}>
      {!has ? (
        <p className="muted">{t('dashboard.noWeather')}</p>
      ) : (
        <dl className="facts">
          {w.temperature_c !== undefined && <Row label={t('dashboard.temperature')} value={`${w.temperature_c.toFixed(0)} °C`} />}
          {w.qnh_hpa !== undefined && <Row label={t('dashboard.qnh')} value={`${w.qnh_hpa.toFixed(0)} hPa`} />}
          {w.wind_speed_ms !== undefined && (
            <Row
              label={t('dashboard.wind')}
              value={`${String(w.wind_dir_deg ?? '–').padStart(3, '0')}° / ${msToKnots(w.wind_speed_ms)} kt`}
            />
          )}
          {w.visibility_m !== undefined && <Row label={t('dashboard.visibility')} value={`${(w.visibility_m / 1000).toFixed(0)} km`} />}
        </dl>
      )}
    </Card>
  );
}
