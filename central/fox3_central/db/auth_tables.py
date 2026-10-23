"""Tables for web login, sessions and Discord <-> UCID linking."""
from __future__ import annotations

from sqlalchemy import BigInteger, Column, Integer, String, Table

from ..core.clock import now
from .tables import md

users = Table("users", md, Column("user_id", Integer, primary_key=True, autoincrement=True),
    Column("discord_id", String, unique=True, nullable=False), Column("discord_name", String),
    Column("avatar", String), Column("role", String, default="user"),
    Column("created_at", String, default=now), Column("last_login_at", String))

sessions = Table("sessions", md, Column("session_hash", String, primary_key=True),
    Column("user_id", Integer, nullable=False, index=True), Column("csrf", String, nullable=False),
    Column("expires_at", String, nullable=False))

oauth_states = Table("oauth_states", md, Column("state", String, primary_key=True),
    Column("verifier", String, nullable=False), Column("expires_at", String, nullable=False),
    Column("browser_hash", String))  # sha256 of the nonce kept in a cookie of the browser that started the login

player_links = Table("player_links", md, Column("ucid", String, primary_key=True),
    Column("user_id", Integer, nullable=False, index=True), Column("linked_at", String, default=now))

link_codes = Table("link_codes", md, Column("code", String, primary_key=True),
    Column("user_id", Integer, nullable=False), Column("expires_at", String, nullable=False),
    Column("used_at", String))

# Pairs reported by an authenticated agent from DCSServerBot (claims, not proof): turned into player_links only by services/discord_links.
discord_link_claims = Table("discord_link_claims", md, Column("server_id", String(36), primary_key=True),
    Column("ucid", String, primary_key=True, index=True), Column("discord_id", BigInteger, nullable=False, index=True),
    Column("updated_at", String, default=now))
