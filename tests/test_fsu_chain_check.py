"""tests/test_fsu_chain_check.py — FSU 传播链审计器（合成事件流，不运行 gem5）。"""
import gzip
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import fsu_chain_check as C
import fsu_prop_fields as P


def evt(**kw):
    d = {k: "" for k in P.PROP_EVT_FIELDS}
    d.update(kw)
    return P.PREFIX + " " + " ".join(f"{k}={d[k]}" for k in P.PROP_EVT_FIELDS)


def base(run="FSU-FP04-F0-W4", seed="s1", fid="1"):
    return dict(run_id=run, sample_run_id=seed, fault_id=fid, model_id="FP04")


def chain_full(t0=100):
    b = base()
    return [
        evt(kind="fault_applied", event_id="0", tick=str(t0), activated="1", **b),
        evt(kind="carrier_state", event_id="1", parent_event_id="0", tick=str(t0 + 1), **b),
        evt(kind="operand_read", event_id="2", parent_event_id="1", tick=str(t0 + 2), **b),
        evt(kind="execute", event_id="3", parent_event_id="2", tick=str(t0 + 3), **b),
        evt(kind="prf_writeback", event_id="4", parent_event_id="3", tick=str(t0 + 4), **b),
        evt(kind="commit", event_id="5", parent_event_id="4", tick=str(t0 + 5),
            detection_layer="L5", outcome="errant_commit",
            oracle_diff="hash_diff", **b),
    ]


def write(tmp_path, lines, name="ev.txt", gz=False):
    p = tmp_path / name
    text = "\n".join(lines) + "\n"
    if gz:
        p.write_bytes(gzip.compress(text.encode()))
    else:
        p.write_text(text, encoding="utf-8")
    return p


def check(tmp_path, lines, **kw):
    p = write(tmp_path, lines, **{k: v for k, v in kw.items() if k in ("name", "gz")})
    return C.check_stream(p, **{k: v for k, v in kw.items() if k in ("run_id", "sample_run_id")})


# ---------- parser ----------

def test_parse_line_and_layers():
    line = evt(kind="fault_applied", event_id="0", tick="7", run_id="FSU-X-F0-W1")
    e = P.parse_line(line)
    assert e["kind"] == "fault_applied" and e["tick"] == "7"
    assert P.parse_line("plain text") is None
    e2 = P.parse_line("PROP-EVT: kind=execute event_id=3 tick=9 model_id=FP04")
    assert e2["kind"] == "execute" and e2["model_id"] == "FP04"
    assert P.layer_of(e2) == "L3"
    assert P.layer_of(e) == "L0"
    assert P.layer_of({"kind": "commit"}) == "L5"
    assert P.layer_of({"kind": "chain_end"}) is None
    assert P.layer_of({"kind": "contain", "detection_layer": "L3"}) == "L3"
    assert P.layer_of({"kind": "contain"}) is None


# ---------- full / contained ----------

def test_full_chain_admitted(tmp_path):
    r = check(tmp_path, chain_full())
    f = r["faults"]["1"]
    assert f["terminal"] == "full"
    assert f["layers"] == ["L0", "L1", "L2", "L3", "L4", "L5"]
    assert f["l5_witness_event_id"] == "5"
    assert f["layers_na"] == []
    assert f["beyond"] == "N/A"
    assert f["violations"] == []
    assert f["admitted"] is True
    assert r["admitted_faults"] == ["1"]


def test_contained_at_L3(tmp_path):
    b = base()
    lines = [
        evt(kind="fault_applied", event_id="0", tick="100", activated="1", **b),
        evt(kind="carrier_state", event_id="1", parent_event_id="0", tick="101", **b),
        evt(kind="operand_read", event_id="2", parent_event_id="1", tick="102", **b),
        evt(kind="execute", event_id="3", parent_event_id="2", tick="103", **b),
        evt(kind="contain", event_id="4", parent_event_id="3", tick="104",
            detection_layer="L3", contained="1", outcome="recovered", **b),
    ]
    f = check(tmp_path, lines)["faults"]["1"]
    assert f["terminal"] == "contained_L3"
    assert f["containment_layer"] == "L3"
    assert f["beyond"] == "N/A"
    assert f["layers_na"] == ["L4", "L5"]
    assert f["admitted"] is True
    assert "L4" not in f["layers"] and "L5" not in f["layers"]


