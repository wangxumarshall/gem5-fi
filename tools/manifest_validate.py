#!/usr/bin/env python3
"""Dependency-free (stdlib-only) manifest validator for the ARM64 CHAOS SDC
fault-injection tool (design doc §1.6, §9.2).

WHY THIS EXISTS: jsonschema is NOT installed on this host (pip offline, 403),
and runner.py degrades to "skipping schema check" silently when it's absent.
A v2 schema FILE alone is therefore useless here — it would be silently
skipped at runtime, defeating §1.6. This validator is the runtime ENFORCER:
it checks the subset of constraints runner.py actually relies on (required
keys, enum values, basic types) so a malformed or v2-but-unmapped manifest is
caught BEFORE gem5 runs. When jsonschema IS available (healthy machine or
future install), runner.py prefers it (full draft-07 enforcement); this is the
honest fallback that makes §1.6 enforced on every host.

This is NOT a full draft-07 parser — it hardcodes the enum/required/type
constraints as a frozen snapshot of the JSON schema's enforcement-relevant
subset. The JSON schema file (schemas/manifest.schema.json) stays as the
machine-readable, interoperable artifact; this module is the runtime spec of
what runner.py checks. A self-test (_selftest, run via `python3 -m
tools.manifest_validate`) keeps the two in sync against the sample manifests.

Usage:
  from tools.manifest_validate import validate
  ok, errs = validate(manifest_dict)
  if not ok: sys.exit("manifest validation FAILED: " + "; ".join(errs))
"""
import os, sys, json, yaml

REPO = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

# ---- enums / required (frozen snapshot of schemas/manifest.schema.json) ----

SCHEMA_VERSIONS = ("arm-chaos-fi/v1", "arm-chaos-fi/v2")
ISA = ("ARM64",)
MODES = ("SE", "FS")
CONFIG_FAMILIES = ("C0", "C1", "C2", "C0-CACHE", "C0-FS", "C2-FS", "C3", "C4-LSU")
TRIGGER_MODES = ("tick", "cycle", "pc", "committedInst", "event")
LAYERS = ("architectural", "physical")
# components runner.py MAPS today (gpr/physreg/memory/cache->l1d/lsqfwd->physreg):
COMPONENTS_MAPPED = ("gpr", "physreg", "memory", "l1d", "l1i", "l2",
                          "rat", "freelist", "rob", "iq", "exec", "fsu",
                          "lsq_fwd", "bpu", "addr_path", "decode", "l1d_fwd",
                          "exmon", "ras")
# v2 forward-declared (schema accepts; runner.py rejects until S1 mapping lands):
COMPONENTS_V2_DECLARED = ("l1_tlb", "l2_tlb", "sysreg", "ptw",
                          "l3", "noc", "coherence", "memctrl")
FAULT_MODELS = ("transient_bit_flip", "local_mbu", "intermittent_burst",
                "stuck_at_zero", "stuck_at_one", "legal_domain_sub",
                "delay_omission",
                # v1.1 Phase 8.4: recurring permanent fault (every eligible
                # event gets the same fixed mask; requires max_faults=0 —
                # runner.py enforces the pairing)
                "recurring_result_stuck")
FAULT_STAGES = ("raw_pre_protection", "post_check_escape",
                "metadata_or_checker", "no_protection_model")
ORACLE_KINDS = ("exact_hash", "invariant", "allowed_set",
                "array_hash", "per_element_diff", "fp_ulp")
# [FSU][FP06] fpu_mode eligibility filters. These mirror CHAOSFPU.cc /
# tools/fsu_seed_runner.py exactly; an unknown name is rejected before gem5.
FPU_OP_CLASSES = ("FloatAdd", "FloatCmp", "FloatCvt", "FloatMult",
                  "FloatMultAcc", "FloatDiv", "FloatMisc", "FloatSqrt",
                  "SimdFloatAdd", "SimdFloatAlu", "SimdFloatCmp",
                  "SimdFloatCvt", "SimdFloatMult", "SimdFloatMultAcc",
                  "SimdFloatDiv", "SimdFloatSqrt", "SimdFloatMisc")
FPU_REG_CLASSES = ("any", "vec", "float", "vec_elem")
FPU_F5_UINT_FIELDS = ("f5_warmup", "f5_sample_limit",
                      "f5_keep_first_last_n")

REQUIRED_TOP = ("schema_version", "run_id", "source", "platform", "workload",
                "trigger", "target", "fault", "rng", "limits")
