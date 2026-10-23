-- FOX3 central database (PostgreSQL 15+). Contract DDL; Alembic migrations must produce this schema.
-- Every server-scoped table carries server_id. Players are identified by ucid (global).

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE servers (
    server_id     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name          text NOT NULL,
    mission_type  text NOT NULL DEFAULT 'generic' CHECK (mission_type IN ('foothold','generic')),
    terrain       text,
    tacview_folder text,                         -- path on the DCS PC, set from admin
    tacview_enabled boolean NOT NULL DEFAULT false,
    enabled       boolean NOT NULL DEFAULT true,
    created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE agents (
    agent_id      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    server_id     uuid NOT NULL REFERENCES servers ON DELETE CASCADE,
    name          text,
    key_hash      text,                          -- argon2/sha256 of the API key; NULL until paired
    pairing_hash  text,                          -- hash of one-time pairing code
    pairing_expires_at timestamptz,
    revoked_at    timestamptz,
    last_seen_at  timestamptz,
    agent_version text,
    created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE server_status (                      -- latest server_info + heartbeat, one row per server
    server_id     uuid PRIMARY KEY REFERENCES servers ON DELETE CASCADE,
    info          jsonb NOT NULL DEFAULT '{}',    -- server_info payload
    heartbeat     jsonb NOT NULL DEFAULT '{}',
    updated_at    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE agent_messages_seen (                -- idempotency
    server_id     uuid NOT NULL REFERENCES servers ON DELETE CASCADE,
    message_id    uuid NOT NULL,
    received_at   timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (server_id, message_id)
);

CREATE TABLE users (                              -- web login (Discord)
    user_id       bigserial PRIMARY KEY,
    discord_id    text NOT NULL UNIQUE,
    discord_name  text,
    avatar        text,
    role          text NOT NULL DEFAULT 'user' CHECK (role IN ('user','admin')),
    created_at    timestamptz NOT NULL DEFAULT now(),
    last_login_at timestamptz
);

CREATE TABLE players (                            -- one per DCS identity, shared across servers
    ucid          text PRIMARY KEY,
    last_name     text,
    first_seen_at timestamptz NOT NULL DEFAULT now(),
    last_seen_at  timestamptz
);
CREATE INDEX players_name_trgm ON players USING gin (last_name gin_trgm_ops);

CREATE TABLE player_names (
    ucid          text NOT NULL REFERENCES players ON DELETE CASCADE,
    name          text NOT NULL,
    last_used_at  timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (ucid, name)
);

CREATE TABLE player_links (                       -- Discord user <-> UCID
    ucid          text PRIMARY KEY REFERENCES players ON DELETE CASCADE,
    user_id       bigint NOT NULL REFERENCES users ON DELETE CASCADE,
    linked_at     timestamptz NOT NULL DEFAULT now(),
    UNIQUE (ucid, user_id)
);

CREATE TABLE discord_link_claims (                -- pairs verified by DCSServerBot, reported by an authenticated agent
    server_id     text NOT NULL,
    ucid          text NOT NULL,
    discord_id    bigint NOT NULL,
    updated_at    timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (server_id, ucid)
);
CREATE INDEX ON discord_link_claims (discord_id);
CREATE INDEX ON discord_link_claims (ucid);

CREATE TABLE link_codes (
    code          text PRIMARY KEY,
    user_id       bigint NOT NULL REFERENCES users ON DELETE CASCADE,
    expires_at    timestamptz NOT NULL,
    used_at       timestamptz
);

CREATE TABLE online_players (                     -- current snapshot
    server_id     uuid NOT NULL REFERENCES servers ON DELETE CASCADE,
    ucid          text NOT NULL,
    name          text NOT NULL,
    coalition     text,
    aircraft      text,
    slot          text,
    in_air        boolean NOT NULL DEFAULT false,
    position      jsonb,
    connected_at  timestamptz,
    updated_at    timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (server_id, ucid)
);

CREATE TABLE foothold_state (                     -- current normalised snapshot
    server_id     uuid PRIMARY KEY REFERENCES servers ON DELETE CASCADE,
    snapshot_at   timestamptz NOT NULL,
    state         jsonb NOT NULL,                 -- validated foothold_state payload
    updated_at    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE zone_history (                       -- territory over time (one row per change)
    id            bigserial PRIMARY KEY,
    server_id     uuid NOT NULL REFERENCES servers ON DELETE CASCADE,
    zone          text NOT NULL,
    coalition     text NOT NULL,
    at            timestamptz NOT NULL
);
CREATE INDEX zone_history_idx ON zone_history (server_id, zone, at);

CREATE TABLE rounds (
    id            bigserial PRIMARY KEY,
    server_id     uuid NOT NULL REFERENCES servers ON DELETE CASCADE,
    external_id   text,
    mission_name  text,
    started_at    timestamptz NOT NULL,
    ended_at      timestamptz,
    winner        text,
    UNIQUE (server_id, started_at)
);

CREATE TABLE events (
    id            bigserial PRIMARY KEY,
    server_id     uuid NOT NULL REFERENCES servers ON DELETE CASCADE,
    event_id      text NOT NULL,
    type          text NOT NULL,
    time_utc      timestamptz NOT NULL,
    mission_time_s double precision,
    round_id      bigint REFERENCES rounds,
    actor_ucid    text,
    actor_name    text,
    actor_coalition text,
    actor_unit    text,
    target_ucid   text,
    target_name   text,
    target_coalition text,
    target_unit   text,
    target_is_player boolean,
    weapon        text,
    zone          text,
    data          jsonb,
    UNIQUE (server_id, event_id)
);
CREATE INDEX events_time_idx ON events (server_id, time_utc DESC);
CREATE INDEX events_actor_idx ON events (actor_ucid, type);

CREATE TABLE player_stats (                       -- per (ucid, server): separate stats per server
    server_id     uuid NOT NULL REFERENCES servers ON DELETE CASCADE,
    ucid          text NOT NULL REFERENCES players ON DELETE CASCADE,
    points        double precision NOT NULL DEFAULT 0,
    stats         jsonb NOT NULL DEFAULT '{}',
    updated_at    timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (server_id, ucid)
);

CREATE TABLE tacview_files (
    id            bigserial PRIMARY KEY,
    server_id     uuid NOT NULL REFERENCES servers ON DELETE CASCADE,
    relative_path text NOT NULL,
    size_bytes    bigint NOT NULL,
    mtime         timestamptz NOT NULL,
    sha256        text,
    reference_time timestamptz,
    duration_s    double precision,
    title         text,
    complete      boolean NOT NULL DEFAULT true,
    index_version integer NOT NULL,
    indexed_at    timestamptz NOT NULL DEFAULT now(),
    UNIQUE (server_id, relative_path)
);

CREATE TABLE tacview_appearances (
    id            bigserial PRIMARY KEY,
    file_id       bigint NOT NULL REFERENCES tacview_files ON DELETE CASCADE,
    pilot         text NOT NULL,
    aircraft      text,
    coalition     text,
    grp           text,
    object_id     text,
    first_offset_s double precision NOT NULL,
    last_offset_s double precision NOT NULL
);
CREATE INDEX tacview_pilot_trgm ON tacview_appearances USING gin (pilot gin_trgm_ops);

CREATE TABLE audit_log (
    id            bigserial PRIMARY KEY,
    at            timestamptz NOT NULL DEFAULT now(),
    actor_user_id bigint REFERENCES users,
    action        text NOT NULL,                  -- e.g. agent.revoke, role.change, server.update
    target        text,
    detail        jsonb
);

CREATE TABLE sessions (
    session_id_hash text PRIMARY KEY,
    user_id       bigint NOT NULL REFERENCES users ON DELETE CASCADE,
    created_at    timestamptz NOT NULL DEFAULT now(),
    expires_at    timestamptz NOT NULL
);
