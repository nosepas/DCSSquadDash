import { useTranslation } from 'react-i18next';
import type { ElevationState } from './useElevationFill';

/** Always-visible data credit for the approximate elevations, plus a hint when the lookup is not available. */
export function ElevationFooter({ state }: { state: ElevationState }) {
  const { t } = useTranslation();
  return (
    <footer className="muted small dtc-footer">
      <p>{t('dtc.elevation.attribution')}</p>
      {state === 'loading' && <p role="status">{t('dtc.elevation.loading')}</p>}
      {state === 'disabled' && <p role="status">{t('dtc.elevation.disabled')}</p>}
      {state === 'failed' && <p role="status">{t('dtc.elevation.failed')}</p>}
    </footer>
  );
}
