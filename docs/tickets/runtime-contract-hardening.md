# Runtime Contract Hardening

## Goal

Make every advertised control affect runtime behavior and make the README demo reproducible from a fresh clone.

## Context

The current application has a real LangGraph workflow, LangChain model/tool integrations, workspace isolation, and trace persistence. A source review found several places where configuration or documentation is more capable than the execution path.

## Verified Findings

1. Active prompt-template records are attached to AI-run metadata, but classification and drafting execute module-level hard-coded prompts.
2. Model planning checks context capacity, but does not reserve against a shared run-level token and cost budget before every call.
3. The documented `check_policy_and_tone` step is not a LangGraph node.
4. Tool timeout and retry settings are returned as metadata but are not enforced by the invocation path.
5. Evaluation baseline names overstate what the mock and canned adapters execute, and evaluation runs lack a partial terminal state.
6. Unexpected graph exceptions can leave a run in `running`.
7. The browser demo seed does not provision the complete advertised workflow.
8. CI does not exercise the complete PostgreSQL-backed browser demo.

## Delivery Order

1. Active prompt execution, template-variable validation, and rendered-prompt attribution.
2. Run-level token and cost budget enforcement.
3. Complete idempotent demo reset, seed, and smoke commands.
4. Explicit policy-and-tone graph node with routing influence.
5. Tool deadline and retry execution with attempt trace data.
6. Truthful, ledgered evaluation modes and partial/failed status handling.
7. Guaranteed terminal graph-run state after exceptions.
8. PostgreSQL, migration, API, frontend, and Playwright demo coverage in CI.

## Non-goals

- Broad frontend redesign.
- Kubernetes, Terraform, or distributed infrastructure.
- Unrelated refactors of existing large modules.
- Claims that future-scale components are already implemented.

## Responsibility Boundaries

- Prompt parsing and variable policy: focused prompt-runtime module.
- Prompt lifecycle: prompt-template service and thin API error mapping.
- Model execution: LangChain chain helpers.
- Orchestration: minimal LangGraph call-site wiring.
- Token and cost reservations: dedicated run-budget service.
- Demo provisioning: idempotent script and Make targets.
- Tool execution policy: dedicated invocation wrapper.
- Evaluation semantics: evaluation adapters and run-status service logic.
- Persistence: focused migrations and model fields.
- Verification: unit, API integration, PostgreSQL integration, and browser smoke tests.

## Test Plan

- Provider-capture tests prove an activated prompt changes the exact provider input.
- Invalid and missing template variables are rejected on creation and activation.
- AI runs store a hash of the rendered prompt actually sent.
- Budget tests exercise token and cost breaches before model invocation.
- Graph tests prove every documented node and terminal state.
- Tool tests exercise timeout, transient failure, retry exhaustion, and attempt persistence.
- Evaluation tests prove each advertised mode and failed/partial status.
- Demo smoke starts from reset state and follows the README path.

## Acceptance Criteria

- No visible configuration is metadata-only.
- The trace and AI ledger describe what actually executed.
- A fresh clone reaches the complete demo through documented commands.
- All model calls obey run and workspace budget policy.
- Every graph and evaluation run reaches an honest terminal state.
- Focused tests, the complete backend suite, lint, frontend build, and browser smoke pass.

## Risks

- Prompt templates can become an injection or formatting boundary if arbitrary variables or roles are accepted.
- Budget reservations can race or double-charge if accounting is not transactional and idempotent.
- Retrying non-idempotent tools can duplicate side effects.
- Demo reset can destroy user data if it is not explicitly restricted to demo identities.
- Baseline comparisons can remain misleading if model/provider differences are not shown.

## Human Review Checklist

- Confirm prompt text sent to providers matches the active version and stored hash.
- Confirm workspace ownership is present on every new query and write.
- Confirm budget failures route to review without making a model call.
- Confirm retries are allowed only for safe tools or use idempotency controls.
- Confirm demo reset targets only documented demo resources.
- Confirm README claims match executable behavior.

## Interview Notes

- Explain why prompt provenance requires both version metadata and a rendered-content hash.
- Explain reservation-based budget enforcement versus reporting usage after a call.
- Explain why bounded LangGraph nodes are preferable to uncontrolled autonomous agents.
- Explain how honest baselines and reproducible demos improve evaluation credibility.
