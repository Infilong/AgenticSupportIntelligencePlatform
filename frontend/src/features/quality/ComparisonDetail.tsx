import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../../api/client';
import type { components } from '../../api/schema';
import { useResource } from '../workbench/useResource';
import { stateLabel } from '../workbench/types';
import { RetrievalTrace } from '../knowledge/RetrievalTrace';

type Detail = components['schemas']['ComparisonDetail'];
const labels: Record<string, string> = { direct_llm: 'Direct answer', vector_rag: 'Vector retrieval', hybrid_rag: 'Hybrid retrieval', system_v1: 'Governed support workflow' };
const pipelineOrder = Object.keys(labels);
const status = (value: string) => value === 'waiting_for_input' ? 'Needs development contribution' : value === 'insufficient_evidence' ? 'No supporting knowledge' : stateLabel(value);

export function ComparisonDetail({ workspaceId, id }: { workspaceId: string; id: string }) {
  const path = `/workspaces/${workspaceId}/comparisons/${id}`;
  const record = useResource<Detail>(path, 3000);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const controller = useRef<AbortController | null>(null);
  useEffect(() => () => controller.current?.abort(), []);
  async function cancel() {
    if (pending) return;
    controller.current = new AbortController(); const signal = controller.current.signal;
    setPending(true); setError('');
    try { await api(`${path}/cancel`, { method: 'POST', signal }); if (!signal.aborted) record.refresh(); }
    catch (err) { if (!signal.aborted) setError((err as Error).message); }
    finally { if (!signal.aborted) setPending(false); }
  }
  if (record.error) return <div><p role="alert" className="error">{record.error}</p><button onClick={record.refresh}>Retry comparison</button></div>;
  if (!record.data) return <p role="status">Loading comparison…</p>;
  const data = record.data;
  const unfinished = data.pipelines.some(item => !['completed', 'rejected', 'cancelled', 'failed', 'insufficient_evidence'].includes(item.state));
  return <section className="comparison-detail" aria-label="Comparison results">
    <h3>{data.question}</h3>
    <p className="muted">Answer language: {data.language.toUpperCase()} · {data.pipelines.some(item => item.configuration.transport === 'local_ollama') ? 'Local model responses' : 'Development responses'} · Answer quality unverified</p>
    {data.cancelled ? <p role="status">Comparison cancelled. Saved outcomes remain in history.</p> : !data.comparable && <p role="alert" className="error">Knowledge changed since this comparison started. Start a new comparison to use current sources.</p>}
    <div className="comparison-grid">{[...data.pipelines].sort((a, b) => pipelineOrder.indexOf(a.name) - pipelineOrder.indexOf(b.name)).map(item => {
      const answer = typeof item.initial_response?.answer === 'string' ? item.initial_response.answer : null;
      return <article key={item.name} className="inbox-panel section-padding">
        <h4>{labels[item.name] ?? item.name}</h4><p className="comparison-state">{status(item.state)}</p>
        {!answer && item.outcome === 'clarification_needed' && <p>More customer details are needed. Open the workflow to inspect the clarification.</p>}
        {!answer && item.outcome === 'insufficient_evidence' && <p>No supporting knowledge was found.</p>}
        {item.error_code && <p className="error">Processing error: {item.error_code}</p>}
        {answer ? <><h5>{item.configuration.transport === 'local_ollama' ? 'Generated answer' : 'Original contribution'}</h5><p className="comparison-answer" lang={data.language}>{answer}</p></> : <p className="muted">No generated answer recorded.</p>}
        {item.reviewed_response && <><h5>Reviewed response</h5><p className="comparison-answer" lang={data.language}>{item.reviewed_response}</p></>}
        {item.run_id && <Link to={`/w/${workspaceId}/runs/${item.run_id}`}>Open workflow and review</Link>}
        {item.retrieval_id && <RetrievalTrace workspaceId={workspaceId} traceId={item.retrieval_id} />}
        <details className="comparison-provenance"><summary>Processing record</summary><dl><dt>Retrieval</dt><dd>{item.configuration.strategy ?? 'None'}</dd><dt>Job attempts</dt><dd>{item.attempts}</dd><dt>Request hash</dt><dd>{item.request_hash ?? 'Not prepared'}</dd><dt>Response hash</dt><dd>{item.response_hash ?? 'Not submitted'}</dd></dl></details>
      </article>;
    })}</div>
    <p className="muted">A completed response is not a correctness score. Human-reviewed wording is shown separately from the original contribution; failed and unfinished paths stay visible.</p>
    {!data.cancelled && unfinished && <button disabled={pending} onClick={() => void cancel()}>{pending ? 'Cancelling…' : 'Cancel pending comparison work'}</button>}
    {error && <p role="alert" className="error">{error}</p>}
  </section>;
}
