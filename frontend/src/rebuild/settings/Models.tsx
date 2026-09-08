import { useEffect, useState, type FormEvent } from "react";
import { errorMessage } from "../api";
import type { AgentModel, Page } from "../work/api";
import type { SettingsApi } from "./api";
import { ModelForm } from "./ModelForm";

export function Models({ api, canWrite }: { api: SettingsApi; canWrite: boolean }) {
  const [page, setPage] = useState<Page<AgentModel> | null>(null);
  const [search, setSearch] = useState(""); const [query, setQuery] = useState("");
  const [offset, setOffset] = useState(0); const [revision, setRevision] = useState(0);
  const [adding, setAdding] = useState(false); const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  useEffect(() => {
    let current = true; setPage(null); setError("");
    api.models(offset, query).then(result => { if (current) setPage(result); })
      .catch(error => { if (current) setError(errorMessage(error)); });
    return () => { current = false; };
  }, [api, query, offset, revision]);
  function filter(event: FormEvent) { event.preventDefault(); setOffset(0); setQuery(search.trim()); }
  return <section aria-label="Models"><header className="page-header"><div><h2>Models</h2>
    <p>Configure a model here, then assign it to an agent in Agents.</p></div>
    {canWrite && !adding && <button onClick={() => setAdding(true)}>Add model</button>}</header>
    {notice && <p role="status" className="notice">{notice}</p>}
    {adding ? <ModelForm api={api} onCancel={() => setAdding(false)} onSaved={() => {
      setAdding(false); setNotice("Model saved. Assign it to an agent in Agents."); setRevision(x => x + 1);
    }} /> : <div className="panel">
      <form onSubmit={filter}><label>Search models<input type="search" value={search} maxLength={160} onChange={event => setSearch(event.target.value)} /></label><button>Search models</button></form>
      {error && <p role="alert">{error} <button onClick={() => setRevision(x => x + 1)}>Retry models</button></p>}
      {!page && !error && <p role="status">Loading models…</p>}
      {page && <>{!page.total ? <p>No models found.</p> : <ul className="resource-list">{page.items.map(model => <li key={model.id}>
        <strong>{model.provider} / {model.model}</strong><p>{model.readiness_label}</p>
      </li>)}</ul>}<div className="pagination"><span>{page.total} models</span>
        <button disabled={!offset} onClick={() => setOffset(x => Math.max(0, x - 20))}>Previous models</button>
        <button disabled={!page.has_next} onClick={() => setOffset(x => x + 20)}>Next models</button></div></>}
    </div>}
  </section>;
}
