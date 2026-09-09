import { useEffect, useRef, useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { api, type Workspace } from '../../api/client';
import { type Created, type Run } from './types';
import { AttemptHistory } from './RunHistory';

export function AttemptControls({ run, workspace, onCreated, showHistory = true, search = '' }: { showHistory?: boolean; search?: string; run: Run; workspace: Workspace; onCreated: (id: string) => void }) {
  const [details, setDetails] = useState('');
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const submission = useRef({ payload: '', key: '' });
  const controller = useRef<AbortController | null>(null);
  useEffect(() => () => controller.current?.abort(), []);
  const latest = run.latest_run_id === run.id;
  const running = ['queued', 'running'].includes(run.state);
  const canAct = !run.input_frozen && latest && !running && workspace.role !== 'viewer' && run.attempt_number < 10;
  const canRetry = ['failed', 'cancelled', 'rejected'].includes(run.state) || run.outcome === 'insufficient_evidence';
  const remaining = Math.max(0, 1000 - Array.from(run.input_text).length - '\n\nCustomer clarification:\n'.length);
  const excess = Array.from(details).length - remaining;
  async function submit(action: 'retry' | 'clarify') {
    if (pending || (action === 'clarify' && (!details.trim() || excess > 0))) return;
    const payload = JSON.stringify({ action, ...(action === 'clarify' ? { clarification: details } : {}) });
    if (submission.current.payload !== payload) submission.current = { payload, key: crypto.randomUUID() };
    setPending(true); setError(''); controller.current = new AbortController();
    const signal = controller.current.signal;
    try {
      const value = await api<Created>(`/workspaces/${workspace.id}/runs/${run.id}/attempts`, {
        method: 'POST', headers: { 'Idempotency-Key': submission.current.key }, body: payload, signal,
      });
      if (!signal.aborted) onCreated(value.run_id);
    } catch (err) { if (!signal.aborted) setError((err as Error).message); }
    finally { if (!signal.aborted) setPending(false); }
  }
  function clarify(event: FormEvent) { event.preventDefault(); void submit('clarify'); }
  return <section className="attempt-controls" aria-label="Processing attempts">
    {run.input_frozen && <p className="muted">This comparison keeps its original question fixed. Its responses and review history remain available.</p>}
    {!latest && <p><Link to={`/w/${workspace.id}/runs/${run.latest_run_id}${search}`}>Open latest attempt</Link></p>}
    {showHistory && run.attempts.length > 1 && <AttemptHistory run={run} workspaceId={workspace.id} search={search} />}
    {canAct && <>{canRetry && <button className="primary" disabled={pending} onClick={() => void submit('retry')}>{pending ? 'Starting…' : 'Retry processing'}</button>}
      <details className="clarification-controls"><summary>Add customer details</summary><form onSubmit={clarify}>
        <p className="muted">Starts a new attempt with fresh evidence. The original message and previous results stay in history. An unreviewed waiting draft will be cancelled.</p>
        <label htmlFor="customer-details">Additional customer details</label><textarea id="customer-details" rows={4} maxLength={2000} aria-invalid={excess > 0} aria-describedby="details-limit" value={details} disabled={pending || !remaining} onChange={e => setDetails(e.target.value)} required />
        <p id="details-limit" className={excess > 0 ? 'error' : 'muted'}>{excess > 0 ? `${excess} characters over the limit. Shorten the added details.` : `${-excess} characters available within the combined 1,000-character input limit.`}</p>
        <button className="primary" disabled={pending || !details.trim() || excess > 0}>{pending ? 'Starting…' : 'Process with added details'}</button>
      </form></details></>}
    {latest && run.attempt_number >= 10 && <p className="muted">This message has reached its ten-attempt limit.</p>}
    {error && <p className="error" role="alert">{error}</p>}
  </section>;
}
