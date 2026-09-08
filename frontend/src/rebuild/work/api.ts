import type { ApiRequest } from "../../app/apiRequest";
import type { Document } from "../api";

export type Agent = { id: string; name: string; active: boolean; archived_at: string | null;
  token_budget: number; settings_json: string; model_config_id: string | null };
export type Run = {
  id: string; input_message: string; final_answer: string | null; status: string;
  created_at: string; completed_at: string | null; language: string | null; route_decision: string | null;
  user_id?: string; agent_config_id?: string; trace_id?: string | null;
};
export type ModelCall = { id: string; provider: string; model: string; purpose: string;
  total_tokens: number; estimated_cost: number; latency_ms: number; status: string; error_message: string | null };
export type Trace = { run: Run; ai_runs: ModelCall[];
  steps: { id: string; step_name: string; status: string; latency_ms: number; output_json: string;
    error_message: string | null; tool_calls: { id: string; tool_name: string; status: string; latency_ms: number }[] }[];
  guardrails: { id: string; passed: boolean; message: string }[];
  checkpoints: { id: string; checkpoint_key: string; state_json: string; created_at: string }[];
};
export type Page<T> = { items: T[]; total: number; has_next: boolean };
export type Review = { id: string; graph_run_id: string; reason: string; proposed_answer: string | null;
  reviewer_display_name: string | null; reviewer_decision: string; run: { input_message: string } | null };
export type WorkApi = ReturnType<typeof workApi>;
export type AnswerLanguage = "en" | "ja" | "zh";
export type TaskConfiguration = { name: string; model_config_id: string | null; token_budget: number;
  instructions: string; knowledge_document_ids: string[] | null; allowed_actions: string[] };
export type TaskAction = { id: string; proposal_hash: string; inputs: { action: "set_category" | "add_note"; value: string };
  status: string; reason: string | null; resolved_at: string | null; reviewer_id: string | null; result?: { reused?: boolean } | null };
export type TaskRun = { task_id: string | null; run: Run; parent_run_id: string | null;
  corrected_instructions: string | null; clarification_reply?: string | null };
export type AgentModel = { id: string; provider: string; model: string; purpose: string; readiness_label: string };
export function workApi(request: ApiRequest, token: string, workspace: string) {
  const base = `/api/v1/workspaces/${encodeURIComponent(workspace)}`;
  const call = <T>(path: string, method = "GET", body?: unknown) => request<T>(base + path, { token, method, body });
  return {
    configuration: (id: string) => call<TaskConfiguration>(`/task-runs/${encodeURIComponent(id)}/configuration`),
    agents: (offset = 0, search = "") => call<Page<Agent>>(`/agents?limit=20&offset=${offset}&search=${encodeURIComponent(search)}`),
    createAgent: (name: string, token_budget: number) => call<Agent>("/agents", "POST", { name, token_budget }),
    models: (offset = 0, search = "") => call<Page<AgentModel>>(`/model-configs?limit=20&offset=${offset}&search=${encodeURIComponent(search)}`),
    knowledge: (offset = 0, search = "") => call<Page<Document>>(`/knowledge-documents?limit=20&offset=${offset}&search=${encodeURIComponent(search)}`),
    updateAgent: (id: string, settings: { name: string; instructions: string; active: boolean; token_budget: number; model_config_id: string | null; knowledge_document_ids: string[] | null; allowed_actions: string[] }) =>
      call<Agent>(`/agents/${id}`, "PATCH", settings),
    runs: (offset: number, search: string, status: string) => call<Page<Run>>(
      `/agent-runs?limit=20&offset=${offset}&search=${encodeURIComponent(search)}&status=${encodeURIComponent(status)}`),
    run: (agent_id: string, input_message: string, request_key: string, language: AnswerLanguage | null = null) =>
      call<{ task_id: string; run: Run }>("/tasks", "POST", { agent_id, input_message, request_key, language }).then(result => result.run),
    taskRun: (id: string) => call<TaskRun>(`/task-runs/${encodeURIComponent(id)}`),
    attempts: (id: string, offset = 0) => call<Page<TaskRun>>(`/task-runs/${encodeURIComponent(id)}/attempts?limit=20&offset=${offset}`),
    retry: (id: string, corrected_instructions: string, request_key: string) => call<TaskRun>(
      `/task-runs/${encodeURIComponent(id)}/retry`, "POST", { corrected_instructions, request_key }),
    stop: (id: string) => call<Run>(`/task-runs/${encodeURIComponent(id)}/stop`, "POST"),
    actions: (id: string) => call<TaskAction[]>(`/task-runs/${encodeURIComponent(id)}/actions?limit=20`),
    resolveAction: (action: TaskAction, decision: "approve" | "reject", reason: string) => call<TaskAction>(
      `/task-actions/${encodeURIComponent(action.id)}/resolve`, "POST", { expected_hash: action.proposal_hash, decision, reason }),
    trace: (id: string) => call<Trace>(`/agent-runs/${encodeURIComponent(id)}/trace`),
    reviews: (offset: number) => call<Page<Review>>(`/human-reviews?decision=pending&limit=10&offset=${offset}`),
    resolve: (id: string, decision: string, edited_answer: string, comments: string) => call<Review>(
      `/human-reviews/${id}/resolve`, "POST", { decision, edited_answer: decision === "edited" ? edited_answer : null, comments: comments || null }),
  };
}
export const runStatus = (status: string, route?: string | null) => route === "human_rejected" ? "Rejected"
  : ({ queued: "Queued", stopping: "Stopping", stopped: "Stopped", rejected: "Rejected",
    awaiting_clarification: "Awaiting clarification",
    needs_human_review: "Needs review", running: "Running", completed: "Completed", failed: "Failed" })[status] ?? status;
