import { useEffect, useRef, useState } from "react";
import type { WorkApi } from "../work/api";
import type { RecordsApi } from "./api";
import { useRecordIntake } from "./useRecordIntake";

export function RecordIntake({ api, actions, onCreated, onCancel }: {
  api: RecordsApi; actions: WorkApi; onCreated: (id: string) => void; onCancel: () => void;
}) {
  const intake = useRecordIntake(api, actions, onCreated);
  const [format, setFormat] = useState<"text" | "json">("text");
  const [content, setContent] = useState(""); const [reference, setReference] = useState("");
  const [language, setLanguage] = useState<"en" | "ja" | "zh" | "">("");
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => { heading.current?.focus(); }, []);
  return <form className="record-detail" aria-label="New record" onSubmit={event => {
    event.preventDefault(); void intake.submit(format, content, reference, language);
  }}><h2 tabIndex={-1} ref={heading}>New record</h2>
    <p>Your input is saved before processing. You can close this page while it runs.</p>
    <fieldset disabled={intake.busy}>
      <label>Processing agent<select value={intake.agent} disabled={intake.loading} onChange={event => intake.setAgent(event.target.value)}>
        {!intake.agents.length && <option value="">{intake.loading ? "Loading agents…" : "No available agents on this page"}</option>}
        {intake.agents.map(agent => <option key={agent.id} value={agent.id}>{agent.name}</option>)}</select></label>
      {(intake.offset > 0 || intake.more) && <div className="actions">
        <button type="button" disabled={intake.loading || !intake.offset} onClick={() => intake.setOffset(x => Math.max(0, x - 20))}>Previous agents</button>
        <button type="button" disabled={intake.loading || !intake.more} onClick={() => intake.setOffset(x => x + 20)}>More agents</button></div>}
      {!intake.loading && !intake.agents.length && <p>Configure an active processing agent in Settings.</p>}
      <label>Input format<select value={format} onChange={event => setFormat(event.target.value as "text" | "json")}>
        <option value="text">Text</option><option value="json">Structured JSON</option></select></label>
      <label>Input data<textarea rows={6} required maxLength={12000} value={content} onChange={event => setContent(event.target.value)} /></label>
      <details><summary>Optional details</summary>
        <label>Source reference<input maxLength={200} value={reference} onChange={event => setReference(event.target.value)} placeholder="Ticket or external reference" /></label>
        <label>Answer language<select value={language} onChange={event => setLanguage(event.target.value as typeof language)}>
          <option value="">Detect from input</option><option value="en">English</option><option value="ja">日本語</option><option value="zh">中文</option></select></label>
      </details>
      {intake.error && <p role="alert" className="error">{intake.error} Retry unchanged data here to avoid duplicate submissions.
        <button type="button" onClick={intake.reload}>Reload agents</button></p>}
      <div className="actions"><button className="primary" disabled={!intake.agent || intake.loading || !content.trim()}>
        {intake.busy ? "Saving…" : "Save and process"}</button><button type="button" onClick={onCancel}>Cancel</button></div>
    </fieldset>
  </form>;
}
