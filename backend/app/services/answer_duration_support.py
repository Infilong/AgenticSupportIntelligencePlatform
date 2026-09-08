"""Conservative duration checks, not semantic entailment or policy interpretation."""

import re
import unicodedata
from decimal import Decimal

from app.services.answer_citations import cited_answer_evidence
from app.services.support_agent_state import SupportAgentState

UNIT_GROUPS = {
    "business_day": ("business day", "business days", "営業日", "工作日", "个工作日", "個工作日"),
    "day": ("day", "days", "日", "天"),
    "week": ("week", "weeks", "週間", "週", "周", "星期", "个星期", "個星期"),
    "hour": ("hour", "hours", "時間", "小时", "小時", "个小时", "個小時"),
    "month": ("month", "months", "か月", "ヶ月", "カ月", "个月", "個月", "月"),
    "year": ("year", "years", "年"),
    "minute": ("minute", "minutes", "分钟", "分鐘", "分"),
    "second": ("second", "seconds", "秒"),
}
UNITS = {alias: unit for unit, aliases in UNIT_GROUPS.items() for alias in aliases}
UNIT_PATTERN = "|".join(
    re.escape(alias) + (r"\b" if alias.isascii() else "")
    for alias in sorted(UNITS, key=len, reverse=True)
)
DURATION = re.compile(
    r"(?<![\d.])([+-]?\d+(?:,\d{3})*(?:\.\d+)?)\s*[-–]?\s*(" + UNIT_PATTERN + ")"
)


def _durations(text: str) -> set[tuple[Decimal, str]]:
    normalized = " ".join(unicodedata.normalize("NFKC", text).lower().split())
    return {(Decimal(number.replace(",", "")), UNITS[unit])
            for number, unit in DURATION.findall(normalized)}


def has_unverified_durations(state: SupportAgentState) -> bool:
    prose, evidence = cited_answer_evidence(state)
    claimed = _durations(prose)
    supported = {quantity for content in evidence for quantity in _durations(content)}
    return bool(claimed - supported)
