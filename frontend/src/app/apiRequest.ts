export type ApiOptions = { method?: string; token?: string | null; body?: unknown };
export type ApiRequest = <T>(path: string, options?: ApiOptions) => Promise<T>;

export class ApiError extends Error {
  constructor(message: string, readonly status: number, readonly requestId?: string) {
    super(message);
    this.name = "ApiError";
  }
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export function createApiRequest(onUnauthorized: (token: string) => void): ApiRequest {
  return async <T>(path: string, options: ApiOptions = {}): Promise<T> => {
    const response = await fetch(`${API_BASE}${path}`, {
      method: options.method ?? "GET",
      headers: { "Content-Type": "application/json",
        ...(options.token ? { Authorization: `Bearer ${options.token}` } : {}) },
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
    });
    if (!response.ok) {
      // Notify before reading the body: a broken error payload must not keep a rejected session.
      if (response.status === 401 && options.token) onUnauthorized(options.token);
      const payload = await response.json().catch(() => null);
      const detail = payload?.detail;
      const message = typeof detail === "string" ? detail : detail?.message ?? response.statusText;
      const reference = response.headers.get("x-request-id");
      const requestId = reference && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(reference)
        ? reference : undefined;
      const feedback = response.status >= 500 && requestId
        ? `${message} (Request ID: ${requestId})` : message;
      throw new ApiError(feedback, response.status, requestId);
    }
    if (response.status === 204) return undefined as T;
    return await response.json() as T;
  };
}
