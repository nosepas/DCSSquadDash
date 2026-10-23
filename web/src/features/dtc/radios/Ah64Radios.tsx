import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { initialChanged, presetChanged } from '../../../lib/dtc/radioBaseline';
import { InitialPanel } from './InitialPanel';
import { PresetPanel } from './PresetPanel';
import type { RadioProps } from './RadioProps';
import { SegTabs } from './SegTabs';

/** AH-64D: "Presets" and "Initial settings" tabs. */
export function Ah64Radios(props: RadioProps) {
  const { t } = useTranslation();
  const [tab, setTab] = useState('presets');
  const { model, base } = props;
  const anyPreset = (model.radios?.presets ?? []).some((p) => presetChanged(model, base, p.index));
  const items = [
    { id: 'presets', label: t('dtc.radios.ah64.tabPresets'), changed: anyPreset },
    { id: 'initial', label: t('dtc.radios.ah64.tabInitial'), changed: initialChanged(model, base) },
  ];
  return (
    <>
      <SegTabs items={items} value={tab} onChange={setTab} label={t('dtc.radios.ah64.tabsAria')} changedLabel={t('dtc.radios.changed')} />
      {tab === 'presets' ? <PresetPanel {...props} /> : <InitialPanel {...props} />}
    </>
  );
}
