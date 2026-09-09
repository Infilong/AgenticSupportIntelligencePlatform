import { Link } from 'react-router-dom';
import { outcomeLabel, stateLabel, type Run } from './types';

export function AttemptHistory({ run, workspaceId, search = '' }: { run: Run; workspaceId: string; search?: string }) {
  return <details><summary>Attempt history · {run.attempts.length}</summary><ol className="attempt-history">{run.attempts.map(item => <li key={item.id}>
    <Link to={`/w/${workspaceId}/runs/${item.id}${search}`} aria-current={item.id === run.id ? 'page' : undefined}>Attempt {item.number} · {item.kind === 'clarify' ? 'Added details' : item.kind === 'retry' ? 'Retry' : 'Original'}</Link>
    <span className="muted">{stateLabel(item.state)}{item.outcome ? ` · ${outcomeLabel(item.outcome)}` : ''}</span>
  </li>)}</ol></details>;
}

export function ReviewHistory({ run }: { run: Run }) {
  if (!run.review) return <p className="muted">No review decision recorded.</p>;
  return <details className="review-history"><summary>Review decision · {run.review.action}</summary>
    {run.review.action === 'clarify' && <><h3>Recorded question</h3><p className="response-text" lang={run.language}>{run.review.response}</p></>}
    <p className="response-text">{run.review.reason}</p><p className="metadata">Reviewed by {run.review.actor_id} · {new Date(run.review.created_at).toLocaleString()}</p>
    <p className="muted">The recorded decision is preserved even if subsequent processing is cancelled or fails.</p>
  </details>;
}
