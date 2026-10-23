import { useTranslation } from 'react-i18next';

export function EmptyState({ message }: { message?: string }) {
  const { t } = useTranslation();
  return <div className="state state-empty">{message ?? t('common.empty')}</div>;
}
