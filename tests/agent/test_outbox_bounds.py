"""Bounded outbox: cap enforcement, drop priorities, snapshot coalescing, drop warning, config validation."""
from __future__ import annotations

import logging

import pytest

from fox3_agent.config import ConfigError, from_mapping
from fox3_agent.outbox import COALESCE_BACKLOG, Outbox


def paths(box):
    return [p for _, p, _ in box.peek(10_000)]


def test_no_loss_under_cap(tmp_path):
    box = Outbox(tmp_path / "q.sqlite", max_messages=100)
    for n in range(10):
        box.put("/events", {"n": n})
    assert len(box) == 10 and box.dropped == 0


def test_row_cap_enforced(tmp_path):
    box = Outbox(tmp_path / "q.sqlite", max_messages=10)
    for n in range(50):
        box.put("/events", {"n": n})
    assert len(box) == 10 and box.dropped == 40
    assert [b["n"] for _, _, b in box.peek(100)] == list(range(40, 50))  # newest kept


def test_byte_cap_enforced(tmp_path):
    box = Outbox(tmp_path / "q.sqlite", max_bytes=2_000)
    for n in range(30):
        box.put("/events", {"blob": "x" * 200, "n": n})
    assert 0 < len(box) < 30 and box.dropped == 30 - len(box)
    assert box.peek(100)[-1][2]["n"] == 29


def test_low_value_dropped_before_events(tmp_path):
    box = Outbox(tmp_path / "q.sqlite", max_messages=6)
    box.put("/events", {"n": 0})
    box.put("/discord-links", {"n": 1})
    box.put("/tacview-index", {"n": 2})
    box.put("/players", {"n": 3})
    box.put("/foothold-state", {"n": 4})
    box.put("/server-info", {"n": 5})
    box.put("/events", {"n": 6})
    box.put("/events", {"n": 7})
    assert "/players" not in paths(box) and "/foothold-state" not in paths(box)
    assert paths(box).count("/events") == 3 and "/discord-links" in paths(box) and "/tacview-index" in paths(box)


def test_events_dropped_oldest_when_only_events_remain(tmp_path):
    box = Outbox(tmp_path / "q.sqlite", max_messages=3)
    for n in range(5):
        box.put("/events", {"n": n})
    assert [b["n"] for _, _, b in box.peek()] == [2, 3, 4]


def test_snapshots_coalesce_when_backlogged(tmp_path):
    box = Outbox(tmp_path / "q.sqlite")
    for n in range(COALESCE_BACKLOG):
        box.put("/events", {"n": n})
    for n in range(5):
        box.put("/players", {"n": n})
    assert paths(box).count("/players") == 1 and box.dropped == 0
    assert [b["n"] for _, p, b in box.peek(100) if p == "/players"] == [4]


def test_snapshots_kept_when_not_backlogged(tmp_path):
    box = Outbox(tmp_path / "q.sqlite")
    for n in range(3):
        box.put("/players", {"n": n})
    assert len(box) == 3


def test_drop_warning_once_per_episode(tmp_path, caplog):
    box = Outbox(tmp_path / "q.sqlite", max_messages=3)
    with caplog.at_level(logging.WARNING, logger="fox3.agent.outbox"):
        for n in range(10):
            box.put("/events", {"n": n})
        assert len([r for r in caplog.records if "outbox is full" in r.message]) == 1
        for msg_id, _, _ in box.peek(100):
            box.delete(msg_id)  # drained: the episode ends
        box.put("/events", {"n": 0})
        for n in range(5):
            box.put("/events", {"n": n})
    assert len([r for r in caplog.records if "outbox is full" in r.message]) == 2


@pytest.mark.parametrize("bad", [{"max_messages": 5}, {"max_mb": 0}, {"max_mb": "9"}, {"max_messages": True}, {"x": 1}])
def test_queue_config_rejects_bad_values(bad):
    with pytest.raises(ConfigError):
        from_mapping({"central": {"url": "https://c.example"}, "queue": bad})


def test_queue_config_values():
    cfg = from_mapping({"central": {"url": "https://c.example"}, "queue": {"max_messages": 1000, "max_mb": 5}})
    assert (cfg.queue.max_messages, cfg.queue.max_bytes) == (1000, 5 * 1024 * 1024)
    assert from_mapping({"central": {"url": "https://c.example"}}).queue.max_messages == 50_000
