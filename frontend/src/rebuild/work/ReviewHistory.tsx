import type { Trace } from "./api";

export function ReviewHistory({ trace }: { trace: Trace }) {
  const records = trace.checkpoints.filter(item => item.checkpoint_key.startsWith("human_review_")
    || ["stop_requested", "worker_stopped"].includes(item.checkpoint_key));
  if (!records.length) return null;
  return <details><summary>Human interventions</summary>{records.map(record => {
    let state: unknown;
    try { state = JSON.parse(record.state_json); } catch { state = null; }
    if (["stop_requested", "worker_stopped"].includes(record.checkpoint_key)) {
      const user = state && typeof state === "object" && "user_id" in state ? String(state.user_id) : null;
      return <div className="call-record" key={record.id}><strong>{record.checkpoint_key === "stop_requested" ? "Stop requested" : "Stop confirmed"}</strong>
        <p>{new Date(record.created_at).toLocaleString()}</p>{user && <p>Requested by: {user}</p>}</div>;
    }
    const review = state && typeof state === "object" && "human_review" in state ? state.human_review : null;
    const read = (key: string) => review && typeof review === "object" && key in review
      && typeof (review as Record<string, unknown>)[key] === "string" ? String((review as Record<string, unknown>)[key]) : "Unavailable";
    return <div className="call-record" key={record.id}><strong>{read("decision")}</strong>
      <p>{new Date(record.created_at).toLocaleString()}</p><p>Reviewer: {read("reviewer_id")}</p>
      <p>Note: {read("comments")}</p></div>;
  })}</details>;
}
