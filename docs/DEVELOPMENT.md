# Development workflow

## Demand-to-evidence loop

Codex owns this loop during active work. The user supplies intent, constraints and authority;
Codex supplies the technical execution prompt and carries it through verification.

1. **Demand:** restate the observable user outcome, scope and acceptance ID. Separate required
   behavior from assumptions and deferred ideas. Do not turn incidental findings into new scope.
2. **Assess:** inspect relevant code, guides and evidence; reproduce defects when applicable.
   Classify complexity and summarize the chosen approach, key risks and unresolved decisions.
   Resolve routine choices yourself; ask only when a material decision or authority is missing.
3. **Prompt:** write the execution brief below for each nontrivial task, including reviews,
   research and planning, before substantive execution. This is an
   actionable specification for yourself or a delegated agent, not a request for another user prompt.
4. **Implement:** deliver the smallest connected slice that advances the user outcome. Reuse
   existing capabilities, keep one owner and avoid unrelated scaffolding or abstractions.
5. **Verify and review:** run the brief's checks, inspect the diff against the original demand,
   exercise affected browser/runtime flows and inspect relevant logs when available. Report
   acceptance evidence, including failures and missing checks; tests passing alone is insufficient.
6. **Repair:** diagnose failures, update the brief with the finding and fix the cause. Re-run
   affected checks. For recurring failures, add a focused regression or improve the harness
   when justified. Never lower the acceptance bar or repeat an unchanged failing approach.
7. **Advance:** compare remaining acceptance gaps with the authorized goal. Select the next
   dependency-ready slice that closes a meaningful gap, write its brief and continue without
   waiting for “continue.” Stop when the goal is verified, the authorized boundary is reached,
   a real blocker requires input, the user pauses work, or the unattended limit is reached.

An authorized multi-milestone goal may proceed across its included milestones. M0-only authority
does not authorize M1. This workflow does not schedule background execution after a turn ends.

## Codex-written execution prompt

For a small task, put a compact brief in the working update; simple answers need only a clear
restatement where helpful. Do not turn routine requests into paperwork or approval gates.
For complex or multi-session work, keep a single execution record at
`docs/plans/active/<task>.md` and link it from STATUS. On completion, move it to
`docs/plans/completed/` and update the link, following the release plan's topology.
Create that file only when needed; update it for repairs instead of generating repetitive prompts.
Record concise decisions and evidence, not a private reasoning transcript.

```text
User outcome / acceptance IDs:
Authorized scope / exclusions / spending and external-action limits:
Observed state / relevant paths and local AGENTS.md guides:
Chosen approach / brief rationale / assumptions and risks:
Implementation slice / owner / dependencies:
Verification: commands and real user flows; expected pass/fail evidence:
Completion conditions / stop conditions:
After execution: results and artifact paths / unresolved gaps / next action and why:
```

Anchor checks to the user requirement before implementing. Include happy-path, failure and
permission-denial checks where relevant. Mark unavailable checks explicitly and implement
necessary verification capability within scope; do not invent commands or claim untested quality.
The same brief can be used for delegation; self-prompting does not require another model call.

## Efficiency and completion

- At a task's start or when blocked, proactively consult relevant primary documentation and
  existing project evidence. Record an actionable lesson in its owning guide or check; do not
  wait for the user to extract tactics. Explain when a source's tradeoff does not fit this app.
- Load only the relevant guide chain; batch independent reads and run focused checks first.
- Broaden verification for changed boundaries and unresolved risk, not to produce more test output.
- Assess progress by closed acceptance gaps and usable flows, not files, prompts or commits produced.
- At checkpoints, update STATUS with the active execution record, verified outcome, evidence,
  remaining gaps and exact next action. Preserve the original demand when new feedback arrives.
- If review finds work outside authority, record it as deferred and continue unaffected work.
  Completion requires the agreed checks and review; missing proof remains an explicit limitation.

