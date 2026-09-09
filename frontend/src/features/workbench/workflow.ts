import type { Run } from './types';

export const workflowNodes = [
  { id: 'validate_input', title: 'Check message', detail: 'Checks whether the input is meaningful enough to retrieve evidence. Short input can finish with a clarification request.' },
  { id: 'retrieve_evidence', title: 'Retrieve evidence', detail: 'LangChain embeddings → PostgreSQL vector search → local reranking → authorized context. Context preparation is included in this node, not timed separately.' },
  { id: 'development_generation', title: 'Prepare response', detail: 'LangGraph pauses for an attributed development contribution. This environment does not call an external generation API.' },
  { id: 'human_review', title: 'Human review', detail: 'A separate durable LangGraph continuation checks the recorded decision. Final publication and its outcome are shown separately.' },
] as const;

export function nodeState(run: Run, node: string) {
  const records = run.steps.filter(step => step.node === node);
  // The API supplies chronological order. Job attempt counters restart for different jobs.
  const latest = records.at(-1);
  const terminal = ['completed', 'cancelled', 'failed', 'rejected'].includes(run.state);
  if (!latest) {
    const skipped = run.state === 'completed' && (
      (run.outcome === 'clarification_needed' && !run.retrieval_id && node !== 'validate_input') ||
      (run.outcome === 'insufficient_evidence' && ['development_generation', 'human_review'].includes(node))
    );
    return { records, latest, tone: 'pending', label: skipped ? 'Skipped by outcome' : terminal ? 'Not reached' : 'Pending' };
  }
  if (latest.status === 'started') return { records, latest, tone: terminal ? 'uncertain' : 'running', label: terminal ? 'Unfinished record' : 'Running' };
  if (latest.status === 'waiting') return { records, latest, tone: terminal ? 'uncertain' : 'waiting', label: terminal ? 'Paused before stop' : 'Paused' };
  return { records, latest, tone: latest.status, label: ({
    succeeded: 'Completed', failed: 'Failed', uncertain: 'Outcome uncertain',
  }[latest.status] ?? latest.status) };
}
