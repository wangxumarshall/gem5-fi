"""tests/test_fsu_seed_runner.py — 单 seed 运行器/证据/文档编排测试（假 gem5）。"""
import gzip
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import fsu_prop_fields as P
import fsu_seed_runner as R

GOLDEN = "a" * 64
RUNID = "FSU-FP04-F0-W4"


def evt(**kw):
    d = {k: "" for k in P.PROP_EVT_FIELDS}
    d.update(kw)
    return P.PREFIX + " " + " ".join(f"{k}={d[k]}" for k in P.PROP_EVT_FIELDS)


def base():
    return dict(run_id=RUNID, sample_run_id="s1", fault_id="1",
                model_id="FP04", unit="FSU Pipe", freq="F0", load_id="W4",
                submodel="FP04-c")


def full_chain():
    b = base()
    return [
        evt(kind="fault_applied", event_id="0", tick="100", activated="1",
            before="0x1", after="0x2", mask="0x1", bit_indices="0",
            **b),
        evt(kind="carrier_state", event_id="1", parent_event_id="0", tick="101", **b),
        evt(kind="operand_read", event_id="2", parent_event_id="1", tick="102", **b),
        evt(kind="execute", event_id="3", parent_event_id="2", tick="103", **b),
        evt(kind="prf_writeback", event_id="4", parent_event_id="3", tick="104", **b),
        evt(kind="commit", event_id="5", parent_event_id="4", tick="105",
            detection_layer="L5", outcome="errant_commit",
            oracle_diff="array_hash_diff", **b),
    ]


def store_chain():
    """FP04 结果被 store 消费：L3(execute) 真实不适用，记 N/A。"""
    b = base()
    return [
        evt(kind="fault_applied", event_id="0", tick="100", attempted="1",
            before="0x1", after="0x2", mask="0x1", bit_indices="0",
            phys_reg="7", field="mant_lo", **b),
        evt(kind="carrier_state", event_id="1", parent_event_id="0", tick="101",
            phys_reg="7", **b),
        evt(kind="operand_read", event_id="2", parent_event_id="1", tick="102",
            producer_seq="10", consumer_seq="20", src_slot="1",
            activated="1", **b),
        evt(kind="consumer", event_id="3", parent_event_id="2", tick="103",
            consumer_seq="20", outcome="arch_side_effect", **b),
        evt(kind="commit", event_id="4", parent_event_id="3", tick="104",
            commit_seq="20", detection_layer="L5", outcome="errant_commit",
            oracle_diff="array_hash_diff", **b),
    ]


def contained_chain():
    b = base()
    return [
        evt(kind="fault_applied", event_id="0", tick="100", activated="1", **b),
        evt(kind="carrier_state", event_id="1", parent_event_id="0", tick="101", **b),
        evt(kind="operand_read", event_id="2", parent_event_id="1", tick="102", **b),
        evt(kind="execute", event_id="3", parent_event_id="2", tick="103", **b),
        evt(kind="contain", event_id="4", parent_event_id="3", tick="104",
            detection_layer="L3", contained="1", outcome="recovered", **b),
    ]


def make_manifest(tmp_path, golden=GOLDEN):
    wl = tmp_path / "fake_workload"
    wl.write_text("#!/bin/sh\nexit 0\n")
    wl.chmod(0o755)
    gem5 = tmp_path / "fake_gem5"
    gem5.write_text("#!/bin/sh\nexit 0\n")
    gem5.chmod(0o755)
    m = {
        "run_id": RUNID, "model_id": "FP04", "unit": "FSU Pipe",
        "freq": "F0", "load_id": "W4", "submodel": "FP04-c",
        "workload": {"binary": str(wl), "golden": golden,
                     "oracle_kind": "array_hash", "oracle_tol": 0},
        "config_family": "C3",
        "injector": {"component": "fsu", "fpu_mode": {"bitseg": "mant_lo"},
                     "max_faults": 1, "first_clock": 0},
        "limits": {"timeout_s": 10},
    }
    p = tmp_path / "manifest.json"
    p.write_text(json.dumps(m), encoding="utf-8")
    return p, gem5


