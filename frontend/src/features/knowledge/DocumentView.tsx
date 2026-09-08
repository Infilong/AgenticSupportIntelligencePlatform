import { useEffect, useState } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { api, ApiError, type Workspace } from '../../api/client';
import { Upload } from './Upload';
import { documentState, type DocumentDetail, type SourcePreview } from './types';
import './knowledge.css';

export function DocumentView({ workspace }: { workspace: Workspace }) {
  const { documentId } = useParams();
  const [params] = useSearchParams();
  const requestedVersion = params.get('version') ?? '';
  const requestedOffset = Number(params.get('offset') ?? 0);
  const initialOffset = Number.isSafeInteger(requestedOffset) && requestedOffset >= 0 && requestedOffset <= 5 * 1024 * 1024 ? requestedOffset : 0;
  const path = `/workspaces/${workspace.id}/documents/${documentId}`;
  const [detail, setDetail] = useState<DocumentDetail | null>(null);
  const [version, setVersion] = useState(requestedVersion);
  const [revision, setRevision] = useState(0);
  const [error, setError] = useState('');
  const [pending, setPending] = useState(false);
  useEffect(() => {
    const controller = new AbortController(); let timer: ReturnType<typeof setTimeout>;
    setError('');
    async function load() {
      try {
        const value = await api<DocumentDetail>(path, { signal: controller.signal });
        setDetail(value); setError('');
        if (['queued', 'running'].includes(value.document.job_status ?? '')) timer = setTimeout(load, 2000);
      } catch (err) { if (!controller.signal.aborted) {
        setError((err as Error).message);
        if (err instanceof ApiError && [403, 404].includes(err.status)) setDetail(null);
      } }
    }
    void load(); return () => { controller.abort(); clearTimeout(timer); };
  }, [path, revision]);
  async function toggle() {
    if (!detail) return; setPending(true); setError('');
    try { await api(path, { method: 'PATCH', body: JSON.stringify({ withdrawn: !detail.document.withdrawn }) }); setRevision(x => x + 1); }
    catch (err) { setError((err as Error).message); }
    finally { setPending(false); }
  }
  const document = detail?.document;
  const versionId = version || document?.active_version_id || document?.desired_version_id;
  return <><Link to={`/w/${workspace.id}/knowledge`}>← Knowledge</Link>
    {error && <div className="error"><p role="alert">{error}</p><button onClick={() => setRevision(x => x + 1)}>Try again</button></div>}
    {!detail && !error && <p role="status">Loading document…</p>}
    {detail && document && <><div className="page-heading knowledge-heading"><div><p className="eyebrow">COMPANY DOCUMENT</p><h1 className="document-title">{document.title}</h1><span className={`status-pill ${documentState(document) === 'Ready' ? 'ready' : ''}`}>{documentState(document)}</span></div>
      {workspace.role === 'admin' && <button disabled={pending} onClick={toggle}>{document.withdrawn ? 'Restore document' : 'Withdraw document'}</button>}</div>
      {document.withdrawn && <p className="notice">This document is excluded from search. Its history is preserved.</p>}
      {!document.withdrawn && document.job_status === 'failed' && <p className="error" role="alert">Indexing failed. {document.active_version_id ? 'The previous version remains available in search.' : 'This document is not available in search.'} Upload a corrected file to retry.</p>}
      {!document.withdrawn && ['queued', 'running'].includes(document.job_status ?? '') && <p className="notice" role="status">Indexing this upload… {document.active_version_id ? 'The previous version remains available until this one is ready.' : 'It will become searchable when indexing finishes.'}</p>}
      <section className="inbox-panel"><div className="panel-heading knowledge-heading"><h2>Source preview</h2><label>Version <select aria-label="Source version" value={versionId ?? ''} onChange={e => setVersion(e.target.value)}>{detail.versions.map(item => <option value={item.id} key={item.id}>Version {item.number}{item.id === document.active_version_id ? ' · Active' : ''}</option>)}</select></label></div>
        {versionId && (detail.versions.some(item => item.id === versionId) ? <Source key={`${path}/${versionId}`} path={`${path}/versions/${versionId}`} initialOffset={version === requestedVersion ? initialOffset : 0} /> : <p className="error" role="alert">The requested source version is unavailable.</p>)}
      </section>
      {workspace.role === 'admin' && !document.withdrawn && <details className="replacement"><summary>Replace this document</summary><p className="muted">The current version stays active until the replacement is successfully indexed.</p><Upload workspaceId={workspace.id} documentId={documentId} onUploaded={() => { setVersion(''); setRevision(x => x + 1); }} /></details>}
    </>}</>;
}

function Source({ path, initialOffset }: { path: string; initialOffset: number }) {
  const [offset, setOffset] = useState(initialOffset);
  const [source, setSource] = useState<SourcePreview | null>(null);
  const [error, setError] = useState('');
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    const controller = new AbortController(); setError(''); setSource(null);
    api<SourcePreview>(`${path}?offset=${offset}&limit=4000`, { signal: controller.signal }).then(setSource)
      .catch(err => { if (!controller.signal.aborted) setError(err.message); });
    return () => controller.abort();
  }, [path, offset, revision]);
  return <div className="section-padding">{error ? <><p className="error" role="alert">{error}</p><button onClick={() => setRevision(x => x + 1)}>Retry preview</button></> : !source ? <p role="status">Loading source…</p> : <><pre className="source-text">{source.text}</pre><div className="pagination"><button disabled={!offset} onClick={() => setOffset(x => Math.max(0, x - 4000))}>Previous passage</button><span>{offset + 1}–{Math.min(offset + 4000, source.total_characters)} of {source.total_characters} characters</span><button disabled={offset + 4000 >= source.total_characters} onClick={() => setOffset(x => x + 4000)}>Next passage</button></div></>}
    <a className="download-link" href={`/api${path}/original`}>Download original</a></div>;
}
