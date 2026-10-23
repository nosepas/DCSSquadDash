import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { fetchMe, logout as apiLogout } from '../../api/auth';
import { setCsrfToken, setUnauthorizedHandler } from '../../api/client';
import type { Me } from '../../api/types';

export type AuthStatus = 'loading' | 'anon' | 'authed';

interface AuthValue {
  status: AuthStatus;
  user: Me | null;
  isAdmin: boolean;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Me | null>(null);
  const [status, setStatus] = useState<AuthStatus>('loading');

  const clear = useCallback(() => {
    setCsrfToken(null);
    setUser(null);
    setStatus('anon');
  }, []);

  useEffect(() => {
    const ctrl = new AbortController();
    setUnauthorizedHandler(clear);
    fetchMe(ctrl.signal)
      .then((me) => {
        setCsrfToken(me.csrf_token);
        setUser(me);
        setStatus('authed');
      })
      .catch(() => {
        if (!ctrl.signal.aborted) clear();
      });
    return () => {
      ctrl.abort();
      setUnauthorizedHandler(null);
    };
  }, [clear]);

  const logout = useCallback(async () => {
    try {
      await apiLogout();
    } finally {
      clear();
    }
  }, [clear]);

  const value = useMemo(() => ({ status, user, isAdmin: user?.role === 'admin', logout }), [status, user, logout]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
