import { useRef, useState, type FormEvent } from 'react';
import { UploadCloud } from 'lucide-react';
import { api } from '../../api/client';
import type { UploadResult } from './types';

export function Upload({ workspaceId, documentId, onUploaded }: { workspaceId: string; documentId?: string; onUploaded: (value: UploadResult) => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const key = useRef(crypto.randomUUID());
  async function submit(event: FormEvent) {
    event.preventDefault(); const form = event.currentTarget as HTMLFormElement;
    if (!file || pending) return;
    if (file.size > 5 * 1024 * 1024) { setError('Choose a document smaller than 5 MiB.'); return; }
    setPending(true); setError('');
    const body = new FormData(); body.append('file', file);
    if (documentId) body.append('document_id', documentId);
    try {
      const result = await api<UploadResult>(`/workspaces/${workspaceId}/documents`, { method: 'POST', body, headers: { 'Idempotency-Key': key.current } });
      key.current = crypto.randomUUID(); setFile(null); form.reset(); onUploaded(result);
    } catch (err) { setError((err as Error).message); }
    finally { setPending(false); }
  }
  return <form onSubmit={submit} className="upload-box">
    <div><UploadCloud size={23} /><h2>{documentId ? 'Upload a replacement' : 'Add company knowledge'}</h2>
      <p className="muted">TXT or Markdown · UTF-8 · up to 5 MiB</p></div>
    <label className="file-picker">Choose document<input aria-label={documentId ? 'Replacement document' : 'Knowledge document'} type="file" accept=".txt,.md" disabled={pending}
      onChange={e => { setFile(e.target.files?.[0] ?? null); key.current = crypto.randomUUID(); setError(''); }} /></label>
    <button className="primary" disabled={!file || pending}>{pending ? 'Uploading…' : documentId ? 'Upload replacement' : 'Upload document'}</button>
    {error && <p className="error" role="alert">{error}</p>}
  </form>;
}
