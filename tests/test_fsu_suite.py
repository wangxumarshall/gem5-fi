"""tests/test_fsu_suite.py — W5 suite 身份、hash、派生 seed 与 suite 门禁。"""
import copy
import hashlib
import json
import sys
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import fsu_suite as S  # noqa: E402

SUITE_PATH = ROOT / "configs/fsu/suites/polybench-fp-v1.json"
F5_SUITE_PATH = ROOT / "configs/fsu/suites/polybench-fp-v1-f5.json"
SCHEMA = json.loads((ROOT / "schemas/fsu_suite.schema.json").read_text(
    encoding="utf-8"))
COMPONENT_SCHEMA = json.loads(
    (ROOT / "schemas/fsu_component.schema.json").read_text(encoding="utf-8"))


def real_suite():
    return json.loads(SUITE_PATH.read_text(encoding="utf-8"))


def complete_suite():
    """Real identity with complete (non-pending) binary hashes for gate tests."""
    suite = copy.deepcopy(real_suite())
    for p in suite["programs"]:
        p["binary_sha256"] = hashlib.sha256(
            ("bin:" + p["program_id"]).encode()).hexdigest()
    suite["suite_hash"] = S.compute_suite_hash(suite)
    return suite


SEED_PLAN = [
    {"suite_seed": 1, "submodel": "FP06-a", "bitseg": "sign",
     "precision": "fp32", "lane_width": 32, "lane_offset": 0,
     "mask": "0x80000000", "polarity": 0, "warmup": 1024,
     "sample": {"limit": 1024, "keep_first_last_n": 256},
     "op_classes": [], "reg_class": "any", "decode_guard": True,
     "permanent_stuck": True},
    {"suite_seed": 2, "submodel": "FP06-b", "bitseg": "sign",
     "precision": "fp32", "lane_width": 32, "lane_offset": 0,
     "mask": "0x80000000", "polarity": 1, "warmup": 1024,
     "sample": {"limit": 1024, "keep_first_last_n": 256},
     "op_classes": [], "reg_class": "any", "decode_guard": True,
     "permanent_stuck": True},
    {"suite_seed": 3, "submodel": "FP06-c",
     "precision": "fp32", "lane_width": 32, "lane_offset": 0,
     "mask": "0x007f8000", "polarity": 0, "warmup": 1024,
     "sample": {"limit": 1024, "keep_first_last_n": 256},
     "op_classes": [], "reg_class": "any", "decode_guard": True,
     "permanent_stuck": True},
]


def f5_suite():
    """A complete F5 suite identity with the real 3-seed pre-registration."""
    suite = complete_suite()
    suite["suite_id"] = "test-polybench-fp-v1-f5"
    suite["run_defaults"]["model_id"] = "FP06"
    suite["run_defaults"]["freq"] = "F5"
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
    suite["seed_plan"] = copy.deepcopy(SEED_PLAN)
    suite["suite_hash"] = S.compute_suite_hash(suite)
    return suite


def component_for(suite, pid, suite_seed=1, attempt=1, status="admitted"):
    p = next(x for x in suite["programs"] if x["program_id"] == pid)
    cseed = S.derive_component_seed(
        suite_seed, pid, S.DEFAULT_COMPONENT_SEED_POLICY,
        suite["suite_id"], suite["suite_version"])
    golden_sha, _ = S.component_golden_sha256(p)
    comp = {
        "suite_id": suite["suite_id"],
        "suite_version": suite["suite_version"],
        "suite_hash": S.compute_suite_hash(suite),
        "suite_seed": suite_seed,
        "program_id": pid,
        "program_index": S.PROGRAM_ORDER.index(pid),
        "program_count": 5,
        "component_seed_policy_version": S.DEFAULT_COMPONENT_SEED_POLICY,
        "component_seed": cseed,
        "component_attempt": attempt,
        "component_manifest_sha256": "a" * 64,
        "component_binary_sha256": p["binary_sha256"],
        "component_source_sha256": p["source_sha256"],
        "component_golden_sha256": golden_sha,
        "component_status": status,
        "component_eligible": 100,
        "component_activated": 1,
        "component_faults": 1,
        "component_terminal": "full",
        "component_oracle": "SDC",
        "component_audit_ok": status == "admitted",
        "component_certified": status == "admitted",
    }
    plan = S.seed_plan_map(suite)
    if plan is not None:
        comp["seed_plan_entry"] = S.seed_plan_identity(plan[suite_seed])
    return comp


