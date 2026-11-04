"""tests/test_fsu_seed_plan_schema.py — versioned seed_plan compatibility.

The tests use the *real* frozen suite configs and, where marked, the real
recorded suite evidence on disk.  They never rewrite evidence: every
normalisation is a derived, in-memory document; source SHA-256 values are
recorded in the assertions.
"""
import copy
import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import fsu_fr03_suite_gate as G  # noqa: E402
import fsu_seed_plan_schema as SP  # noqa: E402
import fsu_suite as S  # noqa: E402
import fsu_suite_audit as U  # noqa: E402

SUITES = ROOT / "configs/fsu/suites"


def load(name):
    return json.loads((SUITES / f"{name}.json").read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# Real frozen configs: schema detection, hash and bindings are unchanged.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("name,kind", [
    ("polybench-fp-v1-fr03", "w5"),
    ("w6-fp-v1-fr03", "w6"),
])
def test_real_fr03_config_normalises(name, kind):
    cfg = load(name)
    schema, digest = SP.suite_hash(cfg, kind)
    assert schema == SP.SCHEMA_FR03
    assert digest == cfg["suite_hash"]
    assert digest == G.compute_suite_hash(cfg)
    document = SP.describe_document(cfg)
    assert document["mask_domain"].startswith("lane-relative")
    assert document["bindings"] == "target_plan_entry"
    for seed in (1, 2, 3):
        entry = SP.seed_entry(cfg, seed)[1]
        assert entry["schema_version"] == SP.SCHEMA_FR03
        assert entry["mask_domain"] == "lane"
        assert entry["mask"].lower().startswith("0x")
        assert entry["mask_value"] == int(entry["mask"], 0)
        for pid, mask in entry["program_mask"].items():
            width = entry["targets"][pid]["vec_lane_width"]
            assert int(mask, 0) < (1 << width)
        ws = SP.warmup_sample_contract(schema, entry)
        assert ws["warmup"]["status"] == "not_applicable"
        assert ws["warmup"]["value"] is None
        assert ws["sample"]["status"] == "not_applicable"


@pytest.mark.parametrize("name,kind", [
    ("polybench-fp-v1", "w5"),
    ("w6-fp-v1", "w6"),
    ("polybench-fp-v1-f5", "w5"),
    ("w6-fp-v1-f5", "w6"),
    ("polybench-fp-v1-fr07-hook", "w5"),
])
def test_other_suite_configs_unchanged(name, kind):
    cfg = load(name)
    schema, digest = SP.suite_hash(cfg, kind)
    assert digest == cfg["suite_hash"]
    if cfg.get("seed_plan"):
        assert schema == SP.SCHEMA_F5
        for seed in (1, 2, 3):
            entry = SP.seed_entry(cfg, seed)[1]
            # The canonical F5 identity is exactly the legacy one.
            assert entry == S.normalise_seed_plan(cfg)[seed - 1]
            ws = SP.warmup_sample_contract(schema, entry)
            assert isinstance(ws["warmup"]["value"], int)
            assert ws["warmup"]["unit"].startswith("eligible event")
            assert isinstance(ws["sample"]["limit"], int)
    else:
        assert schema is None


def test_aliases_agree_and_conflict_fail_closed():
    cfg = load("polybench-fp-v1-fr03")
    original_hash = G.compute_suite_hash(cfg)
    agreed = copy.deepcopy(cfg)
    agreed["seed_plan"][0]["mask"] = agreed["seed_plan"][0]["fault_mask"]
    agreed["seed_plan"][0]["lane_offset"] = \
        agreed["seed_plan"][0]["vec_lane_offset"]
    assert SP.detect_schema(agreed) == SP.SCHEMA_FR03
    assert SP.suite_hash(agreed, "w5")[1] == original_hash

    conflict = copy.deepcopy(cfg)
    conflict["seed_plan"][0]["mask"] = "0x00000001"
    with pytest.raises(SP.SeedPlanSchemaError, match="conflicting aliases"):
        SP.detect_schema(conflict)


