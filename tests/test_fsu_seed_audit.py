"""tests/test_fsu_seed_audit.py — 逐 seed 审计器（伪造/缺事件/跨 seed/哈希）。"""
import gzip
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import fsu_prop_fields as P
import fsu_seed_audit as A
import fsu_seed_runner as R

GOLDEN = "a" * 64
RUNID = "FSU-FP04-F0-W4"


def evt(**kw):
    d = {k: "" for k in P.PROP_EVT_FIELDS}
    d.update(kw)
    return P.PREFIX + " " + " ".join(f"{k}={d[k]}" for k in P.PROP_EVT_FIELDS)


def chain():
    b = dict(run_id=RUNID, sample_run_id="s1", fault_id="1",
             model_id="FP04", unit="FSU Pipe", freq="F0", load_id="W4",
             submodel="FP04-c", field="mant_lo", precision="fp64",
             lane_width="64", lane_offset="0", bit_indices="5",
             bit_in_lane="5", field_lo="0", field_hi="17",
             fault_mask="0x0000000000000020",
             lane_mask="0x00000000000000000000000000000020",
             before="0x3ff0000000000000",
             after="0x3ff0000000000020",
             full_before="0x00000000000000003ff0000000000000",
             full_after="0x00000000000000003ff0000000000020")
    return [
        evt(kind="fault_applied", event_id="0", tick="100", activated="1", **b),
        evt(kind="carrier_state", event_id="1", parent_event_id="0", tick="101", **b),
        evt(kind="operand_read", event_id="2", parent_event_id="1", tick="102",
            activated="1", **b),
        evt(kind="execute", event_id="3", parent_event_id="2", tick="103", **b),
        evt(kind="prf_writeback", event_id="4", parent_event_id="3", tick="104", **b),
        evt(kind="commit", event_id="5", parent_event_id="4", tick="105",
            detection_layer="L5", outcome="errant_commit", **b),
    ]


def fake_runner(lines, stdout="ARRAYHASH=" + "0" * 64):
    def runner(cmd, timeout):
        outdir = Path(cmd[cmd.index("-d") + 1])
        outdir.mkdir(parents=True, exist_ok=True)
        if "--fpu_count_only" in cmd:
            (outdir / "fpu_injections.log").write_text(
                "CHAOS_ELIGIBLE_COUNT=100\n", encoding="utf-8")
            (outdir / "stats.txt").write_text("simSeconds 1\n", encoding="utf-8")
            return 0, "", "", False
        (outdir / "fpu_injections.log").write_text(
            "faults_injected: 1\n", encoding="utf-8")
        (outdir / "stats.txt").write_text("simSeconds 1\n", encoding="utf-8")
        (outdir / "prop_evt.txt.gz").write_bytes(
            gzip.compress(("\n".join(lines) + "\n").encode()))
        return 0, stdout, "", False
    return runner


def make_attempt(tmp_path):
    wl = tmp_path / "wl"
    wl.write_text("#!/bin/sh\nexit 0\n")
    wl.chmod(0o755)
    gem5 = tmp_path / "gem5"
    gem5.write_text("#!/bin/sh\nexit 0\n")
    gem5.chmod(0o755)
    m = {
        "run_id": RUNID, "model_id": "FP04", "unit": "FSU Pipe",
        "freq": "F0", "load_id": "W4", "submodel": "FP04-c",
        "workload": {"binary": str(wl), "golden": GOLDEN,
                     "oracle_kind": "array_hash"},
        "injector": {"component": "fsu", "fpu_mode": {"bitseg": "mant_lo"},
                     "max_faults": 1, "first_clock": 0},
        "limits": {"timeout_s": 10},
    }
    mp = tmp_path / "manifest.json"
    mp.write_text(json.dumps(m), encoding="utf-8")
    res = R.run_seed(mp, 1, out_root=tmp_path / "runs", gem5=gem5,
                     root=Path(__file__).resolve().parents[1],
                     runner=fake_runner(chain()))
    assert res["status"] == "admitted"
    return Path(res["attempt"])


def rewrite_prop(attempt, fn):
    p = attempt / "inject/prop_evt.txt.gz"
    text = gzip.decompress(p.read_bytes()).decode()
    p.write_bytes(gzip.compress(fn(text).encode()))


def test_audit_passes(tmp_path):
    res = A.audit_attempt(make_attempt(tmp_path))
    assert res["ok"] is True, res["failures"]


def test_audit_detects_md_terminal_tamper(tmp_path):
    attempt = make_attempt(tmp_path)
    md = attempt / f"{RUNID}-seed1.md"
    md.write_text(md.read_text(encoding="utf-8").replace(
        "传播链 terminal：**full**", "传播链 terminal：**contained_L3**"),
        encoding="utf-8")
    res = A.audit_attempt(attempt)
    assert res["ok"] is False
    assert any("terminal" in f for f in res["failures"])


def test_audit_detects_md_parent_tamper(tmp_path):
    attempt = make_attempt(tmp_path)
    md = attempt / f"{RUNID}-seed1.md"
    text = md.read_text(encoding="utf-8")
    text = text.replace("| commit | 5 | 4 |", "| commit | 5 | 3 |")
    md.write_text(text, encoding="utf-8")
    res = A.audit_attempt(attempt)
    assert res["ok"] is False
    assert any("parent" in f for f in res["failures"])


