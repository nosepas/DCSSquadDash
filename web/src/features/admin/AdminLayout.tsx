import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { PageHeader } from '../../components/Card';

const TABS = [
  { to: '/admin', key: 'servers' },
  { to: '/admin/agents', key: 'agents' },
  { to: '/admin/users', key: 'users' },
] as const;

export default function AdminLayout() {
  const { t } = useTranslation();
  const { pathname } = useLocation();
  /** The servers tab also covers /admin/servers/:id. */
  const isActive = (to: string) => (to === '/admin' ? pathname === '/admin' || pathname.startsWith('/admin/servers') : pathname.startsWith(to));
  return (
    <>
      <PageHeader title={t('admin.title')} />
      <nav className="tabs" aria-label={t('admin.title')}>
        {TABS.map((tab) => (
          <NavLink key={tab.key} to={tab.to} end className={isActive(tab.to) ? 'active' : ''}>
            {t(`admin.tabs.${tab.key}`)}
          </NavLink>
        ))}
      </nav>
      <Outlet />
    </>
  );
}
