import { useCallback, useEffect, useState } from 'react';
import { api, ApiError, setCsrf, type Session } from '../../api/client';

export function useSession() {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const refresh = useCallback(async () => {
    setError('');
    try {
      const next = await api<Session>('/session');
      setCsrf(next.csrf_token); setSession(next);
      return next;
    } catch (err) { setError((err as Error).message); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { void refresh(); }, [refresh]);
  useEffect(() => {
    const expired = () => { setSession(null); setCsrf(''); void refresh(); };
    window.addEventListener('session-expired', expired);
    return () => window.removeEventListener('session-expired', expired);
  }, [refresh]);
  async function login(email: string, password: string) {
    try {
      const next = await api<Session>('/session/login', { method: 'POST', body: JSON.stringify({ email, password }) });
      setCsrf(next.csrf_token); setSession(next);
    } catch (err) {
      if (err instanceof ApiError && [403, 409].includes(err.status)) {
        await refresh();
        throw new Error('Your sign-in session changed. Please sign in again.');
      }
      throw err;
    }
  }
  async function logout() {
    try { await api('/session/logout', { method: 'POST' }); }
    catch (err) {
      if (err instanceof ApiError && [401, 403].includes(err.status)) {
        const current = await refresh();
        if (current && !current.user) return;
      }
      throw err;
    }
    setSession(null); setCsrf(''); await refresh();
  }
  return { session, loading, error, refresh, login, logout };
}
