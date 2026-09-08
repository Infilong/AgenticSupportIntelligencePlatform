# M0 preparation review — 2026-09-08

Verdict: aligned in direction, partially executable. Preparation is sufficient to begin the
authorized foundation milestone once requested; it is not proof of autonomous product delivery.
Review covered current working-tree preparation, including uncommitted instruction changes.
A separate read-only agent reviewed the instructions independently; the coordinator checked
the actual harness and official articles, reconciled findings and made documentation corrections.

## Refined execution prompt for this review

Audit M0 against the two OpenAI articles and the user's intended autonomous workflow. Inspect
the files and executable preparation checks, identify contradictions and missing capabilities,
and distinguish necessary next steps from premature infrastructure. Correct focused documentation
issues, verify links and preparation tests, and report unresolved gaps with an owning milestone.
Preserve existing edits and M0 isolation. Do not start M1, spend API budget or publish changes.

## Evidence and alignment

The articles recommend scoped planning, issue-like prompts, persistent repository context,
iterative environment improvements and agent review/verification loops:
[How OpenAI uses Codex](https://openai.com/business/guides-and-resources/how-openai-uses-codex/)
and [Harness engineering](https://openai.com/index/harness-engineering/).
They describe practices and an internal experiment, not a production certification standard.
Our explicit self-written execution brief is a local adaptation, not a quoted universal requirement.

| Area | Current evidence | Assessment |
| --- | --- | --- |
| Concise root with focused context | Root routes to six short local guides | Aligned; avoid copying rules into more files |
| Intent translated into execution | DEVELOPMENT defines outcome, brief, checks, repair and next slice | Specified; now includes review/planning requests |
| Reproducible preparation | Doctor, pinned browser, fixture checks and source-linked reports | Executable locally; no app runtime yet |
| Agent-visible application behavior | Only synthetic browser page exists | Missing by design until M1 |
| Enforced architectural/doc constraints | Link test covers root/docs only; no CI or import-boundary rules | Partial; prose is not enforcement |
| Durable progress and quality | STATUS, release gates and evidence distinguish planned/unverified | Useful; full execution/repair cycle still needs demonstration |

## Findings and disposition

| Priority | Finding | Disposition |
| --- | --- | --- |
| P1 | Root prohibited progress even across authorized milestones | Fixed: stop at authority boundary; M0 still excludes M1 |
| P2 | Two execution-plan directory conventions | Fixed: use release-plan `docs/plans/active` and `completed` |
| P2 | Delegation wording exceeded release's read-only review scope | Fixed: explicit bounded read-only delegation |
| P2 | Prompt refinement omitted reviews/research/planning | Fixed: every nontrivial request gets a brief, without extra approval |
| P2 | Review findings lacked explicit disposition | Fixed: record fixed/deferred/rejected findings and unresolved severity |
| P2 | Local guides are outside automated link coverage | Deferred to first M1 harness slice: cover nonignored local guides and size bounds, including broken-link/oversize failure checks |
| P2 | Runtime/browser/log loop is unproven | M1: demonstrate actual login and workspace denial, correlate request logs, reproduce a controlled failure and verify recovery |
| P2 | CI and architecture enforcement are only planned | M1: run deterministic checks in CI; add boundary checks as modules appear, with actionable failure messages |
| P3 | Runbook claimed an old stack is currently running | Fixed: timestamp the observation and require live reinspection |
| P3 | STATUS pointed to a mutable summary as checkpoint evidence | Fixed: distinguish latest summary from immutable timestamped reports |

## What to add next, without expanding the product

- M1: implement the runnable isolated foundation and its real browser/API/database evidence.
  Bind acceptance IDs to commands, outcomes and artifacts in the first execution record.
- M1: add lightweight structured logs accessible by request/run ID and bounded inspection
  commands. An external observability platform is unnecessary for this small local release.
- Before M2 tuning: expand the coherent corpus/cases and freeze numeric quality thresholds,
  as already required by ACCEPTANCE. Fifteen seed cases do not establish RAG quality.
- At each completed slice: check affected guides against implementation and record remaining
  gaps in STATUS/the active plan. Add regression checks for recurring defects when justified.

Do not add a custom prompt-generation service, broad agent hierarchy, Redis, cloud stack,
automatic merge authority or scheduled cleanup to imitate the articles. Existing commands and
focused review can implement the feedback loop. Additional documentation alone will not prove it.

## Verification limits

Use the latest timestamped preparation report for the updated working tree. The separate
link/length inspection includes local guides; it does not upgrade the committed test's coverage.
Browser/runtime tests are not rerun for this documentation-only review. Prior browser evidence
belongs to the M0 source snapshot and becomes stale under the whole-repository fingerprint.
No source implementation changed. Remaining findings above are explicitly deferred, not passed.
