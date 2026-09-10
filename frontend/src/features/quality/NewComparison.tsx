import { useEffect, useRef, useState, type FormEvent } from 'react';
import { api, type Workspace } from '../../api/client';

export function NewComparison({ workspace, onCreated, onBusy }: { workspace: Workspace; onCreated: (id: string) => void; onBusy: (busy: boolean) => void }) {
  const [question, setQuestion] = useState('');
  const [language, setLanguage] = useState(workspace.default_language);
  const [mode, setMode] = useState('manual');
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const request = useRef({ body: '', key: '' });
  const controller = useRef<AbortController | null>(null);
  useEffect(() => () => controller.current?.abort(), []);
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (pending || !question.trim()) return;
    const body = JSON.stringify({ original: question, language, ...(mode === 'local_ollama' ? { generation_mode: mode } : {}) });
    if (request.current.body !== body) request.current = { body, key: crypto.randomUUID() };
    controller.current = new AbortController();
    const signal = controller.current.signal;
    setPending(true); onBusy(true); setError('');
    try {
      const result = await api<{ id: string }>(`/workspaces/${workspace.id}/comparisons`, {
        method: 'POST', body, headers: { 'Idempotency-Key': request.current.key }, signal,
      });
      if (!signal.aborted) onCreated(result.id);
    } catch (err) { if (!signal.aborted) setError((err as Error).message); }
    finally { if (!signal.aborted) { setPending(false); onBusy(false); } }
  }
  return <form className="comparison-create inbox-panel section-padding" onSubmit={submit}>
    <h3>Start a comparison</h3>
    <label htmlFor="comparison-question">Question to compare</label>
    <textarea id="comparison-question" value={question} onChange={event => setQuestion(event.target.value)} rows={3} maxLength={1000} required disabled={pending} />
    <label htmlFor="comparison-language">Answer language</label>
    <select id="comparison-language" value={language} onChange={event => setLanguage(event.target.value as typeof language)} disabled={pending}><option value="en">English</option><option value="ja">日本語</option><option value="zh">中文</option></select>
    <label htmlFor="comparison-mode">Answer provider</label>
    <select id="comparison-mode" value={mode} onChange={event => setMode(event.target.value)} disabled={pending}><option value="manual">Manual development contribution</option><option value="local_ollama">Configured local model</option></select>
    <p className="muted">Runs the same question through four paths. Local mode generates answers automatically when enabled on the server. Manual mode uses attributed contributions through the CLI.</p>
    {error && <p className="error" role="alert">{error}</p>}
    <button className="primary" disabled={pending || !question.trim()}>{pending ? 'Starting comparison…' : 'Start comparison'}</button>
  </form>;
}
