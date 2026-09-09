# Support processing

Read the backend guide and the M2 execution brief before changing this module.
- Preserve original messages; workspace-scoped runs own state and cancellation independently of jobs.
- Development responses are attributed contributions, never external API/billing proof.
- Authenticate before idempotency lookup; check original requester and contributor on resume.
- Validate every packed source and exact citations before export and fenced publication.
- Graph checkpoints are internal; expose domain records only. Do not accept client graph state.
- Keep API, validation, context, persistence and graph orchestration in separate cohesive files.
