# Milestone 3: Dataset Import And Multilingual Examples

## What Was Built
Milestone 3 adds workspace-scoped datasets, import batches, conversation examples, messages, labels, deterministic language detection, JSONL import, CSV import, and manual label editing.

## Why Companies Care
AI support systems need curated data before they need agents. Employers care about this layer because RAG quality, evaluation quality, and human review all depend on clean examples, reliable labels, and strict tenant boundaries.

## How This Project Uses It
The platform can now import English, Japanese, and Chinese support examples and store message language plus labels. Future milestones will use these examples for retrieval evaluation, prompt testing, routing checks, and quality dashboards.

## Design Tradeoffs
- Language detection is deterministic and cheap instead of LLM-based, which keeps token cost at zero for import.
- Japanese kana is detected as `ja`; CJK text without kana is treated as `zh` in v1, so kanji-only Japanese is a known limitation.
- CSV import uses a strict documented format instead of fuzzy column inference.
- Imports are synchronous in this milestone; async workers are reserved for document ingestion and heavier jobs.

## Failure Modes
- Route handlers may forget to filter by both `workspace_id` and resource ID.
- Ambiguous CJK text can be misclassified.
- Broad CSV support can turn into scope creep.
- Import errors must not dump full customer message content into logs or responses.

## Interview Explanation
I built dataset curation before LLM workflows because production AI systems need reliable source examples, labels, and language metadata. This milestone demonstrates deterministic preprocessing, multilingual handling, and tenant-safe APIs without spending tokens or pretending classification is smarter than it is.
