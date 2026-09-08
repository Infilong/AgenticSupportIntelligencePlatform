"""Stable loaded-case identity, without persisting duplicate question text in scores."""

import hashlib
import json
from dataclasses import asdict

from app.services.evaluation_loader import LoadedEvaluationCase


def case_fingerprint(case: LoadedEvaluationCase) -> str:
    encoded = json.dumps(asdict(case), ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
