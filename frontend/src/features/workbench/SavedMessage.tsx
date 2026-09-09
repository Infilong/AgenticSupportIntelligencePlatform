import { useEffect, useRef, useState, type FormEvent } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { api, type Workspace } from '../../api/client';
import type { components } from '../../api/schema';
import { languageLabel, type Created } from './types';
import { useResource } from './useResource';

type Saved = components['schemas']['SavedMessage'];
export function SavedMessage({ workspace, messageId }: { workspace: Workspace; messageId: string }) {
  const path = `/workspaces/${workspace.id}/messages/${messageId}`;
  const resource = useResource<Saved>(path, 10000);
  const [labels, setLabels] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [params] = useSearchParams(); const navigate = useNavigate();
  const search = params.size ? `?${params}` : '';
  const base = `/w/${workspace.id}`;
  const controller = useRef<AbortController | null>(null);
  useEffect(() => () => controller.current?.abort(), []);
  async function act(kind: 'labels' | 'process', event?: FormEvent) {
    event?.preventDefault(); if (pending) return;
    setPending(true); setError(''); setNotice(''); controller.current = new AbortController(); const signal = controller.current.signal;
    try {
      if (kind === 'labels') {
        const values = (labels ?? resource.data?.labels.join(', ') ?? '').split(',').map(x => x.trim()).filter(Boolean);
        await api<Saved>(`${path}/labels`, { method: 'PUT', body: JSON.stringify({ labels: values }), signal });
        if (!signal.aborted) { setLabels(null); setNotice('Labels saved.'); resource.refresh(); }
      } else {
        const result = await api<Created>(`${path}/process`, { method: 'POST', signal });
        if (!signal.aborted) navigate(`${base}/runs/${result.run_id}${search}`);
      }
    } catch (err) { if (!signal.aborted) setError((err as Error).message); }
    finally { if (!signal.aborted) setPending(false); }
  }
  return <div className="message-composer"><Link to={`${base}${search}`}>← All messages</Link>
    {resource.error && <><p role="alert" className="error">{resource.error}</p><button onClick={resource.refresh}>Try again</button></>}
    {!resource.data && !resource.error && <p role="status">Loading message…</p>}
    {resource.data && <><h2>Original message</h2><p className="original-text" lang={resource.data.language}>{resource.data.original}</p>
      <p className="muted">{languageLabel(resource.data.language)} · {resource.data.import_filename ? `Imported from ${resource.data.import_filename}` : 'Entered manually'}</p>
      {workspace.role === 'viewer' ? <p>Labels: {resource.data.labels.join(', ') || 'None'}</p> : <form onSubmit={event => act('labels', event)}><label htmlFor="message-labels">Labels</label><input id="message-labels" value={labels ?? resource.data.labels.join(', ')} maxLength={340} disabled={pending} onChange={event => setLabels(event.target.value)} aria-describedby="labels-help" /><p id="labels-help" className="muted">Separate labels with commas. Up to 10 labels, 32 characters each.</p><button disabled={pending || labels === null}>Save labels</button></form>}
      {notice && <p role="status">{notice}</p>}{error && <p role="alert" className="error">{error}</p>}
      {resource.data.latest_run_id ? <Link className="primary action-link" to={`${base}/runs/${resource.data.latest_run_id}${search}`}>Open processing</Link> : <><p>This message is saved and has not been processed.</p>{workspace.role !== 'viewer' && <button className="primary" disabled={pending} onClick={() => act('process')}>{pending ? 'Saving…' : 'Start processing'}</button>}</>}
    </>}
  </div>;
}
