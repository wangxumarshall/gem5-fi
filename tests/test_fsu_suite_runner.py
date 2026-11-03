"""tests/test_fsu_suite_runner.py — suite runner（假 gem5，不运行真 gem5）。

覆盖：
  - 5/5 component 通过 → suite admitted，index 只 +1 seed；
  - 任一 component 失败 → suite 不 admitted、无 AUTHORITATIVE；
  - 重试只新建失败 component 的 attempt-k+1，旧 attempt-1 原样保留；
  - suite_hash 漂移 / 缺 component / 重复 component 拒绝运行；
  - component 数绝不等于 seed 数。
"""
import gzip
import json
import struct
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import fsu_prop_fields as P  # noqa: E402
import fsu_seed_audit as A  # noqa: E402
import fsu_suite as S  # noqa: E402
import fsu_suite_runner as SR  # noqa: E402
import fsu_index as I  # noqa: E402

RID = "FSU-TEST-F0-W5"


def evt(**kw):
    d = {k: "" for k in P.PROP_EVT_FIELDS}
    d.update(kw)
    return P.PREFIX + " " + " ".join(f"{k}={d[k]}" for k in P.PROP_EVT_FIELDS)


def chain(run_id, seed):
    b = dict(run_id=run_id, sample_run_id=f"s{seed}", fault_id="1",
             model_id="FP04", unit="FSU Pipe", freq="F0", load_id="W5",
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
        evt(kind="carrier_state", event_id="1", parent_event_id="0",
            tick="101", **b),
        evt(kind="operand_read", event_id="2", parent_event_id="1",
            tick="102", activated="1", **b),
        evt(kind="execute", event_id="3", parent_event_id="2", tick="103", **b),
        evt(kind="prf_writeback", event_id="4", parent_event_id="3",
            tick="104", **b),
        evt(kind="commit", event_id="5", parent_event_id="4", tick="105",
            detection_layer="L5", outcome="errant_commit", **b),
    ]


def make_suite(tmp_path):
    root = tmp_path
    (root / "src").mkdir()
    (root / "bin").mkdir()
    golden_dir = root / "golden"
    golden_dir.mkdir()
    golden_arrays = {}
    programs = []
    for i, pid in enumerate(S.PROGRAM_ORDER):
        src = root / "src" / f"{pid}.c"
        src.write_text(f"/* {pid} */\nint main(void){{return 0;}}\n",
                       encoding="utf-8")
        binary = root / "bin" / pid
        binary.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        binary.chmod(0o755)
        golden_path = golden_dir / f"{pid}.bin"
        data = struct.pack("<2f", float(i + 1), float(i + 2))
        golden_path.write_bytes(data)
        golden_arrays[pid] = data
        meta = {
            "program_id": pid, "golden_id": f"test-{pid}-golden-v1",
            "dtype": "fp32", "layout": "row-major",
            "endianness": "little", "count": 2, "shape": [2, 1],
            "abs_tol": 0.0, "rel_tol": 0.0, "ulp_tol": 0,
            "oracle_version": "polybench-element-v1",
        }
        programs.append({
            "program_id": pid,
            "program_index": i,
            "source": str(src),
            "source_sha256": S.sha256_file(src),
            "binary": str(binary),
            "binary_sha256": S.sha256_file(binary),
            "scale": {"N": 8 + i},
            "golden": f"{i + 1:016x}",
            "element_oracle": {
                "golden_array": str(golden_path),
                "meta": meta,
                "oracle_version": "polybench-element-v1",
            },
        })
    suite = {
        "suite_id": "test-polybench-fp-v1",
        "suite_version": "1",
        "program_order": list(S.PROGRAM_ORDER),
        "program_count": 5,
        "run_defaults": {
            "model_id": "FP04", "unit": "FSU Pipe", "freq": "F0",
            "load_id": "W5", "submodel": "FP04-c",
            "config_family": "C3", "config_profile": "C3",
            "limits": {"timeout_s": 10},
        },
        "injector": {
            "component": "fsu",
            "fpu_mode": {"bitseg": "mant_lo"},
            "max_faults": 1,
            "first_clock": 0,
        },
        "compiler": {"cc": "gcc", "version": "test-gcc",
                     "cflags": ["-O2", "-static"]},
        "oracle": {"id": "polybench-element-v1",
                   "version": "polybench-element-v1", "kind": "exact_hash"},
        "programs": programs,
    }
    suite["suite_hash"] = S.compute_suite_hash(suite)
    path = root / "suite.json"
    path.write_text(json.dumps(suite, ensure_ascii=False, indent=2),
                    encoding="utf-8")
    gem5 = root / "fake_gem5"
    gem5.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    gem5.chmod(0o755)
    return path, suite, gem5, golden_arrays


