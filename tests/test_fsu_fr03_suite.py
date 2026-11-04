"""tests/test_fsu_fr03_suite.py — FR03-F5-W5/W6 suite readiness and gate.

No gem5 is executed and nothing is written under runs/.  Covers:

  * fixed program order and suite_hash for both FR03 suites;
  * suite_hash covers every per-program physical target and every seed's
    fault mask / polarity / lane, plus the FR03 run_defaults identity;
  * deterministic target selection, exclusion of the special 32..43 Vec
    slots and of >= numPhysVecRegs, and requireAllocated=true;
  * fixed mask/polarity/fault_type per seed, lane-fit for every program
    (SVD fp64 lane 64 vs FFT/sparse-CG fp32 lane 32);
  * component seeds are deterministic and unique, and components never
    count as formal seeds;
  * gate 5/5 (W5) and 3/3 (W6) PASS, 4/5 FAIL logic;
  * the gate refuses to write runs/fsu and only writes runs/fsu-gates;
  * --print-commands emits the CHAOSPhysReg route (no CHAOSFPU flags);
  * the real FR03 W3 gate evidence still passes fr03_gate_assert and the
    planned-target checks (skipped if the evidence is absent).
"""
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import fsu_fr03_suite_gate as G  # noqa: E402
import fsu_suite as S  # noqa: E402

SUITE_W5 = ROOT / "configs/fsu/suites/polybench-fp-v1-fr03.json"
SUITE_W6 = ROOT / "configs/fsu/suites/w6-fp-v1-fr03.json"
HASH_W5 = "98d88154edeac9992aa73e103cf76d835510cccf03c130c8590d208804a64d17"
HASH_W6 = "3b946a51ffb67e2086ed6df32395e90cd54c2d7dcf791654fb5e0312e61c172e"
REAL_W3 = (ROOT / "runs/fsu-gates/F5-FR03-W3-GATE-v3/FSU-FR03-F5-W3-GATE/"
           "seed1/attempt-1")


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def suite_copy(path):
    return json.loads(json.dumps(load(path)))


# ---------------------------------------------------------------------------
# Identity / order / hash
# ---------------------------------------------------------------------------
def test_w5_order_and_hash():
    suite = load(SUITE_W5)
    info = G.validate_suite_manifest(suite, require_hashes=True,
                                     require_suite_hash=True)
    assert info["suite_hash"] == HASH_W5
    assert tuple(suite["program_order"]) == (
        "gemm", "2mm", "lu", "cholesky", "jacobi-2d")
    assert suite["program_count"] == 5
    assert suite["run_defaults"] == {
        "model_id": "FR03", "unit": "FSU Pipe", "freq": "F5",
        "load_id": "W5", "config_family": "C3", "config_profile": "B0",
        "limits": {"timeout_s": 3600}}
    assert suite["injector"]["component"] == "physreg"


def test_w6_order_and_hash():
    suite = load(SUITE_W6)
    info = G.validate_suite_manifest(suite, require_hashes=True,
                                     require_suite_hash=True)
    assert info["suite_hash"] == HASH_W6
    assert tuple(suite["program_order"]) == ("svd", "fft", "sparse-cg")
    assert suite["program_count"] == 3
    assert suite["run_defaults"]["model_id"] == "FR03"
    assert suite["run_defaults"]["load_id"] == "W6"
    assert suite["run_defaults"]["limits"]["timeout_s"] == 3600


