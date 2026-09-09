import { duration, type Run } from './types';

const nodeName = (node: string) => ({ validate_input: 'Check message', retrieve_evidence: 'Find supporting knowledge', development_generation: 'Prepare development draft' }[node] ?? node);

export function ProcessingDetails({ run }: { run: Run }) {
  return <details className="processing-details"><summary>Processing details</summary>
    <h3>Timeline</h3>{run.steps.length ? <ol className="run-timeline">{run.steps.map(step => <li key={step.id}><div><strong>{nodeName(step.node)}</strong><span>{step.status} · {duration(step.duration_ms)} · attempt {step.job_attempt}</span></div>{step.error_code && <code>{step.error_code}</code>}</li>)}</ol> : <p className="muted">No processing steps recorded yet.</p>}
    <h3>Model calls</h3>{run.model_calls.length ? run.model_calls.map(call => <article className="model-call" key={call.id}><strong>{call.operation === 'embed_query' ? 'Embed query' : call.operation === 'rerank' ? 'Rank evidence' : call.operation}</strong><p>{call.model}</p><dl className="run-facts"><div><dt>Status</dt><dd>{call.status}</dd></div><div><dt>Duration</dt><dd>{duration(call.duration_ms)}</dd></div><div><dt>Input tokens</dt><dd>{call.input_tokens ?? 'Not recorded'}</dd></div><div><dt>External charge</dt><dd>{call.api_cost_usd == null ? 'Unknown' : `$${call.api_cost_usd.toFixed(4)}`}</dd></div></dl><details><summary>Model identity</summary><p className="metadata">Provider: {call.provider}<br />Revision: {call.revision}</p></details>{call.error_code && <p className="error">{call.error_code}</p>}</article>) : <p className="muted">No model calls recorded.</p>}
    {run.handoff && <><h3>Development response</h3><p className="muted">Attributed development contribution. No external generation API was called.</p><dl className="run-facts"><div><dt>Provider</dt><dd>{run.handoff.provider}</dd></div><div><dt>Handoff elapsed</dt><dd>{duration(run.handoff.handoff_elapsed_ms)}</dd></div></dl><p className="muted">Handoff elapsed includes waiting; it is not model inference latency.</p></>}
    <details><summary>Record identifiers</summary><p className="metadata">Run: {run.id}<br />Job: {run.job_id}<br />Retrieval: {run.retrieval_id ?? 'Not started'}<br />Prompt: {run.handoff?.prompt_version ?? 'Not used'}<br />Contributor: {run.handoff?.contributor_id ?? 'Not submitted'}</p></details>
  </details>;
}
