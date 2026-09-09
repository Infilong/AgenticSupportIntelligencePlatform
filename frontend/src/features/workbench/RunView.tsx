import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api, type Workspace } from '../../api/client';
import { DevelopmentResponse } from './DevelopmentResponse';
import { AttemptControls } from './AttemptControls';
import { ProcessingDetails } from './ProcessingDetails';
import { ReviewPanel } from './ReviewPanel';
import { active, languageLabel, outcomeLabel, stateLabel, type Run } from './types';
import { useResource } from './useResource';

export function RunView({ workspace, runId, onChanged }: { workspace: Workspace; runId: string; onChanged: () => void }) {
  const navigate = useNavigate();
  const path = `/workspaces/${workspace.id}/runs/${runId}`;
  const resource = useResource<Run>(path, 3000);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const [citationId, setCitationId] = useState('');
  const [developmentOpen, setDevelopmentOpen] = useState(false);
  const excerpt = useRef<HTMLElement>(null);
  const citationButton = useRef<HTMLButtonElement | null>(null);
  const run = resource.data;
  useEffect(() => { if (run?.state) onChanged(); }, [run?.state, onChanged]);
  const citation = run?.citations.find(item => item.chunk_id === citationId);
  const changed = () => { resource.refresh(); onChanged(); };
  async function cancel() {
    if (pending) return; setPending(true); setError('');
    try { await api(`${path}/cancel`, { method: 'POST' }); changed(); }
    catch (err) { setError((err as Error).message); }
    finally { setPending(false); }
  }
  return <div className="run-view"><Link className="back-to-messages" to={`/w/${workspace.id}`}>← All messages</Link>
    {resource.error && <><p className="error" role="alert">{resource.error}</p><button onClick={resource.refresh}>Try again</button></>}
    {!run && !resource.error && <p role="status">Loading message…</p>}
    {run && <><div className="run-heading"><span className={`run-state ${run.state}`} role="status">{stateLabel(run.state)}</span><span className="muted">{languageLabel(run.language)}</span></div>
      <section><h2>Original message</h2><p className="original-message" lang={run.language}>{run.original}</p></section>
      {run.input_text !== run.original && <details><summary>Processing input · attempt {run.attempt_number}</summary><p className="original-message" lang={run.language}>{run.input_text}</p></details>}
      <section className="run-result"><h2>{outcomeLabel(run.outcome)}</h2>
        {run.reviewed_response ? <><p className="response-text" lang={run.language}>{run.reviewed_response}</p><details><summary>Original development draft</summary><p className="response-text" lang={run.language}>{run.draft}</p></details></> : run.draft ? <><p className="response-text" lang={run.language}>{run.draft}</p>{!!run.citations.length && <p className="muted">{run.state === 'rejected' ? 'Rejected development draft · Not approved for sending' : 'Development draft · Not approved for sending'}</p>}</> : <p className="muted">{run.state === 'waiting_for_input' ? 'Retrieval is complete. An administrator can supply a development response using the supporting evidence.' : run.state === 'cancelled' ? 'This processing attempt was cancelled. The original message and processing history are preserved.' : run.state === 'failed' ? 'Processing stopped before a response was ready. Inspect the details below, then retry or add customer details.' : 'Your message is saved. Processing will continue in the background.'}</p>}
        {run.error_code && <details><summary>Failure information</summary><p className="error">{run.error_code}</p></details>}
        {!!run.citations.length && <div className="citation-links" aria-label="Supporting sources">{run.citations.map((item, index) => <button key={item.chunk_id} aria-expanded={citationId === item.chunk_id} onClick={event => { citationButton.current = event.currentTarget; setCitationId(item.chunk_id); requestAnimationFrame(() => excerpt.current?.focus()); }}><span>{index + 1}</span>{item.section}</button>)}</div>}
      </section>
      {citation && <aside className="citation-panel" ref={excerpt} tabIndex={-1} aria-label="Source excerpt"><div className="run-heading"><h3>{citation.title}</h3><button onClick={() => { setCitationId(''); citationButton.current?.focus(); }}>Close source</button></div><p className="muted">{citation.section}</p><blockquote className="source-excerpt">{citation.quote}</blockquote><Link to={`/w/${workspace.id}/knowledge/${citation.document_id}?version=${citation.version_id}&offset=${citation.quote_start}`}>Open exact document version</Link><p className="muted">Saved evidence at processing time. The document view shows whether this version is still active.</p></aside>}
      {error && <p className="error" role="alert">{error}</p>}
      {workspace.role !== 'viewer' && active(run.state) && <button onClick={cancel} disabled={pending}>{pending ? 'Cancelling…' : 'Cancel processing'}</button>}
      <ReviewPanel key={`${run.draft_hash}:${run.review_version}`} run={run} workspace={workspace} path={path} onSubmitted={changed} />
      {workspace.role === 'admin' && run.state === 'waiting_for_input' && <details className="development-controls" onToggle={event => setDevelopmentOpen(event.currentTarget.open)}><summary>Development response controls</summary>{developmentOpen && <DevelopmentResponse path={path} onSubmitted={changed} />}</details>}
      <AttemptControls run={run} workspace={workspace} onCreated={id => { onChanged(); navigate(`/w/${workspace.id}/runs/${id}`); }} />
      <ProcessingDetails run={run} />
    </>}
  </div>;
}