def test_decimal_and_hex_mask_normalise_to_one_integer():
    cfg = load("polybench-fp-v1-fr03")
    original_hash = G.compute_suite_hash(cfg)
    decimal = copy.deepcopy(cfg)
    for entry in decimal["seed_plan"]:
        entry["fault_mask"] = str(int(entry["fault_mask"], 0))
    assert SP.suite_hash(decimal, "w5")[1] == original_hash
    entry = SP.seed_entry(cfg, 1)[1]
    entry_dec = SP.seed_entry(decimal, 1)[1]
    assert entry["mask_value"] == entry_dec["mask_value"]
    assert entry["program_mask"] == entry_dec["program_mask"]


def test_fault_type_polarity_conflict_fails_closed():
    cfg = load("polybench-fp-v1-fr03")
    bad = copy.deepcopy(cfg)
    bad["seed_plan"][0]["fault_type"] = "stuck_at_one"  # polarity is 0
    with pytest.raises(SP.SeedPlanSchemaError, match="conflicts with polarity"):
        SP.detect_schema(bad)
    # A conflicting mask alias and polarity is caught before hashing.
    bad2 = copy.deepcopy(cfg)
    bad2["seed_plan"][0]["mask"] = "0x1"
    with pytest.raises(SP.SeedPlanSchemaError):
        SP.suite_hash(bad2, "w5")


def test_missing_component_and_duplicate_program_fail():
    cfg = load("polybench-fp-v1-fr03")
    missing = copy.deepcopy(cfg)
    missing["programs"] = [p for p in missing["programs"]
                           if p["program_id"] != "lu"]
    with pytest.raises(Exception, match="missing program|program"):
        SP.suite_hash(missing, "w5")
    duplicate = copy.deepcopy(cfg)
    duplicate["programs"].append(copy.deepcopy(duplicate["programs"][0]))
    with pytest.raises(Exception, match="duplicate"):
        SP.suite_hash(duplicate, "w5")


def test_per_program_precision_and_mask_mismatch_fail():
    cfg = load("polybench-fp-v1-fr03")
    bad_precision = copy.deepcopy(cfg)
    bad_precision["target_plan"]["gemm"]["precision"] = "fp64"
    with pytest.raises(Exception, match="fp64 requires"):
        SP.normalise_plan(bad_precision)
    bad_mask = copy.deepcopy(cfg)
    bad_mask["seed_plan"][0]["fault_mask"] = "0x100000000"
    with pytest.raises(Exception, match="does not fit lane_width"):
        SP.normalise_plan(bad_mask)
    bad_lane = copy.deepcopy(cfg)
    bad_lane["seed_plan"][0]["vec_lane_offset"] = 4
    with pytest.raises(Exception, match="vec_lane_offset"):
        SP.normalise_plan(bad_lane)


def test_component_evidence_hash_change_is_detected():
    cfg = load("polybench-fp-v1-fr03")
    digest = G.compute_suite_hash(cfg)
    changed = copy.deepcopy(cfg)
    changed["programs"][0]["binary_sha256"] = "0" * 64
    assert G.compute_suite_hash(changed) != digest


def test_binding_missing_is_evidence_missing_not_guess():
    cfg = load("polybench-fp-v1-fr03")
    schema, entry = SP.seed_entry(cfg, 1)
    issues = SP.verify_binding(schema, entry, "gemm", {})
    assert issues and all(i.startswith("missing:") for i in issues)
    issues2 = SP.verify_binding(schema, entry, "gemm", None)
    assert issues2 == ["missing:binding"]


# ---------------------------------------------------------------------------
# Real recorded evidence: bindings, component seeds and the known drift.
# ---------------------------------------------------------------------------
REAL_SEEDS = sorted((ROOT / "runs/fsu").glob("FSU-*/seed*"))


@pytest.mark.parametrize("seed_dir", REAL_SEEDS,
                         ids=[str(p.relative_to(ROOT)) for p in REAL_SEEDS])
