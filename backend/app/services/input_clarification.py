"""Conservative preflight for incomplete standalone input, not semantic intent detection."""

import re
import time

from app.services.support_agent_state import SupportAgentState


def needs_input_clarification(state: SupportAgentState) -> bool:
    message = state["input_message"].strip()
    # A one-letter reply can be valid when answering an earlier question.
    if state.get("task_history"):
        return False
    return (not any(character.isalnum() for character in message)
            or re.fullmatch(r"[a-zA-Z]", message) is not None)


def request_input_clarification(runner, state: SupportAgentState) -> SupportAgentState:
    started = time.perf_counter()
    language = state.get("requested_language") or "en"
    messages = {
        "en": "Could you clarify what you would like help with? Please describe your question.",
        "ja": "どのようなことでお困りですか？ご質問の内容をもう少し詳しく教えてください。",
        "zh": "您希望获得什么帮助？请补充说明您的问题。",
    }
    output: SupportAgentState = {
        "detected_language": language,
        "language_source": "requested" if state.get("requested_language") else "default",
        "route_decision": "clarification",
        "route_reasons": ["incomplete_input"],
        "final_answer": messages.get(language, messages["en"]),
    }
    runner._record_step("request_clarification", state, output, started)
    return output