def test_explicit_mask_is_not_unknown(tmp_path):
    b = base()
    lines = [
        evt(kind="fault_applied", event_id="0", tick="100", activated="1", **b),
        evt(kind="carrier_state", event_id="1", parent_event_id="0", tick="101", **b),
        evt(kind="mask", event_id="2", parent_event_id="1", tick="102",
            detection_layer="L1", contained="1", outcome="masked", **b),
    ]
    f = check(tmp_path, lines)["faults"]["1"]
    assert f["terminal"] == "contained_L1"
    assert f["admitted"] is True


def test_not_activated_is_not_contained(tmp_path):
    b = base()
    lines = [
        evt(kind="fault_applied", event_id="0", tick="100", activated="0", **b),
        evt(kind="carrier_state", event_id="1", parent_event_id="0", tick="101", **b),
    ]
    f = check(tmp_path, lines)["faults"]["1"]
    assert f["terminal"] == "not_activated"
    assert f["admitted"] is False


def test_not_activated_event_terminal(tmp_path):
    b = base()
    lines = [
        evt(kind="fault_applied", event_id="0", tick="100", **b),
        evt(kind="carrier_state", event_id="1", parent_event_id="0", tick="101", **b),
        evt(kind="not_activated", event_id="2", parent_event_id="1", tick="102",
            activated="0", **b),
    ]
    f = check(tmp_path, lines)["faults"]["1"]
    assert f["terminal"] == "not_activated"
    assert f["admitted"] is False


# ---------- 负向 ----------

def test_missing_parent_rejected(tmp_path):
    b = base()
    lines = chain_full()
    lines[2] = evt(kind="operand_read", event_id="2", parent_event_id="99",
                   tick="102", **b)
    f = check(tmp_path, lines)["faults"]["1"]
    assert any(v.startswith("orphan_parent:2->99") for v in f["violations"])
    assert f["admitted"] is False


def test_tick_regression_rejected(tmp_path):
    lines = chain_full()
    lines[2] = evt(kind="operand_read", event_id="2", parent_event_id="1",
                   tick="50", **base())
    f = check(tmp_path, lines)["faults"]["1"]
    assert any(v.startswith("tick_regression:2") for v in f["violations"])
    assert f["admitted"] is False


def test_layer_regression_rejected(tmp_path):
    b = base()
    lines = [
        evt(kind="fault_applied", event_id="0", tick="100", activated="1", **b),
        evt(kind="execute", event_id="1", parent_event_id="0", tick="101", **b),
        evt(kind="carrier_state", event_id="2", parent_event_id="1", tick="102", **b),
    ]
    f = check(tmp_path, lines)["faults"]["1"]
    assert "layer_regression" in f["violations"]
    assert f["admitted"] is False


def test_chain_end_cannot_impersonate_l5(tmp_path):
    b = base()
    lines = [
        evt(kind="fault_applied", event_id="0", tick="100", activated="1", **b),
        evt(kind="carrier_state", event_id="1", parent_event_id="0", tick="101", **b),
        evt(kind="chain_end", event_id="2", parent_event_id="1", tick="102",
            detection_layer="L5", outcome="errant_commit_seen", **b),
    ]
    f = check(tmp_path, lines)["faults"]["1"]
    assert f["terminal"] == "provable_to_L1_then_unknown"
    assert f["beyond"] == "Unknown"
    assert any(v.startswith("chain_end_claimed_l5") for v in f["violations"])
    assert f["admitted"] is False


def test_l5_without_witness_rejected(tmp_path):
    lines = chain_full()
    b = base()
    lines[5] = evt(kind="commit", event_id="5", parent_event_id="4", tick="105",
                   detection_layer="L5", outcome="", **b)
    f = check(tmp_path, lines)["faults"]["1"]
    assert any(v.startswith("l5_without_witness:5") for v in f["violations"])
    assert f["terminal"] != "full"
    assert f["admitted"] is False


