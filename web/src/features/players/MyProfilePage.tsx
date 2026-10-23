import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Card, PageHeader } from '../../components/Card';
import { useAuth } from '../auth/AuthContext';
import { LinkAccount } from './LinkAccount';
import { ProfileLoader } from './ProfilePage';

export default function MyProfilePage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const linked = user?.linked_ucids ?? [];
  return (
    <>
      <PageHeader title={t('profile.myTitle')} />
      <Card title={user?.name}>
        <h3 className="section-title">{t('profile.linkedAccounts')}</h3>
        {linked.length === 0 ? (
          <p className="muted">{t('profile.noLinked')}</p>
        ) : (
          <ul className="list">
            {linked.map((u) => (
              <li key={u}>
                <Link to={`/players/${u}`} className="mono">{u}</Link>
              </li>
            ))}
          </ul>
        )}
      </Card>
      {linked[0] && <ProfileLoader ucid={linked[0]} />}
      <LinkAccount />
    </>
  );
}
