import { Navigate, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { DISCORD_LOGIN_URL, demoLoginUrl, fetchAuthConfig } from '../../api/auth';
import { Card, PageHeader } from '../../components/Card';
import { AsyncView } from '../../components/states/AsyncView';
import { useAsync } from '../../hooks/useAsync';
import { safeNext } from '../../lib/safeNext';
import { useAuth } from './AuthContext';
import { rememberNext } from './guards';

export default function LoginPage() {
  const { t } = useTranslation();
  const { status } = useAuth();
  const [params] = useSearchParams();
  const next = safeNext(params.get('next'));
  const config = useAsync(fetchAuthConfig, []);

  if (status === 'authed') return <Navigate to={next} replace />;
  const remember = () => rememberNext(next);

  return (
    <div className="login">
      <PageHeader title={t('auth.title')} />
      <Card>
        <p>{t('auth.intro')}</p>
        {params.get('next') && <p className="notice" role="note">{t('auth.needLogin')}</p>}
        <AsyncView state={config}>
          {(cfg) => (
            <div className="login-actions">
              {cfg.discord ? (
                <a className="btn btn-primary btn-lg" href={DISCORD_LOGIN_URL} onClick={remember}>
                  {t('auth.discord')}
                </a>
              ) : (
                <p className="muted">{t('auth.discordUnavailable')}</p>
              )}
              {cfg.demo && (
                <div className="demo-box">
                  <h2 className="demo-title"><span className="tag tag-warn">DEMO</span> {t('auth.demoTitle')}</h2>
                  <p className="muted small">{t('auth.demoNote')}</p>
                  <div className="row-actions">
                    <a className="btn" href={demoLoginUrl(false)} onClick={remember}>{t('auth.demoPilot')}</a>
                    <a className="btn" href={demoLoginUrl(true)} onClick={remember}>{t('auth.demoAdmin')}</a>
                  </div>
                </div>
              )}
            </div>
          )}
        </AsyncView>
      </Card>
    </div>
  );
}
