#!/usr/bin/env python3
"""Focused tests for the MMU formal authority gates (no gem5 is launched).

Covers:
  1. M02 old_pfn resolution from a REAL gem5 W10 control output file
     (0x834b6 for R02), rejection of missing/faulted/--ctx-all controls, and
     the absence of a literal --mmu_m02_old_pfn in the runner.
  2. The stricter M06 DETECTED_CONTAINED rule against REAL traces:
     exception_delivery proof is required; a consumed descriptor with
     exception_delivered=0 is TRACE_INCOMPLETE, never DETECTED_CONTAINED.
  3. The W10S variant check (WorkloadID stays W10).
  4. Excel/CSV/JSON authority consistency (40 IDs, literal seed).

Run: python3 tools/tests/test_mmu_formal_authority.py
"""

import json
import os
import re
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import mmu_formal_preflight as pf          # noqa: E402
import mmu_formal_runner as runner         # noqa: E402
import mmu_formal_validate as validator    # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    if cond:
        print("PASS %s%s" % (name, (" -- " + str(detail)) if detail else ""))
    else:
        print("FAIL %s%s" % (name, (" -- " + str(detail)) if detail else ""))
        FAILS.append(name)


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(text)


def test_m02_pfn_resolution():
    real = os.path.join(ROOT, "runs", "TEST-M02-R02B", "Run_Log",
                        "observed_output.txt")
    real_text = open(real, errors="replace").read()
    check("m02.real_file_has_834b6", "target_pfn=0x834b6" in real_text,
          real)
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = os.path.join(tmp, "runs", "TEST-CTRL-W10-R02", "Run_Log")
        os.makedirs(ctrl, exist_ok=True)
        shutil.copy2(real, os.path.join(ctrl, "golden_output.txt"))
        mapping = pf.load_w10_pfn_map(tmp)
        rec = mapping["contexts"].get("R02", {})
        check("m02.resolve_R02", mapping["present"] and
              rec.get("target_pfn") == 0x834B6,
              "0x%x" % rec.get("target_pfn", 0))
        check("m02.neighbor", rec.get("neighbor_pfn") == 0x834B7,
              hex(rec.get("neighbor_pfn", 0)))
        check("m02.target_va", rec.get("target_va") == 0x4001100000,
              hex(rec.get("target_va", 0)))
        args = runner._model_fault_args(
            "M02", 0x4001100000, None, "Read", 1, "R02", [],
            m02_old_pfn="0x%x" % rec["target_pfn"])
        joined = " ".join(args)
        check("m02.runner_arg", "--mmu_m02_old_pfn 0x834b6" in joined,
              joined)
        check("m02.no_literal_83480", "0x83480" not in joined)
        # A missing control must not resolve.
        check("m02.missing_blocks",
              not pf.load_w10_pfn_map(
                  tmp, os.path.join(tmp, "does-not-exist"))["present"])
        # A fault-enabled run is never a control.
        cmd = os.path.join(tmp, "runs", "TEST-CTRL-W10-R03", "Run_Log")
        os.makedirs(cmd, exist_ok=True)
        shutil.copy2(real, os.path.join(cmd, "golden_output.txt"))
        write(os.path.join(cmd, "command.txt"),
              "gem5 --mmu_fault_model M02 --mmu_fault_enable true\n")
        bad = pf.load_w10_pfn_map(tmp)
        check("m02.rejects_faulted", "R03" not in bad["contexts"],
              bad.get("rejected"))
        # The legacy --ctx all control does not match the R0x naming rule.
        old = os.path.join(tmp, "runs", "TEST-ENV-CTRL-W10", "Run_Log")
        os.makedirs(old, exist_ok=True)
        shutil.copy2(os.path.join(ROOT, "runs", "TEST-ENV-CTRL-W10", "Run_Log",
                                  "golden_output.txt"),
                     os.path.join(old, "golden_output.txt"))
        old_map = pf.load_w10_pfn_map(tmp)
        # R01 exists only in the legacy --ctx all control, which must not
        # supply it.  R02 comes from the valid scoped fixture above.
        check("m02.rejects_all_context_control",
              "R01" not in old_map["contexts"],
              "contexts=%s %s" % (sorted(old_map["contexts"]),
                                  old_map.get("detail")))
    ok, detail = pf.check_runner_pfn_hardcode(ROOT)
    check("m02.no_hardcoded_literal_in_tools", ok, detail)


def _ctx_of(run_id):
    return "R" + re.search(r"R(0[1-5])", run_id).group(1)


