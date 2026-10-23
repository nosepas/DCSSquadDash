import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../features/auth/AuthContext';

export function UserMenu() {
  const { t } = useTranslation();
  const { status, user, logout } = useAuth();
  const navigate = useNavigate();
  if (status === 'loading') return null;
  if (!user) {
    return (
      <Link to="/login" className="btn btn-primary">
        {t('header.login')}
      </Link>
    );
  }
  return (
    <div className="user-menu" role="group" aria-label={t('header.userMenu')}>
      <Link to="/profile" className="user-name">
        <span className="mono">{user.name}</span>
        <span className="role-tag">{t(`auth.role.${user.role}`)}</span>
      </Link>
      <button
        type="button"
        className="btn"
        onClick={() => {
          void logout().finally(() => navigate('/map'));
        }}
      >
        {t('header.logout')}
      </button>
    </div>
  );
}
