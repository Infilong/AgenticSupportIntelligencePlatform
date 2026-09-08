# Rebuild requirements QA

Date: 2026-09-08. Verdict: does not yet meet the approved rebuild requirements.
Scope: running new interface at http://localhost:5174/rebuild.html, current source,
and focused browser tests. This is an acceptance review, not a production-readiness claim.

## Live evidence
- Preview HTTP response: 200. Chrome opened the actual application using its existing session.
- Navigation contains only Knowledge; no Work, Agents, Activity or Settings.
- Opened Rebuild QA policy: content and Version 2 displayed. No next action leads
  from a document to agent configuration, a task or a cited answer.
- Open existing application leads to the old interface with repeated metric panels,
  technical descriptions and Owner/Developer/Reviewer/Viewer role terminology.
  This is a migration fallback, not completion of the simplified user journey.
- Current WorkspaceRole source still includes owner/developer/reviewer/viewer/member.
- Current run_agent service executes the graph synchronously and publishes its outcome.
- New source tree contains session, knowledge, editor, API and styling modules only.
  No CLI implementation was found by filename search; no asi entry point is declared
  in backend/pyproject.toml. Required CLI commands were not demonstrated.

## Requirement matrix
| Requirement | Current evidence | Verdict |
| --- | --- | --- |
| Clear five-area navigation; Work landing | Only Knowledge exists | Missing |
| Modern, simple UI | Restrained desktop knowledge screen; old-app escape returns complex UI | Partial |
| Upload/search/edit/remove knowledge | Real backend browser regressions pass | Implemented narrow slice |
| Processing failures and recovery | File extension validation tested; failed backend ingestion/retry not demonstrated this review | Unverified |
| EN/JA/ZH cited answers | No task/question interface in rebuild | Missing from new experience |
| Agent instructions/model/knowledge/tools | No Agents screen | Missing |
| Bounded agent actions | No new action workflow or action approval interface | Missing |
| Human approval/edit/rejection | No task/review interface | Missing |
| Stop active run; prevent later effects | No Stop control; current execution synchronous | Missing |
| Shared run detail and activity | Neither implemented in rebuild | Missing |
| Duration/model/tokens/cost/errors | Not visible in rebuild | Missing |
| Viewer/Operator/Admin/Owner | Existing role definitions differ | Not met |
| Backend permissions and isolation | Viewer upload rejected; UI hides upload | Partial; not full new-role coverage |
| Navigation/refresh consistency | Knowledge reload covered; full application workflow absent | Partial |
| Shared API and working CLI | Knowledge reuses API; CLI commands absent | Partial foundation only |
| Accessibility and responsive behavior | No complete keyboard/mobile acceptance run | Unverified |
| Real-provider behavior | No real-provider task run in this review | Unverified |

## Tests run now
`FRONTEND_URL=http://localhost:5174 npm run test:e2e -- rebuild-knowledge.spec.ts --workers=1`
Executed through PowerShell with the environment variable set before npm.
Result: 2 passed in 6.8 seconds against the running backend.

Coverage: registration, workspace creation, invalid file extension, Japanese Markdown
upload, explicit Chinese language revision, search, removal confirmation/cancellation,
refresh, viewer UI restriction and backend upload denial.
These tests do not prove the agent product, cancellation, role migration or CLI.

## User-facing gaps
1. The core journey ends after knowledge management. There is no AI task to perform next.
2. The old-application link makes users switch between incompatible navigation systems.
3. The existing synthetic policy contains Chinese text but still has its earlier JA label.
   It predates the explicit language selector; current tests verify selecting ZH on edit.
   Existing metadata is not automatically corrected. Language-mismatch feedback remains absent.
4. Completed implementation is a knowledge-management slice, not the requested RAG agent app.

## Required next work
Continue the approved plan: complete Work + Agents + shared run detail as an end-to-end
journey, then durable execution, action approval/cancellation, fixed roles, Activity,
Settings and CLI. Verify each boundary; do not substitute the legacy UI for missing areas.
No application source or existing user data changed during this review. Regression tests
created disposable QA accounts/workspaces. Full rebuild acceptance remains open.