def _validate_m06(run_id):
    ctx = _ctx_of(run_id)
    run_dir = os.path.join(ROOT, "runs", run_id)
    paths = validator.find_run_paths(run_dir)
    events, bad, err = validator.load_events_tolerant(paths["trace"])
    by_id = {e["event_id"]: e for e in events}
    manifest = validator.load_manifest(paths.get("manifest"))
    target_va = manifest.get("target_va") or pf.W10_CONTEXT_VA.get(
        0x4001000000 + (int(ctx[1:]) - 1) * 0x1000000)
    return validator.evaluate_run(
        events, by_id, bad, "M06", "W10", ctx, target_va,
        manifest.get("target_mode", "Read"), run_id, paths.get("golden"),
        paths.get("terminal"), manifest, trace_error=err)


def test_m06_rule():
    contained = {
        "TEST-M06-R01": "summary exception_delivered=1",
        "TEST-M06-R02D": "real exception_delivery event",
    }
    for run_id, why in contained.items():
        res = _validate_m06(run_id)
        check("m06.%s.contained" % run_id, res["TerminalState"] ==
              "DETECTED_CONTAINED", "%s (%s)" % (res["TerminalState"], why))
    for run_id in ("TEST-M06-R03B2", "TEST-M06-R04B2", "TEST-M06-R05B2"):
        res = _validate_m06(run_id)
        sep = (res.get("Details") or {}).get("m06_separation") or {}
        check("m06.%s.not_contained" % run_id,
              res["TerminalState"] != "DETECTED_CONTAINED",
              "terminal=%s exception_delivered=%s" %
              (res["TerminalState"], sep.get("exception_delivered")))
        check("m06.%s.trace_incomplete" % run_id,
              res["TerminalState"] in ("TRACE_INCOMPLETE", "SQUASHED"),
              res["TerminalState"])


def test_w10s_variant():
    excel, samples, ctx, hooks, workloads, rs, cfg = pf.build_environment(ROOT)
    by_id = {s["SampleRunID"]: s for s in samples}
    for sid, model, ctx_id, variant in (
            ("M06-F0-W10-S01-R02", "M06", "R02", "W10S-COLD-STORE"),
            ("M08-F0-W10-S01-R05", "M08", "R05", "W10S-WARM-STORE")):
        sample = by_id[sid]
        row = pf.evaluate_sample(sample, ctx, ROOT, hooks, workloads, cfg, rs)
        check("w10s.%s.workload_id" % sid, row["WorkloadID"] == "W10",
              row["WorkloadID"])
        check("w10s.%s.variant" % sid, row["WorkloadVariant"] == variant and
              row["RunWorkload"] == "W10S",
              "%s/%s" % (row["WorkloadVariant"], row["RunWorkload"]))
        check("w10s.%s.variant_status" % sid, row["VariantStatus"] == "PASS",
              row["VariantDetail"])


def test_authority_consistency():
    frozen = pf.frozen_authority_paths(ROOT)
    excel, samples, ctx, _hooks, _wl, _rs, _cfg = pf.build_environment(ROOT)
    check("authority.sample_count", len(samples) == 40, len(samples))
    ids = [s["SampleRunID"] for s in samples]
    check("authority.unique_ids", len(set(ids)) == 40, len(set(ids)))
    check("authority.seed_literal",
          {s.get("Seed") for s in samples} ==
          {pf.SEED_LITERAL_DETERMINISTIC},
          sorted({s.get("Seed") for s in samples}))
    check("authority.seed_policy",
          {s.get("SeedPolicy") for s in samples} ==
          {pf.SEED_POLICY_DETERMINISTIC})
    cfg = json.load(open(os.path.join(frozen["dir"],
                                      pf.FROZEN_CONFIG_JSON_NAME)))
    check("authority.json_count", len(cfg.get("samples", [])) == 40,
          len(cfg.get("samples", [])))
    check("authority.json_seed", cfg.get("seed") ==
          pf.SEED_LITERAL_DETERMINISTIC and cfg.get("seed_policy") ==
          pf.SEED_POLICY_DETERMINISTIC)
    check("authority.json_ids",
          [s.get("SampleRunID") for s in cfg.get("samples", [])] == ids)
    check("authority.no_triple_issues", not ctx["issues"], ctx["issues"][:3])


def main():
    test_m02_pfn_resolution()
    test_m06_rule()
    test_w10s_variant()
    test_authority_consistency()
    print("\n%s" % ("ALL TESTS PASS" if not FAILS else
                   "%d FAILURE(S): %s" % (len(FAILS), FAILS)))
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(main())
