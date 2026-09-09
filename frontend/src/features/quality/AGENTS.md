# Quality and usage views

Read frontend/AGENTS.md. Display server-owned metrics and uncertainty; never infer answer quality
from call success. Keep periods and model groups bounded, and avoid exposing raw inputs. Preserve
loading, empty, failed and permission-denied states. Verify responsive tables and workspace changes
in the actual browser. Evaluation results are a separate capability, not implied by usage charts.
