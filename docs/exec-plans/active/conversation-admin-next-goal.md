# Conversation administration and verified RAG — proposed next goal

## Goal

Build a polished, intuitive AI support administration app in this repository. Administrators
should understand user questions, inspect AI answers and evidence, manage company knowledge,
and intervene when necessary. An embedded assistant should help them investigate and act.
Keep the visible product simple while implementing a reliable LangChain, LangGraph and real
RAG workflow underneath. Quality is defined by observed user journeys and evidence, not feature count.

Status: superseded by [data processing administration](data-processing-admin.md), 2026-09-08.
This historical proposal does not authorize implementation.
It supersedes the earlier five-area product direction only after approval.

## Context

Inspected current WorkspaceApp, Work, Reviews, RunDetail, RunSources, DocumentEditor,
workspace.css, support_graph_builder and retrieval_service, plus the architecture and context.
Used the running app in Chrome: workspace selection, Work, the existing `w` review,
Inspect evidence, and Knowledge upload editor. No app data or implementation was changed.
The inspected browser error log was empty; this was a focused desktop review, not a full
responsive, accessibility, security or production audit.

Confirmed findings:
- Work mixes a review queue, submission form, execution details and history. Activity repeats history.
- Clicking Inspect evidence renders the detail below the submission form without moving focus
  to it; the resulting detail was outside the visible viewport in Chrome.
- The `w` request is pending review with `citation required, unsupported answer` as its explanation.
- The screen prioritizes running test requests instead of monitoring user conversations.
- Source labels expose chunk identifiers; settings and form controls occupy disproportionate space.
- Upload accepts only UTF-8 text/Markdown, up to 2 MB; it is not a company-PDF ingestion experience.
- The graph has finalization/review branches but no explicit clarification conversation branch.
- Retrieval defaults to lexical search with mock embeddings; its vector path loads candidates
  and scores them in Python. Database-native ranked vector retrieval is missing from that path.
- The current UI has no embedded administrator assistant. Existing dataset conversation examples
  must not be mistaken for an operational conversation/message model.
- Current documentation explicitly routes missing evidence to review; this product rule must change.

Earlier live investigation in this conversation found `w` used lexical retrieval with no source;
pgvector was installed and all 1,029 embeddings were mock. Recheck runtime before implementation.
The working tree has extensive pre-existing changes: preserve them and capture a baseline.

Reference: https://github.com/langgenius/dify — use its ingestion, workflow and observability
concepts selectively. Do not copy its entire platform, add a canvas editor, or assume licensing
permits copying code without checking. This is not a Dify fork.

## Requirements

### Product and visual design

Three navigation areas: Conversations, Knowledge, Settings. An Ask assistant control is always
available. Merge Work/Activity into Conversations; move occasional agent configuration into Settings.

Conversations uses a compact searchable inbox and selected conversation pane on desktop.
Show user identity where available, timestamps, question/answer messages and understandable status.
Use an attention filter rather than a second duplicate list. Identify synthetic test requests.
Provide a clearly labeled Test assistant entry and a scoped API/CLI submission path; do not invent
customer identities or build an external customer portal or channel integrations in this goal.

The selected conversation contains its messages and one relevant next action. Show sources beside
the answer through concise document/section labels. Open evidence in context without losing the
conversation. Put workflow steps, model/provider, tokens, estimated cost, errors and timing under
How the AI answered. Show observable events and evidence, never private chain-of-thought.

Use consistent typography, spacing, neutral surfaces, restrained accent colors, semantic status
styles, clear button priorities and accessible focus. Avoid large empty cards and form-first layouts.
Long documents, long names, CJK text, tables and errors must remain readable. Support keyboard use,
200% zoom and responsive layouts at 360, 768, 1280 and 1440 CSS-pixel widths. On narrow screens,
show list/detail sequentially with Back navigation; do not squeeze desktop columns into mobile.
Provide deliberate loading, empty, error, offline, permission-denied and reconnect states.
Opening an item must visibly reveal and focus its content; preserve relevant navigation/filter state.

