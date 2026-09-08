import { useEffect, useState } from "react";
import { errorMessage, type WorkspaceApi } from "../api";

export function DocumentVersionView({ api, id, version }: { api: WorkspaceApi; id: string; version: number }) {
  const [saved, setSaved] = useState<Awaited<ReturnType<WorkspaceApi["version"]>> | null>(null);
  const [error, setError] = useState("");
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    let current = true; setSaved(null); setError("");
    api.version(id, version).then(result => { if (current) setSaved(result); })
      .catch(error => { if (current) setError(errorMessage(error)); });
    return () => { current = false; };
  }, [api, id, version, revision]);
  return <section className="panel" aria-label="Saved document version">
    <div className="page-header"><h2>Document version {version}</h2><a href="#knowledge">Close version</a></div>
    <p className="muted">This is the saved version referenced by the run, which may differ from current knowledge.</p>
    {error && <p role="alert">{error} <button onClick={() => setRevision(x => x + 1)}>Retry</button></p>}
    {!saved && !error && <p role="status">Loading saved version…</p>}
    {saved && <><p>Saved {new Date(saved.created_at).toLocaleString()}</p>
      <pre className="document-content">{saved.raw_text}</pre></>}
  </section>;
}
