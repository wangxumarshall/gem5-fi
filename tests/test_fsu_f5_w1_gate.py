"""tests/test_fsu_f5_w1_gate.py — FP06-F5-W1 filters, pre-registration, gate.

No gem5 is started here. The tests cover:
  * schema + runtime validator support for op_classes/reg_class/F5 fields;
  * runner CLI construction for the new filters (and fail-closed rejection);
  * the three formal seed manifests are fully pre-registered and distinct;
  * the gate tool's evidence checks fail closed on forged/missing data;
  * gate artifacts are forced under runs/fsu-gates, never runs/fsu.
"""
import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import fsu_f5_w1_gate as G  # noqa: E402
import fsu_prop_fields as P  # noqa: E402
import fsu_seed_runner as R  # noqa: E402
import manifest_validate as MV  # noqa: E402

CONFIG = ROOT / "configs/fsu"
SEEDS = [CONFIG / f"FSU-FP06-F5-W1-seed{i}.json" for i in (1, 2, 3)]
GATES = [CONFIG / f"FSU-FP06-F5-W1-{name}.json" for name in (
    "FP32-SIGN-GATE", "FP64-SIGN-GATE", "FP32-MANT-GATE",
    "PRECISION-MISMATCH-GATE")]


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def base_manifest(fpu_mode=None):
    return {
        "schema_version": "arm-chaos-fi/v1",
        "run_id": "unit-test",
        "source": {"chaos_commit": "a", "gem5_commit": "b"},
        "platform": {"isa": "ARM64", "mode": "SE", "cpu_model": "O3",
                     "config_family": "C3"},
        "workload": {"binary_sha256": "0" * 64},
        "trigger": {"mode": "event", "value": 0},
        "target": {"layer": "physical", "component": "fsu",
                   "instance": "f0"},
        "fault": {"model": "stuck_at_zero", "duration_events": 1,
                  "stage": "no_protection_model",
                  "fpu_mode": fpu_mode or {}},
        "rng": {"master_seed": 1, "selection_seed": 1},
        "limits": {"max_faults": 1},
    }


def evt(**kw):
    d = {k: "" for k in P.PROP_EVT_FIELDS}
    d.update(kw)
    return d


def f5_events(mask="0x0000000080000000", polarity="0"):
    """A small but complete FP32-sign permanent-fault stream."""
    common = dict(run_id="GATE", sample_run_id="s1", fault_id="1",
                  model_id="FP06", submodel="FP06-a", unit="FSU Pipe",
                  freq="F5", load_id="W1", precision="fp32",
                  lane_width="32", lane_offset="0", field="sign",
                  fault_mask=mask, fixed_mask=mask, stuck_polarity=polarity,
                  reg_class="vec", op_class="FloatMult",
                  decoded_kind="scalar_vfp", decoded_precision="fp32",
                  decoded_element_width="32", decoded_lanes="1",
                  decoded_reliable="1", manifest_precision="fp32",
                  manifest_lane_width="32", manifest_lane_offset="0",
                  precision_match="1", lane_match="1")
    root = evt(kind="fault_installed", event_id="0", parent_event_id="",
               tick="100", install_event="0", dyn_inst_seq="10",
               first_eligible_sn="10", **common)
    carrier = evt(kind="carrier_state", event_id="1", parent_event_id="0",
                  tick="100", install_event="0", **common)
    exp1 = evt(kind="exposure", event_id="2", parent_event_id="1",
               tick="101", install_event="0", exposure_id="1",
               exposure_count="1", activated="0",
               activated_exposure_count="0", last_exposure_sn="11",
               correct_before="0x00000000", stuck_after="0x00000000",
               exposures_total="1", exposures_sampled="1",
               exposures_dropped="0", **common)
    exp2 = evt(kind="exposure", event_id="3", parent_event_id="1",
               tick="102", install_event="0", exposure_id="2",
               exposure_count="2", activated="1",
               activated_exposure_count="1", first_activated_sn="12",
               last_exposure_sn="12", correct_before="0x80000000",
               stuck_after="0x00000000", exposures_total="2",
               exposures_sampled="2", exposures_dropped="0", **common)
    commit = evt(kind="commit", event_id="4", parent_event_id="3",
                 tick="103", install_event="0", **common)
    end = evt(kind="chain_end", event_id="5", parent_event_id="4",
              tick="104", install_event="0", exposure_count="2",
              activated_exposure_count="1", exposures_total="2",
              exposures_sampled="2", exposures_dropped="0",
              terminal="committed", outcome="committed", **common)
    return [root, carrier, exp1, exp2, commit, end]


