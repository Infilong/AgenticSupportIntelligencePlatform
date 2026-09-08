import { useEffect, useRef, useState, type FormEvent } from "react";
import { errorMessage } from "../api";
import { runStatus, type Agent, type AnswerLanguage, type Page, type Run, type WorkApi } from "./api";
import { RunDetail } from "./RunDetail";
import { Reviews } from "./Reviews";

export function Work({ api, canRun, canReadReviews, canResolve, activity = false }: {
  api: WorkApi; canRun: boolean; canReadReviews: boolean; canResolve: boolean; activity?: boolean;
}) {
  const mounted = useRef(true);
  const submission = useRef<{ key: string; agent: string; message: string; language: string } | null>(null);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  const [page, setPage] = useState<Page<Run> | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [agentOffset, setAgentOffset] = useState(0);
  const [moreAgents, setMoreAgents] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState("");
  const [offset, setOffset] = useState(0);
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [revision, setRevision] = useState(0);
  const [error, setError] = useState("");
  const [agentError, setAgentError] = useState("");
  const [runError, setRunError] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [language, setLanguage] = useState<AnswerLanguage | "">("");
  const [selected, setSelected] = useState(() => new URLSearchParams(location.hash.split("?")[1]).get("run") ?? "");
  useEffect(() => {
    let current = true; setPage(null); setError("");
    api.runs(offset, search, filter).then(result => { if (current) setPage(result); })
      .catch(error => { if (current) setError(errorMessage(error)); });
    return () => { current = false; };
  }, [api, offset, search, filter, revision]);
  useEffect(() => {
    if (activity || !canRun) return;
    let current = true; setAgentError("");
    api.agents(agentOffset).then(result => {
      if (!current) return;
      const active = result.items.filter(agent => agent.active && !agent.archived_at);
      setAgents(active); setMoreAgents(result.has_next); setSelectedAgent(active[0]?.id ?? "");
    }).catch(error => { if (current) setAgentError(errorMessage(error)); });
    return () => { current = false; };
  }, [api, activity, canRun, agentOffset]);
  useEffect(() => {
    const restore = () => setSelected(new URLSearchParams(location.hash.split("?")[1]).get("run") ?? "");
    window.addEventListener("hashchange", restore);
    return () => window.removeEventListener("hashchange", restore);
  }, []);
  function selectRun(id: string) {
    location.hash = `${activity ? "activity" : "work"}${id ? `?run=${encodeURIComponent(id)}` : ""}`;
    setSelected(id);
  }
  async function submit(event: FormEvent) {
    event.preventDefault(); setBusy(true); setRunError("");
    const input = message.trim();
    if (submission.current?.agent !== selectedAgent || submission.current.message !== input || submission.current.language !== language)
      submission.current = { key: crypto.randomUUID(), agent: selectedAgent, message: input, language };
    try {
      const run = await api.run(selectedAgent, input, submission.current.key, language || null);
      if (!mounted.current) return;
      submission.current = null;
      selectRun(run.id); setMessage(""); setRevision(value => value + 1);
    } catch (error) { if (mounted.current) setRunError(`${errorMessage(error)} You can retry the unchanged request here without creating a duplicate.`); }
    finally { if (mounted.current) setBusy(false); }
  }
  return <><header className="page-header"><div><p className="eyebrow">{activity ? "Execution history" : "Your team's work"}</p>
    <h1>{activity ? "Activity" : "Work"}</h1><p className="muted">{activity ? "Understand what happened, which sources were used, and what each run cost."
      : "Ask a support question and inspect the answer with its evidence."}</p></div></header>
    {!activity && canReadReviews && <Reviews api={api} revision={revision} canResolve={canResolve} onInspect={selectRun}
      onResolved={id => { if (mounted.current) { selectRun(id); setRevision(x => x + 1); } }} />}
    {!activity && canRun && <form className="panel" onSubmit={submit}><h2>Ask your agent</h2>
      {agentError && <p role="alert" className="error">{agentError}</p>}
      <label>Agent<select value={selectedAgent} disabled={busy} onChange={event => setSelectedAgent(event.target.value)}>
        {!agents.length && <option value="">No available agents on this page</option>}
        {agents.map(agent => <option key={agent.id} value={agent.id}>{agent.name}</option>)}</select></label>
      {(agentOffset > 0 || moreAgents) && <div className="actions"><button type="button" disabled={busy || !agentOffset} onClick={() => setAgentOffset(x => Math.max(0, x - 20))}>Previous agents</button>
        <button type="button" disabled={busy || !moreAgents} onClick={() => setAgentOffset(x => x + 20)}>More agents</button></div>}
      {!agents.length && <p className="muted">Create an agent in Agents, then return here.</p>}
      <label>Your request<textarea value={message} onChange={event => setMessage(event.target.value)} rows={4} maxLength={4000} required disabled={busy}
        placeholder="What is our refund policy?" /></label>
      <label>Response language<select value={language} disabled={busy}
        onChange={event => setLanguage(event.target.value as AnswerLanguage | "")}>
        <option value="">Auto — follow the request</option><option value="en">English</option>
        <option value="ja">日本語</option><option value="zh">中文</option>
      </select></label>
      {runError && <p role="alert" className="error">{runError}</p>}
      {busy && <p role="status">Submitting your request…</p>}
      <button className="primary" disabled={busy || !selectedAgent || !message.trim()}>{busy ? "Submitting…" : "Ask agent"}</button>
    </form>}
    {selected && <RunDetail key={selected} api={api} id={selected} refreshToken={revision} canStop={canRun}
      onSelectRun={id => { selectRun(id); setRevision(value => value + 1); }}
      onSettled={() => setRevision(x => x + 1)} onClose={() => selectRun("")} />}
    <section className="panel" aria-label="Runs"><form className="search" onSubmit={event => {
      event.preventDefault(); setSearch(String(new FormData(event.currentTarget).get("search")).trim()); setOffset(0);
    }}><label className="grow">Search requests<input name="search" type="search" /></label>
      <label>Status<select value={filter} onChange={event => { setFilter(event.target.value); setOffset(0); }}>
        <option value="all">All runs</option><option value="needs_human_review">Needs review</option>
        <option value="queued">Queued</option><option value="stopping">Stopping</option><option value="stopped">Stopped</option>
        <option value="running">Running</option><option value="failed">Failed</option><option value="rejected">Rejected</option><option value="completed">Completed</option>
      </select></label><button>Search</button><button type="button" onClick={() => setRevision(x => x + 1)}>Refresh runs</button></form>
      {error && <p role="alert" className="error">{error}</p>}
      {!page && !error ? <p role="status">Loading runs…</p> : page && <>
        {!page.items.length ? <div className="empty-state"><h2>No matching runs</h2><p>Start a request or change the filters.</p></div>
          : <ul className="resource-list">{page.items.map(run => <li key={run.id}>
            <button className="text-button" onClick={() => selectRun(run.id)}>{run.input_message}</button>
            <p className="muted">{runStatus(run.status, run.route_decision)} · {new Date(run.created_at).toLocaleString()}</p></li>)}</ul>}
        <footer className="pagination"><span>{page.total} runs</span><button disabled={!offset} onClick={() => setOffset(x => Math.max(0, x - 20))}>Previous</button>
          <button disabled={!page.has_next} onClick={() => setOffset(x => x + 20)}>Next</button></footer></>}
    </section></>;
}
