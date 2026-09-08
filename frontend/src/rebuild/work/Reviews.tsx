import { useEffect, useState, type FormEvent } from "react";
import { errorMessage } from "../api";
import type { Page, Review, WorkApi } from "./api";
import { TaskActions } from "./TaskActions";

export function Reviews({ api, revision, onResolved, onInspect, canResolve }: {
  api: WorkApi; revision: number; onResolved: (run: string) => void; onInspect: (run: string) => void; canResolve: boolean;
}) {
  const [page, setPage] = useState<Page<Review> | null>(null);
  const [offset, setOffset] = useState(0);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState<Review | null>(null);
  useEffect(() => {
    let current = true; setError(""); setSelected(null);
    api.reviews(offset).then(result => { if (current) setPage(result); })
      .catch(error => { if (current) setError(errorMessage(error)); });
    return () => { current = false; };
  }, [api, offset, revision]);
  if (!error && page?.total === 0) return null;
  return <section className="panel" aria-label="Needs your attention"><h2>Needs your attention</h2>
    {error && <p role="alert" className="error">{error}</p>}
    {!page && !error && <p role="status">Checking pending reviews…</p>}
    {page && <><ul className="resource-list">{page.items.map(review => <li key={review.id}>
      <strong>{review.run?.input_message ?? "Support request"}</strong><p className="muted">{review.reason.includes("task_action_approval") ? "Task changes need your approval." : review.reason.replaceAll("_", " ")}</p>
      {review.reviewer_display_name && <p>Assigned to {review.reviewer_display_name}</p>}
      <div className="actions"><button onClick={() => onInspect(review.graph_run_id)}>Inspect evidence</button>
        {canResolve && <button onClick={() => setSelected(review)}>{review.reason.includes("task_action_approval") ? "Review request" : "Review answer"}</button>}</div>
    </li>)}</ul><footer className="pagination"><span>{page.total} pending</span>
      <button disabled={!offset} onClick={() => setOffset(x => Math.max(0, x - 10))}>Previous reviews</button>
      <button disabled={!page.has_next} onClick={() => setOffset(x => x + 10)}>Next reviews</button></footer></>}
    {selected && <ReviewForm key={selected.id} review={selected} api={api} onCancel={() => setSelected(null)}
      onResolved={() => { setSelected(null); setOffset(0); onResolved(selected.graph_run_id); }} />}
  </section>;
}

export function ReviewForm({ review, api, onResolved, onCancel }: {
  review: Review; api: WorkApi; onResolved: () => void; onCancel: () => void;
}) {
  const [decision, setDecision] = useState(review.proposed_answer ? "approved" : "edited");
  const [pendingActions, setPendingActions] = useState(true);
  const [answer, setAnswer] = useState(review.proposed_answer ?? "");
  const [comments, setComments] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function submit(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError("");
    try { await api.resolve(review.id, decision, answer.trim(), comments.trim()); onResolved(); }
    catch (error) { setError(errorMessage(error)); } finally { setBusy(false); }
  }
  return <form onSubmit={submit} aria-label="Review decision"><h3>Review answer</h3>
    <TaskActions api={api} runId={review.graph_run_id} canResolve onPendingChange={setPendingActions} />
    {pendingActions && <p>Resolve the actions before publishing an answer, or reject this request to discard pending actions.</p>}
    {review.proposed_answer && <p className="answer-text">{review.proposed_answer}</p>}
    <fieldset disabled={busy}><label>Decision<select value={decision} onChange={event => setDecision(event.target.value)}>
      {review.proposed_answer && <option value="approved">Approve proposed answer</option>}
      <option value="edited">Publish a human answer</option><option value="rejected">Reject without publishing</option>
    </select></label>
      {decision === "edited" && <label>Human answer<textarea required maxLength={4000} value={answer} onChange={event => setAnswer(event.target.value)} /></label>}
      <label>Review note<textarea maxLength={2000} value={comments} onChange={event => setComments(event.target.value)} /></label>
    </fieldset>
    {error && <p role="alert" className="error">{error}</p>}
    <div className="actions"><button className="primary" disabled={busy || (pendingActions && decision !== "rejected") || (decision === "edited" && !answer.trim())}>
      {busy ? "Saving decision…" : "Save decision"}</button><button type="button" disabled={busy} onClick={onCancel}>Cancel review</button></div>
  </form>;
}
