import { useTranslation } from 'react-i18next';
import type { DetectedFolder } from '../../../api/types.admin';

interface Props {
  items: DetectedFolder[] | undefined;
  current: string;
  onPick: (path: string) => void;
}

/** "Detected on the server" suggestions: clicking one fills the field (the admin still has to save). */
export function DetectedChips({ items, current, onPick }: Props) {
  const { t } = useTranslation();
  return (
    <div className="detected" aria-label={t('admin.server.detected.title')} role="group">
      <span className="detected-label">{t('admin.server.detected.title')}:</span>
      {items && items.length > 0 ? (
        items.map((d) => (
          <button
            key={d.path}
            type="button"
            className={`chip ${d.path === current ? 'chip-active' : ''}`}
            onClick={() => onPick(d.path)}
            title={t('admin.server.detected.pick', { path: d.path })}
          >
            <span className="mono">{d.path}</span>
            {d.note && <small>{d.note}</small>}
          </button>
        ))
      ) : (
        <span className="muted small">{t('admin.server.detected.none')}</span>
      )}
    </div>
  );
}
