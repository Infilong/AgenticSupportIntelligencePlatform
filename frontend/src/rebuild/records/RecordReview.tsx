import { useEffect, useState } from "react";
import { errorMessage } from "../api";
import type { Review, WorkApi } from "../work/api";
import { ReviewForm } from "../work/Reviews";
import type { RecordsApi } from "./api";

export function RecordReview({ api, actions, id, run, onUpdated }: {
  api: RecordsApi; actions: WorkApi; id: string; run: string; onUpdated: () => void;
}) {
  const [review, setReview] = useState<Review | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(true);
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    let current = true; setLoading(true); setError("");
    api.review(id, run).then(result => { if (current) setReview(result); })
      .catch(error => { if (current) setError(errorMessage(error)); })
      .finally(() => { if (current) setLoading(false); });
    return () => { current = false; };
  }, [api, id, run, revision]);
  return <section aria-label="Review this record">
    {loading && <p role="status">Loading review…</p>}
    {error && <p role="alert">{error} <button onClick={() => setRevision(x => x + 1)}>Retry review</button></p>}
    {!loading && !error && !review && <p>No review was found for this attempt.</p>}
    {review?.reviewer_decision === "pending" && (open
      ? <ReviewForm review={review} api={actions} onCancel={() => setOpen(false)} onResolved={onUpdated} />
      : <button onClick={() => setOpen(true)}>Review result</button>)}
    {review && review.reviewer_decision !== "pending" && <p>This review has already been resolved. Refresh the record to see the result.</p>}
  </section>;
}
