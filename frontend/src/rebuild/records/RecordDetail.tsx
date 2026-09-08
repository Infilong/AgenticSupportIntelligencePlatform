import { useEffect, useRef, useState } from "react";
import { runStatus } from "../work/api";
import { RunSources } from "../work/RunSources";
import type { RecordsApi } from "./api";
import { useRecordDetail } from "./useRecords";
import { Artifacts } from "./Artifacts";
import { DataValue } from "./DataValue";
import { RecordActions } from "./RecordActions";
import { RecordReview } from "./RecordReview";
import type { WorkApi } from "../work/api";
import { TaskAttempts } from "../work/TaskAttempts";

export function RecordDetail({ api, id, onClose, canRun, canResolve, actions }: {
  api: RecordsApi; id: string; onClose: () => void; canRun: boolean; canResolve: boolean; actions: WorkApi;
}) {
  const [view, setView] = useState("Overview");
  const [revision, setRevision] = useState(0);
  const [runId, setRunId] = useState("");
  const { record, trace, error } = useRecordDetail(api, id, revision, runId);
  const current = record && trace ? { ...record, latest_run_id: trace.run.id, status: trace.run.status } : null;
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => { if (record) heading.current?.focus(); }, [record?.id]);
  return <section className="record-detail" aria-label="Selected record">
    <div className="actions"><button onClick={onClose}>Back to records</button>
      <button onClick={() => setRevision(x => x + 1)}>Refresh record</button></div>
    {error && <p role="alert" className="error">{error}</p>}
    {!record && !error && <p role="status">Loading record…</p>}
    {record && trace && current && <><header><p className="muted">Received {new Date(record.received_at).toLocaleString()}</p>
      <h2 ref={heading} tabIndex={-1}>Record details</h2><span className={`status ${current.status}`}>{runStatus(current.status)}</span>
      {trace.run.id !== record.latest_run_id && <p>Viewing an earlier attempt. <button onClick={() => setRunId("")}>Open latest attempt</button></p>}
      <p className="muted">{record.attempt_count} {record.attempt_count === 1 ? "attempt" : "attempts"} · Source: {record.input.source}</p></header>
      <nav className="record-tabs" aria-label="Record views">{["Overview", "Processing", "Artifacts"].map(name =>
        <button key={name} aria-pressed={view === name} onClick={() => setView(name)}>{name}</button>)}</nav>
      {view === "Overview" && <><h3>{current.status === "awaiting_clarification" ? "More information needed" : "Result"}</h3>
        <p className="answer-text">{trace.run.final_answer ?? (current.status === "needs_human_review"
          ? "An administrator needs to review this attempt." : "No final result is available yet.")}</p>
        {canRun && <RecordActions key={`actions-${current.latest_run_id}`} api={api} record={current} onUpdated={() => { setRunId(""); setRevision(x => x + 1); }} />}
        {canResolve && current.status === "needs_human_review" && <RecordReview key={`review-${current.latest_run_id}`}
          api={api} actions={actions} id={id} run={current.latest_run_id} onUpdated={() => setRevision(x => x + 1)} />}
        {trace.ai_runs.some(call => call.provider.startsWith("mock")) && <p className="notice">Demo model execution — real AI quality has not been verified.</p>}
        <TaskAttempts api={actions} run={trace.run} current={null} canRun={canRun && trace.run.id === record.latest_run_id}
          revision={revision} onSelect={next => { setRunId(next); setRevision(x => x + 1); }} />
        <RunSources trace={trace} /><h3>Original input</h3><DataValue value={record.input.content} />
        {record.input.source_reference && <p>Source reference: {record.input.source_reference}</p>}</>}
      {view === "Processing" && <><h3>Processing timeline</h3><ol className="processing-timeline">{trace.steps.map(step =>
        <li key={step.id}><strong>{step.step_name.replaceAll("_", " ")}</strong><p>{step.status} · {step.latency_ms} ms</p>
          {step.error_message && <p className="error">{step.error_message}</p>}
          {step.tool_calls.map(tool => <p key={tool.id}>{tool.tool_name} · {tool.status} · {tool.latency_ms} ms</p>)}</li>)}</ol>
        <h3>Model calls</h3>{trace.ai_runs.length === 0 && <p>No model calls recorded.</p>}
        {trace.ai_runs.map(call => <article className="call-record" key={call.id}><strong>{call.provider} / {call.model}</strong>
          <p>{call.purpose} · {call.status} · {call.latency_ms} ms</p><p>{call.total_tokens} tokens · ${call.estimated_cost.toFixed(6)} estimated</p>
          {call.error_message && <p className="error">{call.error_message}</p>}</article>)}</>}
      {view === "Artifacts" && <Artifacts key={current.latest_run_id} api={api} id={id} run={current.latest_run_id} />}
    </>}
  </section>;
}
