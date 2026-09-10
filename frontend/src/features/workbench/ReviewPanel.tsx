import { useEffect, useRef, useState, type FormEvent } from 'react';
import { api, type Workspace } from '../../api/client';
import type { Run } from './types';
import { ReviewHistory } from './RunHistory';

export function ReviewPanel({ run, workspace, path, onSubmitted }: { run: Run; workspace: Workspace; path: string; onSubmitted: () => void }) {
  const [action, setAction] = useState('approve');
  const [reason, setReason] = useState('');
  const [response, setResponse] = useState(run.draft ?? '');
  const [question, setQuestion] = useState('');
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const alive = useRef(true);
  useEffect(() => { alive.current = true; return () => { alive.current = false; }; }, []);
  const adminRequired = ['policy_exception', 'unclassified'].includes(run.review_kind);
  const unsupported = run.outcome === 'insufficient_evidence' || !run.citations.length;
  const mayApprove = !unsupported && (workspace.role === 'admin' || !adminRequired);
  const selected = !mayApprove && ['approve', 'edit'].includes(action) ? 'reject' : action;
  const questionInvalid = !question.trim() || Array.from(question).length > 1000;
  async function submit(event: FormEvent) {
    event.preventDefault(); if (pending || !reason.trim() || (selected === 'clarify' && questionInvalid)) return;
    setPending(true); setError('');
    try {
      await api(`${path}/review`, { method: 'POST', body: JSON.stringify({ action: selected, reason,
        expected_revision: run.review_version, draft_hash: run.draft_hash,
        ...(selected === 'edit' ? { response } : selected === 'clarify' ? { response: question } : {}) }) });
      if (alive.current) onSubmitted();
    } catch (err) { if (alive.current) setError((err as Error).message); }
    finally { if (alive.current) setPending(false); }
  }
  if (run.review) return <ReviewHistory run={run} />;
  if (run.state !== 'awaiting_review') return null;
  if (workspace.role === 'viewer') return <p className="muted">An operator or administrator must review this draft before it becomes an approved response.</p>;
  return <section className="review-panel"><h2>Review response</h2>
    {adminRequired && !unsupported && <p className="muted">This request needs an administrator decision. Operators can reject it or request clarification.</p>}
    <form onSubmit={submit}>
      <label htmlFor="review-action">Decision</label><select id="review-action" value={selected} onChange={e => setAction(e.target.value)} disabled={pending}>
        {mayApprove && <><option value="approve">Approve draft</option><option value="edit">Edit and approve</option></>}<option value="clarify">Request clarification</option><option value="reject">Reject response</option>
      </select>
      {selected === 'edit' && <><label htmlFor="review-response">Approved wording</label><textarea id="review-response" rows={6} value={response} maxLength={8000} required disabled={pending} onChange={e => setResponse(e.target.value)} /></>}
      {selected === 'clarify' && <><label htmlFor="review-question">Question for the customer</label><textarea id="review-question" rows={4} value={question} maxLength={2000} required disabled={pending} onChange={e => setQuestion(e.target.value)} /><p className="muted">Ask for the missing details in up to 1,000 characters. The draft stays unapproved. This records the question here; it does not send it.</p>{Array.from(question).length > 1000 && <p className="error">Shorten the question to 1,000 characters.</p>}</>}
      <label htmlFor="review-reason">Reason for your decision</label><textarea id="review-reason" rows={3} value={reason} maxLength={1000} required disabled={pending} onChange={e => setReason(e.target.value)} />
      {error && <p className="error" role="alert">{error}</p>}
      <p className="muted">Check the supporting sources. Approval records a response here; it does not send it to a customer.</p>
      <button className="primary" disabled={pending || !reason.trim() || (selected === 'edit' && !response.trim()) || (selected === 'clarify' && questionInvalid)}>{pending ? 'Recording decision…' : selected === 'reject' ? 'Reject response' : selected === 'clarify' ? 'Record clarification request' : 'Approve response'}</button>
    </form>
  </section>;
}
