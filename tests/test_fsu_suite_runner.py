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
        dump = next((t.split("=", 1)[1] for t in cmd
                     if t.startswith("--array-dump=")), None)
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
    assert "--cmd_arg" in inj
    assert f"--array-dump={outdir / 'array.bin'}" in inj
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
