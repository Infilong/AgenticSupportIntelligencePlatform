import { BarChart3, BookOpen, Inbox, LogOut, Settings as SettingsIcon, ShieldCheck } from 'lucide-react';
import { useEffect, useState } from 'react';
import { NavLink, Route, Routes, useLocation, useNavigate, useParams } from 'react-router-dom';
import { api, type User, type Workspace } from '../api/client';
import { Settings } from '../features/settings/Settings';
import { Quality } from '../features/quality/Quality';
import { Members } from '../features/settings/Members';
import { Knowledge } from '../features/knowledge/Knowledge';
import { DocumentView } from '../features/knowledge/DocumentView';
import { SearchKnowledge } from '../features/knowledge/SearchKnowledge';
import { Workbench } from '../features/workbench/Workbench';

export function Shell({ user, workspaces, logout, refreshWorkspaces }: { user: User; workspaces: Workspace[]; logout: () => Promise<void>; refreshWorkspaces: () => void }) {
  const { workspaceId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [error, setError] = useState('');
  const [actionError, setActionError] = useState('');
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    const controller = new AbortController(); setError(''); setWorkspace(null);
    api<Workspace>(`/workspaces/${workspaceId}`, { signal: controller.signal }).then(value => {
      setWorkspace(value); localStorage.setItem(`aster.workspace.${user.id}`, value.id);
    }).catch(err => { if (!controller.signal.aborted) setError(err.message); });
    return () => controller.abort();
  }, [workspaceId, user.id, revision]);
  async function signOut() { try { await logout(); } catch (err) { setActionError((err as Error).message); } }
  if (error) return <main className="center-page"><ShieldCheck size={36} /><h1>Workspace unavailable</h1>
    <p role="alert">{error}</p><button onClick={() => { navigate('/'); refreshWorkspaces(); }}>Back to my workspace</button>
    <button onClick={signOut}>Sign out</button>{actionError && <p role="alert">{actionError}</p>}</main>;
  if (!workspace || workspace.id !== workspaceId) return <div className="center-page" role="status">Opening workspace…</div>;
  const base = `/w/${workspace.id}`;
  return <div className="app-shell">
    <a className="skip-link" href="#main-content">Skip to content</a>
    <aside className="sidebar">
      <div className="brand"><span className="brand-symbol">a</span><strong>aster</strong></div>
      <p className="sidebar-label">WORKSPACE</p>
      <nav aria-label="Main navigation"><NavLink to={base} end><Inbox size={19} />Workbench</NavLink>
        <NavLink to={`${base}/knowledge`}><BookOpen size={19} />Knowledge</NavLink>
        <NavLink to={`${base}/quality`}><BarChart3 size={19} />Quality</NavLink>{workspace.role === 'admin' && <NavLink to={`${base}/settings`}><SettingsIcon size={19} />Settings</NavLink>}</nav>
      <div className="sidebar-bottom"><span className="mode-badge">Simulated responses · Development</span>
        <div className="identity"><span className="avatar">{user.display_name.slice(0, 1)}</span><div><strong>{user.display_name}</strong><span>{user.email}</span></div></div>
        <button className="quiet" onClick={signOut}><LogOut size={17} />Sign out</button></div>
    </aside>
    <div className="workspace-main">
      <header className="topbar"><label className="sr-only" htmlFor="workspace">Workspace</label>
        <select id="workspace" value={workspace.id} onChange={e => navigate(`/w/${e.target.value}`)}>
          {workspaces.map(w => <option key={w.id} value={w.id}>{w.name}</option>)}</select>
        <span className="role-badge">{workspace.role}</span></header>
      <main id="main-content" className="page-content">
        {actionError && <p role="alert" className="error">{actionError}</p>}
        <Routes><Route index element={<Workbench key={workspace.id} workspace={workspace} />} />
          <Route path="messages/:messageId" element={<Workbench key={workspace.id} workspace={workspace} />} />
          <Route path="runs/:runId" element={<Workbench key={workspace.id} workspace={workspace} />} />
          <Route path="knowledge" element={<Knowledge key={workspace.id} workspace={workspace} />} />
          <Route path="knowledge/search" element={<SearchKnowledge key={workspace.id} workspace={workspace} />} />
          <Route path="knowledge/:documentId" element={<DocumentView key={`${workspace.id}/${location.pathname}${location.search}`} workspace={workspace} />} />
          <Route path="settings" element={<Settings key={workspace.id} workspace={workspace} onChange={() => setRevision(x => x + 1)} />} />
          <Route path="quality" element={<Quality key={workspace.id} workspace={workspace} />} />
          <Route path="members" element={<Members workspace={workspace} onChange={() => setRevision(x => x + 1)} />} />
          <Route path="*" element={<div className="empty-state"><h1>Page not found</h1><NavLink to={base}>Back to workbench</NavLink></div>} />
        </Routes>
      </main>
    </div>
  </div>;
}
