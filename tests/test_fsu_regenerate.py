"""tests/test_fsu_regenerate.py — 派生证据重建与 certified 门禁测试。"""
import gzip
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import fsu_prop_fields as P
import fsu_regenerate as G
import fsu_seed_runner as R

GOLDEN = "a" * 64
RUNID = "FSU-FP04-F0-W4"


def evt(**kw):
    d = {k: "" for k in P.PROP_EVT_FIELDS}
    d.update(kw)
    return P.PREFIX + " " + " ".join(f"{k}={d[k]}" for k in P.PROP_EVT_FIELDS)


def chain():
    b = dict(run_id=RUNID, sample_run_id="s1", fault_id="1",
             model_id="FP04", unit="FSU_Pipe", freq="F0", load_id="W4",
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
        evt(kind="fault_applied", event_id="0", tick="100", attempted="1",
            activated="", **b),
        evt(kind="carrier_state", event_id="1", parent_event_id="0", tick="101", **b),
        evt(kind="operand_read", event_id="2", parent_event_id="1", tick="102",
            activated="1", **b),
        evt(kind="execute", event_id="3", parent_event_id="2", tick="103", **b),
        evt(kind="prf_writeback", event_id="4", parent_event_id="3", tick="104", **b),
        evt(kind="commit", event_id="5", parent_event_id="4", tick="105",
            detection_layer="L5", outcome="errant_commit", **b),
    ]


def fake_runner(lines):
    def runner(cmd, timeout):
        outdir = Path(cmd[cmd.index("-d") + 1])
        outdir.mkdir(parents=True, exist_ok=True)
        if "--fpu_count_only" in cmd:
            (outdir / "fpu_injections.log").write_text(
                "CHAOS_ELIGIBLE_COUNT=100\n", encoding="utf-8")
            (outdir / "stats.txt").write_text("simSeconds 1\n", encoding="utf-8")
            return 0, "", "", False
        (outdir / "fpu_injections.log").write_text("faults_injected: 1\n",
                                                   encoding="utf-8")
        (outdir / "stats.txt").write_text("simSeconds 1\n", encoding="utf-8")
        (outdir / "prop_evt.txt.gz").write_bytes(
            gzip.compress(("\n".join(lines) + "\n").encode()))
        return 0, "ARRAYHASH=" + "0" * 64, "", False
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


def raw_hashes(a):
    return {rel: hashlib.sha256((a / rel).read_bytes()).hexdigest()
            for rel in G.RAW_FILES if (a / rel).exists()}


def test_regenerate_adds_computed_certified(tmp_path):
    a = make_attempt(tmp_path)
    before = raw_hashes(a)
    res = G.regenerate(a, tmp_path / "runs2")
    assert raw_hashes(a) == before          # 原始证据未被修改
    rep = json.loads((a / "chain_report.json").read_text(encoding="utf-8"))
    assert rep["admitted"] is True
    assert rep["certified"] is True
    assert rep["violations"] == []
    audit = json.loads((a / "audit.json").read_text(encoding="utf-8"))
    for key in ("gzip_eof_ok", "event_count", "identity_ok",
                "direct_parent_chain", "tick_monotonic", "layers", "layers_na",
                "l5_witness", "oracle", "chain_terminal", "stats_nonempty",
                "evidence_sha256", "cross_seed_ok", "admitted", "certified",
                "violations"):
        assert key in audit, key
    assert audit["certified"] is True and audit["ok"] is True
    assert audit["l5_witness"]["kind"] == "commit"
    assert audit["oracle"] == "SDC"
    assert audit["chain_terminal"] == "full"
    assert (a / "audit.md").exists()
    md = (a / f"{RUNID}-seed1.md").read_text(encoding="utf-8")
    assert "admitted / certified：True / True" in md
    assert res["audit_ok"] is True
    assert (tmp_path / "runs2/COMPLETE_PROPAGATION_PATHS" / RUNID /
            f"{RUNID}-seed1.md").exists()


def test_regenerate_forged_parent_not_certified(tmp_path):
    a = make_attempt(tmp_path)
    p = a / "inject/prop_evt.txt.gz"
    text = gzip.decompress(p.read_bytes()).decode()
    p.write_bytes(gzip.compress(text.replace("parent_event_id=4",
                                             "parent_event_id=99").encode()))
    res = G.regenerate(a, tmp_path / "runs2")
    rep = json.loads((a / "chain_report.json").read_text(encoding="utf-8"))
    assert rep["certified"] is False
    assert rep["violations"]
    audit = json.loads((a / "audit.json").read_text(encoding="utf-8"))
    assert audit["certified"] is False
    assert audit["ok"] is False
    assert res["certified"] is False