def golden_for(suite, cmd):
    binary = Path(cmd[cmd.index("--cmd") + 1]).name
    return next(p["golden"] for p in suite["programs"]
                if p["program_id"] == binary)


def fake_runner(suite, golden_arrays=None, fail_programs=(), census_zero=(),
                calls=None, omit_array=(), sdc_programs=()):
    fail_programs = set(fail_programs)
    census_zero = set(census_zero)
    omit_array = set(omit_array)
    sdc_programs = set(sdc_programs)

    def runner(cmd, timeout):
        if calls is not None:
            calls.append(list(cmd))
        outdir = Path(cmd[cmd.index("-d") + 1])
        outdir.mkdir(parents=True, exist_ok=True)
        program = Path(cmd[cmd.index("--cmd") + 1]).name
        if "--fpu_count_only" in cmd:
            n = 0 if program in census_zero else 100
            (outdir / "fpu_injections.log").write_text(
                f"CHAOS_ELIGIBLE_COUNT={n}\n", encoding="utf-8")
            (outdir / "stats.txt").write_text("simSeconds 1\n",
                                              encoding="utf-8")
            return 0, "", "", False
        seed = int(cmd[cmd.index("--rng_seed") + 1])
        run_id = cmd[cmd.index("--prop_run_id") + 1]
        (outdir / "fpu_injections.log").write_text(
            "Tick: 100, Site: dyn_inst_execute, sn=7, mask=0x20, "
            "faults_injected: 1\n", encoding="utf-8")
        (outdir / "stats.txt").write_text("simSeconds 1\nsimInsts 10\n",
                                          encoding="utf-8")
        data = gzip.compress(("\n".join(chain(run_id, seed)) + "\n").encode())
        if program in fail_programs:
            data = data[:-12]
        (outdir / "prop_evt.txt.gz").write_bytes(data)
        dump = next((t.split("--array-dump=", 1)[1] for t in cmd
                     if "--array-dump=" in t), None)
        if dump and program not in omit_array:
            if program in sdc_programs:
                payload = struct.pack("<2f", 9.0, 9.0)
            else:
                payload = golden_arrays[program]
            Path(dump).parent.mkdir(parents=True, exist_ok=True)
            Path(dump).write_bytes(payload)
        return 0, f"FINAL={golden_for(suite, cmd)}\n", "", False
    return runner


def run(tmp_path, suite_path, gem5, runner, seed=1, out="runs",
        allow_rerun=False):
    return SR.run_suite(suite_path, seed, RID, out_root=tmp_path / out,
                        gem5=gem5, root=tmp_path, runner=runner,
                        allow_rerun=allow_rerun)


def component_attempts(seed_dir):
    return sorted(seed_dir.glob("components/*/*/seed*/attempt-*"))


