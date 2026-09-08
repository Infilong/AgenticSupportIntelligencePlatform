import { useEffect, useState } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { api, type Workspace, type User } from '../api/client';
import { Login } from '../features/auth/Login';
import { useSession } from '../features/auth/useSession';
import { Shell } from './Shell';

export function App() {
  const auth = useSession();
  if (auth.loading) return <div className="center-page" role="status">Opening your workspace…</div>;
  if (auth.error) return <div className="center-page"><p role="alert">{auth.error}</p><button onClick={auth.refresh}>Try again</button></div>;
  if (!auth.session?.user) return <Login onLogin={auth.login} />;
  return <WorkspaceRoutes key={auth.session.user.id} user={auth.session.user} logout={auth.logout} />;
}

function WorkspaceRoutes({ user, logout }: { user: User; logout: () => Promise<void> }) {
  const [workspaces, setWorkspaces] = useState<Workspace[] | null>(null);
  const [error, setError] = useState('');
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setError(''); setWorkspaces(null);
    api<Workspace[]>('/workspaces', { signal: controller.signal }).then(setWorkspaces).catch(err => {
      if (!controller.signal.aborted) setError(err.message);
    });
    return () => controller.abort();
  }, [retry]);
  if (error) return <div className="center-page"><p role="alert">{error}</p><button onClick={() => setRetry(x => x + 1)}>Try again</button></div>;
  if (!workspaces) return <div className="center-page" role="status">Loading workspaces…</div>;
  if (!workspaces.length) return <div className="center-page"><h1>No workspace access</h1><p>Ask an administrator to add you to a workspace.</p><button onClick={logout}>Sign out</button></div>;
  const saved = localStorage.getItem(`aster.workspace.${user.id}`);
  const home = workspaces.find(w => w.id === saved) ?? workspaces[0];
  return <Routes>
    <Route path="/w/:workspaceId/*" element={<Shell user={user} workspaces={workspaces} logout={logout} refreshWorkspaces={() => setRetry(x => x + 1)} />} />
    <Route path="*" element={<Navigate to={`/w/${home.id}`} replace />} />
  </Routes>;
}
