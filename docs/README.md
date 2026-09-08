# Documentation router

Start with the task row below, then load only the code and focused references it needs.
[AGENTS.md](../AGENTS.md) is the instruction map. Do not read this entire tree by default.
Requirements/design documents are not evidence of implementation; consult the code and tests.

| Task | Start here | Load only if needed |
| --- | --- | --- |
| Understand product/scope | [Project context](PROJECT_CONTEXT.md) | [Product spec](product-spec.md), [milestones](milestone-plan.md) |
| Architecture/refactor | [Architecture](../ARCHITECTURE.md), [code map](code-map.md) | [Coding rules](../codingRules.md), relevant local guide |
| Plan or resume long work | [Plans](PLANS.md), [execution index](exec-plans/README.md) | Selected active plan and its evidence |
| Assess readiness | [Quality score](QUALITY_SCORE.md) | [Production audit](audits/production-readiness-2026-09-07.md), [limitations](known-limitations.md) |
| Debug/runtime/failures | [Reliability](RELIABILITY.md), [testing](testing.md) | [Observability](observability-design.md), [infra](../infra/README.md) |
| Backend/API | [Backend](../backend/README.md), [API guide](../backend/app/api/README.md) | [API design](api-design.md), [service ownership](../backend/app/services/README.md) |
| Schema/transactions | [Migrations](../backend/alembic/README.md) | [Database schema](database-schema.md), affected service/tests |
| Auth/permissions/security | [Threat model](security-threat-model.md) | [Reliability](RELIABILITY.md), affected route and workspace dependency |
| Knowledge/RAG | [RAG](rag-design.md) | [Tokens](token-economy-design.md), security and affected models |
| Graph/tools/review | [Graph workflow](langgraph-workflow-design.md) | [Tool execution](tool-execution-design.md), [observability](observability-design.md) |
| Evaluation/AI quality | [Evaluation](evaluation-design.md) | [RAG](rag-design.md), [tokens](token-economy-design.md) |
| Frontend/UI | [Frontend](../frontend/README.md), [UI design](ui-design-system.md) | Affected page/hook/API contract, [UX audit](audits/platform-ux-backend-recovery-audit.md) |
| CLI | [CLI guide](cli.md) | [Testing](testing.md), [task API](api-design.md) |
| Tooling/CI | [Scripts](../scripts/README.md), [testing](testing.md) | [CI workflow](../.github/workflows/ci.yml) |
| Workflow principles | [Core beliefs](CORE_BELIEFS.md) | [Codex workflow entry](codex-workflow.md) |
| Learning/decisions | [Learning index](learning/README.md) | [Tradeoffs](tradeoffs.md), selected plan Decisions |
| Demo/portfolio | [Root README](../README.md), [demo](demo-script.md) | [Scale path](scale-path.md), [interview](interview-explanation.md), [resume](resume-bullets.md), [screenshots](screenshots/README.md) |

## Ownership and history
Root ARCHITECTURE.md owns top-level flow/dependencies; code-map.md owns file locations.
RELIABILITY.md owns failure contracts; observability-design.md owns record/log shapes.
QUALITY_SCORE.md owns the dated status summary; testing.md owns commands and detailed evidence.
PLANS.md owns plan lifecycle; each execution plan owns its progress and decisions.

Existing tickets and audits remain historical records. The older architecture-tree.md is a
conceptual artifact; use the current code map instead. Fix a stale owning document rather than
creating another competing summary. Keep compatibility entry pages short when relocating docs.

## Maintaining the map
When a boundary changes, update its owning guide and any affected router links in the same
change. Keep dated execution details in plans and verification evidence in testing.md; standing
guides should remain useful across sessions. Label requirements separately from implemented
behavior, and retain superseded decisions as history rather than competing current instructions.
Run `python scripts/check_docs.py` after documentation edits. This gate checks maintained local
file targets and plan structure; manually review factual claims and heading links. Its exact
coverage and limitations live in the [tooling guide](../scripts/README.md).
