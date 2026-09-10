import { ArrowDown, ArrowRight, GitBranch } from 'lucide-react';
import { useState } from 'react';
import { duration, outcomeLabel, stateLabel, type Run } from './types';
import { nodeState, workflowNodes as defaultNodes } from './workflow';
import './workflow.css';
import { RetrievalTrace } from '../knowledge/RetrievalTrace';

export function WorkflowView({ run, workspaceId }: { run: Run; workspaceId: string }) {
  const local = run.handoff?.provider === 'local_ollama' || run.steps.some(step => step.node === 'local_generation');
  const workflowNodes = defaultNodes.map(item => local && item.id === 'development_generation'
    ? { ...item, id: 'local_generation', detail: 'A local model generates a draft from retrieved evidence through LangChain. Administrator review is still required.' } : item);
  const [selected, setSelected] = useState<string | null>(null);
  const node = workflowNodes.find(item => item.id === selected);
  const state = node ? nodeState(run, node.id) : null;
  const published = ['completed', 'rejected'].includes(run.state);
  return <section className="workflow-view" aria-label="Workflow execution">
    <div className="workflow-heading"><h2><GitBranch size={17} aria-hidden="true" />Workflow</h2><span>LangGraph · attempt {run.attempt_number}</span></div>
    <p className="muted">Recorded execution. Select a stage to inspect its evidence and history.</p>
    <ol className="workflow-path">{workflowNodes.map((item, index) => {
      const current = nodeState(run, item.id);
      return <li key={item.id}><button className={`workflow-node ${current.tone}`} aria-expanded={selected === item.id} aria-controls={selected === item.id ? 'workflow-inspector' : undefined}
        onClick={() => setSelected(selected === item.id ? null : item.id)}>
        <span className="workflow-number">{index + 1}</span><strong>{item.title}</strong><span>{current.label}</span>
        <small>{current.latest ? duration(current.latest.duration_ms) : 'No execution time'}</small>
      </button>{index < workflowNodes.length - 1 && <ArrowRight className="workflow-arrow" size={16} aria-hidden="true" />}</li>;
    })}</ol>
    <div className="workflow-outcome"><ArrowDown size={15} aria-hidden="true" /><span>Run outcome:</span><strong>{published && run.outcome ? outcomeLabel(run.outcome) : stateLabel(run.state)}</strong>
      {run.error_code && <code>{run.error_code}</code>}</div>
    {node && state && <div id="workflow-inspector" className="workflow-inspector" role="region" aria-label={`${node.title} details`}>
      <h3>{node.title}</h3><p>{node.detail}</p>
      {node.id === 'validate_input' && <blockquote lang={run.language}>{run.input_text}</blockquote>}
      {node.id === 'retrieve_evidence' && <><p>Retrieval record: <code>{run.retrieval_id ?? 'Not recorded'}</code></p>
        {run.retrieval_id && <RetrievalTrace workspaceId={workspaceId} traceId={run.retrieval_id} />}
        {run.model_calls.filter(call => call.operation !== 'generate').map(call => <div className="workflow-call" key={call.id}><strong>{call.operation === 'embed_query' ? 'Embed query' : call.operation === 'rerank' ? 'Rank evidence' : call.operation}</strong>
          <span>{call.model}</span><span>{call.status} · {duration(call.duration_ms)} · {call.input_tokens ?? 'Unknown'} input tokens</span>
          <span>External charge: {call.api_cost_usd == null ? 'Unknown' : `$${call.api_cost_usd.toFixed(4)}`}</span>
          {call.error_code && <code>{call.error_code}</code>}</div>)}
        <p className="muted">Model calls belong to the linked retrieval. Their time is included in retrieval time; this is not lifetime accounting across retries.</p></>}
      {node.id === 'development_generation' && <><p>{run.handoff ? `Provider: ${run.handoff.provider}` : 'No development handoff recorded.'}</p>
        {run.handoff && <p>{run.handoff.timing_status === 'clock_anomaly' ? 'Turnaround unavailable: recorded timestamps are out of order.' : `Handoff turnaround: ${duration(run.handoff.handoff_elapsed_ms)}`}</p>}
        <p className="muted">Turnaround includes waiting and contribution time. It is not model inference latency.</p></>}
      {node.id === 'local_generation' && <><p>Provider: local_ollama · LangChain</p>
        {run.model_calls.filter(call => call.operation === 'generate').map(call => <div className="workflow-call" key={call.id}>
          <strong>{call.model}</strong><span>{call.status} · {duration(call.duration_ms)} · {call.input_tokens ?? 'Unknown'} input tokens</span>
          <span>External charge: {call.api_cost_usd == null ? 'Unknown' : `$${call.api_cost_usd.toFixed(4)}`}</span>
          {call.error_code && <code>{call.error_code}</code>}</div>)}
        <p className="muted">Runs on this computer. Citations identify retrieved passages; an administrator must check the answer.</p></>}
      {node.id === 'human_review' && <p>{run.review ? `Recorded decision: ${run.review.action}. ${run.review.reason}` : 'No human decision recorded.'}</p>}
      {state.records.length ? <><h3>Recorded invocations</h3><ol className="workflow-records">{state.records.map(step => <li key={step.id}>
        <span>{step.status} · {duration(step.duration_ms)} · job attempt {step.job_attempt}</span>{step.error_code && <code>{step.error_code}</code>}
      </li>)}</ol></> : <p>No execution record for this stage.</p>}
      <p className="muted">Invocation time excludes suspended waiting. Node completion alone does not prove a response was published.</p>
    </div>}
  </section>;
}
