import { useTranslation } from 'react-i18next';
import { errorKey } from '../../lib/errors';

interface Props {
  error: unknown;
  onRetry?: () => void;
}

export function ErrorState({ error, onRetry }: Props) {
  const { t } = useTranslation();
  return (
    <div className="state state-error" role="alert">
      <p>{t(`errors.${errorKey(error)}`)}</p>
      {onRetry && (
        <button type="button" className="btn" onClick={onRetry}>
          {t('common.retry')}
        </button>
      )}
    </div>
  );
}
