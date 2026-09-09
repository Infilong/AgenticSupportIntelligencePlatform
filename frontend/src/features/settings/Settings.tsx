import { useEffect, useRef, useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { api, type Workspace } from '../../api/client';
import type { components } from '../../api/schema';
import { useResource } from '../workbench/useResource';
import './settings.css';

type Config = components['schemas']['WorkspaceSettings'];
export function Settings({ workspace, onChange }: { workspace: Workspace; onChange: () => void }) {
  if (workspace.role !== 'admin') return <section className="empty-state"><h1>Administrator access required</h1><p>Your role does not allow workspace settings.</p></section>;
  return <SettingsForm workspace={workspace} onChange={onChange} />;
}

function SettingsForm({ workspace, onChange }: { workspace: Workspace; onChange: () => void }) {
  const path = `/workspaces/${workspace.id}/settings`;
  const config = useResource<Config>(path);
  const [language, setLanguage] = useState<string | null>(null);
  const [pending, setPending] = useState(false); const [error, setError] = useState('');
  const controller = useRef<AbortController | null>(null);
  useEffect(() => () => controller.current?.abort(), []);
  async function save(event: FormEvent) {
    event.preventDefault(); if (pending || !language) return;
    controller.current = new AbortController(); const signal = controller.current.signal;
    setPending(true); setError('');
    try {
      await api<Config>(path, { method: 'PUT', body: JSON.stringify({ default_language: language }), signal });
      if (!signal.aborted) onChange();
    } catch (err) { if (!signal.aborted) setError((err as Error).message); }
    finally { if (!signal.aborted) setPending(false); }
  }
  return <><div className="page-heading"><p className="eyebrow">WORKSPACE ADMINISTRATION</p><h1>Settings</h1><p className="muted">Processing preferences, provider configuration and people.</p></div>
    {config.error && <div><p role="alert" className="error">{config.error}</p><button onClick={config.refresh}>Try again</button></div>}
    {!config.data && !config.error && <p role="status">Loading settings…</p>}
    {config.data && <div className="settings-stack"><section className="inbox-panel section-padding"><h2>Processing defaults</h2><form onSubmit={save}>
      <label htmlFor="default-language">Default response language</label><select id="default-language" value={language ?? config.data.default_language} onChange={event => setLanguage(event.target.value)} disabled={pending}><option value="en">English</option><option value="ja">日本語</option><option value="zh">中文</option></select>
      <p className="muted">Preselects the language for new manual messages. Each message can override it; existing messages and imports keep their language.</p>
      {error && <p role="alert" className="error">{error}</p>}<button className="primary" disabled={pending || language === null || language === config.data.default_language}>{pending ? 'Saving…' : 'Save defaults'}</button>
    </form></section>
    <section className="inbox-panel section-padding"><h2>AI configuration</h2><dl className="configuration-list"><dt>Response generation</dt><dd>Attributed development responses</dd><dt>Automatic response API</dt><dd>{config.data.automatic_generation_available ? 'Available' : 'Not configured'}</dd><dt>Retrieval</dt><dd>Real local embeddings and reranking</dd><dt>Embedding model</dt><dd>{config.data.embedding_model}</dd><dt>Reranker</dt><dd>{config.data.reranker_model}</dd></dl><p className="muted">An administrator supplies development drafts from retrieved evidence. No external generation API or billing has been verified. Local compute still uses this computer’s resources.</p><details><summary>Model revisions</summary><p className="model-revision">Embedding: {config.data.embedding_revision}<br />Reranker: {config.data.reranker_revision}</p></details></section>
    <section className="inbox-panel section-padding"><h2>Workspace access</h2><p className="muted">Viewers inspect. Operators handle requests. Admins manage knowledge and access.</p><Link to={`/w/${workspace.id}/members`}>Manage members →</Link></section></div>}
  </>;
}
