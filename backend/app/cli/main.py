"""CLI entry point with versioned JSON results and explicit failure exit codes."""

import getpass
import json
import os
import sys

from app.cli.commands import execute
from app.cli.errors import CliError
from app.cli.http import Client, api_address
from app.cli.parser import normalize_options, parser
from app.cli.session import load_token, save_session


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    arguments = list(sys.argv[1:] if argv is None else argv)
    compact = "--json" in arguments

    def emit(data):
        print(
            json.dumps(
                {"schema_version": 1, "ok": True, "data": data},
                ensure_ascii=False,
                indent=None if compact else 2,
            ),
            flush=True,
        )

    try:
        args = parser().parse_args(normalize_options(arguments))
        api_url = api_address(args.api_url)
        if args.group == "auth":
            if not args.email:
                if not sys.stdin.isatty():
                    raise CliError("Use --email for non-interactive login.")
                args.email = input("Email: ").strip()
            if args.password_stdin and hasattr(sys.stdin, "reconfigure"):
                sys.stdin.reconfigure(encoding="utf-8")
            if not args.password_stdin and not sys.stdin.isatty():
                raise CliError("Use --password-stdin for non-interactive login.")
            password = (
                sys.stdin.readline().rstrip("\r\n")
                if args.password_stdin
                else (getpass.getpass("Password: "))
            )
            if not password:
                raise CliError("Password must not be empty.")
            response = Client(api_url).call(
                "/auth/login", method="POST", body={"email": args.email, "password": password}
            )
            if not isinstance(response, dict) or not isinstance(response.get("access_token"), str):
                raise CliError("API returned an invalid login response.", 7)
            save_session(args.session_file, api_url, response["access_token"])
            emit({"authenticated": True, "api_url": api_url, "email": args.email})
        else:
            token = os.environ.get("ASI_TOKEN") or load_token(args.session_file, api_url)
            result = execute(args, Client(api_url, token), emit)
            if result is not None:
                emit(result)
        return 0
    except CliError as error:
        code, message, details = error.exit_code, str(error), error.details
    except (OSError, UnicodeError):
        code, message, details = 2, "Unable to read/write a required UTF-8 file or session.", None
    except KeyboardInterrupt:
        code, message, details = (
            130,
            "Interrupted; server work was not automatically stopped.",
            None,
        )
    print(
        json.dumps(
            {
                "schema_version": 1,
                "ok": False,
                "error": {"message": message, "exit_code": code, "details": details},
            },
            ensure_ascii=False,
        ),
        file=sys.stderr,
    )
    return code
