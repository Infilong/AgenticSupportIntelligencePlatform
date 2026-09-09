import { useEffect, useRef, useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { api, type Workspace } from '../../api/client';
import { outcomeLabel, stateLabel, type Created, type Run } from './types';

export function AttemptControls({ run, workspace, onCreated }: { run: Run; workspace: Workspace; onCreated: (id: string) => void }) {
  const [details, setDetails] = useState('');
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const submission = useRef({ payload: '', key: '' });
  const controller = useRef<AbortController | null>(null);
  useEffect(() => () => controller.current?.abort(), []);
  const latest = run.latest_run_id === run.id;
  const running = ['queued', 'running'].includes(run.state);
  const canAct = latest && !running && workspace.role !== 'viewer' && run.attempt_number < 10;
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
    {!latest && <p><Link to={`/w/${workspace.id}/runs/${run.latest_run_id}`}>Open latest attempt</Link></p>}
    {run.attempts.length > 1 && <details><summary>Attempt history · {run.attempts.length}</summary><ol className="attempt-history">{run.attempts.map(item => <li key={item.id}>
      <Link to={`/w/${workspace.id}/runs/${item.id}`} aria-current={item.id === run.id ? 'page' : undefined}>Attempt {item.number} · {item.kind === 'clarify' ? 'Added details' : item.kind === 'retry' ? 'Retry' : 'Original'}</Link>
      <span className="muted">{stateLabel(item.state)}{item.outcome ? ` · ${outcomeLabel(item.outcome)}` : ''}</span>
    </li>)}</ol></details>}
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
