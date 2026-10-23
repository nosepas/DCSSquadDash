"""Section 4: newest recordings, and a full indexer run on the newest finished one."""
from __future__ import annotations

import os
import time
import zipfile
from collections import Counter
from pathlib import Path

from ..sources.tacview.cloud import folder_missing_message, is_transient_name
from ..sources.tacview.indexer import index_file
from ..sources.tacview.scanner import AcmiFile, FolderMissingError, scan_folder
from .context import Context
from .report import Section
from .tacview_stats import AcmiStats, collect

LIST_NEWEST = 5


def _human(n: float) -> str:
    return f"{n / 1e6:.1f} MB" if n >= 1e6 else f"{n / 1e3:.1f} KB" if n >= 1e3 else f"{n:.0f} B"


def _is_zip(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            return f.read(4) == b"PK\x03\x04"
    except OSError:
        return False


def _listing(files: list[AcmiFile], now: float, sec: Section) -> None:
    sec.line(f"  newest {min(LIST_NEWEST, len(files))} recordings (of {len(files)}):")
    for f in files[:LIST_NEWEST]:
        ext = "".join(Path(f.rel).suffixes[-2:]).lower()
        sec.line(f"    {f.rel}  {_human(f.size)}  age {max(0.0, now - f.mtime_ns / 1e9):.0f} s  ext={ext}  zip={_is_zip(f.path)}"
                 f"  online-only={f.online_only}")


def _other_files(folder: Path, sec: Section) -> None:
    ext: Counter = Counter()
    transient = 0
    for e in os.scandir(folder):
        if e.is_file():
            ext[Path(e.name).suffix.lower() or "(none)"] += 1
            transient += is_transient_name(e.name)
    sec.kv("file extensions in the top folder", dict(ext.most_common(8)))
    if transient:
        sec.kv("temporary sync/download files ignored", transient)
    if ext.get(".zip") or ext.get(".txt"):
        sec.flag("top folder holds .zip/.txt files: only *.acmi recordings are indexed (Tacview writes *.zip.acmi / *.txt.acmi)")


def _stats(st: AcmiStats, sec: Section) -> None:
    sec.kv("objects (distinct ids)", st.objects)
    sec.kv("objects with a Pilot property", st.pilot_objects)
    sec.kv("  AI-looking / other", f"{st.ai_like} / {st.pilot_objects - st.ai_like}  (heuristic, unverified: Pilot equals Group, "
           "or DCS default name like Aerial-1-1)")
    sec.kv("Color among Pilot objects", dict(st.colors.most_common()))
    sec.kv("Coalition among Pilot objects", dict(st.coalitions.most_common()))
    sec.kv("(Color/Coalition) pairs", {f"{c}/{k}": n for (c, k), n in st.color_x_coalition.most_common(10)})
    sec.kv("Type combos of Pilot objects (top 10)", dict(st.pilot_types.most_common(10)))
    sec.kv("Type combos of all objects (top 10)", dict(st.all_types.most_common(10)))
    sec.line("  pilot objects (first 15, names replaced):")
    for label, color, coal, typ, ai in st.rows:
        sec.line(f"    {label}: Color={color} Coalition={coal} Type={typ} ai_like={ai}")
    if st.partial:
        sec.flag("statistics pass stopped early (size cap): counts are partial")


def _index(f: AcmiFile, sec: Section) -> None:
    t0 = time.perf_counter()
    idx = index_file(f.path)
    secs = max(time.perf_counter() - t0, 1e-6)
    sec.line(f"  newest finished recording: {f.rel}")
    sec.kv("indexer throughput", f"{f.size / 1e6 / secs:.1f} MB/s of file on disk ({secs:.2f} s)")
    sec.kv("ReferenceTime / Title / DataSource", f"{idx.reference_time} / {idx.title!r} / {idx.data_source!r}")
    sec.kv("duration_s", idx.duration_s)
    sides = Counter(a.coalition for a in idx.appearances)
    sec.kv("appearances (our parser) / by mapped side", f"{len(idx.appearances)} / {dict(sides)}")
    sec.kv("complete / malformed / oversized / dropped",
           f"{idx.complete} / {idx.malformed_lines} / {idx.oversized_lines} / {idx.dropped_objects}")
    if not idx.complete:
        sec.flag("indexer says the recording is incomplete or truncated")
    if sides.get("unknown"):
        sec.flag(f"{sides['unknown']} appearances have an unknown side: see the Color/Coalition values below")
    if _is_zip(f.path):
        with zipfile.ZipFile(f.path) as zf:
            names = zf.namelist()
        sec.kv("zip members", f"{len(names)}: {', '.join(names[:5])}")
    _stats(collect(f.path), sec)


def tacview(ctx: Context, sec: Section) -> None:
    folder = ctx.tacview_dir
    if folder is None:
        sec.flag("no Tacview folder known (use --tacview-dir, or set it in the admin panel)")
        return
    try:
        files = sorted(scan_folder(folder), key=lambda f: f.mtime_ns, reverse=True)
    except FolderMissingError:
        sec.flag(folder_missing_message(folder))
        return
    _other_files(folder, sec)
    if not files:
        sec.flag("no .acmi recording in the folder")
        return
    now = ctx.now()
    _listing(files, now, sec)
    done = next((f for f in files if now - f.mtime_ns / 1e9 >= ctx.settle_s), None)
    if done is None:
        sec.flag(f"every recording is newer than the settle time ({ctx.settle_s:.0f} s): none indexed")
        return
    if done.online_only:
        sec.line("  note: this recording is online-only; reading it downloads it first (may be slow)")
    _index(done, sec)
