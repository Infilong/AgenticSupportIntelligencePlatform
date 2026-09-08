import { useState, type FormEvent } from "react";
import { errorMessage } from "../api";
import type { SettingsApi } from "./api";

export function ModelForm({ api, onSaved, onCancel }: { api: SettingsApi; onSaved: () => void; onCancel: () => void }) {
  const [provider, setProvider] = useState("mock");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const data = new FormData(event.currentTarget); setBusy(true); setError("");
    try {
      await api.addModel({ provider, model: String(data.get("model")).trim(), purpose: "agent_default", active: false,
        max_context_tokens: Number(data.get("context")), prompt_token_cost_per_1k: Number(data.get("input")),
        completion_token_cost_per_1k: Number(data.get("output")) });
      onSaved();
    } catch (error) { setError(errorMessage(error)); } finally { setBusy(false); }
  }
  return <form className="panel" onSubmit={save} aria-label="Add model"><h2>Add model</h2>
    <fieldset disabled={busy}>
      <label>Provider<select value={provider} onChange={event => setProvider(event.target.value)}>
        <option value="mock">Mock — local testing</option><option value="openai">OpenAI</option>
      </select></label>
      <label>Model name<input name="model" autoFocus required maxLength={120} placeholder={provider === "mock" ? "support-test" : "Your enabled model identifier"} /></label>
      <p className="muted">{provider === "mock" ? "Deterministic test responses; this does not verify real AI quality." : "Uses credentials configured on the server. Adding a model does not make a model call; readiness is shown after saving."}</p>
      <label>Context limit (tokens)<input key={`context-${provider}`} name="context" type="number" min={256} max={2000000} defaultValue={provider === "mock" ? 12000 : ""} required /></label>
      <p className="muted">Enter the model's context limit and pricing. These values control request budgets and cost estimates.</p>
      <label>Input cost (USD per 1,000 tokens)<input key={`input-${provider}`} name="input" type="number" min={0} step="any" defaultValue={provider === "mock" ? 0 : ""} required /></label>
      <label>Output cost (USD per 1,000 tokens)<input key={`output-${provider}`} name="output" type="number" min={0} step="any" defaultValue={provider === "mock" ? 0 : ""} required /></label>
    </fieldset>
    {error && <p role="alert" className="error">{error}</p>}
    <div className="actions"><button className="primary" disabled={busy}>{busy ? "Saving…" : "Save model"}</button>
      <button type="button" disabled={busy} onClick={onCancel}>Cancel</button></div>
  </form>;
}
