import { useEffect, useState, type FormEvent } from "react";
import { errorMessage, type Membership } from "../api";
import type { Member, SettingsApi } from "./api";

export function Members({ api, membership, canWrite }: {
  api: SettingsApi; membership: Membership; canWrite: boolean;
}) {
  const [members, setMembers] = useState<Member[] | null>(null);
  const [offset, setOffset] = useState(0); const [search, setSearch] = useState("");
  const [query, setQuery] = useState(""); const [revision, setRevision] = useState(0);
  const [adding, setAdding] = useState(false); const [editing, setEditing] = useState<Member | null>(null);
  const [removing, setRemoving] = useState<Member | null>(null); const [role, setRole] = useState("viewer");
  const [busy, setBusy] = useState(false); const [error, setError] = useState(""); const [notice, setNotice] = useState("");
  const roles = membership.role === "owner" ? ["viewer", "operator", "admin", "owner"] : ["viewer", "operator"];
  useEffect(() => {
    let current = true; setMembers(null); setError("");
    api.members(offset, query).then(items => { if (current) setMembers(items); })
      .catch(error => { if (current) setError(errorMessage(error)); });
    return () => { current = false; };
  }, [api, offset, query, revision]);
  async function mutate(operation: () => Promise<unknown>, message: string) {
    setBusy(true); setError(""); setNotice("");
    try { await operation(); setAdding(false); setEditing(null); setRemoving(null); setNotice(message); setRevision(x => x + 1); }
    catch (error) { setError(errorMessage(error)); } finally { setBusy(false); }
  }
  function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const data = new FormData(event.currentTarget);
    void mutate(() => editing ? api.changeRole(editing.user_id, role) : api.addMember(String(data.get("email")).trim(), role), "Membership saved.");
  }
  const manage = (member: Member) => canWrite && member.user_id !== membership.user_id
    && (membership.role === "owner" || ["viewer", "operator"].includes(member.role));
  return <section aria-label="Members"><header className="page-header"><div><h2>Members</h2>
    <p>Viewer reads. Operator runs and reviews. Admin manages knowledge, agents and lower roles. Owner manages the workspace and providers.</p></div>
    {canWrite && !adding && !editing && <button onClick={() => { setAdding(true); setRole("viewer"); }}>Add member</button>}</header>
    {notice && <p role="status" className="notice">{notice}</p>}
    {error && <p role="alert" className="error">{error} <button onClick={() => setRevision(x => x + 1)}>Refresh members</button></p>}
    {(adding || editing) && <form className="panel" onSubmit={save} aria-label="Membership editor"><h3>{editing ? `Edit ${editing.email}` : "Add member"}</h3>
      <fieldset disabled={busy}>{!editing && <label>Email<input name="email" type="email" autoFocus required maxLength={320} /></label>}
        <p>The person must already have an account.</p><label>Role<select value={role} onChange={event => setRole(event.target.value)}>
          {!roles.includes(role) && <option value={role} disabled>{role} — choose a supported role</option>}
          {roles.map(value => <option key={value} value={value}>{value[0].toUpperCase() + value.slice(1)}</option>)}
        </select></label></fieldset>
      <div className="actions"><button disabled={busy || !roles.includes(role)}>{busy ? "Saving…" : "Save member"}</button>
        <button type="button" disabled={busy} onClick={() => { setAdding(false); setEditing(null); }}>Cancel</button></div></form>}
    {!adding && !editing && <div className="panel"><form onSubmit={event => { event.preventDefault(); setQuery(search.trim()); setOffset(0); }}>
      <label>Search members<input type="search" value={search} maxLength={160} onChange={event => setSearch(event.target.value)} /></label><button>Search members</button></form>
      {!members && !error && <p role="status">Loading members…</p>}
      {members && <>{!members.length ? <p>No matching members.</p> : <ul className="resource-list">{members.map(member => <li key={member.user_id}>
        <strong>{member.display_name}</strong><p>{member.email} · {member.role}{member.user_id === membership.user_id ? " · You" : ""}</p>
        {manage(member) && <div className="actions"><button disabled={busy} onClick={() => { setEditing(member); setRole(member.role); }}>Edit {member.email}</button>
          <button disabled={busy} onClick={() => setRemoving(member)}>Remove {member.email}</button></div>}
      </li>)}</ul>}<div className="pagination"><button disabled={!offset || busy} onClick={() => setOffset(x => Math.max(0, x - 20))}>Previous members</button>
        <button disabled={members.length < 20 || busy} onClick={() => setOffset(x => x + 20)}>Next members</button></div></>}
    </div>}
    {removing && <section className="panel" aria-label="Confirm member removal"><h3>Remove {removing.email}?</h3><p>This removes their access to this workspace.</p>
      <button disabled={busy} onClick={() => void mutate(() => api.removeMember(removing.user_id), "Member removed.")}>Confirm removal</button>
      <button disabled={busy} onClick={() => setRemoving(null)}>Keep member</button></section>}
  </section>;
}
