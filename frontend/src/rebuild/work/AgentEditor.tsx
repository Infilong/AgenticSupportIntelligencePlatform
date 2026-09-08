import { useState, type FormEvent } from "react";
import { errorMessage } from "../api";
import type { Agent, WorkApi } from "./api";
import { AgentModelPicker } from "./AgentModelPicker";
import { AgentKnowledgePicker, knowledgeScope } from "./AgentKnowledgePicker";
import { AgentActionPicker, allowedActions } from "./AgentActionPicker";

function instructions(agent: Agent) {
  try {
    const value = JSON.parse(agent.settings_json);
    return typeof value?.instructions === "string" ? value.instructions : "";
  } catch { return ""; }
}
export function AgentEditor({ agent, api, onSaved, onCancel }: {
  agent: Agent; api: WorkApi; onSaved: () => void; onCancel: () => void;
}) {
  const [name, setName] = useState(agent.name);
  const [guidance, setGuidance] = useState(() => instructions(agent));
  const [active, setActive] = useState(agent.active);
  const [model, setModel] = useState(agent.model_config_id ?? "");
  const [knowledge, setKnowledge] = useState(() => knowledgeScope(agent));
  const [actions, setActions] = useState(() => allowedActions(agent));
  const [budget, setBudget] = useState(agent.token_budget);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function save(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError("");
    try {
      await api.updateAgent(agent.id, { name: name.trim(), instructions: guidance.trim(), active, token_budget: budget,
        model_config_id: model || null, knowledge_document_ids: knowledge, allowed_actions: actions });
      onSaved();
    } catch (error) { setError(errorMessage(error)); } finally { setBusy(false); }
  }
  return <form className="panel" onSubmit={save} aria-label="Agent settings"><h2>Edit agent</h2>
    <fieldset disabled={busy}><label>Name<input autoFocus value={name} onChange={event => setName(event.target.value)} required maxLength={160} /></label>
      <label>Instructions<textarea value={guidance} onChange={event => setGuidance(event.target.value)} maxLength={4000} rows={6}
        placeholder="For example: keep answers concise and explain the next step." /></label>
      <p className="muted">These instructions guide new answers. Evidence requirements and workspace permissions still apply. Mock responses do not simulate instruction-following quality.</p>
      <label>Availability<select value={active ? "active" : "inactive"} onChange={event => setActive(event.target.value === "active")}>
        <option value="active">Available for new requests</option><option value="inactive">Inactive</option>
      </select></label>
      <AgentModelPicker api={api} value={model} onChange={setModel} />
      <AgentKnowledgePicker api={api} value={knowledge} onChange={setKnowledge} />
      <AgentActionPicker value={actions} onChange={setActions} />
      <details><summary>Execution limits</summary><label>Token budget<input type="number" min={500} max={32000} required value={budget}
        onChange={event => setBudget(Number(event.target.value))} /></label></details>
    </fieldset>
    {error && <p role="alert" className="error">{error}</p>}
    <div className="actions"><button className="primary" disabled={busy || !name.trim()}>{busy ? "Saving…" : "Save settings"}</button>
      <button type="button" disabled={busy} onClick={onCancel}>Cancel</button></div>
  </form>;
}
