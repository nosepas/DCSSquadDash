"""Windows DPAPI (CryptProtectData) through ctypes: encrypt a secret so only this Windows account/machine can read it."""
from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes

AVAILABLE = sys.platform == "win32"


class _Blob(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]


def _to_blob(data: bytes) -> tuple[_Blob, ctypes.Array]:
    buf = ctypes.create_string_buffer(data, len(data))
    return _Blob(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char))), buf


def _from_blob(blob: _Blob) -> bytes:
    out = ctypes.string_at(blob.pbData, blob.cbData)
    ctypes.windll.kernel32.LocalFree(blob.pbData)  # type: ignore[attr-defined]
    return out


def protect(data: bytes, machine_scope: bool = False) -> bytes:
    """machine_scope=True lets any account on this PC decrypt (needed when a service runs as another account than the installer)."""
    if not AVAILABLE:
        raise OSError("DPAPI is only available on Windows")
    blob_in, _keep = _to_blob(data)
    blob_out = _Blob()
    flags = 0x4 if machine_scope else 0  # CRYPTPROTECT_LOCAL_MACHINE
    if not ctypes.windll.crypt32.CryptProtectData(ctypes.byref(blob_in), None, None, None, None, flags, ctypes.byref(blob_out)):  # type: ignore[attr-defined]
        raise ctypes.WinError()  # type: ignore[attr-defined]
    return _from_blob(blob_out)


def unprotect(data: bytes) -> bytes:
    if not AVAILABLE:
        raise OSError("DPAPI is only available on Windows")
    blob_in, _keep = _to_blob(data)
    blob_out = _Blob()
    if not ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)):  # type: ignore[attr-defined]
        raise ctypes.WinError()  # type: ignore[attr-defined]
    return _from_blob(blob_out)
