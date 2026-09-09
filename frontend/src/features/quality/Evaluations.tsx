import { useState } from 'react';
import type { components } from '../../api/schema';
import { useResource } from '../workbench/useResource';
import { EvaluationResults } from './EvaluationResults';
import './evaluations.css';

type Records = components['schemas']['EvaluationList'];
type Detail = components['schemas']['EvaluationDetail'];

function Record({ workspaceId, id }: { workspaceId: string; id: string }) {
  const record = useResource<Detail>(`/workspaces/${workspaceId}/evaluations/${id}`);
  if (record.error) return <div><p role="alert" className="error">{record.error}</p><button onClick={record.refresh}>Retry evaluation</button></div>;
  if (!record.data) return <p role="status">Loading evaluation…</p>;
  return <EvaluationResults workspaceId={workspaceId} record={record.data} />;
}

export function Evaluations({ workspaceId }: { workspaceId: string }) {
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState('');
  const records = useResource<Records>(`/workspaces/${workspaceId}/evaluations?page=${page}`);
  const id = records.data?.items.some(item => item.id === selected) ? selected : records.data?.items[0]?.id;
  return <section className="evaluation-view" aria-labelledby="evaluation-heading">
    <h2 id="evaluation-heading">Historical retrieval checks</h2>
    <p className="muted">Compare saved searches and inspect the evidence behind each result.</p>
    {records.error ? <div><p role="alert" className="error">{records.error}</p><button onClick={records.refresh}>Retry evaluations</button></div> : !records.data ? <p role="status">Loading evaluation history…</p> : <>
      {!records.data.items.length ? <div className="inbox-panel section-padding"><h3>No registered results</h3><p>No historical retrieval report is registered for this workspace. A workspace administrator can register a completed local report using the documented evaluation command.</p></div> : <>
        <label className="evaluation-history">Saved report <select value={id} onChange={event => setSelected(event.target.value)}>{records.data.items.map(item => <option key={item.id} value={item.id}>Registered {new Date(item.registered_at).toLocaleString()} · {item.report_sha256.slice(0, 8)}</option>)}</select></label>
        {id && <Record key={`${workspaceId}/${id}`} workspaceId={workspaceId} id={id} />}
      </>}
      {(page > 1 || records.data.more) && <nav className="evaluation-paging" aria-label="Evaluation pages"><button disabled={page === 1} onClick={() => setPage(page - 1)}>Previous reports</button><span>Page {page}</span><button disabled={!records.data.more || page === 500} onClick={() => setPage(page + 1)}>Next reports</button></nav>}
    </>}
  </section>;
}
