"""Read-only local operator evidence export; no credentials or expected answers leave the evaluator."""

import json
import subprocess


def export(workspace, comparison_ids):
    # Explicit UUID-bound read from the local development database. App admission/generation still
    # uses authenticated APIs and the worker; this is an operator audit, not a public API endpoint.
    code = '''
import json,sys,uuid
from sqlalchemy import create_engine,text
from app.core.settings import Settings
payload=json.load(sys.stdin)
workspace=str(uuid.UUID(payload["workspace"]))
ids=[str(uuid.UUID(value)) for value in payload["ids"]]
engine=create_engine(Settings().database_url.get_secret_value())
result=[]
with engine.connect() as db:
    for identity in ids:
        rows=db.execute(text("""SELECT p.name,p.request,p.context,p.response,p.request_hash,p.response_hash,
            p.contributor_id,p.run_id,h.generation_request,h.context AS handoff_context,
            h.response AS handoff_response,h.request_hash AS handoff_request_hash,
            h.response_hash AS handoff_response_hash,h.contributor_id AS handoff_contributor_id
            FROM generation_pipelines p LEFT JOIN development_handoffs h
              ON h.workspace_id=p.workspace_id AND h.run_id=p.run_id
            WHERE p.workspace_id=:workspace AND p.comparison_id=:identity"""),
            {"workspace":workspace,"identity":identity}).mappings()
        items=[]
        for record in rows:
            row=dict(record)
            if row["run_id"]:
                row.update(request=row["generation_request"],context=row["handoff_context"],
                    response=row["handoff_response"],request_hash=row["handoff_request_hash"],
                    response_hash=row["handoff_response_hash"],contributor_id=row["handoff_contributor_id"])
            request=row["request"] or {}
            call_id=request.get("call_id")
            call=db.execute(text("SELECT * FROM model_calls WHERE workspace_id=:workspace AND id=:id"),
                {"workspace":workspace,"id":str(uuid.UUID(call_id))}).mappings().first() if call_id else None
            items.append({key:row[key] for key in ("name","request","context","response","request_hash",
                "response_hash","contributor_id")} | {"call":dict(call) if call else None})
        result.append({"comparison_id":identity,"pipelines":items})
print(json.dumps(result,default=str,ensure_ascii=False))
'''
    result = subprocess.run(
        ["docker", "exec", "-i", "asi-rebuild-v1-api-1", "/app/.venv/bin/python", "-c", code],
        input=json.dumps({"workspace": workspace, "ids": comparison_ids}),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
        check=True,
    )
    return json.loads(result.stdout)
