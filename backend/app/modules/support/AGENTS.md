# Support processing

Read the backend guide and the current execution record linked from root docs/STATUS.md.
- Preserve original messages; workspace-scoped runs own state and cancellation independently of jobs.
- Development responses are attributed contributions, never external API/billing proof.
- Authenticate before idempotency lookup; check original requester, current attempt creator
  and contributor on resume. New attempts retrieve under their creator's current authority.
- Keep linked attempts immutable and sequence-scoped; preserve original input and prior decisions.
  Validate actual customer input, never application-added labels or later attempts' details.
- Validate every packed source and exact citations before export and fenced publication.
- Graph checkpoints are internal; expose domain records only. Do not accept client graph state.
- Keep API, validation, context, persistence and graph orchestration in separate cohesive files.
