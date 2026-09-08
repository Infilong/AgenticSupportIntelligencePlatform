import { createApiRequest, type ApiRequest } from "../app/apiRequest";

export type Workspace = { id: string; name: string; archived_at: string | null };
export type Membership = { user_id: string; role: string; permissions: string[] };
export type Document = {
  id: string; title: string; language: string; status: string;
  error_message: string | null; updated_at: string;
};
export type DocumentPage = { items: Document[]; total: number; has_next: boolean };
export type DocumentDetail = {
  document: Document; latest_version: { raw_text: string; version: number } | null;
};
export type WorkspaceApi = ReturnType<typeof workspaceApi>;

export function workspaceApi(request: ApiRequest, token: string, workspaceId: string) {
  const base = `/api/v1/workspaces/${encodeURIComponent(workspaceId)}`;
  const call = <T>(path: string, method = "GET", body?: unknown) =>
    request<T>(`${base}${path}`, { token, method, body });
  return {
    membership: () => call<Membership>("/membership"),
    documents: (search: string, offset: number) => call<DocumentPage>(
      `/knowledge-documents?limit=20&offset=${offset}&search=${encodeURIComponent(search)}`),
    document: (id: string) => call<DocumentDetail>(`/knowledge-documents/${id}`),
    version: (id: string, version: number) => call<{ version: number; raw_text: string; created_at: string }>(
      `/knowledge-documents/${encodeURIComponent(id)}/versions/${version}`),
    addDocument: (title: string, content: string, language: string) => call<{ document: Document }>(
      "/knowledge-documents", "POST", { title, content, language: language || null, content_type: "text/markdown" }),
    reindex: (id: string, title: string, content: string, language: string) => call<{ document: Document }>(
      `/knowledge-documents/${id}/reindex`, "POST", { title, content, language: language || null }),
    remove: (id: string) => call<void>(`/knowledge-documents/${id}`, "DELETE"),
  };
}

export { createApiRequest };
export const errorMessage = (error: unknown) =>
  error instanceof Error ? error.message : "Something went wrong. Please try again.";
