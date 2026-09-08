import { useState } from "react";
import { errorMessage } from "../api";
import { runStatus, type WorkApi } from "./api";
import { ReviewHistory } from "./ReviewHistory";
import { useRunTrace } from "./useRunTrace";
import { TaskActions } from "./TaskActions";
import { TaskAttempts } from "./TaskAttempts";
import { RunConfiguration } from "./RunConfiguration";

import { RunSources } from "./RunSources";

export function RunDetail({ api, id, onClose, refreshToken, canStop, onSettled, onSelectRun }: {
  api: WorkApi; id: string; onClose: () => void; refreshToken: number; canStop: boolean; onSettled: () => void;
  onSelectRun: (id: string) => void;
}) {
  const [revision, setRevision] = useState(0);
  const [stopping, setStopping] = useState(false);
  const [stopError, setStopError] = useState("");
  const { trace, taskId, taskInfo, error } = useRunTrace(api, id, revision + refreshToken, onSettled);
  async function stop() {
    setStopping(true); setStopError("");
    try { await api.stop(id); setRevision(x => x + 1); }
    catch (error) { setStopError(errorMessage(error)); }
    finally { setStopping(false); }
  }
  const elapsed = trace?.run.completed_at
    ? Math.max(0, new Date(trace.run.completed_at).getTime() - new Date(trace.run.created_at).getTime()) : null;
  return <section className="panel" aria-label="Run details">
    <div className="page-header"><h2>Execution record</h2><div className="actions">
      <button onClick={() => setRevision(value => value + 1)}>Refresh record</button><button onClick={onClose}>Close record</button>
    </div></div>
    {error && <p role="alert" className="error">{error}</p>}
    {stopError && <p role="alert" className="error">{stopError}</p>}
    {!trace && !error && <p role="status">Loading execution record…</p>}
    {trace && <><span className="status">{runStatus(trace.run.status, trace.run.route_decision)}</span>
      {canStop && taskId && ["queued", "running", "needs_human_review"].includes(trace.run.status) &&
        <button disabled={stopping} onClick={() => void stop()}>{stopping ? "Requesting stop…" : "Stop run"}</button>}
      {trace.run.status === "stopping" && <p role="status">Stop requested. Waiting for the active step to finish; later steps will not run.</p>}
      {trace.run.status === "stopped" && <p>Stopped. Completed model calls may still incur charges.</p>}
      {trace.run.status === "failed" && trace.run.route_decision && <p className="error">Run ended: {trace.run.route_decision.replaceAll("_", " ")}.</p>}
      <h3>Request</h3><p className="answer-text">{trace.run.input_message}</p>
      <h3>Answer</h3><p className="answer-text">{trace.run.final_answer ?? (trace.run.status === "needs_human_review"
        ? "This request needs human review. No final answer has been published." : "No final answer is available.")}</p>
      {trace.ai_runs.some(call => call.provider.startsWith("mock")) && <p className="notice">Mock execution — this result does not verify a real AI provider.</p>}
      <RunSources trace={trace} />
      <div className="run-facts"><p>Elapsed to outcome <strong>{elapsed === null ? "Not complete" : `${(elapsed / 1000).toFixed(2)} s`}</strong></p>
        <p>Recorded step time <strong>{(trace.steps.reduce((sum, step) => sum + step.latency_ms, 0) / 1000).toFixed(2)} s</strong></p>
        <p>Tokens <strong>{trace.ai_runs.reduce((sum, call) => sum + call.total_tokens, 0)}</strong></p>
        <p>Estimated model cost <strong>${trace.ai_runs.reduce((sum, call) => sum + call.estimated_cost, 0).toFixed(6)}</strong></p></div>
      {trace.run.route_decision?.startsWith("human_") && <p className="muted">Elapsed time includes the wait for human review. Recorded step time sums the agent's measured steps.</p>}
      <details><summary>Execution steps and model calls</summary>
        <ol>{trace.steps.map(step => <li key={step.id}><strong>{step.step_name.replaceAll("_", " ")}</strong>
          <p className="muted">{step.status} · {step.latency_ms} ms</p>
          {step.error_message && <p className="error">{step.error_message}</p>}
          {step.tool_calls.map(tool => <p key={tool.id}>Tool: {tool.tool_name} · {tool.status} · {tool.latency_ms} ms</p>)}
        </li>)}</ol>
        {trace.ai_runs.map(call => <div key={call.id} className="call-record"><strong>{call.model}</strong>
          <p>{call.provider} · {call.purpose} · {call.status}</p>
          <p>{call.total_tokens} tokens · {call.latency_ms} ms model latency · ${call.estimated_cost.toFixed(6)} estimated</p>
          {call.error_message && <p className="error">{call.error_message}</p>}</div>)}
      </details>
      {trace.guardrails.some(item => !item.passed) && <details><summary>Issues requiring attention</summary>
        {trace.guardrails.filter(item => !item.passed).map(item => <p key={item.id}>{item.message}</p>)}</details>}
      <ReviewHistory trace={trace} />
      {taskId && <RunConfiguration api={api} id={id} />}
      <details><summary>Run context</summary>
        <p>Initiating user ID: {trace.run.user_id ?? "Unavailable"}</p>
        <p>Agent ID: {trace.run.agent_config_id ?? "Unavailable"}</p>
        <p>Trace ID: {trace.run.trace_id ?? "Unavailable"}</p>
        <p>Created: {new Date(trace.run.created_at).toLocaleString()}</p>
        <p>Completed: {trace.run.completed_at ? new Date(trace.run.completed_at).toLocaleString() : "Not complete"}</p>
      </details>
      <TaskActions api={api} runId={id} refreshToken={`${revision}:${refreshToken}:${trace.run.status}`} />
      {taskId && <TaskAttempts api={api} run={trace.run} current={taskInfo} canRun={canStop} onSelect={onSelectRun} revision={revision + refreshToken} />}
      <p className="muted">Run {trace.run.id} · {new Date(trace.run.created_at).toLocaleString()}</p>
    </>}
  </section>;
}