def test_missing_L2_is_full_with_na(tmp_path):
    """真实未到达的 L2 记 N/A，不算跳接凑层；L0/L1/L5 齐全仍为 full。"""
    b = base()
    lines = [
        evt(kind="fault_applied", event_id="0", tick="100", activated="1", **b),
        evt(kind="carrier_state", event_id="1", parent_event_id="0", tick="101", **b),
        evt(kind="execute", event_id="2", parent_event_id="1", tick="102", **b),
        evt(kind="prf_writeback", event_id="3", parent_event_id="2", tick="103", **b),
        evt(kind="commit", event_id="4", parent_event_id="3", tick="104",
            detection_layer="L5", outcome="errant_commit", **b),
    ]
    f = check(tmp_path, lines)["faults"]["1"]
    assert f["terminal"] == "full"
    assert f["layers_na"] == ["L2"]
    assert f["admitted"] is True


def test_missing_carrier_not_full(tmp_path):
    b = base()
    lines = [
        evt(kind="fault_applied", event_id="0", tick="100", activated="1", **b),
        evt(kind="execute", event_id="1", parent_event_id="0", tick="101", **b),
        evt(kind="prf_writeback", event_id="2", parent_event_id="1", tick="102", **b),
        evt(kind="commit", event_id="3", parent_event_id="2", tick="103",
            detection_layer="L5", outcome="errant_commit", **b),
    ]
    f = check(tmp_path, lines)["faults"]["1"]
    assert f["terminal"].startswith("provable_to_L5_then_unknown")
    assert "incomplete_carrier_sequence" in f["violations"]
    assert f["admitted"] is False


def test_branch_is_off_chain(tmp_path):
    b = base()
    lines = chain_full() + [
        evt(kind="carrier_state", event_id="b1", parent_event_id="0",
            tick="101", **b),
    ]
    f = check(tmp_path, lines)["faults"]["1"]
    assert f["terminal"] == "full"
    assert "b1" in f["off_chain_event_ids"]
    assert "b1" not in f["path_event_ids"]


def test_duplicate_event_id_rejected(tmp_path):
    b = base()
    lines = [
        evt(kind="fault_applied", event_id="0", tick="100", activated="1", **b),
        evt(kind="carrier_state", event_id="1", parent_event_id="0", tick="101", **b),
        evt(kind="operand_read", event_id="1", parent_event_id="0", tick="102", **b),
    ]
    f = check(tmp_path, lines)["faults"]["1"]
    assert any(v.startswith("duplicate_event_id:1") for v in f["violations"])
    assert f["admitted"] is False


def test_cross_seed_identity_rejected(tmp_path):
    r = check(tmp_path, chain_full(), sample_run_id="s2")
    f = r["faults"]["1"]
    assert r["identity_violations"]
    assert f["admitted"] is False


def test_wrong_run_id_rejected(tmp_path):
    r = check(tmp_path, chain_full(), run_id="FSU-OTHER-F0-W4")
    assert r["identity_violations"]
    assert r["admitted_faults"] == []


# ---------- 截断 / 容量 ----------

def test_truncated_gzip_detected(tmp_path):
    p = write(tmp_path, chain_full(), name="ev.txt.gz", gz=True)
    data = p.read_bytes()
    p.write_bytes(data[:-12])           # 破坏 gzip 尾部/CRC
    events, truncated, reason = P.read_stream(p)
    assert truncated is True
    assert reason


def test_truncation_blocks_admission(tmp_path, monkeypatch):
    p = write(tmp_path, chain_full())
    orig = P.read_stream
    monkeypatch.setattr(P, "read_stream",
                        lambda _p: (orig(p)[0], True, "forced"))
    r = C.check_stream(p)
    assert r["truncated"] is True
    assert r["admitted_faults"] == []
    assert any("truncated_stream" in f["violations"] for f in r["faults"].values())


def test_event_cap_marks_truncated(tmp_path, monkeypatch):
    p = write(tmp_path, chain_full())
    monkeypatch.setattr(P, "EVENT_CAP", 2)
    events, truncated, reason = P.read_stream(p)
    assert len(events) == 2
    assert truncated is True
    assert reason.startswith("event_cap_exceeded")
