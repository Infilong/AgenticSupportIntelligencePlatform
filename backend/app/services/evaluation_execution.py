"""Publish evaluation metrics or preserve an explicit unexpected-failure outcome."""

import json
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.request_context import request_id_context
from app.models.evaluation import (
    EvaluationMetric,
    EvaluationMode,
    EvaluationResult,
    EvaluationRun,
    EvaluationRunStatus,
)
from app.services.evaluation_metrics import calculate_metrics

logger = logging.getLogger(__name__)


@contextmanager
def evaluation_execution(db: Session, run: EvaluationRun) -> Iterator[list[EvaluationResult]]:
    run_id, workspace_id = run.id, run.workspace_id
    results = []
    try:
        yield results
        for (mode, language), metric_values in calculate_metrics(results).items():
            for name, value in metric_values.items():
                db.add(EvaluationMetric(
                    workspace_id=workspace_id, evaluation_run_id=run_id,
                    mode=EvaluationMode(mode), language=language,
                    metric_name=name, metric_value=value,
                ))
        run.status = EvaluationRunStatus.completed
        run.completed_at = datetime.now(UTC)
        db.commit()
    except Exception as primary:
        recorded = False
        recording_error = None
        try:
            db.rollback()
            run.status = EvaluationRunStatus.failed
            run.completed_at = datetime.now(UTC)
            db.commit()
            recorded = True
        except Exception as secondary:
            recording_error = type(secondary).__name__
            try:
                db.rollback()
            except Exception as rollback_error:
                recording_error = type(rollback_error).__name__
        logger.error(json.dumps({
            "event": "evaluation_execution_failed", "evaluation_run_id": str(run_id),
            "request_id": request_id_context.get(), "error_type": type(primary).__name__,
            "failure_recorded": recorded, "recording_error_type": recording_error,
        }, sort_keys=True))
        raise
