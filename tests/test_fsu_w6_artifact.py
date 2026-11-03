"""tests/test_fsu_w6_artifact.py — W6 SVD + FFT + sparse artifact identity.

Covers:
  * the fixed 3-component order and real on-disk source/binary/golden SHA;
  * native golden arrays are bit-identical across the recorded 3 runs;
  * the documented build command reproduces each committed binary;
  * any identity/tolerance drift is rejected via suite_hash;
  * the sparse component is a real CG solver, never an SpMV proxy.
"""
import copy
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import fsu_w6_oracle as WO  # noqa: E402
import fsu_w6_suite as WS  # noqa: E402

SUITE_PATH = ROOT / "configs/fsu/suites/w6-fp-v1.json"
GOLDEN_MANIFEST = (ROOT / "configs/fsu/suites/w6-fp-v1/golden/manifest.json")


def real_suite():
    return json.loads(SUITE_PATH.read_text(encoding="utf-8"))


def test_real_w6_suite_identity_and_disk_hashes():
    info = WS.load_suite(SUITE_PATH, root=ROOT)
    suite = info["suite"]
    assert suite["program_order"] == ["svd", "fft", "sparse-cg"]
    assert suite["program_count"] == 3
    assert info["suite_hash"] == suite["suite_hash"]
    for p in suite["programs"]:
        assert WS.sha256_file(ROOT / p["source"]) == p["source_sha256"]
        assert WS.sha256_file(ROOT / p["binary"]) == p["binary_sha256"]
        golden = ROOT / p["element_oracle"]["golden_array"]
        assert WS.sha256_file(golden) == p["golden_array_sha256"]
        meta = WO.validate_meta(p["element_oracle"]["meta"])
        assert meta["count"] * WO.ELEM_SIZES[meta["dtype"]] == golden.stat().st_size
        # Tolerances are pre-registered and fixed (bit-exact expectation).
        assert (meta["abs_tol"], meta["rel_tol"], meta["ulp_tol"]) == (0.0, 0.0, 0)


def test_malformed_final_token_rejected():
    d = real_suite()
    d["programs"][0]["golden"] = "not-a-hash"
    with pytest.raises(WS.W6SuiteError, match="16 lowercase hex"):
        WS.validate_suite_manifest(d)


def test_svd_final_is_the_registered_golden():
    suite = real_suite()
    svd = next(p for p in suite["programs"] if p["program_id"] == "svd")
    assert svd["golden"] == "4afb95b5b32f3820"
    runner = (ROOT / "tools/runner.py").read_text(encoding="utf-8")
    assert "svditerative-golden-v1" in runner
    assert "4afb95b5b32f3820" in runner


def test_native_golden_manifest_is_3x_identical():
    manifest = json.loads(GOLDEN_MANIFEST.read_text(encoding="utf-8"))
    assert manifest["ok"] is True
    assert manifest["program_order"] == ["svd", "fft", "sparse-cg"]
    suite = real_suite()
    by_id = {p["program_id"]: p for p in suite["programs"]}
    for pid in WS.W6_PROGRAM_ORDER:
        rec = manifest["programs"][pid]
        assert rec["native_reps"] == 3
        assert len(rec["native_shas"]) == 3
        assert len(set(rec["native_shas"])) == 1
        assert rec["native_shas"][0] == rec["sha256"]
        assert rec["sha256"] == by_id[pid]["golden_array_sha256"]
        assert rec["native_rcs"] == [0, 0, 0]
        assert len(set(rec["native_finals"])) == 1
        assert rec["native_finals"][0] == by_id[pid]["golden"]