def test_suite_5_of_5_admitted_and_counts_one_seed(tmp_path):
    suite_path, suite, gem5, goldens = make_suite(tmp_path)
    res = run(tmp_path, suite_path, gem5, fake_runner(suite, goldens))
    assert res["status"] == "admitted", res
    assert res["component_runs"] == 5
    assert res["formal_suite_seed_increment"] == 1

    seed_dir = Path(res["suite_seed_dir"])
    for name in ("suite_manifest.json", "suite_report.json", "audit.json",
                 "audit.md", "AUTHORITATIVE", ".done"):
        assert (seed_dir / name).exists(), name
    assert not (seed_dir / ".failed").exists()

    report = json.loads((seed_dir / "suite_report.json").read_text(
        encoding="utf-8"))
    assert report["formal_suite_seed_count"] == 1
    assert report["component_run_count"] == 5
    assert report["component_fault_total"] == 5
    assert report["suite_status"] == "admitted"

    sm = json.loads((seed_dir / "suite_manifest.json").read_text(
        encoding="utf-8"))
    assert [c["program_id"] for c in sm["components"]] == list(
        S.PROGRAM_ORDER)
    assert len(component_attempts(seed_dir)) == 5
    for c in sm["components"]:
        cm = json.loads((Path(c["attempt"]) / "component_manifest.json")
                        .read_text(encoding="utf-8"))
        S.validate_component_manifest(cm, suite)
        assert cm["component_status"] == "admitted"
        assert cm["component_certified"] is True
        assert cm["component_attempt"] == 1
        assert cm["component_oracle"] == "MASKED"
        oe = json.loads((Path(c["attempt"]) / "oracle_elements.json")
                        .read_text(encoding="utf-8"))
        assert oe["ok"] is True
        assert oe["mismatch_count"] == 0
        assert oe["golden_sha256"] and oe["fault_sha256"]
        hashes = json.loads((Path(c["attempt"]) / "evidence_sha256.json")
                            .read_text(encoding="utf-8"))
        assert "oracle_elements.json" in hashes
        assert "inject/array.bin" in hashes

    # The authoritative directory carries exactly ONE suite-level Markdown
    # for the formal seed (component MDs are linked, never copied as seeds).
    complete = tmp_path / "runs/COMPLETE_PROPAGATION_PATHS" / RID
    suite_mds = sorted(complete.glob(f"{RID}-seed*.md"))
    assert [p.name for p in suite_mds] == [f"{RID}-seed1.md"]

    # index: 5 component runs == 1 admitted seed, never 5.
    runids = tmp_path / "runids.json"
    runids.write_text(json.dumps({"runids": [{"RunID": RID}]}),
                      encoding="utf-8")
    summary, rows = I.write_index(I._load_runids(runids),
                                  tmp_path / "runs", runids, None)
    assert summary["admitted_seeds_total"] == 1
    assert summary["suite_seed_dirs"] == 1
    assert summary["suite_seed_admitted"] == 1
    assert summary["component_runs_in_admitted_suites"] == 5
    assert rows[0]["seeds"][1]["state"] == "admitted"

    # Idempotent second call.
    res2 = run(tmp_path, suite_path, gem5, fake_runner(suite, goldens))
    assert res2["status"] == "already_admitted"
    assert len(component_attempts(seed_dir)) == 5


def test_component_failure_blocks_suite_and_retry_preserves_attempt1(tmp_path):
    suite_path, suite, gem5, goldens = make_suite(tmp_path)
    res = run(tmp_path, suite_path, gem5,
              fake_runner(suite, goldens, fail_programs={"lu"}))
    assert res["status"] == "failed"
    seed_dir = Path(res["suite_seed_dir"])
    assert (seed_dir / ".failed").exists()
    assert not (seed_dir / "AUTHORITATIVE").exists()
    assert not (seed_dir / "suite_manifest.json").exists()
    assert res["failed_components"] == ["lu"]

    lu_attempt1 = next(seed_dir.glob(
        "components/lu/*/seed*/attempt-1"))
    assert (lu_attempt1 / ".failed").exists()
    old_manifest_sha = S.sha256_file(lu_attempt1 / "manifest.json")
    good_attempts = {}
    for pid in S.PROGRAM_ORDER:
        if pid == "lu":
            continue
        att = next(seed_dir.glob(f"components/{pid}/*/seed*/attempt-*"))
        good_attempts[pid] = S.sha256_file(att / "manifest.json")

    res2 = run(tmp_path, suite_path, gem5, fake_runner(suite, goldens))
    assert res2["status"] == "admitted", res2
    seed_dir2 = Path(res2["suite_seed_dir"])
    assert seed_dir2 == seed_dir
    lu_attempt2 = sorted(seed_dir.glob("components/lu/*/seed*/attempt-*"))[-1]
    assert lu_attempt2.name == "attempt-2"
    assert lu_attempt1.exists()
    assert S.sha256_file(lu_attempt1 / "manifest.json") == old_manifest_sha
    # Already-admitted components are reused, not rerun.
    for pid, sha in good_attempts.items():
        att = next(seed_dir.glob(f"components/{pid}/*/seed*/attempt-*"))
        assert att.name == "attempt-1"
        assert S.sha256_file(att / "manifest.json") == sha
    assert (seed_dir / "AUTHORITATIVE").exists()
    assert not (seed_dir / ".failed").exists()
    assert (seed_dir / "suite_failures.jsonl").exists()