This is the repository's adaptation of OpenAI's guidance on
[scoped planning and issue-like prompts](https://openai.com/business/guides-and-resources/how-openai-uses-codex/)
and [agent implementation, review and feedback loops](https://openai.com/index/harness-engineering/).
It is a working protocol, not evidence that this application's full loop has already been proven.

Keep source files cohesive, normally under 300 lines. Split by responsibility; propose a split
before exceeding that size without a concrete reason. Avoid empty architecture scaffolds and
duplicate implementations. Area instruction files are useful preparation, not implemented services.

## Delegation and context

Use bounded read-only independent investigation/review only when it materially helps. Supply an agent
with the objective, owned paths, relevant root/local guide paths, acceptance criteria and
expected evidence. Require it to read those files; do not assume a root-started agent has
automatically loaded every descendant guide. Tell it that others may be working and to preserve
their edits. Keep tightly coupled changes with one owner and integrate results before completion.
Record each review finding as fixed, deferred with reason/owning milestone, or rejected with
evidence. Unresolved critical or high-severity defects prevent completion; a clean review without
executed acceptance checks is not proof. If no independent review ran, say so rather than imply it.

Root guidance provides direction; local guides carry area rules. Create a deeper `AGENTS.md`
only when a module needs distinct guidance, and link it from its parent guide. Keep each under
200 lines. Store implementation recipes in owning design/runbook documents and read on demand.
This organization follows [OpenAI's nested instruction guidance](https://developers.openai.com/codex/guides/agents-md/).

## Verification and authority

- [Acceptance](ACCEPTANCE.md) defines the proof required; [runbook](RUNBOOK.md) lists real commands.
- Separate fixture checks, software correctness, actual browser journeys and live AI quality.
  Offline application E2E uses the real UI/API/database/worker with only external AI faked.
- Never weaken assertions or silently change criteria. Retain failed evidence and explain fixes.
- Record revision/source fingerprint, commands, results and artifact locations. Documentation
  changes can make the current whole-repository evidence fingerprint stale; report that honestly.
- Do not commit artifacts, generated dependencies, credentials or real customer data.
- Routine dependencies, local commits and normal pushes to the working branch are authorized.
  Merges, deployment and paid model use need separate authority; a key alone is not a spending grant.
- Ask only for missing authority or material product/security decisions. Target 30–60-minute
  slices; reassess by 90 minutes and diagnose after three failed repairs. Stop unattended work
  after four hours with saved state and exact resume instructions.
- Stop at the authorized milestone boundary. Only the complete release matrix supports a
  release-completion claim; report verified, failed, skipped and unverified separately.

## Small verified changes and active learning

- Commit and push after each coherent verified slice, including documentation and harness
  improvements. Do not wait until milestone end or manufacture commits for individual keystrokes.
- Review the exact staged diff, exclude secrets/generated artifacts, run affected checks and
  use a descriptive commit message. Push explicitly to the current rebuild branch and confirm
  the remote revision. Never force-push or update main/archive branches under this authority.
- When CI exists, inspect its result after pushing; repair new failures promptly. Missing CI
  stays explicit. A remote checkpoint is not release completion, and a failed push is not success.
- Keep changes reviewable and integrate feedback promptly. Short-lived PRs are useful for
  integration, but push authorization does not grant merge authority or weaken security gates.
- Convert recurring mistakes into focused checks with actionable repair messages; enforce
  dependency directions and important invariants as modules appear, rather than adding prose alone.
- Make app state observable through browser journeys and request/run-correlated logs. Capture
  before/after evidence for defects; improve the missing tool or environment when progress stalls.
- Compare alternative approaches for genuinely uncertain decisions before committing to one;
  do not run multiple implementations by default. Respect the single implementation owner.
- Fold small, related documentation cleanup into each slice; track unrelated debt without
  expanding scope or creating unsolicited recurring tasks. Keep decisions and review dispositions
  in the repository so future work does not depend on remembered chat history.
- Before checkpointing, compare changed behavior/commands with README, architecture, status
  and the affected area guide. Update the owning fact and link it elsewhere; do not duplicate
  milestone snapshots in instruction files. Record implementation/plan differences explicitly.
  Documentation link checks cannot detect semantic drift: review against code and dated evidence.

These practices adapt the articles' short-lived changes, agent feedback loops, environment
improvement and mechanical enforcement. Frequent verified branch pushes are explicitly the
user's chosen policy; the articles do not prescribe a commit count or an every-edit push rule.