Knowledge provides upload, processing progress, extraction preview, ready/failed state, retry,
version history and removal. Support text-based PDF, Markdown and text. Reject scanned PDFs with
an actionable explanation when OCR is unavailable; OCR is outside this goal. Processing must be
durable and bounded, with worker recovery and no silent truncation. Distinguish effective policy
dates from upload dates. Preserve exact historical citations while new queries use applicable policy.

Settings contains provider readiness, knowledge/model configuration and members. Retain Viewer,
Operator, Admin and Owner. Clearly identify demo mode and missing provider configuration before
the first request. Never display simulated cost as actual provider billing.

### Workflow and RAG

Add persistent conversations/messages linked to runs and interventions, with explicit actor and
workspace ownership. Follow-up clarification continues the same conversation; it is not a new
unrelated task. Keep customer support conversations separate from administrator assistant sessions.

Use LangChain for model/prompt/tool/structured-output boundaries and LangGraph for explicit state
transitions. Route input to clarification, knowledge answering, authorized tools, or genuine human
review. Meaningless input such as `w` asks for clarification without creating a review. Do not use
a blanket minimum-length rule: short valid replies and CJK questions must work in context.
Missing knowledge should produce an honest response and useful next step. Define explicit reasons
for escalation; no-source alone does not require an administrator. Clarifications/greetings do not
require citations. Company-policy assertions do. Handle prompt injection as untrusted input.

Implement real document/query embeddings with matching provider/model/dimensions, and pgvector
ranking in SQL with workspace/document authorization applied before results enter model context.
Bound top-k and context tokens. Use lexical retrieval where useful without silently replacing a
configured semantic path. Inspect query plans and justify the exact-search/index choice at the
tested scale. Record retrieval strategy, scores, selected passages and embedding/model costs.
Reindex safely when embedding configuration changes; do not mix incompatible vectors.
Handle multilingual and cross-language queries without an unconditional language filter excluding
relevant authorized evidence. Ground answers in applicable policy sections and cite exact versions.

Preserve durable work, stop checks, budgets, audit and exact-action approvals. Make intervention
clear: edit an answer, approve/reject a proposed action, stop work, retry with corrected instructions.
Stopping prevents subsequent work; it cannot undo completed effects or guarantee zero provider cost.
Distinguish execution duration, provider latency and time awaiting human review.

### Embedded administrator assistant

Provide a contextual assistant panel with a visible scope, conversation history, cited results and
links to records. It can search conversations/knowledge, inspect a selected run, explain failures,
summarize permission-scoped issues and suggest missing policy coverage. Summaries must query real,
bounded data and state their time range and coverage; never invent totals from a partial page.

Start with these read tools and only the necessary existing mutation tools: stop a run, propose
an answer/review decision, and propose a knowledge change. Mutations require explicit confirmation
bound to exact inputs, server-side permission checks, audit and idempotency. Do not auto-publish
assistant suggestions or expose arbitrary SQL, shell or unrestricted tools. Authorization is enforced
on every call, including after role changes. Malicious document text cannot grant tool authority.

## Non-goals

No customer portal, external channel integrations, OCR service, workflow canvas, plugin marketplace,
arbitrary-code agent tools or enterprise infrastructure expansion. No implementation during this
proposal review. Keep existing unrelated work intact.

## Acceptance Criteria

- Admin can find a request, read its answer, open its source and understand its status without
  navigating between duplicate pages. Evidence is reachable in one action from the selected answer.
- Main journeys pass visual inspection at all stated widths and 200% zoom, with no clipped controls,
  overlapping text, unintended horizontal page scrolling, lost focus or inaccessible primary actions.
- Keyboard navigation and automated accessibility checks pass on the primary flows; resolve all
  serious/critical findings. Automated checks do not replace visual and keyboard review.
- `w`, greetings, valid short follow-ups, unknown answers and genuine review cases follow distinct,
  tested routes. Clarification does not create an unnecessary administrator task.
- Real-provider evidence proves document ingestion, embedding calls, SQL vector ranking and grounded
  answers. Mock-only evidence is insufficient. Preserve raw failures alongside summaries.