def test_suite_hash_drift_refuses_before_running(tmp_path):
    suite_path, suite, gem5, goldens = make_suite(tmp_path)
    tampered = json.loads(suite_path.read_text(encoding="utf-8"))
    tampered["compiler"]["version"] = "tampered"
    suite_path.write_text(json.dumps(tampered), encoding="utf-8")
    calls = []
    with pytest.raises(S.SuiteError, match="suite_hash drift"):
        run(tmp_path, suite_path, gem5,
            fake_runner(suite, goldens, calls=calls))
    assert calls == []
    assert not (tmp_path / "runs" / RID / "seed1").exists()


def test_missing_component_refused(tmp_path):
    suite_path, suite, gem5, goldens = make_suite(tmp_path)
    bad = json.loads(suite_path.read_text(encoding="utf-8"))
    bad["programs"] = [p for p in bad["programs"]
                       if p["program_id"] != "jacobi-2d"]
    suite_path.write_text(json.dumps(bad), encoding="utf-8")
    calls = []
    with pytest.raises(S.SuiteError, match="missing program"):
        run(tmp_path, suite_path, gem5, fake_runner(suite, goldens,
                                                    calls=calls))
    assert calls == []


def test_duplicate_component_refused(tmp_path):
    suite_path, suite, gem5, goldens = make_suite(tmp_path)
    bad = json.loads(suite_path.read_text(encoding="utf-8"))
    bad["programs"][4] = json.loads(json.dumps(bad["programs"][0]))
    suite_path.write_text(json.dumps(bad), encoding="utf-8")
    calls = []
    with pytest.raises(S.SuiteError, match="duplicate program"):
        run(tmp_path, suite_path, gem5, fake_runner(suite, goldens,
                                                    calls=calls))
    assert calls == []


def test_census_zero_component_blocks_suite(tmp_path):
    suite_path, suite, gem5, goldens = make_suite(tmp_path)
    res = run(tmp_path, suite_path, gem5,
              fake_runner(suite, goldens, census_zero={"cholesky"}))
    assert res["status"] == "failed"
    assert "cholesky" in res["failed_components"]
    seed_dir = Path(res["suite_seed_dir"])
    cm = json.loads(next(seed_dir.glob(
        "components/cholesky/*/seed*/attempt-*/component_manifest.json")
    ).read_text(encoding="utf-8"))
    assert cm["component_status"] == "failed"
    assert cm["component_eligible"] == 0


def test_element_oracle_sdc_recorded_and_admitted(tmp_path):
    suite_path, suite, gem5, goldens = make_suite(tmp_path)
    res = run(tmp_path, suite_path, gem5,
              fake_runner(suite, goldens, sdc_programs={"lu"}))
    assert res["status"] == "admitted", res
    seed_dir = Path(res["suite_seed_dir"])
    lu = next(seed_dir.glob("components/lu/*/seed*/attempt-1"))
    cm = json.loads((lu / "component_manifest.json").read_text(
        encoding="utf-8"))
    assert cm["component_oracle"] == "SDC"
    assert cm["component_oracle_mismatch_count"] > 0
    oe = json.loads((lu / "oracle_elements.json").read_text(
        encoding="utf-8"))
    assert oe["category"] == "DIFF"
    assert oe["mismatch_count"] > 0
    assert oe["first_mismatch_index"] == 0
    other = next(seed_dir.glob("components/gemm/*/seed*/attempt-1"))
    cm2 = json.loads((other / "component_manifest.json").read_text(
        encoding="utf-8"))
    assert cm2["component_oracle"] == "MASKED"


