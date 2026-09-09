# Quality and usage views

Read frontend/AGENTS.md. Display server-owned metrics and uncertainty; never infer answer quality
from call success. Keep periods and model groups bounded, and avoid exposing raw model inputs. Preserve
loading, empty, failed and permission-denied states. Verify responsive tables and workspace changes
in the actual browser. Historical retrieval comparisons are separate from usage charts and answer
quality. Render only the backend projection; case questions belong to the authorized workspace.
Preserve failed and excluded cases, language denominators, lazy trace access and provenance limits.
Never equate registration time with measurement time or historical scores with current quality.
