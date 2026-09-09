# OpenAPI generator dependency repair

Fresh release build reported two high-severity npm entries representing one underlying
[js-yaml advisory](https://github.com/advisories/GHSA-2883-xcg3-v3hh). Independent triage traced
openapi-typescript7.13.0 → Redocly1.34.19 → exactly pinned js-yaml4.3.1. Production-only audit
was already clean; the exposure was development OpenAPI parsing. Root owns the narrow patch.

The parent-scoped npm override selects published js-yaml4.3.2; the lockfile changes only that
package's version, registry URL and integrity. No broad audit-fix or unrelated upgrade.
Clean npm ci and full audit pass with zero findings; audit JSON is retained at
`.artifacts/m6/dependency-audit-fixed-20260909.json`. Backend OpenAPI export and patched generator
produce unchanged API types.39 frontend tests and TypeScript/Vite pass; built JS/CSS filenames
remain identical to the preceding release. No new UI behavior or live-provider claim.
