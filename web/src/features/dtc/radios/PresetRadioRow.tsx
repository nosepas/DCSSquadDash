import { useTranslation } from 'react-i18next';
import type { PresetRadioId, RadioSettings } from '../../../api/types.radios';
import { FreqField } from './FreqField';
import { IntField } from './IntField';
import { ModulationField } from './ModulationField';
import type { ReportInvalid } from './RadioProps';

interface Props {
  preset: number;
  radio: PresetRadioId;
  settings: RadioSettings | undefined;
  aircraft: string;
  report: ReportInvalid;
  onChange: (patch: Partial<RadioSettings>) => void;
}

/** One of the six radios of a preset: frequency, modulation code and encryption code. */
export function PresetRadioRow({ preset, radio, settings, aircraft, report, onChange }: Props) {
  const { t } = useTranslation();
  const name = t('dtc.radios.ah64.presetRadioName', { n: preset, radio: t(`dtc.radios.ah64.radio.${radio}`) });
  const id = `rd-p${preset}-${radio}`;
  return (
    <fieldset className="rd-row">
      <legend>{t(`dtc.radios.ah64.radio.${radio}`)}</legend>
      <FreqField
        id={`${id}-f`} label={t('dtc.radios.ah64.frequency')} aria={t('dtc.radios.freqAria', { name })} value={settings?.frequency_mhz}
        aircraft={aircraft} radioId={radio} report={report} onCommit={(mhz) => onChange({ frequency_mhz: mhz })}
      />
      <ModulationField
        id={`${id}-m`} aria={t('dtc.radios.ah64.modAria', { name })} value={settings?.modulation} raw={radio.startsWith('HF')}
        report={report} onCommit={(modulation) => onChange({ modulation })}
      />
      <IntField
        id={`${id}-e`} label={t('dtc.radios.ah64.encryption')} aria={t('dtc.radios.ah64.encAria', { name })} value={settings?.encryption}
        min={0} report={report} onCommit={(encryption) => onChange({ encryption })} hint={t('dtc.radios.ah64.encryptionHint')}
      />
    </fieldset>
  );
}
