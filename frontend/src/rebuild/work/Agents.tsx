import { useEffect, useState, type FormEvent } from "react";
import { errorMessage } from "../api";
import type { Agent, Page, WorkApi } from "./api";
import { AgentEditor } from "./AgentEditor";

export function Agents({ api, canConfigure }: { api: WorkApi; canConfigure: boolean }) {
  const [page, setPage] = useState<Page<Agent> | null>(null);
  const [offset, setOffset] = useState(0);
  const [search, setSearch] = useState("");
  const [revision, setRevision] = useState(0);
  const [adding, setAdding] = useState(false);
  const [editing, setEditing] = useState<Agent | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  useEffect(() => {
    let current = true; setPage(null); setError("");
    api.agents(offset, search).then(result => { if (current) setPage(result); })
      .catch(error => { if (current) setError(errorMessage(error)); });
    return () => { current = false; };
  }, [api, offset, search, revision]);
  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const data = new FormData(event.currentTarget); setBusy(true); setError("");
    try {
      await api.createAgent(String(data.get("name")).trim(), Number(data.get("budget")));
      setAdding(false); setNotice("Agent created. Open Work to ask a question."); setRevision(value => value + 1);
    } catch (error) { setError(errorMessage(error)); } finally { setBusy(false); }
  }
  return <><header className="page-header"><div><p className="eyebrow">Your support team</p><h1>Agents</h1>
    <p className="muted">Support agents answer using the knowledge available in this workspace.</p></div>
    {canConfigure && !adding && !editing && <button className="primary" onClick={() => setAdding(true)}>Create agent</button>}</header>
    {notice && <p role="status" className="notice">{notice}</p>}
    {editing && <AgentEditor key={editing.id} agent={editing} api={api} onCancel={() => setEditing(null)}
      onSaved={() => { setEditing(null); setNotice("Agent settings saved for new requests."); setRevision(value => value + 1); }} />}
    {error && <p role="alert" className="error">{error} <button onClick={() => setRevision(value => value + 1)}>Retry</button></p>}
    {adding && <form className="panel" onSubmit={create}><h2>Create support agent</h2>
      <label>Name<input name="name" required maxLength={160} /></label>
      <details><summary>Execution limits</summary><label>Token budget<input name="budget" type="number" min={500} max={32000} defaultValue={4000} required /></label></details>
      <p className="muted">Uses the current workspace model routing and support instructions. The execution record identifies the model actually used.</p>
      <div className="actions"><button className="primary" disabled={busy}>{busy ? "Creating…" : "Save agent"}</button>
        <button type="button" disabled={busy} onClick={() => setAdding(false)}>Cancel</button></div></form>}
    {!editing && <section className="panel"><form className="search" onSubmit={event => {
      event.preventDefault(); setSearch(String(new FormData(event.currentTarget).get("search")).trim());
      setOffset(0); setRevision(value => value + 1);
    }}><label className="grow">Search agents<input name="search" type="search" defaultValue={search} maxLength={120} /></label>
      <button>Search</button></form>
      {!page && !error ? <p role="status">Loading agents…</p> : page && <>
      {!page.items.length ? <div className="empty-state"><h2>{search ? "No matching agents" : "No agents yet"}</h2>
        <p>{search ? "Try another name or clear your search." : "An administrator can create your team's first support agent."}</p></div>
        : <ul className="resource-list">{page.items.map(agent => <li key={agent.id}><strong>{agent.name}</strong>
          <p className="muted">{agent.active && !agent.archived_at ? "Available" : "Inactive"} · {agent.token_budget} token budget</p>
          {canConfigure && <button onClick={() => { setEditing(agent); setAdding(false); }}>Edit {agent.name}</button>}</li>)}</ul>}
      <footer className="pagination"><span>{page.total} agents</span><button disabled={!offset} onClick={() => setOffset(x => Math.max(0, x - 20))}>Previous</button>
        <button disabled={!page.has_next} onClick={() => setOffset(x => x + 20)}>Next</button></footer></>}
    </section>}</>;
}
