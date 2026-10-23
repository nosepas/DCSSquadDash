import { useTranslation } from 'react-i18next';
import type { DtcAircraft } from '../../api/types.dtc';

interface Props {
  aircraft: DtcAircraft;
  /** Backend wording for oddities found in the imported file. */
  warnings: string[];
}

/** Tells the pilot which parts of the file exist but cannot be edited here and are kept exactly as they were. */
export function PreservedBox({ aircraft, warnings }: Props) {
  const { t } = useTranslation();
  return (
    <>
      {aircraft.unsupported.length > 0 && (
        <div className="notice" role="note">
          <b>{t('dtc.preserved.title')}</b>
          <p>{t('dtc.preserved.body')}</p>
          <ul>{aircraft.unsupported.map((u) => <li key={u}>{t(`dtc.preserved.parts.${u}`, { defaultValue: u })}</li>)}</ul>
        </div>
      )}
      {warnings.length > 0 && (
        <details className="notice notice-warn">
          <summary>{t('dtc.import.warnings', { count: warnings.length })}</summary>
          <ul>{warnings.map((w) => <li key={w}>{w}</li>)}</ul>
        </details>
      )}
    </>
  );
}
