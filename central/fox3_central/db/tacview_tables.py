"""Tacview index tables: one row per indexed recording and per pilot appearance in it."""
from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, Column, Float, Integer, String, Table, UniqueConstraint

from ..core.clock import now
from .tables import BigId, md

tacview_files = Table("tacview_files", md, Column("id", BigId, primary_key=True, autoincrement=True),
    Column("server_id", String(36), nullable=False, index=True), Column("relative_path", String, nullable=False),
    Column("size_bytes", BigInteger), Column("mtime", String), Column("sha256", String), Column("reference_time", String, index=True),
    Column("duration_s", Float), Column("title", String), Column("complete", Boolean, default=True),
    Column("index_version", Integer, nullable=False), Column("indexed_at", String, default=now),
    UniqueConstraint("server_id", "relative_path"))

tacview_appearances = Table("tacview_appearances", md, Column("id", BigId, primary_key=True, autoincrement=True),
    Column("file_id", BigId, nullable=False, index=True), Column("pilot", String, nullable=False, index=True),
    Column("aircraft", String), Column("coalition", String), Column("grp", String), Column("object_id", String),
    Column("first_offset_s", Float, nullable=False), Column("last_offset_s", Float, nullable=False))
