#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fsu_f5_w1_gate.py — FP06-F5-W1 non-formal gate (never counted in 519/240).

Runs the four PRE-REGISTERED W1 gates end to end and decides PASS/FAIL from
real evidence only:

  FP32-SIGN          FP32 scalar sign, SA0, mask 0x80000000
  FP64-SIGN          FP64 scalar sign, SA1, mask 0x8000000000000000
  FP32-MANT           FP32 scalar fixed mantissa, SA0, mask 0x007f8000
  PRECISION-MISMATCH FP32-only workload + manifest fp64 + decode_guard
                     -> census CHAOS_ELIGIBLE_COUNT must be 0

For the three permanent gates the tool calls fsu_seed_runner (census ->
injection -> oracle -> chain), then fsu_seed_audit, and checks the raw
PROP-EVT stream itself (one installation, one fault_id, fixed mask/polarity,
exposure accounting, activation formula, opClass/regClass/precision filters,
chain_end conservation). The mismatch gate runs ONLY the countOnly census.

Artifacts ALWAYS live under runs/fsu-gates/...; the formal runs/fsu tree is
never written. Every missing/invalid artifact is a hard failure (fail closed).

Usage (the main agent runs this after building gem5):
  python3 tools/fsu_f5_w1_gate.py
  python3 tools/fsu_f5_w1_gate.py --outdir runs/fsu-gates/F5-FP06-W1-<tag>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fsu_config_profile as CP  # noqa: E402
import fsu_prop_fields as P  # noqa: E402
import fsu_seed_audit as A  # noqa: E402
import fsu_seed_runner as R  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GEM5 = ROOT / "CHAOS/gem5/build/ARM/gem5.opt"
DEFAULT_CONFIG = ROOT / "configs/se/ooo_proxy.py"
DEFAULT_OUT = ROOT / "runs/fsu-gates/F5-FP06-W1"

SCALAR_OPS = ["FloatAdd", "FloatMult", "FloatMultAcc", "FloatDiv",
              "FloatSqrt"]
F5_TERMINALS = ("committed", "exposed_unconsumed", "not_activated")
# Oracle outcomes that are a real, decidable result. UNKNOWN / Inactive /
# SimulatorError / Hang do NOT prove anything about the filter or the fault.
DECIDABLE_ORACLE = ("SDC", "Masked", "Crash")

