import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app


def test_static_frontend_is_opt_in(monkeypatch):
    monkeypatch.delenv("FRONTEND_DIST_PATH", raising=False)
    get_settings.cache_clear()
    with TestClient(create_app()) as client:
        assert client.get("/").status_code == 404


@pytest.mark.parametrize("missing", ["index", "assets"])
def test_incomplete_build_fails_startup(tmp_path, monkeypatch, missing):
    if missing != "index":
        (tmp_path / "index.html").write_text("index")
    if missing != "assets":
        (tmp_path / "assets").mkdir()
    monkeypatch.setenv("FRONTEND_DIST_PATH", str(tmp_path))
    get_settings.cache_clear()
    with pytest.raises(ValueError, match="FRONTEND_DIST_PATH"):
        create_app()


def test_built_frontend_preserves_api_and_file_boundaries(tmp_path, monkeypatch):
    root = tmp_path / "build"
    root.mkdir()
    (root / "index.html").write_text('<html><script src="/assets/app.js"></script></html>')
    (root / "assets").mkdir()
    (root / "assets" / "app.js").write_text('console.log("built browser");')
    (root / ".env").write_text("private-root-marker")
    (tmp_path / "secret.txt").write_text("private-outside-marker")
    monkeypatch.setenv("FRONTEND_DIST_PATH", str(root))
    get_settings.cache_clear()
    with TestClient(create_app()) as client:
        page = client.get("/")
        assert page.status_code == 200 and "/assets/app.js" in page.text
        assert page.headers["cache-control"] == "no-store"
        script = client.get("/assets/app.js")
        assert script.status_code == 200 and "built browser" in script.text
        cached = client.get("/assets/app.js", headers={"If-None-Match": script.headers["etag"]})
        assert cached.status_code == 304
        for path in ("/.env", "/assets/%2e%2e/.env", "/assets/%2e%2e/%2e%2e/secret.txt",
                     "/api/v1/missing", "/unknown-page", "/assets/missing.js"):
            response = client.get(path)
            assert response.status_code == 404
            assert "private-" not in response.text
            assert "<html>" not in response.text
        assert client.get("/api/v1/auth/me").status_code == 401
