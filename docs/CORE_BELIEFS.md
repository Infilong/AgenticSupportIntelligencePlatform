# Core engineering beliefs

- Humans define goals, constraints, architecture judgment and acceptance criteria. Agents inspect,
  plan, implement, test, review and fix within that authorization; human judgment is not replaced
  by a passing test or a model's confidence.
- The repository is the system of record. Keep decisions, constraints, failures and verified
  outcomes in focused documents and execution plans, rather than relying on chat history.
- Load context progressively. AGENTS.md is a map and control layer; the documentation router
  directs a task to its owning documents. Do not preload every guide or duplicate its contents.
- Mechanical constraints beat repeated reminders. Use tests, lint, types, CI and architecture
  checks for enforceable rules; document remaining gaps instead of implying enforcement exists.
- Verification is implementation work. Match evidence to the claim: type checking is not a
  browser journey, mocks are not real AI quality, and successful startup is not recovery proof.
- Recurring agent failures should improve the harness. Preserve reproduction evidence, isolate
  the cause, then add a regression or improve commands/context. Blind retries are not a repair.
- Control entropy. Keep one owner for each concept, small cohesive files, declining legacy size
  limits and one canonical document per contract. Do not propagate a bad pattern for consistency.
- Be honest about scope. Implement the small-team product well before adding scale infrastructure;
  track unfinished invariants in the quality score and active plans.

## Basis and local choices
Reviewed 2026-09-07: OpenAI's [Codex best practices](https://learn.chatgpt.com/guides/best-practices)
recommend clear goals, relevant context and explicit completion criteria. Its
[AGENTS.md guidance](https://learn.chatgpt.com/docs/agent-configuration/agents-md) describes layered
repository instructions. This repository's filenames, scorecard and plan lifecycle are local
engineering choices implementing the user's requested workflow, not an OpenAI certification.

The user's source articles, [Harness engineering](https://openai.com/index/harness-engineering/)
and [How OpenAI uses Codex](https://openai.com/business/guides-and-resources/how-openai-uses-codex/),
were also checked on 2026-09-08, along with the AGENTS.md guidance above. The harness article supports a short instruction map,
repository-owned knowledge, progressive disclosure, persistent plans and mechanical checks.
Apply these practices to this project's needs; the articles do not certify this application's
security, AI quality or production readiness.
