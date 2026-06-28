# Agent Evaluation Posture

## Goal
Make Agent Management show whether the selected agent has been evaluated recently and whether those evaluations passed, using backend-owned evaluation data instead of UI-only inference.

## Files Changed
Expected files:
- `backend/app/models/evaluation.py`
- `backend/alembic/versions/*_evaluation_run_agent_id.py`
- `backend/app/services/evaluation_runner.py`
- `backend/app/services/agent_service.py`
- `backend/app/schemas/evaluation.py`
- `backend/app/schemas/agent.py`
- `backend/app/api/v1/agents.py`
- `backend/tests/test_agents.py`
- `backend/tests/test_evaluations.py`
- `frontend/src/App.tsx`

## Design Reasoning
The Agent page already shows runs, cost, model route, and workflow node health. The objective also requires evaluation status for agents. Evaluation runs accept an agent_id today, but that link is not persisted, so per-agent evaluation posture cannot be trusted. This ticket stores the agent link and aggregates evaluation health into the agent summary API.

## Backend/API Impact
- Add nullable `agent_config_id` to `evaluation_runs`.
- Persist the selected/default evaluation agent on evaluation run creation.
- Return evaluation run agent IDs in evaluation responses.
- Extend agent summary with evaluation count, latest evaluation timestamp, pass rate, and failed evaluation count.
- Keep workspace isolation through existing workspace-scoped routes.

## Tests / Validation
- Backend tests prove evaluation runs persist `agent_config_id`.
- Agent summary tests prove evaluation posture is aggregated for the selected agent only.
- Run backend lint/tests and frontend build.

## Risks
- Historical evaluation runs will have null agent IDs until rerun; UI should say no agent-linked evaluations rather than pretending.
- Baseline-only evaluations with no agent should remain valid.
- The summary should not scan unrelated workspaces or unrelated agents.

## Manual Review Checklist
- Run a system-v1 evaluation for an agent and confirm Agent page shows evaluation status.
- Confirm another agent does not inherit that evaluation posture.
- Confirm baseline-only evaluations do not falsely attach to an agent.

## Before / After Behavior
Before: Agent page showed runs and workflow health but no backend-supported evaluation status.
After: Agent page shows linked evaluation run count, pass rate, failed result count, and latest evaluation time for the selected agent.