def make_suite_seed(tmp_path, suite, audit_ok=True, broken_pid=None,
                    rid="FSU-TEST-F0-W5", seed=1):
    seed_dir = tmp_path / "runs" / rid / f"seed{seed}"
    policy = S.DEFAULT_COMPONENT_SEED_POLICY
    cseeds = S.derive_component_seeds(seed, policy, suite["suite_id"],
                                      suite["suite_version"])
    comps = []
    for pid in S.PROGRAM_ORDER:
        attempt = (seed_dir / "components" / pid / rid /
                   f"seed{cseeds[pid]}" / "attempt-1")
        attempt.mkdir(parents=True)
        mp = attempt / "manifest.json"
        mp.write_text(json.dumps({"run_id": rid, "program_id": pid}),
                      encoding="utf-8")
        cm = component_for(suite, pid, seed)
        cm["component_manifest_sha256"] = S.sha256_file(mp)
        audit = {"ok": True, "certified": True}
        if broken_pid == pid:
            cm["component_status"] = "failed"
            cm["component_audit_ok"] = False
            cm["component_certified"] = False
            audit = {"ok": False, "certified": False}
        (attempt / "component_manifest.json").write_text(
            json.dumps(cm, ensure_ascii=False, indent=2), encoding="utf-8")
        (attempt / "audit.json").write_text(
            json.dumps(audit), encoding="utf-8")
        # Element-oracle evidence required by suite_seed_state.
        (attempt / "inject").mkdir()
        (attempt / "inject/array.bin").write_bytes(b"\x00" * 8)
        (attempt / "oracle_elements.json").write_text(
            json.dumps({"ok": True, "program_id": pid,
                        "mismatch_count": 0, "category": "EXACT_MATCH"}),
            encoding="utf-8")
        hashes = {
            "oracle_elements.json": S.sha256_file(
                attempt / "oracle_elements.json"),
            "inject/array.bin": S.sha256_file(attempt / "inject/array.bin"),
        }
        (attempt / "evidence_sha256.json").write_text(
            json.dumps(hashes), encoding="utf-8")
        comps.append({**cm, "attempt": str(attempt)})
    sm = {
        "suite": suite,
        "suite_id": suite["suite_id"],
        "suite_version": suite["suite_version"],
        "suite_hash": S.compute_suite_hash(suite),
        "suite_seed": seed,
        "run_id": rid,
        "program_order": list(S.PROGRAM_ORDER),
        "program_count": 5,
        "component_seed_policy_version": policy,
        "components": comps,
    }
    (seed_dir / "suite_manifest.json").write_text(
        json.dumps(sm, ensure_ascii=False, indent=2), encoding="utf-8")
    (seed_dir / "audit.json").write_text(
        json.dumps({"ok": audit_ok}), encoding="utf-8")
    return seed_dir


# ---------- suite hash ----------

def test_real_suite_is_valid_and_fixed_order():
    suite = real_suite()
    assert suite["program_order"] == list(S.PROGRAM_ORDER)
    assert suite["program_count"] == 5
    info = S.validate_suite_manifest(suite)
    assert info["ok"] is True
    assert info["suite_hash"] == suite["suite_hash"]
    assert len(info["identity"]["programs"]) == 5


def test_suite_hash_stable():
    suite = real_suite()
    assert S.compute_suite_hash(suite) == S.compute_suite_hash(
        json.loads(json.dumps(suite)))
    assert S.compute_suite_hash(suite) == suite["suite_hash"]