def test_missing_array_dump_fails_component(tmp_path):
    suite_path, suite, gem5, goldens = make_suite(tmp_path)
    res = run(tmp_path, suite_path, gem5,
              fake_runner(suite, goldens, omit_array={"cholesky"}))
    assert res["status"] == "failed"
    assert "cholesky" in res["failed_components"]
    seed_dir = Path(res["suite_seed_dir"])
    att = next(seed_dir.glob("components/cholesky/*/seed*/attempt-1"))
    cm = json.loads((att / "component_manifest.json").read_text(
        encoding="utf-8"))
    assert cm["component_status"] == "failed"
    assert cm["component_oracle"] == "ORACLE_ERROR"
    assert not (seed_dir / "AUTHORITATIVE").exists()


def test_seed_build_cmd_adds_array_dump_only_for_injection(tmp_path):
    import fsu_seed_runner as R
    binary = tmp_path / "bin"
    binary.write_text("#!/bin/sh\n", encoding="utf-8")
    outdir = tmp_path / "inject"
    manifest = {
        "run_id": "FSU-X-F0-W5",
        "workload": {"binary": str(binary),
                     "element_oracle": {"golden_array": "g.bin"}},
        "injector": {"fpu_mode": {}, "max_faults": 1},
    }
    inj = R.build_cmd(manifest, outdir, 7, 0, False,
                      tmp_path / "gem5", tmp_path / "cfg.py", tmp_path)
    assert any(t.startswith("--cmd_arg=") for t in inj)
    assert f"--array-dump={outdir / 'array.bin'}" in " ".join(inj)
    census = R.build_cmd(manifest, tmp_path / "census", 7, None, True,
                         tmp_path / "gem5", tmp_path / "cfg.py", tmp_path)
    assert "--cmd_arg" not in census


def test_suite_audit_detects_broken_component(tmp_path):
    suite_path, suite, gem5, goldens = make_suite(tmp_path)
    res = run(tmp_path, suite_path, gem5, fake_runner(suite, goldens))
    seed_dir = Path(res["suite_seed_dir"])
    assert A.audit_suite(seed_dir)["ok"] is True
    cm = next(seed_dir.rglob("component_manifest.json"))
    cm.unlink()
    audit = A.audit_suite(seed_dir)
    assert audit["ok"] is False


# ---------- F5: pre-registered seed_plan drives every component ----------

F5_PLAN = [
    {"suite_seed": 1, "submodel": "FP06-a",
     "precision": "fp32", "lane_width": 32, "lane_offset": 0,
     "mask": "0x80000000", "polarity": 0, "warmup": 1024,
     "sample": {"limit": 1024, "keep_first_last_n": 256},
     "op_classes": [], "reg_class": "any", "decode_guard": True,
     "permanent_stuck": True},
    {"suite_seed": 2, "submodel": "FP06-b",
     "precision": "fp32", "lane_width": 32, "lane_offset": 0,
     "mask": "0x80000000", "polarity": 1, "warmup": 1024,
     "sample": {"limit": 1024, "keep_first_last_n": 256},
     "op_classes": [], "reg_class": "any", "decode_guard": True,
     "permanent_stuck": True},
    {"suite_seed": 3, "submodel": "FP06-c", "precision": "fp32",
     "lane_width": 32, "lane_offset": 0, "mask": "0x007f8000",
     "polarity": 0, "warmup": 1024,
     "sample": {"limit": 1024, "keep_first_last_n": 256},
     "op_classes": [], "reg_class": "any", "decode_guard": True,
     "permanent_stuck": True},
]


def make_f5_suite(tmp_path):
    path, suite, gem5, goldens = make_suite(tmp_path)
    suite["run_defaults"].update(
        {"model_id": "FP06", "freq": "F5", "load_id": "W5",
         "submodel": "FP06-a"})
    suite["injector"] = {
        "component": "fsu", "max_faults": 1, "first_clock": 0,
        "fpu_mode": {
            "precision": "fp32", "lane_width": 32, "lane_offset": 0,
            "decode_guard": True, "permanent_stuck": True,
            "f5_warmup": 1024, "f5_sample_limit": 1024,
            "f5_keep_first_last_n": 256,
            "op_classes": [], "reg_class": "any",
        },
    }
    suite["seed_plan"] = json.loads(json.dumps(F5_PLAN))
    suite["suite_hash"] = S.compute_suite_hash(suite)
    path.write_text(json.dumps(suite, ensure_ascii=False, indent=2),
                    encoding="utf-8")
    return path, suite, gem5, goldens


