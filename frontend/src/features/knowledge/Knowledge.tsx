import { useEffect, useState, type FormEvent } from 'react';
import { BookOpen, Search } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { api, type Workspace } from '../../api/client';
import { Upload } from './Upload';
import { documentState, type DocumentPage } from './types';
import './knowledge.css';

export function Knowledge({ workspace }: { workspace: Workspace }) {
  const navigate = useNavigate();
  const [page, setPage] = useState<DocumentPage | null>(null);
  const [input, setInput] = useState('');
  const [search, setSearch] = useState('');
  const [offset, setOffset] = useState(0);
  const [revision, setRevision] = useState(0);
  const [error, setError] = useState('');
  useEffect(() => {
    const controller = new AbortController(); let timer: ReturnType<typeof setTimeout>;
    setPage(null); setError('');
    async function load() {
      try {
        const value = await api<DocumentPage>(`/workspaces/${workspace.id}/documents?search=${encodeURIComponent(search)}&offset=${offset}&limit=20`, { signal: controller.signal });
        setPage(value); setError('');
        if (value.items.some(item => ['queued', 'running'].includes(item.job_status ?? ''))) timer = setTimeout(load, 2000);
      } catch (err) { if (!controller.signal.aborted) setError((err as Error).message); }
    }
    void load(); return () => { controller.abort(); clearTimeout(timer); };
  }, [workspace.id, search, offset, revision]);
  function filter(event: FormEvent) { event.preventDefault(); setSearch(input); setOffset(0); }
  const base = `/w/${workspace.id}/knowledge`;
  return <><div className="page-heading knowledge-heading"><div><p className="eyebrow">TRUSTED SOURCES</p><h1>Knowledge</h1>
    <p className="muted">Manage the policies your support team can rely on.</p></div><Link className="button-link" to={`${base}/search`}><Search size={17} />Search knowledge</Link></div>
    {workspace.role === 'admin' && <Upload workspaceId={workspace.id} onUploaded={value => navigate(`${base}/${value.document_id}`)} />}
    <section className="inbox-panel"><div className="panel-heading knowledge-heading"><h2>Documents {page && <span className="count">{page.total}</span>}</h2>
      <form onSubmit={filter} className="compact-search"><input aria-label="Filter documents" placeholder="Find a document…" value={input} onChange={e => setInput(e.target.value)} maxLength={200} /><button>Filter</button></form></div>
      {error && <div className="section-padding"><p className="error" role="alert">{error}</p><button onClick={() => setRevision(x => x + 1)}>Try again</button></div>}
      {!page && !error && <p className="section-padding" role="status">Loading documents…</p>}
      {page?.items.map(item => <Link className="document-row" key={item.id} to={`${base}/${item.id}`}><BookOpen size={22} /><span className="document-name"><strong>{item.title}</strong><small>Version {item.version_number}</small></span><span className={`status-pill ${documentState(item) === 'Ready' ? 'ready' : ''}`}>{documentState(item)}</span></Link>)}
      {page?.items.length === 0 && <div className="empty-state"><BookOpen size={30} /><h2>{search ? 'No matching documents' : 'Your knowledge starts here'}</h2><p>{search ? 'Try another document name.' : 'Upload a company policy, then search for the exact passages that answer a question.'}</p></div>}
      {page && (offset > 0 || offset + 20 < page.total) && <div className="pagination"><button disabled={offset === 0} onClick={() => setOffset(x => Math.max(0, x - 20))}>Previous</button><span>{offset + 1}–{Math.min(offset + 20, page.total)} of {page.total}</span><button disabled={offset + 20 >= page.total} onClick={() => setOffset(x => x + 20)}>Next</button></div>}
    </section></>;
}
