import { useEffect, useState } from "react";
import { errorMessage } from "../api";
import type { AgentModel, Page, WorkApi } from "./api";

export function AgentModelPicker({ api, value, onChange }: {
  api: WorkApi; value: string; onChange: (id: string) => void;
}) {
  const [page, setPage] = useState<Page<AgentModel> | null>(null);
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [offset, setOffset] = useState(0);
  const [retry, setRetry] = useState(0);
  const [error, setError] = useState("");
  const [chosen, setChosen] = useState<AgentModel | null>(null);
  useEffect(() => {
    let current = true; setPage(null); setError("");
    api.models(offset, query).then(result => { if (current) setPage(result); })
      .catch(error => { if (current) setError(errorMessage(error)); });
    return () => { current = false; };
  }, [api, offset, query, retry]);
  const selected = page?.items.find(model => model.id === value) ?? (chosen?.id === value ? chosen : null);
  return <section aria-label="Agent model"><h3>Model</h3>
    <label>Search models<input type="search" value={search} maxLength={160} onChange={event => setSearch(event.target.value)}
      onKeyDown={event => { if (event.key === "Enter") { event.preventDefault(); setQuery(search.trim()); setOffset(0); } }} /></label>
    <button type="button" onClick={() => { setQuery(search.trim()); setOffset(0); }}>Search models</button>
    {error && <p role="alert">{error} <button type="button" onClick={() => setRetry(x => x + 1)}>Retry models</button></p>}
    {!page && !error && <p role="status">Loading models…</p>}
    <label>Assigned model<select value={value} onChange={event => {
      const id = event.target.value; setChosen(page?.items.find(model => model.id === id) ?? null); onChange(id);
    }}>
      <option value="">Workspace default routing</option>
      {value && !page?.items.some(model => model.id === value) && <option value={value}>
        {selected ? `${selected.provider} / ${selected.model}` : "Saved model assignment (unchanged)"}
      </option>}
      {page?.items.map(model => <option key={model.id} value={model.id}>{model.provider} / {model.model} · {model.purpose}</option>)}
    </select></label>
    <p className="muted">{selected?.readiness_label ?? (value ? "The saved assignment is preserved while you browse models." : "Uses workspace routing for each model call.")}</p>
    {page?.total === 0 && <p>{query ? "No matching models. Try another search." : "No workspace models configured. Default routing remains available."}</p>}
    {page && <div className="pagination"><span>{page.total} models</span>
      <button type="button" disabled={!offset} onClick={() => setOffset(x => Math.max(0, x - 20))}>Previous models</button>
      <button type="button" disabled={!page.has_next} onClick={() => setOffset(x => x + 20)}>Next models</button>
    </div>}
  </section>;
}
