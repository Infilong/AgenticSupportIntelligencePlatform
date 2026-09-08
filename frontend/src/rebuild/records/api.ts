import type { ApiRequest } from "../../app/apiRequest";
import type { Page, Trace, Review } from "../work/api";

export type RecordSummary = { id: string; input_message: string; received_at: string;
  latest_run_id: string; status: string; result_summary: string | null; attempt_count: number };
export type RecordDetail = RecordSummary & { input: { format: string; content: unknown;
  source: string; source_reference: string | null } };
export type Artifact = { step_id: string; kind: string; status: string;
  data: Record<string, unknown>; error: string | null };
export type RecordsApi = ReturnType<typeof recordsApi>;
export type RecordSubmission = { agent_id: string; language: "en" | "ja" | "zh" | null;
  input: { format: "text" | "json"; content: string | object; source: "admin"; source_reference: string | null } };
export function recordsApi(request: ApiRequest, token: string, workspace: string) {
  const base = `/api/v1/workspaces/${encodeURIComponent(workspace)}`;
  const get = <T>(path: string) => request<T>(base + path, { token });
  return {
    create: (body: RecordSubmission, request_key: string) => request<RecordDetail>(`${base}/records`,
      { token, method: "POST", body: { ...body, request_key } }),
    review: (id: string, run: string) => get<Review | null>(
      `/records/${encodeURIComponent(id)}/attempts/${encodeURIComponent(run)}/review`),
    clarify: (id: string, run_id: string, reply: string, request_key: string) => request<RecordDetail>(
      `${base}/records/${encodeURIComponent(id)}/clarifications`, { token, method: "POST", body: { run_id, reply, request_key } }),
    stop: (run: string) => request(`${base}/task-runs/${encodeURIComponent(run)}/stop`, { token, method: "POST" }),
    list: (search: string, status: string, offset: number) => get<Page<RecordSummary>>(
      `/records?search=${encodeURIComponent(search)}&offset=${offset}&limit=20${status ? `&status=${status}` : ""}`),
    detail: (id: string) => get<RecordDetail>(`/records/${encodeURIComponent(id)}`),
    trace: (run: string) => get<Trace>(`/agent-runs/${encodeURIComponent(run)}/trace`),
    artifacts: (id: string, run: string, offset: number) => get<Page<Artifact>>(
      `/records/${encodeURIComponent(id)}/attempts/${encodeURIComponent(run)}/artifacts?limit=20&offset=${offset}`),
  };
}