def test_documented_gcc_command_reproduces_committed_binaries(tmp_path):
    gcc = shutil.which("gcc")
    if not gcc:
        pytest.skip("gcc not available")
    suite = real_suite()
    for p in suite["programs"]:
        dst = tmp_path / p["program_id"]
        cmd = [gcc, "-O2", "-static", "-Wall", "-Wextra",
               "-I", "workloads/ooo/polybench/utilities",
               "-o", str(dst), p["source"], "-lm"]
        r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True,
                           text=True)
        assert r.returncode == 0, r.stderr
        assert r.stderr.strip() == "", r.stderr
        assert WS.sha256_file(dst) == p["binary_sha256"]


def test_golden_arrays_reproduce_native_output(tmp_path):
    suite = real_suite()
    for p in suite["programs"]:
        dump = tmp_path / f"{p['program_id']}.bin"
        r = subprocess.run([str(ROOT / p["binary"]),
                            f"--array-dump={dump}"],
                           cwd=str(ROOT), capture_output=True, text=True)
        assert r.returncode == 0
        golden = (ROOT / p["element_oracle"]["golden_array"]).read_bytes()
        assert dump.read_bytes() == golden
        meta = WO.validate_meta(p["element_oracle"]["meta"])
        cmp = WO.compare(golden, golden, meta, meta["abs_tol"],
                         meta["rel_tol"], meta["ulp_tol"])
        assert cmp["category"] == "EXACT_MATCH"


def test_suite_hash_covers_identity_and_tolerances():
    base = real_suite()
    h0 = WS.compute_suite_hash(base)

    def changed(mut):
        d = copy.deepcopy(base)
        mut(d)
        return WS.compute_suite_hash(d)

    mutations = {
        "source": lambda d: d["programs"][0].__setitem__(
            "source_sha256", "a" * 64),
        "binary": lambda d: d["programs"][1].__setitem__(
            "binary_sha256", "b" * 64),
        "golden_array": lambda d: d["programs"][2].__setitem__(
            "golden_array_sha256", "c" * 64),
        "final": lambda d: d["programs"][1].__setitem__(
            "golden", "deadbeefdeadbeef"),
        "abs_tol": lambda d: d["programs"][0]["element_oracle"]["meta"]
        .__setitem__("abs_tol", 1e-9),
        "rel_tol": lambda d: d["programs"][1]["element_oracle"]["meta"]
        .__setitem__("rel_tol", 1e-6),
        "ulp_tol": lambda d: d["programs"][2]["element_oracle"]["meta"]
        .__setitem__("ulp_tol", 1),
        "scale": lambda d: d["programs"][2]["scale"].__setitem__("N", 255),
        "input_id": lambda d: d["programs"][0].__setitem__(
            "input_id", "other-input"),
        "cflags": lambda d: d["compiler"]["cflags"].append("-DFOO"),
    }
    for name, fn in mutations.items():
        assert changed(fn) != h0, name


def test_suite_hash_drift_rejected():
    suite = real_suite()
    suite["compiler"]["version"] = "tampered"
    with pytest.raises(WS.W6SuiteError, match="suite_hash drift"):
        WS.validate_suite_manifest(suite, require_suite_hash=True)


def test_fixed_order_missing_and_duplicate_rejected():
    base = real_suite()
    d = copy.deepcopy(base)
    d["program_order"] = ["fft", "svd", "sparse-cg"]
    with pytest.raises(WS.W6SuiteError, match="order is fixed"):
        WS.validate_suite_manifest(d)

    d = copy.deepcopy(base)
    d["programs"] = [p for p in d["programs"]
                     if p["program_id"] != "sparse-cg"]
    with pytest.raises(WS.W6SuiteError, match="missing"):
        WS.validate_suite_manifest(d)

    d = copy.deepcopy(base)
    d["programs"][2] = copy.deepcopy(d["programs"][0])
    with pytest.raises(WS.W6SuiteError, match="duplicate"):
        WS.validate_suite_manifest(d)


def test_require_hashes_rejects_pending():
    d = real_suite()
    d["programs"][0]["binary_sha256"] = "pending"
    with pytest.raises(WS.W6SuiteError, match="pending"):
        WS.validate_suite_manifest(d, require_hashes=True)


