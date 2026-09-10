"""Domain publication remains atomic and fenced after separate graph checkpoint commits."""

import uuid

from sqlalchemy import func, select

from app.jobs.contracts import Publication
from app.modules.reviews.service import draft_identity
from app.modules.support.context import citations, digest, validate_sources
from app.modules.support.models import Handoff
from app.modules.support.service import handoff_for
from app.providers.development_generation import render, snapshot
from app.workflows.review_graph import execute as wait_for_review
from app.workflows.support_graph import CLARIFICATION, execute, guard

MISSING = {
    "en": "No current knowledge sources were found. Add relevant documents or clarify the question.",
    "ja": "現在のナレッジに該当する情報がありません。関連資料を追加するか、質問を具体的にしてください。",
    "zh": "未找到当前有效的知识来源。请添加相关文档或进一步说明问题。",
}


def process(engine, job, retrieval=None):
    result = execute(engine, job, **({"retrieval": retrieval} if retrieval else {}))
    run_id = uuid.UUID(job.payload["run_id"])
    if result["outcome"] == "draft":
        quoted = citations(result["context"], result["response"])
        wait_for_review(engine, job, draft_identity(result["response"]["answer"], quoted))

    def publish(db, current):
        run, message = guard(db, current, run_id)  # Checks authority, lease and cancellation before writes.
        if run.state in {"awaiting_review", "completed", "rejected"}:
            return {"run_id": str(run.id), "state": run.state}
        if result.get("retrieval_id"):
            run.retrieval_id = uuid.UUID(result["retrieval_id"])
        outcome = result["outcome"]
        if outcome in {"generate", "draft"}:
            validate_sources(db, run.workspace_id, result["context"])
            handoff = handoff_for(db, run)
            if handoff is None:
                request = render(result["context"])
                handoff = Handoff(
                    workspace_id=run.workspace_id,
                    run_id=run.id,
                    context=result["context"],
                    context_hash=result["context_hash"],
                    prompt_version=result["context"]["prompt_version"],
                    generation_request=request,
                    request_hash=digest(request),
                )
                db.add(handoff)
            if outcome == "draft":
                if handoff.provider == "local_ollama":
                    from app.modules.support.local_response import snapshot as local_snapshot

                    local_snapshot(db, handoff)
                else:
                    snapshot(handoff)  # Revalidate identities even after a completed-checkpoint replay.
                if handoff.response != result["response"]:
                    raise ValueError("Completed graph response differs from stored contribution")
                run.citations = citations(handoff.context, handoff.response)
                run.draft, run.state = handoff.response["answer"], "awaiting_review"
                run.review_kind = handoff.response.get("review_category", "unclassified")
                run.outcome = {
                    "ordinary": "grounded_draft",
                    "policy_exception": "policy_review_required",
                    "conflicting_evidence": "conflicting_evidence",
                    "unclassified": "grounded_draft",
                }[run.review_kind]
                run.drafted_at = db.scalar(select(func.clock_timestamp()))
            else:
                run.state = "waiting_for_input"
        else:
            run.state = "completed"
            run.outcome = "clarification_needed" if outcome == "clarification" else "insufficient_evidence"
            run.draft = (CLARIFICATION if outcome == "clarification" else MISSING)[message.language]
            if result.get("generation_mode") == "local_ollama" and result.get("response"):
                from app.modules.support.local_response import snapshot as local_snapshot

                response = local_snapshot(db, handoff_for(db, run))
                if response != result["response"] or response["citations"]:
                    raise ValueError("Unsupported response does not match its recorded evidence")
                run.draft = response["answer"]
            run.finished_at = db.scalar(select(func.clock_timestamp()))
        return {"run_id": str(run.id), "state": run.state}

    return Publication(publish)
