import { useTranslation } from 'react-i18next';
import { errorKey } from '../../lib/errors';
import type { Issue } from '../../lib/dtc/validate';
import type { DownloadResult } from './useDtcDownload';

interface Props {
  blocking: Issue[];
  download: DownloadResult;
  onClear: () => void;
}

/** Primary action, the reason it may be disabled, what happened afterwards, and how to use the file in DCS. */
export function DownloadBar({ blocking, download, onClear }: Props) {
  const { t } = useTranslation();
  const disabled = blocking.length > 0 || download.busy;
  return (
    <div className="dtc-download">
      <div className="dtc-download-row">
        <button type="button" className="btn btn-primary btn-lg" disabled={disabled} aria-describedby="dtc-why" onClick={() => void download.run()}>
          {download.busy ? t('dtc.download.busy') : t('dtc.download.button')}
        </button>
        <button type="button" className="btn btn-ghost" onClick={onClear}>{t('dtc.draft.clear')}</button>
      </div>
      <p id="dtc-why" className="muted small">{blocking.length > 0 ? t('dtc.download.disabled', { count: blocking.length }) : t('dtc.draft.saved')}</p>
      {download.templateExpired && (
        <div className="notice notice-warn" role="alert">
          <p>{t('dtc.download.expired')}</p>
          <button type="button" className="btn" onClick={() => void download.run(false)}>{t('dtc.download.useBuiltin')}</button>
        </div>
      )}
      {download.failure && <div className="notice notice-error" role="alert">{t(`errors.${errorKey(download.failure)}`)}</div>}
      {download.done && (
        <div className="notice" role="status">
          <b>{t('dtc.download.done')}</b>
          {download.warnings.length > 0 && <ul>{download.warnings.map((w) => <li key={w}>{w}</li>)}</ul>}
        </div>
      )}
      <details className="dtc-howto">
        <summary>{t('dtc.howto.title')}</summary>
        <p>{t('dtc.howto.body')}</p>
      </details>
    </div>
  );
}
