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


def test_golden_control_bounded_on_huge_stream():
    """lsu_r6_golden_control 的流探测/计数不得整体 read() 解压流。

    覆盖两处旧的 `fh.read()`：`stream_status`（完整性探测）与 `kind_counts`
    （kind 计数）。二者都必须逐行流式，峰值 RSS 有界。
    """
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "prop_evt.txt.gz"
        _write_stream(p, 12_000_000)
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
        import lsu_r6_golden_control as GC

        before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        st = GC.stream_status(p)
        after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        g1 = (after - before) / 1024.0
        assert st["readable"] is True and st["truncated"] is False
        assert g1 < 400, f"stream_status must not load the whole stream ({g1:.0f} MB)"

        before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        counts = GC.kind_counts(p)
        after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        g2 = (after - before) / 1024.0
        assert counts.get("probe") == 12_000_000
        assert g2 < 400, f"kind_counts must not load the whole stream ({g2:.0f} MB)"


if __name__ == "__main__":
    test_cap_is_200k(); test_under_cap_is_not_truncated()
    test_over_cap_is_flagged_not_silently_truncated(); test_peak_rss_bounded_on_huge_stream()
    test_golden_control_bounded_on_huge_stream()
    print("test_lsu_prop_stream_cap: ALL PASS")
