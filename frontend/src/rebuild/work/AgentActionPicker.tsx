import type { Agent } from "./api";

export function allowedActions(agent: Agent): string[] {
  try {
    const actions = JSON.parse(agent.settings_json).allowed_actions;
    return Array.isArray(actions) ? actions.filter(value => ["set_category", "add_note"].includes(value)) : [];
  } catch { return []; }
}

export function AgentActionPicker({ value, onChange }: { value: string[]; onChange: (value: string[]) => void }) {
  return <section aria-label="Agent actions"><h3>Allowed actions</h3>
    <p className="muted">After a grounded answer, this agent can propose these internal updates. A human must approve each exact change.</p>
    {[["set_category", "Suggest a task category"], ["add_note", "Suggest the answer as an internal note"]].map(([id, label]) =>
      <label className="knowledge-choice" key={id}><input type="checkbox" checked={value.includes(id)}
        onChange={event => onChange(event.target.checked ? [...value, id] : value.filter(item => item !== id))} />{label}</label>)}
  </section>;
}
