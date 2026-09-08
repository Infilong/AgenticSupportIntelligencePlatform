"""Verify the running API and worker execute the backend files being evaluated."""

import hashlib
import json
import subprocess
from pathlib import Path


def files(root):
    paths = [
        *root.glob("app/**/*.py"),
        *root.glob("migrations/**/*.py"),
        root / "pyproject.toml",
        root / "uv.lock",
    ]
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(paths)
    }


def verify_runtime():
    root = Path(__file__).resolve().parents[1] / "backend"
    expected = files(root)
    code = (
        "import pathlib,hashlib,json; r=pathlib.Path('/app'); "
        "p=[*r.glob('app/**/*.py'),*r.glob('migrations/**/*.py'),r/'pyproject.toml',r/'uv.lock']; "
        "print(json.dumps({x.relative_to(r).as_posix():hashlib.sha256(x.read_bytes()).hexdigest() for x in sorted(p)}))"
    )
    result = {}
    for service in ("api", "worker"):
        container = f"asi-rebuild-v1-{service}-1"
        actual = json.loads(
            subprocess.check_output(
                ["docker", "exec", container, "/app/.venv/bin/python", "-c", code],
                timeout=30,
                text=True,
            )
        )
        if actual != expected:
            raise ValueError(
                f"Running {service} source differs from the current backend; rebuild before evaluation"
            )
        image_id = subprocess.check_output(
            ["docker", "inspect", "--format", "{{.Image}}", container],
            timeout=30,
            text=True,
        ).strip()
        result[service] = {
            "container": container,
            "image_id": image_id,
            "files": actual,
        }
    return result