def test_suite_hash_changes_on_any_identity_tamper():
    base = real_suite()
    h0 = S.compute_suite_hash(base)

    def changed(mut):
        d = copy.deepcopy(base)
        mut(d)
        return S.compute_suite_hash(d)

    mutations = {
        "suite_id": lambda d: d.__setitem__("suite_id", "other-v1"),
        "suite_version": lambda d: d.__setitem__("suite_version", "2"),
        "source_sha256": lambda d: d["programs"][0].__setitem__(
            "source_sha256", "b" * 64),
        "binary_sha256": lambda d: d["programs"][0].__setitem__(
            "binary_sha256", "c" * 64),
        "scale": lambda d: d["programs"][0]["scale"].__setitem__(
            "NI", 89),
        "compiler_version": lambda d: d["compiler"].__setitem__(
            "version", "10.9.9"),
        "cflags": lambda d: d["compiler"]["cflags"].append("-DFOO"),
        "oracle_version": lambda d: d["oracle"].__setitem__("version", "2"),
    }
    for name, fn in mutations.items():
        assert changed(fn) != h0, name

    # program_order / program_count are fixed identity constraints, not
    # mutable hash inputs: changing them must be rejected loudly.
    with pytest.raises(S.SuiteError, match="order is fixed"):
        changed(lambda d: d.__setitem__(
            "program_order", list(reversed(S.PROGRAM_ORDER))))
    with pytest.raises(S.SuiteError, match="program_count"):
        changed(lambda d: d.__setitem__("program_count", 4))


def test_suite_hash_excludes_run_results():
    suite = real_suite()
    h0 = S.compute_suite_hash(suite)
    d = copy.deepcopy(suite)
    d["last_run"] = {"status": "admitted", "oracle": "SDC"}
    d["programs"][0]["golden"] = "deadbeefdeadbeef"
    d["programs"][0]["component_status"] = "admitted"
    d["attempt"] = "attempt-9"
    assert S.compute_suite_hash(d) == h0
    assert "golden" not in json.dumps(S.suite_identity_document(d))
    assert "attempt" not in json.dumps(S.suite_identity_document(d))


def test_suite_hash_drift_rejected():
    suite = complete_suite()
    suite["compiler"]["version"] = "tampered"
    with pytest.raises(S.SuiteError, match="suite_hash drift"):
        S.validate_suite_manifest(suite, require_suite_hash=True)


def test_missing_component_rejected():
    suite = complete_suite()
    suite["programs"] = [p for p in suite["programs"]
                         if p["program_id"] != "lu"]
    with pytest.raises(S.SuiteError, match="missing program"):
        S.validate_suite_manifest(suite)


def test_duplicate_component_rejected():
    suite = complete_suite()
    suite["programs"][2] = copy.deepcopy(suite["programs"][0])
    with pytest.raises(S.SuiteError, match="duplicate program"):
        S.validate_suite_manifest(suite)


def test_program_count_and_index_mismatch_rejected():
    suite = complete_suite()
    suite["program_count"] = 4
    with pytest.raises(S.SuiteError, match="program_count"):
        S.validate_suite_manifest(suite)

    suite = complete_suite()
    p = next(x for x in suite["programs"] if x["program_id"] == "lu")
    p["program_index"] = 1
    with pytest.raises(S.SuiteError, match="program_index"):
        S.validate_suite_manifest(suite)


def test_program_order_reorder_rejected():
    suite = complete_suite()
    suite["program_order"] = ["2mm", "gemm", "lu", "cholesky", "jacobi-2d"]
    with pytest.raises(S.SuiteError, match="order is fixed"):
        S.validate_suite_manifest(suite)


def test_require_hashes_rejects_pending():
    suite = complete_suite()
    suite["programs"][0]["binary_sha256"] = "pending"
    suite["suite_hash"] = S.compute_suite_hash(suite)
    with pytest.raises(S.SuiteError, match="pending"):
        S.validate_suite_manifest(suite, require_hashes=True)
    ok = complete_suite()
    assert S.validate_suite_manifest(ok, require_hashes=True)["ok"] is True
    # The real config is pending today (post-oracle source change, no
    # rebuild); if it has been backfilled, require_hashes must accept it.
    real = real_suite()
    pending = any(p["binary_sha256"] == "pending" for p in real["programs"])
    if pending:
        with pytest.raises(S.SuiteError, match="pending"):
            S.validate_suite_manifest(real, require_hashes=True)
    else:
        assert S.validate_suite_manifest(
            real, require_hashes=True, require_suite_hash=True)["ok"] is True


# ---------- component seed derivation ----------

