from app.jobs.contracts import Publication
from app.modules.reviews.processing import process
from app.worker import run_once
from tests.integration.conftest import login
from tests.integration.support_helpers import base, create, draft_payload, prepare, run_support


def ready_draft(system, category="ordinary"):
    prepare(system)
    run = create(system)
    assert run_support(system)
    client, path = system["client"], base(system, run)
    auth = login(client)
    handoff = client.get(path + "/development-handoff").json()
    payload = {**draft_payload(handoff), "review_category": category}
    assert (
        client.post(path + f"/development-handoff/{handoff['id']}", headers=auth, json=payload).status_code
        == 202
    )
    assert run_support(system), system.get("claim_diagnostic")
    result = client.get(path).json()
    assert result["state"] == "awaiting_review"
    return path, result


def decision_payload(run, action="approve"):
    return {
        "action": action,
        "reason": "Checked the cited policy and requested outcome.",
        "expected_revision": run["review_version"],
        "draft_hash": run["draft_hash"],
        **(
            {"response": "Reviewed wording: the refund request window is fourteen days."}
            if action == "edit"
            else {}
        ),
    }


def run_review(system):
    errors = []

    def handler(engine, job):
        try:
            result = process(engine, job)
        except Exception as exc:
            errors.append(exc)
            raise

        def publish(db, current):
            try:
                return result.publish(db, current)
            except Exception as exc:
                errors.append(exc)
                raise

        return Publication(publish)

    worked = run_once(system["engine"], handlers={"support_review": handler})
    return worked, errors