def recording_failure_runner(calls):
    def runner(cmd, timeout):
        calls.append(list(cmd))
        return 0, "", "", False  # no census log -> attempt fails, manifest stays
    return runner


def test_f5_seed_plan_overrides_fpu_mode_and_mask(tmp_path):
    suite_path, suite, gem5, goldens = make_f5_suite(tmp_path)
    calls = []
    for seed in (1, 2, 3):
        res = run(tmp_path, suite_path, gem5,
                  recording_failure_runner(calls), seed=seed)
        assert res["status"] == "failed"  # fake runner provides no census
    assert len(calls) == 3 * S.PROGRAM_COUNT

    by_seed = {1: (0, "FP06-a", "0x80000000", 0),
               2: (1, "FP06-b", "0x80000000", 1),
               3: (0, "FP06-c", "0x007f8000", 0)}
    for seed, (polarity, submodel, mask, want_pol) in by_seed.items():
        assert polarity == want_pol
        seed_dir = tmp_path / "runs" / RID / f"seed{seed}"
        attempts = sorted(seed_dir.glob("components/*/*/seed*/attempt-1"))
        assert len(attempts) == S.PROGRAM_COUNT
        masks = set()
        subs = set()
        for attempt in attempts:
            m = json.loads((attempt / "manifest.json").read_text(
                encoding="utf-8"))
            fpu = m["injector"]["fpu_mode"]
            assert m["freq"] == "F5"
            assert m["model_id"] == "FP06"
            assert m["load_id"] == "W5"
            assert m["submodel"] == submodel
            assert m["injector"]["fault_mask"] == mask
            assert fpu["precision"] == "fp32"
            assert fpu["lane_width"] == 32
            assert fpu["lane_offset"] == 0
            assert fpu["permanent_stuck"] is True
            assert fpu["stuck_polarity"] == want_pol
            assert fpu["decode_guard"] is True
            assert fpu["f5_warmup"] == 1024
            assert fpu["f5_sample_limit"] == 1024
            assert fpu["f5_keep_first_last_n"] == 256
            assert fpu["op_classes"] == []
            assert fpu["reg_class"] == "any"
            # permanentStuck forbids bitseg in CHAOSFPU; the fixed mask
            # owns the target for every F5 seed.
            assert "bitseg" not in fpu
            assert m["seed_plan_entry"] == S.seed_plan_identity(
                S.seed_plan_entry(suite, seed))
            masks.add(m["injector"]["fault_mask"])
            subs.add(m["submodel"])
        assert masks == {mask}
        assert subs == {submodel}


def test_f5_suite_without_seed_plan_refused_before_running(tmp_path):
    path, suite, gem5, goldens = make_f5_suite(tmp_path)
    bad = json.loads(path.read_text(encoding="utf-8"))
    del bad["seed_plan"]
    bad["suite_hash"] = S.compute_suite_hash(bad)
    path.write_text(json.dumps(bad), encoding="utf-8")
    calls = []
    with pytest.raises(S.SuiteError, match="must pre-register a seed_plan"):
        run(tmp_path, path, gem5, fake_runner(suite, goldens, calls=calls))
    assert calls == []
    assert not (tmp_path / "runs" / RID / "seed1").exists()


def test_f5_suite_requires_permanent_stuck_injector(tmp_path):
    path, suite, gem5, goldens = make_f5_suite(tmp_path)
    bad = json.loads(path.read_text(encoding="utf-8"))
    bad["injector"]["fpu_mode"]["permanent_stuck"] = False
    bad["suite_hash"] = S.compute_suite_hash(bad)
    path.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(S.SuiteError, match="permanent_stuck"):
        run(tmp_path, path, gem5, fake_runner(suite, goldens))


