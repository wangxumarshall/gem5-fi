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
             submodel="FP04-c")
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
