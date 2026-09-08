import { useRef, useState, type FormEvent } from "react";
import { errorMessage } from "../api";
import type { RecordDetail, RecordsApi } from "./api";

export function RecordActions({ api, record, onUpdated }: {
  api: RecordsApi; record: RecordDetail; onUpdated: () => void;
}) {
  const [reply, setReply] = useState(""); const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const submission = useRef<{ reply: string; key: string } | null>(null);
  async function clarify(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError("");
    const text = reply.trim();
    if (submission.current?.reply !== text) submission.current = { reply: text, key: crypto.randomUUID() };
    try { await api.clarify(record.id, record.latest_run_id, text, submission.current.key); setReply(""); onUpdated(); }
    catch (error) { setError(errorMessage(error)); } finally { setBusy(false); }
  }
  async function stop() {
    setBusy(true); setError("");
    try { await api.stop(record.latest_run_id); onUpdated(); }
    catch (error) { setError(errorMessage(error)); } finally { setBusy(false); }
  }
  return <section aria-label="Record actions">
    {record.status === "awaiting_clarification" && <form onSubmit={clarify}>
      <label>Additional information<textarea value={reply} onChange={event => setReply(event.target.value)}
        required maxLength={2000} disabled={busy} /></label>
      <button className="primary" disabled={busy || !reply.trim()}>Continue processing</button></form>}
    {["queued", "running", "needs_human_review", "awaiting_clarification"].includes(record.status) &&
      <p><button onClick={() => void stop()} disabled={busy}>Stop processing</button></p>}
    {record.status === "stopping" && <p role="status">Stopping after the active step. Completed actions cannot be undone.</p>}
    {busy && <p role="status">Saving your action…</p>}
    {error && <p role="alert" className="error">{error}</p>}
  </section>;
}
