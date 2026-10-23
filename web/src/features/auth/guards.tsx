import { useEffect, type ReactNode } from 'react';
import { Navigate, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { ErrorState } from '../../components/states/ErrorState';
import { Loading } from '../../components/states/Loading';
import { ApiError } from '../../api/client';
import { safeNext } from '../../lib/safeNext';
import { readStored, writeStored } from '../../lib/storage';
import { useAuth } from './AuthContext';

const NEXT_KEY = 'fox3.next';

/** Remember where the visitor was heading, so we can return there after the external login redirect. */
export function rememberNext(path: string): void {
  writeStored(NEXT_KEY, safeNext(path), 'session');
}

/** After the backend redirects to "/", jump to the remembered page once logged in. */
export function usePostLoginRedirect(): void {
  const { status } = useAuth();
  const navigate = useNavigate();
  useEffect(() => {
    if (status !== 'authed') return;
    const next = readStored(NEXT_KEY, 'session');
    if (!next) return;
    writeStored(NEXT_KEY, null, 'session');
    const dest = safeNext(next);
    if (dest !== '/') navigate(dest, { replace: true });
  }, [status, navigate]);
}

export function RequireAuth({ children }: { children?: ReactNode }) {
  const { status } = useAuth();
  const location = useLocation();
  if (status === 'loading') return <Loading />;
  if (status === 'anon') {
    const next = safeNext(location.pathname + location.search);
    return <Navigate to={`/login?next=${encodeURIComponent(next)}`} replace />;
  }
  return children ?? <Outlet />;
}

export function RequireAdmin({ children }: { children?: ReactNode }) {
  const { isAdmin } = useAuth();
  if (!isAdmin) return <ErrorState error={new ApiError(403, 'forbidden', 'forbidden')} />;
  return children ?? <Outlet />;
}
