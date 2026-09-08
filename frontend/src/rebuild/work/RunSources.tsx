import type { Trace } from "./api";

type Source = { citation: string; content: string; document_id?: string; version?: number };
function sources(trace: Trace): Source[] {
  const step = trace.steps.find(step => step.step_name === "compress_context");
  if (!step) return [];
  let output: unknown;
  try { output = JSON.parse(step.output_json); } catch { return []; }
  if (!output || typeof output !== "object" || !("packed_context_chunks" in output)) return [];
  const chunks = output.packed_context_chunks;
  if (!Array.isArray(chunks)) return [];
  return chunks.filter((chunk): chunk is Source => chunk !== null && typeof chunk === "object"
    && typeof chunk.citation === "string" && typeof chunk.content === "string");
}

export function RunSources({ trace }: { trace: Trace }) {
  const chunks = sources(trace);
  return <><h3>Sources used</h3>{chunks.length ? chunks.map((source, index) =>
    <details key={`${source.citation}-${index}`}><summary>{source.citation}</summary>
      <p className="answer-text">{source.content}</p>
      {typeof source.document_id === "string" && Number.isSafeInteger(source.version) && source.version! > 0 &&
        <a href={`#knowledge?document=${encodeURIComponent(source.document_id)}&version=${source.version}`}>
          Open document version {source.version}</a>}
    </details>) : <p className="muted">No source excerpts were recorded for drafting.</p>}</>;
}
