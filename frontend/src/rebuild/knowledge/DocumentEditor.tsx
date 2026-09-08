import { useRef, useState, type FormEvent } from "react";
import { errorMessage } from "../api";

export function DocumentEditor({ initial, onSave, onCancel }: {
  initial?: { title: string; content: string; language: string };
  onSave: (title: string, content: string, language: string) => Promise<void>; onCancel: () => void;
}) {
  const [title, setTitle] = useState(initial?.title ?? "");
  const [content, setContent] = useState(initial?.content ?? "");
  const [language, setLanguage] = useState(initial?.language ?? "");
  const [busy, setBusy] = useState(false);
  const [reading, setReading] = useState(false);
  const [error, setError] = useState("");
  const fileVersion = useRef(0);
  async function read(file?: File) {
    const version = ++fileVersion.current;
    if (!file) { setReading(false); return; }
    setReading(false);
    setError("");
    if (!/\.(txt|md|markdown)$/i.test(file.name)) { setError("Choose a text or Markdown file."); return; }
    if (file.size > 2 * 1024 * 1024) { setError("Choose a file smaller than 2 MB."); return; }
    setReading(true);
    try {
      const bytes = await file.arrayBuffer();
      const text = new TextDecoder("utf-8", { fatal: true }).decode(bytes);
      if (version !== fileVersion.current) return;
      if (text.includes("\0")) throw new Error("This file contains binary content. Choose a UTF-8 text file.");
      setContent(text); setTitle(previous => previous || file.name.replace(/\.[^.]+$/, ""));
    } catch (error) {
      if (version === fileVersion.current) setError(error instanceof TypeError
        ? "Save the file as UTF-8 text and try again." : errorMessage(error));
    } finally { if (version === fileVersion.current) setReading(false); }
  }
  async function submit(event: FormEvent) {
    event.preventDefault(); setError(""); setBusy(true);
    try { await onSave(title.trim(), content.trim(), language); }
    catch (error) { setError(errorMessage(error)); }
    finally { setBusy(false); }
  }
  return <section className="panel editor" aria-label={initial ? "Edit knowledge" : "Add knowledge"}>
    <h2>{initial ? "Update document" : "Add knowledge"}</h2>
    <p className="muted">Upload a text or Markdown file, or paste the information your agents should use.</p>
    <form onSubmit={submit}>
      <fieldset disabled={busy}><label>Text or Markdown file<input type="file" accept=".txt,.md,.markdown"
        onChange={event => void read(event.target.files?.[0])} /></label>
        <label>Title<input value={title} onChange={event => setTitle(event.target.value)} required maxLength={200} /></label>
        <label>Document language<select value={language} onChange={event => setLanguage(event.target.value)}>
          {!initial && <option value="">Detect automatically</option>}
          <option value="en">English</option><option value="ja">日本語</option><option value="zh">中文</option>
        </select></label>
        <label>Content<textarea value={content} onChange={event => setContent(event.target.value)} required rows={12} /></label>
      </fieldset>
      {error && <p role="alert" className="error">{error}</p>}
      <div className="actions"><button className="primary" disabled={busy || reading || !title.trim() || !content.trim()}>
        {reading ? "Reading file…" : busy ? "Processing document…" : initial ? "Save new version" : "Add document"}
      </button><button type="button" disabled={busy} onClick={onCancel}>Cancel</button></div>
    </form>
  </section>;
}