def test_suite_hash_excludes_run_results():
    suite = real_suite()
    h0 = WS.compute_suite_hash(suite)
    d = copy.deepcopy(suite)
    d["last_run"] = {"status": "admitted", "oracle": "SDC"}
    d["attempt"] = "attempt-9"
    d["programs"][0]["component_status"] = "admitted"
    assert WS.compute_suite_hash(d) == h0


def test_sparse_component_is_a_real_cg_solver_not_spmv_proxy():
    suite = real_suite()
    sparse = next(p for p in suite["programs"]
                  if p["program_id"] == "sparse-cg")
    assert Path(sparse["binary"]).name == "sparse_cg_kernel"
    src = (ROOT / sparse["source"]).read_text(encoding="utf-8")
    assert "conjugate gradient" in src.lower()
    assert "CG_MAXIT" in src and "rsold" in src and "matvec" in src
    assert "method1_controls" not in sparse["binary"]
    assert "pure_spmv" not in sparse["binary"]
    assert sparse["element_oracle"]["meta"]["count"] == 256


def test_fft_component_is_fixed_input_radix2():
    suite = real_suite()
    fft = next(p for p in suite["programs"] if p["program_id"] == "fft")
    src = (ROOT / fft["source"]).read_text(encoding="utf-8")
    assert "radix" in src.lower()
    assert "srand(" not in src
    assert "gettimeofday" not in src
    assert "#include <time.h>" not in src
    assert "FINAL=" in src
    assert fft["element_oracle"]["meta"]["count"] == 1024


# ---------- W6 per-program precision / program_overrides ----------

F5_W6 = ROOT / "configs/fsu/suites/w6-fp-v1-f5.json"
EXPECTED_GEOMETRY = {
    "svd": ("fp64", 64, 0),
    "fft": ("fp32", 32, 0),
    "sparse-cg": ("fp32", 32, 0),
}


def test_w6_f0_program_overrides_are_identity():
    suite = real_suite()
    ovs = WS._normalise_program_overrides(suite)
    for pid, (precision, lane, offset) in EXPECTED_GEOMETRY.items():
        fpu = ovs[pid]["fpu_mode"]
        assert fpu["precision"] == precision
        assert fpu["lane_width"] == lane
        assert fpu["lane_offset"] == offset
        inj = WS.resolved_injector(suite, pid)
        assert inj["fpu_mode"]["precision"] == precision
        assert inj["fpu_mode"]["lane_width"] == lane
    # The base injector is unchanged: bitseg=sign.
    assert suite["injector"]["fpu_mode"]["bitseg"] == "sign"


