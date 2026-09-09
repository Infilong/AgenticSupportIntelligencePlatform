import { useEffect, useState, type FormEvent } from 'react';
import { api } from '../../api/client';
import type { Handoff } from './types';

export function DevelopmentResponse({ path, onSubmitted }: { path: string; onSubmitted: () => void }) {
  const [handoff, setHandoff] = useState<Handoff | null>(null);
  const [sourceId, setSourceId] = useState('');
  const [quote, setQuote] = useState('');
  const [answer, setAnswer] = useState('');
  const [error, setError] = useState('');
  const [pending, setPending] = useState(false);
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    const controller = new AbortController(); setError('');
    api<Handoff>(`${path}/development-handoff`, { signal: controller.signal }).then(setHandoff).catch(err => { if (!controller.signal.aborted) setError(err.message); });
    return () => controller.abort();
  }, [path, revision]);
  const source = handoff?.context.sources.find(item => item.chunk_id === sourceId);
  async function submit(event: FormEvent) {
    event.preventDefault(); if (!handoff || pending || !source || !quote.trim() || !answer.trim()) return;
    setPending(true); setError('');
    try {
      await api(`${path}/development-handoff/${handoff.id}`, { method: 'POST', body: JSON.stringify({ context_hash: handoff.context_hash, answer, citations: [{ chunk_id: sourceId, quote }] }) });
      onSubmitted();
    } catch (err) { setError((err as Error).message); }
    finally { setPending(false); }
  }
  return <div className="development-form"><p className="muted">Use the retrieved evidence below to contribute a development answer. Submitting creates an unverified draft; it does not approve a customer response.</p>
    {error && <p className="error" role="alert">{error}</p>}
    {!handoff ? error ? <button onClick={() => setRevision(x => x + 1)}>Reload evidence</button> : <p role="status">Loading authorized evidence…</p> : <form onSubmit={submit}>
      <label htmlFor="development-source">Supporting passage</label><select id="development-source" value={sourceId} required onChange={e => { setSourceId(e.target.value); setQuote(''); }}><option value="">Choose a source</option>{handoff.context.sources.map((item, index) => <option key={item.chunk_id} value={item.chunk_id}>{index + 1}. {item.title} · {item.section}</option>)}</select>
      {source && <blockquote className="source-excerpt">{source.text}</blockquote>}
      <label htmlFor="development-quote">Exact supporting quote</label><textarea id="development-quote" value={quote} rows={3} maxLength={2000} required onChange={e => setQuote(e.target.value)} />
      <label htmlFor="development-answer">Development answer</label><textarea id="development-answer" value={answer} rows={5} maxLength={8000} required onChange={e => setAnswer(e.target.value)} />
      <button className="primary" disabled={pending || !source || !source.text.includes(quote) || !quote.trim() || !answer.trim()}>{pending ? 'Submitting…' : 'Submit development draft'}</button>
    </form>}
  </div>;
}