REQUIRED_SOURCE = ("chaos_commit", "gem5_commit")
REQUIRED_PLATFORM = ("isa", "mode", "cpu_model", "config_family")
REQUIRED_WORKLOAD = ("binary_sha256",)
REQUIRED_TRIGGER = ("mode", "value")
REQUIRED_TARGET = ("layer", "component", "instance")
REQUIRED_FAULT = ("model", "duration_events", "stage")
REQUIRED_RNG = ("master_seed", "selection_seed")
REQUIRED_LIMITS = ("max_faults",)


def _is_int(v):
    # bool is a subclass of int in python — exclude it (a YAML true is not a
    # valid max_faults integer).
    return isinstance(v, int) and not isinstance(v, bool)


def _check_enum(val, allowed, path, errs):
    if val not in allowed:
        errs.append(f"{path}: '{val}' not in {list(allowed)}")


def _check_required(d, reqs, path, errs):
    for k in reqs:
        if k not in d:
            errs.append(f"{path}: missing required key '{k}'")


def _validate_fpu_mode(fpu, errs):
    """Validate the CHAOSFPU mode block (only keys that are present).

    [FSU][FP06] op_classes/reg_class and the F5 permanent-fault knobs are
    checked here because a wrong value would either panic inside gem5 or
    silently change the eligible stream. Legacy manifests without these keys
    are unaffected.
    """
    p = "fault.fpu_mode"
    if "op_classes" in fpu:
        oc = fpu["op_classes"]
        if not isinstance(oc, list):
            errs.append(f"{p}.op_classes: not an array")
        else:
            for i, name in enumerate(oc):
                if not isinstance(name, str):
                    errs.append(f"{p}.op_classes[{i}]: not a string")
                elif name not in FPU_OP_CLASSES:
                    errs.append(f"{p}.op_classes[{i}]: '{name}' not in "
                                f"{list(FPU_OP_CLASSES)}")
            if len(set(oc)) != len(oc):
                errs.append(f"{p}.op_classes: duplicate names")
    if "reg_class" in fpu:
        rc = fpu["reg_class"]
        if not isinstance(rc, str):
            errs.append(f"{p}.reg_class: not a string")
        elif rc not in FPU_REG_CLASSES:
            errs.append(f"{p}.reg_class: '{rc}' not in "
                        f"{list(FPU_REG_CLASSES)}")
    if "decode_guard" in fpu and not isinstance(fpu["decode_guard"], bool):
        errs.append(f"{p}.decode_guard: not a boolean")
    if "permanent_stuck" in fpu and not isinstance(
            fpu["permanent_stuck"], bool):
        errs.append(f"{p}.permanent_stuck: not a boolean")
    if "stuck_polarity" in fpu:
        sp = fpu["stuck_polarity"]
        if not _is_int(sp) or sp not in (-1, 0, 1):
            errs.append(f"{p}.stuck_polarity: must be -1, 0 or 1 (got {sp!r})")
    for key in FPU_F5_UINT_FIELDS:
        if key in fpu:
            v = fpu[key]
            if not _is_int(v) or v < 0:
                errs.append(f"{p}.{key}: must be an integer >= 0 (got {v!r})")


