import { useEffect, useState } from 'react';
import type { Workspace } from '../../api/client';
import type { components } from '../../api/schema';
import { useResource } from '../workbench/useResource';
import { ComparisonDetail } from './ComparisonDetail';
import { NewComparison } from './NewComparison';
import './comparisons.css';

export function Comparisons({ workspace }: { workspace: Workspace }) {
  const [offset, setOffset] = useState(0);
  const [selected, setSelected] = useState('');
  const [creating, setCreating] = useState(false);
  const [busy, setBusy] = useState(false);
  const records = useResource<components['schemas']['ComparisonList']>(`/workspaces/${workspace.id}/comparisons?offset=${offset}`, 3000);
  const unavailable = !records.data && !!records.error;
  useEffect(() => { if (unavailable) { setSelected(''); setCreating(false); setBusy(false); } }, [unavailable]);
  function created(id: string) { setBusy(false); setCreating(false); setOffset(0); setSelected(id); records.refresh(); }
  const id = selected || records.data?.items[0]?.id;
  if (!records.data) return records.error ? <div><p className="error" role="alert">{records.error}</p><button onClick={records.refresh}>Retry comparison history</button></div> : <p role="status">Loading comparison history…</p>;
  return <section className="generation-comparisons" aria-labelledby="comparison-heading">
    <div className="usage-toolbar"><h2 id="comparison-heading">Generation comparisons</h2><button disabled={busy} onClick={() => setCreating(!creating)}>{creating ? 'Close new comparison' : 'New comparison'}</button></div>
    {creating && <NewComparison key={workspace.id} workspace={workspace} onCreated={created} onBusy={setBusy} />}
    {records.error ? <div><p className="error" role="alert">{records.error}</p><button onClick={records.refresh}>Retry comparison history</button></div> : !records.data ? <p role="status">Loading comparison history…</p> : <>
      {!records.data.items.length && !selected && <p>No comparisons yet. Start one to inspect the four processing paths.</p>}
      {!!records.data.items.length && <label className="comparison-history">Saved comparison<select value={id} onChange={event => setSelected(event.target.value)}>{records.data.items.map(item => <option key={item.id} value={item.id}>{item.question} · {item.language.toUpperCase()}{item.cancelled ? ' · Cancelled' : ''}</option>)}</select></label>}
      {id && <ComparisonDetail key={`${workspace.id}/${id}`} workspaceId={workspace.id} id={id} />}
      {(offset > 0 || records.data.items.length === 20) && <nav className="evaluation-paging" aria-label="Comparison pages"><button disabled={!offset} onClick={() => { setOffset(offset - 20); setSelected(''); }}>Previous comparisons</button><span>Page {offset / 20 + 1}</span><button disabled={records.data.items.length < 20 || offset >= 980} onClick={() => { setOffset(offset + 20); setSelected(''); }}>Next comparisons</button></nav>}
    </>}
  </section>;
}
