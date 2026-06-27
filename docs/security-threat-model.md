# Security Threat Model

## Primary Risks
- user accesses another workspace's data
- retrieval leaks another workspace's chunks
- prompt injection forces system or raw document leakage
- unsafe tool calls bypass backend permissions
- PII is logged in traces or errors
- secrets are hardcoded or exposed
- evaluations or cost summaries leak cross-workspace data
- human review is bypassed for high-risk cases

## Required Controls
- authentication on protected routes
- workspace membership checks on workspace routes
- `workspace_id` filters on all workspace-owned queries
- retrieval filtering by workspace before ranking or returning chunks
- prompt injection detection
- unsafe tool call blocking
- citation-required validation
- unsupported answer refusal
- language preservation check
- token/cost limit checks
- structured output validation
- safety-risk escalation

## Required Permission Tests
Test that users cannot access another workspace's documents, datasets, examples, labels, graph runs, human reviews, evaluations, cost summaries, audit logs, or retrieval chunks.

## Logging Rules
Do not log PII, raw secrets, raw long documents, full prompts by default, or provider credentials. Graph traces should be useful but privacy-conscious.

## Review Checklist
Every security-sensitive ticket must verify auth, workspace isolation, prompt injection handling, unsafe tool blocking, PII logging risk, and failure tests.