def validate(m):
    """Validate a manifest dict. Returns (ok, errors_list). ok=False iff any
    constraint fails; errors_list is a list of human-readable strings."""
    errs = []
    if not isinstance(m, dict):
        return False, ["manifest: top-level is not a dict"]

    # required top-level keys
    _check_required(m, REQUIRED_TOP, "manifest", errs)

    # schema_version (enum)
    if "schema_version" in m:
        _check_enum(m["schema_version"], SCHEMA_VERSIONS, "manifest.schema_version", errs)

    # source
    s = m.get("source", {})
    if isinstance(s, dict):
        _check_required(s, REQUIRED_SOURCE, "source", errs)

    # platform
    p = m.get("platform", {})
    if isinstance(p, dict):
        _check_required(p, REQUIRED_PLATFORM, "platform", errs)
        if "isa" in p:
            _check_enum(p["isa"], ISA, "platform.isa", errs)
        if "mode" in p:
            _check_enum(p["mode"], MODES, "platform.mode", errs)
        if "config_family" in p:
            _check_enum(p["config_family"], CONFIG_FAMILIES, "platform.config_family", errs)

    # workload
    w = m.get("workload", {})
    if isinstance(w, dict):
        _check_required(w, REQUIRED_WORKLOAD, "workload", errs)

    # trigger
    t = m.get("trigger", {})
    if isinstance(t, dict):
        _check_required(t, REQUIRED_TRIGGER, "trigger", errs)
        if "mode" in t:
            _check_enum(t["mode"], TRIGGER_MODES, "trigger.mode", errs)
        if "value" in t and not _is_int(t["value"]):
            errs.append(f"trigger.value: not an integer (got {type(t['value']).__name__})")
        if "value" in t and _is_int(t["value"]) and t["value"] < 0:
            errs.append(f"trigger.value: must be >= 0")

    # target
    tg = m.get("target", {})
    if isinstance(tg, dict):
        _check_required(tg, REQUIRED_TARGET, "target", errs)
        if "layer" in tg:
            _check_enum(tg["layer"], LAYERS, "target.layer", errs)
        if "component" in tg:
            _check_enum(tg["component"], COMPONENTS_MAPPED + COMPONENTS_V2_DECLARED,
                        "target.component", errs)
        if "index" in tg and not _is_int(tg["index"]):
            errs.append(f"target.index: not an integer")
        if "width_bits" in tg and not _is_int(tg["width_bits"]):
            errs.append(f"target.width_bits: not an integer")

    # fault
    f = m.get("fault", {})
    if isinstance(f, dict):
        _check_required(f, REQUIRED_FAULT, "fault", errs)
        if "model" in f:
            _check_enum(f["model"], FAULT_MODELS, "fault.model", errs)
        if "stage" in f:
            _check_enum(f["stage"], FAULT_STAGES, "fault.stage", errs)
        if "duration_events" in f and (not _is_int(f["duration_events"]) or f["duration_events"] < 1):
            errs.append(f"fault.duration_events: must be an integer >= 1")
        if "bit_indices" in f and not isinstance(f["bit_indices"], list):
            errs.append(f"fault.bit_indices: not an array")
        if "f6_phase_offset" in f and not _is_int(f["f6_phase_offset"]):
            errs.append(f"fault.f6_phase_offset: not an integer")
        fpu = f.get("fpu_mode")
        if fpu is not None:
            if not isinstance(fpu, dict):
                errs.append("fault.fpu_mode: not an object")
            else:
                _validate_fpu_mode(fpu, errs)

    # rng
    r = m.get("rng", {})
    if isinstance(r, dict):
        _check_required(r, REQUIRED_RNG, "rng", errs)

    # limits
    l = m.get("limits", {})
    if isinstance(l, dict):
        _check_required(l, REQUIRED_LIMITS, "limits", errs)
        if "max_faults" in l:
            if not _is_int(l["max_faults"]) or l["max_faults"] < 0 or l["max_faults"] > 1:
                errs.append(f"limits.max_faults: must be an integer in {{0,1}} "
                            f"(got {l['max_faults']})")

    # oracle (optional; if kind present, must be a known enum)
    o = m.get("oracle", {})
    if isinstance(o, dict) and "kind" in o:
        _check_enum(o["kind"], ORACLE_KINDS, "oracle.kind", errs)

    return (len(errs) == 0), errs


def _selftest():
    """Assert the validator accepts the sample manifests and rejects a broken
    one. Run via `python3 -m tools.manifest_validate`. Keeps this module in
    sync with schemas/manifest.schema.json + the sample manifests."""
    failures = []
    for rel in ("manifests/p1-gpr-regchain-000384.yaml",
                "manifests/p2-rob-directed-v2.yaml"):
        p = os.path.join(REPO, rel)
        if not os.path.exists(p):
            failures.append(f"missing sample: {rel}")
            continue
        with open(p) as f:
            m = yaml.safe_load(f)
        ok, errs = validate(m)
        if not ok:
            failures.append(f"{rel}: should validate but got: {errs}")

    # deliberately-broken manifest must FAIL
    broken = {"schema_version": "arm-chaos-fi/v3",  # unknown version
              "run_id": "x", "source": {}, "platform": {"isa": "x86", "mode": "SE",
              "cpu_model": "Z", "config_family": "C9"}, "workload": {"binary_sha256": ""},
              "trigger": {"mode": "bogus", "value": -1}, "target": {"layer": "phys",
              "component": "nonsense", "instance": "c"}, "fault": {"model": "fake",
              "duration_events": 0, "stage": "raw"}, "rng": {}, "limits": {"max_faults": 5}}
    ok, errs = validate(broken)
    if ok:
        failures.append("broken manifest: should FAIL but validated (validator too weak)")
    if len(errs) < 6:
        failures.append(f"broken manifest: expected >=6 errors, got {len(errs)}: {errs}")

    if failures:
        print("SELFTEST FAILED:")
        for f_ in failures:
            print(f"  - {f_}")
        sys.exit(1)
    print("SELFTEST OK: v1 p1 + v2 p2 validate, broken manifest rejected "
          f"({len(errs)} errors as expected).")


if __name__ == "__main__":
    _selftest()
