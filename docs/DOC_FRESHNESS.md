# Documentation freshness

The [manifest](freshness.json) maps source areas to authoritative documents. The
[generated reference](generated/source-reference.md) derives current paths and command names
from Git inventory and literal source declarations without executing application code.
Historical plans and dated evidence are not rewritten to describe current behavior.

## Change-to-review loop

1. Run `python scripts/docs_freshness.py garden`. It emits a JSON report of each area's
   source paths, owning docs, current fingerprint and previous review receipt, plus errors.
2. An independent reviewer reads affected sources, owning docs and relevant saved evidence.
   Also compare README, STATUS and target scope against current architecture. Record specific
   contradictions and fix them in the owning document; preserve unresolved scope deviations.
   A fresh fingerprint does not establish semantic accuracy or runtime evidence freshness.
3. Run `python scripts/docs_freshness.py generate` after source structure or command changes.
   This never refreshes review receipts. Check the generated diff.
4. Run `garden` again after corrections. The reviewer records the exact reviewed fingerprint:

   ```text
   python scripts/docs_freshness.py acknowledge --area tooling --fingerprint HASH --reviewer REVIEWER --outcome updated --rationale "Reviewed commands against source; corrected owning instructions."
   ```

   Use `--outcome no-doc-impact` only with a concrete explanation of why the changed code
   leaves the owning claims accurate. This is an accountable assertion, not an automated review.
   Never have an implementation agent blindly acknowledge its own work to clear CI.
5. Run `python scripts/docs_freshness.py check` and preparation tests before committing.
   CI runs the same check on Windows and Linux. Any later relevant source/doc change invalidates
   the receipt and requires review again. Whitespace edits can invalidate it; timestamps cannot
   renew it. CRLF/LF and UTF-8 BOM differences are normalized for cross-platform checkouts.

The manifest selects tracked and new repository-nonignored files, including Markdown corpus data and area
guides. New unmapped non-Markdown source areas fail closed. Historical plans and other unmapped
Markdown remain semantic gardening inputs rather than enforced source mappings. Personal Git
global ignore files are excluded so local preferences cannot silently change CI coverage. Source
names/content, owning document names/content and area mappings contribute
to hashes; deletions and renames invalidate them too. Receipts and generated output are excluded
to avoid self-referential hashes. Treat the manifest itself as review-sensitive configuration.

## Periodic gardening

Run `garden` periodically and at checkpoints, including when CI passes. The reviewer should
inspect current-state claims in README, STATUS and architecture, not just flagged areas:
external changes, expired evidence and stale prose can occur without source changes. Save a
dated review summary with findings, dispositions and exact evidence in the execution record.
Make bounded documentation corrections; record product issues without expanding implementation.
The command is read-only and does not call AI, schedule execution or open PRs. A separately
authorized Codex automation can use this same workflow. Missing review authority or evidence
must remain explicit; do not invent receipts, model results or successful checks.

An app-managed Codex heartbeat (`review-repository-documentation-freshness`) is scheduled for
Mondays at 09:00 local time. It permits up to 30 minutes of independent review and bounded
documentation corrections, stays quiet when unchanged, and does not resume product work.
Execution depends on the Codex scheduler and device/runtime availability; this is not GitHub cron.

This adapts OpenAI's [harness engineering](https://openai.com/index/harness-engineering/)
approach: generated references, mechanical checks and recurring semantic documentation review.
The local harness verifies content binding and declared ownership, not reviewer identity,
honesty or every claim's truth. A changed date or a passing link check proves neither freshness
nor production readiness.
