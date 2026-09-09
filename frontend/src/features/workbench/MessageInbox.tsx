import { Inbox, Search } from 'lucide-react';
import { useEffect, useState, type FormEvent } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import type { Workspace } from '../../api/client';
import { languageLabel, outcomeLabel, stateLabel, type MessagePage } from './types';
import { useResource } from './useResource';

export function MessageInbox({ workspace }: { workspace: Workspace }) {
  const [params, setParams] = useSearchParams();
  const search = (params.get('search') ?? '').slice(0, 200);
  const view = ['all', 'attention', 'ready', 'processing', 'failed'].includes(params.get('view') ?? '') ? params.get('view')! : 'all';
  const limit = params.get('limit') === '50' ? 50 : 20;
  const rawOffset = Number(params.get('offset'));
  const offset = Number.isSafeInteger(rawOffset) && rawOffset > 0 ? Math.floor(rawOffset / limit) * limit : 0;
  const [query, setQuery] = useState(search);
  const [pageInput, setPageInput] = useState('1');
  const list = useResource<MessagePage>(`/workspaces/${workspace.id}/messages?search=${encodeURIComponent(search)}&view=${view}&offset=${offset}&limit=${limit}`, 10000);
  const total = list.data?.total;
  const pages = Math.max(1, Math.ceil((total ?? 0) / limit));
  const page = Math.floor(offset / limit) + 1;
  function change(values: Record<string, string>, replace = false) {
    const next = new URLSearchParams(params);
    for (const [key, value] of Object.entries(values)) value ? next.set(key, value) : next.delete(key);
    setParams(next, { replace });
  }
  useEffect(() => { setQuery(search); }, [search]);
  useEffect(() => { setPageInput(String(page)); }, [page]);
  useEffect(() => {
    if (total !== undefined && offset > 0 && offset >= total) {
      const next = new URLSearchParams(params); next.set('offset', String(Math.max(0, Math.ceil(total / limit) - 1) * limit));
      setParams(next, { replace: true });
    }
  }, [total, offset, limit, params, setParams]);
  function find(event: FormEvent) { event.preventDefault(); change({ offset: '', search: query }); }
  return <section className="message-list" aria-label="Customer messages">
    <div className="inbox-toolbar"><form className="message-search" onSubmit={find}><label className="sr-only" htmlFor="message-search">Search messages</label><input id="message-search" maxLength={200} placeholder="Search message text" value={query} onChange={e => setQuery(e.target.value)} /><button aria-label="Search messages"><Search size={17} /></button></form>
      <div className="message-filters"><label htmlFor="message-view">Message view</label><select id="message-view" value={view} onChange={e => change({ view: e.target.value, offset: '' })}><option value="all">All messages</option><option value="attention">Needs attention</option><option value="ready">Ready responses</option><option value="processing">Processing</option><option value="failed">Failed</option></select>{(view !== 'all' || search) && <button onClick={() => change({ view: '', search: '', offset: '' })}>Clear filters</button>}</div></div>
    {list.error && <div className="section-padding"><p role="alert" className="error">{list.error}</p><button onClick={list.refresh}>Try again</button></div>}
    {!list.data && !list.error && <p className="section-padding" role="status">Loading messages…</p>}
    {list.data && <><div className="message-count" role="status">{list.data.total.toLocaleString()} messages{search && ` matching “${search}”`}</div>
      <div className="message-table-scroll" role="region" aria-label="Message results" tabIndex={0}><table className="message-table"><caption className="sr-only">Customer messages, newest first</caption><thead><tr><th scope="col">Message</th><th scope="col">Status</th><th scope="col">Language</th><th scope="col">Received</th></tr></thead><tbody>{list.data.items.map(message => <tr key={message.id}>
        <td><Link className="message-preview" lang={message.language} to={`/w/${workspace.id}/runs/${message.run_id}${params.size ? `?${params}` : ''}`}>{message.original}</Link></td>
        <td><span className={`run-state ${message.state}`}>{message.state === 'completed' && message.outcome ? outcomeLabel(message.outcome) : stateLabel(message.state)}</span>{message.error_code && <span className="message-error">{message.error_code}</span>}</td>
        <td>{languageLabel(message.language)}</td><td><time dateTime={message.created_at}>{new Date(message.created_at).toLocaleString()}</time></td>
      </tr>)}</tbody></table></div>
      {!list.data.items.length && <div className="inbox-empty"><Inbox size={26} /><h2>{search || view !== 'all' ? 'No matching messages' : 'Your inbox is ready'}</h2><p>{search || view !== 'all' ? 'Try another view or clear the filters.' : 'Add a customer message to prepare an evidence-based response.'}</p></div>}
      <div className="list-pagination"><label>Rows per page <select value={limit} onChange={e => change({ limit: e.target.value, offset: '' })}><option value="20">20</option><option value="50">50</option></select></label>
        <span>{total ? `${offset + 1}–${Math.min(offset + limit, total)} of ${total.toLocaleString()}` : '0 results'}</span>
        <div className="page-controls"><button disabled={!offset} onClick={() => change({ offset: '' })}>First</button><button disabled={!offset} onClick={() => change({ offset: String(Math.max(0, offset - limit)) })}>Previous</button>
          <form onSubmit={event => { event.preventDefault(); const next = Number(pageInput); if (Number.isInteger(next) && next >= 1 && next <= pages) change({ offset: String((next - 1) * limit) }); }}><label>Page <input type="number" min={1} max={pages} value={pageInput} onChange={e => setPageInput(e.target.value)} required /></label><span>of {pages.toLocaleString()}</span><button>Go</button></form>
          <button disabled={offset + limit >= list.data.total} onClick={() => change({ offset: String(offset + limit) })}>Next</button><button disabled={page >= pages} onClick={() => change({ offset: String((pages - 1) * limit) })}>Last</button></div>
      </div></>}
  </section>;
}
