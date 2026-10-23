"""TemplateCache: TTL, ownership, entry caps and the byte budget (fake clock)."""
import pytest

from fox3_central.core.errors import BadRequest, NotFound
from fox3_central.services.dtc_templates import TemplateCache


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def _cache(**kw) -> tuple[TemplateCache, Clock]:
    clock = Clock()
    return TemplateCache(clock=clock, **kw), clock


def test_owner_isolation_and_expiry():
    c, clock = _cache(ttl_s=10)
    tid = c.put(1, {"a": 1}, 5)
    assert c.get(1, tid) == {"a": 1}
    with pytest.raises(NotFound):
        c.get(2, tid)
    clock.now = 11
    with pytest.raises(NotFound):
        c.get(1, tid)


def test_budget_evicts_oldest_of_same_owner_first():
    c, _ = _cache(max_bytes=100, max_per_user=10)
    other = c.put(2, {}, 40)
    a = c.put(1, {}, 30)
    b = c.put(1, {}, 30)  # 100 used
    new = c.put(1, {}, 30)  # must free 30: owner 1's oldest goes, owner 2 stays
    with pytest.raises(NotFound):
        c.get(1, a)
    assert c.get(2, other) == {} and c.get(1, b) == {} and c.get(1, new) == {}


def test_budget_falls_back_to_other_owners():
    c, _ = _cache(max_bytes=100)
    old = c.put(2, {}, 90)
    mine = c.put(1, {}, 90)
    with pytest.raises(NotFound):
        c.get(2, old)
    assert c.get(1, mine) == {}


def test_single_entry_over_budget_is_rejected_and_nothing_evicted():
    c, _ = _cache(max_bytes=100)
    keep = c.put(1, {}, 50)
    with pytest.raises(BadRequest):
        c.put(1, {}, 101)
    assert c.get(1, keep) == {}


def test_expired_entries_free_budget_and_counts_still_apply():
    c, clock = _cache(ttl_s=10, max_bytes=100, max_entries=2, max_per_user=5)
    c.put(1, {}, 100)
    clock.now = 11
    assert c.get(1, c.put(1, {}, 100)) == {}
    first = c.put(3, {}, 1)
    c.put(3, {}, 1)
    c.put(3, {}, 1)  # max_entries=2 evicts the oldest
    with pytest.raises(NotFound):
        c.get(3, first)
