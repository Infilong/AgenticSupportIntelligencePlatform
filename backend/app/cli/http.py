"""Bounded JSON transport; redirects never forward credentials."""

import ipaddress
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from app.cli.errors import CliError


def api_address(value: str) -> str:
    parsed = urlsplit(value)
    local = parsed.hostname == "localhost"
    try:
        local = local or ipaddress.ip_address(parsed.hostname or "").is_loopback
    except ValueError:
        pass
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
        or (parsed.scheme == "http" and not local)
    ):
        raise CliError("API address must be an HTTPS origin, or HTTP on loopback.")
    return value.rstrip("/")


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Client:
    def __init__(self, api_url: str, token: str | None = None):
        self.api_url, self.token = api_address(api_url), token
        self.opener = build_opener(NoRedirect())

    def call(self, path: str, *, method="GET", body=None, timeout=30):
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        data = json.dumps(body, ensure_ascii=False).encode() if body is not None else None
        request = Request(
            self.api_url + "/api/v1" + path, data=data, headers=headers, method=method
        )
        try:
            with self.opener.open(request, timeout=timeout) as response:
                raw = response.read(16 * 1024 * 1024 + 1)
            if len(raw) > 16 * 1024 * 1024:
                raise CliError("Response exceeded the CLI size limit. Narrow the request.", 7)
            return json.loads(raw)
        except HTTPError as error:
            code = {401: 3, 403: 4, 404: 5, 409: 6}.get(error.code, 2 if error.code < 500 else 7)
            message = f"API returned HTTP {error.code}."
            try:
                detail = json.loads(error.read(65536)).get("detail")
                if isinstance(detail, dict):
                    message = detail.get("message", message)
                elif isinstance(detail, str):
                    message = detail
            except (ValueError, UnicodeError):
                pass
            raise CliError(message, code) from error
        except (URLError, TimeoutError, OSError) as error:
            raise CliError("API connection failed or timed out.", 7) from error
        except (ValueError, UnicodeError) as error:
            raise CliError("API returned invalid JSON.", 7) from error
