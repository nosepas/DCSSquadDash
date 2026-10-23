import { useTranslation } from 'react-i18next';

export function OnlineBadge({ online }: { online: boolean }) {
  const { t } = useTranslation();
  return (
    <span className={`status-badge ${online ? 'status-on' : 'status-off'}`}>
      <span className="dot" aria-hidden="true" />
      {online ? t('common.online') : t('common.offline')}
    </span>
  );
}
