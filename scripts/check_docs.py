"""Check the maintained instruction map and execution plans, not legacy ticket prose."""

from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

CONTROL_DOCS = (
    "AGENTS.md", "ARCHITECTURE.md", "docs/README.md", "docs/CORE_BELIEFS.md",
    "docs/PLANS.md", "docs/QUALITY_SCORE.md", "docs/RELIABILITY.md",
    "docs/exec-plans/README.md", "docs/architecture.md", "docs/codex-workflow.md",
    "docs/production-improvement-loop.md", "docs/code-map.md",
    "backend/README.md", "backend/app/api/README.md", "backend/app/services/README.md",
    "backend/alembic/README.md", "frontend/README.md", "infra/README.md", "scripts/README.md",
)
PLAN_SECTIONS = (
    "Goal", "Context", "Requirements", "Non-goals", "Acceptance Criteria", "Plan",
    "Verification", "Risks", "Progress", "Decisions", "Findings", "Final Result",
)


def check_file(path: Path, *, plan: bool = False) -> list[str]:
    if not path.is_file():
        return [f"{path}: missing document"]
    content = path.read_text(encoding="utf-8")
    errors = []
    if path.name == "AGENTS.md" and len(content.splitlines()) >= 200:
        errors.append(f"{path}: keep instructions under 200 lines")
    prose = re.sub(r"```.*?```", "", content, flags=re.DOTALL)
    if plan:
        headings = set(re.findall(r"^## (.+)$", prose, flags=re.MULTILINE))
        errors.extend(f"{path}: missing plan section {section}"
                      for section in PLAN_SECTIONS if section not in headings)
    for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", prose):
        target = target.strip().strip("<>")
        parsed = urlsplit(target)
        if parsed.scheme or parsed.netloc or not parsed.path:
            continue
        destination = path.parent / unquote(parsed.path)
        if not destination.exists():
            errors.append(f"{path}: broken local link {target}")
    return errors


def check_repository(root: Path) -> list[str]:
    errors = []
    for name in CONTROL_DOCS:
        errors.extend(check_file(root / name))
    for state in ("active", "completed"):
        directory = root / "docs" / "exec-plans" / state
        if not directory.is_dir():
            errors.append(f"{directory}: missing plan directory")
        for plan in directory.glob("*.md"):
            errors.extend(check_file(plan, plan=True))
    return errors


if __name__ == "__main__":
    issues = check_repository(Path(__file__).resolve().parents[1])
    if issues:
        print("\n".join(issues))
        sys.exit(1)
    print("Documentation map, plan sections and instruction size passed.")
