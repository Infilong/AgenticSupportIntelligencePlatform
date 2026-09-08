# Evaluation guidance

Scope: this directory and its descendants. Read the [root director](../AGENTS.md).
The [fixture contract](README.md) owns corpus/case details; do not duplicate them here.

- Keep fixtures synthetic, versioned and traceable to source sections. Do not commit customer data.
- Cover EN/JA/ZH and cross-language evidence, clarification, insufficient/conflicting evidence,
  injection, withdrawn versions and workspace denial as required by the release contract.
- Preserve expected facts and forbidden claims independently of generated answers.
  Application code must never consume expected-answer cases to produce responses.
- Freeze corpus, source equivalence, scoring and thresholds before tuning; never weaken
  assertions or silently change acceptance criteria to make a model pass.
- Distinguish fixture integrity, retrieval correctness and live semantic quality. M0 seeds
  are not the complete release corpus and no live quality evaluation has passed.
- Compare the same cases and compatible settings across the required baselines. Model
  grading supplements source checks and human review; it does not replace them.
- Use [acceptance](../docs/ACCEPTANCE.md) for gates and [runbook](../docs/RUNBOOK.md)
  for available commands. A provider key does not authorize spending.
- Retain failures and report per-language denominators, configuration/corpus fingerprints,
  representative answers and costs with results.
