import type { ApiRequest } from "../../app/apiRequest";
import type { Workspace } from "../api";
import type { Page, AgentModel } from "../work/api";

export type ModelInput = { provider: string; model: string; purpose: string; active: boolean;
  max_context_tokens: number; prompt_token_cost_per_1k: number; completion_token_cost_per_1k: number };
export type SettingsApi = ReturnType<typeof settingsApi>;
export type Member = { user_id: string; email: string; display_name: string; role: string };
export function settingsApi(request: ApiRequest, token: string, workspace: string) {
  const base = `/api/v1/workspaces/${encodeURIComponent(workspace)}`;
  const call = <T>(path: string, method = "GET", body?: unknown) => request<T>(base + path, { token, method, body });
  return {
    rename: (name: string) => call<Workspace>("", "PATCH", { name }),
    members: (offset: number, search: string) => call<Member[]>(`/members?limit=20&offset=${offset}&search=${encodeURIComponent(search)}`),
    addMember: (email: string, role: string) => call<Member>("/members", "POST", { email, role }),
    changeRole: (id: string, role: string) => call<Member>(`/members/${encodeURIComponent(id)}`, "PATCH", { role }),
    removeMember: (id: string) => call<void>(`/members/${encodeURIComponent(id)}`, "DELETE"),
    models: (offset: number, search: string) => call<Page<AgentModel>>(`/model-configs?limit=20&offset=${offset}&search=${encodeURIComponent(search)}`),
    addModel: (input: ModelInput) => call<AgentModel>("/model-configs", "POST", input),
  };
}
