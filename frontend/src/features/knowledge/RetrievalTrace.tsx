import { useState } from 'react';
import { Link } from 'react-router-dom';
import type { components } from '../../api/schema';
import { useResource } from '../workbench/useResource';
import './retrieval-trace.css';

type Trace = components['schemas']['TraceDetail'];
const score = (value: number | null | undefined) => value == null ? '—' : value.toFixed(3);

function Evidence({ workspaceId, traceId }: { workspaceId: string; traceId: string }) {
  const [expanded, setExpanded] = useState(false);
  const { data, error, refresh } = useResource<Trace>(`/workspaces/${workspaceId}/retrieval/${traceId}`);
  if (error) return <><p className="error" role="alert">{error}</p><button onClick={refresh}>Retry trace</button></>;
  if (!data) return <p role="status">Loading retrieval evidence…</p>;
  return <div className="retrieval-trace">
    <p><strong>{data.strategy}</strong> · {data.status}{data.duration_ms != null && ` · ${(data.duration_ms / 1000).toFixed(2)} s`}</p>
    {data.error_code && <p className="error">Recorded failure: {data.error_code}</p>}
    {data.phase === 'unavailable' ? <p>Candidate history was not recorded for this older search. Its saved results remain available.</p> : <>
      <p className="muted">{data.candidates.length} recorded candidates. Scores use different scales and are not confidence percentages. A dash means that stage did not score the source.</p>
      {data.phase !== 'completed' && <p role="status">{data.status === 'started' ? 'Retrieval is in progress' : 'Retrieval stopped'} at “{data.phase}”. Final ranking is not available. <button onClick={refresh}>Refresh trace</button></p>}
      {data.candidates.length > 5 && <p className="muted">Showing {expanded ? data.candidates.length : 5} of {data.candidates.length} candidates in retrieval order.</p>}
      <ol className="trace-candidates">{(expanded ? data.candidates : data.candidates.slice(0, 5)).map(row => <li key={row.chunk_id}>
        <div className="trace-source"><Link to={`/w/${workspaceId}/knowledge/${row.document_id}?version=${row.version_id}&offset=${row.start_offset}`}>{row.title} · {row.section}</Link>
          <strong>{row.final_rank ? `Final #${row.final_rank}` : row.exclusion ? row.exclusion.replaceAll('_', ' ') : 'No final rank'}</strong></div>
        {!row.currently_active && <p className="muted">This version is no longer an active source.</p>}
        <dl className="trace-scores"><div><dt>Vector</dt><dd>{row.vector_rank ? `#${row.vector_rank} · ` : ''}{score(row.cosine_similarity)}</dd></div>
          <div><dt>BM25</dt><dd>{row.bm25_rank ? `#${row.bm25_rank} · ` : ''}{score(row.bm25_score)}</dd></div>
          <div><dt>Fusion</dt><dd>{row.fusion_rank ? `#${row.fusion_rank} · ` : ''}{score(row.fusion_score)}</dd></div>
          <div><dt>Reranker</dt><dd>{row.reranker_rank ? `#${row.reranker_rank} · ` : ''}{score(row.reranker_score)}</dd></div></dl>
      </li>)}</ol>
      {data.candidates.length > 5 && <button onClick={() => setExpanded(!expanded)} aria-expanded={expanded}>{expanded ? 'Show fewer candidates' : `Show all ${data.candidates.length} candidates`}</button>}
      {!data.candidates.length && <p>No candidate sources were recorded.</p>}
    </>}
    <details><summary>Recorded parameters</summary><dl>{Object.entries(data.parameters).map(([key, value]) => <div key={key}><dt>{key.replaceAll('_', ' ')}</dt><dd>{value}</dd></div>)}</dl><p className="metadata">Trace {data.id}</p></details>
  </div>;
}

export function RetrievalTrace({ workspaceId, traceId }: { workspaceId: string; traceId: string }) {
  const [open, setOpen] = useState(false);
  return <details onToggle={event => setOpen(event.currentTarget.open)}><summary>Retrieval evidence</summary>
    {open && <Evidence workspaceId={workspaceId} traceId={traceId} />}
  </details>;
}