def test_audit_detects_evidence_hash_tamper(tmp_path):
    attempt = make_attempt(tmp_path)
    with open(attempt / "run.out", "a", encoding="utf-8") as f:
        f.write("TAMPERED\n")
    res = A.audit_attempt(attempt)
    assert res["ok"] is False
    assert any("SHA-256" in f for f in res["failures"])


def test_audit_detects_cross_seed_copy(tmp_path):
    attempt = make_attempt(tmp_path)
    rewrite_prop(attempt, lambda t: t.replace("sample_run_id=s1",
                                              "sample_run_id=s2"))
    res = A.audit_attempt(attempt)
    assert res["ok"] is False
    assert any("身份全为本 seed" in f for f in res["failures"])


def test_audit_detects_forged_parent(tmp_path):
    attempt = make_attempt(tmp_path)
    rewrite_prop(attempt, lambda t: t.replace("parent_event_id=4",
                                              "parent_event_id=99"))
    res = A.audit_attempt(attempt)
    assert res["ok"] is False
    assert any("terminal" in f or "violations" in f for f in res["failures"])


def test_audit_detects_missing_event(tmp_path):
    attempt = make_attempt(tmp_path)
    rewrite_prop(attempt, lambda t: "\n".join(
        l for l in t.splitlines() if "event_id=4 " not in l))
    res = A.audit_attempt(attempt)
    assert res["ok"] is False
    assert any("MD event 4" in f or "主链全部事件" in f for f in res["failures"])


def test_field_violations_decimal_bit_and_fp04d_lane_domain():
    # bit_indices is decimal: "63" must mean bit 63, not 0x63=99.
    e = P.parse_line(evt(
        kind="fault_applied", field="sign", precision="fp64",
        submodel="FP04-a", lane_width="64", lane_offset="0",
        bit_indices="63", bit_in_lane="63", field_lo="63", field_hi="63",
        fault_mask="0x8000000000000000",
        lane_mask="0x00000000000000008000000000000000",
        before="0x4080580000000000", after="0xc080580000000000",
        full_before="0x00000000000000004080580000000000",
        full_after="0x0000000000000000c080580000000000"))
    assert A._field_violations(e) == []

    # FP04-d is the lane domain: a lane-selected sign flip is valid even
    # though the field itself maps to FP04-a.
    lane2 = P.parse_line(evt(
        kind="fault_applied", field="sign", precision="fp32",
        submodel="FP04-d", lane_width="32", lane_offset="2",
        bit_indices="95", bit_in_lane="31", field_lo="31", field_hi="31",
        fault_mask="0x0000000080000000",
        lane_mask="0x00000000800000000000000000000000",
        before="0x3e7ff79e", after="0xbe7ff79e",
        full_before="0x3f9170e73e7ff79e3e7efbb53f1b9433",
        full_after="0x3f9170e7be7ff79e3e7efbb53f1b9433"))
    assert A._field_violations(lane2) == []

    # A scalar sign flip labelled FP04-c is still a mapping violation.
    wrong = P.parse_line(evt(
        kind="fault_applied", field="sign", precision="fp32",
        submodel="FP04-c", lane_width="32", lane_offset="0",
        bit_indices="31", bit_in_lane="31", field_lo="31", field_hi="31",
        fault_mask="0x80000000", lane_mask="0x00000000000000000000000080000000",
        before="0x3ec41894", after="0xbec41894",
        full_before="0x0000000000000000000000003ec41894",
        full_after="0x000000000000000000000000bec41894"))
    assert A._field_violations(wrong)


def test_decode_violations_new_and_legacy():
    # Legacy root: no decoded_kind -> legacy-valid, no decode violation.
    legacy = P.parse_line(evt(kind="fault_applied", fault_id="1"))
    assert A._decode_violations(legacy) == []

    good = P.parse_line(evt(
        kind="fault_applied", fault_id="1", decoded_kind="scalar_vfp",
        decoded_reliable="1", precision_match="1", lane_match="1",
        instruction_bits="0x1e222820", decoded_precision="fp32",
        manifest_precision="fp32", decoded_element_width="32",
        decoded_lanes="1", manifest_lane_width="32", lane_width="32",
        lane_offset="0"))
    assert A._decode_violations(good) == []

    bad_prec = P.parse_line(evt(
        kind="fault_applied", fault_id="2", decoded_kind="scalar_vfp",
        decoded_reliable="1", precision_match="0", lane_match="1",
        instruction_bits="0x1e622820", decoded_precision="fp64",
        manifest_precision="fp32", decoded_element_width="64",
        decoded_lanes="1", manifest_lane_width="64", lane_width="64",
        lane_offset="0"))
    assert any("precision_match" in v for v in A._decode_violations(bad_prec))

    bad_lane = P.parse_line(evt(
        kind="fault_applied", fault_id="3", decoded_kind="neon_vector",
        decoded_reliable="1", precision_match="1", lane_match="0",
        instruction_bits="0x4e22d420", decoded_precision="fp32",
        manifest_precision="fp32", decoded_element_width="32",
        decoded_lanes="4", manifest_lane_width="64", lane_width="64",
        lane_offset="0"))
    viol = A._decode_violations(bad_lane)
    assert any("lane_match" in v or "lane_width" in v for v in viol)

    undecoded = P.parse_line(evt(
        kind="fault_applied", fault_id="4", decoded_kind="cvt",
        decoded_reliable="0", precision_match="0", lane_match="0"))
    assert any("decoded_kind" in v or "reliable" in v
               for v in A._decode_violations(undecoded))
