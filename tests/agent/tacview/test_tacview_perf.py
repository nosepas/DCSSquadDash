"""Throughput check on a synthetic ~100 MB ACMI. Deselect with `-m "not slow"` (or set FOX3_SKIP_SLOW=1)."""
import os
import random
import time
import zipfile

import pytest

from fox3_agent.sources.tacview import index_file

pytestmark = [pytest.mark.slow, pytest.mark.skipif(bool(os.environ.get("FOX3_SKIP_SLOW")), reason="FOX3_SKIP_SLOW")]

TARGET_MB = 100
MIN_MB_S = 8.0


def generate(path, target_bytes: int) -> int:
    rnd = random.Random(1)
    n_obj, pilots = 3000, 40
    with open(path, "wb", buffering=1 << 20) as f:
        f.write(b"\xef\xbb\xbfFileType=text/acmi/tacview\nFileVersion=2.2\n0,ReferenceTime=2024-05-01T18:00:00Z,Title=Perf\n")
        for i in range(n_obj):
            extra = f",Pilot=Pilot {i},Color=Blue,Group=G{i}" if i < pilots else ""
            f.write(f"{i + 0x3000000:x},T=10.1|20.2|3000,Type=Air+FixedWing,Name=F-16C-52{extra}\n".encode())
        t, size = 0.0, f.tell()
        while size < target_bytes:
            t += 0.5
            f.write(f"#{t}\n".encode())
            for i in rnd.sample(range(n_obj), 400):
                f.write(f"{i + 0x3000000:x},T=10.123456|20.654321|{rnd.randint(0, 9000)}|1.5|2.5|{rnd.randint(0, 359)},AGL=12.5\n".encode())
            size = f.tell()
    return size


def report(label: str, size: int, secs: float) -> float:
    mbs = size / 1e6 / secs
    print(f"\n[tacview perf] {label}: {size / 1e6:.0f} MB in {secs:.1f}s = {mbs:.1f} MB/s")
    return mbs


def test_throughput_plain_and_zip(tmp_path):
    p = tmp_path / "big.acmi"
    size = generate(p, TARGET_MB * 1_000_000)
    t0 = time.perf_counter()
    idx = index_file(p)
    assert report("plain", size, time.perf_counter() - t0) >= MIN_MB_S
    assert len(idx.appearances) == 40 and idx.complete

    z = tmp_path / "big.zip.acmi"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED, compresslevel=1) as zf:
        zf.write(p, "big.txt.acmi")
    p.unlink()
    t0 = time.perf_counter()
    idx2 = index_file(z)
    assert report("zip", size, time.perf_counter() - t0) >= MIN_MB_S
    assert idx2.appearances == idx.appearances
