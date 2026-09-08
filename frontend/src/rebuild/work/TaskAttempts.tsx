import { useEffect, useRef, useState, type FormEvent } from "react";
import { errorMessage } from "../api";
import { runStatus, type Page, type Run, type TaskRun, type WorkApi } from "./api";

export function TaskAttempts({ api, run, current, canRun, onSelect, revision }: {
  api: WorkApi; run: Run; canRun: boolean; onSelect: (id: string) => void; revision: number;
  current: TaskRun | null;
}) {
  const [page, setPage] = useState<Page<TaskRun> | null>(null);
  const [offset, setOffset] = useState(0); const [reload, setReload] = useState(0);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState<TaskRun | null>(null);
  const [detailError, setDetailError] = useState("");
  useEffect(() => {
    let active = true; setSelected(null); setDetailError("");
    if (!current) api.taskRun(run.id).then(result => { if (active) setSelected(result); })
      .catch(error => { if (active) setDetailError(errorMessage(error)); });
    return () => { active = false; };
  }, [api, run.id, current, revision, reload]);
  const attempt = current ?? (selected?.run.id === run.id ? selected : null);
  useEffect(() => {
    let current = true; setError("");
    api.attempts(run.id, offset).then(result => { if (current) setPage(result); })
      .catch(error => { if (current) setError(errorMessage(error)); });
    return () => { current = false; };
  }, [api, run.id, run.status, offset, revision, reload]);
  return <section aria-label="Task attempts">
    {detailError && <p role="alert">Attempt details: {detailError} <button onClick={() => setReload(value => value + 1)}>Retry attempt details</button></p>}
    {attempt?.parent_run_id && <p>New attempt of <button className="text-button" onClick={() => onSelect(attempt.parent_run_id!)}>Open parent attempt</button></p>}
    {attempt?.clarification_reply && <section aria-label="Clarification reply"><h3>Clarification reply</h3><p className="answer-text">{attempt.clarification_reply}</p></section>}
    {attempt?.corrected_instructions && <details><summary>Instructions for this attempt</summary><p className="answer-text">{attempt.corrected_instructions}</p></details>}
    <details><summary>Task history ({page?.total ?? "…"} {page?.total === 1 ? "attempt" : "attempts"})</summary>
      {error && <p role="alert">{error} <button onClick={() => setReload(value => value + 1)}>Refresh attempts</button></p>}
      {!page && !error && <p role="status">Loading task history…</p>}
      {page && <><ul>{page.items.map(item => <li key={item.run.id}>
        <button disabled={item.run.id === run.id} onClick={() => onSelect(item.run.id)}>
          {item.parent_run_id ? "Follow-up" : "Original"} · {runStatus(item.run.status, item.run.route_decision)} · {new Date(item.run.created_at).toLocaleString()}
        </button>{item.run.id === run.id && " — viewing"}
      </li>)}</ul><div className="pagination"><button disabled={!offset} onClick={() => setOffset(value => Math.max(0, value - 20))}>Previous attempts</button>
        <button disabled={!page.has_next} onClick={() => setOffset(value => value + 20)}>Next attempts</button></div></>}
    </details>
    {canRun && ["completed", "rejected", "failed", "stopped"].includes(run.status) && <NewAttempt api={api} runId={run.id} onStarted={onSelect} />}
  </section>;
}

function NewAttempt({ api, runId, onStarted }: { api: WorkApi; runId: string; onStarted: (id: string) => void }) {
  const [instructions, setInstructions] = useState("");
  const [busy, setBusy] = useState(false); const [error, setError] = useState("");
  const submission = useRef<{ instructions: string; key: string } | null>(null);
  async function submit(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError("");
    const correction = instructions.trim();
    if (submission.current?.instructions !== correction)
      submission.current = { instructions: correction, key: crypto.randomUUID() };
    try { const result = await api.retry(runId, correction, submission.current.key); onStarted(result.run.id); }
    catch (error) { setError(errorMessage(error)); } finally { setBusy(false); }
  }
  return <details><summary>New attempt</summary><form onSubmit={submit} aria-label="New attempt">
    <p>Run this request again using current agent settings and your correction. The previous record stays available. New model calls may incur charges.</p>
    <label>Corrected instructions<textarea required maxLength={2000} rows={3} value={instructions} disabled={busy}
      onChange={event => setInstructions(event.target.value)} /></label>
    {error && <p role="alert">{error} Retry the unchanged correction here to avoid duplicate requests.</p>}
    <button className="primary" disabled={busy || !instructions.trim()}>{busy ? "Starting…" : "Start new attempt"}</button>
  </form></details>;
}