def test_f5_unknown_suite_seed_refused(tmp_path):
    suite_path, suite, gem5, goldens = make_f5_suite(tmp_path)
    calls = []
    with pytest.raises(S.SuiteError, match="not in the pre-registered"):
        run(tmp_path, suite_path, gem5,
            fake_runner(suite, goldens, calls=calls), seed=4)
    assert calls == []
    assert not list((tmp_path / "runs" / RID / "seed4").glob("components/*"))


def test_f5_disk_binary_identity_mismatch_refused(tmp_path):
    path, suite, gem5, goldens = make_f5_suite(tmp_path)
    bad = json.loads(path.read_text(encoding="utf-8"))
    bad["programs"][0]["binary_sha256"] = "a" * 64
    bad["suite_hash"] = S.compute_suite_hash(bad)
    path.write_text(json.dumps(bad), encoding="utf-8")
    calls = []
    with pytest.raises(S.SuiteError, match="binary SHA drift"):
        run(tmp_path, path, gem5, fake_runner(suite, goldens, calls=calls))
    assert calls == []
    assert not (tmp_path / "runs" / RID / "seed1").exists()


# ---------- W6 program_overrides in component manifests ----------

def test_f0_program_overrides_reach_component_manifest(tmp_path):
    path, suite, gem5, goldens = make_suite(tmp_path)
    suite["program_overrides"] = {
        "gemm": {"fpu_mode": {"precision": "fp64", "lane_width": 64,
                              "lane_offset": 0},
                 "fault_mask": "0x8000000000000000"},
        "2mm": {"fpu_mode": {"precision": "fp32", "lane_width": 32,
                             "lane_offset": 0}},
    }
    suite["suite_hash"] = S.compute_suite_hash(suite)
    path.write_text(json.dumps(suite, ensure_ascii=False, indent=2),
                    encoding="utf-8")
    calls = []
    res = run(tmp_path, path, gem5, recording_failure_runner(calls))
    assert res["status"] == "failed"  # fake runner has no census
    root = tmp_path / "runs" / RID / "seed1"
    for pid, precision, lane, mask in (
            ("gemm", "fp64", 64, "0x8000000000000000"),
            ("2mm", "fp32", 32, None)):
        attempt = next(root.glob(f"components/{pid}/*/seed*/attempt-1"))
        m = json.loads((attempt / "manifest.json").read_text(
            encoding="utf-8"))
        assert m["injector"]["fpu_mode"]["precision"] == precision
        assert m["injector"]["fpu_mode"]["lane_width"] == lane
        assert m["effective_injector"] == m["injector"]
        assert m["program_override"] == S.program_override_identity(
            S.normalise_program_overrides(suite)[pid])
        if mask:
            assert m["injector"]["fault_mask"] == mask
        else:
            assert "fault_mask" not in m["injector"]
    # Programs without an override keep the suite base injector.
    att = next(root.glob("components/lu/*/seed*/attempt-1"))
    m = json.loads((att / "manifest.json").read_text(encoding="utf-8"))
    assert m["program_override"] is None
    # No override: the resolver materialises the fp32/lane32 defaults.
    assert m["injector"]["fpu_mode"]["precision"] == "fp32"
    assert m["injector"]["fpu_mode"]["lane_width"] == 32


def test_f5_seed_plan_geometry_wins_over_program_override(tmp_path):
    path, suite, gem5, goldens = make_f5_suite(tmp_path)
    suite["program_overrides"] = {
        "gemm": {"fpu_mode": {"precision": "fp64", "lane_width": 64}}}
    suite["suite_hash"] = S.compute_suite_hash(suite)
    path.write_text(json.dumps(suite, ensure_ascii=False, indent=2),
                    encoding="utf-8")
    calls = []
    run(tmp_path, path, gem5, recording_failure_runner(calls), seed=1)
    root = tmp_path / "runs" / RID / "seed1"
    attempt = next(root.glob("components/gemm/*/seed*/attempt-1"))
    m = json.loads((attempt / "manifest.json").read_text(encoding="utf-8"))
    # The W5 seed_plan declares fp32 and is applied last.
    assert m["injector"]["fpu_mode"]["precision"] == "fp32"
    assert m["injector"]["fpu_mode"]["lane_width"] == 32
    # The override is still recorded as the applied per-program override.
    assert m["program_override"]["fpu_mode"]["precision"] == "fp64"