def test_suite_hash_covers_targets_masks_and_polarity():
    base = load(SUITE_W5)
    base_hash = G.compute_suite_hash(base)

    target = suite_copy(SUITE_W5)
    target["target_plan"]["gemm"]["target_phys_idx"] = 1
    assert G.compute_suite_hash(target) != base_hash

    mask = suite_copy(SUITE_W5)
    mask["seed_plan"][1]["fault_mask"] = "0x00000010"
    assert G.compute_suite_hash(mask) != base_hash

    pol = suite_copy(SUITE_W5)
    pol["seed_plan"][2]["polarity"] = 0
    pol["seed_plan"][2]["fault_type"] = "stuck_at_zero"
    assert G.compute_suite_hash(pol) != base_hash

    lane = suite_copy(SUITE_W5)
    lane["seed_plan"][0]["vec_lane_offset"] = 3
    assert G.compute_suite_hash(lane) != base_hash

    run_defaults = suite_copy(SUITE_W5)
    run_defaults["run_defaults"]["config_family"] = "C2"
    assert G.compute_suite_hash(run_defaults) != base_hash

    cflags = suite_copy(SUITE_W5)
    cflags["compiler"]["cflags"] = cflags["compiler"]["cflags"] + ["-g"]
    assert G.compute_suite_hash(cflags) != base_hash

    # The program load_id is fixed by the suite family; a drift is refused.
    wrong_load = suite_copy(SUITE_W5)
    wrong_load["run_defaults"]["load_id"] = "W6"
    with pytest.raises(G.FR03SuiteError, match="load_id"):
        G.compute_suite_hash(wrong_load)

    # The declared hash is the identity hash; no run result is in it.
    assert G.compute_suite_hash(load(SUITE_W5)) == HASH_W5


# ---------------------------------------------------------------------------
# Target plan
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("path", [SUITE_W5, SUITE_W6])
def test_target_plan_is_deterministic_and_excludes_reserved(path):
    suite = load(path)
    targets = G.normalise_target_plan(suite)
    for pid in G.program_order(G.family_of(suite)):
        values = {
            G.resolve_component_plan(suite, pid, seed)["target_phys_idx"]
            for seed in (1, 2, 3)
        }
        assert len(values) == 1, (pid, values)
        target = values.pop()
        assert target == targets[pid]["target_phys_idx"]
        assert target in G.ALLOWED_TARGETS
        assert target not in G.SPECIAL_VEC_SLOTS
        assert 0 <= target < G.NUM_PHYS_VEC_REGS
        # Determinism: repeated resolution is byte-identical.
        assert (G.resolve_component_plan(suite, pid, 1)
                == G.resolve_component_plan(suite, pid, 1))
    # The geometry constants are the C3/B0 north-star values.
    assert G.NUM_PHYS_VEC_REGS == 48
    assert G.VEC_ARCH_REGS == 44
    assert G.SPECIAL_VEC_SLOTS == tuple(range(32, 44))
    assert G.DYNAMIC_POOL == (44, 45, 46, 47)


def test_rejects_special_and_out_of_range_targets():
    for bad in (32, 40, 43, 48, 100):
        suite = suite_copy(SUITE_W5)
        suite["target_plan"]["gemm"]["target_phys_idx"] = bad
        with pytest.raises(G.FR03SuiteError):
            G.compute_suite_hash(suite)


def test_rejects_fpu_or_non_phys_injector():
    fpu = suite_copy(SUITE_W5)
    fpu["injector"]["component"] = "fsu"
    with pytest.raises(G.FR03SuiteError, match="component == 'physreg'"):
        G.compute_suite_hash(fpu)

    noalloc = suite_copy(SUITE_W5)
    noalloc["injector"]["physreg_mode"]["require_allocated"] = False
    with pytest.raises(G.FR03SuiteError, match="require_allocated"):
        G.compute_suite_hash(noalloc)

    mixing = suite_copy(SUITE_W5)
    mixing["injector"]["fpu_mode"] = {"precision": "fp32"}
    with pytest.raises(G.FR03SuiteError, match="fpu_mode is forbidden"):
        G.compute_suite_hash(mixing)


