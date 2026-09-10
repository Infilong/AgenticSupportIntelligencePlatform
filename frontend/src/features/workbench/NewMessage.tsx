import { useEffect, useRef, useState, type FormEvent } from 'react';
import { api, type Workspace } from '../../api/client';
import type { Created } from './types';

export function NewMessage({ workspace, onCreated, onClose }: { workspace: Workspace; onCreated: (id: string) => void; onClose: () => void }) {
  const [original, setOriginal] = useState('');
  const [language, setLanguage] = useState('auto');
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const submission = useRef({ payload: '', key: '' });
  const controller = useRef<AbortController | null>(null);
  useEffect(() => () => controller.current?.abort(), []);
  async function submit(event: FormEvent) {
    event.preventDefault(); if (pending || !original.trim()) return;
    const payload = JSON.stringify({ original, language });
    if (submission.current.payload !== payload) submission.current = { payload, key: crypto.randomUUID() };
    setPending(true); setError('');
    controller.current = new AbortController();
    const signal = controller.current.signal;
    try {
      const value = await api<Created>(`/workspaces/${workspace.id}/messages`, {
        method: 'POST', headers: { 'Idempotency-Key': submission.current.key }, body: payload, signal,
      });
      if (!signal.aborted) onCreated(value.run_id);
    } catch (err) { if (!signal.aborted) setError((err as Error).message); }
    finally { if (!signal.aborted) setPending(false); }
  }
  return <form className="message-composer" onSubmit={submit} aria-label="New customer message">
    <h2>New message</h2><label htmlFor="customer-message">Customer message</label>
    <textarea id="customer-message" autoFocus rows={5} maxLength={1000} value={original} onChange={e => setOriginal(e.target.value)} disabled={pending} required placeholder="Paste the original question or request…" />
    <div className="composer-footer"><label htmlFor="answer-language">Response language<select id="answer-language" value={language} onChange={e => setLanguage(e.target.value)} disabled={pending}><option value="auto">Match question</option><option value="en">English</option><option value="ja">日本語</option><option value="zh">中文</option></select></label>
      <span className="muted">{original.length}/1,000</span></div>
    {error && <p className="error" role="alert">{error}</p>}
    <div className="workbench-actions"><button type="button" onClick={onClose} disabled={pending}>Cancel</button><button className="primary" disabled={pending || !original.trim()}>{pending ? 'Saving…' : 'Start processing'}</button></div>
  </form>;
}
