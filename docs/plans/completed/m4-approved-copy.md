# Copy approved responses — 2026-09-09

Outcome UX: make the product's final approved wording reusable without selecting unrelated
drafts or evidence. Root owns the small frontend slice; no API, approval or delivery change.
Read frontend/AGENTS.md. Use a native button, exact stored reviewed_response, explicit clipboard
success/failure feedback and per-result state reset. Only completed approved responses qualify.

Verification: 39 component tests and TypeScript/Vite build pass. Tests cover clipboard denial,
retry, exact multiline Japanese wording, state eligibility and feedback reset. Three real
EN/JA/ZH retrieval→review browser journeys pass in 56.7s at
`.artifacts/m4/approved-copy-20260909`; approved/edited text matches the actual clipboard after
keyboard activation and rejected drafts expose no copy control. Final Japanese journey passes
in 21.4s at `.artifacts/m4/approved-copy-layout-20260909`, checking 360/768/1440 layout.
Independent frontend review found no actionable issue. Clipboard denial uses a deterministic
component fake; browser success uses the actual clipboard. No sending or generation-quality claim.
