import { useState, type FormEvent } from "react";
import type { ApiRequest } from "../app/apiRequest";
import { errorMessage } from "./api";

export function SignIn({ request, onSignIn, notice }: {
  request: ApiRequest; onSignIn: (token: string) => void; notice: string;
}) {
  const [register, setRegister] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const credentials = { email: String(data.get("email")), password: String(data.get("password")) };
    setBusy(true); setError("");
    try {
      if (register) await request("/api/v1/auth/register", {
        method: "POST", body: { ...credentials, display_name: String(data.get("name")) },
      });
      const result = await request<{ access_token: string }>("/api/v1/auth/login", {
        method: "POST", body: credentials,
      });
      onSignIn(result.access_token);
    } catch (error) { setError(errorMessage(error)); }
    finally { setBusy(false); }
  }
  return <main className="sign-in"><div className="brand">Support<span>Team workspace</span></div>
    <h1>{register ? "Create your account" : "Welcome back"}</h1>
    <p className="muted">Your knowledge. Your agents. Your team in control.</p>
    {notice && <p role="status">{notice}</p>}
    <form onSubmit={submit}>
      {register && <label>Name<input name="name" autoComplete="name" required maxLength={120} /></label>}
      <label>Email<input name="email" type="email" autoComplete="username" required /></label>
      <label>Password<input name="password" type="password" required minLength={register ? 8 : 1}
        autoComplete={register ? "new-password" : "current-password"} /></label>
      {error && <p role="alert" className="error">{error}</p>}
      <button className="primary" disabled={busy}>{busy ? "Please wait…" : register ? "Create account" : "Sign in"}</button>
    </form>
    <button className="text-button" disabled={busy} onClick={() => { setRegister(!register); setError(""); }}>
      {register ? "Already have an account? Sign in" : "New here? Create an account"}
    </button>
  </main>;
}