def spec_for(gate_id):
    return next(s for s in G.GATE_SPECS if s["id"] == gate_id)


def checks_ok(checks):
    return all(c["ok"] for c in checks)


def failures(checks):
    return [c["check"] for c in checks if not c["ok"]]


def test_schema_declares_filters_and_f5_fields():
    schema = load(ROOT / "schemas/manifest.schema.json")
    fpu = schema["properties"]["fault"]["properties"]["fpu_mode"][
        "properties"]
    assert fpu["op_classes"]["type"] == "array"
    assert set(fpu["op_classes"]["items"]["enum"]) == set(MV.FPU_OP_CLASSES)
    assert set(fpu["reg_class"]["enum"]) == {"any", "vec", "float",
                                             "vec_elem"}
    for name in ("permanent_stuck", "stuck_polarity", "f5_warmup",
                 "f5_sample_limit", "f5_keep_first_last_n"):
        assert name in fpu, name
    assert fpu["stuck_polarity"]["enum"] == [-1, 0, 1]


def test_manifest_validator_accepts_good_filters_and_rejects_bad():
    seed = load(SEEDS[0])
    good = base_manifest(copy.deepcopy(seed["injector"]["fpu_mode"]))
    ok, errs = MV.validate(good)
    assert ok, errs

    bad = base_manifest({"op_classes": ["FloatAdd", "BogusOp"]})
    ok, errs = MV.validate(bad)
    assert not ok and any("op_classes" in e for e in errs)

    bad = base_manifest({"reg_class": "gpr"})
    ok, errs = MV.validate(bad)
    assert not ok and any("reg_class" in e for e in errs)

    bad = base_manifest({"stuck_polarity": 2})
    ok, errs = MV.validate(bad)
    assert not ok and any("stuck_polarity" in e for e in errs)

    bad = base_manifest({"f5_warmup": -1})
    ok, errs = MV.validate(bad)
    assert not ok and any("f5_warmup" in e for e in errs)

    bad = base_manifest({"permanent_stuck": "yes"})
    ok, errs = MV.validate(bad)
    assert not ok and any("permanent_stuck" in e for e in errs)


def test_runner_builds_filter_flags_for_census_and_injection():
    manifest = load(SEEDS[0])
    cmd = R.build_cmd(manifest, Path("/tmp/out"), 1, 0, False,
                      Path("/bin/true"), Path("cfg.py"), ROOT)
    assert "--fpu_op_classes" in cmd
    assert cmd[cmd.index("--fpu_op_classes") + 1] == ",".join(G.SCALAR_OPS)
    assert cmd[cmd.index("--fpu_reg_class") + 1] == "vec"
    assert "--fpu_decode_guard" in cmd
    ccmd = R.build_cmd(manifest, Path("/tmp/out"), 1, None, True,
                       Path("/bin/true"), Path("cfg.py"), ROOT)
    assert ccmd[ccmd.index("--fpu_op_classes") + 1] == ",".join(G.SCALAR_OPS)
    assert ccmd[ccmd.index("--fpu_reg_class") + 1] == "vec"


