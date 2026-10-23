import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { startLink } from '../../api/players';
import type { ApiError } from '../../api/client';
import type { LinkCode } from '../../api/types';
import { Card } from '../../components/Card';
import { ErrorState } from '../../components/states/ErrorState';
import { useCountdown } from '../../hooks/useCountdown';
import { formatClock } from '../../lib/format';

function CodeBox({ link, onRegenerate, busy }: { link: LinkCode; onRegenerate: () => void; busy: boolean }) {
  const { t } = useTranslation();
  const left = useCountdown(link.expires_at);
  return (
    <div className="link-code">
      <p className="muted">{t('profile.link.code')}</p>
      <output className="code mono" aria-live="polite">{link.code}</output>
      <p className={left > 0 ? 'mono' : 'error-text'} role="timer">
        {left > 0 ? t('profile.link.expiresIn', { time: formatClock(left) }) : t('profile.link.expired')}
      </p>
      <p>{t('profile.link.instructions')}</p>
      <button type="button" className="btn" onClick={onRegenerate} disabled={busy}>
        {t('profile.link.regenerate')}
      </button>
    </div>
  );
}

/** "Link my DCS account" flow: asks the API for a one-time code the user types in the DCS chat. */
export function LinkAccount() {
  const { t } = useTranslation();
  const [link, setLink] = useState<LinkCode>();
  const [error, setError] = useState<ApiError>();
  const [busy, setBusy] = useState(false);

  const generate = () => {
    setBusy(true);
    setError(undefined);
    startLink()
      .then(setLink)
      .catch((e: ApiError) => setError(e))
      .finally(() => setBusy(false));
  };

  return (
    <Card title={t('profile.link.title')}>
      <p>{t('profile.link.intro')}</p>
      {error && <ErrorState error={error} />}
      {link ? (
        <CodeBox link={link} onRegenerate={generate} busy={busy} />
      ) : (
        <button type="button" className="btn btn-primary" onClick={generate} disabled={busy}>
          {t('profile.link.generate')}
        </button>
      )}
    </Card>
  );
}
