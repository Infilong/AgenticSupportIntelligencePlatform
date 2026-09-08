import type { components } from './schema';

export type Session = components['schemas']['SessionResponse'];
export type User = components['schemas']['PublicUser'];
export type Workspace = components['schemas']['WorkspaceResponse'];
export type Member = components['schemas']['MemberResponse'];
export type Role = Workspace['role'];

let csrf = '';
export const setCsrf = (value: string) => { csrf = value; };

export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message); }
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api${path}`, {
      ...options, credentials: 'same-origin',
      headers: { ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }), 'X-CSRF-Token': csrf, ...options.headers },
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error;
    throw new ApiError(0, 'Cannot reach the server. Check the connection and try again.');
  }
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    if (response.status === 401 && !path.startsWith('/session')) window.dispatchEvent(new Event('session-expired'));
    throw new ApiError(response.status, typeof payload?.detail === 'string' ? payload.detail :
      response.status === 422 ? 'Check the highlighted information and try again.' : 'Something went wrong. Please try again.');
  }
  return response.status === 204 ? undefined as T : response.json();
}
