#!/usr/bin/env python3
"""Focused tests for MMU formal-runner parameter parity (no gem5 launch).

Covers:
  1. TargetVA resolution precedence: TargetVAExact > numeric TargetVA >
     unique embedded 0x token > workload macro.
  2. M07 R04/R05 resolve the exact instruction VA from the v3.0.2 authority
     while R01-R03 and the ambiguous M03 R05 cell keep their previous values.
  3. M05 rows carry the approved DecoyVA / table base columns.

Run: python3 tools/tests/test_mmu_parameter_parity.py
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import mmu_formal_preflight as pf  # noqa: E402
import mmu_formal_runner as runner  # noqa: E402

V302 = os.path.join(ROOT, "phase3", "final",
                    "MMU_Final_Formal_Readiness_Package_v3.0.2")
EXCEL = os.path.join(V302, "gem5-fi-MMU-Final-Paper-Experiment-Plan.xlsx")
CSV = os.path.join(V302, "MMU_40_Sample_Matrix.csv")

FAILS = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name +
          ((" -- " + str(detail)) if detail else ""))
    if not cond:
        FAILS.append(name)


def by_id(samples):
    return {s["SampleRunID"]: s for s in samples}


def test_precedence():
    wl = {"workload_vas": {"W11_DATA_VA": 0x4004000000,
                           "W11_CODE_VA": 0x4005000000}}
    sample = {"WorkloadID": "W11", "ContextID": "R05"}
    sample["TargetVAExact"] = "0x400d400100"
    sample["TargetVA"] = "XN code VA 0x400d400000"
    value, basis = pf.resolve_target_va(sample, wl)
    check("target.explicit_wins", value == 0x400D400100 and
          basis == "excel:TargetVAExact", (hex(value), basis))

    sample = {"TargetVA": "XN code VA 0x400d400100",
              "WorkloadID": "W14", "ContextID": "R04"}
    value, basis = pf.resolve_target_va(sample, wl)
    check("target.embedded_unique", value == 0x400D400100 and
          "embedded" in basis, (hex(value), basis))

    sample = {"TargetVA": "data 0x4004000000 (R01-R04), "
                          "code 0x4005000000 (R05)",
              "WorkloadID": "W11", "ContextID": "R05"}
    value, basis = pf.resolve_target_va(sample, wl)
    check("target.embedded_ambiguous_falls_back",
          value == 0x4005000000 and basis == "W11_CODE_VA",
          (hex(value), basis))

    sample = {"TargetVA": "0x4001100000", "WorkloadID": "W10",
              "ContextID": "R02"}
    value, basis = pf.resolve_target_va(sample, wl)
    check("target.numeric_cell", value == 0x4001100000 and basis == "excel",
          (hex(value), basis))


def test_authority_rows():
    _excel, samples, ctx, _hooks, wls, _rs, _cfg = pf.build_environment(
        ROOT, EXCEL, CSV)
    recs = by_id(samples)
    check("authority.count", len(samples) == 40, len(samples))
    check("authority.no_issues", not ctx.get("issues"), ctx.get("issues"))

    wl = wls["W14"]
    expected = {
        "M07-F0-W14-S01-R01": 0x400D000000,
        "M07-F0-W14-S01-R02": 0x400D000000,
        "M07-F0-W14-S01-R03": 0x400D200000,
        "M07-F0-W14-S01-R04": 0x400D400100,
        "M07-F0-W14-S01-R05": 0x400D600180,
    }
    for sid, want in expected.items():
        value, basis = pf.resolve_target_va(recs[sid], wl)
        check("authority.%s" % sid, value == want,
              (hex(value or 0), basis))

    for sid in expected:
        check("authority.%s.exact_col" % sid,
              recs[sid].get("TargetVAExact") == "0x%x" % expected[sid],
              recs[sid].get("TargetVAExact"))

    for i in range(1, 6):
        sid = "M05-F0-W13-S01-R%02d" % i
        check("authority.%s.decoy" % sid,
              recs[sid].get("M05DecoyVA") == "0x4010200000" and
              recs[sid].get("M05DecoyTableBase") == "0",
              (recs[sid].get("M05DecoyVA"),
               recs[sid].get("M05DecoyTableBase")))

    # R03's symbolic cell still carries an embedded exact value that matches
    # the workload macro; the ambiguous M03 R05 cell is untouched.
    value, basis = pf.resolve_target_va(recs["M03-F0-W11-S01-R05"],
                                        wls["W11"])
    check("authority.M03.R05.fallback", value == 0x4005000000,
          (hex(value or 0), basis))
    value, basis = pf.resolve_target_va(recs["M05-F0-W13-S01-R01"],
                                        wls["W13"])
    check("authority.M05.target_va", value == 0x4010000000,
          (hex(value or 0), basis))


def test_m05_command():
    args = runner._model_fault_args(
        "M05", 0x4010000000, None, "Read", 1, "R01", [],
        m05_decoy_table_base="0", m05_decoy_va="0x4010200000")
    check("m05.command.table_base",
          "--mmu_m05_decoy_table_base" in args and
          args[args.index("--mmu_m05_decoy_table_base") + 1] == "0", args)
    check("m05.command.decoy_va",
          "--mmu_m05_decoy_va" in args and
          args[args.index("--mmu_m05_decoy_va") + 1] == "0x4010200000",
          args)
    check("m05.command.target_n21",
          args[args.index("--mmu_target_n") + 1] == "21", args)
    # A zero decoy VA is never emitted; the caller fails closed instead.
    args0 = runner._model_fault_args(
        "M05", 0x4010000000, None, "Read", 1, "R01", [],
        m05_decoy_table_base="0", m05_decoy_va="0")
    check("m05.command.no_zero_flag", "--mmu_m05_decoy_va" not in args0,
          args0)
    auth = runner.load_param_authority(os.path.join(
        V302, "MMU_Parameter_Authority_v3.0.2.json"))
    check("m05.authority.loaded", auth["present"] and auth["sha256"],
          auth["detail"])
    rec = (auth["data"].get("samples") or {}).get("M05-F0-W13-S01-R05", {})
    check("m05.authority.value",
          rec.get("M05DecoyVA") == "0x4010200000" and
          rec.get("pilot_decoy_va") == "0x4010200000" and
          rec.get("pilot_decoy_table_base") == "0", rec)


def _base_plan(model, context, target_va, mode, instruction):
    return {
        "sample_run_id": "%s-F0-W1x-S01-%s" % (model, context),
        "model": model, "workload": "W13" if model == "M05" else "W14",
        "run_workload": "W13" if model == "M05" else "W14",
        "context": context, "seed": "N/A_DETERMINISTIC",
        "seed_policy": "DETERMINISTIC", "seed_valid": True,
        "seed_used_by_gem5": False,
        "gem5_sha256": runner.FROZEN_GEM5_SHA256,
        "source_sha256": dict(runner.FROZEN_SOURCE_SHA256),
        "workload_sha256": runner.FROZEN_WORKLOAD_SHA256[
            "W13" if model == "M05" else "W14"],
        "control_oracle": {"present": True, "sha256": "deadbeef"},
        "target_va": target_va, "target_mode": mode,
        "target_instruction": instruction,
        "target_n": 21 if model == "M05" else 12,
        "m05_decoy_va": "0x4010200000", "m05_decoy_table_base": "0",
        "command": ["--mmu_target_n", "21" if model == "M05" else "12",
                    "--mmu_m05_decoy_table_base", "0",
                    "--mmu_m05_decoy_va", "0x4010200000"],
    }


def test_parity_gate():
    m05_rec = {"SampleRunID": "M05-F0-W1x-S01-R01", "ModelID": "M05",
               "WorkloadID": "W13", "ContextID": "R01",
               "AccessMode": "Read", "TargetInstruction": "LDR",
               "M05DecoyVA": "0x4010200000", "M05DecoyTableBase": "0"}
    m05_auth = {
        "samples": {"M05-F0-W1x-S01-R01": {
            "M05DecoyVA": "0x4010200000", "M05DecoyTableBase": "0",
            "pilot_decoy_va": "0x4010200000",
            "pilot_decoy_table_base": "0"}},
        "provenance": {"W13_DECOY_VA": {"value": "0x4010200000"}}}
    plan = _base_plan("M05", "R01", 0x4010000000, "Read", "LDR")
    m05_auth = {"present": True, "data": m05_auth}
    good = runner.evaluate_parameter_parity(plan, m05_rec, m05_auth)
    check("parity.m05.good", good["ok"], good["failures"])
    bad_plan = dict(plan)
    bad_plan["m05_decoy_va"] = "0"
    bad_plan["command"] = ["--mmu_target_n", "21",
                           "--mmu_m05_decoy_table_base", "0"]
    bad = runner.evaluate_parameter_parity(bad_plan, m05_rec, m05_auth)
    check("parity.m05.zero_blocks", not bad["ok"] and
          "m05.decoy_va_present" in bad["failures"] and
          "m05.command_explicit_decoy_va" in bad["failures"],
          bad["failures"])

    m07_rec = {"SampleRunID": "M07-F0-W1x-S01-R04", "ModelID": "M07",
               "WorkloadID": "W14", "ContextID": "R04",
               "AccessMode": "Execute", "TargetInstruction": "EL0 execute",
               "TargetVA": "XN code VA 0x400d400100",
               "TargetVAExact": "0x400d400100"}
    m07_auth = {"samples": {"M07-F0-W1x-S01-R04": {
        "TargetVAExact": "0x400d400100",
        "pilot_target_va": "0x400d400100",
        "pilot_target_mode": "Execute"}}, "provenance": {}}
    plan = _base_plan("M07", "R04", 0x400D400100, "Execute", "EL0 execute")
    plan["command"] = ["--mmu_target_n", "12"]
    m07_auth = {"present": True, "data": m07_auth}
    good = runner.evaluate_parameter_parity(plan, m07_rec, m07_auth)
    check("parity.m07.good", good["ok"], good["failures"])
    bad_plan = dict(plan)
    bad_plan["target_va"] = 0x400D400000
    bad = runner.evaluate_parameter_parity(bad_plan, m07_rec, m07_auth)
    check("parity.m07.page_base_blocks", not bad["ok"] and
          "m07.target_va_equals_authority" in bad["failures"],
          bad["failures"])


def main():
    test_precedence()
    test_authority_rows()
    test_m05_command()
    test_parity_gate()
    if FAILS:
        print("FAILED: %d" % len(FAILS))
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
