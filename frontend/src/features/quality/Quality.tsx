import { useState } from 'react';
import type { Workspace } from '../../api/client';
import type { components } from '../../api/schema';
import { useResource } from '../workbench/useResource';
import './quality.css';

type Usage = components['schemas']['UsageReport'];
const number = (value: number) => value.toLocaleString();
export function Quality({ workspace }: { workspace: Workspace }) {
  const [days, setDays] = useState(7);
  const report = useResource<Usage>(`/workspaces/${workspace.id}/usage?days=${days}`, 30000);
  const totals = report.data?.totals;
  return <><div className="page-heading"><p className="eyebrow">WORKSPACE ACTIVITY</p><h1>Quality</h1><p className="muted">Inspect recorded model activity and measurement gaps.</p></div>
    <div className="usage-toolbar"><h2>Model usage</h2><label>Period <select value={days} onChange={event => setDays(Number(event.target.value))}><option value={1}>Last 24 hours</option><option value={7}>Last 7 days</option><option value={30}>Last 30 days</option><option value={90}>Last 90 days</option></select></label></div>
    {report.error && <div><p className="error" role="alert">{report.error}</p><button onClick={report.refresh}>Try again</button></div>}
    {!report.data && !report.error && <p role="status">Loading usage…</p>}
    {totals && <><div className="usage-cards"><section className="inbox-panel section-padding"><h3>Recorded calls</h3><strong>{number(totals.calls)}</strong><p>{number(totals.succeeded)} succeeded · {number(totals.failed)} failed</p><p className="muted">{number(totals.started)} started · {number(totals.uncertain)} uncertain</p></section>
      <section className="inbox-panel section-padding"><h3>Recorded input tokens</h3><strong>{number(totals.input_tokens)}</strong><p className="muted">{number(totals.missing_tokens)} calls without token measurements</p></section>
      <section className="inbox-panel section-padding"><h3>Recorded external charge</h3><strong>${totals.recorded_cost_usd.toFixed(4)}</strong><p className="muted">{number(totals.missing_cost)} calls without cost measurements</p></section></div>
      <p className="usage-note">These are recorded operations, not an answer-quality score. Local embedding and reranking have no external API charge. Missing measurements are excluded from sums; an uncertain call may still have used resources. Development handoffs are not automatic model calls.</p>
      <section className="inbox-panel"><div className="panel-heading"><h2>By model and operation</h2></div>{!totals.calls ? <div className="section-padding"><h3>No recorded model calls</h3><p>Index a knowledge document or process a message to see activity here.</p></div> : <div className="usage-table-scroll" role="region" aria-label="Model usage results" tabIndex={0}><table className="usage-table"><thead><tr><th>Model / operation</th><th>Calls</th><th>Failed / uncertain</th><th>Input tokens</th><th>Recorded duration</th><th>External charge</th></tr></thead><tbody>{report.data!.models.map(model => <tr key={`${model.provider}/${model.model}/${model.revision}/${model.operation}`}><td><strong>{model.model}</strong><p>{model.operation.replaceAll('_', ' ')} · {model.provider.replaceAll('_', ' ')}</p><details><summary>Revision</summary><span className="model-revision">{model.revision}</span></details></td><td>{number(model.calls)}</td><td>{model.failed} / {model.uncertain}</td><td>{number(model.input_tokens)}<small>{model.missing_tokens} unmeasured</small></td><td>{(model.recorded_duration_ms / 1000).toFixed(2)} s<small>{model.missing_duration} unmeasured</small></td><td>${model.recorded_cost_usd.toFixed(4)}<small>{model.missing_cost} unmeasured</small></td></tr>)}</tbody></table></div>}</section>
      <p className="muted usage-note">{report.data!.more_models ? 'Showing the 20 most-used model/operation groups. Totals include every group. ' : ''}Durations sum recorded call time; they are not workflow wall time. Window ends {new Date(report.data!.until).toLocaleString()}.</p>
    </>}
  </>;
}