def fake_runner_factory(events, stdout, eligible=100, truncate=False,
                        census_zero=False):
    def runner(cmd, timeout):
        outdir = Path(cmd[cmd.index("-d") + 1])
        outdir.mkdir(parents=True, exist_ok=True)
        if "--fpu_count_only" in cmd:
            n = 0 if census_zero else eligible
            (outdir / "fpu_injections.log").write_text(
                f"CHAOS_ELIGIBLE_COUNT={n}\n", encoding="utf-8")
            (outdir / "stats.txt").write_text("simSeconds 1\n", encoding="utf-8")
            return 0, "", "", False
        (outdir / "fpu_injections.log").write_text(
            "Tick: 100, Site: dyn_inst_execute, sn=7, mask=0x1, "
            "faults_injected: 1\n", encoding="utf-8")
        (outdir / "stats.txt").write_text("simSeconds 1\nsimInsts 10\n",
                                          encoding="utf-8")
        data = gzip.compress(("\n".join(events) + "\n").encode())
        if truncate:
            data = data[:-12]
        (outdir / "prop_evt.txt.gz").write_bytes(data)
        return 0, stdout, "", False
    return runner


def run(tmp_path, runner, **kw):
    manifest, gem5 = make_manifest(tmp_path)
    return R.run_seed(manifest, 1, out_root=tmp_path / "runs", gem5=gem5,
                      root=Path(__file__).resolve().parents[1],
                      runner=runner, **kw)


def test_seed_admitted_and_evidence(tmp_path):
    res = run(tmp_path, fake_runner_factory(full_chain(), "ARRAYHASH=" + "0" * 64))
    assert res["status"] == "admitted"
    attempt = Path(res["attempt"])
    for name in ["manifest.json", "run.out", "run.err", "stats.txt",
                 "oracle.json", "chain_report.json", "evidence_sha256.json",
                 ".done"]:
        assert (attempt / name).exists(), name
    assert (attempt.parent / "AUTHORITATIVE").exists()
    rep = json.loads((attempt / "chain_report.json").read_text(encoding="utf-8"))
    assert rep["oracle"]["category"] == "SDC"
    assert rep["chain"]["admitted_faults"] == ["1"]
    f = rep["chain"]["faults"]["1"]
    assert f["terminal"] == "full" and f["admitted"] is True
    md = attempt / f"{RUNID}-seed1.md"
    text = md.read_text(encoding="utf-8")
    for sec in ["## 1. 实验身份与复现信息", "## 2. 故障注入发生在哪里",
                "## 3. 注入前后状态", "## 4. 之后依次经过哪些真实部件",
                "## 5. 完整主链事件表", "## 6. 数据、控制和污点在各层如何变化",
                "## 7. 最终结局", "## 8. 为什么该结局成立",
                "## 9. 原始证据位置与 SHA-256", "## 10. 诚实边界"]:
        assert sec in text, sec
    assert "SDC" in text and "full" in text
    hashes = json.loads((attempt / "evidence_sha256.json").read_text(encoding="utf-8"))
    assert "inject/prop_evt.txt.gz" in hashes
    # 权威 Markdown 复制
    assert (tmp_path / "runs/COMPLETE_PROPAGATION_PATHS" / RUNID /
            f"{RUNID}-seed1.md").exists()


def test_admitted_seed_not_rerun(tmp_path):
    runner = fake_runner_factory(full_chain(), "ARRAYHASH=" + "0" * 64)
    r1 = run(tmp_path, runner)
    assert r1["status"] == "admitted"
    r2 = run(tmp_path, runner)
    assert r2["status"] == "already_admitted"


