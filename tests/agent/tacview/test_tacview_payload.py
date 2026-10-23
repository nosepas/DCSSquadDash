from pathlib import Path

from tacview_samples import BASIC, write_plain

from fox3_agent.sources.tacview import index_file
from fox3_agent.sources.tacview.model import Appearance, TacviewIndex
from fox3_agent.sources.tacview.payload import INDEX_VERSION, build_payload, file_sha256
from fox3_central.core.validation import Validators

SCHEMAS = Path(__file__).resolve().parents[3] / "contracts" / "schemas"


def test_payload_validates_against_contract(tmp_path):
    p = write_plain(tmp_path / "a.acmi", BASIC)
    st = p.stat()
    built = build_payload(index_file(p), "sub\\a.acmi", st.st_size, st.st_mtime_ns, sha256=file_sha256(p))
    assert Validators(SCHEMAS).errors("tacview_index", built.payload) == []
    f = built.payload["file"]
    assert built.payload["index_version"] == INDEX_VERSION == 1
    assert f["relative_path"] == "sub/a.acmi" and f["mtime"].endswith("Z") and f["complete"] is True
    assert len(f["sha256"]) == 64
    assert str(tmp_path) not in str(built.payload)


def test_minimal_index_validates():
    built = build_payload(TacviewIndex(complete=False), "x.acmi", 0, 0)
    assert Validators(SCHEMAS).errors("tacview_index", built.payload) == []
    assert built.payload["file"]["sha256"] is None and built.payload["file"]["duration_s"] is None


def test_relative_path_never_absolute():
    built = build_payload(TacviewIndex(), "/abs/x.acmi", 1, 0)
    assert built.payload["file"]["relative_path"] == "abs/x.acmi"


def test_cap_applies_and_flags():
    idx = TacviewIndex(appearances=[Appearance(f"p{i}", f"{i:x}", None, "unknown", None, float(i), float(i)) for i in range(50)])
    built = build_payload(idx, "x.acmi", 1, 0, max_appearances=10)
    assert built.capped and len(built.payload["appearances"]) == 10
    assert Validators(SCHEMAS).errors("tacview_index", built.payload) == []
    assert not build_payload(idx, "x.acmi", 1, 0).capped