def test_component_seed_deterministic_and_unique():
    a = S.derive_component_seeds(1)
    b = S.derive_component_seeds(1)
    assert a == b
    assert list(a) == list(S.PROGRAM_ORDER)
    assert len(set(a.values())) == 5
    assert all(v >= 1 for v in a.values())
    assert S.derive_component_seeds(2) != a
    assert S.derive_component_seeds(1, "other-policy") != a


def test_component_seed_zero_maps_to_one():
    assert S.component_seed_from_digest(b"\x00" * 32) == 1
    assert S.component_seed_from_digest(b"\x00" * 8 + b"\xff") == 1
    assert S.component_seed_from_digest(b"\x00" * 7 + b"\x01") == 1
    assert S.component_seed_from_digest(b"\x00" * 7 + b"\x02") == 2


def test_component_seed_hash_material():
    suite_seed, pid, policy = 3, "lu", "p1"
    material = "|".join([S.DEFAULT_SUITE_ID, S.DEFAULT_SUITE_VERSION,
                         str(suite_seed), pid, policy]).encode()
    want = S.component_seed_from_digest(hashlib.sha256(material).digest())
    assert S.derive_component_seed(suite_seed, pid, policy) == want


# ---------- component manifests ----------

def test_component_manifest_valid_and_drift_rejected():
    suite = complete_suite()
    comp = component_for(suite, "gemm")
    assert S.validate_component_manifest(comp, suite)["ok"] is True
    S.validate_component_manifests(
        [component_for(suite, p) for p in S.PROGRAM_ORDER], suite)

    bad = copy.deepcopy(comp)
    bad["program_index"] = 1
    with pytest.raises(S.SuiteError, match="program_index"):
        S.validate_component_manifest(bad, suite)

    bad = copy.deepcopy(comp)
    bad["suite_hash"] = "b" * 64
    with pytest.raises(S.SuiteError, match="suite_hash drift"):
        S.validate_component_manifest(bad, suite)

    bad = copy.deepcopy(comp)
    del bad["component_oracle"]
    with pytest.raises(S.SuiteError, match="missing fields"):
        S.validate_component_manifest(bad, suite)

    bad = copy.deepcopy(comp)
    bad["program_count"] = 4
    with pytest.raises(S.SuiteError, match="program_count"):
        S.validate_component_manifest(bad, suite)

    bad = copy.deepcopy(comp)
    bad["component_status"] = "unknown"
    with pytest.raises(S.SuiteError, match="component_status"):
        S.validate_component_manifest(bad, suite)


def test_missing_and_duplicate_components_rejected():
    suite = complete_suite()
    comps = [component_for(suite, p) for p in S.PROGRAM_ORDER]
    with pytest.raises(S.SuiteError, match="exactly 5"):
        S.validate_component_manifests(comps[:4], suite)
    dup = copy.deepcopy(comps)
    dup[4] = copy.deepcopy(dup[0])
    with pytest.raises(S.SuiteError, match="duplicate"):
        S.validate_component_manifests(dup, suite)
    reordered = [comps[1], comps[0], comps[2], comps[3], comps[4]]
    with pytest.raises(S.SuiteError, match="fixed order"):
        S.validate_component_manifests(reordered, suite)


# ---------- suite_seed_state ----------

def test_suite_seed_state_admitted_only_with_5_of_5(tmp_path):
    suite = complete_suite()
    seed_dir = make_suite_seed(tmp_path, suite)
    st = S.suite_seed_state(seed_dir)
    assert st["state"] == "admitted", st
    assert st["component_runs"] == 5
    assert st["component_certified"] == 5
    assert st["suite_audit_ok"] is True


def test_suite_seed_state_rejects_broken_component(tmp_path):
    suite = complete_suite()
    seed_dir = make_suite_seed(tmp_path, suite, broken_pid="2mm")
    st = S.suite_seed_state(seed_dir)
    assert st["state"] != "admitted"
    assert st["component_certified"] == 4


def test_suite_seed_state_requires_suite_audit_ok(tmp_path):
    suite = complete_suite()
    seed_dir = make_suite_seed(tmp_path, suite, audit_ok=False)
    st = S.suite_seed_state(seed_dir)
    assert st["state"] != "admitted"
    assert st["suite_audit_ok"] is False


