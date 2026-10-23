"""Serves recording download requests: polls central (outbound only) and streams the requested file back."""
from __future__ import annotations

import logging
import threading
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

from ..client import CentralClient
from .files import safe_recording_path

log = logging.getLogger("fox3.agent.transfers")
CHUNK = 1024 * 1024


def read_exactly(path: Path, size: int) -> Iterator[bytes]:
    """Yield the first `size` bytes. A file that shrank yields less: central then aborts the download (no silent truncation)."""
    left = size
    with path.open("rb") as f:
        while left > 0:
            block = f.read(min(CHUNK, left))
            if not block:
                return
            left -= len(block)
            yield block


class TransferResponder:
    def __init__(self, client: CentralClient, folder_provider: Callable[[], Path | None], wait_s: float = 25.0, workers: int = 2):
        self._client, self._folder, self._wait = client, folder_provider, wait_s
        self._busy: set[str] = set()
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="fox3-transfer")
        self._thread = threading.Thread(target=self._loop, name="fox3-transfers", daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._pool.shutdown(wait=False, cancel_futures=True)

    def _loop(self) -> None:
        delay = 2.0
        while not self._stop.is_set():
            try:
                for req in self._client.file_requests(self._wait):
                    self._submit(req)
                delay = 2.0
            except httpx.HTTPError as exc:
                log.warning("file-request poll failed (%s), retrying in %.0fs", type(exc).__name__, delay)
                self._stop.wait(delay)
                delay = min(delay * 2, 60.0)

    def _submit(self, req: dict) -> None:
        with self._lock:
            if req["request_id"] in self._busy:
                return
            self._busy.add(req["request_id"])
        self._pool.submit(self._serve, req)

    def _serve(self, req: dict) -> None:
        rid = req["request_id"]
        try:
            folder = self._folder()
            path = safe_recording_path(folder, req["relative_path"]) if folder else None
            if path is None:
                self._client.fail_request(rid, "file not available on the server")
                return
            self._client.upload_file(rid, read_exactly(path, path.stat().st_size), path.stat().st_size)
        except (OSError, httpx.HTTPError) as exc:
            log.warning("transfer %s failed: %s", rid, type(exc).__name__)  # never log paths
        finally:
            with self._lock:
                self._busy.discard(rid)
