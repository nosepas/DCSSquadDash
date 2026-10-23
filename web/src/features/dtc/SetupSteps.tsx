import { useTranslation } from 'react-i18next';
import type { Calibration, DtcAircraft, DtcModel, DtcTerrain } from '../../api/types.dtc';

const BADGE: Record<Calibration, string> = { exact: 'tag-ok', plausible: '', airports: 'tag-warn' };

export function CalibrationBadge({ level }: { level: Calibration | null }) {
  const { t } = useTranslation();
  if (!level) return null;
  return (
    <span className={`tag ${BADGE[level]}`} title={t(`dtc.calibration.${level}Hint`)}>
      {t(`dtc.calibration.${level}`)}
    </span>
  );
}

interface AircraftProps {
  aircraft: DtcAircraft[];
  value: string;
  onChange: (id: string) => void;
}

export function AircraftStep({ aircraft, value, onChange }: AircraftProps) {
  const { t } = useTranslation();
  return (
    <label className="field">
      <span>{t('dtc.steps.aircraft')}</span>
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        <option value="" disabled>{t('dtc.steps.pickAircraft')}</option>
        {aircraft.map((a) => (
          <option key={a.id} value={a.id} disabled={!a.enabled}>
            {a.enabled ? a.label : `${a.label} (${t('dtc.steps.soon')})`}
          </option>
        ))}
      </select>
    </label>
  );
}

interface TerrainProps {
  terrains: DtcTerrain[];
  model: DtcModel | null;
  onChange: (id: string) => void;
}

export function TerrainStep({ terrains, model, onChange }: TerrainProps) {
  const { t } = useTranslation();
  const current = terrains.find((x) => x.id === model?.terrain);
  return (
    <div className="field">
      <label htmlFor="dtc-terrain" className="field-label">{t('dtc.steps.terrain')}</label>
      <select id="dtc-terrain" value={model?.terrain ?? ''} disabled={!model} onChange={(e) => onChange(e.target.value)} aria-describedby="dtc-terrain-note">
        <option value="" disabled>{t('dtc.steps.pickTerrain')}</option>
        {terrains.map((x) => <option key={x.id} value={x.id}>{x.id}</option>)}
      </select>
      <p id="dtc-terrain-note" className="field-help">
        {current ? <><CalibrationBadge level={current.calibration} /> {t(`dtc.calibration.${current.calibration ?? 'plausible'}Hint`)}</> : t('dtc.steps.terrainHelp')}
      </p>
    </div>
  );
}

export function NameStep({ model, onChange }: { model: DtcModel | null; onChange: (name: string) => void }) {
  const { t } = useTranslation();
  return (
    <label className="field">
      <span>{t('dtc.steps.name')}</span>
      <input type="text" value={model?.name ?? ''} disabled={!model} placeholder="FOX3" onChange={(e) => onChange(e.target.value)} />
    </label>
  );
}
