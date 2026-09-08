import { useEffect, useMemo, useState, type FormEvent } from "react";
import { createApiRequest, errorMessage, workspaceApi, type Membership, type Workspace } from "./api";
import { SignIn } from "./SignIn";
import { Knowledge } from "./knowledge/Knowledge";
import { workApi } from "./work/api";
import { Work } from "./work/Work";
import { Agents } from "./work/Agents";
import { Settings } from "./settings/Settings";
import { settingsApi } from "./settings/api";
import { Records } from "./records/Records";
import { recordsApi } from "./records/api";

function useArea() {
  const read = () => location.hash.slice(1).split("?")[0] || "records";
  const [area, setArea] = useState(read);
  useEffect(() => {
    const update = () => setArea(read());
    window.addEventListener("hashchange", update);
    return () => window.removeEventListener("hashchange", update);
  }, []);
  return area;
}

export function WorkspaceApp() {
  const [token, setToken] = useState(() => localStorage.getItem("asi_token") ?? "");
  const [notice, setNotice] = useState("");
  const request = useMemo(() => createApiRequest(rejected => {
    setToken(current => current === rejected ? "" : current);
    setNotice("Your session expired. Sign in again.");
  }), []);
  useEffect(() => {
    if (token) localStorage.setItem("asi_token", token);
    else localStorage.removeItem("asi_token");
  }, [token]);
  if (!token) return <SignIn request={request} onSignIn={setToken} notice={notice} />;
  return <WorkspaceSession key={token} token={token} request={request}
    signOut={() => { setNotice(""); setToken(""); }} />;
}

function WorkspaceSession({ token, request, signOut }: {
  token: string; request: ReturnType<typeof createApiRequest>; signOut: () => void;
}) {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const area = useArea();
  const [selected, setSelected] = useState(() => new URL(window.location.href).searchParams.get("workspace") ?? "");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    if (!workspaces.some(item => item.id === selected)) return;
    const url = new URL(window.location.href);
    url.searchParams.set("workspace", selected);
    window.history.replaceState(null, "", url);
  }, [selected, workspaces]);
  useEffect(() => {
    function restoreLocation() {
      const id = new URL(window.location.href).searchParams.get("workspace");
      if (id && workspaces.some(item => item.id === id)) setSelected(id);
    }
    window.addEventListener("popstate", restoreLocation);
    return () => window.removeEventListener("popstate", restoreLocation);
  }, [workspaces]);
  function selectWorkspace(id: string) {
    const url = new URL(window.location.href);
    url.searchParams.set("workspace", id);
    window.history.pushState(null, "", url);
    setSelected(id);
  }
  useEffect(() => {
    let current = true;
    setLoading(true); setError("");
    request<Workspace[]>("/api/v1/workspaces", { token }).then(items => {
      if (!current) return;
      setWorkspaces(items);
      setSelected(previous => items.some(item => item.id === previous) ? previous : items[0]?.id ?? "");
    }).catch(error => { if (current) setError(errorMessage(error)); })
      .finally(() => { if (current) setLoading(false); });
    return () => { current = false; };
  }, [request, token, revision]);
  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setCreating(true); setError("");
    const name = String(new FormData(event.currentTarget).get("name")).trim();
    try {
      const workspace = await request<Workspace>("/api/v1/workspaces", { token, method: "POST", body: { name } });
      setWorkspaces(items => [...items, workspace]); setSelected(workspace.id);
    } catch (error) { setError(errorMessage(error)); }
    finally { setCreating(false); }
  }
  const workspace = workspaces.find(item => item.id === selected);
  return <div className="workspace-layout">
    <a className="skip-link" href="#main" onClick={event => {
      event.preventDefault(); document.getElementById("main")?.focus();
    }}>Skip to content</a>
    <aside className="sidebar"><div className="brand">Support<span>Team workspace</span></div>
      <label>Workspace<select value={selected} disabled={loading} onChange={event => selectWorkspace(event.target.value)}>
        {!workspaces.length && <option value="">No workspace</option>}
        {workspaces.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}
      </select></label>
      <nav aria-label="Main navigation">{["records", "knowledge", "settings"].map(item =>
        <a key={item} href={`#${item}`} aria-current={area === item ? "page" : undefined}>{item[0].toUpperCase() + item.slice(1)}</a>)}</nav>
      <div className="sidebar-footer"><button onClick={signOut}>Sign out</button></div>
    </aside>
    <main id="main" className="main-content" tabIndex={-1}>
      {error && <div role="alert" className="error">{error} <button onClick={() => setRevision(x => x + 1)}>Retry</button></div>}
      {loading ? <p role="status">Loading your workspace…</p> : workspace
        ? <WorkspaceContent key={workspace.id} workspace={workspace} token={token} request={request} area={area}
          onUpdated={updated => setWorkspaces(items => items.map(item => item.id === updated.id ? updated : item))} />
        : !error && <section className="empty-state"><h1>A place for your team's knowledge</h1>
          <p>Create a workspace to get started.</p><form onSubmit={create}>
            <label>Workspace name<input name="name" required maxLength={160} /></label>
            <button className="primary" disabled={creating}>{creating ? "Creating…" : "Create workspace"}</button>
          </form></section>}
    </main>
  </div>;
}

