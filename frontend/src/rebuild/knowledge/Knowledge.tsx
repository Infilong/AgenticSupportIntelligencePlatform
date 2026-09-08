import { useEffect, useState, type FormEvent } from "react";
import { errorMessage, type DocumentDetail, type DocumentPage, type WorkspaceApi } from "../api";
import { DocumentEditor } from "./DocumentEditor";
import { DocumentVersionView } from "./DocumentVersionView";

const statuses: Record<string, string> = { indexed: "Ready", pending: "Waiting", indexing: "Processing", failed: "Failed" };
export function Knowledge({ api, canWrite, canDelete }: {
  api: WorkspaceApi; canWrite: boolean; canDelete: boolean;
}) {
  const [page, setPage] = useState<DocumentPage | null>(null);
  const [search, setSearch] = useState("");
  const [offset, setOffset] = useState(0);
  const [revision, setRevision] = useState(0);
  const [selected, setSelected] = useState("");
  const [adding, setAdding] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [location, setLocation] = useState(() => window.location.hash);
  useEffect(() => {
    const update = () => setLocation(window.location.hash);
    window.addEventListener("hashchange", update);
    return () => window.removeEventListener("hashchange", update);
  }, []);
  const params = new URLSearchParams(location.split("?")[1]);
  const version = Number(params.get("version"));
  const versionDocument = params.get("document");
  useEffect(() => {
    let current = true;
    setPage(null); setError("");
    api.documents(search, offset).then(result => { if (current) setPage(result); })
      .catch(error => { if (current) setError(errorMessage(error)); });
    return () => { current = false; };
  }, [api, search, offset, revision]);
  function refresh(message: string) { setNotice(message); setRevision(value => value + 1); }
  function find(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setOffset(0);
    setSearch(String(new FormData(event.currentTarget).get("search")).trim());
    setRevision(value => value + 1);
  }
  return <>
    <header className="page-header"><div><p className="eyebrow">Your team's sources</p><h1>Knowledge</h1>
      <p className="muted">Keep the information your agents rely on accurate and up to date.</p></div>
      {canWrite && !adding && <button className="primary" onClick={() => { setAdding(true); setSelected(""); }}>Add knowledge</button>}
    </header>
    {notice && <p role="status" className="notice">{notice}</p>}
    {versionDocument && Number.isSafeInteger(version) && version > 0 &&
      <DocumentVersionView api={api} id={versionDocument} version={version} />}
    {adding && <DocumentEditor onCancel={() => setAdding(false)} onSave={async (title, content, language) => {
      const result = await api.addDocument(title, content, language);
      setAdding(false); refresh(result.document.status === "indexed" ? "Document is ready to use." : "Document added. Check its processing status.");
    }} />}
    {selected && <DocumentView key={selected} api={api} id={selected} canWrite={canWrite} canDelete={canDelete}
      onClose={() => setSelected("")} onChange={refresh} />}
    <section className="panel" aria-label="Knowledge documents">
      <form className="search" onSubmit={find}><label className="grow">Search documents
        <input name="search" type="search" placeholder="Search by title" /></label><button>Search</button>
        <button type="button" onClick={() => setRevision(value => value + 1)}>Refresh</button></form>
      {error ? <p role="alert" className="error">{error}</p> : !page ? <p role="status">Loading documents…</p>
        : !page.items.length ? <div className="empty-state"><h2>{search ? "No matching documents" : "No documents here yet"}</h2>
          <p>{search ? "Try another search." : canWrite ? "Add a policy, guide, or support article to get started." : "An administrator can add knowledge for your team."}</p></div>
        : <><div className="table-scroll"><table><thead><tr><th>Document</th><th>Status</th><th>Language</th><th>Updated</th></tr></thead>
          <tbody>{page.items.map(document => <tr key={document.id}>
            <td><button className="text-button" onClick={() => { setSelected(document.id); setAdding(false); }}>{document.title}</button>
              {document.error_message && <p className="error">{document.error_message}</p>}</td>
            <td><span className={`status ${document.status}`}>{statuses[document.status] ?? document.status}</span></td>
            <td>{document.language.toUpperCase()}</td><td>{new Date(document.updated_at).toLocaleDateString()}</td>
          </tr>)}</tbody></table></div>
          <footer className="pagination"><span>{offset + 1}–{offset + page.items.length} of {page.total}</span>
            <button disabled={offset === 0} onClick={() => setOffset(value => Math.max(0, value - 20))}>Previous</button>
            <button disabled={!page.has_next} onClick={() => setOffset(value => value + 20)}>Next</button></footer></>}
    </section>
  </>;
}

function DocumentView({ api, id, canWrite, canDelete, onClose, onChange }: {
  api: WorkspaceApi; id: string; canWrite: boolean; canDelete: boolean;
  onClose: () => void; onChange: (message: string) => void;
}) {
  const [detail, setDetail] = useState<DocumentDetail | null>(null);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [busy, setBusy] = useState(false);
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    let current = true; setError("");
    api.document(id).then(result => { if (current) setDetail(result); })
      .catch(error => { if (current) setError(errorMessage(error)); });
    return () => { current = false; };
  }, [api, id, revision]);
  if (editing && detail) return <DocumentEditor initial={{ title: detail.document.title,
    content: detail.latest_version?.raw_text ?? "", language: detail.document.language }} onCancel={() => setEditing(false)}
    onSave={async (title, content, language) => {
      await api.reindex(id, title, content, language); setEditing(false); setRevision(value => value + 1);
      onChange("Document updated. Check its processing status.");
    }} />;
  async function remove() {
    setBusy(true); setError("");
    try { await api.remove(id); onChange("Document removed."); onClose(); }
    catch (error) { setError(errorMessage(error)); }
    finally { setBusy(false); }
  }
  return <section className="panel" aria-label="Document details"><div className="page-header">
    <h2>{detail?.document.title ?? "Document"}</h2><button onClick={onClose}>Close</button></div>
    {error && <p className="error" role="alert">{error} <button onClick={() => setRevision(value => value + 1)}>Retry</button></p>}
    {!detail && !error && <p role="status">Loading document…</p>}
    {detail && <><p className="muted">{statuses[detail.document.status] ?? detail.document.status} · Version {detail.latest_version?.version ?? "unavailable"}</p>
      {detail.document.error_message && <p className="error">{detail.document.error_message}</p>}
      <pre className="document-content">{detail.latest_version?.raw_text ?? "No document content is available."}</pre>
      <div className="actions">{canWrite && <button onClick={() => setEditing(true)}>
        {detail.document.status === "failed" ? "Edit and retry" : "Edit document"}</button>}
        {canDelete && <button className="danger" onClick={() => setConfirmDelete(true)}>Remove document</button>}</div>
      {confirmDelete && <div className="confirmation"><p>Remove “{detail.document.title}” from your workspace knowledge?</p>
        <button className="danger" disabled={busy} onClick={() => void remove()}>{busy ? "Removing…" : "Confirm removal"}</button>
        <button disabled={busy} onClick={() => setConfirmDelete(false)}>Keep document</button></div>}
    </>}
  </section>;
}
