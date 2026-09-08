# API boundary guide

`main.py` mounts public liveness and `v1/router.py`; domain routers live in `v1/`.
See [API design](../../../docs/api-design.md) for intended contracts and the running
`/openapi.json` for the current generated schema.

## Implementing an operation

1. Define input/output schemas in `app/schemas/<domain>.py`.
2. Use `get_current_user` and the appropriate `require_workspace_permission` dependency.
   Named aliases such as `AgentRunAccess` in `v1/agents.py` show the current pattern.
3. Pass validated identifiers and explicit `workspace_id` into the service.
4. Translate expected domain errors into explicit HTTP status/code/message responses.
5. Test success, invalid input, missing identity, denied role and foreign-workspace IDs.

Role presets live in `services/workspace_service.py`: owner, developer, member, reviewer
and viewer. Archived workspace write restrictions are enforced by the permission dependency.
Frontend visibility is explanatory; never accept a frontend role as authorization.

## Boundaries and review traps

- A child ID is not authorization: verify its workspace even when its parent is already scoped.
- List/search/count endpoints need the same scope and filters; keep collections bounded.
- Public `/health`, registration and login are intentional exceptions to protected routes.
- Avoid logging credentials, request bodies, document text or raw provider error payloads.
- Existing large routers contain persistence/response shaping; extract touched responsibilities
  incrementally rather than copying those patterns into new endpoints.

Use [backend tests](../../../docs/testing.md) and update API docs for observable contract changes.
