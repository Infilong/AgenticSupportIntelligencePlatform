"""Validate the v1 report envelope and recompute bounded presentation arithmetic."""

import hashlib
import json
import math
from collections import Counter
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictBool

from app.modules.evaluations.schemas import EvaluationCase, EvaluationSnapshot, EvaluationStrategy

STRATEGIES = ("vector", "bm25", "hybrid", "vector_rerank", "hybrid_rerank")
Hash = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Text = Annotated[str, Field(min_length=1, max_length=1000)]


class Input(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)


class Source(Input):
    commit: Annotated[str, Field(pattern=r"^[0-9a-f]{40}$")]
    source_sha256: Hash


class Trace(Input):
    id: UUID
    query: Text
    strategy: str
    status: Literal["succeeded"]


class Probe(Input):
    question: Text
    trace: Trace
    trace_valid: StrictBool
    candidate_leakage: list = Field(max_length=40)
    leakage: list = Field(max_length=10)
    result_bound_violated: StrictBool


class Case(Probe):
    id: Annotated[str, Field(min_length=1, max_length=40)]
    language: Literal["en", "ja", "zh"]
    groups: list[list[Text]] = Field(max_length=10)
    groups_found: Annotated[int, Field(strict=True, ge=0, le=10)]
    retrieval_passed: StrictBool | None
    fact_results: list[StrictBool] = Field(max_length=40)
    elapsed_seconds: Annotated[float, Field(ge=0, le=600)]


class Strategy(Input):
    cases: list[Case] = Field(min_length=30, max_length=30)
    negative_probes: list[Probe] = Field(min_length=2, max_length=2)
    foreign_request_status: Annotated[int, Field(strict=True)]


class Report(Input):
    experiment: Literal["retrieval-strategies-v1"]
    status: Literal["completed"]
    generation: Literal["not_verified"]
    scorer_version: Literal["active-required-sections-v2"]
    source_unchanged: Literal[True]
    runtime_unchanged: Literal[True]
    experiment_valid: Literal[True]
    source_state: Source
    frozen: dict
    workspaces: dict[str, UUID]
    strategies: dict[str, Strategy]


def project(raw: bytes):
    if len(raw) > 8 * 1024 * 1024:
        raise ValueError("Report exceeds 8 MiB")
    report = Report.model_validate_json(raw)
    if set(report.strategies) != set(STRATEGIES) or "primary" not in report.workspaces:
        raise ValueError("Require the five completed strategies and primary workspace")
    if report.frozen.get("recall_at") != 5:
        raise ValueError("Unsupported retrieval depth")
    projections, traces, case_identity = [], [], None
    for name in STRATEGIES:
        strategy = report.strategies[name]
        identity = [(case.id, case.language, case.question, case.groups) for case in strategy.cases]
        if case_identity is not None and identity != case_identity:
            raise ValueError("Strategies must use identical ordered cases")
        case_identity = identity
        if len({case.id for case in strategy.cases}) != 30 or Counter(
            case.language for case in strategy.cases
        ) != {"en": 10, "ja": 10, "zh": 10}:
            raise ValueError("Require thirty unique balanced language cases")
        cases = []
        for case in strategy.cases:
            expected_pass = (
                (
                    case.groups_found == len(case.groups)
                    and all(case.fact_results)
                    and not case.leakage
                    and not case.result_bound_violated
                )
                if case.groups
                else None
            )
            if (
                case.groups_found > len(case.groups)
                or case.retrieval_passed != expected_pass
                or bool(case.fact_results) != bool(case.groups)
            ):
                raise ValueError("Inconsistent case outcome or section counts")
            cases.append(
                EvaluationCase(
                    id=case.id,
                    language=case.language,
                    question=case.question,
                    trace_id=case.trace.id,
                    passed=case.retrieval_passed,
                    groups_found=case.groups_found,
                    total_groups=len(case.groups),
                    elapsed_seconds=case.elapsed_seconds,
                )
            )
        scores = {}
        for language in ("en", "ja", "zh", "all"):
            eligible = [
                case
                for case in cases
                if case.total_groups and (language == "all" or case.language == language)
            ]
            scores[language] = dict(
                passed=sum(case.passed is True for case in eligible),
                total=len(eligible),
                groups_found=sum(case.groups_found for case in eligible),
                total_groups=sum(case.total_groups for case in eligible),
            )
        if [scores[lang]["total"] for lang in ("en", "ja", "zh")] != [8, 9, 9] or (
            scores["all"]["total_groups"] != 27
        ):
            raise ValueError("Unsupported v1 evidence denominators")
        all_rows = [*strategy.cases, *strategy.negative_probes]
        traces.extend((row.trace, row.question, name) for row in all_rows)
        safety = strategy.foreign_request_status == 404 and all(
            row.trace_valid
            and not row.candidate_leakage
            and not row.leakage
            and not row.result_bound_violated
            for row in all_rows
        )
        quality = all(
            score["passed"] / score["total"] >= (0.9 if lang == "all" else 0.8)
            and score["groups_found"] / score["total_groups"] >= (0.9 if lang == "all" else 0.8)
            for lang, score in scores.items()
        )
        p95 = sorted(case.elapsed_seconds for case in cases)[math.ceil(0.95 * len(cases)) - 1]
        projections.append(
            EvaluationStrategy(
                name=name,
                scores=scores,
                warm_p95_seconds=p95,
                measured_requests=len(cases),
                safety_passed=safety,
                retrieval_gate_passed=safety and quality and p95 <= 3,
                cases=cases,
            )
        )
    snapshot = EvaluationSnapshot(
        scorer_version=report.scorer_version,
        source_commit=report.source_state.commit,
        source_sha256=report.source_state.source_sha256,
        corpus_sha256=hashlib.sha256(
            json.dumps(
                report.frozen,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode()
        ).hexdigest(),
        strategies=projections,
    )
    return report.workspaces["primary"], snapshot, traces