def test_w6_f5_config_identity_and_per_program_masks():
    suite = json.loads(F5_W6.read_text(encoding="utf-8"))
    info = WS.validate_suite_manifest(suite, require_hashes=True,
                                      require_suite_hash=True)
    assert info["ok"] is True
    assert suite["run_defaults"]["freq"] == "F5"
    assert suite["run_defaults"]["model_id"] == "FP06"
    assert suite["run_defaults"]["load_id"] == "W6"
    assert suite["run_defaults"]["limits"]["timeout_s"] == 3600
    plan = WS._normalise_seed_plan(suite)
    assert [e["suite_seed"] for e in plan] == [1, 2, 3]
    assert [e["submodel"] for e in plan] == ["FP06-a", "FP06-b", "FP06-c"]
    # Golden/binary/source identity is the same real artifact as F0.
    f0 = real_suite()
    f0_by = {p["program_id"]: p for p in f0["programs"]}
    for p in suite["programs"]:
        q = f0_by[p["program_id"]]
        assert p["source_sha256"] == q["source_sha256"]
        assert p["binary_sha256"] == q["binary_sha256"]
        assert p["golden_array_sha256"] == q["golden_array_sha256"]
        assert p["golden"] == q["golden"]

    expected = {
        1: {"svd": ("0x8000000000000000", 0),
            "fft": ("0x80000000", 0), "sparse-cg": ("0x80000000", 0)},
        2: {"svd": ("0x8000000000000000", 1),
            "fft": ("0x80000000", 1), "sparse-cg": ("0x80000000", 1)},
        3: {"svd": ("0x0007f80000000000", 0),
            "fft": ("0x007f8000", 0), "sparse-cg": ("0x007f8000", 0)},
    }
    for entry in plan:
        for pid in WS.W6_PROGRAM_ORDER:
            inj = WS.resolved_injector(suite, pid, entry)
            mask, polarity = expected[entry["suite_seed"]][pid]
            assert inj["fault_mask"] == mask, (entry["suite_seed"], pid)
            assert inj["fpu_mode"]["stuck_polarity"] == polarity
            precision, lane, _ = EXPECTED_GEOMETRY[pid]
            assert inj["fpu_mode"]["precision"] == precision
            assert inj["fpu_mode"]["lane_width"] == lane
            assert inj["fpu_mode"]["permanent_stuck"] is True
            # CHAOSFPU forbids permanentStuck + bitseg; the fixed mask owns
            # the target, so the F0 base bitseg=sign must be dropped.
            assert "bitseg" not in inj["fpu_mode"]
            assert inj["fpu_mode"]["f5_warmup"] == 1024
            assert inj["fpu_mode"]["f5_sample_limit"] == 1024
            assert inj["fpu_mode"]["f5_keep_first_last_n"] == 256
    # A 64-bit SVD mask would be invalid under fp32; the per-program mask
    # is what keeps this configuration decodable.
    assert int(expected[2]["svd"][0], 0) >> 32 != 0
    assert int(expected[2]["fft"][0], 0) >> 32 == 0


def test_w6_program_overrides_hash_and_rejection():
    suite = real_suite()
    h0 = WS.compute_suite_hash(suite)
    d = json.loads(json.dumps(suite))
    d["program_overrides"]["svd"]["fpu_mode"]["lane_offset"] = 1
    assert WS.compute_suite_hash(d) != h0
    d = json.loads(json.dumps(suite))
    d["program_overrides"]["nope"] = {"fpu_mode": {"precision": "fp32"}}
    with pytest.raises(WS.W6SuiteError, match="unknown program_id"):
        WS.validate_suite_manifest(d)
    d = json.loads(json.dumps(suite))
    d["program_overrides"]["svd"]["fpu_mode"]["bogus"] = 1
    with pytest.raises(WS.W6SuiteError, match="unknown field"):
        WS.validate_suite_manifest(d)


def test_w6_f5_requires_seed_plan_and_fitting_masks():
    suite = json.loads(F5_W6.read_text(encoding="utf-8"))
    d = json.loads(json.dumps(suite))
    del d["seed_plan"]
    with pytest.raises(WS.W6SuiteError, match="seed_plan"):
        WS.validate_suite_manifest(d)
    # Remove SVD's 64-bit program_mask: the fp32 global mask then targets a
    # 64-bit lane and is still valid; force an explicitly too-wide fp32 mask
    # to prove the fail-closed check.
    d = json.loads(json.dumps(suite))
    d["seed_plan"][0]["mask"] = "0x8000000000000000"
    d["seed_plan"][0]["program_mask"] = {"svd": "0x8000000000000000"}
    with pytest.raises(WS.W6SuiteError, match="does not fit"):
        WS.validate_suite_manifest(d)


def test_w6_f5_unknown_program_mask_rejected():
    suite = json.loads(F5_W6.read_text(encoding="utf-8"))
    d = json.loads(json.dumps(suite))
    d["seed_plan"][0]["program_mask"] = {"nope": "0x80000000"}
    with pytest.raises(WS.W6SuiteError, match="unknown program_id"):
        WS.validate_suite_manifest(d)
