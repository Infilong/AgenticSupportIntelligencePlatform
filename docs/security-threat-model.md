# Security Threat Model

## Primary Risks
- user accesses another workspace's data
- retrieval leaks another workspace's chunks
- prompt injection forces system or raw document leakage
- unsafe tool calls bypass backend permissions
- PII is logged in traces or errors
- secrets are hardcoded or exposed
- evaluations or cost summaries leak cross-workspace data
- human review is bypassed for high-risk cases

## Required Controls
- authentication on protected routes
- workspace membership checks on workspace routes
- `workspace_id` filters on all workspace-owned queries
- retrieval filtering by workspace before ranking or returning chunks
- prompt injection detection
- unsafe tool call blocking
- citation-required validation
- unsupported answer refusal
- language preservation check
- token/cost limit checks
- structured output validation
- safety-risk escalation

## Signing-key configuration
Staging/production settings reject the public development signing key and keys shorter than
32 UTF-8 bytes. Unknown environment names fail validation. Local/development/test retain
development defaults. Operators must supply cryptographically random keys and configure
production mode explicitly; key rotation, database credentials and deployment hardening remain
separate requirements. This startup guard does not certify a secure deployment.

## Required Permission Tests
Test that users cannot access another workspace's documents, datasets, examples, labels, graph runs, human reviews, evaluations, cost summaries, audit logs, or retrieval chunks.

Evaluation resource IDs and folder IDs remain scoped even for an owner of both workspaces:
18 foreign-ID requests across both directions reject with unchanged evidence and no model
dispatch. This includes each comparison operand and creation with a foreign folder. See
[workspace isolation evidence](testing.md#evaluation-resource-workspace-isolation).

Evaluation management denial is verified for anonymous, outsider and disallowed specialized
roles across list/detail/comparison/move/archive/permanent deletion. Real services remain
unentered and evaluation/accounting/audit snapshots unchanged. Permitted reads remain available.
See [exact coverage and exclusions](testing.md#evaluation-management-authorization); this does
not replace the remaining permission matrix or prove mutation/audit atomicity.

## Logging Rules
Do not log PII, raw secrets, raw long documents, full prompts by default, or provider credentials. Graph traces should be useful but privacy-conscious.

## Review Checklist
Every security-sensitive ticket must verify auth, workspace isolation, prompt injection handling, unsafe tool blocking, PII logging risk, and failure tests.


## Implemented In Milestone 8
- Deterministic prompt injection pattern checks.
- Citation-required, unsupported-answer, confidence-threshold, and language-preservation guardrail results.
- Guardrail results are persisted per graph run.
- Blocking guardrail failures route graph runs to human review.
- Pending human review records are created for low-confidence, no-source, or unsafe graph runs.
- Review APIs enforce workspace isolation and allow approve/edit/reject resolution.

Known limitations:
- Guardrails are practical deterministic checks, not comprehensive safety classifiers.
- No external policy engine or model-based judge is used yet.
- Review claim/release/resolve now lock the workspace-scoped row and refresh stale ORM state.
  Decision, graph outcome, checkpoint and audit share a transaction. Controlled PostgreSQL
  overlap and rollback tests cover this boundary; full permission coverage remains release work.


## Verified workflow entry boundaries
Dataset management and label editing have a separate
[six-actor admission matrix](testing.md#dataset-authorization-before-service-entry) covering
25 denied read/write requests before service entry and unchanged conversation/label/audit data.
Reviewers do not have dataset-read permission; permitted viewer/member/developer reads remain
available. This verifies existing policy rather than broadening access.

Knowledge upload/reindex/move/delete have a separate
[management admission matrix](testing.md#knowledge-management-authorization), covering six
actor categories with service-entry observers and unchanged index/usage/audit snapshots.
This establishes the tested denials, not complete management transaction or permission coverage.

Folder create/rename/delete now have a separate
[four-resource denial matrix](testing.md#folder-mutation-authorization-boundary): anonymous,
outsider, viewer and reviewer requests cannot enter the service or change folder/audit state.
Owner-positive populated reads prevent empty-fixture false confidence. This does not establish
permission coverage for every management route or concurrent folder-operation integrity.

The [workflow authorization matrix](testing.md#workflow-authorization-boundary-verification)
checks populated resources with real authentication/permission dependencies, owner-positive
reads, denied execution spies and unchanged ledgers. It covers anonymous/outsider disclosure,
viewer/reviewer write denial and developer/reviewer separation. Full route/resource-management
coverage remains open. [Real-role browser verification](testing.md#restricted-role-browser-verification)
now covers viewer/reviewer allowed reads, forged denied writes, foreign document/search IDs,
unchanged usage and a persisted reviewer rejection against PostgreSQL. No blanket security
claim or complete role-by-route proof is implied.
