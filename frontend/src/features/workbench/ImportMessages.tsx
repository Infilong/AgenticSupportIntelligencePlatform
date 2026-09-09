import { useEffect, useRef, useState, type FormEvent } from 'react';
import { api, type Workspace } from '../../api/client';
import type { components } from '../../api/schema';

export function ImportMessages({ workspace, onClose, onImported }: { workspace: Workspace; onClose: () => void; onImported: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<components['schemas']['ImportResult'] | null>(null);
  const key = useRef(crypto.randomUUID());
  const controller = useRef<AbortController | null>(null);
  useEffect(() => () => controller.current?.abort(), []);
  async function submit(event: FormEvent) {
    event.preventDefault(); if (!file || pending) return;
    if (file.size > 1024 * 1024) { setError('Choose a file no larger than 1 MiB.'); return; }
    const body = new FormData(); body.set('file', file);
    setPending(true); setError(''); controller.current = new AbortController();
    const signal = controller.current.signal;
    try {
      const value = await api<components['schemas']['ImportResult']>(`/workspaces/${workspace.id}/message-imports`, { method: 'POST', body, headers: { 'Idempotency-Key': key.current }, signal });
      if (!signal.aborted) setResult(value);
    } catch (err) { if (!signal.aborted) setError((err as Error).message); }
    finally { if (!signal.aborted) setPending(false); }
  }
  if (result) return <div className="message-composer"><h2>Messages imported</h2><p role="status">{result.message_count} messages saved from {result.filename}.</p><p>Open a message to inspect its original text and start processing when you’re ready.</p><button className="primary" onClick={onImported}>View unprocessed messages</button></div>;
  return <form className="message-composer" aria-label="Import customer messages" onSubmit={submit}>
    <h2>Import messages</h2><p>Upload customer messages as UTF-8 JSONL. Each line is one message. Importing saves them without starting processing.</p>
    <label htmlFor="message-file">JSONL file</label><input id="message-file" type="file" accept=".jsonl" required disabled={pending} onChange={event => { setFile(event.target.files?.[0] ?? null); key.current = crypto.randomUUID(); setError(''); }} />
    <p className="muted">Up to 100 messages · 1 MiB · 1,000 characters per message</p>
    <details><summary>File format and example</summary><p>Use original, language (en, ja or zh), and optional labels. Labels use letters, numbers, spaces, hyphens or underscores; up to 10 per message, 32 characters each.</p><pre className="import-example">{'{"original":"What is the refund deadline?","language":"en","labels":["billing"]}\n{"original":"返金期限はいつですか？","language":"ja"}'}</pre></details>
    {error && <p role="alert" className="error">{error}</p>}
    <div className="workbench-actions"><button type="button" disabled={pending} onClick={onClose}>Cancel</button><button className="primary" disabled={pending || !file}>{pending ? 'Importing…' : 'Import messages'}</button></div>
  </form>;
}
