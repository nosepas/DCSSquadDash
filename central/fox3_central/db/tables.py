"""Table definitions (SQLAlchemy Core). PostgreSQL target schema: contracts/db/schema.sql."""
from __future__ import annotations

from sqlalchemy import JSON, BigInteger, Boolean, Column, Float, Integer, MetaData, String, Table, UniqueConstraint

from ..core.clock import now

md = MetaData()
BigId = BigInteger().with_variant(Integer, "sqlite")  # 64-bit on PostgreSQL; SQLite needs INTEGER to auto-increment
_id = lambda: Column("server_id", String(36), primary_key=True)  # noqa: E731

servers = Table("servers", md, _id(), Column("name", String, nullable=False),
    Column("mission_type", String, nullable=False, default="generic"), Column("terrain", String),
    Column("address", String), Column("description", String), Column("settings", JSON, default=dict),
    Column("enabled", Boolean, default=True), Column("created_at", String, default=now))

agents = Table("agents", md, Column("agent_id", String(36), primary_key=True),
    Column("server_id", String(36), nullable=False, index=True), Column("name", String),
    Column("key_hash", String), Column("pairing_hash", String, index=True), Column("pairing_expires_at", String),
    Column("revoked_at", String), Column("last_seen_at", String), Column("agent_version", String),
    Column("created_at", String, default=now))

server_status = Table("server_status", md, _id(), Column("info", JSON, default=dict),
    Column("heartbeat", JSON, default=dict), Column("updated_at", String))

messages_seen = Table("agent_messages_seen", md, Column("server_id", String(36), primary_key=True),
    Column("message_id", String(36), primary_key=True), Column("received_at", String, default=now))

foothold_state = Table("foothold_state", md, _id(), Column("snapshot_at", String),
    Column("state", JSON), Column("updated_at", String))

zone_history = Table("zone_history", md, Column("id", BigId, primary_key=True, autoincrement=True),
    Column("server_id", String(36), index=True), Column("zone", String), Column("coalition", String), Column("at", String))

online_players = Table("online_players", md, _id(), Column("ucid", String, primary_key=True),
    Column("name", String), Column("coalition", String), Column("aircraft", String), Column("slot", String),
    Column("in_air", Boolean, default=False), Column("position", JSON), Column("connected_at", String),
    Column("updated_at", String))

players = Table("players", md, Column("ucid", String, primary_key=True), Column("last_name", String),
    Column("first_seen_at", String, default=now), Column("last_seen_at", String))

player_stats = Table("player_stats", md, _id(), Column("ucid", String, primary_key=True),
    Column("points", Float, default=0), Column("stats", JSON, default=dict), Column("updated_at", String))

events = Table("events", md, Column("id", BigId, primary_key=True, autoincrement=True),
    Column("server_id", String(36), nullable=False), Column("event_id", String, nullable=False),
    Column("type", String, nullable=False), Column("time_utc", String, nullable=False),
    Column("actor_ucid", String, index=True), Column("actor_name", String), Column("actor_coalition", String),
    Column("actor_unit", String), Column("target_ucid", String, index=True), Column("target_name", String),
    Column("target_coalition", String), Column("target_unit", String), Column("target_is_player", Boolean),
    Column("weapon", String), Column("zone", String), Column("data", JSON),
    UniqueConstraint("server_id", "event_id"))
