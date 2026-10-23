import { useTranslation } from 'react-i18next';
import { formatFrequency, parseFrequency } from '../../../lib/dtc/radioFreq';
import { BAND_RANGES, bandOf, isOutOfRange, isUnconfirmedFraction } from '../../../lib/dtc/radioRanges';
import type { ReportInvalid } from './RadioProps';
import { useRadioInput } from './useRadioInput';

interface Props {
  id: string;
  /** Short visible label ("Ch 3", "UHF"). */
  label: string;
  /** Full accessible name, e.g. "COMM1 channel 3 frequency, MHz". */
  aria: string;
  value: number | undefined;
  aircraft: string;
  radioId: string;
  changed?: boolean;
  report: ReportInvalid;
  onCommit: (mhz: number) => void;
}

/** One frequency in MHz (comma or dot), with the non-blocking range warning, the F-16 fraction note and a "changed" marker. */
export function FreqField({ id, label, aria, value, aircraft, radioId, changed, report, onCommit }: Props) {
  const { t } = useTranslation();
  const input = useRadioInput({ id, value, format: formatFrequency, parse: parseFrequency, onCommit, report });
  const band = bandOf(aircraft, radioId);
  const shown = parseFrequency(input.text);
  const mhz = shown.ok ? shown.value : value;
  const out = band !== null && mhz !== undefined && isOutOfRange(aircraft, radioId, mhz);
  const fraction = mhz !== undefined && isUnconfirmedFraction(aircraft, mhz);
  return (
    <div className={`dtc-num rd-field${input.error ? ' field-invalid' : ''}${changed ? ' rd-changed' : ''}`}>
      <label htmlFor={id} className="dtc-num-label">
        {label}
        {changed && <span className="rd-dot" role="img" aria-label={t('dtc.radios.changed')} title={t('dtc.radios.changed')} />}
      </label>
      <input
        id={id} type="text" inputMode="decimal" autoComplete="off" spellCheck={false} aria-label={aria} value={input.text}
        aria-invalid={input.error ? true : undefined} aria-describedby={`${id}-note`}
        onChange={(e) => input.change(e.target.value)} onBlur={input.blur}
      />
      <span id={`${id}-note`} className="rd-notes">
        {input.error && <small className="field-error" role="alert">{t(`dtc.radios.errors.${input.error}`)}</small>}
        {!input.error && out && band && (
          <small className="rd-warn">{t('dtc.radios.outOfRange', { min: BAND_RANGES[band][0], max: BAND_RANGES[band][1] })}</small>
        )}
        {!input.error && fraction && <small className="rd-warn">{t('dtc.radios.fraction')}</small>}
      </span>
    </div>
  );
}
