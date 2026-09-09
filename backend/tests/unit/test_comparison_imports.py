"""A first baseline job must not depend on a prior support job registering its FK targets."""

import subprocess
import sys


def test_fresh_baseline_worker_resolves_foreign_keys():
    code = (
        "from app.modules.identity import models; "
        "from app.modules.comparisons.processing import process; "
        "from app.modules.knowledge.retrieval import retrieve; "
        "from app.modules.comparisons.models import Pipeline; "
        "assert all(fk.column is not None for fk in Pipeline.__table__.foreign_keys)"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, timeout=15)
    assert result.returncode == 0, result.stderr.decode(errors="replace")
