import { useTranslation } from 'react-i18next';
import { channelChanged, freqOf, radioChanged } from '../../../lib/dtc/radioBaseline';
import { BAND_RANGES, bandOf } from '../../../lib/dtc/radioRanges';
import { FreqField } from './FreqField';
import type { RadioProps } from './RadioProps';
import { ResetButton } from './ResetButton';

interface Props extends RadioProps {
  radioId: string;
  channels: number;
}

/** One F-16 radio: its band hint, a reset action and the grid of channels (frequency only; modulation is preserved raw). */
export function ChannelPanel({ radioId, channels, model, base, fromFile, act, report }: Props) {
  const { t } = useTranslation();
  const band = bandOf(model.aircraft, radioId);
  return (
    <div id="rd-panel" role="tabpanel" aria-labelledby={`rd-tab-${radioId}`}>
      <div className="rd-head">
        {band && <p className="muted small">{t('dtc.radios.band', { band, min: BAND_RANGES[band][0], max: BAND_RANGES[band][1] })}</p>}
        <ResetButton disabled={!radioChanged(model, base, radioId)} fromFile={fromFile} onReset={() => act.resetRadio(radioId)} />
      </div>
      <div className="rd-grid">
        {Array.from({ length: channels }, (_, i) => i + 1).map((n) => (
          <FreqField
            key={`${radioId}-${n}`} id={`rd-${radioId}-${n}`} label={t('dtc.radios.channel', { n })}
            aria={t('dtc.radios.freqAria', { name: t('dtc.radios.channelName', { radio: radioId, n }) })}
            value={freqOf(model.radios, radioId, n)} aircraft={model.aircraft} radioId={radioId}
            changed={channelChanged(model, base, radioId, n)} report={report} onCommit={(mhz) => act.channel(radioId, n, mhz)}
          />
        ))}
      </div>
    </div>
  );
}
