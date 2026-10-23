import pytest


@pytest.fixture(autouse=True)
def no_size_recheck_pause(monkeypatch):
    """Unit tests drive the scans themselves; the real 3 s pause between two size observations is tested explicitly."""
    monkeypatch.setattr("fox3_agent.sources.tacview.source.RECHECK_S", 0.0)
