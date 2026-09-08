"""API-bound local sessions: Windows DPAPI or owner-only POSIX files."""

import base64
import ctypes
import json
import os
import tempfile
from pathlib import Path

from app.cli.errors import CliError


def _dpapi(data: bytes, *, decrypt: bool = False) -> bytes:
    from ctypes import wintypes

    class Blob(ctypes.Structure):
        _fields_ = [("size", wintypes.DWORD), ("data", ctypes.POINTER(ctypes.c_ubyte))]

    buffer = (ctypes.c_ubyte * len(data)).from_buffer_copy(data)
    source = Blob(len(data), buffer)
    target = Blob()
    crypt = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    method = crypt.CryptUnprotectData if decrypt else crypt.CryptProtectData
    method.argtypes = [
        ctypes.POINTER(Blob),
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(Blob),
    ]
    method.restype = wintypes.BOOL
    if not method(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(target)):
        raise CliError("Windows could not protect or unlock the CLI session.", 3)
    try:
        return ctypes.string_at(target.data, target.size)
    finally:
        kernel.LocalFree(target.data)


def save_session(path: Path, api_url: str, token: str):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    windows = os.name == "nt"
    encoded = base64.b64encode(_dpapi(token.encode())).decode() if windows else token
    payload = {
        "api_url": api_url,
        "protection": "dpapi" if windows else "owner-only",
        "token": encoded,
    }
    descriptor, temporary = tempfile.mkstemp(prefix="asi-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def load_token(path: Path, api_url: str) -> str:
    if not path.exists():
        raise CliError("Sign in with 'asi auth login', or provide ASI_TOKEN.", 3)
    if os.name != "nt" and path.stat().st_mode & 0o077:
        raise CliError("Session permissions are too broad; restrict the file to its owner.", 3)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload["api_url"] != api_url:
            raise CliError("Session belongs to another API address. Sign in to this address.", 3)
        if payload["protection"] == "dpapi" and os.name == "nt":
            return _dpapi(base64.b64decode(payload["token"]), decrypt=True).decode()
        if payload["protection"] == "owner-only" and os.name != "nt":
            return payload["token"]
    except (ValueError, KeyError, UnicodeError) as error:
        raise CliError("CLI session is invalid. Sign in again.", 3) from error
    raise CliError("This session cannot be opened on this operating system.", 3)
