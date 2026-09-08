import { useEffect, useState } from "react";
import { runStatus, type WorkApi } from "../work/api";
import type { RecordsApi } from "./api";
import { useRecords } from "./useRecords";
import { RecordDetail } from "./RecordDetail";
import { RecordIntake } from "./RecordIntake";
import "./records.css";

export function Records({ api, canRun, canResolve, actions }: {
  api: RecordsApi; canRun: boolean; canResolve: boolean; actions: WorkApi;
}) {
  const [search, setSearch] = useState(""); const [status, setStatus] = useState("");
  const [offset, setOffset] = useState(0); const [revision, setRevision] = useState(0);
  const readId = () => new URLSearchParams(location.hash.split("?")[1]).get("record") ?? "";
  const [selected, setSelected] = useState(readId);
  const [creating, setCreating] = useState(false);
  useEffect(() => { const update = () => setSelected(readId()); window.addEventListener("hashchange", update);
    return () => window.removeEventListener("hashchange", update); }, []);
  const { page, error } = useRecords(api, search, status, offset, revision);
  function select(id: string) { setCreating(false); location.hash = `records${id ? `?record=${encodeURIComponent(id)}` : ""}`; setSelected(id); }
  return <><header className="page-header"><div><p className="eyebrow">Data and processing</p><h1>Records</h1>
    <p className="muted">Inspect inputs, understand results, and act when needed.</p></div>
    {canRun && <button onClick={() => setCreating(true)}>New record</button>}</header>
    <div className={`records-layout ${selected || creating ? "has-selection" : ""}`}><section className="records-inbox" aria-label="Input records">
      <form onSubmit={event => { event.preventDefault(); setSearch(String(new FormData(event.currentTarget).get("search")).trim()); setOffset(0); }}>
        <label>Search records<input type="search" name="search" maxLength={200} placeholder="Find an input…" /></label>
        <label>Status<select value={status} onChange={event => { setStatus(event.target.value); setOffset(0); }}>
          <option value="">All records</option>{["queued", "running", "awaiting_clarification", "needs_human_review", "completed", "failed", "stopped"].map(value =>
            <option key={value} value={value}>{runStatus(value)}</option>)}</select></label>
        <div className="actions"><button>Search</button><button type="button" onClick={() => setRevision(x => x + 1)}>Refresh list</button></div></form>
      {error && <p role="alert" className="error">{error}</p>}
      {!page && !error && <p role="status">Loading records…</p>}
      {page?.items.map(record => <button key={record.id} className="record-row" aria-pressed={selected === record.id} onClick={() => select(record.id)}>
        <strong>{record.input_message.slice(0, 160)}</strong><span className="muted">{runStatus(record.status)} · {new Date(record.received_at).toLocaleDateString()}</span>
        {record.result_summary && <span className="record-summary">{record.result_summary}</span>}</button>)}
      {page?.total === 0 && <p>No matching records. Submit an input or change the filters.</p>}
      {page && <footer className="pagination"><span>{page.total} records</span><button disabled={!offset} onClick={() => setOffset(x => Math.max(0, x - 20))}>Previous</button>
        <button disabled={!page.has_next} onClick={() => setOffset(x => x + 20)}>Next</button></footer>}
      <p className="muted"><a href="#activity">Earlier run-only history</a></p>
    </section>{creating && canRun ? <RecordIntake api={api} actions={actions} onCancel={() => setCreating(false)}
      onCreated={id => { select(id); setOffset(0); setRevision(x => x + 1); }} /> : selected ? <RecordDetail key={selected} api={api} id={selected} canRun={canRun}
      canResolve={canResolve} actions={actions} onClose={() => select("")} />
      : <section className="record-detail empty-state"><h2>Select a record</h2><p>Its result, processing timeline and saved artifacts appear here.</p></section>}</div></>;
}