# ---------------------------------------------------------------------------
# Frozen seed plan / masks / polarity
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("path", [SUITE_W5, SUITE_W6])
def test_seed_masks_and_polarity_are_fixed_and_fit(path):
    suite = load(path)
    family = G.family_of(suite)
    plan = G.normalise_seed_plan(suite)
    assert [e["suite_seed"] for e in plan] == [1, 2, 3]
    assert [e["submodel"] for e in plan] == [
        "FR03-a", "FR03-b", "FR03-c"]
    masks = [(e["fault_mask_value"], e["vec_lane_offset"]) for e in plan]
    assert len(set(masks)) == 3
    for entry in plan:
        assert entry["polarity"] in (0, 1)
        assert entry["fault_type"] == (
            "stuck_at_one" if entry["polarity"] else "stuck_at_zero")
        for pid in G.program_order(family):
            plan_pid = G.resolve_component_plan(suite, pid,
                                                entry["suite_seed"])
            assert plan_pid["fault_mask"] == entry["program_mask"][pid]
            assert plan_pid["polarity"] == entry["polarity"]
            assert plan_pid["fault_type"] == entry["fault_type"]
            assert plan_pid["vec_lane_offset"] == entry["vec_lane_offset"]
            width = plan_pid["vec_lane_width"]
            assert 0 < plan_pid["fault_mask_value"] < (1 << width)
            assert entry["vec_lane_offset"] < 128 // width


def test_w6_per_program_lane_width():
    suite = load(SUITE_W6)
    assert G.resolve_component_plan(suite, "svd", 1)["precision"] == "fp64"
    assert G.resolve_component_plan(suite, "svd", 1)["vec_lane_width"] == 64
    for pid in ("fft", "sparse-cg"):
        plan = G.resolve_component_plan(suite, pid, 1)
        assert plan["precision"] == "fp32"
        assert plan["vec_lane_width"] == 32


def test_rejects_bad_masks_polarity_and_unknown_fields():
    zero = suite_copy(SUITE_W5)
    zero["seed_plan"][0]["fault_mask"] = "0x0"
    with pytest.raises(G.FR03SuiteError, match="non-zero mask"):
        G.compute_suite_hash(zero)

    mismatched = suite_copy(SUITE_W5)
    mismatched["seed_plan"][0]["fault_type"] = "stuck_at_one"
    with pytest.raises(G.FR03SuiteError, match="inconsistent"):
        G.compute_suite_hash(mismatched)

    unknown = suite_copy(SUITE_W5)
    unknown["seed_plan"][0]["sdc_hint"] = True
    with pytest.raises(G.FR03SuiteError, match="unknown field"):
        G.compute_suite_hash(unknown)


def test_component_seeds_deterministic_and_unique():
    for path in (SUITE_W5, SUITE_W6):
        suite = load(path)
        first = G.derive_component_seeds(suite, 1)
        second = G.derive_component_seeds(suite, 1)
        assert first == second
        assert len(set(first.values())) == len(first)
        assert all(v > 0 for v in first.values())
        assert G.derive_component_seeds(suite, 2) != first


def test_component_spec_matches_physreg_event_identity():
    """CHAOSPhysReg emits model_id=FR03, freq=F5, submodel=semanticRole and
    no load_id.  The component manifest must agree with that stream (the
    independent audit compares these fields), while the suite keeps W5/W6
    and the FR03-a/b/c seed label in explicit sibling fields."""
    for path, load_id in ((SUITE_W5, "W5"), (SUITE_W6, "W6")):
        suite = load(path)
        pid = G.program_order(G.family_of(suite))[0]
        program = next(p for p in suite["programs"]
                       if p["program_id"] == pid)
        cseed = G.derive_component_seed(suite, 1, pid)
        spec = G._component_spec(suite, program, 1, cseed, "GATE")
        assert spec["model_id"] == "FR03"
        assert spec["freq"] == "F5"
        assert spec["submodel"] == "FR03"
        assert spec["injector"]["physreg_mode"]["semantic_role"] == "FR03"
        assert "load_id" not in spec
        assert spec["suite_load_id"] == load_id
        assert spec["suite_seed_submodel"] == "FR03-a"
        assert spec["component"]["suite_family"] == G.family_of(suite)
        want = G.resolve_component_plan(suite, pid, 1)
        assert (spec["target_plan_entry"]["target_phys_idx"]
                == want["target_phys_idx"])
        assert (int(spec["target_plan_entry"]["fault_mask"], 0)
                == want["fault_mask_value"])
        assert spec["target_plan_entry"]["polarity"] == want["polarity"]


