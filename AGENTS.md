# Repository instructions

## Project
Local-first Multilingual Agentic Support Intelligence Platform for a small internal team.
English, Japanese and Chinese are first-class. Build a production-minded platform; do not
claim enterprise infrastructure or production readiness without evidence.

## Context map
- Start with [docs/README.md](docs/README.md); load only the relevant task row.
- Structure: [ARCHITECTURE.md](ARCHITECTURE.md), then the linked local module guide.
- Before source edits: [codingRules.md](codingRules.md).
- Product decisions: [project context](docs/PROJECT_CONTEXT.md) and [product spec](docs/product-spec.md).
- Planning/history: [PLANS](docs/PLANS.md) and [execution plans](docs/exec-plans/README.md).
- Quality and failures: [QUALITY_SCORE](docs/QUALITY_SCORE.md), [RELIABILITY](docs/RELIABILITY.md).
- Commands/evidence: [testing](docs/testing.md). Principles: [CORE_BELIEFS](docs/CORE_BELIEFS.md).

## Task workflow
1. Understand the goal, constraints and acceptance criteria; inspect relevant code and docs.
2. Classify: simple work can proceed directly; complex/high-risk work needs a plan first.
   Persist a plan only for the criteria in PLANS.md. Keep one focused implementation owner.
3. Implement, verify, review and fix until the accepted scope is complete. Preserve unrelated edits.
4. Update the owning docs and evidence; record durable decisions in the plan and learning notes.
   Continue within existing authorization. Ask only when a decision or action needs new authority.

## Agent delegation
Do not spawn agents by default. Use them only when independent search, root-cause analysis,
verification, security or performance review materially improves the outcome. Give each a
bounded task and ownership; keep tightly coupled changes under one owner and never revert
others' edits. If routing is available and permitted, use a lightweight model for search and
mechanical work, a mid-tier model for ordinary implementation/tests, and the strongest model
for architecture, security or difficult debugging. Respect session restrictions and actual tools.
Use only OpenAI-provided tools and skills.

## Core invariants
- Backend owns authentication, authorization, schema, persistence, evaluation and accounting.
- Every workspace-owned entity has workspace_id. Check permission before protected data enters
  retrieval, tools or model context; frontend controls never replace server enforcement.
- Every model call needs an AI ledger record; graph nodes and retrieval calls need trace data.
  Account for token/cost use and failures. Route unsafe/unsupported cases explicitly to review.
- Prefer deterministic code; retrieve/filter/compress before model calls. Never send raw long
  documents. Automated tests use deterministic mock LLM/embedding providers.
- Uploaded/imported resources need permission-gated management and bounded/searchable lists.
- Keep files cohesive, normally under 300 lines. Existing oversize exceptions may not grow.
  Never add fake implementations, hidden broad exception handling, secrets or PII in logs.

## Verification and failure handling
Run checks for the changed boundary using testing.md. Features require happy-path, failure
and permission-denial coverage; UI behavior requires browser evidence, not only type checks.
Inspect the diff and fix unresolved P0/P1 issues before calling the feature done. Preserve
failed evidence, diagnose the cause, and turn recurring failures into tests or harness checks.
Never weaken assertions or hide failures to make a run green. Revalidate live process handles
before restarting work. Report missing verification honestly; do not infer readiness from setup.

## Progress
Work autonomously. At meaningful checkpoints report Done, Current, Next and Blocker as relevant;
do not end work just to report. Final output names changes, verification and remaining limits.
