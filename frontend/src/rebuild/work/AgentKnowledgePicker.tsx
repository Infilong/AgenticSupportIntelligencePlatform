import { useEffect, useState } from "react";
import { errorMessage, type Document } from "../api";
import type { Agent, Page, WorkApi } from "./api";

export function knowledgeScope(agent: Agent): string[] | null {
  try {
    const value = JSON.parse(agent.settings_json).knowledge_document_ids;
    if (value == null) return null;
    return Array.isArray(value) ? value.filter((id): id is string => typeof id === "string") : [];
  } catch { return []; }
}

export function AgentKnowledgePicker({ api, value, onChange }: {
  api: WorkApi; value: string[] | null; onChange: (ids: string[] | null) => void;
}) {
  const [mode, setMode] = useState(value === null ? "all" : value.length ? "selected" : "none");
  const [page, setPage] = useState<Page<Document> | null>(null);
  const [search, setSearch] = useState(""); const [query, setQuery] = useState("");
  const [offset, setOffset] = useState(0); const [revision, setRevision] = useState(0);
  const [error, setError] = useState("");
  useEffect(() => {
    if (mode !== "selected") return;
    let current = true; setPage(null); setError("");
    api.knowledge(offset, query).then(result => { if (current) setPage(result); })
      .catch(error => { if (current) setError(errorMessage(error)); });
    return () => { current = false; };
  }, [api, offset, query, revision, mode]);
  function filter() { setQuery(search.trim()); setOffset(0); }
  return <section aria-label="Agent knowledge"><h3>Knowledge access</h3>
    <label>Knowledge scope<select value={mode} onChange={event => {
      const mode = event.target.value; setMode(mode); onChange(mode === "all" ? null : []);
    }}><option value="all">All workspace knowledge</option><option value="selected">Selected documents</option>
      <option value="none">No knowledge documents</option></select></label>
    <p className="muted">Applies to new requests. Only ready documents in this workspace can be retrieved.</p>
    {mode === "selected" && <><p>{value?.length ?? 0} selected (maximum 100). An empty selection provides no evidence.</p>
      <label>Search knowledge<input type="search" value={search} maxLength={120} onChange={event => setSearch(event.target.value)}
        onKeyDown={event => { if (event.key === "Enter") { event.preventDefault(); filter(); } }} /></label>
      <button type="button" onClick={filter}>Search knowledge</button>
      {error && <p role="alert">{error} <button type="button" onClick={() => setRevision(x => x + 1)}>Retry knowledge</button></p>}
      {!page && !error && <p role="status">Loading knowledge…</p>}
      {page && <>{!page.items.length && <p>No matching documents.</p>}
        {page.items.map(doc => <label className="knowledge-choice" key={doc.id}><input type="checkbox" checked={value?.includes(doc.id) ?? false}
          disabled={!value?.includes(doc.id) && (value?.length ?? 0) >= 100}
          onChange={event => onChange(event.target.checked ? [...(value ?? []), doc.id] : (value ?? []).filter(id => id !== doc.id))} />
          {doc.title} · {doc.language} · {doc.status}</label>)}
        <div className="pagination"><button type="button" disabled={!offset} onClick={() => setOffset(x => Math.max(0, x - 20))}>Previous documents</button>
          <button type="button" disabled={!page.has_next} onClick={() => setOffset(x => x + 20)}>Next documents</button></div></>}
    </>}
  </section>;
}
