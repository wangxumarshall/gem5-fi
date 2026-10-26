# tests/test_lsu_prop_stream_cap.py
"""R6 prop_evt 流式读取 + EVENT_CAP 语义（合成超大流，峰值内存有界）。"""
import gzip, os, resource, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import tools.lsu_prop_fields as PF


def _write_stream(path, n):
    with gzip.open(path, "wt") as f:
        f.write("# prop-evt v1: header\n")
        for i in range(n):
            f.write(f"PROP-EVT: tick={i} kind=probe fault_id=1 event_id={i} parent_event_id=0\n")


def test_cap_is_200k():
    assert PF.EVENT_CAP == 200000


def test_under_cap_is_not_truncated():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "prop_evt.txt.gz"
        _write_stream(p, 1000)
        ev, truncated = PF.read_events(p)
        assert len(ev) == 1000 and truncated is False


def test_over_cap_is_flagged_not_silently_truncated():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "prop_evt.txt.gz"
        _write_stream(p, PF.EVENT_CAP + 5000)
        ev, truncated = PF.read_events(p)
        assert truncated is True, "over-cap streams must be flagged truncated"
        assert len(ev) <= PF.EVENT_CAP + 1


def test_peak_rss_bounded_on_huge_stream():
    """合成 ~1200 万事件（远超 EVENT_CAP）——峰值 RSS 必须有界。"""
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "prop_evt.txt.gz"
        _write_stream(p, 12_000_000)
        before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        ev, truncated = PF.read_events(p)
        after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        assert truncated is True
        growth_mb = (after - before) / 1024.0
        assert growth_mb < 400, f"peak RSS grew {growth_mb:.0f} MB (>400 MB bound)"


if __name__ == "__main__":
    test_cap_is_200k(); test_under_cap_is_not_truncated()
    test_over_cap_is_flagged_not_silently_truncated(); test_peak_rss_bounded_on_huge_stream()
    print("test_lsu_prop_stream_cap: ALL PASS")