def test_runner_keeps_legacy_mode_when_filters_are_absent():
    manifest = load(SEEDS[0])
    legacy = copy.deepcopy(manifest)
    legacy["injector"]["fpu_mode"].pop("op_classes")
    legacy["injector"]["fpu_mode"].pop("reg_class")
    cmd = R.build_cmd(legacy, Path("/tmp/out"), 1, 0, False,
                      Path("/bin/true"), Path("cfg.py"), ROOT)
    assert "--fpu_op_classes" not in cmd
    assert "--fpu_reg_class" not in cmd
    # Explicit "any" is the same legacy predicate and emits no restriction.
    legacy["injector"]["fpu_mode"]["reg_class"] = "any"
    cmd = R.build_cmd(legacy, Path("/tmp/out"), 1, 0, False,
                      Path("/bin/true"), Path("cfg.py"), ROOT)
    assert "--fpu_reg_class" not in cmd


def test_runner_rejects_unknown_opclass_and_regclass():
    manifest = load(SEEDS[0])
    bad = copy.deepcopy(manifest)
    bad["injector"]["fpu_mode"]["op_classes"] = ["FloatAdd", "MadeUp"]
    with pytest.raises(ValueError, match="unknown fpu_mode.op_classes"):
        R.build_cmd(bad, Path("/tmp/out"), 1, 0, False, Path("/bin/true"),
                    Path("cfg.py"), ROOT)
    bad = copy.deepcopy(manifest)
    bad["injector"]["fpu_mode"]["reg_class"] = "int"
    with pytest.raises(ValueError, match="unknown fpu_mode.reg_class"):
        R.build_cmd(bad, Path("/tmp/out"), 1, 0, False, Path("/bin/true"),
                    Path("cfg.py"), ROOT)
    bad = copy.deepcopy(manifest)
    bad["injector"]["fpu_mode"]["op_classes"] = ["FloatAdd", "FloatAdd"]
    with pytest.raises(ValueError, match="duplicate"):
        R.build_cmd(bad, Path("/tmp/out"), 1, 0, False, Path("/bin/true"),
                    Path("cfg.py"), ROOT)


def test_three_formal_seeds_are_frozen_and_distinct():
    identities = set()
    for path in SEEDS:
        m = load(path)
        assert m["run_id"] == "FSU-FP06-F5-W1"
        assert m["config_profile"] == "B0"
        fpu = m["injector"]["fpu_mode"]
        pre = m["pre_registration"]
        assert fpu["decode_guard"] is True
        assert fpu["permanent_stuck"] is True
        assert fpu["reg_class"] == "vec"
        assert fpu["op_classes"] == G.SCALAR_OPS
        assert m["injector"]["max_faults"] == 1
        assert m["injector"]["probability"] == 1.0
        assert fpu["f5_warmup"] == 1024
        assert fpu["f5_sample_limit"] == 1024
        assert fpu["f5_keep_first_last_n"] == 256
        # Frozen pre-registration == runtime block.
        assert pre["precision"] == fpu["precision"]
        assert pre["lane_width"] == fpu["lane_width"]
        assert pre["polarity"] == fpu["stuck_polarity"]
        assert G._hex_int(pre["mask"]) == G._hex_int(
            m["injector"]["fault_mask"])
        assert pre["op_classes"] == fpu["op_classes"]
        assert pre["reg_class"] == fpu["reg_class"]
        identities.add((m["submodel"], fpu["precision"],
                        G._hex_int(m["injector"]["fault_mask"]),
                        fpu["stuck_polarity"]))
    assert identities == {
        ("FP06-a", "fp32", 0x80000000, 0),
        ("FP06-b", "fp64", 0x8000000000000000, 1),
        ("FP06-c", "fp32", 0x007f8000, 0),
    }
    # The three formal seeds differ in mask/polarity/precision.
    assert len({x[1:] for x in identities}) == 3


def test_gate_manifests_are_non_formal_and_pre_registered():
    runids = load(ROOT / "docs/gem5-fi/fsu/runids.json")
    items = runids.get("runids", runids)
    registered = {x["RunID"] for x in items}
    for path, spec in zip(GATES, G.GATE_SPECS):
        m = load(path)
        assert m["run_id"].endswith("-GATE")
        assert m["run_id"] not in registered
        assert m["gate"] is True
        assert m["counts_toward_519"] is False
        pre = m["pre_registration"]
        assert G._hex_int(pre["mask"]) == spec["mask"]
        assert pre["polarity"] == spec["polarity"]
        assert pre["precision"] == spec["precision"]
        assert pre["op_classes"] == spec["op_classes"]
        assert pre["reg_class"] == spec["reg_class"]
        assert m["injector"]["fpu_mode"]["decode_guard"] is True
        assert m["workload"]["binary"].endswith(spec["workload"])


