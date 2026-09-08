import { useEffect, useRef, useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { Search } from 'lucide-react';
import { api, type Workspace } from '../../api/client';
import type { RetrievalResult } from './types';
import './knowledge.css';

export function SearchKnowledge({ workspace }: { workspace: Workspace }) {
  const [query, setQuery] = useState('');
  const [searched, setSearched] = useState('');
  const [result, setResult] = useState<RetrievalResult | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const controller = useRef<AbortController | null>(null);
  useEffect(() => () => controller.current?.abort(), []);
  async function submit(event: FormEvent) {
    event.preventDefault(); if (pending || !query.trim()) return;
    controller.current?.abort(); controller.current = new AbortController();
    setPending(true); setResult(null); setError(''); setSearched(query);
    try { setResult(await api<RetrievalResult>(`/workspaces/${workspace.id}/retrieval`, { method: 'POST', body: JSON.stringify({ query, limit: 5 }), signal: controller.current.signal })); }
    catch (err) { if (!controller.current.signal.aborted) setError((err as Error).message); }
    finally { setPending(false); }
  }
  return <><Link to={`/w/${workspace.id}/knowledge`}>← Knowledge</Link><div className="page-heading"><p className="eyebrow">FIND THE SOURCE</p><h1>Search knowledge</h1><p className="muted">Find relevant passages in your workspace’s active documents.</p></div>
    <form className="knowledge-query" onSubmit={submit}><label htmlFor="knowledge-query">What would you like to find?</label><div><input id="knowledge-query" value={query} maxLength={1000} onChange={e => setQuery(e.target.value)} placeholder="For example, when can a customer request a refund?" /><button className="primary" disabled={pending || !query.trim()}><Search size={18} />{pending ? 'Searching…' : 'Search'}</button></div></form>
    {error && <p className="error" role="alert">{error}</p>}
    {pending && <p role="status" className="muted">Searching your documents. The first query may take longer while the local model loads.</p>}
    {result && <section aria-label="Search results"><div className="knowledge-heading"><h2>{result.results.length ? 'Relevant passages' : 'No indexed sources'}</h2><span className="muted">{(result.duration_ms / 1000).toFixed(2)} s</span></div>
      <p className="searched-query">Results for “{searched}”</p>
      <p className="muted">{result.results.length ? 'These are source matches, not an AI-generated answer. Check whether they support your question.' : 'Add and index a document before searching.'}</p>
      {result.results.map((row, index) => <article className="passage-card" key={row.chunk_id}><div className="passage-heading"><span className="citation-number">{index + 1}</span><div><Link to={`/w/${workspace.id}/knowledge/${row.document_id}?version=${row.version_id}&offset=${row.start_offset}`}>{row.title}</Link><p className="muted">{row.section}</p></div></div><blockquote>{row.text}</blockquote>
        <details><summary>Source details</summary><p className="metadata">Characters {row.start_offset}–{row.end_offset} · similarity {row.cosine_similarity.toFixed(3)}<br />Version {row.version_id}</p></details></article>)}
      <details><summary>Retrieval details</summary><p className="metadata">Trace {result.trace_id}<br />Real local embeddings and PostgreSQL search. Active workspace documents only.</p></details>
    </section>}</>;
}
