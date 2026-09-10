"""Conservative publication policy for local informational answers, never tool authority."""

import re

VERSION = "support-routing-v1"


def route(decision, reason, context, source_ids):
    reason = reason.strip()
    if not reason:
        decision, reason = "review", "The model did not explain its routing decision."
    if decision == "answer" and not source_ids:
        decision, reason = "missing", "No cited evidence supports an automatic answer."
    if decision in {"missing", "irrelevant"} and source_ids:
        decision, reason = "review", "The proposed outcome conflicts with its cited evidence."
    # Personal requests involving privileged operations remain reviewable even if a model
    # wrongly labels them informational. This is a backstop, not the semantic classifier.
    question = context.get("original", "").casefold()
    personal = re.search(
        r"\b(my|me|our|i)\b|我|私|please\s+(?:refund|reimburse|delete|transfer|grant)"
        r"|请(?:帮忙)?(?:退款|退费|删除|转移)|(?:返金|削除|移転)してください",
        question,
    )
    sensitive = re.search(
        r"refund|reimburse|delete|transfer|grant|breach|unauthorized|退款|退费|删除|转移|泄露|"
        r"返金|削除|移転|不正アクセス",
        question,
    )
    if decision == "answer" and personal and sensitive:
        decision = "review"
        reason = {
            "en": "This request involves a sensitive account or policy decision.",
            "ja": "この依頼には、アカウント操作またはポリシー判断の確認が必要です。",
            "zh": "此请求涉及敏感账户操作或政策决定，需要人工审核。",
        }[context.get("language", "en")]
    return {"version": VERSION, "decision": decision, "reason": reason}
