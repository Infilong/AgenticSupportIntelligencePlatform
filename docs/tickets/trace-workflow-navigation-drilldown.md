# Trace Workflow Navigation Drilldown

Date: 2026-06-28

## Goal
Make the trace viewer feel like a professional AI engineering debugger. A developer should be able to scan the full LangGraph execution path, filter important nodes, select a step, and inspect model/tool/state signals without reading raw JSON first.

## Context
The trace API already returns backend-supported data: graph steps, inline AI runs, tool calls, guardrails, checkpoints, runtime metadata, token/cost/latency fields, and step state keys. The UI presents this data, but the experience is still linear and heavy. The objective identifies the trace viewer as one of the most important proof surfaces for the platform.

## Requirements
- Add a trace execution navigator with filter modes for all steps, problems, model calls, tool calls, and LangChain nodes.
- Add a selected-step inspector showing step role, status, latency, tokens, cost, state keys, model call, tool calls, and compact output signals.
- Keep raw JSON available behind details, not as the primary reading path.
- Preserve existing runtime, checkpoint, guardrail, and timeline information.
- Do not change backend contracts unless the existing trace data is insufficient.

## Non-goals
- Do not add a new trace backend endpoint.
- Do not implement distributed tracing or OpenTelemetry spans yet.
- Do not add a graphical canvas.
- Do not remove raw JSON debug access.

## Design Plan
Frontend:
- Add local trace filter state inside `TraceViewer`.
- Derive filtered steps and selected step from existing `GraphTrace`.
- Add a navigator rail and selected-step inspector above the detailed timeline.
- Add compact CSS for black-and-white professional trace cards.

Backend:
- No backend changes expected. Existing `GraphTraceResponse` already has the needed fields.

## Test Plan
- Frontend typecheck and build.
- Full backend suite to prove no API regression if backend remains unchanged.
- Live smoke: run/load a trace and confirm API/frontend stay healthy.

## Acceptance Criteria
- Trace page shows a clear execution navigator.
- Filters make model/tool/problem/LangChain steps easier to find.
- Selected step has a readable drilldown before raw JSON.
- Timeline still shows all detailed step cards.
- No fake trace data is introduced.

## Human Review Checklist
- Confirm the trace page explains how an output was produced at a glance.
- Confirm raw JSON is available but not the main experience.
- Confirm filters do not hide the ability to inspect all steps.
- Confirm the UI remains stable with completed and human-review runs.

## Interview Notes
This ticket shows how to turn stored execution records into an operational debugging surface: the product exposes state transitions, model calls, tool calls, guardrails, cost, and checkpoint signals in a way a developer can use during incident/debug review.