- Long-policy evaluation meets the predeclared targets below, with results split by language and case
  type. No aggregate score may conceal an unresolved critical policy or permission failure.
- Stop, approval, retries, provider failure and permission changes have happy/failure/denial coverage;
  no duplicate effects or cross-workspace leaks in the security acceptance suite.
- The embedded assistant answers an investigation question from actual records, opens its evidence,
  and performs one explicitly approved action. Unapproved or unauthorized effects are denied.

## Plan

1. Baseline and design: capture revision/diff, runtime and recovery point; document migrations and
   keep/replace decisions. Produce browser-reviewable layouts for populated inbox, selected answer,
   review, upload failure and assistant panel. Review these before broad implementation.
2. Conversation/workflow foundation: add scoped persistence and clarification/no-answer branches;
   preserve existing run history and worker guarantees. Prove routing before UI integration.
3. Real RAG: implement durable PDF/text ingestion, real embeddings, database ranking, versions and
   evidence records. Verify with the long policy collection before adding answer polish.
4. Main interface: implement the three-area design, conversation details, inline intervention and
   source reading. Move occasional configuration and eliminate duplicated entry points.
5. Administrator assistant: integrate scoped read tools, then confirmed mutations and permission
   tests. Keep its history and purpose separate from customer support.
6. Acceptance: run full user journeys in Chrome, visual/accessibility checks, real RAG evaluation,
   recovery/security tests and built-app verification. Fix findings and update current owning docs.

## Verification

Create a coherent synthetic company handbook of 30–50 rendered pages, related procedures/FAQs,
regional EN/JA/ZH materials, tables, exceptions, cross-references and effective dates. Include an old
and replacement policy with explicit precedence. Do not pad documents to reach a page count.
Use meaningful policy breadth, not tiny paragraphs, as the primary RAG evidence.

Create 90 separately maintained evaluation questions, 30 per language. Cover paraphrases, buried
facts, multi-section evidence, conflicting-looking rules, exceptions, updates, cross-language
retrieval, missing knowledge and clarification. Store expected supporting sections and acceptable
answers. Freeze a held-out subset before tuning; report both development and held-out results.

Proposed minimum gates to freeze at baseline: at least 90% required-evidence recall@5 on answerable
cases; at least 90% fully correct grounded answers; at least 95% supported-citation precision;
at least 90% correct missing-knowledge/clarification handling. Define scoring denominators and
multi-section coverage explicitly. Report counts, per-language results and reviewed failure examples;
do not rely solely on an LLM judge. Require all critical exception/version cases and access-denial
tests to pass. Never lower gates just to report success.

Record corpus size, provider/model, query-plan evidence, p50/p95 latency, token/cost data and exact
commands/artifacts. Establish performance budgets on the actual configured hardware/provider during
baseline. Test one document update, worker interruption, provider outage and restore/migration path.
Use deterministic tests for regression and real providers for semantic-quality acceptance.

## Risks

Credentials and provider spend must be available for real acceptance; otherwise mark it blocked,
not complete. Existing mock documents need explicit reindexing. Conversation migrations must not
erase runs or fabricate history. The existing dirty tree needs a recoverable baseline, not reset.
Long policy tables and extraction boundaries can corrupt meaning; inspect extraction and citations.
Assistant mutation scope and policy precedence must remain explicit and testable.

## Decisions

Proposed: one default support workflow, three main areas, an embedded admin assistant, no canvas
builder, no external messaging integration, no general-purpose autonomous agent, no broad rewrite
of sound authorization/accounting code. Retain API/CLI access and update their contracts as needed.
Use only OpenAI development tools/skills. No commits or destructive data cleanup without authority.

## Progress

2026-09-08: focused code/Chrome review complete; proposal prepared. No implementation started.

## Findings

The primary defect is the product model: the app presents execution machinery instead of a clear
conversation and administration journey. Styling alone will not fix that. Existing backend safety
and trace boundaries are useful foundations; real semantic retrieval and clarification need work.

## Final Result

Pending user review. After approval, complete the accepted milestones and provide evidence for
each acceptance criterion. Do not claim production readiness from builds or mock demonstrations.
