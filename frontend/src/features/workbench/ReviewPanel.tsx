import { useEffect, useRef, useState, type FormEvent } from 'react';
import { api, type Workspace } from '../../api/client';
import type { Run } from './types';

export function ReviewPanel({ run, workspace, path, onSubmitted }: { run: Run; workspace: Workspace; path: string; onSubmitted: () => void }) {
  const [action, setAction] = useState('approve');
  const [reason, setReason] = useState('');
  const [response, setResponse] = useState(run.draft ?? '');
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const alive = useRef(true);
  useEffect(() => { alive.current = true; return () => { alive.current = false; }; }, []);
  const adminRequired = ['policy_exception', 'unclassified'].includes(run.review_kind);
  const mayApprove = workspace.role === 'admin' || !adminRequired;
  const selected = mayApprove ? action : 'reject';
  async function submit(event: FormEvent) {
    event.preventDefault(); if (pending || !reason.trim()) return;
    setPending(true); setError('');
    try {
      await api(`${path}/review`, { method: 'POST', body: JSON.stringify({ action: selected, reason,
        expected_revision: run.review_version, draft_hash: run.draft_hash,
        ...(selected === 'edit' ? { response } : {}) }) });
      if (alive.current) onSubmitted();
    } catch (err) { if (alive.current) setError((err as Error).message); }
    finally { if (alive.current) setPending(false); }
  }
  if (run.review) return <details className="review-history"><summary>Review decision · {run.review.action}</summary>
    <p className="response-text">{run.review.reason}</p><p className="metadata">Reviewed by {run.review.actor_id} · {new Date(run.review.created_at).toLocaleString()}</p>
    <p className="muted">The recorded decision is preserved even if subsequent processing is cancelled or fails.</p>
  </details>;
  if (run.state !== 'awaiting_review') return null;
  if (workspace.role === 'viewer') return <p className="muted">An operator or administrator must review this draft before it becomes an approved response.</p>;
  return <section className="review-panel"><h2>Review response</h2>
    {adminRequired && <p className="muted">{run.review_kind === 'unclassified' ? 'This earlier draft has no review classification.' : 'This draft requests a policy exception.'} Administrator approval is required. Operators can reject it.</p>}
    <form onSubmit={submit}>
      <label htmlFor="review-action">Decision</label><select id="review-action" value={selected} onChange={e => setAction(e.target.value)} disabled={pending}>
        {mayApprove && <><option value="approve">Approve draft</option><option value="edit">Edit and approve</option></>}<option value="reject">Reject response</option>
      </select>
      {selected === 'edit' && <><label htmlFor="review-response">Approved wording</label><textarea id="review-response" rows={6} value={response} maxLength={8000} required disabled={pending} onChange={e => setResponse(e.target.value)} /></>}
      <label htmlFor="review-reason">Reason for your decision</label><textarea id="review-reason" rows={3} value={reason} maxLength={1000} required disabled={pending} onChange={e => setReason(e.target.value)} />
      {error && <p className="error" role="alert">{error}</p>}
      <p className="muted">Check the supporting sources. Approval records a response here; it does not send it to a customer.</p>
      <button className="primary" disabled={pending || !reason.trim() || (selected === 'edit' && !response.trim())}>{pending ? 'Recording decision…' : selected === 'reject' ? 'Reject response' : 'Approve response'}</button>
    </form>
  </section>;
}
