import type { ReactNode } from 'react';
import { CopyResponse } from './CopyResponse';
import { outcomeLabel, type Run } from './types';

export function RunResult({ run, children }: { run: Run; children?: ReactNode }) {
  const draftName = run.handoff?.provider === 'local_ollama' ? 'AI draft' : 'Development draft';
  const question = run.state === 'completed' && run.outcome === 'clarification_needed' && run.review?.action === 'clarify' ? run.review.response : null;
  const primary = question ?? run.reviewed_response ?? run.draft;
  const historical = question ? 'Original unapproved draft' : run.reviewed_response ? `Original ${draftName.toLowerCase()}` : null;
  const pending = {
    waiting_for_input: 'Retrieval is complete. An administrator can supply a development response using the supporting evidence.',
    cancelled: 'This processing attempt was cancelled. The original message and processing history are preserved.',
    failed: 'Processing stopped before a response was ready. Inspect the Workflow tab, then retry or add customer details.',
  }[run.state] ?? 'Your message is saved. Processing will continue in the background.';
  return <section className="run-result">
    <h2>{question ? 'Clarification requested' : outcomeLabel(run.outcome)}</h2>
    {primary ? <p className="response-text" lang={run.language}>{primary}</p> : <p className="muted">{pending}</p>}
    {run.state === 'completed' && run.outcome === 'approved_response' && run.reviewed_response &&
      <CopyResponse key={`${run.id}:${run.reviewed_response}`} response={run.reviewed_response} />}
    {question && <p className="muted">Recorded here, not sent to the customer. Sources below belong to the original draft.</p>}
    {historical && <details><summary>{historical}</summary><p className="response-text" lang={run.language}>{run.draft}</p></details>}
    {!historical && run.draft && !!run.citations.length && <p className="muted">{run.state === 'rejected' ? `Rejected ${draftName.toLowerCase()}` : draftName} · Not approved for sending</p>}
    {run.error_code && <details><summary>Failure information</summary><p className="error">{run.error_code}</p></details>}
    {children}
  </section>;
}