def test_gate_default_outdir_is_under_runs_fsu_gates():
    default = G.DEFAULT_OUT.resolve()
    gate_root = (ROOT / "runs/fsu-gates").resolve()
    assert gate_root == default or gate_root in default.parents
    assert (ROOT / "runs/fsu").resolve() not in default.parents


def test_gate_main_rejects_formal_runs_root_without_running():
    rc = G.main(["--outdir", str(ROOT / "runs/fsu/forbidden-gate")])
    assert rc == 2


def test_analyze_f5_events_accepts_a_complete_stream():
    checks = G.analyze_f5_events(f5_events(), spec_for("FP32-SIGN"))
    assert checks_ok(checks), failures(checks)


@pytest.mark.parametrize("mutation", [
    "missing_chain_end",
    "wrong_mask",
    "second_fault_id",
    "wrong_polarity",
    "forged_activated",
    "foreign_opclass",
    "wrong_decoded_precision",
    "sampled_count_mismatch",
])
def test_analyze_f5_events_fails_closed_on_forged_evidence(mutation):
    events = copy.deepcopy(f5_events())
    if mutation == "missing_chain_end":
        events = [e for e in events if e["kind"] != "chain_end"]
    elif mutation == "wrong_mask":
        events[0]["fault_mask"] = "0x0000000000000001"
    elif mutation == "second_fault_id":
        events[2]["fault_id"] = "2"
    elif mutation == "wrong_polarity":
        events[0]["stuck_polarity"] = "1"
    elif mutation == "forged_activated":
        # correct_before sign=0 under SA0 means NOT activated.
        events[2]["activated"] = "1"
    elif mutation == "foreign_opclass":
        events[2]["op_class"] = "SimdFloatAdd"
    elif mutation == "wrong_decoded_precision":
        events[2]["decoded_precision"] = "fp64"
    elif mutation == "sampled_count_mismatch":
        events[-1]["exposures_sampled"] = "1"
    checks = G.analyze_f5_events(events, spec_for("FP32-SIGN"))
    assert not checks_ok(checks), mutation


def test_parse_census_conservation_and_allowlist():
    text = "\n".join([
        "CHAOS_ELIGIBLE_COUNT=10",
        "CHAOS_ELIGIBLE_OPCLASS FloatAdd=6",
        "CHAOS_ELIGIBLE_OPCLASS FloatMultAcc=4",
        "CHAOS_ELIGIBLE_REGCLASS vec=10",
    ])
    census = G.parse_census(text)
    assert census["eligible"] == 10
    assert census["opclass"] == {"FloatAdd": 6, "FloatMultAcc": 4}
    assert census["regclass"] == {"vec": 10}
    spec = spec_for("FP32-SIGN")
    assert checks_ok(G.census_checks(census, spec))

    bad = G.parse_census(text.replace(
        "CHAOS_ELIGIBLE_REGCLASS vec=10",
        "CHAOS_ELIGIBLE_REGCLASS vec=9"))
    assert not checks_ok(G.census_checks(bad, spec))

    foreign = G.parse_census(text.replace(
        "CHAOS_ELIGIBLE_OPCLASS FloatMultAcc=4",
        "CHAOS_ELIGIBLE_OPCLASS SimdFloatAdd=4"))
    assert not checks_ok(G.census_checks(foreign, spec))