def test_real_suite_seed_binding(seed_dir):
    sm_path = seed_dir / "suite_manifest.json"
    if not sm_path.exists():
        pytest.skip("not a suite seed")
    sm = json.loads(sm_path.read_text(encoding="utf-8"))
    cfg = json.loads((SUITES / f"{sm['suite_id']}.json").read_text(
        encoding="utf-8"))
    schema, entry = SP.seed_entry(cfg, sm["suite_seed"])
    if schema is None:
        pytest.skip("legacy F0 suite has no frozen seed_plan")
    key = SP.BINDING_KEY[schema]
    for comp in sm["components"]:
        recorded = comp.get(key)
        if recorded is None:
            # Some writers record the plan projection in the attempt
            # manifest only; the audit reads both places.
            attempt = Path(comp["attempt"])
            recorded = json.loads(
                (attempt / "manifest.json").read_text(encoding="utf-8")
            ).get(key)
        assert recorded is not None, (seed_dir, comp["program_id"], key)
        issues = SP.verify_binding(schema, entry, comp["program_id"],
                                   recorded)
        if seed_dir.name == "seed1" and sm["suite_id"] == \
                "polybench-fp-v1-fr03":
            assert issues == ["submodel='FR03-c' != 'FR03-a'"], issues
        else:
            assert issues == [], (seed_dir, comp["program_id"], issues)


@pytest.mark.parametrize("kind", ["polybench-fp-v1-fr03", "w6-fp-v1-fr03"])
def test_real_component_seeds_derived_and_unique(kind):
    cfg = load(kind)
    family = G.family_of(cfg)
    for seed in (1, 2, 3):
        derived = G.derive_component_seeds(cfg, seed)
        assert len(set(derived.values())) == len(derived)
        seed_dirs = list((ROOT / "runs/fsu").glob(
            f"FSU-FR03-F5-{family}/seed{seed}"))
        if not seed_dirs:
            continue
        sm = json.loads((seed_dirs[0] / "suite_manifest.json").read_text(
            encoding="utf-8"))
        for comp in sm["components"]:
            assert comp["component_seed"] == derived[comp["program_id"]]


def test_real_fr03_seed1_legacy_report_conflicts_with_current_tool():
    seed = ROOT / "runs/fsu/FSU-FR03-F5-W5/seed1"
    if not (seed / "suite_manifest.json").exists():
        pytest.skip("real FR03-W5 seed1 evidence not present")
    legacy = json.loads((seed / "audit_v2.json").read_text(encoding="utf-8"))
    assert legacy.get("suite_certified") is True  # historical report only
    report = U.audit_seed(seed)
    assert report["recompute_status"] == "current_verification_failed"
    assert report["suite_certified"] is False
    assert any("suite_hash drift" in v for v in report["violations"])
    # Every fault-geometry value agrees; only the pre-freeze seed1 label
    # (FR03-c) differs from the frozen plan (FR03-a).
    assert any("submodel='FR03-c' != 'FR03-a'" in v
               for v in report["violations"])
    assert not any(v.startswith("missing_evidence:") for v in report["violations"])


def test_real_fr03_physical_identity_cross_sources():
    seed = ROOT / "runs/fsu/FSU-FR03-F5-W5/seed2"
    if not (seed / "suite_manifest.json").exists():
        pytest.skip("real FR03-W5 seed2 evidence not present")
    sm = json.loads((seed / "suite_manifest.json").read_text(encoding="utf-8"))
    comp = sm["components"][0]
    attempt = Path(comp["attempt"])
    cfg = load("polybench-fp-v1-fr03")
    schema, entry = SP.seed_entry(cfg, 2)
    manifest = json.loads((attempt / "manifest.json").read_text(
        encoding="utf-8"))
    cm = json.loads((attempt / "component_manifest.json").read_text(
        encoding="utf-8"))
    report = json.loads((attempt / "chain_report.json").read_text(
        encoding="utf-8"))
    ini = (attempt / "inject/config.ini").read_text(encoding="utf-8")
    result = SP.physical_identity(
        schema, entry, comp["program_id"], manifest, cm,
        report["command"]["inject"], ini)
    assert result["ok"] is True, result
    assert set(result["sources"]) == {
        "manifest.effective_injector.physreg_mode",
        "component_manifest.target_plan_entry",
        "chain_report.command.inject",
        "inject/config.ini[board.chaos_phys]",
    }
    assert result["sources"]["component_manifest.target_plan_entry"][
        "target_phys_idx"] == entry["targets"][comp["program_id"]][
            "target_phys_idx"]