# ---------------------------------------------------------------------------
# Gate accounting / 5-of-5 logic
# ---------------------------------------------------------------------------
def _record(ok, pid="gemm", index=0):
    return {"program_id": pid, "program_index": index, "ok": ok,
            "status": "PASS" if ok else "FAIL",
            "component_oracle": "SDC",
            "target_plan_entry": {"target_phys_idx": 0}}


def test_gate_5_of_5_pass_and_4_of_5_fail(tmp_path):
    suite = load(SUITE_W5)
    info = G.validate_suite_manifest(suite, require_hashes=True,
                                     require_suite_hash=True)
    records = [_record(True, pid, i)
               for i, pid in enumerate(G.W5_ORDER)]
    report = G._write_report(tmp_path / "seed1", "FSU-FR03-F5-W5-GATE", suite,
                             info, 1, records)
    assert report["ok"] is True
    assert report["component_pass_count"] == 5
    assert report["component_run_count"] == 5
    assert report["non_formal"] is True
    assert report["counts_toward_519"] is False
    assert report["formal_suite_seed_count"] == 0
    assert (tmp_path / "seed1/gate_report.json").exists()
    assert (tmp_path / "seed1/GATE.md").exists()
    assert (tmp_path / "seed1/SHA256SUMS").exists()

    broken = list(records)
    broken[2] = _record(False, "lu", 2)
    report = G._write_report(tmp_path / "seed2", "FSU-FR03-F5-W5-GATE",
                             suite, info, 2, broken)
    assert report["ok"] is False
    assert report["component_pass_count"] == 4
    assert report["formal_suite_seed_count"] == 0


def test_gate_3_of_3_w6_counts_zero_seeds(tmp_path):
    suite = load(SUITE_W6)
    info = G.validate_suite_manifest(suite, require_hashes=True,
                                     require_suite_hash=True)
    records = [_record(True, pid, i)
               for i, pid in enumerate(G.W6_ORDER)]
    report = G._write_report(tmp_path / "seed1", "FSU-FR03-F5-W6-GATE",
                             suite, info, 1, records)
    assert report["ok"] is True
    assert report["component_run_count"] == 3
    assert report["formal_suite_seed_count"] == 0
    assert report["counts_toward_519"] is False
    broken = records[:-1] + [_record(False, "sparse-cg", 2)]
    report = G._write_report(tmp_path / "seed2", "FSU-FR03-F5-W6-GATE",
                             suite, info, 2, broken)
    assert report["ok"] is False
    assert report["component_pass_count"] == 2


def test_gate_refuses_runs_fsu(tmp_path):
    with pytest.raises(G.FR03SuiteError, match="runs/fsu is reserved"):
        G._assert_gate_outdir(tmp_path / "runs/fsu/EVIL", tmp_path)
    G._assert_gate_outdir(tmp_path / "runs/fsu-gates/OK", tmp_path)
    with pytest.raises(G.FR03SuiteError, match="must live under"):
        G._assert_gate_outdir(tmp_path / "elsewhere/OK", tmp_path)
    with pytest.raises(G.FR03SuiteError, match="runs/fsu is reserved"):
        G.run_gate(SUITE_W5, tmp_path / "runs/fsu/EVIL", ROOT / "nope",
                   ROOT / "nope", tmp_path, verify_only=True)


