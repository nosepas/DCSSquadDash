import { useTranslation } from 'react-i18next';

export function Loading({ label }: { label?: string }) {
  const { t } = useTranslation();
  return (
    <div className="state state-loading" role="status" aria-live="polite">
      <span className="spinner" aria-hidden="true" />
      <span>{label ?? t('common.loading')}</span>
    </div>
  );
}