GATE_SPECS = [
    {
        "id": "FP32-SIGN",
        "kind": "permanent",
        "manifest": "configs/fsu/FSU-FP06-F5-W1-FP32-SIGN-GATE.json",
        "workload": "w1_fp_scalar_probe",
        "precision": "fp32",
        "lane_width": 32,
        "mask": 0x80000000,
        "polarity": 0,
        "op_classes": SCALAR_OPS,
        "reg_class": "vec",
        "expect_eligible_zero": False,
    },
    {
        "id": "FP64-SIGN",
        "kind": "permanent",
        "manifest": "configs/fsu/FSU-FP06-F5-W1-FP64-SIGN-GATE.json",
        "workload": "w1_fp_scalar_probe",
        "precision": "fp64",
        "lane_width": 64,
        "mask": 0x8000000000000000,
        "polarity": 1,
        "op_classes": SCALAR_OPS,
        "reg_class": "vec",
        "expect_eligible_zero": False,
    },
    {
        "id": "FP32-MANT",
        "kind": "permanent",
        "manifest": "configs/fsu/FSU-FP06-F5-W1-FP32-MANT-GATE.json",
        "workload": "w1_fp_scalar_probe",
        "precision": "fp32",
        "lane_width": 32,
        "mask": 0x007f8000,
        "polarity": 0,
        "op_classes": SCALAR_OPS,
        "reg_class": "vec",
        "expect_eligible_zero": False,
    },
    {
        "id": "PRECISION-MISMATCH",
        "kind": "mismatch",
        "manifest": "configs/fsu/FSU-FP06-F5-W1-PRECISION-MISMATCH-GATE.json",
        "workload": "fp32_fma_kernel",
        "precision": "fp64",
        "lane_width": 64,
        "mask": 0x8000000000000000,
        "polarity": 0,
        "op_classes": SCALAR_OPS,
        "reg_class": "vec",
        "expect_eligible_zero": True,
    },
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _hex_int(value):
    text = str(value if value is not None else "").strip()
    if not text:
        return None
    try:
        return int(text, 0)
    except ValueError:
        try:
            return int(text, 16)
        except ValueError:
            return None


def _dec_int(value):
    text = str(value if value is not None else "").strip()
    if not text:
        return None
    try:
        return int(text, 10)
    except ValueError:
        return None


def stuck_activated(correct: int, mask: int, polarity: int) -> bool:
    """Python twin of chaos_fsu::stuckActivated."""
    if mask == 0:
        return False
    return bool((~correct & mask) != 0) if polarity else bool(correct & mask)


def apply_stuck(correct: int, mask: int, polarity: int) -> int:
    """Python twin of chaos_fsu::applyStuck (forced polarity, not XOR)."""
    return (correct | mask) if polarity else (correct & ~mask)


def parse_census(text: str):
    """Parse the countOnly census log into explicit per-class counts."""
    out = {
        "eligible": -1,
        "opclass": {},
        "regclass": {},
        "decode_rejects": 0,
        "decode_reasons": {},
    }
    for line in text.splitlines():
        s = line.strip()
        if "CHAOS_ELIGIBLE_COUNT=" in s:
            try:
                out["eligible"] = int(
                    s.split("CHAOS_ELIGIBLE_COUNT=")[1].split()[0])
            except (IndexError, ValueError):
                pass
        elif s.startswith("CHAOS_ELIGIBLE_OPCLASS "):
            try:
                name, val = s[len("CHAOS_ELIGIBLE_OPCLASS "):].split("=", 1)
                out["opclass"][name.strip()] = int(val.split()[0])
            except (ValueError, IndexError):
                out["opclass"][s] = -1
        elif s.startswith("CHAOS_ELIGIBLE_REGCLASS "):
            try:
                name, val = s[len("CHAOS_ELIGIBLE_REGCLASS "):].split("=", 1)
                out["regclass"][name.strip()] = int(val.split()[0])
            except (ValueError, IndexError):
                out["regclass"][s] = -1
        elif "CHAOS_DECODE_REJECTS=" in s:
            try:
                out["decode_rejects"] = int(
                    s.split("CHAOS_DECODE_REJECTS=")[1].split()[0])
            except (IndexError, ValueError):
                pass
        elif s.startswith("CHAOS_DECODE_REJECT_REASON "):
            try:
                name, val = s[len("CHAOS_DECODE_REJECT_REASON "):].split(
                    "=", 1)
                out["decode_reasons"][name.strip()] = int(val.split()[0])
            except (ValueError, IndexError):
                out["decode_reasons"][s] = -1
    return out


def _checker():
    checks = []

    def check(name, ok):
        checks.append({"check": name, "ok": bool(ok)})
        return bool(ok)

    return checks, check


def census_checks(census, spec):
    checks, check = _checker()
    eligible = census["eligible"]
    check("census CHAOS_ELIGIBLE_COUNT present", eligible >= 0)
    if spec["expect_eligible_zero"]:
        check("precision mismatch: eligible == 0", eligible == 0)
    else:
        check("gate eligible > 0", eligible > 0)
    op_sum = sum(census["opclass"].values())
    rc_sum = sum(census["regclass"].values())
    check("sum(per-opClass eligible) == eligible", op_sum == eligible)
    check("sum(per-regClass eligible) == eligible", rc_sum == eligible)
    check("census opClass names are all inside the pre-registered allowlist",
          all(k in spec["op_classes"] for k in census["opclass"]))
    check("census regClass names are all the pre-registered reg_class",
          all(k == spec["reg_class"] for k in census["regclass"]))
    if not spec["expect_eligible_zero"]:
        # W1 executes several distinct scalar FP opClasses. Seeing >=2
        # filtered classes proves the census really splits an interleaved
        # stream by opClass instead of counting a single relabeled stream.
        check("census reports >=2 distinct allowed opClasses",
              len(census["opclass"]) >= 2)
        check("census reports the pre-registered reg_class",
              census["regclass"].get(spec["reg_class"], 0) > 0)
    if spec["expect_eligible_zero"]:
        check("rejection reason is precision_mismatch",
              census["decode_reasons"].get("precision_mismatch", 0) > 0)
        check("census decode rejects > 0", census["decode_rejects"] > 0)
    return checks


def prereg_checks(manifest, spec):
    """Prove the on-disk manifest still matches the frozen pre-registration."""
    checks, check = _checker()
    pre = manifest.get("pre_registration")
    check("pre_registration block present", isinstance(pre, dict))
    pre = pre if isinstance(pre, dict) else {}
    fpu = ((manifest.get("injector") or {}).get("fpu_mode") or {})
    inj = manifest.get("injector") or {}
    check("manifest marked gate=true", manifest.get("gate") is True)
    check("manifest counts_toward_519=false",
          manifest.get("counts_toward_519") is False)
    check("manifest config_profile == B0",
          manifest.get("config_profile") == "B0")
    check("pre-registered precision == gate spec",
          pre.get("precision") == spec["precision"])
    check("pre-registered lane_width == gate spec",
          pre.get("lane_width") == spec["lane_width"])
    check("pre-registered mask == gate spec",
          _hex_int(pre.get("mask")) == spec["mask"])
    check("pre-registered polarity == gate spec",
          pre.get("polarity") == spec["polarity"])
    check("pre-registered op_classes == gate spec",
          pre.get("op_classes") == spec["op_classes"])
    check("pre-registered reg_class == gate spec",
          pre.get("reg_class") == spec["reg_class"])
    check("pre-registered decode_guard == true",
          pre.get("decode_guard") is True)
    # The runtime block must agree with the frozen pre-registration.
    check("runtime precision == pre-registered precision",
          fpu.get("precision") == pre.get("precision"))
    check("runtime lane_width == pre-registered lane_width",
          fpu.get("lane_width") == pre.get("lane_width"))
    check("runtime mask == pre-registered mask",
          _hex_int(inj.get("fault_mask", fpu.get("fault_mask")))
          == _hex_int(pre.get("mask")))
    check("runtime polarity == pre-registered polarity",
          fpu.get("stuck_polarity") == pre.get("polarity"))
    check("runtime op_classes == pre-registered op_classes",
          fpu.get("op_classes") == pre.get("op_classes"))
    check("runtime reg_class == pre-registered reg_class",
          fpu.get("reg_class") == pre.get("reg_class"))
    check("runtime decode_guard == true", fpu.get("decode_guard") is True)
    check("runtime permanent_stuck == true",
          fpu.get("permanent_stuck") is True)
    wl = str((manifest.get("workload") or {}).get("binary", ""))
    check("workload is the pre-registered binary", wl.endswith(spec["workload"]))
    return checks


def command_checks(report, spec):
    checks, check = _checker()
    cmds = (report.get("command") or {})
    for which in ("census", "inject"):
        cmd = cmds.get(which) or []
        want_ops = ",".join(spec["op_classes"])
        op_ok = ("--fpu_op_classes" in cmd
                 and cmd[cmd.index("--fpu_op_classes") + 1] == want_ops)
        rc_ok = ("--fpu_reg_class" in cmd
                 and cmd[cmd.index("--fpu_reg_class") + 1] == spec["reg_class"])
        check(f"{which} command carries the pre-registered op_classes", op_ok)
        check(f"{which} command carries the pre-registered reg_class", rc_ok)
        check(f"{which} command enables decode_guard",
              "--fpu_decode_guard" in cmd)
    return checks


def analyze_f5_events(events, spec):
    """Audit the raw permanent-fault stream against the pre-registration."""
    checks, check = _checker()
    roots = [e for e in events if str(e.get("kind")) == "fault_installed"]
    fids = {str(e.get("fault_id")) for e in events if e.get("fault_id")}
    check("exactly one fault_installed root", len(roots) == 1)
    check("exactly one fault_id in the stream", len(fids) == 1)
    if len(roots) != 1 or len(fids) != 1:
        return checks
    root = roots[0]
    fid = str(root.get("fault_id"))
    root_eid = str(root.get("event_id"))
    check("root fault_id is the only fault_id", fids == {fid})
    mask = _hex_int(root.get("fault_mask"))
    fixed = _hex_int(root.get("fixed_mask"))
    pol = _dec_int(root.get("stuck_polarity"))
    check("root fault_mask == pre-registered mask", mask == spec["mask"])
    check("root fixed_mask == pre-registered mask", fixed == spec["mask"])
    check("root stuck_polarity == pre-registered polarity",
          pol == spec["polarity"])
    check("root reg_class == pre-registered reg_class",
          root.get("reg_class") == spec["reg_class"])
    check("root op_class inside pre-registered allowlist",
          root.get("op_class") in spec["op_classes"])
    check("root precision == pre-registered precision",
          root.get("precision") == spec["precision"])

    carriers = [e for e in events if str(e.get("kind")) == "carrier_state"]
    check("exactly one carrier_state", len(carriers) == 1)
    f5_identity = roots + carriers + [
        e for e in events if str(e.get("kind")) == "exposure"]
    # Only the F5 terminal (it carries exposures_total) belongs to the
    # permanent-fault identity; the tracer's generic lifecycle chain_end
    # (outcome=run_end) has no fault fields and is not part of this family.
    f5_identity += [e for e in events
                    if str(e.get("kind")) == "chain_end"
                    and _dec_int(e.get("exposures_total")) is not None]
    check("every F5 identity event carries op_class and reg_class",
          all(e.get("op_class") and e.get("reg_class")
              for e in f5_identity))
    check("carrier_state keeps the fixed mask/polarity",
          all(_hex_int(e.get("fixed_mask")) == spec["mask"]
              and _dec_int(e.get("stuck_polarity")) == spec["polarity"]
              for e in carriers))

    exposures = [e for e in events if str(e.get("kind")) == "exposure"]
    check("exposure events present", bool(exposures))
    ids = [str(e.get("exposure_id")) for e in exposures]
    check("exposure_id values are unique", len(set(ids)) == len(ids))
    check("all exposures keep the fixed mask",
          all(_hex_int(e.get("fixed_mask")) == spec["mask"]
              for e in exposures))
    check("all exposures keep the fixed polarity",
          all(_dec_int(e.get("stuck_polarity")) == spec["polarity"]
              for e in exposures))
    check("all exposures point at the installation event",
          all(str(e.get("install_event")) == root_eid for e in exposures))
    check("all exposures keep one fault_id",
          all(str(e.get("fault_id")) == fid for e in exposures))
    check("all exposure op_class values are inside the allowlist",
          all(e.get("op_class") in spec["op_classes"] for e in exposures))
    check("all exposure reg_class values == pre-registered reg_class",
          all(e.get("reg_class") == spec["reg_class"] for e in exposures))
    check("no exposure comes from an FCVT opClass",
          all(e.get("op_class") not in ("FloatCvt", "SimdFloatCvt")
              for e in exposures))
    check("all exposures decode as scalar_vfp",
          all(e.get("decoded_kind") == "scalar_vfp" for e in exposures))
    check(f"all exposures decode as {spec['precision']}",
          all(e.get("decoded_precision") == spec["precision"]
              for e in exposures))
    check("all exposures declare the pre-registered precision",
          all(e.get("precision") == spec["precision"] for e in exposures))

    act_bad, after_bad, missing = [], [], []
    for e in exposures:
        cb = _hex_int(e.get("correct_before"))
        sa = _hex_int(e.get("stuck_after"))
        if cb is None or sa is None:
            missing.append(e)
            continue
        want_act = stuck_activated(cb, mask, pol)
        if str(e.get("activated")) != ("1" if want_act else "0"):
            act_bad.append(e)
        if sa != apply_stuck(cb, mask, pol):
            after_bad.append(e)
    check("every exposure has correct_before/stuck_after", not missing)
    check("activation == stuckActivated(correct_before, mask, polarity)",
          not act_bad)
    check("stuck_after == applyStuck(correct_before, mask, polarity)",
          not after_bad)
    check("at least one exposed-but-NOT-activated exposure",
          any(str(e.get("activated")) == "0" for e in exposures))
    check("at least one activated exposure",
          any(str(e.get("activated")) == "1" for e in exposures))
    snap_bad = []
    for e in exposures:
        t = _dec_int(e.get("exposures_total"))
        s = _dec_int(e.get("exposures_sampled"))
        d = _dec_int(e.get("exposures_dropped"))
        if None in (t, s, d) or t != s + d:
            snap_bad.append(e)
    check("every exposure satisfies total == sampled + dropped", not snap_bad)

    # The propagation tracer also emits a generic lifecycle `chain_end`
    # (outcome=run_end, no exposure counters). Only the F5 terminal carrying
    # exposures_total is the permanent-fault chain_end.
    chain_ends = [e for e in events
                  if str(e.get("kind")) == "chain_end"
                  and _dec_int(e.get("exposures_total")) is not None]
    check("exactly one F5 chain_end (with exposures_total)",
          len(chain_ends) == 1)
    if len(chain_ends) != 1:
        return checks
    ce = chain_ends[0]
    total = _dec_int(ce.get("exposures_total"))
    sampled = _dec_int(ce.get("exposures_sampled"))
    dropped = _dec_int(ce.get("exposures_dropped"))
    act_count = _dec_int(ce.get("activated_exposure_count"))
    check("chain_end counts are integers",
          None not in (total, sampled, dropped, act_count))
    if None not in (total, sampled, dropped, act_count):
        check("exposures_total == exposures_sampled + exposures_dropped",
              total == sampled + dropped)
        check("exposures_sampled == exposure events in the stream",
              sampled == len(exposures))
        check("activated_exposure_count >= activated stream events",
              act_count >= sum(1 for e in exposures
                               if str(e.get("activated")) == "1"))
        check("exposures_total > 0", total > 0)
    check("chain_end install_event == root event_id",
          str(ce.get("install_event")) == root_eid)
    check("chain_end fixed_mask == pre-registered mask",
          _hex_int(ce.get("fixed_mask")) == spec["mask"])
    check("chain_end stuck_polarity == pre-registered polarity",
          _dec_int(ce.get("stuck_polarity")) == spec["polarity"])
    check("chain_end op_class inside allowlist",
          ce.get("op_class") in spec["op_classes"])
    check("chain_end reg_class == pre-registered reg_class",
          ce.get("reg_class") == spec["reg_class"])
    terminal = str(ce.get("terminal") or "")
    check("chain_end terminal is a defined F5 terminal",
          terminal in F5_TERMINALS)
    check("chain_end outcome agrees with terminal",
          str(ce.get("outcome") or "") == terminal)
    if terminal == "committed":
        check("terminal=committed has a real L5 commit witness",
              any(str(e.get("kind")) == "commit"
                  and str(e.get("fault_id")) == fid for e in events))
    if terminal == "not_activated":
        check("terminal=not_activated implies zero activated exposures",
              act_count == 0)
    return checks


def _merge(checks, more):
    checks.extend(more)
    return checks


def _record(spec, checks, extra=None):
    failures = [c["check"] for c in checks if not c["ok"]]
    rec = {
        "gate": spec["id"],
        "kind": spec["kind"],
        "manifest": str(ROOT / spec["manifest"]),
        "checks": checks,
        "failures": failures,
        "ok": not failures,
    }
    if extra:
        rec.update(extra)
    return rec


def run_permanent_gate(spec, outdir: Path, gem5: Path, config: Path,
                       root: Path, timeout: int, runner=None):
    manifest_path = root / spec["manifest"]
    gate_dir = outdir / spec["id"]
    gate_dir.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    checks = prereg_checks(manifest, spec)
    if any(not c["ok"] for c in checks):
        return _record(spec, checks, {"status": "not_run",
                                      "reason": "pre-registration mismatch"})
    res = R.run_seed(manifest_path, 1, out_root=gate_dir / "runs",
                     gem5=gem5, root=root, runner=runner,
                     timeout_s=timeout, copy_to_complete=False,
                     config=config)
    extra = {"status": res.get("status"), "run_result": res}
    if res.get("status") not in ("admitted", "already_admitted"):
        more, check = _checker()
        check("seed runner admitted the gate run", False)
        _merge(checks, more)
        return _record(spec, checks, extra)
    if res.get("status") == "already_admitted":
        attempt = Path(res.get("authoritative", ""))
    else:
        attempt = Path(res["attempt"])
    extra["attempt"] = str(attempt)
    audit = A.write_audit(attempt)
    report = json.loads((attempt / "chain_report.json").read_text(
        encoding="utf-8"))
    oracle = json.loads((attempt / "oracle.json").read_text(encoding="utf-8"))
    written = json.loads((attempt / "manifest.json").read_text(
        encoding="utf-8"))
    events, truncated, reason = P.read_stream(
        attempt / "inject/prop_evt.txt.gz")
    more, check = _checker()
    check("audit.ok", audit.get("ok") is True)
    check("audit.certified", audit.get("certified") is True)
    check(f"prop_evt not truncated ({reason or 'ok'})", not truncated)
    check("oracle category is decidable (not UNKNOWN/Inactive/SimulatorError)",
          oracle.get("category") in DECIDABLE_ORACLE)
    check("B0 census config.ini matches",
          CP.verify_config_profile(attempt / "census/config.ini",
                                   "B0").get("ok") is True)
    check("B0 injection config.ini matches",
          CP.verify_config_profile(attempt / "inject/config.ini",
                                   "B0").get("ok") is True)
    _merge(checks, more)
    _merge(checks, command_checks(report, spec))
    _merge(checks, analyze_f5_events(events, spec))
    census_text = ""
    for name in ("census/fpu_injections.log", "census.out", "census.err"):
        p = attempt / name
        if p.exists():
            census_text += "\n" + p.read_text(encoding="utf-8",
                                              errors="replace")
    census = parse_census(census_text)
    _merge(checks, census_checks(census, spec))
    more, check = _checker()
    check("injection census used the same eligible total",
          _dec_int(report.get("oracle", {}).get("eligible_count"))
          == census["eligible"])
    # Permanent-fault conservation: after the single installation at
    # eligible ordinal f5_warmup+1, EVERY later eligible event is an
    # exposure, so chain_end.exposures_total == eligible - f5_warmup.
    ce = [e for e in events if str(e.get("kind")) == "chain_end"]
    total = _dec_int(ce[0].get("exposures_total")) if len(ce) == 1 else None
    warmup = _dec_int(
        ((written.get("injector") or {}).get("fpu_mode") or {})
        .get("f5_warmup"))
    if (total is not None and warmup is not None
            and census["eligible"] > warmup):
        check("exposures_total == eligible - f5_warmup",
              total == census["eligible"] - warmup)
    _merge(checks, more)
    extra.update({
        "eligible": census["eligible"],
        "opclass_census": census["opclass"],
        "regclass_census": census["regclass"],
        "oracle": oracle.get("category"),
        "audit_ok": audit.get("ok"),
        "audit_certified": audit.get("certified"),
        "event_count": len(events),
        "truncated": truncated,
    })
    return _record(spec, checks, extra)


def run_mismatch_gate(spec, outdir: Path, gem5: Path, config: Path,
                      root: Path, timeout: int, runner=None):
    manifest_path = root / spec["manifest"]
    gate_dir = outdir / spec["id"]
    gate_dir.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    checks = prereg_checks(manifest, spec)
    if any(not c["ok"] for c in checks):
        return _record(spec, checks, {"status": "not_run",
                                      "reason": "pre-registration mismatch"})
    runner = runner or R._default_runner
    census_dir = gate_dir / "census"
    cmd = R.build_cmd(manifest, census_dir, 1, None, True, gem5, config,
                      root)
    rc, out, err, timed = runner(cmd, timeout)
    (gate_dir / "census.out").write_text(out, encoding="utf-8")
    (gate_dir / "census.err").write_text(err, encoding="utf-8")
    log = ""
    logp = census_dir / "fpu_injections.log"
    if logp.exists():
        log = logp.read_text(encoding="utf-8", errors="replace")
    census = parse_census(log + "\n" + out + "\n" + err)
    more, check = _checker()
    check("census rc == 0", rc == 0)
    check("census not timed out", not timed)
    check("census command carries pre-registered op_classes",
          "--fpu_op_classes" in cmd and cmd[cmd.index("--fpu_op_classes") + 1]
          == ",".join(spec["op_classes"]))
    check("census command carries pre-registered reg_class",
          "--fpu_reg_class" in cmd
          and cmd[cmd.index("--fpu_reg_class") + 1] == spec["reg_class"])
    check("census command enables decode_guard",
          "--fpu_decode_guard" in cmd)
    check("B0 census config.ini matches",
          CP.verify_config_profile(census_dir / "config.ini",
                                   "B0").get("ok") is True)
    _merge(checks, more)
    _merge(checks, census_checks(census, spec))
    extra = {
        "status": "pass" if rc == 0 and not timed else "fail",
        "eligible": census["eligible"],
        "opclass_census": census["opclass"],
        "regclass_census": census["regclass"],
        "decode_rejects": census["decode_rejects"],
        "decode_reasons": census["decode_reasons"],
        "command": cmd,
    }
    return _record(spec, checks, extra)


def run_gate(spec, outdir, gem5, config, root, timeout, runner=None):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    if spec["kind"] == "mismatch":
        return run_mismatch_gate(spec, outdir, Path(gem5), Path(config),
                                 Path(root), timeout, runner=runner)
    return run_permanent_gate(spec, outdir, Path(gem5), Path(config),
                              Path(root), timeout, runner=runner)


def _write_report(outdir: Path, records):
    ok = all(r["ok"] for r in records)
    report = {
        "gate": "F5-FP06-W1",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "non_formal": True,
        "counts_toward_519": False,
        "outdir": str(outdir),
        "records": records,
        "ok": ok,
    }
    (outdir / "gate_checks.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    lines = [
        "# FP06-F5-W1 gate（非正式，不计 519/240）", "",
        f"- 生成时间：{report['created_at']}",
        f"- 证据目录：`{outdir}`",
        f"- 结论：**{'PASS' if ok else 'FAIL'}**", "",
        "| gate | eligible | oracle | audit.ok | certified | 结论 |",
        "|---|---|---|---|---|---|",
    ]
    for r in records:
        lines.append(
            f"| {r['gate']} | {r.get('eligible', '—')} | "
            f"{r.get('oracle', '—')} | {r.get('audit_ok', '—')} | "
            f"{r.get('audit_certified', '—')} | "
            f"{'PASS' if r['ok'] else 'FAIL'} |")
    lines += ["", "## 逐 gate 检查", ""]
    for r in records:
        lines += [f"### {r['gate']}", "",
                  "| 检查 | 结果 |", "|---|---|"]
        for c in r["checks"]:
            lines.append(f"| {c['check']} | {'PASS' if c['ok'] else 'FAIL'} |")
        lines.append("")
    (outdir / "GATE.md").write_text("\n".join(lines) + "\n",
                                    encoding="utf-8")
    sums = []
    for f in sorted(outdir.rglob("*")):
        if f.is_file() and f.name != "SHA256SUMS":
            sums.append(f"{sha256_file(f)}  {f.relative_to(outdir)}")
    (outdir / "SHA256SUMS").write_text("\n".join(sums) + "\n",
                                       encoding="utf-8")
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(description="FP06-F5-W1 non-formal gate")
    ap.add_argument("--outdir", default=str(DEFAULT_OUT))
    ap.add_argument("--gem5", default=str(DEFAULT_GEM5))
    ap.add_argument("--config", default=str(DEFAULT_CONFIG))
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--only", default="",
                    help="comma-separated gate ids (default: all)")
    a = ap.parse_args(argv)

    root = Path(a.root)
    outdir = Path(a.outdir)
    gate_root = (root / "runs/fsu-gates").resolve()
    out_res = outdir.resolve()
    if out_res != gate_root and gate_root not in out_res.parents:
        print(json.dumps({
            "ok": False,
            "reason": f"gate artifacts must live under {gate_root} "
                      f"(got {out_res}); runs/fsu is reserved for formal "
                      f"seeds"},
            ensure_ascii=False, indent=2))
        return 2

    selected = [s.strip() for s in a.only.split(",") if s.strip()]
    specs = [s for s in GATE_SPECS if not selected or s["id"] in selected]
    if selected and len(specs) != len(selected):
        known = {s["id"] for s in GATE_SPECS}
        print(json.dumps({"ok": False,
                          "reason": f"unknown gate id(s): "
                                    f"{sorted(set(selected) - known)}"},
                         ensure_ascii=False, indent=2))
        return 2
    records = []
    for spec in specs:
        rec = run_gate(spec, outdir, Path(a.gem5), Path(a.config), root,
                       a.timeout)
        records.append(rec)
        print(f"[{'PASS' if rec['ok'] else 'FAIL'}] {rec['gate']}")
        for name in rec["failures"]:
            print(f"    FAIL: {name}")
    report = _write_report(outdir, records)
    print(json.dumps({"ok": report["ok"], "outdir": str(outdir),
                      "gates": {r["gate"]: r["ok"] for r in records}},
                     ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