# ---------------------------------------------------------------------------
# --print-commands: the CHAOSPhysReg route only
# ---------------------------------------------------------------------------
def test_print_commands_physreg_only(tmp_path, capsys):
    outdir = tmp_path / "runs/fsu-gates/FR03-F5-W5-GATE"
    rc = G.run_gate(SUITE_W5, outdir, ROOT / "nope", ROOT / "nope", tmp_path,
                    print_only=True, suite_seed=1)
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["gate_id"] == "FSU-FR03-F5-W5-GATE"
    assert data["suite_hash"] == HASH_W5
    assert len(data["seeds"]) == 1
    seed = data["seeds"][0]
    assert [c["program_id"] for c in seed["commands"]] == list(G.W5_ORDER)
    suite_obj = json.loads(Path(SUITE_W5).read_text(encoding="utf-8"))
    for cmd in seed["commands"]:
        inject = cmd["inject"]
        assert "--chaos_phys" in inject
        assert "--chaos_fpu" not in inject
        assert inject[inject.index("--phys_mode") + 1] == "phys"
        assert inject[inject.index("--phys_reg_class") + 1] == "vector"
        plan = G.resolve_component_plan(suite_obj, cmd["program_id"], 1)
        assert (inject[inject.index("--phys_target_idx") + 1]
                == str(plan["target_phys_idx"]))
        assert "--phys_require_allocated" in inject
        assert inject[inject.index("--phys_semantic_role") + 1] == "FR03"
        assert inject[inject.index("--config_profile") + 1] == "B0"
        assert inject[inject.index("--fault_type") + 1] == plan["fault_type"]
        assert (int(inject[inject.index("--fault_mask") + 1])
                == plan["fault_mask_value"])
        assert any(x.startswith("--cmd_arg=--array-dump=") for x in inject)
        assert cmd["target_phys_idx"] == plan["target_phys_idx"]
        assert cmd["require_allocated"] is True
        assert int(cmd["fault_mask"], 0) == plan["fault_mask_value"]
        assert cmd["polarity"] == plan["polarity"]
    assert not outdir.exists()


def test_print_commands_w6_all_seeds(tmp_path, capsys):
    rc = G.run_gate(SUITE_W6, tmp_path / "runs/fsu-gates/X", ROOT / "nope",
                    ROOT / "nope", tmp_path, print_only=True, suite_seed=1,
                    all_seeds=True)
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["suite_hash"] == HASH_W6
    seeds = {s["suite_seed"]: s for s in data["seeds"]}
    assert sorted(seeds) == [1, 2, 3]
    for seed_no, seed in seeds.items():
        for cmd in seed["commands"]:
            if cmd["program_id"] == "svd":
                assert cmd["vec_lane_width"] == 64
                assert cmd["precision"] == "fp64"
                assert int(cmd["fault_mask"], 0) < (1 << 64)
            else:
                assert cmd["vec_lane_width"] == 32
                assert cmd["precision"] == "fp32"
            assert cmd["target_phys_idx"] == 47
            assert cmd["polarity"] == 1


# ---------------------------------------------------------------------------
# FR03 assertions driving the gate
# ---------------------------------------------------------------------------
def _synthetic_fr03_report(plan):
    return {
        "ok": True, "violations": [], "truncated": False,
        "fault_id": "1",
        "target": {
            "reg_class": "vec",
            "phys_reg": str(plan["target_phys_idx"]),
            "fixed_mask": plan["fault_mask"],
            "stuck_polarity": str(plan["polarity"]),
            "lane_width": str(plan["vec_lane_width"]),
            "lane_offset": str(plan["vec_lane_offset"]),
        },
        "counts": {
            "exposures_total": 3, "write_exposures_total": 3,
            "read_exposures_total": 2, "commit_events": 1,
            "squash_events": 0, "observed_operand_reads": 2,
            "observed_phys_writes": 3, "observed_commits": 1,
            "observed_squashes": 0,
        },
        "l5": {"terminal": "committed", "first_impact_sn": "10",
               "first_impact_latency": "100", "l5_witness_event": "4"},
    }


def test_plan_checks_accept_and_reject():
    suite = load(SUITE_W5)
    plan = G.resolve_component_plan(suite, "gemm", 1)
    report = _synthetic_fr03_report(plan)
    assert all(c["ok"] for c in G._plan_checks(report, plan))
    drift = json.loads(json.dumps(report))
    drift["target"]["phys_reg"] = "45"
    assert any(not c["ok"] for c in G._plan_checks(drift, plan))
    no_l5 = json.loads(json.dumps(report))
    no_l5["l5"]["terminal"] = "exposed_unconsumed"
    no_l5["counts"]["observed_commits"] = 0
    no_l5["counts"]["observed_squashes"] = 0
    assert any(not c["ok"] for c in G._plan_checks(no_l5, plan))


