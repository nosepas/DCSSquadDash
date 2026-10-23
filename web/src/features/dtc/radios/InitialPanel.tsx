import { useTranslation } from 'react-i18next';
import { INITIAL_RADIOS } from '../../../api/types.radios';
import { initialChanged } from '../../../lib/dtc/radioBaseline';
import { ToggleField } from '../../../components/form/ToggleField';
import { FreqField } from './FreqField';
import { IntField } from './IntField';
import type { RadioProps } from './RadioProps';
import { ResetButton } from './ResetButton';

/** AH-64 start-up settings: frequency and the preset each radio starts on, plus the UHF guard receiver. `mode` stays untouched. */
export function InitialPanel({ model, base, fromFile, act, report }: RadioProps) {
  const { t } = useTranslation();
  const initial = model.radios?.initial;
  if (!initial) return <p className="muted">{t('dtc.radios.empty')}</p>;
  const rn = (r: string) => t(`dtc.radios.ah64.radio.${r}`);
  const aria = (r: string) => t('dtc.radios.ah64.initialName', { radio: rn(r) });
  const preset = (id: string, r: string, value: number | undefined, commit: (n: number) => void) => (
    <IntField
      id={id} label={t('dtc.radios.ah64.startPreset')} aria={t('dtc.radios.ah64.startPresetAria', { name: aria(r) })}
      value={value} min={1} max={10} report={report} onCommit={commit}
    />
  );
  const freq = (id: string, r: string, label: string, name: string, value: number | undefined, commit: (mhz: number) => void) => (
    <FreqField id={id} label={label} aria={t('dtc.radios.freqAria', { name })} value={value} aircraft={model.aircraft} radioId={r} report={report} onCommit={commit} />
  );
  return (
    <div id="rd-panel" role="tabpanel" aria-labelledby="rd-tab-initial">
      <div className="rd-head">
        <p className="muted small">{t('dtc.radios.ah64.initialHelp')}</p>
        <ResetButton disabled={!initialChanged(model, base)} fromFile={fromFile} onReset={act.resetInitial} />
      </div>
      {INITIAL_RADIOS.map((r) => (
        <fieldset key={r} className="rd-row">
          <legend>{rn(r)}</legend>
          {freq(`rd-i-${r}-f`, r, t('dtc.radios.ah64.frequency'), aria(r), initial[r]?.frequency_mhz, (mhz) => act.initialRadio(r, { frequency_mhz: mhz }))}
          {preset(`rd-i-${r}-p`, r, initial[r]?.preset, (n) => act.initialRadio(r, { preset: n }))}
        </fieldset>
      ))}
      <fieldset className="rd-row">
        <legend>{rn('HF')}</legend>
        {freq('rd-i-HF-rx', 'HF_RX', rn('HF_RX'), `${aria('HF')} ${rn('HF_RX')}`, initial.HF?.rx?.frequency_mhz, (mhz) => act.initialHf({ rx: { frequency_mhz: mhz } }))}
        {freq('rd-i-HF-tx', 'HF_TX', rn('HF_TX'), `${aria('HF')} ${rn('HF_TX')}`, initial.HF?.tx?.frequency_mhz, (mhz) => act.initialHf({ tx: { frequency_mhz: mhz } }))}
        {preset('rd-i-HF-p', 'HF', initial.HF?.preset, (n) => act.initialHf({ preset: n }))}
      </fieldset>
      <ToggleField
        id="rd-guard" label={t('dtc.radios.ah64.guard')} help={t('dtc.radios.ah64.guardHelp')}
        checked={model.radios?.guard_receiver === true} onChange={act.guard}
      />
    </div>
  );
}
