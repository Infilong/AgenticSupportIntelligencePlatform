"""Conservative response-only trace redaction; never rewrite persisted evidence."""

import json
import re

REDACTED = "[REDACTED]"
SENSITIVE_KEYS = {
    "authorization", "cookie", "setcookie", "password", "passwd", "secret",
    "apikey", "openaiapikey", "accesstoken", "refreshtoken", "clientsecret",
    "email", "emailaddress", "phone", "phonenumber", "ssn", "creditcard",
    "chainofthought", "privatechainofthought",
}
EMAIL = re.compile(r"\b[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
TOKEN = re.compile(r"\b(?:sk-[A-Za-z0-9_-]{12,}|Bearer\s+[A-Za-z0-9._~+/=-]+)", re.I)
ASSIGNMENT = re.compile(
    r"(?i)\b(api[_-]?key|password|client[_-]?secret|access[_-]?token|refresh[_-]?token)"
    r"(\s*[:=]\s*)(?:\"[^\"]*\"|'[^']*'|[^\s,;&]+)"
)


def redact_trace(value, *, depth=0):
    if depth > 40:
        return REDACTED
    if isinstance(value, dict):
        return {key: REDACTED if re.sub(r"[^a-z0-9]", "", str(key).lower())
                in SENSITIVE_KEYS else redact_trace(item, depth=depth + 1)
                for key, item in value.items()}
    if isinstance(value, list):
        return [redact_trace(item, depth=depth + 1) for item in value]
    if not isinstance(value, str):
        return value
    # Trace payloads are JSON strings inside JSON responses. Preserve their parseability.
    if value.lstrip().startswith(("{", "[")):
        try:
            parsed = json.loads(value)
        except (ValueError, RecursionError):
            pass
        else:
            return json.dumps(redact_trace(parsed, depth=depth + 1), ensure_ascii=False)
    value = ASSIGNMENT.sub(lambda match: match[1] + match[2] + REDACTED, value)
    return EMAIL.sub(REDACTED, TOKEN.sub(REDACTED, value))
