"""Probe the isolated API's access-log privacy without using customer data."""

import argparse
import json
import subprocess
from urllib.error import HTTPError
from urllib.request import urlopen
from uuid import uuid4


def inspect_logs(logs: str, request_id: str, marker: str) -> None:
    if marker in logs:
        raise ValueError("Raw synthetic path/query marker appeared in server logs.")
    matches = []
    for line in logs.splitlines():
        start = line.find("{")
        if start < 0:
            continue
        try:
            record = json.loads(line[start:])
        except json.JSONDecodeError:
            continue
        if record.get("event") == "http_request" and record.get("request_id") == request_id:
            matches.append(record)
    if len(matches) != 1:
        raise ValueError("Expected exactly one correlated HTTP outcome.")
    record = matches[0]
    if record.get("status") != 404 or record.get("route") != "<unmatched>":
        raise ValueError("Synthetic request did not retain its safe route/status outcome.")
    if record.get("error_type") is not None:
        raise ValueError("Synthetic request had an unexpected server error.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", default="asi-verification")
    args = parser.parse_args()
    marker = "synthetic-private-" + uuid4().hex
    try:
        response = urlopen(f"http://127.0.0.1:8000/{marker}?token={marker}", timeout=10)
    except HTTPError as error:
        response = error
    with response:
        if response.status != 404:
            raise ValueError("Synthetic unmatched route did not return 404.")
        request_id = response.headers.get("X-Request-ID")
        if not request_id:
            raise ValueError("HTTP outcome is missing its diagnostic reference.")
        response.read()
    logs = subprocess.run(
        ["docker", "compose", "-p", args.project, "logs", "--no-color", "--since", "30s", "api"],
        check=True, capture_output=True, text=True, encoding="utf-8", timeout=20,
    )
    inspect_logs(logs.stdout, request_id, marker)
    print("HTTP privacy passed: safe correlated 404 outcome; raw path/query marker absent.")


if __name__ == "__main__":
    main()
