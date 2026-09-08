import { useState, type FormEvent } from "react";
import { errorMessage, type Workspace, type Membership } from "../api";
import type { SettingsApi } from "./api";
import { Models } from "./Models";
import { Members } from "./Members";

export function Settings({ api, workspace, membership, onUpdated }: {
  api: SettingsApi; workspace: Workspace; membership: Membership; onUpdated: (workspace: Workspace) => void;
}) {
  const [name, setName] = useState(workspace.name); const [busy, setBusy] = useState(false);
  const [error, setError] = useState(""); const [notice, setNotice] = useState("");
  const can = (permission: string) => membership.permissions.includes(permission);
  const canEdit = !workspace.archived_at && can("workspace:manage");
  async function save(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError(""); setNotice("");
    try { onUpdated(await api.rename(name.trim())); setNotice("Workspace name saved."); }
    catch (error) { setError(errorMessage(error)); } finally { setBusy(false); }
  }
  return <><header className="page-header"><div><h1>Settings</h1><p>Workspace and model configuration.</p></div></header>
    <section className="panel"><h2>Workspace</h2><p>Your role: {membership.role}</p>
      {workspace.archived_at && <p>This workspace is archived and read-only.</p>}
      {canEdit ? <form onSubmit={save}><label>Workspace name<input value={name} maxLength={160} required disabled={busy} onChange={event => setName(event.target.value)} /></label>
        <button disabled={busy || !name.trim()}>{busy ? "Saving…" : "Save workspace"}</button></form> : <p>{workspace.name}</p>}
      {notice && <p role="status" className="notice">{notice}</p>}{error && <p role="alert" className="error">{error}</p>}
    </section>
    {can("models:read") && <Models api={api} canWrite={!workspace.archived_at && can("models:write")} />}
    {can("members:read") && <Members api={api} membership={membership} canWrite={!workspace.archived_at && can("members:manage")} />}
  </>;
}
