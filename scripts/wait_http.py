"""Wait for each development endpoint to return HTTP 200 within a shared deadline."""

import argparse
import time
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import urlopen


def wait_ready(urls: list[str], timeout: float = 120, interval: float = 0.5) -> bool:
    if not urls or timeout <= 0 or interval <= 0:
        raise ValueError("Provide endpoints and positive timeout/interval values")
    if any(urlsplit(url).scheme not in {"http", "https"} for url in urls):
        raise ValueError("Readiness endpoints must use HTTP or HTTPS")
    pending = set(urls)
    deadline = time.monotonic() + timeout
    while pending:
        for url in tuple(pending):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                print(f"Readiness deadline exceeded: {len(pending)} endpoint(s) unavailable", flush=True)
                return False
            try:
                with urlopen(url, timeout=min(5, remaining)) as response:
                    if response.status == 200:
                        pending.remove(url)
                        print(f"Ready: {urlsplit(url).netloc}{urlsplit(url).path}", flush=True)
            except (URLError, OSError):
                # Startup can temporarily refuse connections or return an HTTP error.
                pass
        if pending:
            time.sleep(min(interval, max(0, deadline - time.monotonic())))
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("urls", nargs="+")
    parser.add_argument("--timeout", type=float, default=120)
    args = parser.parse_args()
    try:
        return 0 if wait_ready(args.urls, args.timeout) else 1
    except ValueError as error:
        parser.error(str(error))


if __name__ == "__main__":
    raise SystemExit(main())
