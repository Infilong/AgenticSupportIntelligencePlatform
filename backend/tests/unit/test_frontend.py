import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.settings import Settings
from app.main import create_app


@pytest.fixture
def build(tmp_path):
    root = tmp_path / "web"
    (root / "assets").mkdir(parents=True)
    (root / "index.html").write_text('<html><div id="root">App shell</div></html>')
    (root / "assets" / "index-12345678.js").write_text("export const ready = true;")
    (root / "assets" / "index-12345678.css").write_text("body { color: black; }")
    (root / "assets" / ".env").write_text("do-not-serve")
    return root


def settings(path):
    return Settings(database_url="postgresql+psycopg://none:none@127.0.0.1:1/unavailable", frontend_dist=path)


def test_built_shell_and_assets_keep_api_errors_and_private_paths_separate(build):
    with TestClient(create_app(settings(build))) as client:
        for path in ["/", f"/w/{uuid.uuid4()}", f"/w/{uuid.uuid4()}/runs/{uuid.uuid4()}"]:
            response = client.get(path)
            assert response.status_code == 200 and "App shell" in response.text
            assert response.headers["cache-control"] == "no-store"
            assert client.head(path).status_code == 200
            assert client.head(path).content == b""
            assert client.post(path).status_code == 405
        for suffix, content_type in [("js", "javascript"), ("css", "text/css")]:
            response = client.get(f"/assets/index-12345678.{suffix}")
            assert response.status_code == 200
            assert content_type in response.headers["content-type"]
            assert "immutable" in response.headers["cache-control"]
        for path in [
            "/api/missing",
            "/assets/missing.js",
            "/.env",
            "/app/main.py",
            "/index.html",
            "/assets/.env",
            "/assets/%2e%2e/index.html",
            "/assets/%2e%2e%2findex.html",
            "/w/not-a-workspace",
            f"/w/{uuid.uuid4()}/private",
        ]:
            response = client.get(path)
            assert response.status_code == 404, path
            assert "App shell" not in response.text and "do-not-serve" not in response.text
        assert client.get("/api/health/live").json() == {"status": "alive"}


def test_explicit_missing_build_fails_instead_of_serving_a_broken_release(tmp_path):
    with pytest.raises(FileNotFoundError):
        create_app(settings(tmp_path / "missing"))


@pytest.mark.parametrize("missing", ["index.html", "assets"])
def test_incomplete_build_fails(tmp_path, missing):
    if missing != "index.html":
        (tmp_path / "index.html").write_text("incomplete")
    if missing != "assets":
        (tmp_path / "assets").mkdir()
    with pytest.raises(FileNotFoundError):
        create_app(settings(tmp_path))


def test_frontend_disabled_keeps_backend_only_behavior():
    with TestClient(create_app(settings(None))) as client:
        assert client.get("/").status_code == 404


def test_assets_do_not_follow_symlinks_outside_public_directory(build, tmp_path):
    secret = tmp_path / "private.txt"
    secret.write_text("outside-public-assets")
    try:
        (build / "assets" / "leak.js").symlink_to(secret)
    except OSError:
        pytest.skip("Host does not permit symlink creation; covered on Linux")
    with TestClient(create_app(settings(build))) as client:
        response = client.get("/assets/leak.js")
        assert response.status_code == 404
        assert "outside-public-assets" not in response.text
