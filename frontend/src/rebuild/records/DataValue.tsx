export function DataValue({ value, depth = 0 }: { value: unknown; depth?: number }) {
  if (value === null || value === undefined) return <span className="muted">Not recorded</span>;
  if (typeof value !== "object") return <span className="record-value">{String(value)}</span>;
  if (depth >= 5) return <details><summary>Nested data</summary><pre className="record-json">{JSON.stringify(value, null, 2)}</pre></details>;
  if (Array.isArray(value)) return <div className="record-values">{value.slice(0, 50).map((item, index) =>
    <div key={index}><DataValue value={item} depth={depth + 1} /></div>)}
    {value.length > 50 && <p>Showing 50 of {value.length} entries.</p>}</div>;
  return <dl className="record-fields">{Object.entries(value).map(([key, item]) =>
    <div key={key}><dt>{key.replaceAll("_", " ")}</dt><dd><DataValue value={item} depth={depth + 1} /></dd></div>)}</dl>;
}
