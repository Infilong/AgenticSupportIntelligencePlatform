import { useEffect, useState } from "react";
import { errorMessage } from "../api";
import type { TaskAction, WorkApi } from "./api";

export function TaskActions({ api, runId, canResolve = false, refreshToken = "", onPendingChange }: {
  api: WorkApi; runId: string; canResolve?: boolean; refreshToken?: string;
  onPendingChange?: (pending: boolean) => void;
}) {
  const [actions, setActions] = useState<TaskAction[] | null>(null);
  const [error, setError] = useState(""); const [revision, setRevision] = useState(0);
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    let current = true; setError(""); onPendingChange?.(true);
    api.actions(runId).then(items => {
      if (current) { setActions(items); onPendingChange?.(items.some(item => item.status === "pending")); }
    }).catch(error => { if (current) setError(errorMessage(error)); });
    return () => { current = false; };
  }, [api, runId, revision, refreshToken, onPendingChange]);
  async function resolve(action: TaskAction, decision: "approve" | "reject", reason: string) {
    setBusy(true); setError("");
    try {
      const result = await api.resolveAction(action, decision, reason);
      setActions(previous => {
        const next = previous?.map(item => item.id === result.id ? result : item) ?? [result];
        return next;
      });
      setRevision(value => value + 1);
    } catch (error) { setError(errorMessage(error)); }
    finally { setBusy(false); }
  }
  if (actions?.length === 0 && !error) return null;
  const content = <>
    {!actions && !error && <p role="status">Loading task actions…</p>}
    {error && <p role="alert">{error} <button type="button" onClick={() => setRevision(value => value + 1)}>Refresh actions</button></p>}
    {actions?.map(action => <ActionItem key={action.id} action={action} busy={busy}
      canResolve={canResolve} resolve={resolve} />)}
  </>;
  return <section aria-label={canResolve ? "Proposed task actions" : "Task action records"}>
    {canResolve ? <><h3>Proposed task actions</h3>{content}</> :
      <details><summary>Task actions ({actions?.length ?? 0})</summary>{content}</details>}
  </section>;
}

function ActionItem({ action, busy, canResolve, resolve }: {
  action: TaskAction; busy: boolean; canResolve: boolean;
  resolve: (action: TaskAction, decision: "approve" | "reject", reason: string) => Promise<void>;
}) {
  const [reason, setReason] = useState("");
  const label = action.inputs.action === "set_category" ? "category" : "note";
  return <article className="call-record" aria-label={`Task ${label}`}>
    <h4>{label === "category" ? "Set task category" : "Add internal note"}</h4>
    <p className="answer-text">{action.inputs.value}</p>
    <p>{action.status === "pending" ? "Awaiting approval — no change applied" : action.status === "applied"
      ? action.result?.reused ? "Already applied in an earlier attempt" : "Applied" : "Rejected — no change applied"}</p>
    {action.reason && <p>{action.reason}</p>}
    {action.resolved_at && <p className="muted">Resolved {new Date(action.resolved_at).toLocaleString()}</p>}
    {canResolve && action.status === "pending" && <>
      <label>Reason to reject {label}<input maxLength={2000} value={reason} disabled={busy}
        onChange={event => setReason(event.target.value)} /></label>
      <div className="actions"><button type="button" disabled={busy} onClick={() => void resolve(action, "approve", "")}>Approve {label}</button>
        <button type="button" disabled={busy || !reason.trim()} onClick={() => void resolve(action, "reject", reason.trim())}>Reject {label}</button></div>
    </>}
  </article>;
}
