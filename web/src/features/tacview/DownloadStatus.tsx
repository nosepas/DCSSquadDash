import { useTranslation } from 'react-i18next';
import type { DownloadState } from './useTacviewDownload';

interface Props {
  state: DownloadState;
  onCancel: () => void;
}

/** Live feedback for the running download, or the friendly reason why the last one failed. */
export function DownloadStatus({ state, onCancel }: Props) {
  const { t } = useTranslation();
  if (state.errorKey) {
    return (
      <div className="notice notice-warn" role="alert">
        <b className="mono">{state.errorFile}</b>
        <p>{t(`tacview.errors.${state.errorKey}`)}</p>
      </div>
    );
  }
  if (state.phase === 'idle') return null;
  const text =
    state.phase === 'asking'
      ? t('tacview.asking')
      : state.percent === null
        ? t('tacview.downloadingUnknown')
        : t('tacview.downloading', { percent: `${state.percent}%` });
  return (
    <div className="notice dl-status" role="status">
      <span className="spinner" aria-hidden="true" />
      <span>{text}</span>
      <button type="button" className="btn" onClick={onCancel}>{t('tacview.cancel')}</button>
    </div>
  );
}