function WorkspaceContent({ workspace, token, request, area, onUpdated }: {
  workspace: Workspace; token: string; request: ReturnType<typeof createApiRequest>; area: string;
  onUpdated: (workspace: Workspace) => void;
}) {
  const api = useMemo(() => workspaceApi(request, token, workspace.id), [request, token, workspace.id]);
  const agentApi = useMemo(() => workApi(request, token, workspace.id), [request, token, workspace.id]);
  const configurationApi = useMemo(() => settingsApi(request, token, workspace.id), [request, token, workspace.id]);
  const recordApi = useMemo(() => recordsApi(request, token, workspace.id), [request, token, workspace.id]);
  const [membership, setMembership] = useState<Membership | null>(null);
  const [error, setError] = useState("");
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    let current = true;
    setError("");
    api.membership().then(result => { if (current) setMembership(result); })
      .catch(error => { if (current) setError(errorMessage(error)); });
    return () => { current = false; };
  }, [api, revision]);
  if (error) return <p role="alert">{error} <button onClick={() => setRevision(x => x + 1)}>Retry</button></p>;
  if (!membership) return <p role="status">Checking workspace access…</p>;
  const can = (permission: string) => membership.permissions.includes(permission);
  if (area === "records") return can("traces:read")
    ? <Records api={recordApi} actions={agentApi} canRun={!workspace.archived_at && can("agents:run")}
      canResolve={!workspace.archived_at && can("reviews:resolve")} />
    : <p>You don't have permission to view records.</p>;
  if (area === "settings") return can("settings:read")
    ? <><Settings api={configurationApi} workspace={workspace} membership={membership} onUpdated={onUpdated} />
      {can("agents:read") && <a href="#agents">Processing configuration</a>}</>
    : <p>You don't have permission to view settings.</p>;
  if (area === "work" || area === "activity") return can("traces:read")
    ? <Work key={area} api={agentApi} activity={area === "activity"} canRun={!workspace.archived_at && can("agents:run")}
      canReadReviews={can("reviews:read")} canResolve={!workspace.archived_at && can("reviews:resolve")} />
    : <p>You don't have permission to view execution records.</p>;
  if (area === "agents") return can("agents:read")
    ? <Agents api={agentApi} canConfigure={!workspace.archived_at && can("agents:configure")} />
    : <p>You don't have permission to view agents.</p>;
  if (!membership.permissions.includes("knowledge:read")) return <p>You don't have permission to view knowledge.</p>;
  return <Knowledge api={api} canWrite={!workspace.archived_at && membership.permissions.includes("knowledge:write")}
    canDelete={!workspace.archived_at && membership.permissions.includes("resources:delete")} />;
}
