# Customer message imports

Read backend/AGENTS.md and ../support/AGENTS.md. This module owns JSONL admission, labels
and import provenance; support owns messages and processing attempts. Imported customer text
is never trusted knowledge. Validate the whole bounded batch before writing; authorize before
idempotency lookup and serialize capacity/admission under the workspace lock. Preserve original
text. Labels are operator metadata, never instructions or permission grants. Starting a saved
message must reuse support admission and create one initial job under concurrent requests.
