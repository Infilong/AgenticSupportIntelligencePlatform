# Multilingual Knowledge Demo Templates

## Goal
Make the browser Knowledge form safer and more useful for multilingual testing by providing realistic English, Japanese, and Chinese source templates instead of a single English-only demo document.

## Context
The platform supports English, Japanese, and Chinese, and the chunk inspector now uses sentence-aware CJK chunking. The frontend Knowledge form still initialized with an English refund policy regardless of selected language. A user could switch the language selector to Chinese or Japanese and accidentally index English content as CJK, making chunks and retrieval quality look wrong during visual testing.

## Implementation
- Added `demoDocumentTemplates` keyed by `en`, `ja`, and `zh`.
- Added matching demo document titles per language.
- Added `changeDocumentLanguage()` so switching language updates title/content only when the current title/content are still untouched built-in demo templates.
- Preserved manual user edits: once the user types custom source content or title, language changes do not overwrite it.
- Kept saved-document editing behavior unchanged.

## Validation
- `cd frontend && npm run build`
- `cd frontend && npm test -- --run`

## Manual Review Checklist
- Open Knowledge, click New, switch Language to Japanese, and confirm the title/content become Japanese.
- Switch to Chinese and confirm the title/content become Chinese.
- Edit the content manually, switch language, and confirm the custom text is not overwritten.
- Upload/index the Chinese template and confirm chunks are complete sentence-like snippets.

## Known Limitations
This only improves browser demo defaults. Backend seed/demo files can still be expanded later with more domain-specific policies, FAQs, and evaluation cases.