def test_rerun_creates_new_attempt(tmp_path):
    runner = fake_runner_factory(full_chain(), "ARRAYHASH=" + "0" * 64)
    r1 = run(tmp_path, runner)
    r2 = run(tmp_path, runner, allow_rerun=True)
    assert r1["status"] == "admitted" and r2["status"] == "admitted"
    assert Path(r1["attempt"]).name == "attempt-1"
    assert Path(r2["attempt"]).name == "attempt-2"
    assert Path(r1["attempt"]).exists()          # 旧 attempt 保留


def test_truncated_chain_fails(tmp_path):
    res = run(tmp_path, fake_runner_factory(full_chain(), "ARRAYHASH=" + "0" * 64,
                                            truncate=True))
    assert res["status"] == "failed"
    attempt = Path(res["attempt"])
    assert (attempt / ".failed").exists()
    assert not (attempt.parent / "AUTHORITATIVE").exists()
    rep = json.loads((attempt / "chain_report.json").read_text(encoding="utf-8"))
    assert rep["chain"]["truncated"] is True


def test_eligible_zero_fails(tmp_path):
    res = run(tmp_path, fake_runner_factory(full_chain(), "", census_zero=True))
    assert res["status"] == "failed"
    assert "eligible=0" in res["reason"]


def test_store_consumer_chain_l3_na(tmp_path):
    res = run(tmp_path, fake_runner_factory(store_chain(), "ARRAYHASH=" + "0" * 64))
    assert res["status"] == "admitted"
    attempt = Path(res["attempt"])
    rep = json.loads((attempt / "chain_report.json").read_text(encoding="utf-8"))
    f = rep["chain"]["faults"]["1"]
    assert f["terminal"] == "full"
    assert f["layers"] == ["L0", "L1", "L2", "L4", "L5"]
    assert f["layers_na"] == ["L3"]
    assert f["admitted"] is True
    text = (attempt / f"{RUNID}-seed1.md").read_text(encoding="utf-8")
    assert "N/A（本 seed 真实未到达" in text
    assert "1 / 100 / 1" in text          # attempted / eligible / activated


def test_contained_chain_doc_marks_na(tmp_path):
    res = run(tmp_path, fake_runner_factory(contained_chain(), "ARRAYHASH=" + "0" * 64))
    assert res["status"] == "admitted"
    attempt = Path(res["attempt"])
    rep = json.loads((attempt / "chain_report.json").read_text(encoding="utf-8"))
    f = rep["chain"]["faults"]["1"]
    assert f["terminal"] == "contained_L3"
    assert f["layers_na"] == ["L4", "L5"]
    text = (attempt / f"{RUNID}-seed1.md").read_text(encoding="utf-8")
    assert "N/A（本 seed 真实未到达" in text
    assert "contained_L3" in text


def test_component_seed_dir_override_and_metadata(tmp_path):
    manifest, gem5 = make_manifest(tmp_path)
    cdir = tmp_path / "suite" / "components" / "gemm" / RUNID / "seed1"
    component = {
        "suite_id": "suite-test", "suite_version": "1",
        "suite_hash": "a" * 64, "suite_seed": 1,
        "program_id": "gemm", "program_index": 0, "program_count": 5,
    }
    runner = fake_runner_factory(full_chain(), "ARRAYHASH=" + "0" * 64)
    res = R.run_seed(manifest, 1, out_root=tmp_path / "runs", gem5=gem5,
                     root=Path(__file__).resolve().parents[1],
                     runner=runner, seed_dir=cdir, component=component,
                     write_authoritative=False, copy_to_complete=False)
    assert res["status"] == "admitted"
    attempt = Path(res["attempt"])
    assert attempt.parent == cdir and attempt.name == "attempt-1"
    written = json.loads((attempt / "manifest.json").read_text(encoding="utf-8"))
    assert written["component"] == component
    assert written["seed"] == 1
    assert written["sample_run_id"] == "s1"
    assert (attempt / ".done").exists()
    # Component evidence must never look like a formal seed.
    assert not (cdir / "AUTHORITATIVE").exists()
    assert not (tmp_path / "runs/COMPLETE_PROPAGATION_PATHS").exists()


