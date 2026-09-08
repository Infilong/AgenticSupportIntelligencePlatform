import { ShieldCheck } from 'lucide-react';
import { useEffect, useState } from 'react';
import { api, type Member, type Role, type Workspace } from '../../api/client';

export function Members({ workspace, onChange }: { workspace: Workspace; onChange: () => void }) {
  const [members, setMembers] = useState<Member[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [pending, setPending] = useState('');
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    if (workspace.role !== 'admin') { setLoading(false); return; }
    const controller = new AbortController(); setLoading(true); setMembers([]); setError('');
    api<Member[]>(`/workspaces/${workspace.id}/members`, { signal: controller.signal }).then(setMembers)
      .catch(err => { if (!controller.signal.aborted) setError(err.message); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [workspace.id, workspace.role, revision]);
  async function update(member: Member, role: Role) {
    setPending(member.id); setError('');
    try { await api(`/workspaces/${workspace.id}/members/${member.id}`, { method: 'PATCH', body: JSON.stringify({ role }) });
      setRevision(x => x + 1); onChange(); }
    catch (err) { setError((err as Error).message); }
    finally { setPending(''); }
  }
  if (workspace.role !== 'admin') return <section className="empty-state"><ShieldCheck size={32} /><h1>Administrator access required</h1><p>Your role does not allow member management.</p></section>;
  return <><div className="page-heading"><p className="eyebrow">WORKSPACE SETTINGS</p><h1>Members</h1><p className="muted">Give each person the access they need.</p></div>
    {error && <div className="error"><p role="alert">{error}</p><button onClick={() => setRevision(x => x + 1)}>Try again</button></div>}
    <section className="inbox-panel"><div className="panel-heading"><h2>People with access</h2><span className="count">{members.length}</span></div>
      {loading ? <p className="section-padding" role="status">Loading members…</p> : <div className="member-list">
        {members.map(member => <div className="member-row" key={member.id}><div className="member-person"><span className="avatar">{member.display_name.slice(0, 1)}</span>
          <div><strong>{member.display_name}</strong><span>{member.email}</span></div></div>
          <label className="sr-only" htmlFor={`role-${member.id}`}>Role for {member.display_name}</label>
          <select id={`role-${member.id}`} value={member.role} disabled={Boolean(pending)} onChange={e => update(member, e.target.value as Role)}>
            <option value="viewer">Viewer</option><option value="operator">Operator</option><option value="admin">Admin</option></select></div>)}
      </div>}
    </section><p className="access-note">Viewers inspect. Operators handle requests. Admins manage knowledge and workspace access.</p></>;
}
