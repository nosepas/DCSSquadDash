import { useTranslation } from 'react-i18next';
import { parseWhole } from '../../../lib/dtc/radioFreq';
import type { ReportInvalid } from './RadioProps';
import { useRadioInput } from './useRadioInput';

interface Props {
  id: string;
  label: string;
  aria: string;
  value: number | undefined;
  min: number;
  max?: number;
  report: ReportInvalid;
  onCommit: (n: number) => void;
  /** Visible explanation under the field (also its tooltip). */
  hint?: string;
}

const format = (v: number | undefined): string => (v === undefined ? '' : String(v));

/** Small whole number (raw DCS code or preset number); invalid text reverts on blur like the frequencies. */
export function IntField({ id, label, aria, value, min, max, report, onCommit, hint }: Props) {
  const { t } = useTranslation();
  const parse = (s: string) => {
    const r = parseWhole(s, min, max);
    return r.ok ? r : { ok: false as const, reason: 'int' };
  };
  const input = useRadioInput<number>({ id, value, report, onCommit, format, parse });
  return (
    <div className={`dtc-num rd-field${input.error ? ' field-invalid' : ''}`} title={hint}>
      <label htmlFor={id} className="dtc-num-label">{label}</label>
      <input
        id={id} type="text" inputMode="numeric" autoComplete="off" aria-label={aria} value={input.text}
        aria-invalid={input.error ? true : undefined} aria-describedby={`${id}-note`}
        onChange={(e) => input.change(e.target.value)} onBlur={input.blur}
      />
      <span id={`${id}-note`} className="rd-notes">
        {input.error && <small className="field-error" role="alert">{t('dtc.radios.errors.int', { min, max: max ?? '∞' })}</small>}
        {!input.error && hint && <small className="muted">{hint}</small>}
      </span>
    </div>
  );
}
