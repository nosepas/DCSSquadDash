import { NavLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../features/auth/AuthContext';
import { useServers } from '../../features/servers/ServerContext';
import { NAV_ITEMS, visibleNav } from './navItems';

export function Nav() {
  const { t } = useTranslation();
  const { status, isAdmin } = useAuth();
  const { current } = useServers();
  const items = visibleNav(NAV_ITEMS, { authed: status === 'authed', isAdmin, missionType: current?.mission_type });
  return (
    <nav className="nav" aria-label={t('nav.main')}>
      <ul>
        {items.map((i) => (
          <li key={i.to}>
            <NavLink to={i.to} end={i.to === '/'} className={({ isActive }) => (isActive ? 'active' : '')}>
              {t(i.labelKey)}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}
