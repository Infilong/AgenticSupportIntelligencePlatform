"""Real 50k-row API/query proof; fixtures do not simulate successful AI processing."""

import json
import math
import os
from pathlib import Path
from time import perf_counter

from sqlalchemy import event

from tests.integration.capacity_data import seed_capacity
from tests.integration.conftest import login


def test_50000_message_reads_are_bounded_scoped_and_use_latest_attempt(system, tmp_path):
    expected = seed_capacity(system["engine"], system["workspace"], system["users"]["operator"].id)
    seed_capacity(system["engine"], system["foreign"], system["users"]["other"].id, 100, "FOREIGN")
    client = system["client"]
    login(client, "viewer")
    path = f"/api/workspaces/{system['workspace']}/messages"
    cases = [("first", "all", "", 0), ("middle", "all", "", 25000), ("last", "all", "", 49950)]
    cases += [(view, view, "", 0) for view in ("attention", "ready", "processing", "failed")]
    cases += [("selective", "all", "CAP-49999", 0), ("japanese", "all", "返金", 0)]
    measurements, plans, captured = [], {}, []

    def capture(connection, cursor, statement, parameters, context, many):
        if statement.startswith("SELECT") and "support_messages" in statement:
            captured.append((statement, parameters))

    engine = system["app"].state.engine
    event.listen(engine, "before_cursor_execute", capture)
    try:
        for name, view, search, offset in cases:
            wanted = [
                item
                for item in expected
                if (view == "all" or item["view"] == view) and search in item["original"]
            ]
            samples = []
            for repeat in range(6):
                started = perf_counter()
                response = client.get(path, params=dict(view=view, search=search, offset=offset, limit=50))
                elapsed = (perf_counter() - started) * 1000
                assert response.status_code == 200, response.text
                result = response.json()
                assert result["total"] == len(wanted)
                assert [item["id"] for item in result["items"]] == [
                    item["id"] for item in wanted[offset : offset + 50]
                ]
                assert [item["run_id"] for item in result["items"]] == [
                    item["run_id"] for item in wanted[offset : offset + 50]
                ]
                if repeat:
                    samples.append(elapsed)
                else:
                    cold_ms = elapsed
                    if name in ("first", "last", "attention", "selective"):
                        with system["engine"].connect() as connection:
                            plans[name] = [
                                connection.exec_driver_sql(
                                    "EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + sql, args
                                ).scalar()
                                for sql, args in captured[-2:]
                            ]
            measurements.append(
                dict(
                    case=name,
                    total=len(wanted),
                    first_ms=cold_ms,
                    warm_ms=samples,
                    p95_ms=sorted(samples)[math.ceil(len(samples) * 0.95) - 1],
                )
            )
    finally:
        event.remove(engine, "before_cursor_execute", capture)
    assert client.get(path, params={"search": "FOREIGN"}).json() == {"items": [], "total": 0}
    assert client.get(path, params={"offset": 50000}).json()["items"] == []
    assert client.get(path, params={"limit": 51}).status_code == 422
    assert client.get(f"/api/workspaces/{system['foreign']}/messages").status_code == 404
    login(client, "other")
    assert client.get(path).status_code == 404
    directory = Path(os.environ.get("ASI_EVIDENCE_DIR", str(tmp_path)))
    directory.mkdir(parents=True, exist_ok=True)
    report = dict(
        scope="50k synthetic stored-state API reads; no provider, throughput or processing proof",
        rows=50000,
        foreign_rows=100,
        measurements=measurements,
        query_plans=plans,
    )
    (directory / "inbox-capacity.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    # The opt-in local benchmark sets its budget before measurement. CI checks correctness only.
    budget = os.environ.get("ASI_CAPACITY_BUDGET_MS")
    if budget:
        assert max(item["p95_ms"] for item in measurements) <= float(budget), measurements
    if os.environ.get("ASI_CAPACITY_BROWSER") == "1":
        from tests.integration.capacity_browser import verify_browser

        verify_browser(system, directory)