def test_suite_seed_state_rejects_hash_drift(tmp_path):
    suite = complete_suite()
    seed_dir = make_suite_seed(tmp_path, suite)
    sm_path = seed_dir / "suite_manifest.json"
    sm = json.loads(sm_path.read_text(encoding="utf-8"))
    sm["suite_hash"] = "c" * 64
    sm_path.write_text(json.dumps(sm), encoding="utf-8")
    st = S.suite_seed_state(seed_dir)
    assert st["state"] == "invalid"


def test_suite_seed_state_missing_component_manifest(tmp_path):
    suite = complete_suite()
    seed_dir = make_suite_seed(tmp_path, suite)
    cm = next(seed_dir.rglob("component_manifest.json"))
    cm.unlink()
    st = S.suite_seed_state(seed_dir)
    assert st["state"] != "admitted"


# ---------- schemas ----------

def test_suite_schema_accepts_real_config_and_rejects_violations():
    suite = real_suite()
    jsonschema.validate(suite, SCHEMA)

    bad = copy.deepcopy(suite)
    del bad["suite_hash"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, SCHEMA)

    bad = copy.deepcopy(suite)
    bad["program_order"] = list(reversed(S.PROGRAM_ORDER))
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, SCHEMA)

    bad = copy.deepcopy(suite)
    bad["program_count"] = 4
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, SCHEMA)

    bad = copy.deepcopy(suite)
    bad["compiler"]["cflags"] = []
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, SCHEMA)


def test_component_schema():
    suite = complete_suite()
    comp = component_for(suite, "cholesky")
    jsonschema.validate(comp, COMPONENT_SCHEMA)

    bad = copy.deepcopy(comp)
    del bad["component_eligible"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, COMPONENT_SCHEMA)

    bad = copy.deepcopy(comp)
    bad["component_status"] = "maybe"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, COMPONENT_SCHEMA)

    bad = copy.deepcopy(comp)
    bad["program_count"] = 4
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, COMPONENT_SCHEMA)


# ---------- F5 seed_plan (pre-registered 3 suite seeds) ----------

def test_real_f5_suite_identity_matches_disk():
    suite = json.loads(F5_SUITE_PATH.read_text(encoding="utf-8"))
    info = S.validate_suite_manifest(suite, require_hashes=True,
                                     require_suite_hash=True)
    assert info["ok"] is True
    assert suite["run_defaults"]["freq"] == "F5"
    assert suite["run_defaults"]["model_id"] == "FP06"
    assert suite["run_defaults"]["load_id"] == "W5"
    assert suite["run_defaults"]["limits"]["timeout_s"] == 3600
    plan = S.normalise_seed_plan(suite)
    assert [e["suite_seed"] for e in plan] == [1, 2, 3]
    assert [e["submodel"] for e in plan] == ["FP06-a", "FP06-b", "FP06-c"]
    assert [(e["mask"], e["polarity"]) for e in plan] == [
        ("0x80000000", 0), ("0x80000000", 1), ("0x007f8000", 0)]
    # Real on-disk identities, not copied tokens.
    for p in suite["programs"]:
        assert S.sha256_file(ROOT / p["source"]) == p["source_sha256"]
        assert S.sha256_file(ROOT / p["binary"]) == p["binary_sha256"]
        golden = ROOT / p["element_oracle"]["golden_array"]
        assert S.sha256_file(golden) == p["golden_array_sha256"]


