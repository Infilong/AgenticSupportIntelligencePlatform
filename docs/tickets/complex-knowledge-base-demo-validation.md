# Complex Knowledge Base Demo Validation

## Goal
Create a reusable multilingual knowledge base and test it through the real local API.

## Scope
- Add a dense English/Japanese/Chinese support-policy fixture.
- Seed it through `/api/v1/workspaces/{workspace_id}/knowledge-documents`.
- Verify retrieval through `/api/v1/workspaces/{workspace_id}/retrieval/search`.
- Verify one full agent run and trace through the LangGraph-backed agent API.

## Knowledge Coverage
- English self-service refund, renewal exception, downgrade, and billing escalation rules.
- English security incident, audit retention, workspace soft-delete, and role permission rules.
- Japanese refund and privacy-escalation guidance.
- Chinese privacy incident, refund, escalation, and retention guidance.

## Validation Checks
- English refund query returns the billing refund document and cites 30-day self-service language.
- English deletion-retention query returns the security/audit document.
- Japanese refund query returns the Japanese FAQ and includes `30日以内`.
- Japanese privacy-leak query returns human-review escalation guidance.
- Chinese privacy query returns the Chinese privacy handbook and includes `72小时`.
- Unrelated English query returns no source at a high threshold.
- Full agent run completes, stores a trace, stores AI runs, and uses the seeded refund evidence.

## Command
```bash
python3 scripts/seed_complex_knowledge_base.py --base-url http://127.0.0.1:8000
```

## Notes
- By default, this script creates a unique local demo user like `complex-demo+<timestamp>@example.com`.
- Password defaults to `complex-demo-password`; pass `--email` and `--password` to use a chosen account.
- The fixture is idempotent for documents by title, so reruns do not duplicate uploaded documents.
- The script intentionally uses the public API instead of direct database writes.
