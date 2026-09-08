"""Check repository Markdown without traversing ignored dependencies or archived data."""
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def repository_docs(root=ROOT):
    result = subprocess.check_output(
        ["git", "-c", f"safe.directory={root.as_posix()}", "ls-files", "--cached",
         "--others", "--exclude-standard", "-z"], cwd=root
    )
    return sorted({name for name in result.decode("utf-8").split("\0") if name.endswith(".md")})


def validate(root, names):
    errors = []
    root = root.resolve()
    for name in names:
        path = root / name
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            errors.append(f"{name}: documentation must stay inside the repository; replace external symlinks")
            continue
        if not path.is_file():
            errors.append(f"{name}: missing documentation; restore it or remove its tracked entry")
            continue
        content = path.read_text(encoding="utf-8-sig")
        if path.name == "AGENTS.md" and len(content.splitlines()) >= 200:
            errors.append(f"{name}: keep instructions under 200 lines; move recipes into a linked owning guide")
        # Only inline links are checked. Fenced examples and remote links are not local file contracts.
        content = re.sub(r"```.*?```", "", content, flags=re.DOTALL)
        for target in re.findall(r"\]\((<[^>]+>|[^\s)]+)(?:\s+\"[^\"]*\")?\)", content):
            target = target.strip("<>")
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            linked = (path.parent / unquote(parsed.path)).resolve()
            if not linked.is_relative_to(root) or not linked.exists():
                errors.append(f"{name}: broken/local-outside link {target}; fix the path or restore its target")
    return errors


def main():
    errors = validate(ROOT, repository_docs())
    for error in errors:
        print(error)
    if not errors:
        print("Documentation paths and instruction limits passed.")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
