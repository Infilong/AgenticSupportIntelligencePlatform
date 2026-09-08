import { useEffect, useState } from "react";
import { errorMessage } from "../api";
import type { Page } from "../work/api";
import type { Artifact, RecordsApi } from "./api";
import { DataValue } from "./DataValue";

export function Artifacts({ api, id, run }: { api: RecordsApi; id: string; run: string }) {
  const [offset, setOffset] = useState(0);
  const [revision, setRevision] = useState(0);
  const [page, setPage] = useState<Page<Artifact> | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let current = true; setPage(null); setError("");
    api.artifacts(id, run, offset).then(result => { if (current) setPage(result); })
      .catch(error => { if (current) setError(errorMessage(error)); });
    return () => { current = false; };
  }, [api, id, run, offset, revision]);
  return <section aria-label="Saved artifacts"><div className="actions"><h3>Saved artifacts</h3>
    <button onClick={() => setRevision(x => x + 1)}>Refresh artifacts</button></div>
    <p className="muted">Intermediate outputs saved during processing.</p>
    {error && <p role="alert">{error}</p>}
    {!page && !error && <p role="status">Loading artifacts…</p>}
    {page?.items.map(item => <details key={item.step_id}><summary>{item.kind.replaceAll("_", " ")}</summary>
      {item.error ? <p role="alert">{item.error}</p> : <DataValue value={item.data} />}</details>)}
    {page?.total === 0 && <p>No artifacts have been saved yet.</p>}
    {page && <footer className="pagination"><span>{page.total} artifacts</span>
      <button disabled={!offset} onClick={() => setOffset(x => Math.max(0, x - 20))}>Previous artifacts</button>
      <button disabled={!page.has_next} onClick={() => setOffset(x => x + 20)}>Next artifacts</button></footer>}
  </section>;
}
