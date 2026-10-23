import { useTranslation } from 'react-i18next';
import type { AgentWarning } from '../../../api/types.admin';
import { warningKeys } from '../../../lib/warnings';

/** Agent warnings as friendly messages with what to do about them; unknown codes are shown raw. */
export function WarningList({ warnings }: { warnings: AgentWarning[] }) {
  const { t } = useTranslation();
  return (
    <ul className="warnings" aria-label={t('admin.server.status.warnings')}>
      {warnings.map((w, i) => {
        const keys = warningKeys(w.code);
        return (
          <li key={`${w.code}-${i}`} className="warning">
            <strong>{keys ? t(keys.title) : w.code}</strong>
            {keys && (
              <p>
                <b>{t('admin.server.status.whatToDo')}:</b> {t(keys.fix)}
              </p>
            )}
            {w.message && (
              <p className="muted small">
                {keys ? `${t('admin.server.status.technical')}: ` : ''}
                <span className="mono">{w.message}</span>
              </p>
            )}
          </li>
        );
      })}
    </ul>
  );
}
