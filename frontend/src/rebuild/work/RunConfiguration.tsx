import { useEffect, useState } from "react";
import { errorMessage } from "../api";
import type { TaskConfiguration, WorkApi } from "./api";

export function RunConfiguration({ api, id }: { api: WorkApi; id: string }) {
  const [configuration, setConfiguration] = useState<TaskConfiguration | null>(null);
  const [error, setError] = useState("");
  const [open, setOpen] = useState(false);
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    if (!open) return;
    let current = true;
    setError("");
    api.configuration(id).then(result => { if (current) setConfiguration(result); })
      .catch(error => { if (current) setError(errorMessage(error)); });
    return () => { current = false; };
  }, [api, id, open, revision]);
  return <details onToggle={event => setOpen(event.currentTarget.open)}>
    <summary>Agent configuration at start</summary>
    {error && <p role="alert">{error} <button onClick={() => setRevision(value => value + 1)}>Retry configuration</button></p>}
    {!configuration && !error && <p role="status">Loading saved configuration…</p>}
    {configuration && <>
      <p>Agent: {configuration.name}</p>
      <p>Assigned model ID: {configuration.model_config_id ?? "Workspace default routing"}</p>
      <p>Token budget: {configuration.token_budget}</p>
      <p className="answer-text">Instructions: {configuration.instructions || "Default support instructions"}</p>
      <p>Knowledge: {configuration.knowledge_document_ids === null ? "All permitted ready documents"
        : configuration.knowledge_document_ids.length ? `${configuration.knowledge_document_ids.length} selected documents` : "No documents"}</p>
      {configuration.knowledge_document_ids?.map(id => <p key={id}>Document ID: {id}</p>)}
      <p>Allowed actions: {configuration.allowed_actions.map(action => action.replaceAll("_", " ")).join(", ") || "None"}</p>
      <p className="muted">Saved when this attempt started. Model calls above identify the models actually used.</p>
    </>}
  </details>;
}
