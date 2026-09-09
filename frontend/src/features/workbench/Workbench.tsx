import { Plus } from 'lucide-react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import type { Workspace } from '../../api/client';
import { ImportMessages } from './ImportMessages';
import { SavedMessage } from './SavedMessage';
import { NewMessage } from './NewMessage';
import { RunView } from './RunView';
import { MessageInbox } from './MessageInbox';
import './workbench.css';

export function Workbench({ workspace }: { workspace: Workspace }) {
  const { runId, messageId } = useParams();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const composing = params.get('compose') === '1' && !runId && !messageId && workspace.role !== 'viewer';
  const importing = params.get('import') === '1' && !runId && !messageId && workspace.role !== 'viewer';
  const inboxParams = new URLSearchParams(params); inboxParams.delete('compose'); inboxParams.delete('import');
  const search = inboxParams.size ? `?${inboxParams}` : '';
  const base = `/w/${workspace.id}`;
  // The inbox remounts and fetches current results on return; hidden lists do not poll.
  return <><div className="workbench-heading"><div><p className="eyebrow">CUSTOMER SUPPORT</p><h1>Workbench</h1><p className="muted">Review messages, inspect processing and manage the next step.</p></div>
    {workspace.role !== 'viewer' && !composing && !importing && <div className="workbench-actions"><button onClick={() => { const next = new URLSearchParams(inboxParams); next.set('import', '1'); navigate(`${base}?${next}`); }}>Import</button><button className="primary" onClick={() => { const next = new URLSearchParams(inboxParams); next.set('compose', '1'); navigate(`${base}?${next}`); }}><Plus size={17} />New message</button></div>}</div>
    <div className="workbench-grid">
      {importing ? <section className="message-detail" aria-label="Import messages"><ImportMessages workspace={workspace} onClose={() => navigate(`${base}${search}`)} onImported={() => navigate(`${base}?view=unprocessed`)} /></section> : messageId ? <section className="message-detail" aria-label="Selected message"><SavedMessage key={`${workspace.id}/${messageId}`} workspace={workspace} messageId={messageId} /></section> : composing ? <section className="message-detail" aria-label="New message"><NewMessage key={workspace.id} workspace={workspace} onClose={() => navigate(`${base}${search}`)} onCreated={id => navigate(`${base}/runs/${id}${search}`)} /></section>
        : runId ? <section className="message-detail" aria-label="Selected message"><RunView key={`${workspace.id}/${runId}`} workspace={workspace} runId={runId} /></section>
          : <MessageInbox workspace={workspace} />}
    </div></>;
}
