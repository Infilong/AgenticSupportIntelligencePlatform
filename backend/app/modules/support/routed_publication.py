"""Publish versioned machine outcomes under the caller's transaction and job fence."""

from sqlalchemy import func, select

from app.modules.support.context import citations
from app.modules.support.local_response import snapshot
from app.modules.support.service import handoff_for

SET_ASIDE = {
    "en": "This message was set aside as unclear. Add a clear support question to process it again.",
    "ja": "内容が不明なため保留対象から外しました。具体的な質問を追加すると再処理できます。",
    "zh": "此消息缺少有意义的信息，已搁置。补充明确的支持问题后可以重新处理。",
}


def applies(result):
    return bool(result.get("routing_version")) and (
        result.get("response", {}).get("routing") is not None or result["outcome"] == "set_aside"
    )


def publish(db, run, message, result):
    response = result.get("response")
    if response:
        handoff = handoff_for(db, run)
        recorded = snapshot(db, handoff)
        if response != recorded or response["routing"]["version"] != result["routing_version"]:
            raise ValueError("Routing evidence differs from the recorded model response")
        decision = response["routing"]["decision"]
        expected = {"answer": "answer", "review": "draft", "missing": "missing", "irrelevant": "set_aside"}
        if expected[decision] != result["outcome"]:
            raise ValueError("Checkpoint outcome differs from its recorded routing decision")
        run.citations = citations(handoff.context, response) if response["citations"] else []
        if decision == "answer" and not run.citations:
            raise ValueError("An automatic answer requires current supporting citations")
        run.draft = response["answer"]
    else:
        decision = "irrelevant"
        run.draft = SET_ASIDE[message.language]
    run.review_kind = "unclassified"
    run.outcome = {
        "answer": "answered",
        "review": "policy_review_required",
        "missing": "insufficient_evidence",
        "irrelevant": "set_aside",
    }[decision]
    run.state = "awaiting_review" if decision in {"review", "missing"} else "completed"
    now = db.scalar(select(func.clock_timestamp()))
    run.drafted_at = now
    if run.state == "completed":
        run.finished_at = now
    # No ReviewDecision or reviewed_response is created: the answer is explicitly automatic.
