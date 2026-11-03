"""tests/test_fsu_suite_f5_gate.py — FP06-F5-W5 gate logic (no real gem5).

Covers:
  * --print-commands emits five component commands driven by the SAME
    pre-registered seed_plan entry (suite seed 1), without executing gem5;
  * --verify-only accepts 5/5 admitted components only;
  * one broken component turns the gate into FAIL (4/5);
  * gate evidence may not be written under runs/fsu.
"""
import hashlib
import json
import struct
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import fsu_suite as S  # noqa: E402
import fsu_suite_f5_gate as G  # noqa: E402
import fsu_suite_runner as SR  # noqa: E402

RID = "FSU-TEST-F0-W5"
GATE_ID = "FSU-TEST-F5-W5-GATE"

PLAN = [
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
    root = tmp_path
    (root / "src").mkdir()
    (root / "bin").mkdir()
    golden_dir = root / "golden"
    golden_dir.mkdir()
    programs = []
    for i, pid in enumerate(S.PROGRAM_ORDER):
        src = root / "src" / f"{pid}.c"
        src.write_text(f"/* {pid} */\nint main(void){{return 0;}}\n",
                       encoding="utf-8")
        binary = root / "bin" / pid
        binary.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        binary.chmod(0o755)
        golden = golden_dir / f"{pid}.bin"
        golden.write_bytes(struct.pack("<2f", float(i + 1), float(i + 2)))
        programs.append({
            "program_id": pid,
            "program_index": i,
            "source": str(src),
            "source_sha256": S.sha256_file(src),
            "binary": str(binary),
            "binary_sha256": S.sha256_file(binary),
            "scale": {"N": 8 + i},
            "golden": f"{i + 1:016x}",
            "golden_array_sha256": S.sha256_file(golden),
            "element_oracle": {
                "golden_array": str(golden),
                "oracle_version": "polybench-element-v1",
                "meta": {
                    "program_id": pid, "golden_id": f"test-{pid}-golden-v1",
                    "dtype": "fp32", "layout": "row-major",
                    "endianness": "little", "count": 2, "shape": [2, 1],
                    "abs_tol": 0.0, "rel_tol": 0.0, "ulp_tol": 0,
                    "oracle_version": "polybench-element-v1",
                },
            },
        })
    suite = {
        "suite_id": "test-polybench-fp-v1-f5",
        "suite_version": "1",
        "program_order": list(S.PROGRAM_ORDER),
        "program_count": 5,
        "run_defaults": {
            "model_id": "FP06", "unit": "FSU Pipe", "freq": "F5",
            "load_id": "W5", "submodel": "FP06-a",
            "config_family": "C3", "config_profile": "B0",
            "limits": {"timeout_s": 10},
        },
        "injector": {
            "component": "fsu", "max_faults": 1, "first_clock": 0,
            "fpu_mode": {
                "precision": "fp32", "lane_width": 32, "lane_offset": 0,
                "decode_guard": True, "permanent_stuck": True,
                "f5_warmup": 1024, "f5_sample_limit": 1024,
                "f5_keep_first_last_n": 256,
                "op_classes": [], "reg_class": "any",
            },
        },
        "compiler": {"cc": "gcc", "version": "test-gcc",
                     "cflags": ["-O2", "-static"]},
        "oracle": {"id": "polybench-element-v1",
                   "version": "polybench-element-v1", "kind": "exact_hash"},
        "seed_plan": json.loads(json.dumps(PLAN)),
        "programs": programs,
    }
    suite["suite_hash"] = S.compute_suite_hash(suite)
    path = root / "suite.json"
    path.write_text(json.dumps(suite, ensure_ascii=False, indent=2),
                    encoding="utf-8")
    gem5 = root / "fake_gem5"
    gem5.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    gem5.chmod(0o755)
    config = root / "cfg.py"
    config.write_text("# fake\n", encoding="utf-8")
    return path, suite, gem5, config


def fabricate_attempt(seed_dir, suite, plan_entry, program, broken=False):
    policy = S.DEFAULT_COMPONENT_SEED_POLICY
    cseed = S.derive_component_seed(
        1, program["program_id"], policy, suite["suite_id"],
        suite["suite_version"])
    attempt = (Path(seed_dir) / "components" / program["program_id"] /
               GATE_ID / f"seed{cseed}" / "attempt-1")
    (attempt / "inject").mkdir(parents=True)
    fpu = {
        "precision": plan_entry["precision"],
        "lane_width": plan_entry["lane_width"],
        "lane_offset": plan_entry["lane_offset"],
        "decode_guard": plan_entry["decode_guard"],
        "permanent_stuck": True,
        "stuck_polarity": plan_entry["polarity"],
        "f5_warmup": plan_entry["warmup"],
        "f5_sample_limit": plan_entry["sample"]["limit"],
        "f5_keep_first_last_n": plan_entry["sample"]["keep_first_last_n"],
        "op_classes": list(plan_entry["op_classes"]),
        "reg_class": plan_entry["reg_class"],
    }
    if "bitseg" in plan_entry:
        fpu["bitseg"] = plan_entry["bitseg"]
    manifest = {
        "run_id": GATE_ID,
        "model_id": "FP06", "unit": "FSU Pipe", "freq": "F5",
        "load_id": "W5", "submodel": plan_entry["submodel"],
        "workload": {"binary": program["binary"]},
        "injector": {"component": "fsu", "max_faults": 1,
                     "first_clock": 0, "fault_mask": plan_entry["mask"],
                     "fpu_mode": fpu},
        "seed_plan_entry": S.seed_plan_identity(plan_entry),
    }
    (attempt / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    golden_sha, _ = S.component_golden_sha256(program)
    cm = {
        "suite_id": suite["suite_id"],
        "suite_version": suite["suite_version"],
        "suite_hash": S.compute_suite_hash(suite),
        "suite_seed": 1,
        "program_id": program["program_id"],
        "program_index": program["program_index"],
        "program_count": S.PROGRAM_COUNT,
        "component_seed_policy_version": policy,
        "component_seed": cseed,
        "component_attempt": 1,
        "component_manifest_sha256": S.sha256_file(attempt / "manifest.json"),
        "component_binary_sha256": program["binary_sha256"],
        "component_source_sha256": program["source_sha256"],
        "component_golden_sha256": golden_sha,
        "component_status": "admitted" if not broken else "failed",
        "component_eligible": 100,
        "component_activated": 1,
        "component_faults": 1,
        "component_terminal": "committed",
        "component_oracle": "MASKED",
        "component_audit_ok": not broken,
        "component_certified": not broken,
        "seed_plan_entry": S.seed_plan_identity(plan_entry),
    }
    (attempt / "component_manifest.json").write_text(
        json.dumps(cm, ensure_ascii=False, indent=2), encoding="utf-8")
    (attempt / "audit.json").write_text(
        json.dumps({"ok": not broken, "certified": not broken}),
        encoding="utf-8")
    (attempt / "oracle_elements.json").write_text(
        json.dumps({"ok": True, "program_id": program["program_id"],
                    "mismatch_count": 0, "category": "EXACT_MATCH"}),
        encoding="utf-8")
    (attempt / "inject/array.bin").write_bytes(struct.pack("<2f", 1.0, 2.0))
    hashes = {
        "oracle_elements.json": S.sha256_file(
            attempt / "oracle_elements.json"),
        "inject/array.bin": S.sha256_file(attempt / "inject/array.bin"),
    }
    (attempt / "evidence_sha256.json").write_text(
        json.dumps(hashes), encoding="utf-8")
    return attempt


def test_gate_verify_only_passes_5_of_5(tmp_path):
    path, suite, gem5, config = make_f5_suite(tmp_path)
    outdir = tmp_path / "runs/fsu-gates/F5-GATE"
    seed_dir = outdir / "gate-seed1"
    entry = S.seed_plan_entry(suite, 1)
    for program in suite["programs"]:
        fabricate_attempt(seed_dir, suite, entry, program)
    report = G.run_gate(path, outdir, gem5, config, tmp_path, verify_only=True,
                        gate_id=GATE_ID)
    assert report["ok"] is True, report["records"]
    assert report["component_pass_count"] == 5
    assert report["non_formal"] is True
    assert report["counts_toward_519"] is False
    assert report["formal_suite_seed_count"] == 0
    assert (outdir / "gate_report.json").exists()
    assert (outdir / "GATE.md").exists()
    assert (outdir / "SHA256SUMS").exists()
    assert [r["program_id"] for r in report["records"]] == list(
        S.PROGRAM_ORDER)


def test_gate_verify_only_fails_on_one_broken_component(tmp_path):
    path, suite, gem5, config = make_f5_suite(tmp_path)
    outdir = tmp_path / "runs/fsu-gates/F5-GATE"
    seed_dir = outdir / "gate-seed1"
    entry = S.seed_plan_entry(suite, 1)
    for program in suite["programs"]:
        fabricate_attempt(seed_dir, suite, entry, program,
                          broken=program["program_id"] == "lu")
    report = G.run_gate(path, outdir, gem5, config, tmp_path, verify_only=True,
                        gate_id=GATE_ID)
    assert report["ok"] is False
    assert report["component_pass_count"] == 4
    lu = next(r for r in report["records"] if r["program_id"] == "lu")
    assert lu["status"] == "FAIL"
    assert any("audit.ok" in f for f in lu["failures"])


def test_gate_refuses_runs_fsu_outdir(tmp_path):
    path, suite, gem5, config = make_f5_suite(tmp_path)
    with pytest.raises(S.SuiteError, match="must live under"):
        G.run_gate(path, tmp_path / "runs/fsu/EVIL", gem5, config, tmp_path,
                   verify_only=True, gate_id=GATE_ID)


def test_gate_print_commands_uses_seed_plan_one(tmp_path, capsys):
    path, suite, gem5, config = make_f5_suite(tmp_path)
    outdir = tmp_path / "runs/fsu-gates/F5-GATE"
    rc = G.run_gate(path, outdir, gem5, config, tmp_path, print_only=True,
                    gate_id=GATE_ID)
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["seed_plan"]["submodel"] == "FP06-a"
    assert data["seed_plan"]["mask"] == "0x80000000"
    assert data["seed_plan"]["polarity"] == 0
    assert [c["program_id"] for c in data["commands"]] == list(S.PROGRAM_ORDER)
    mask_dec = int("0x80000000", 0)
    for cmd in data["commands"]:
        inject = cmd["inject"]
        assert "--fpu_permanent_stuck" in inject
        assert inject[inject.index("--fpu_fault_mask") + 1] == str(mask_dec)
        assert inject[inject.index("--fpu_stuck_polarity") + 1] == "0"
        assert inject[inject.index("--fpu_f5_warmup") + 1] == "1024"
        assert inject[inject.index("--fpu_f5_sample_limit") + 1] == "1024"
        assert inject[inject.index("--fpu_f5_keep_first_last_n") + 1] == "256"
        assert "--fpu_op_classes" not in inject
        assert "--fpu_reg_class" not in inject
        assert cmd["submodel"] == "FP06-a"
    # Nothing was executed and no formal seed tree was created.
    assert not (tmp_path / "runs/fsu").exists()
