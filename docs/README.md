# Documentation Map

Use this file to choose the smallest useful context set for each task. Do not read every Markdown file by default.

## Always Automatic
`AGENTS.md` is loaded by Codex automatically. It contains durable repo rules and should stay concise.

## Usually Read For Implementation
Read `docs/PROJECT_CONTEXT.md` for real implementation tasks. It contains standing rules for token economy, multilingual support, workspace isolation, evaluation, observability, and the human/Codex operating model.

## Quick Orientation
- Start here for a compact architecture and tools tree: `docs/architecture-tree.md`

## Planning And Governance
- Create or review a ticket plan: `docs/PLANS.md`
- Check milestone order or scope: `docs/milestone-plan.md`
- Check product intent or Phase 1/Phase 2 boundaries: `docs/product-spec.md`
- Check AI-native workflow expectations: `docs/codex-workflow.md`

## Backend And API Work
Read:
- `docs/architecture.md`
- `docs/database-schema.md`
- `docs/api-design.md`
- `docs/security-threat-model.md` when auth, permissions, workspace isolation, or sensitive data are involved

## RAG And Knowledge Work
Read:
- `docs/rag-design.md`
- `docs/token-economy-design.md`
- `docs/database-schema.md`
- `docs/security-threat-model.md` for retrieval leakage checks

## LangGraph And Tool Work
Read:
- `docs/langgraph-workflow-design.md`
- `docs/tool-execution-design.md`
- `docs/token-economy-design.md`
- `docs/observability-design.md`

## Evaluation Work
Read:
- `docs/evaluation-design.md`
- `docs/rag-design.md` when retrieval metrics are involved
- `docs/token-economy-design.md` when cost metrics are involved

## Frontend And Dashboard Work
Read:
- `docs/observability-design.md`
- `docs/api-design.md`
- `docs/product-spec.md` for workflow intent
- `docs/audits/platform-ux-backend-recovery-audit.md` for the approved UX/backend recovery roadmap when working on recovery tickets

## Security Review Or Red-Team Work
Read:
- `docs/security-threat-model.md`
- `docs/database-schema.md`
- `docs/api-design.md`
- relevant subsystem design docs

## Portfolio Packaging
Read:
- `README.md`
- `docs/product-spec.md`
- `docs/tradeoffs.md`
- `docs/scale-path.md`
- `docs/demo-script.md`
- `docs/interview-explanation.md`
- `docs/resume-bullets.md`
- `docs/known-limitations.md`
- `docs/screenshots/README.md`

## Learning Notes
Read `docs/learning/README.md` only when creating or updating learning notes.

## Rule Of Thumb
For most implementation tickets, read at most:
1. `docs/PROJECT_CONTEXT.md`
2. `docs/PLANS.md` if planning
3. one or two focused subsystem docs
4. the files being changed

If more context seems necessary, explain why before loading many additional docs.
