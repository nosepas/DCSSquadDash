import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { radioChanged } from '../../../lib/dtc/radioBaseline';
import { ChannelPanel } from './ChannelPanel';
import type { RadioProps } from './RadioProps';
import { SegTabs } from './SegTabs';

interface Props extends RadioProps {
  /** `limits.radio_channels` from /dtc/aircraft. */
  channels: number;
}

/** F-16C: COMM1 (UHF) and COMM2 (VHF) as tabs. */
export function ChannelRadios({ channels, ...rest }: Props) {
  const { t } = useTranslation();
  const ids = (rest.model.radios?.radios ?? []).map((r) => r.id);
  const [picked, setPicked] = useState('COMM1');
  const radioId = ids.includes(picked) ? picked : ids[0];
  if (!radioId) return <p className="muted">{t('dtc.radios.empty')}</p>;
  const items = ids.map((id) => ({ id, label: t(`dtc.radios.f16.${id}`, { defaultValue: id }), changed: radioChanged(rest.model, rest.base, id) }));
  return (
    <>
      <SegTabs items={items} value={radioId} onChange={setPicked} label={t('dtc.radios.f16.aria')} changedLabel={t('dtc.radios.changed')} />
      <ChannelPanel {...rest} radioId={radioId} channels={channels} />
    </>
  );
}
