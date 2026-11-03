"""tests/test_fsu_w6_gate.py — W6 gate command preparation/verification.

No gem5 is executed. Covers:
  * --print-commands per-program precision/lane/mask for F0 and F5;
  * SVD is fp64 / lane 64 with 64-bit masks, FFT/sparse-CG are fp32 / lane 32;
  * 3/3 components with independent audit + element oracle certify a gate
    seed; one broken component -> FAIL (2/3);
  * the gate refuses runs/fsu and never counts components as seeds.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import fsu_suite as S  # noqa: E402
import fsu_w6_gate as G  # noqa: E402
import fsu_w6_suite as WS  # noqa: E402

SUITE_F0 = ROOT / "configs/fsu/suites/w6-fp-v1.json"
SUITE_F5 = ROOT / "configs/fsu/suites/w6-fp-v1-f5.json"
GATE_F0 = "FSU-FP04-F0-W6-GATE"
GATE_F5 = "FSU-FP06-F5-W6-GATE"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_print_commands_f0_per_program_precision(tmp_path, capsys):
    outdir = tmp_path / "runs/fsu-gates/W6-F0-GATE"
    rc = G.run_gate(SUITE_F0, outdir, ROOT / "nope", ROOT / "nope", tmp_path,
                    print_only=True, suite_seed=1)
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["freq"] == "F0"
    assert data["gate_id"] == GATE_F0
    assert len(data["seeds"]) == 1
    seed = data["seeds"][0]
    assert seed["suite_seed"] == 1
    assert [c["program_id"] for c in seed["commands"]] == list(
        WS.W6_PROGRAM_ORDER)
    expect = {"svd": ("fp64", 64), "fft": ("fp32", 32),
              "sparse-cg": ("fp32", 32)}
    for cmd in seed["commands"]:
        precision, lane = expect[cmd["program_id"]]
        assert cmd["precision"] == precision
        assert cmd["lane_width"] == lane
        assert cmd["bitseg"] == "sign"
        assert cmd["fault_mask"] is None
        inject = cmd["inject"]
        assert inject[inject.index("--fpu_precision") + 1] == precision
        assert inject[inject.index("--fpu_lane_width") + 1] == str(lane)
        assert "--fpu_permanent_stuck" not in inject
        assert cmd["submodel"] == "FP04-W6"
    # Nothing was executed.
    assert not outdir.exists()


def test_print_commands_f5_per_program_masks(tmp_path, capsys):
    outdir = tmp_path / "runs/fsu-gates/W6-F5-GATE"
    rc = G.run_gate(SUITE_F5, outdir, ROOT / "nope", ROOT / "nope", tmp_path,
                    print_only=True, suite_seed=1, all_seeds=True)
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["freq"] == "F5" and data["gate_id"] == GATE_F5
    seeds = {s["suite_seed"]: s for s in data["seeds"]}
    assert sorted(seeds) == [1, 2, 3]

    expected = {
        1: {"svd": ("0x8000000000000000", 0),
            "fft": ("0x80000000", 0), "sparse-cg": ("0x80000000", 0)},
        2: {"svd": ("0x8000000000000000", 1),
            "fft": ("0x80000000", 1), "sparse-cg": ("0x80000000", 1)},
        3: {"svd": ("0x0007f80000000000", 0),
            "fft": ("0x007f8000", 0), "sparse-cg": ("0x007f8000", 0)},
    }
    for seed_no, seed in seeds.items():
        for cmd in seed["commands"]:
            mask, pol = expected[seed_no][cmd["program_id"]]
            assert cmd["fault_mask"] == mask
            assert cmd["stuck_polarity"] == pol
            inject = cmd["inject"]
            assert "--fpu_permanent_stuck" in inject
            assert inject[inject.index("--fpu_stuck_polarity") + 1] == str(pol)
            assert inject[inject.index("--fpu_f5_warmup") + 1] == "1024"
            assert inject[inject.index("--fpu_f5_sample_limit") + 1] == "1024"
            assert inject[inject.index("--fpu_f5_keep_first_last_n") + 1] == \
                "256"
            # permanentStuck forbids bitseg in CHAOSFPU.
            assert cmd["bitseg"] is None
            assert "--fpu_bitseg" not in inject
            if cmd["program_id"] == "svd":
                assert cmd["precision"] == "fp64"
                assert cmd["lane_width"] == 64
            else:
                assert cmd["precision"] == "fp32"
                assert cmd["lane_width"] == 32
    assert not outdir.exists()


def fabricate(seed_dir, suite, plan_entry, program, seed, gate_id,
              broken=False):
    policy = WS.DEFAULT_COMPONENT_SEED_POLICY
    cseed = WS.derive_component_seed(seed, program["program_id"], policy,
                                     suite["suite_id"],
                                     suite["suite_version"])
    attempt = (Path(seed_dir) / "components" / program["program_id"] /
               gate_id / f"seed{cseed}" / "attempt-1")
    (attempt / "inject").mkdir(parents=True)
    injector = WS.resolved_injector(suite, program["program_id"], plan_entry)
    overrides = S.normalise_program_overrides(suite) or {}
    defaults = suite["run_defaults"]
    manifest = {
        "run_id": gate_id,
        "model_id": defaults["model_id"],
        "unit": defaults["unit"],
        "freq": defaults["freq"],
        "load_id": defaults["load_id"],
        "submodel": (plan_entry["submodel"] if plan_entry
                     else defaults["submodel"]),
        "workload": {"binary": program["binary"]},
        "injector": injector,
        "effective_injector": injector,
        "program_override": S.program_override_identity(
            overrides.get(program["program_id"])),
    }
    if plan_entry is not None:
        manifest["seed_plan_entry"] = S.seed_plan_identity(plan_entry)
    (attempt / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    cm = {
        "suite_id": suite["suite_id"],
        "suite_version": suite["suite_version"],
        "suite_hash": WS.compute_suite_hash(suite),
        "suite_seed": seed,
        "program_id": program["program_id"],
        "program_index": program["program_index"],
        "program_count": WS.W6_PROGRAM_COUNT,
        "component_seed_policy_version": policy,
        "component_seed": cseed,
        "component_attempt": 1,
        "component_manifest_sha256": G.sha256_file(attempt / "manifest.json"),
        "component_binary_sha256": program["binary_sha256"],
        "component_source_sha256": program["source_sha256"],
        "component_golden_sha256": program["golden_array_sha256"],
        "component_status": "admitted" if not broken else "failed",
        "component_eligible": 100,
        "component_activated": 1,
        "component_faults": 1,
        "component_terminal": "committed",
        "component_oracle": "MASKED",
        "component_audit_ok": not broken,
        "component_certified": not broken,
        "program_override": S.program_override_identity(
            overrides.get(program["program_id"])),
        "effective_injector": injector,
    }
    if plan_entry is not None:
        cm["seed_plan_entry"] = S.seed_plan_identity(plan_entry)
    (attempt / "component_manifest.json").write_text(
        json.dumps(cm, ensure_ascii=False, indent=2), encoding="utf-8")
    (attempt / "audit.json").write_text(
        json.dumps({"ok": not broken, "certified": not broken}),
        encoding="utf-8")
    (attempt / "oracle_elements.json").write_text(
        json.dumps({"ok": True, "program_id": program["program_id"],
                    "mismatch_count": 0, "category": "EXACT_MATCH"}),
        encoding="utf-8")
    golden = ROOT / program["element_oracle"]["golden_array"]
    (attempt / "inject/array.bin").write_bytes(golden.read_bytes())
    hashes = {
        "oracle_elements.json": G.sha256_file(
            attempt / "oracle_elements.json"),
        "inject/array.bin": G.sha256_file(attempt / "inject/array.bin"),
    }
    (attempt / "evidence_sha256.json").write_text(
        json.dumps(hashes), encoding="utf-8")
    return attempt


def test_verify_only_3_of_3_pass(tmp_path):
    suite = load(SUITE_F0)
    info = WS.validate_suite_manifest(suite, require_hashes=True,
                                      require_suite_hash=True)
    outdir = tmp_path / "runs/fsu-gates/W6-F0-GATE"
    seed_dir = outdir / "seed1"
    for program in suite["programs"]:
        fabricate(seed_dir, suite, None, program, 1, GATE_F0)
    report = G.run_gate(SUITE_F0, outdir, ROOT / "nope", ROOT / "nope",
                        tmp_path, suite_seed=1, verify_only=True)
    assert report["ok"] is True, report["records"]
    assert report["component_pass_count"] == 3
    assert report["component_run_count"] == 3
    assert report["non_formal"] is True
    assert report["counts_toward_519"] is False
    assert report["formal_suite_seed_count"] == 0
    assert info["suite_hash"] == report["suite_hash"]
    assert (outdir / "gate_report.json").exists()
    assert (outdir / "GATE.md").exists()
    assert (outdir / "SHA256SUMS").exists()


def test_verify_only_one_broken_component_fails(tmp_path):
    suite = load(SUITE_F0)
    outdir = tmp_path / "runs/fsu-gates/W6-F0-GATE"
    seed_dir = outdir / "seed1"
    for program in suite["programs"]:
        fabricate(seed_dir, suite, None, program, 1, GATE_F0,
                  broken=program["program_id"] == "fft")
    report = G.run_gate(SUITE_F0, outdir, ROOT / "nope", ROOT / "nope",
                        tmp_path, suite_seed=1, verify_only=True)
    assert report["ok"] is False
    assert report["component_pass_count"] == 2
    fft = next(r for r in report["records"] if r["program_id"] == "fft")
    assert fft["status"] == "FAIL"
    assert any("audit.ok" in f for f in fft["failures"])


def test_verify_only_f5_per_program_mask_identity(tmp_path):
    suite = load(SUITE_F5)
    plan = S.seed_plan_entry(suite, 2)
    outdir = tmp_path / "runs/fsu-gates/W6-F5-GATE"
    seed_dir = outdir / "seed2"
    for program in suite["programs"]:
        fabricate(seed_dir, suite, plan, program, 2, GATE_F5)
    report = G.run_gate(SUITE_F5, outdir, ROOT / "nope", ROOT / "nope",
                        tmp_path, suite_seed=2, verify_only=True)
    assert report["ok"] is True, report["records"]
    assert report["seed_plan_entry"]["submodel"] == "FP06-b"
    svd = next(r for r in report["records"] if r["program_id"] == "svd")
    assert svd["checks"]
    assert all(c["ok"] for c in svd["checks"])


def test_gate_refuses_runs_fsu(tmp_path):
    with pytest.raises(WS.W6SuiteError, match="must live under"):
        G.run_gate(SUITE_F0, tmp_path / "runs/fsu/EVIL", ROOT / "nope",
                   ROOT / "nope", tmp_path, verify_only=True)
