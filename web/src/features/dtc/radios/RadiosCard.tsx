import { useTranslation } from 'react-i18next';
import type { DtcAircraft } from '../../../api/types.dtc';
import { Card } from '../../../components/Card';
import { errorKey } from '../../../lib/errors';
import { Ah64Radios } from './Ah64Radios';
import { ChannelRadios } from './ChannelRadios';
import type { RadioProps } from './RadioProps';
import type { RadioDefaults } from './useRadioDefaults';

interface Props extends RadioProps {
  info: DtcAircraft | undefined;
  defaults: RadioDefaults;
}

function MissingRadios({ defaults }: { defaults: RadioDefaults }) {
  const { t } = useTranslation();
  if (defaults.mode === 'auto' && !defaults.error) return <p className="muted" role="status">{t('dtc.radios.loading')}</p>;
  const fromFile = defaults.mode === 'ask';
  return (
    <div className="notice" role="note">
      <p>{t(fromFile ? 'dtc.radios.missingFile' : 'dtc.radios.missing')}</p>
      {defaults.error && <p role="alert">{t(`errors.${errorKey(defaults.error)}`)}</p>}
      <button type="button" className="btn" disabled={defaults.busy} onClick={() => void defaults.load()}>
        {t(fromFile ? 'dtc.radios.loadDefaultsFile' : 'dtc.radios.loadDefaults')}
      </button>
    </div>
  );
}

/** The "Radios" section: the aircraft's own editor, or a calm note when its DTC has no radios. */
export function RadiosCard({ info, defaults, ...props }: Props) {
  const { t } = useTranslation();
  const supported = !!info?.supports.includes('radios');
  const body = () => {
    if (!supported) return <div className="notice" role="note">{t('dtc.radios.none')}</div>;
    if (!props.model.radios) return <MissingRadios defaults={defaults} />;
    if (props.model.aircraft === 'AH-64D_BLK_II') return <Ah64Radios {...props} />;
    return <ChannelRadios {...props} channels={info?.limits.radio_channels ?? 20} />;
  };
  return (
    <Card title={t('dtc.radios.title')} className="rd-card">
      {supported && <p className="muted small">{t('dtc.radios.intro')}</p>}
      {body()}
    </Card>
  );
}
