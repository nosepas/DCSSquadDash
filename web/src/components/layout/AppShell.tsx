import { Outlet } from 'react-router-dom';
import { usePostLoginRedirect } from '../../features/auth/guards';
import { Header } from './Header';

export function AppShell() {
  usePostLoginRedirect();
  return (
    <>
      <Header />
      <main id="main" className="app-main" tabIndex={-1}>
        <Outlet />
      </main>
    </>
  );
}
