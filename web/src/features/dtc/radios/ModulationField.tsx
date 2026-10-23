import { useTranslation } from 'react-i18next';
import { IntField } from './IntField';
import type { ReportInvalid } from './RadioProps';

interface Props {
  id: string;
  aria: string;
  value: number | undefined;
  /** HF: the code's meaning is unverified, so it is a raw number instead of AM/FM. */
  raw: boolean;
  report: ReportInvalid;
  onCommit: (code: number) => void;
}

/** FM/UHF/VHF: AM = 0 or FM = 1 (standard DCS codes; any other code in a file is kept and shown). HF: raw code. */
export function ModulationField({ id, aria, value, raw, report, onCommit }: Props) {
  const { t } = useTranslation();
  if (raw) {
    return <IntField id={id} label={t('dtc.radios.ah64.modulation')} aria={aria} value={value} min={0} report={report} onCommit={onCommit} hint={t('dtc.radios.ah64.hfModulationHint')} />;
  }
  const codes = value === undefined || value === 0 || value === 1 ? [0, 1] : [0, 1, value];
  return (
    <div className="dtc-num rd-field">
      <label htmlFor={id} className="dtc-num-label">{t('dtc.radios.ah64.modulation')}</label>
      <select id={id} aria-label={aria} value={value ?? ''} onChange={(e) => onCommit(Number(e.target.value))}>
        {value === undefined && <option value="" disabled>-</option>}
        {codes.map((c) => <option key={c} value={c}>{t(`dtc.radios.ah64.mod.${c === 0 || c === 1 ? c : 'other'}`, { code: c })}</option>)}
      </select>
    </div>
  );
}