def test_precision_mismatch_census_requires_zero_and_precision_reason():
    spec = spec_for("PRECISION-MISMATCH")
    text = "\n".join([
        "CHAOS_ELIGIBLE_COUNT=0",
        "CHAOS_DECODE_REJECTS=123",
        "CHAOS_DECODE_REJECT_REASON precision_mismatch=123",
    ])
    census = G.parse_census(text)
    assert checks_ok(G.census_checks(census, spec))
    # A zero caused by a missing opClass match is NOT the precision gate.
    no_reason = G.parse_census("CHAOS_ELIGIBLE_COUNT=0")
    assert not checks_ok(G.census_checks(no_reason, spec))
    non_zero = G.parse_census("CHAOS_ELIGIBLE_COUNT=5\n"
                              "CHAOS_ELIGIBLE_OPCLASS FloatMultAcc=5\n"
                              "CHAOS_ELIGIBLE_REGCLASS vec=5\n"
                              "CHAOS_DECODE_REJECT_REASON precision_mismatch=9")
    assert not checks_ok(G.census_checks(non_zero, spec))


def test_gate_refuses_a_drifted_manifest_before_running_gem5(tmp_path):
    spec = spec_for("FP32-SIGN")
    manifest_path = tmp_path / spec["manifest"]
    manifest_path.parent.mkdir(parents=True)
    drifted = load(GATES[0])
    drifted["injector"]["fault_mask"] = "0x0000000000000001"
    manifest_path.write_text(json.dumps(drifted), encoding="utf-8")

    def must_not_run(cmd, timeout):
        raise AssertionError("gem5 must not run after pre-registration drift")

    rec = G.run_permanent_gate(
        spec, tmp_path / "out", Path("/bin/true"),
        Path("configs/se/ooo_proxy.py"), tmp_path, 5, runner=must_not_run)
    assert rec["ok"] is False
    assert rec["status"] == "not_run"
    assert any("pre-registered mask" in f for f in rec["failures"])


def test_mismatch_gate_passes_on_zero_eligible_precision_reason(tmp_path):
    spec = spec_for("PRECISION-MISMATCH")
    b0 = [
        "[system.cpu]",
        "type=BaseO3CPU",
        "fetchWidth=3",
        "decodeWidth=3",
        "renameWidth=3",
        "dispatchWidth=6",
        "issueWidth=8",
        "wbWidth=8",
        "commitWidth=8",
        "numROBEntries=40",
        "numPhysIntRegs=128",
        "numPhysFloatRegs=192",
        "numPhysVecRegs=48",
        "LQEntries=16",
        "SQEntries=16",
        "fetchBufferSize=16",
        "squashWidth=8",
        "",
        "[system.cpu.instQueues]",
        "type=IQUnit",
        "numEntries=32",
        "",
    ]

    def fake(cmd, timeout):
        outdir = Path(cmd[cmd.index("-d") + 1])
        outdir.mkdir(parents=True, exist_ok=True)
        (outdir / "config.ini").write_text("\n".join(b0), encoding="utf-8")
        (outdir / "fpu_injections.log").write_text(
            "CHAOS_ELIGIBLE_COUNT=0\n"
            "CHAOS_DECODE_REJECTS=12\n"
            "CHAOS_DECODE_REJECT_REASON precision_mismatch=12\n",
            encoding="utf-8")
        return 0, "", "", False

    rec = G.run_mismatch_gate(
        spec, tmp_path / "out", Path("/bin/true"),
        Path("configs/se/ooo_proxy.py"), G.ROOT, 5, runner=fake)
    assert rec["ok"] is True, rec["failures"]
    assert rec["eligible"] == 0
    assert all(k in G.SCALAR_OPS for k in rec["opclass_census"])


def test_prereg_checks_detect_manifest_drift():
    path = GATES[0]
    spec = spec_for("FP32-SIGN")
    assert checks_ok(G.prereg_checks(load(path), spec))
    drifted = load(path)
    drifted["injector"]["fault_mask"] = "0x0000000000000001"
    assert not checks_ok(G.prereg_checks(drifted, spec))
    drifted = load(path)
    drifted["injector"]["fpu_mode"]["op_classes"] = ["FloatAdd"]
    assert not checks_ok(G.prereg_checks(drifted, spec))