def test_old_seed_dir_behavior_unchanged(tmp_path):
    res = run(tmp_path, fake_runner_factory(full_chain(),
                                            "ARRAYHASH=" + "0" * 64))
    assert res["status"] == "admitted"
    attempt = Path(res["attempt"])
    assert attempt.parent == (tmp_path / "runs" / RUNID / "seed1")
    assert (attempt.parent / "AUTHORITATIVE").exists()
    assert (tmp_path / "runs/COMPLETE_PROPAGATION_PATHS" / RUNID /
            f"{RUNID}-seed1.md").exists()


def test_f5_permanent_cli_is_wired():
    m = {
        "run_id": "FSU-FP06-F5-W3", "model_id": "FP06", "unit": "FSU Pipe",
        "freq": "F5", "load_id": "W3", "submodel": "FP06-b",
        "workload": {"binary": "wl", "golden": GOLDEN,
                     "oracle_kind": "array_hash"},
        "injector": {
            "component": "fsu",
            "fault_mask": "0x80000000",
            "max_faults": 1, "first_clock": 0,
            "fpu_mode": {"precision": "fp32", "lane_width": 32,
                         "lane_offset": 2, "decode_guard": True,
                         "permanent_stuck": True, "stuck_polarity": 1,
                         "f5_warmup": 7, "f5_sample_limit": 1024,
                         "f5_keep_first_last_n": 256}},
        "limits": {"timeout_s": 10},
    }
    cmd = R.build_cmd(m, Path("/tmp/out"), 3, 999, False,
                      Path("/bin/true"), Path("cfg.py"), Path("/"))
    assert "--fpu_permanent_stuck" in cmd
    assert cmd[cmd.index("--fpu_stuck_polarity") + 1] == "1"
    assert cmd[cmd.index("--fpu_fault_mask") + 1] == str(0x80000000)
    assert cmd[cmd.index("--fpu_f5_warmup") + 1] == "7"
    assert cmd[cmd.index("--fpu_f5_sample_limit") + 1] == "1024"
    assert cmd[cmd.index("--fpu_f5_keep_first_last_n") + 1] == "256"
    # Permanent mode uses f5Warmup, never the F0 uniform skip (C++ panics).
    assert "--fpu_events_to_skip" not in cmd
    assert "--chaos_propagation" in cmd
    # Census keeps the same permanent identity so the stream predicate is
    # identical, but adds --fpu_count_only and never the skip.
    ccmd = R.build_cmd(m, Path("/tmp/out"), 3, 999, True,
                       Path("/bin/true"), Path("cfg.py"), Path("/"))
    assert "--fpu_count_only" in ccmd and "--fpu_permanent_stuck" in ccmd
    assert "--fpu_events_to_skip" not in ccmd


def test_f5_mask_string_is_parsed():
    assert R._mask_int("0x80000000") == 0x80000000
    assert R._mask_int(0x20) == 0x20
    assert R._mask_int(None) == 0
    with pytest.raises(ValueError):
        R._mask_int(True)


def test_skip_matches_cpp_formula():
    # gem5::chaosPickSkip(seed, n) = LCG(seed ^ const) % n
    def cpp(seed, n):
        x = (seed ^ 0x9E3779B97F4A7C15) & R.MASK64
        x = (x * 6364136223846793005 + 1442695040888963407) & R.MASK64
        return x % n
    for seed, n in [(1, 100), (2, 100), (3, 7), (123456789, 99991)]:
        assert R.chaos_pick_skip(seed, n) == cpp(seed, n)
    assert R.chaos_pick_skip(0, 0) == 0
    assert R.chaos_pick_skip(5, 1) == 0
