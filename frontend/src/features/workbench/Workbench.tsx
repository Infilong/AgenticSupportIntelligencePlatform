import { Inbox, Plus, Search } from 'lucide-react';
import { useEffect, useState, type FormEvent } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import type { Workspace } from '../../api/client';
import { NewMessage } from './NewMessage';
import { RunView } from './RunView';
import { languageLabel, outcomeLabel, stateLabel, type MessagePage } from './types';
import { useResource } from './useResource';
import './workbench.css';

export function Workbench({ workspace }: { workspace: Workspace }) {
  const { runId } = useParams();
  const navigate = useNavigate();
  const [composing, setComposing] = useState(false);
  const [query, setQuery] = useState('');
  const [search, setSearch] = useState('');
  const [offset, setOffset] = useState(0);
  const [view, setView] = useState('all');
  const base = `/w/${workspace.id}`;
  const list = useResource<MessagePage>(`/workspaces/${workspace.id}/messages?search=${encodeURIComponent(search)}&view=${view}&offset=${offset}&limit=20`, 5000);
  const total = list.data?.total;
  useEffect(() => {
    if (total !== undefined && offset > 0 && offset >= total) setOffset(Math.max(0, Math.ceil(total / 20) - 1) * 20);
  }, [total, offset]);
  function find(event: FormEvent) { event.preventDefault(); setOffset(0); setSearch(query); }
  return <><div className="workbench-heading"><div><p className="eyebrow">CUSTOMER SUPPORT</p><h1>Workbench</h1><p className="muted">Messages, supporting knowledge, and the next step.</p></div>
    {workspace.role !== 'viewer' && <button className="primary" onClick={() => { setComposing(true); navigate(base); }}><Plus size={17} />New message</button>}</div>
    <div className={`workbench-grid ${runId || composing ? 'has-selection' : ''}`}>
      <section className="message-list" aria-label="Customer messages">
        <form className="message-search" onSubmit={find}><label className="sr-only" htmlFor="message-search">Search messages</label><input id="message-search" maxLength={200} placeholder="Search messages" value={query} onChange={e => setQuery(e.target.value)} /><button aria-label="Search messages"><Search size={17} /></button></form>
        <div className="message-filters"><label htmlFor="message-view">Message view</label><select id="message-view" value={view} onChange={e => { setView(e.target.value); setOffset(0); }}><option value="all">All messages</option><option value="attention">Needs attention</option><option value="ready">Ready responses</option><option value="processing">Processing</option><option value="failed">Failed</option></select>{(view !== 'all' || search) && <button onClick={() => { setView('all'); setQuery(''); setSearch(''); setOffset(0); }}>Clear filters</button>}</div>
        {list.error && <div className="section-padding"><p role="alert" className="error">{list.error}</p><button onClick={list.refresh}>Try again</button></div>}
        {!list.data && !list.error && <p className="section-padding" role="status">Loading messages…</p>}
        {list.data && <><div className="message-count">{list.data.total} messages{search && ` matching “${search}”`}</div>
          <div className="message-rows" role="region" aria-label="Message results" tabIndex={0}>{list.data.items.map(message => <Link className={`message-row ${runId === message.run_id ? 'selected' : ''}`} key={message.id} to={`${base}/runs/${message.run_id}`} onClick={() => setComposing(false)} aria-current={runId === message.run_id ? 'page' : undefined}>
            <span className="message-preview" lang={message.language}>{message.original}</span><span className="message-meta"><span className={`run-state ${message.state}`}>{message.state === 'completed' && message.outcome ? outcomeLabel(message.outcome) : stateLabel(message.state)}</span><span>{languageLabel(message.language)}</span></span>
          </Link>)}
          {!list.data.items.length && <div className="inbox-empty"><Inbox size={26} /><h2>{search || view !== 'all' ? 'No matching messages' : 'Your inbox is ready'}</h2><p>{search || view !== 'all' ? 'Try another view or clear the filters.' : 'Add a customer message to find supporting knowledge and prepare a response.'}</p></div>}</div>
          {list.data.total > 20 && <div className="list-pagination"><button disabled={!offset} onClick={() => setOffset(x => Math.max(0, x - 20))}>Previous</button><span>{offset + 1}–{Math.min(offset + 20, list.data.total)}</span><button disabled={offset + 20 >= list.data.total} onClick={() => setOffset(x => x + 20)}>Next</button></div>}
        </>}
      </section>
      <section className="message-detail" aria-label="Selected message">
        {composing ? <NewMessage key={workspace.id} workspace={workspace} onClose={() => setComposing(false)} onCreated={id => { setComposing(false); setSearch(''); setQuery(''); setView('all'); setOffset(0); list.refresh(); navigate(`${base}/runs/${id}`); }} /> : runId ? <RunView key={`${workspace.id}/${runId}`} workspace={workspace} runId={runId} onChanged={list.refresh} /> : <div className="inbox-empty detail-placeholder"><Inbox size={30} /><h2>Select a message</h2><p>Read the original request, check its response and explore how it was processed.</p></div>}
      </section>
    </div></>;
}
