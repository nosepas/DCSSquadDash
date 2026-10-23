from __future__ import annotations

from typing import Any

from sqlalchemy import delete, func, insert, select
from sqlalchemy.engine import Connection

from ..core.clock import now
from ..db import tables as t
from ..db.tacview_tables import tacview_appearances as ap
from ..db.tacview_tables import tacview_files as tf
from ..db.utils import upsert
from .sql_text import ESCAPE, like_contains

Row = dict[str, Any]


def replace_file(cn: Connection, server_id: str, payload: Row) -> int:
    """Store (or re-store) the index of one recording. Re-indexing a changed file replaces its appearances."""
    f = payload["file"]
    upsert(cn, tf, {"server_id": server_id, "relative_path": f["relative_path"]},
           size_bytes=f["size_bytes"], mtime=f["mtime"], sha256=f.get("sha256"), reference_time=f.get("reference_time"),
           duration_s=f.get("duration_s"), title=f.get("title"), complete=f.get("complete", True),
           index_version=payload["index_version"], indexed_at=now())
    file_id = cn.execute(select(tf.c.id).where(tf.c.server_id == server_id, tf.c.relative_path == f["relative_path"])).scalar_one()
    cn.execute(delete(ap).where(ap.c.file_id == file_id))
    rows = [{"file_id": file_id, "pilot": a["pilot"], "aircraft": a.get("aircraft"), "coalition": a.get("coalition"),
             "grp": a.get("group"), "object_id": a.get("object_id"), "first_offset_s": a["first_offset_s"],
             "last_offset_s": a["last_offset_s"]} for a in payload["appearances"]]
    if rows:
        cn.execute(insert(ap), rows)
    return file_id


def search(cn: Connection, pilot: str, limit: int, server_id: str | None = None) -> list[Row]:
    """Appearances whose pilot name contains `pilot` (case-insensitive), newest recordings first."""
    q = (select(ap, tf.c.relative_path, tf.c.reference_time, tf.c.server_id, tf.c.complete,
                t.servers.c.name.label("server_name"))
         .join(tf, tf.c.id == ap.c.file_id).join(t.servers, t.servers.c.server_id == tf.c.server_id)
         .where(func.lower(ap.c.pilot).like(like_contains(pilot), escape=ESCAPE), t.servers.c.enabled.is_(True)))
    if server_id:
        q = q.where(tf.c.server_id == server_id)
    q = q.order_by(tf.c.reference_time.desc(), ap.c.first_offset_s).limit(limit)
    return [dict(r) for r in cn.execute(q).mappings()]


def get_file(cn: Connection, file_id: int) -> Row | None:
    """A recording of an enabled server (disabled servers are invisible to users)."""
    q = (select(tf).join(t.servers, t.servers.c.server_id == tf.c.server_id)
         .where(tf.c.id == file_id, t.servers.c.enabled.is_(True)))
    r = cn.execute(q).mappings().first()
    return dict(r) if r else None


def delete_for_server(cn: Connection, server_id: str) -> None:
    ids = select(tf.c.id).where(tf.c.server_id == server_id)
    cn.execute(delete(ap).where(ap.c.file_id.in_(ids)))
    cn.execute(delete(tf).where(tf.c.server_id == server_id))