def _fabricate_component(seed_dir, suite, program, suite_seed, gate_id,
                         broken=False):
    plan = G.resolve_component_plan(suite, program["program_id"], suite_seed)
    cseed = G.derive_component_seed(suite, suite_seed, program["program_id"])
    attempt = (Path(seed_dir) / "components" / program["program_id"] /
               gate_id / f"seed{cseed}" / "attempt-1")
    (attempt / "inject").mkdir(parents=True)
    spec = G._component_spec(suite, program, suite_seed, cseed, gate_id)
    (attempt / "manifest.json").write_text(
        json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    cm = {
        "suite_id": suite["suite_id"],
        "suite_version": suite["suite_version"],
        "suite_hash": G.compute_suite_hash(suite),
        "suite_seed": suite_seed,
        "program_id": program["program_id"],
        "program_index": program["program_index"],
        "component_status": "admitted" if not broken else "failed",
        "component_oracle": "MASKED",
        "component_manifest_sha256": G.sha256_file(attempt / "manifest.json"),
        "target_plan_entry": plan,
    }
    (attempt / "component_manifest.json").write_text(
        json.dumps(cm, ensure_ascii=False, indent=2), encoding="utf-8")
    (attempt / "audit.json").write_text(json.dumps({
        "ok": not broken, "certified": not broken}), encoding="utf-8")
    golden = G._golden_path(program, ROOT)
    (attempt / "inject/array.bin").write_bytes(golden.read_bytes())
    return attempt, plan


def test_verify_only_5_of_5_and_4_of_5(tmp_path, monkeypatch):
    suite = load(SUITE_W5)
    monkeypatch.setattr(G, "fr03_analyze",
                        lambda attempt: _synthetic_fr03_report(
                            G.resolve_component_plan(
                                suite, _pid_of(attempt), 1)))
    outdir = tmp_path / "runs/fsu-gates/FR03-F5-W5-GATE"
    seed_dir = outdir / "seed1"
    for program in suite["programs"]:
        _fabricate_component(seed_dir, suite, program, 1,
                             G.default_gate_id(suite))
    report = G.run_gate(SUITE_W5, outdir, ROOT / "nope", ROOT / "nope",
                        tmp_path, suite_seed=1, verify_only=True)
    assert report["ok"] is True, report["records"]
    assert report["component_pass_count"] == 5
    assert report["formal_suite_seed_count"] == 0
    assert report["counts_toward_519"] is False


def _pid_of(attempt):
    # .../components/<program_id>/<gate>/seed<cseed>/attempt-1
    return Path(attempt).parents[2].name


def test_verify_only_one_broken_component_fails(tmp_path, monkeypatch):
    suite = load(SUITE_W5)
    monkeypatch.setattr(G, "fr03_analyze",
                        lambda attempt: _synthetic_fr03_report(
                            G.resolve_component_plan(
                                suite, _pid_of(attempt), 1)))
    outdir = tmp_path / "runs/fsu-gates/FR03-F5-W5-GATE"
    seed_dir = outdir / "seed1"
    for program in suite["programs"]:
        _fabricate_component(seed_dir, suite, program, 1,
                             G.default_gate_id(suite),
                             broken=program["program_id"] == "lu")
    report = G.run_gate(SUITE_W5, outdir, ROOT / "nope", ROOT / "nope",
                        tmp_path, suite_seed=1, verify_only=True)
    assert report["ok"] is False
    assert report["component_pass_count"] == 4
    lu = next(r for r in report["records"] if r["program_id"] == "lu")
    assert lu["status"] == "FAIL"
    assert any("audit.ok" in f for f in lu["failures"])


# ---------------------------------------------------------------------------
# W6 artifact readiness: sources, fixed inputs, oracle strictness
# ---------------------------------------------------------------------------
def test_w6_sources_and_pre_registered_oracle():
    svd = (ROOT / "workloads/directed/svd_iterative_kernel.c").read_text()
    fft = (ROOT / "workloads/directed/fft_radix2_kernel.c").read_text()
    cg = (ROOT / "workloads/directed/sparse_cg_kernel.c").read_text()
    assert "#define N 8" in svd
    assert "sweep < 10" in svd
    assert "#define FFT_N 1024" in fft
    assert "((i * 37 + 11) % 101) - 50" in fft
    assert "#define GRID 16" in cg
    assert "#define CG_N (GRID * GRID)" in cg
    assert "#define CG_MAXIT 400" in cg
    assert "#define CG_TOL 1.0e-7f" in cg
    assert "4.0f * v[idx]" in cg          # five-point Laplacian (SPD)
    assert "1.0f + (float)((idx * 7 + 3) % 11) / 11.0f" in cg
    assert "x[i] = 0.0f" in cg            # x0 = 0
    for src in (svd, fft, cg):
        code = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
        code = re.sub(r"//[^\n]*", "", code)
        assert not re.search(r"\brand\s*\(", code)
        assert not re.search(r"\btime\s*\(", code)

    suite = load(SUITE_W6)
    expect = {"svd": ("fp64", 64, 64), "fft": ("fp32", 32, 1024),
              "sparse-cg": ("fp32", 32, 256)}
    for program in suite["programs"]:
        meta = program["element_oracle"]["meta"]
        dtype, width, count = expect[program["program_id"]]
        assert meta["dtype"] == dtype
        assert meta["count"] == count
        assert meta["abs_tol"] == 0.0
        assert meta["rel_tol"] == 0.0
        assert meta["ulp_tol"] == 0
        assert G.resolve_component_plan(
            suite, program["program_id"], 1)["vec_lane_width"] == width


def test_element_oracle_rejects_missing_short_and_nan(tmp_path):
    suite = load(SUITE_W6)
    program = next(p for p in suite["programs"]
                   if p["program_id"] == "svd")
    attempt = tmp_path / "attempt-1"
    (attempt / "inject").mkdir(parents=True)

    # Missing output: a loud failure, never a silent pass.
    with pytest.raises(G.FR03SuiteError, match="array-dump"):
        G.element_oracle(attempt, program, "W6", ROOT, write=False)

    # Truncated array (wrong length) must fail the oracle.
    (attempt / "inject/array.bin").write_bytes(b"\x00" * 4)
    with pytest.raises(Exception):
        G.element_oracle(attempt, program, "W6", ROOT, write=False)

    # NaN where the golden has a finite value is never rescued by tolerance.
    golden = G._golden_path(program, ROOT).read_bytes()
    nan_bits = (0x7FF8000000000000).to_bytes(8, "little")
    (attempt / "inject/array.bin").write_bytes(nan_bits + golden[8:])
    result = G.element_oracle(attempt, program, "W6", ROOT, write=False)
    assert result["ok"] is True
    assert result["mismatch_count"] >= 1
    assert result["category"] != "EXACT_MATCH"


# ---------------------------------------------------------------------------
# Real FR03 W3 evidence (read-only integration check)
# ---------------------------------------------------------------------------
@pytest.mark.skipif(not (REAL_W3 / "inject/prop_evt.txt.gz").exists(),
                    reason="FR03 W3 gate evidence not present")
def test_real_w3_evidence_still_passes_plan_checks():
    report = G.fr03_analyze(REAL_W3)
    assert report["ok"], report["violations"]
    plan = {
        "target_phys_idx": 0,
        "vec_lane_width": 32,
        "vec_lane_offset": 2,
        "fault_mask": "0x80000000",
        "fault_mask_value": 0x80000000,
        "polarity": 1,
    }
    assert all(c["ok"] for c in G._plan_checks(report, plan))
    assert report["l5"]["terminal"] in G.L5_OK_TERMINALS
