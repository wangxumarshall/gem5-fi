"""tests/test_fsu_suite_audit.py — unified suite audit (W5/W6).

Each fixture is a synthetic but real-evidence suite seed: component attempts
are produced by fsu_seed_runner with a fake gem5 runner, then component
manifests / oracle arrays / evidence manifests are added. The audit itself
still recomputes the chain and the component audit from the raw stream, so
these tests exercise the real tool, not a stub.
"""
import gzip
import hashlib
import json
import sys
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import fsu_prop_fields as P  # noqa: E402
import fsu_seed_audit as A  # noqa: E402
import fsu_seed_runner as R  # noqa: E402
import fsu_suite as S  # noqa: E402
import fsu_suite_audit as U  # noqa: E402
import fsu_w6_suite as WS  # noqa: E402

SCHEMA = json.loads(
    (ROOT / "schemas/fsu_suite_audit.schema.json").read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evt(**kw):
    d = {k: "" for k in P.PROP_EVT_FIELDS}
    d.update(kw)
    return P.PREFIX + " " + " ".join(f"{k}={d[k]}" for k in P.PROP_EVT_FIELDS)


def chain(run_id, sample_run_id):
    b = dict(run_id=run_id, sample_run_id=sample_run_id, fault_id="1",
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
        evt(kind="operand_read", event_id="2", parent_event_id="1", tick="102",
            activated="1", **b),
        evt(kind="execute", event_id="3", parent_event_id="2", tick="103", **b),
        evt(kind="prf_writeback", event_id="4", parent_event_id="3",
            tick="104", **b),
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


def _write_evidence(attempt: Path):
    files = [
        "manifest.json", "chain_report.json", "oracle.json",
        "oracle_elements.json", "inject/array.bin", "component_manifest.json",
        "stats.txt", "run.out", "inject/prop_evt.txt.gz",
    ]
    hashes = {rel: _sha(attempt / rel) for rel in files
              if (attempt / rel).exists()}
    (attempt / "evidence_sha256.json").write_text(
        json.dumps(hashes, indent=2), encoding="utf-8")


def _make_component(tmp_path, suite_cfg, suite_hash, run_id, pid, index,
                    component_seed, oracle="SDC"):
    wl = tmp_path / "wl"
    wl.write_text("#!/bin/sh\nexit 0\n")
    wl.chmod(0o755)
    gem5 = tmp_path / "gem5"
    gem5.write_text("#!/bin/sh\nexit 0\n")
    gem5.chmod(0o755)
    manifest = {
        "run_id": run_id,
        "model_id": "FP04", "unit": "FSU Pipe", "freq": "F0",
        "load_id": str(suite_cfg.get("load_id") or "W5"),
        "submodel": "FP04-c",
        "workload": {"binary": str(wl), "golden": "a" * 64,
                     "oracle_kind": "array_hash"},
        "injector": {"component": "fsu", "max_faults": 1, "first_clock": 0,
                     "fpu_mode": {"bitseg": "mant_lo"}},
        "limits": {"timeout_s": 10},
    }
    mp = tmp_path / f"manifest-{pid}.json"
    mp.write_text(json.dumps(manifest), encoding="utf-8")
    comp_seed_dir = (tmp_path / "seed") / "components" / pid / run_id / \
        f"seed{component_seed}"
    res = R.run_seed(
        mp, component_seed, out_root=tmp_path / "runs", gem5=gem5,
        root=ROOT, runner=fake_runner(chain(run_id, f"s{component_seed}")),
        seed_dir=comp_seed_dir,
        component={"suite_id": suite_cfg["suite_id"], "program_id": pid},
        write_authoritative=False, copy_to_complete=False)
    assert res["status"] == "admitted", res
    attempt = Path(res["attempt"])
    A.write_audit(attempt)
    (attempt / "oracle_elements.json").write_text(
        json.dumps({"ok": True, "program_id": pid}), encoding="utf-8")
    (attempt / "inject/array.bin").write_bytes(b"ARRAY")
    audit = json.loads((attempt / "audit.json").read_text(encoding="utf-8"))
    cm = {
        "suite_id": suite_cfg["suite_id"],
        "suite_version": suite_cfg["suite_version"],
        "suite_hash": suite_hash,
        "suite_seed": 1,
        "program_id": pid,
        "program_index": index,
        "program_count": len(suite_cfg["program_order"]),
        "component_seed_policy_version": "w5-component-seed-v1",
        "component_seed": component_seed,
        "component_attempt": int(attempt.name.split("-")[1]),
        "component_manifest_sha256": _sha(attempt / "manifest.json"),
        "component_binary_sha256": "b" * 64,
        "component_source_sha256": "c" * 64,
        "component_golden_sha256": "d" * 64,
        "component_status": "admitted",
        "component_eligible": 100,
        "component_activated": 1,
        "component_faults": 1,
        "component_terminal": "full",
        "component_oracle": oracle,
        "component_audit_ok": audit.get("ok") is True,
        "component_certified": audit.get("certified") is True,
        "attempt": str(attempt),
    }
    (attempt / "component_manifest.json").write_text(
        json.dumps(cm, indent=2), encoding="utf-8")
    _write_evidence(attempt)
    return cm


def make_suite(tmp_path, kind="w5", legacy_audit=True):
    if kind == "w5":
        cfg_path = ROOT / "configs/fsu/suites/polybench-fp-v1.json"
        hash_fn = S.compute_suite_hash
        run_id = "FSU-FP04-F0-W5"
    else:
        cfg_path = ROOT / "configs/fsu/suites/w6-fp-v1.json"
        hash_fn = WS.compute_suite_hash
        run_id = "FSU-FP04-F0-W6"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    suite_hash = hash_fn(cfg)
    order = list(cfg["program_order"])
    seed_dir = tmp_path / "suite"
    comps = []
    for idx, pid in enumerate(order):
        comps.append(_make_component(
            tmp_path, cfg, suite_hash, run_id, pid, idx,
            component_seed=1000 + idx))
    sm = {
        "run_id": run_id,
        "suite_id": cfg["suite_id"],
        "suite_version": cfg["suite_version"],
        "suite_hash": suite_hash,
        "suite_seed": 1,
        "program_order": order,
        "program_count": len(order),
        "component_seed_policy_version": "w5-component-seed-v1",
        "components": comps,
    }
    if kind == "w5":
        sm["suite"] = cfg
    seed_dir.mkdir(parents=True, exist_ok=True)
    (seed_dir / "suite_manifest.json").write_text(
        json.dumps(sm, indent=2), encoding="utf-8")
    (seed_dir / "suite_report.json").write_text(json.dumps({
        "run_id": run_id, "suite_id": cfg["suite_id"],
        "suite_version": cfg["suite_version"], "suite_hash": suite_hash,
        "suite_seed": 1, "program_order": order,
        "program_count": len(order), "component_run_count": len(order),
        "formal_suite_seed_count": 1,
        "suite_status": "admitted", "suite_admitted": True,
    }, indent=2), encoding="utf-8")
    if legacy_audit:
        (seed_dir / "audit.json").write_text(json.dumps({
            "suite_id": cfg["suite_id"], "suite_hash": suite_hash,
            "suite_seed": 1, "run_id": run_id,
            "checks": [{"check": "legacy", "ok": True}], "failures": [],
            "ok": True,
        }, indent=2), encoding="utf-8")
    return seed_dir, cfg, suite_hash


def test_w5_normal_certified(tmp_path):
    seed_dir, _, suite_hash = make_suite(tmp_path, "w5")
    report = U.audit_seed(seed_dir)
    jsonschema.validate(report, SCHEMA)
    assert report["suite_execution_complete"] is True
    assert report["suite_evidence_valid"] is True
    assert report["suite_certified"] is True, report["violations"]
    assert report["formal_seed_contribution"] == 1
    assert report["component_count"] == 5
    assert report["suite_hash"] == suite_hash
    assert report["legacy_audit"]["legacy"] is True
    assert "certified" in report["legacy_audit"]["fields_missing"]
    assert "certified" not in report["legacy_audit"]["raw"]


def test_w6_normal_certified(tmp_path):
    seed_dir, _, _ = make_suite(tmp_path, "w6")
    report = U.audit_seed(seed_dir)
    jsonschema.validate(report, SCHEMA)
    assert report["suite_certified"] is True, report["violations"]
    assert report["expected_programs"] == list(WS.W6_PROGRAM_ORDER)
    assert report["component_count"] == 3


def test_missing_program_fails(tmp_path):
    seed_dir, _, _ = make_suite(tmp_path, "w5")
    sm_path = seed_dir / "suite_manifest.json"
    sm = json.loads(sm_path.read_text(encoding="utf-8"))
    sm["components"] = sm["components"][:4]
    sm_path.write_text(json.dumps(sm), encoding="utf-8")
    report = U.audit_seed(seed_dir)
    assert report["suite_certified"] is False
    assert any("missing program: jacobi-2d" in v
               for v in report["violations"])


def test_duplicate_program_fails(tmp_path):
    seed_dir, _, _ = make_suite(tmp_path, "w5")
    sm_path = seed_dir / "suite_manifest.json"
    sm = json.loads(sm_path.read_text(encoding="utf-8"))
    sm["components"][2] = json.loads(json.dumps(sm["components"][0]))
    sm_path.write_text(json.dumps(sm), encoding="utf-8")
    report = U.audit_seed(seed_dir)
    assert report["suite_certified"] is False
    assert any("duplicate program: gemm" in v for v in report["violations"])
    assert any("missing program: lu" in v for v in report["violations"])


def test_unexpected_program_fails(tmp_path):
    seed_dir, _, _ = make_suite(tmp_path, "w5")
    sm_path = seed_dir / "suite_manifest.json"
    sm = json.loads(sm_path.read_text(encoding="utf-8"))
    extra = json.loads(json.dumps(sm["components"][0]))
    extra["program_id"] = "not-a-polybench-program"
    sm["components"].append(extra)
    sm_path.write_text(json.dumps(sm), encoding="utf-8")
    report = U.audit_seed(seed_dir)
    assert report["suite_certified"] is False
    assert any("unexpected program" in v for v in report["violations"])


def test_component_binding_drift_fails(tmp_path):
    seed_dir, _, _ = make_suite(tmp_path, "w5")
    sm_path = seed_dir / "suite_manifest.json"
    sm = json.loads(sm_path.read_text(encoding="utf-8"))
    sm["components"][0]["suite_seed"] = 2
    sm["components"][0]["suite_hash"] = "0" * 64
    sm_path.write_text(json.dumps(sm), encoding="utf-8")
    report = U.audit_seed(seed_dir)
    assert report["suite_certified"] is False
    assert any("component suite_seed drift" in v
               for v in report["violations"])
    assert any("component suite_hash drift" in v
               for v in report["violations"])


def test_suite_hash_drift_fails(tmp_path):
    seed_dir, _, _ = make_suite(tmp_path, "w5")
    sm_path = seed_dir / "suite_manifest.json"
    sm = json.loads(sm_path.read_text(encoding="utf-8"))
    sm["suite_hash"] = "0" * 64
    sm_path.write_text(json.dumps(sm), encoding="utf-8")
    report = U.audit_seed(seed_dir)
    assert report["suite_certified"] is False
    assert any("suite_hash drift" in v for v in report["violations"])


def test_tampered_component_hash_fails(tmp_path):
    seed_dir, _, _ = make_suite(tmp_path, "w5")
    sm = json.loads((seed_dir / "suite_manifest.json").read_text(
        encoding="utf-8"))
    attempt = Path(sm["components"][0]["attempt"])
    with open(attempt / "chain_report.json", "a", encoding="utf-8") as f:
        f.write("TAMPER\n")
    report = U.audit_seed(seed_dir)
    assert report["suite_evidence_valid"] is False
    assert report["suite_certified"] is False
    assert any("SHA-256 mismatch: chain_report.json" in v
               for v in report["violations"])


def test_masked_component_audit_failure_fails(tmp_path):
    seed_dir, _, _ = make_suite(tmp_path, "w5")
    sm = json.loads((seed_dir / "suite_manifest.json").read_text(
        encoding="utf-8"))
    attempt = Path(sm["components"][0]["attempt"])
    # Break the raw stream and refresh its evidence hash so the blind hash
    # check passes; the recomputed chain/audit must still catch it.
    prop = attempt / "inject/prop_evt.txt.gz"
    text = gzip.decompress(prop.read_bytes()).decode()
    prop.write_bytes(gzip.compress(
        "\n".join(l for l in text.splitlines()
                  if "event_id=4 " not in l).encode() + b"\n"))
    evidence = json.loads((attempt / "evidence_sha256.json").read_text(
        encoding="utf-8"))
    evidence["inject/prop_evt.txt.gz"] = _sha(prop)
    (attempt / "evidence_sha256.json").write_text(
        json.dumps(evidence), encoding="utf-8")
    # Stored audit still claims success: the suite must not inherit it.
    stored = json.loads((attempt / "audit.json").read_text(encoding="utf-8"))
    assert stored["ok"] is True
    report = U.audit_seed(seed_dir)
    assert report["suite_certified"] is False
    assert any("stored audit.ok=True != recomputed False" in v
               for v in report["violations"])


def test_legacy_audit_read_only_and_migrate(tmp_path, capsys):
    seed_dir, _, _ = make_suite(tmp_path, "w5")
    legacy_path = seed_dir / "audit.json"
    before = legacy_path.read_bytes()
    out = tmp_path / "migrated.json"
    rc = U.main([str(seed_dir), "--migrate-report", str(out), "--quiet"])
    assert rc == 0
    assert out.exists()
    assert legacy_path.read_bytes() == before
    migrated = json.loads(out.read_text(encoding="utf-8"))
    assert migrated["schema_version"] == U.SCHEMA_VERSION
    assert migrated["legacy_audit"]["legacy"] is True
    assert "certified" in migrated["legacy_audit"]["fields_missing"]
    # Refuse to overwrite legacy evidence.
    rc = U.main([str(seed_dir), "--migrate-report", str(legacy_path),
                 "--quiet"])
    assert rc == 2
    assert legacy_path.read_bytes() == before


def test_legacy_audit_ok_mismatch_is_reported(tmp_path):
    seed_dir, _, _ = make_suite(tmp_path, "w5")
    audit_path = seed_dir / "audit.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    audit["ok"] = False
    audit_path.write_text(json.dumps(audit), encoding="utf-8")
    report = U.audit_seed(seed_dir)
    assert report["suite_evidence_valid"] is False
    assert any("legacy suite audit ok disagrees" in v
               for v in report["violations"])
