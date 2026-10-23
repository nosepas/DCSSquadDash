import { useTranslation } from 'react-i18next';
import type { Overview } from '../../api/types';
import { CoalitionBar } from '../../components/Coalition';

function Kpi({ label, value, tone }: { label: string; value: number; tone?: string }) {
  return (
    <div className={`card kpi ${tone ?? ''}`}>
      <span className="kpi-label">{label}</span>
      <span className="kpi-value mono">{value}</span>
    </div>
  );
}

export function KpiGrid({ data }: { data: Overview }) {
  const { t } = useTranslation();
  const o = data.objectives;
  return (
    <div className="kpi-grid">
      <Kpi label={t('dashboard.kpi.online')} value={data.online} />
      <Kpi label={t('dashboard.kpi.airborne')} value={data.airborne} />
      <div className="card kpi kpi-wide">
        <span className="kpi-label">{t('dashboard.kpi.objectives')}</span>
        <span className="kpi-value mono">
          <span className="text-red">{o.red}</span>
          <span className="muted"> : </span>
          <span className="text-blue">{o.blue}</span>
          {o.neutral > 0 && <span className="muted small"> (+{o.neutral})</span>}
        </span>
        <CoalitionBar counts={o} />
      </div>
      <Kpi label={t('dashboard.kpi.atRisk')} value={data.at_risk} tone={data.at_risk > 0 ? 'kpi-warn' : ''} />
      <Kpi label={t('dashboard.kpi.kills1h')} value={data.kills_1h} />
      <Kpi label={t('dashboard.kpi.pilots')} value={data.pilots} />
    </div>
  );
}
