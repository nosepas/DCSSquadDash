import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { PRESET_RADIOS } from '../../../api/types.radios';
import { presetChanged } from '../../../lib/dtc/radioBaseline';
import { PresetRadioRow } from './PresetRadioRow';
import type { RadioProps } from './RadioProps';
import { ResetButton } from './ResetButton';

/** AH-64 comm presets: pick 1..10, then call sign, unit id and the six radios. primary_frequency, dl_net and the HF ALE data stay untouched. */
export function PresetPanel({ model, base, fromFile, act, report }: RadioProps) {
  const { t } = useTranslation();
  const presets = model.radios?.presets ?? [];
  const [picked, setPicked] = useState(1);
  const preset = presets.find((p) => p.index === picked) ?? presets[0];
  if (!preset) return <p className="muted">{t('dtc.radios.empty')}</p>;
  const n = preset.index;
  const text = (key: 'unit_id' | 'call_sign') => (
    <label className="dtc-text">
      <span className="dtc-num-label">{t(`dtc.radios.ah64.${key}`)}</span>
      <input
        type="text" value={preset[key] ?? ''} autoComplete="off" aria-label={t(`dtc.radios.ah64.${key}Aria`, { n })}
        onChange={(e) => act.presetText(n, key, e.target.value)}
      />
    </label>
  );
  return (
    <div id="rd-panel" role="tabpanel" aria-labelledby="rd-tab-presets">
      <p className="muted small">{t('dtc.radios.ah64.codesHelp')}</p>
      <div role="group" aria-label={t('dtc.radios.ah64.presetPick')} className="dtc-lists">
        {presets.map((p) => (
          <button key={p.index} type="button" className={`chip${p.index === n ? ' chip-active' : ''}`} aria-pressed={p.index === n} onClick={() => setPicked(p.index)}>
            {p.index}
            {presetChanged(model, base, p.index) && <span className="rd-dot" role="img" aria-label={t('dtc.radios.changed')} />}
          </button>
        ))}
      </div>
      <div className="rd-head">
        <h3 className="rd-subtitle">{t('dtc.radios.ah64.presetN', { n })}</h3>
        <ResetButton disabled={!presetChanged(model, base, n)} fromFile={fromFile} onReset={() => act.resetPreset(n)} />
      </div>
      <div className="rd-texts">{text('unit_id')}{text('call_sign')}</div>
      {PRESET_RADIOS.map((radio) => (
        <PresetRadioRow
          key={`${n}-${radio}`} preset={n} radio={radio} settings={preset.radios?.[radio]} aircraft={model.aircraft} report={report}
          onChange={(patch) => act.presetRadio(n, radio, patch)}
        />
      ))}
    </div>
  );
}