def test_f5_suite_schema_accepts_real_config():
    suite = json.loads(F5_SUITE_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(suite, SCHEMA)


def test_f5_suite_without_seed_plan_is_rejected():
    suite = f5_suite()
    del suite["seed_plan"]
    with pytest.raises(S.SuiteError, match="must pre-register a seed_plan"):
        S.validate_suite_manifest(suite)


def test_seed_plan_hash_covers_every_pre_registered_field():
    base = f5_suite()
    h0 = S.compute_suite_hash(base)

    def changed(mut):
        d = copy.deepcopy(base)
        mut(d["seed_plan"][0])
        return S.compute_suite_hash(d)

    mutations = {
        "submodel": lambda e: e.__setitem__("submodel", "FP06-z"),
        "precision": lambda e: (e.__setitem__("precision", "fp64"),
                                e.__setitem__("lane_width", 64)),
        "mask": lambda e: e.__setitem__("mask", "0x80000001"),
        "polarity": lambda e: e.__setitem__("polarity", 1),
        "warmup": lambda e: e.__setitem__("warmup", 0),
        "sample.limit": lambda e: e["sample"].__setitem__("limit", 512),
        "sample.keep": lambda e: e["sample"].__setitem__(
            "keep_first_last_n", 128),
        "op_classes": lambda e: e.__setitem__("op_classes", ["FloatAdd"]),
        "reg_class": lambda e: e.__setitem__("reg_class", "vec"),
        "decode_guard": lambda e: e.__setitem__("decode_guard", False),
        "permanent_stuck": lambda e: e.__setitem__("permanent_stuck", False),
        "bitseg": lambda e: e.__setitem__("bitseg", "mant_lo"),
        "lane_offset": lambda e: e.__setitem__("lane_offset", 1),
    }
    for name, fn in mutations.items():
        assert changed(fn) != h0, name


def test_seed_plan_validation_rejects_garbage():
    def expect(entry, match):
        d = f5_suite()
        d["seed_plan"][0] = entry
        with pytest.raises(S.SuiteError, match=match):
            S.validate_suite_manifest(d)

    expect({"suite_seed": 1}, "missing required")
    expect(dict(SEED_PLAN[0], polarity=2), "polarity")
    expect(dict(SEED_PLAN[0], mask="0x100000000"), "does not fit lane_width")
    expect(dict(SEED_PLAN[0], mask="0x0"), "non-zero")
    expect(dict(SEED_PLAN[0], precision="fp16"), "precision")
    expect(dict(SEED_PLAN[0], submodel=""), "submodel")
    expect(dict(SEED_PLAN[0], unknown=1), "unknown field")
    expect(dict(SEED_PLAN[0], warmup=-1), "warmup")
    bad_sample = copy.deepcopy(SEED_PLAN[0])
    bad_sample["sample"]["keep_first_last_n"] = 2048
    expect(bad_sample, "keep_first_last_n")
    bad_ops = dict(SEED_PLAN[0], op_classes=["NotAnOp"])
    expect(bad_ops, "unknown name")


def test_seed_plan_requires_exactly_three_unique_seeds():
    d = f5_suite()
    d["seed_plan"] = d["seed_plan"][:2]
    with pytest.raises(S.SuiteError, match="exactly 3"):
        S.validate_suite_manifest(d)

    d = f5_suite()
    d["seed_plan"][1]["suite_seed"] = 1
    with pytest.raises(S.SuiteError, match="exactly"):
        S.validate_suite_manifest(d)


def test_seed_plan_entry_lookup_is_loud():
    suite = f5_suite()
    assert S.seed_plan_entry(suite, 1)["submodel"] == "FP06-a"
    assert S.seed_plan_entry(suite, 2)["polarity"] == 1
    assert S.seed_plan_entry(suite, 3)["mask"] == "0x007f8000"
    with pytest.raises(S.SuiteError, match="not in the pre-registered"):
        S.seed_plan_entry(suite, 4)
    legacy = real_suite()
    assert S.seed_plan_entry(legacy, 1) is None


def test_legacy_suite_hash_is_unchanged_by_seed_plan_support():
    suite = real_suite()
    assert S.compute_suite_hash(suite) == suite["suite_hash"]


def test_component_manifest_requires_matching_seed_plan_entry():
    suite = f5_suite()
    comp = component_for(suite, "gemm", suite_seed=2)
    assert S.validate_component_manifest(comp, suite)["ok"] is True

    bad = copy.deepcopy(comp)
    del bad["seed_plan_entry"]
    with pytest.raises(S.SuiteError, match="seed_plan_entry is required"):
        S.validate_component_manifest(bad, suite)

    bad = copy.deepcopy(comp)
    bad["seed_plan_entry"]["polarity"] = 0
    with pytest.raises(S.SuiteError, match="seed_plan_entry drift"):
        S.validate_component_manifest(bad, suite)

    # A component cannot silently use a different suite seed's plan.
    bad = copy.deepcopy(comp)
    bad["seed_plan_entry"] = S.seed_plan_identity(
        S.seed_plan_entry(suite, 1))
    with pytest.raises(S.SuiteError, match="seed_plan_entry drift"):
        S.validate_component_manifest(bad, suite)
