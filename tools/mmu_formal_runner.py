#!/usr/bin/env python3
"""MMU Phase-3 formal-experiment runner.

Two modes:

  FORMAL  --sample <SampleRunID>
      Reads ModelID / WorkloadID / ContextID / ROI / target event / Seed from
      the FROZEN AUTHORITY workbook (07_Sample_Matrix), defaulting to
      phase3/freeze/authority/.  The triple is validated before anything else.
      The researcher-approved literal Seed `N/A_DETERMINISTIC` is VALID when
      SeedPolicy=DETERMINISTIC: it is recorded as a literal, never parsed as
      an integer, and never passed to gem5 (seed_used_by_gem5=false).  A
      missing/placeholder seed yields exit 3 / BLOCKED_MISSING_SEED; an
      inconsistent seed/policy pair (numeric seed under DETERMINISTIC, or the
      literal under a random policy) yields exit 3 / BLOCKED_SEED_POLICY.
      No seed is ever generated, hashed, timestamped or defaulted.  The
      command is additionally checked to contain no seed flag at all.

  PILOT   --pilot <TEST-ID> --model M0x --workload W1x --context R0x
          --target <VA-or-ASID> --eligible-event-index N
      An explicit, deterministic eligible-event trigger.  No seed is read or
      generated.  The output manifest and report are labelled PILOT, never
      formal.

Both modes:
  * write to runs/<RunID>/ with a fresh disk copy;
  * refuse to overwrite an existing non-empty run directory (exit 4);
  * record gem5_sha256, source_sha256 (mmu.cc/table_walker.cc/.hh/tlb.cc) and
    workload_sha256 in the plan and sample_manifest.json, and fail closed
    (BLOCKED_BINARY/BLOCKED_SOURCE/BLOCKED_WORKLOAD) if any changes between
    plan and execution;
  * resolve an independent control oracle from the preflight mapping (or an
    explicit --control-run) and record its SHA256 in the manifest;
  * resolve M02's `--mmu_m02_old_pfn` per context from an INDEPENDENT
    no-fault scoped W10 control (directory / JSON map / golden file), and
    refuse the run (`BLOCKED_MISSING_W10_PFN_MAPPING`) when it cannot be
    resolved.  No literal old_pfn exists in this tool;
  * capture command, gem5 exit code, board.terminal, config, prop_evt.txt.gz,
    golden output and SHA256;
  * wait until prop_evt.txt.gz size+mtime are stable across two checks before
    copying/validating; if the trace is unstable or a truncated/EOF read is
    reported, re-wait and re-validate once, then record `trace_read_error`
    honestly (never suppressed);
  * invoke tools/mmu_formal_validate.py automatically and store the JSON/MD
    verdict under Validation/.

Exit codes
  0  run completed and validation produced a report
  2  usage / triple validation error
  3  seed gate blocked (BLOCKED_MISSING_SEED / BLOCKED_SEED_POLICY; formal)
  4  output directory already contains results (refuse overwrite)
  5  other BLOCKED_* precondition (hook/workload/context/config/trace/oracle)
  6  gem5 or validator failure

--describe prints the exact plan/command and does not launch gem5.
"""

import argparse
import datetime
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mmu_formal_preflight as pf

GOLDEN_RE = re.compile(
    r"^W(?:9|10S|1[0-4])_(?:RESULT|INFO|LIMITATION)\b|^W14_FAULT\b")


class RunRefused(Exception):
    def __init__(self, status, message, code):
        super().__init__(message)
        self.status = status
        self.message = message
        self.code = code


def _now():
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _git_head(repo_root):
    try:
        out = subprocess.run(["git", "-C", repo_root, "rev-parse", "HEAD"],
                             capture_output=True, text=True, timeout=10)
        return out.stdout.strip() if out.returncode == 0 else ""
    except Exception:
        return ""


def _parse_eligible_index(sample):
    text = pf._s(sample.get("EventOrdinal"))
    m = re.search(r"(\d+)(?:st|nd|rd|th)?", text)
    return int(m.group(1)) if m else None


KNOWN_WORKLOADS = {"W9", "W10", "W10S", "W11", "W12", "W13", "W14"}

# Deterministic pilot defaults from the authoritative sample matrix context
# definitions.  Formal samples always carry AccessMode in the Excel.
CONTEXT_MODE = {
    "M03": {"R05": "Execute"},
    "M04": {"R05": "Execute"},
    "M05": {"R05": "Execute"},
    "M06": {"R02": "Write"},
    "M07": {"R01": "Write", "R02": "Atomic", "R03": "Read",
            "R04": "Execute", "R05": "Execute"},
    "M08": {"R05": "Write"},
}


def default_mode(model, context):
    if model in CONTEXT_MODE and context in CONTEXT_MODE[model]:
        return CONTEXT_MODE[model][context]
    if model in ("M03", "M04", "M05", "M06", "M07", "M08"):
        return "Read"
    return ""


def _read_text(path):
    try:
        with open(path, "r", errors="replace") as fh:
            return fh.read()
    except (OSError, ValueError):
        return ""


def scope_rcs_text(text, workload, context):
    """Return (scoped_text, method) selecting exactly one workload context.

    Formal samples are per-context, so the run must not execute all five
    contexts (a one-shot fault would otherwise always land on the first).
    The derived script lives only under runs/<SampleRunID>/; the source rcS
    is never modified.
    """
    if workload == "W9":
        # W9 ASIDs are kernel-assigned in process-creation order.  The
        # canonical 220/224/228/232/236 table is produced by running the
        # guest-disk /root/mmu_w9 directly for all five contexts.  Embedding
        # the binary and decoding it in the rcS forks extra shell processes
        # that consume ASID slots, shifting the workload to 234..250 and
        # making an M01 target ASID unreachable (measured:
        # TEST-M01-R02C/R02D all had asid=234..250; TEST-M01-R02B had only
        # 220 because it ran a single context).  Keep the historical shape.
        return ("#!/bin/sh\n"
                "ulimit -l unlimited 2>/dev/null || true\n"
                "for c in R01 R02 R03 R04 R05; do\n"
                "  echo \"[mmu-w9] ctx=$c\"\n"
                "  /root/mmu_w9 --ctx $c\n"
                "  echo \"[mmu-w9] ctx=$c rc=$?\"\n"
                "done\n"
                "m5 exit\n"), \
            "W9 all-contexts script (target ASID selects; guest-disk /root/mmu_w9)"
    if "--ctx all" in text:
        return text.replace("--ctx all", "--ctx %s" % context), \
            "--ctx all -> --ctx %s" % context
    if "--all" in text:
        return text.replace("--all", "--ctx %s" % context), \
            "--all -> --ctx %s" % context
    if workload == "W10S":
        # Context-specialised cold-write workload (R02 arm).
        return text, "context-specialised W10S"
    if "--ctx" in text and context in text:
        return text, "already single-context"
    return None, "unscopable"


def _assert_triple(model, workload, context, strict=True):
    if model not in pf.MODEL_WORKLOAD:
        raise RunRefused("BLOCKED_CONFIG", "unknown model %r" % model, 2)
    expected = pf.MODEL_WORKLOAD[model]
    if workload not in KNOWN_WORKLOADS:
        raise RunRefused("BLOCKED_WORKLOAD", "unknown workload %r" % workload,
                         2)
    if strict and workload != expected:
        raise RunRefused(
            "BLOCKED_CONFIG",
            "triple invalid: model %s requires workload %s, got %s" %
            (model, expected, workload), 2)
    if context not in pf.CONTEXT_IDS:
        raise RunRefused(
            "BLOCKED_CONTEXT", "context %r not in R01-R05" % context, 2)
    return expected


def _find_sample(samples, sample_id):
    for sample in samples:
        if sample.get("SampleRunID") == sample_id:
            return sample
    raise RunRefused(
        "BLOCKED_CONFIG",
        "SampleRunID %r not in authoritative 07_Sample_Matrix" % sample_id, 2)


def _as_int(text):
    """Parse an integer cell (0x... or decimal), else return None."""
    try:
        return int(str(text).strip(), 0)
    except (TypeError, ValueError):
        return None


# The M05 decoy is workload-owned: W13 maps a second 4 KiB page exactly
# 2 MiB above the target and defines W13_DECOY_VA = 0x4010200000.  The formal
# runner may not guess or scan for a live partial entry; the decoy VA is read
# from the v3.0.2 authority and passed explicitly.
M05_APPROVED_DECOY_VA = 0x4010200000
PARAM_AUTHORITY_NAME = "MMU_Parameter_Authority_v3.0.2.json"


def load_param_authority(path):
    """Load the v3.0.2 parameter authority, recording absence honestly."""
    rec = {"path": path or "", "present": False, "sha256": "",
           "data": {}, "detail": "no parameter authority supplied"}
    if not path:
        return rec
    if not os.path.isfile(path):
        rec["detail"] = "parameter authority not found: %s" % path
        return rec
    try:
        with open(path, "r", encoding="utf-8") as fh:
            rec["data"] = json.load(fh)
    except (OSError, ValueError) as exc:
        rec["detail"] = "parameter authority unreadable: %s" % exc
        return rec
    rec["present"] = True
    rec["sha256"] = _sha256(path)
    rec["detail"] = "loaded"
    return rec


def default_param_authority(excel_path):
    """Locate MMU_Parameter_Authority_v3.0.2.json next to the Excel."""
    if not excel_path:
        return ""
    cand = os.path.join(os.path.dirname(os.path.abspath(excel_path)),
                        PARAM_AUTHORITY_NAME)
    return cand if os.path.isfile(cand) else ""


def _model_fault_args(model, target_va, target_asid, mode, eligible_index,
                      context, extra, m04_decoy_pfn="0",
                      m05_decoy_table_base="0", m02_old_pfn="0",
                      m05_decoy_va="0"):
    """Model-specific CLI arguments (Phase-3 verified model parameters)."""
    if model == "M01":
        if target_asid is None:
            raise RunRefused("BLOCKED_CONFIG",
                             "M01 pilot needs --target <ASID>", 2)
        return [
            "--mmu_fault_model", "M01", "--mmu_fault_enable", "true",
            "--mmu_m01_va", hex(target_va), "--mmu_m01_asid",
            str(target_asid), "--mmu_m01_vmid", "0",
            "--mmu_m01_regime", "0", "--mmu_m01_security_state", "0",
            "--mmu_m01_n", "12",
        ]
    if model == "M02":
        if target_va is None:
            raise RunRefused("BLOCKED_CONFIG",
                             "M02 needs a target VA", 2)
        # The old_pfn is the per-context W10 target PFN resolved from an
        # independent no-fault control.  A literal is never trusted: the
        # legacy 0x83480 came from an `--ctx all` control and is wrong for a
        # scoped run (measured 0x834b6 for R02).
        if str(m02_old_pfn).strip() in ("", "0", "0x0"):
            raise RunRefused(
                "BLOCKED_MISSING_W10_PFN_MAPPING",
                "M02 old_pfn was not resolved from an independent no-fault "
                "W10 control", 5)
        return [
            "--mmu_fault_model", "M02", "--mmu_fault_enable", "true",
            "--mmu_m02_va", hex(target_va),
            "--mmu_m02_old_pfn", str(m02_old_pfn),
            "--mmu_m02_xor_mask", "1",
            "--mmu_m02_dram_lo", "0x80000000",
            "--mmu_m02_dram_hi", "0x100000000",
        ]
    if target_va is None:
        raise RunRefused("BLOCKED_CONFIG",
                         "%s needs a target VA" % model, 2)
    # Verified per-model page size: M05 targets 2 MiB L2 partial pages.
    target_n = 21 if model == "M05" else 12
    args = [
        "--mmu_fault_model", model, "--mmu_fault_enable", "true",
        "--mmu_target_va", hex(target_va), "--mmu_target_n", str(target_n),
        "--mmu_eligible_event_index", str(eligible_index),
        "--mmu_m02_dram_lo", "0x80000000",
        "--mmu_m02_dram_hi", "0x100000000",
    ]
    if mode:
        args += ["--mmu_target_mode", mode]
    extras = {
        "M03": ["--mmu_m03_candidate_asid", "-1"],
        "M04": ["--mmu_target_instance", "itb" if context == "R05" else "dtb",
                "--mmu_m04_decoy_pfn", str(m04_decoy_pfn)],
        "M05": ["--mmu_target_instance", "l2_shared",
                "--mmu_target_walk_level", "2",
                "--mmu_fault_persistence", "entry_lifetime",
                "--mmu_m05_decoy_table_base", str(m05_decoy_table_base)] + (
                    # FORMAL path (table_walker.cc:2979-2990): a nonzero decoy
                    # VA selects the live partial entry owned by that workload
                    # VA and forbids the pilot-only live_partial_scan fallback.
                    ["--mmu_m05_decoy_va", str(m05_decoy_va)]
                    if _as_int(m05_decoy_va) else []),
        "M06": ["--mmu_target_walk_level", "3"],
        "M07": ["--mmu_fault_persistence", "one_shot"],
        "M08": ["--mmu_m08_pa_xor_mask", "0x1000"],
    }
    args += extras.get(model, [])
    if extra:
        args += list(extra)
    return args


def build_plan(repo_root, out_root, *, sample=None, pilot_id=None, model=None,
               workload=None, context=None, target=None, target_mode=None,
               eligible_index=None, timeout=3600, extra=None,
               excel_path=None, csv_path=None, m04_decoy_pfn="0",
               m05_decoy_table_base="0", control_run=None,
               trace_wait_sec=120, w10_control_golden=None,
               param_authority_path=None, m05_decoy_va=None):
    """Build a fully-resolved run plan (no side effects, no gem5)."""
    excel, samples, ctx, hooks, workloads, run_script_defaults, \
        config_text = pf.build_environment(repo_root, excel_path, csv_path)
    authority_path = (param_authority_path or
                      default_param_authority(excel))
    param_authority = load_param_authority(authority_path)

    run_kind = "FORMAL" if sample else "PILOT"
    variant = None
    if sample:
        rec = _find_sample(samples, sample)
        model = rec.get("ModelID", "")
        workload = rec.get("WorkloadID", "")
        context = rec.get("ContextID", "")
        _assert_triple(model, workload, context)
        # A formal run may not start before the researcher freezes the ID.
        sid = pf.check_sample_id(rec)
        if not sid["frozen"]:
            raise RunRefused("BLOCKED_SAMPLE_ID_NOT_FROZEN",
                             sid["detail"], 5)
        # Seed gate: the deterministic literal must be paired with
        # SeedPolicy=DETERMINISTIC.  Never parse or forward a seed.
        seed = pf.check_seed(rec)
        if not seed["seed_valid"]:
            raise RunRefused(
                "BLOCKED_MISSING_SEED"
                if seed["status"] == "MISSING" else "BLOCKED_SEED_POLICY",
                seed["detail"], 3)
        # Excel WorkloadID stays W10; the internal variant selects W10S.
        variant = pf.w10s_variant(model, context)
        run_workload = variant["workload"] if variant else workload
        acc_ok, acc_detail = pf.check_access_mode(rec)
        if not acc_ok:
            raise RunRefused("BLOCKED_CONFIG", acc_detail, 5)
        run_id = rec["SampleRunID"]
        eligible_index = _parse_eligible_index(rec)
        target_mode = rec.get("AccessMode", "") or target_mode
        wl = workloads.get(run_workload, {})
        target_va, target_basis = pf.resolve_target_va(rec, wl)
        if variant:
            target_va = variant["target_va"]
            target_basis = ("%s target VA" % variant["variant"])
            target_mode = variant["mode"]
        target_asid = None
        if model == "M01":
            # W9 context -> real ASID identity from the workload trace table.
            asid = [k for k, v in pf.W9_CONTEXT_ASID.items() if v == context]
            target_asid = asid[0] if asid else None
            target_va = target_va or 0x4000000000
    else:
        if not pilot_id:
            raise RunRefused("BLOCKED_CONFIG", "--pilot needs a TEST-ID", 2)
        if not model or not workload or not context:
            raise RunRefused(
                "BLOCKED_CONFIG",
                "--pilot needs --model/--workload/--context", 2)
        # Pilots may use an experimental workload variant (e.g. W10S).  The
        # authoritative mapping is recorded, not silently overridden.
        authoritative_workload = _assert_triple(
            model, workload, context, strict=False)
        variant = pf.w10s_variant(model, context)
        run_workload = variant["workload"] if variant else workload
        rec = None
        run_id = pilot_id
        wl = workloads.get(run_workload, {})
        if target is None:
            raise RunRefused(
                "BLOCKED_CONFIG",
                "--pilot needs an explicit --target (VA; M01: ASID)", 2)
        if eligible_index is None or int(eligible_index) < 1:
            raise RunRefused(
                "BLOCKED_CONFIG",
                "--pilot needs an explicit --eligible-event-index N>=1", 2)
        target_va = None
        target_asid = None
        if model == "M01":
            try:
                target_asid = int(str(target), 0)
            except ValueError:
                raise RunRefused("BLOCKED_CONFIG",
                                 "--target must be an ASID for M01", 2)
            target_va = 0x4000000000
            target_basis = "pilot M01 fixed W9 VA"
        else:
            try:
                target_va = int(str(target), 0)
            except ValueError:
                raise RunRefused("BLOCKED_CONFIG",
                                 "--target must be a VA (0x...)", 2)
            target_basis = "pilot explicit target"
        eligible_index = int(eligible_index)
        if not target_mode:
            target_mode = default_mode(model, context)

    if not wl.get("ready"):
        raise RunRefused(
            "BLOCKED_WORKLOAD",
            "workload %s assets missing: %s" %
            (run_workload, ",".join(wl.get("missing") or ["unknown"])), 5)

    roi_lo, roi_hi = wl["roi_lo"], wl["roi_hi"]
    if variant:
        roi_lo, roi_hi = variant["roi"]
        variant_rcs = os.path.join(repo_root, variant["rcs"])
        if not os.path.isfile(variant_rcs):
            raise RunRefused(
                "BLOCKED_WORKLOAD",
                "variant rcS missing: %s" % variant_rcs, 5)
    if target_va is not None and roi_lo is not None:
        if not (roi_lo <= target_va < roi_hi):
            raise RunRefused(
                "BLOCKED_CONFIG",
                "target VA 0x%x outside ROI [0x%x,0x%x)" %
                (target_va, roi_lo, roi_hi), 5)

    # M04: the decoy PFN is never defaulted.  Resolve it from the verified
    # W12 control golden (or the explicit operator value) and block if absent.
    decoy_source = "operator"
    if model == "M04" and str(m04_decoy_pfn).strip() in ("", "0", "0x0"):
        decoy_map = pf.load_w12_decoy_map(repo_root)
        rec_d = decoy_map.get("contexts", {}).get(context)
        if not rec_d or not rec_d.get("decoy_pfn"):
            raise RunRefused(
                "BLOCKED_MISSING_DECOY_MAPPING",
                "no verified decoy PFN for M04 %s in %s" %
                (context, decoy_map.get("path")), 5)
        m04_decoy_pfn = "0x%x" % rec_d["decoy_pfn"]
        decoy_source = ("W12 control %s sha256=%s" %
                        (decoy_map["path"], decoy_map.get("sha256", "")))

    # M05: the decoy is workload-owned.  A formal run reads the decoy VA from
    # the v3.0.2 authority row, requires it to equal the final F1 pilot value
    # and the W13_DECOY_VA symbol, and passes it explicitly.  A missing/zero
    # value is a blocked run, never a live-scan guess.
    m05_decoy_va = "0"
    m05_decoy_source = "operator"
    if model == "M05":
        if sample:
            auth_data = param_authority.get("data") or {}
            auth_rec = ((auth_data.get("samples") or {}).get(run_id) or {})
            w13 = ((auth_data.get("provenance") or {}).get("W13_DECOY_VA")
                   or {})
            rec_va = str(rec.get("M05DecoyVA") or "").strip()
            rec_tb = str(rec.get("M05DecoyTableBase") or "").strip()
            auth_va = str(auth_rec.get("M05DecoyVA") or "").strip()
            auth_tb = str(auth_rec.get("M05DecoyTableBase") or "").strip()
            pilot_va = str(auth_rec.get("pilot_decoy_va") or "").strip()
            pilot_tb = str(auth_rec.get("pilot_decoy_table_base") or "").strip()
            w13_va = str(w13.get("value") or "").strip()
            if not (param_authority.get("present") and rec_va and auth_va
                    and pilot_va and w13_va and auth_tb and pilot_tb):
                raise RunRefused(
                    "BLOCKED_PARITY_EVIDENCE_MISSING",
                    "M05 %s needs the v3.0.2 authority, the Excel DecoyVA "
                    "column and pilot evidence (authority=%s present=%s "
                    "excel=%r authority=%r pilot=%r w13=%r)" %
                    (run_id, param_authority.get("path"),
                     param_authority.get("present"), rec_va, auth_va,
                     pilot_va, w13_va), 5)
            va_vals = [_as_int(rec_va), _as_int(auth_va), _as_int(pilot_va),
                       _as_int(w13_va)]
            if None in va_vals:
                raise RunRefused(
                    "BLOCKED_PARITY_M05_DECOY_VA",
                    "M05 decoy VA is not an integer: %r" % (va_vals,), 5)
            if len(set(va_vals)) != 1:
                raise RunRefused(
                    "BLOCKED_PARITY_M05_DECOY_VA",
                    "M05 decoy VA disagreement excel=%s authority=%s "
                    "pilot=%s w13=%s" % (rec_va, auth_va, pilot_va, w13_va),
                    5)
            if va_vals[0] == 0:
                raise RunRefused(
                    "BLOCKED_PARITY_M05_DECOY_VA",
                    "M05 decoy VA must not be 0", 5)
            if va_vals[0] != M05_APPROVED_DECOY_VA:
                raise RunRefused(
                    "BLOCKED_PARITY_M05_DECOY_VA",
                    "M05 decoy VA 0x%x is not the W13 workload-owned "
                    "0x%x" % (va_vals[0], M05_APPROVED_DECOY_VA), 5)
            tb_vals = [_as_int(rec_tb), _as_int(auth_tb), _as_int(pilot_tb)]
            if None in tb_vals or len(set(tb_vals)) != 1:
                raise RunRefused(
                    "BLOCKED_PARITY_M05_DECOY_TABLE_BASE",
                    "M05 decoy table base disagreement excel=%r authority=%r "
                    "pilot=%r" % (rec_tb, auth_tb, pilot_tb), 5)
            m05_decoy_va = "0x%x" % va_vals[0]
            m05_decoy_table_base = str(tb_vals[0])
            m05_decoy_source = (
                "authority v3.0.2 + Excel + final F1 pilot + W13_DECOY_VA")
        elif m05_decoy_va:
            # Pilot: an explicit operator value is recorded, never guessed.
            parsed = _as_int(m05_decoy_va)
            if not parsed:
                raise RunRefused(
                    "BLOCKED_PARITY_M05_DECOY_VA",
                    "pilot --m05-decoy-va is not a nonzero integer", 2)
            m05_decoy_va = "0x%x" % parsed
            m05_decoy_source = "pilot explicit"

    # M02: the old_pfn is the per-context W10 target PFN.  Resolve it from an
    # INDEPENDENT no-fault scoped W10 control (directory, JSON map, or a
    # single golden file).  Never fall back to a literal.  The legacy
    # `--ctx all` control reports a different PFN (0x83480) and is rejected
    # by the loader because its allocation history does not transfer.
    m02_old_pfn = "0"
    m02_source = ""
    if model == "M02":
        pfn_map = pf.load_w10_pfn_map(repo_root, w10_control_golden)
        rec_p = (pfn_map.get("contexts") or {}).get(context)
        if not rec_p or not rec_p.get("target_pfn"):
            raise RunRefused(
                "BLOCKED_MISSING_W10_PFN_MAPPING",
                "no independent no-fault W10 control PFN for %s in %s%s; "
                "run a scoped no-fault control and collect it with "
                "tools/mmu_collect_w10_pfn.py" %
                (context, pfn_map.get("path"),
                 (" (%s)" % pfn_map.get("detail"))
                 if pfn_map.get("detail") else ""), 5)
        m02_old_pfn = "0x%x" % rec_p["target_pfn"]
        m02_source = ("W10 control %s sha256=%s" %
                      (rec_p.get("source_run") or pfn_map.get("path"),
                       (rec_p.get("source_sha256") or
                        pfn_map.get("sha256") or "")[:16]))

    if eligible_index is None or eligible_index < 1:
        raise RunRefused(
            "BLOCKED_CONFIG", "eligible-event index is missing/invalid", 5)

    # Check hooks / trace / oracle for the selected model.
    model_hook = hooks.get(model, {})
    if not model_hook.get("hook_present"):
        raise RunRefused(
            "BLOCKED_HOOK",
            "no real hook site for %s in CHAOS/gem5/src" % model, 5)
    if model not in pf.VALIDATOR_MODELS:
        raise RunRefused("BLOCKED_TRACE",
                         "validator does not support %s" % model, 5)

    outdir = os.path.join(out_root, run_id)
    if os.path.isdir(outdir) and os.listdir(outdir):
        raise RunRefused(
            "BLOCKED_CONFIG",
            "refusing to overwrite existing results: %s" % outdir, 4)

    # Per-sample context isolation: derive a single-context rcS artefact
    # under the run directory.  Formal samples refuse an unscopable rcS.
    rcs_source = variant_rcs if variant else wl["rcs"]
    scoped_text, isolation = scope_rcs_text(
        _read_text(rcs_source), run_workload, context)
    if scoped_text is None:
        if sample:
            raise RunRefused(
                "BLOCKED_CONTEXT",
                "workload rcS cannot isolate context %s" % context, 5)
        isolation = "unscopable pilot (all contexts)"
        scoped_path = rcs_source
    elif variant:
        # The generated variant rcS is already single-variant.
        scoped_path = rcs_source
        isolation = "%s (pre-scoped rcS)" % variant["variant"]
    else:
        scoped_path = os.path.join(outdir, "rcS.scoped")
    scope_line = next((ln.strip() for ln in scoped_text.splitlines()
                       if "--ctx" in ln or "--all" in ln or "--cold" in ln or
                       "--warm" in ln or "--target-va" in ln),
                      "") if scoped_text else ""

    gem5 = os.path.join(repo_root, "CHAOS", "gem5", "build", "ARM",
                        "gem5.opt")
    config = os.path.join(repo_root, "configs", "fs", "lsu_b0_fs.py")
    kernel = os.path.join(repo_root, "gem5-fs", "vmlinux")
    bootloader = os.path.join(repo_root, "gem5-fs", "boot.arm64")
    for name, path in (("gem5", gem5), ("config", config), ("kernel", kernel),
                       ("bootloader", bootloader)):
        if not os.path.exists(path):
            raise RunRefused("BLOCKED_WORKLOAD",
                             "runtime asset missing: %s=%s" % (name, path), 5)

    # Provenance is part of the plan: the gem5 binary, the four MMU sources
    # and the run workload are hashed BEFORE launch and re-checked before
    # execute_plan starts gem5.  Every sample_manifest.json therefore carries
    # the actual hashes (never only a path).
    gem5_sha256 = _sha256(gem5)
    source_sha256 = {}
    for rel in MMU_SOURCE_FILES:
        src_path = os.path.join(repo_root, rel)
        if not os.path.isfile(src_path):
            raise RunRefused("BLOCKED_SOURCE",
                             "MMU source missing: %s" % src_path, 5)
        source_sha256[rel] = _sha256(src_path)
    workload_binary = wl.get("binary", "")
    if not workload_binary or not os.path.isfile(workload_binary):
        raise RunRefused("BLOCKED_WORKLOAD",
                         "run workload binary missing: %s" % workload_binary, 5)
    workload_sha256 = _sha256(workload_binary)

    # Independent control oracle: an explicit --control-run wins; otherwise
    # the preflight's per-context/per-workload mapping is used for BOTH formal
    # and pilot runs so the SHA256 is always recorded (present or missing).
    if control_run:
        ctrl_path = (control_run if os.path.isabs(control_run)
                     else os.path.join(repo_root, control_run))
        if not os.path.isfile(ctrl_path):
            raise RunRefused("BLOCKED_ORACLE",
                             "explicit --control-run not found: %s" % ctrl_path,
                             5)
        control = {
            "present": True, "path": ctrl_path, "line": "",
            "sha256": _sha256(ctrl_path),
            "detail": "explicit --control-run sha256=%s" %
                      _sha256(ctrl_path)[:16],
            "source": "EXPLICIT_OVERRIDE",
        }
    else:
        control = pf.control_oracle_for(repo_root, model, workload, context)
        control["source"] = "PREFLIGHT_RESOLVED"

    disk = os.path.join(outdir, "disk.img")
    run_dir = os.path.join(outdir, "run")
    command = [
        gem5, "--outdir", run_dir, config,
        "--kernel", kernel, "--disk", disk, "--bootloader", bootloader,
        "--cpu", "O3",
        "--restore-checkpoint", wl["ckpt"], "--readfile", scoped_path,
        "--chaos_propagation",
        "--prop_mmu_va_lo", hex(roi_lo),
        "--prop_mmu_va_hi", hex(roi_hi),
        "--prop_run_id", run_id, "--prop_sample_run_id", run_id,
        "--prop_mmu_trace", "--prop_write_log", "on",
    ]
    command += _model_fault_args(model, target_va, target_asid,
                                 target_mode, eligible_index, context, extra,
                                 m04_decoy_pfn=m04_decoy_pfn,
                                 m05_decoy_table_base=m05_decoy_table_base,
                                 m02_old_pfn=m02_old_pfn,
                                 m05_decoy_va=m05_decoy_va)

    # Hard guarantee: no seed is ever forwarded to gem5.  There is no --seed
    # in configs/fs/lsu_b0_fs.py nor in configs/se/arm_chaos_fs.py, and any
    # future seed-bearing flag is rejected here instead of being passed.
    seed_flags = [arg for arg in command
                  if str(arg).startswith("--") and "seed" in str(arg).lower()]
    if seed_flags:
        raise RunRefused(
            "BLOCKED_SEED_POLICY",
            "run command contains seed flag(s) %s; deterministic policy "
            "forbids passing a seed to gem5" % seed_flags, 3)

    seed_info = pf.check_seed(rec) if rec else {
        "seed_raw": "", "seed_valid": False, "seed_present": False,
        "seed_policy": "<unset>", "seed_source": "<unset>",
        "status": "PILOT_NO_SEED", "seed_literal_deterministic": False,
    }
    seed_raw = seed_info["seed_raw"]
    return {
        "run_kind": run_kind,
        "formal": run_kind == "FORMAL",
        "run_id": run_id,
        "sample_run_id": rec.get("SampleRunID", "") if rec else "",
        "sub_task_id": rec.get("SubTaskID", "") if rec else "",
        "model": model,
        "workload": workload,
        "workload_variant": variant["variant"] if variant else workload,
        "run_workload": run_workload,
        "context": context,
        "sample_id_status": (pf.check_sample_id(rec)["status_raw"]
                             if rec else ""),
        "decoy_pfn": m04_decoy_pfn,
        "decoy_source": decoy_source,
        "m05_decoy_va": m05_decoy_va,
        "m05_decoy_table_base": m05_decoy_table_base,
        "m05_decoy_source": m05_decoy_source,
        "m02_old_pfn": m02_old_pfn,
        "m02_old_pfn_source": m02_source,
        "control_oracle": control,
        "control_oracle_sha256": control.get("sha256", ""),
        "control_oracle_source": control.get("source", ""),
        "control_run": control.get("path", ""),
        "dynamic_context": rec.get("DynamicContext", "") if rec else "",
        "target_event": rec.get("TargetEvent", "") if rec else "",
        "eligible_event_index": eligible_index,
        "target_va": target_va,
        "target_va_source": target_basis if sample else "pilot explicit",
        "target_instruction": rec.get("TargetInstruction", "") if rec else "",
        "target_n": 21 if model == "M05" else 12,
        "authoritative_workload": pf.MODEL_WORKLOAD.get(model, ""),
        "authoritative_workload_match":
            (rec.get("WorkloadID", "") == pf.MODEL_WORKLOAD.get(model, ""))
            if rec else
            (workload == pf.MODEL_WORKLOAD.get(model, "")),
        "target_asid": target_asid,
        "target_mode": target_mode,
        "roi": [roi_lo, roi_hi],
        "seed": seed_raw,
        # The literal N/A_DETERMINISTIC is a valid deterministic value under
        # SeedPolicy=DETERMINISTIC.  It is recorded verbatim and never
        # parsed/derived/forwarded.
        "seed_present": bool(seed_info.get("seed_valid")),
        "seed_valid": bool(seed_info.get("seed_valid")),
        "seed_policy": seed_info.get("seed_policy", "<unset>"),
        "seed_source": seed_info.get("seed_source", "<unset>"),
        "seed_status": seed_info.get("status", "<unset>"),
        "seed_literal_deterministic": bool(
            seed_info.get("seed_literal_deterministic")),
        "seed_used_by_gem5": False,
        "seed_delivery": "not_passed_to_gem5",
        "authority_excel": excel,
        "authority_excel_source": ctx.get("excel_source", "<unknown>"),
        "authority_csv": ctx.get("csv"),
        "authority_csv_source": ctx.get("csv_source", "<unknown>"),
        "parameter_authority": {
            "path": param_authority.get("path", ""),
            "present": bool(param_authority.get("present")),
            "sha256": param_authority.get("sha256", ""),
            "detail": param_authority.get("detail", ""),
        },
        "outdir": outdir,
        "disk_image": disk,
        "checkpoint": wl["ckpt"],
        "rcs_source": rcs_source,
        "rcs_pre_scoped": bool(variant),
        "rcs": scoped_path,
        "rcs_scoped": scoped_path if scoped_path != rcs_source else "",
        "context_isolation": isolation,
        "rcs_scoped_preview": scope_line,
        "gem5": gem5,
        "gem5_sha256": gem5_sha256,
        "source_sha256": source_sha256,
        "workload_binary": workload_binary,
        "workload_sha256": workload_sha256,
        "command": command,
        "command_shell": shlex.join(command),
        "trace_wait_sec": trace_wait_sec,
        "timeout_sec": timeout,
        "created_at_utc": _now(),
        "git_head": _git_head(repo_root),
        "repo_root": repo_root,
        "excel": excel,
    }


def _copy_if_exists(src, dst):
    if src and os.path.exists(src):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        return True
    return False


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_if_file(path):
    return _sha256(path) if path and os.path.isfile(path) else ""


# The four MMU sources whose behaviour the formal samples depend on.  Each
# manifest records their content hash next to the binary hash.
MMU_SOURCE_FILES = [
    os.path.join("CHAOS", "gem5", "src", "arch", "arm", "mmu.cc"),
    os.path.join("CHAOS", "gem5", "src", "arch", "arm", "table_walker.cc"),
    os.path.join("CHAOS", "gem5", "src", "arch", "arm", "table_walker.hh"),
    os.path.join("CHAOS", "gem5", "src", "arch", "arm", "tlb.cc"),
    # [M08] the squash-witness gate lives in CHAOSPropagation; its source is
    # part of the frozen provenance even though it is not an MMU file.
    os.path.join("CHAOS", "gem5", "src", "cpu", "o3",
                 "CHAOSPropagation", "CHAOSPropagation.cc"),
    os.path.join("CHAOS", "gem5", "src", "cpu", "o3",
                 "CHAOSPropagation", "CHAOSPropagation.hh"),
]

TRACE_READ_ERROR_PATTERNS = (
    "truncated", "eof", "badgzipfile", "crc check", "corrupt gzip",
    "trace read error", "unexpected end of file", "not a gzip",
)


def _file_signature(path):
    try:
        st = os.stat(path)
    except OSError:
        return None
    return (st.st_size, st.st_mtime_ns)


def wait_for_stable_file(path, checks=2, poll_sec=1.0, timeout_sec=120.0):
    """Wait until size+mtime are identical across `checks` consecutive polls.

    Returns (stable, signature, detail).  A missing file is never treated as
    stable: the caller must record that honestly.
    """
    deadline = time.time() + timeout_sec
    last = None
    consecutive = 0
    while time.time() < deadline:
        sig = _file_signature(path)
        if sig is not None and sig == last:
            consecutive += 1
            if consecutive >= checks - 1:
                return True, sig, "stable"
        else:
            consecutive = 0
            last = sig
        time.sleep(poll_sec)
    if last is None:
        return False, None, "file never appeared within %ss" % timeout_sec
    return False, last, ("size/mtime did not stabilise across %d checks "
                         "within %ss" % (checks, timeout_sec))


def _trace_read_error(log_path):
    """Return the first real trace-read error line, or '' when none."""
    text = _read_text(log_path).lower()
    for line in text.splitlines():
        if any(pattern in line for pattern in TRACE_READ_ERROR_PATTERNS):
            return line.strip()
    return ""


def _write_golden(terminal_path, out_path):
    if not os.path.exists(terminal_path):
        return 0
    count = 0
    with open(terminal_path, "r", errors="replace") as src, \
            open(out_path, "w") as dst:
        for line in src:
            if GOLDEN_RE.match(line):
                dst.write(line)
                count += 1
    return count


def execute_plan(plan, validator_path):
    """Actually run gem5.  Not invoked by this task; kept for production."""
    # Fail closed if any provenance changed between plan and execution.
    current_bin = _sha256(plan["gem5"])
    if plan.get("gem5_sha256") and current_bin != plan["gem5_sha256"]:
        raise RunRefused(
            "BLOCKED_BINARY",
            "gem5 binary changed between plan and execution: plan=%s now=%s"
            % (plan["gem5_sha256"], current_bin), 5)
    for rel, want in (plan.get("source_sha256") or {}).items():
        got = _sha256_if_file(os.path.join(plan["repo_root"], rel))
        if got != want:
            raise RunRefused(
                "BLOCKED_SOURCE",
                "MMU source changed between plan and execution: %s plan=%s "
                "now=%s" % (rel, want, got or "<missing>"), 5)
    if plan.get("workload_sha256"):
        got = _sha256_if_file(plan.get("workload_binary", ""))
        if got != plan["workload_sha256"]:
            raise RunRefused(
                "BLOCKED_WORKLOAD",
                "workload binary changed between plan and execution: %s "
                "plan=%s now=%s" % (plan.get("workload_binary", ""),
                                    plan["workload_sha256"],
                                    got or "<missing>"), 5)

    outdir = plan["outdir"]
    if os.path.isdir(outdir) and os.listdir(outdir):
        raise RunRefused("BLOCKED_CONFIG",
                         "refusing to overwrite %s" % outdir, 4)
    for sub in ("Config", "Run_Log", "Trace", "SHA256", "Validation", "run"):
        os.makedirs(os.path.join(outdir, sub), exist_ok=True)

    # Materialise the single-context rcS derived in build_plan (if any).
    # A variant rcS is already single-variant and must be used verbatim.
    if plan.get("rcs_pre_scoped"):
        scoped = _read_text(plan["rcs_source"])
    elif plan.get("rcs_scoped"):
        scoped, _method = scope_rcs_text(
            _read_text(plan["rcs_source"]), plan["run_workload"],
            plan["context"])
        if scoped is None:
            raise RunRefused(
                "BLOCKED_CONTEXT",
                "workload rcS cannot isolate context %s" % plan["context"], 5)
        with open(plan["rcs_scoped"], "w") as fh:
            fh.write(scoped)

    # Fresh disk copy per run (reflink when the filesystem supports it).
    try:
        rc = subprocess.run(["cp", "--reflink=auto",
                             os.path.join(plan["repo_root"], "runs", "disks",
                                          "mmu_template.img"),
                             plan["disk_image"]]).returncode
        if rc != 0:
            raise OSError("cp rc=%d" % rc)
    except (OSError, FileNotFoundError):
        shutil.copy2(os.path.join(plan["repo_root"], "runs", "disks",
                                  "mmu_template.img"), plan["disk_image"])

    command_txt = os.path.join(outdir, "Run_Log", "command.txt")
    with open(command_txt, "w") as fh:
        fh.write(plan["command_shell"] + "\n")

    stdout_path = os.path.join(outdir, "Run_Log", "gem5_stdout.log")
    timed_out = False
    started = _now()
    with open(stdout_path, "w") as log:
        try:
            proc = subprocess.run(plan["command"], stdout=log,
                                  stderr=subprocess.STDOUT,
                                  timeout=plan["timeout_sec"])
            rc = proc.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            rc = 124
            log.write("\n[mmu_formal_runner] TIMEOUT after %ss\n" %
                      plan["timeout_sec"])
    with open(os.path.join(outdir, "Run_Log", "gem5_exit_code.txt"),
              "w") as fh:
        fh.write("%d\n" % rc)

    run_dir = os.path.join(outdir, "run")

    # Wait for the propagation trace to be quiescent before copying or
    # validating.  A validator must never read a gzip stream that gem5 (or a
    # concurrent writer) is still appending to; the old code copied and
    # validated immediately, which produced stale verdicts on real trees.
    trace_src = os.path.join(run_dir, "prop_evt.txt.gz")
    trace_csv_src = os.path.join(run_dir, "prop_trace.csv.gz")
    wait_sec = float(plan.get("trace_wait_sec") or 120)
    evt_stable, evt_sig, evt_detail = wait_for_stable_file(
        trace_src, checks=2, poll_sec=1.0, timeout_sec=wait_sec)
    csv_stable, csv_sig, csv_detail = (True, None, "absent")
    if os.path.exists(trace_csv_src):
        csv_stable, csv_sig, csv_detail = wait_for_stable_file(
            trace_csv_src, checks=2, poll_sec=1.0, timeout_sec=wait_sec)

    def _trace_stat(sig):
        return {"size": sig[0] if sig else None,
                "mtime_ns": sig[1] if sig else None}

    trace_stability = {
        "prop_evt": dict({"path": trace_src, "stable": evt_stable,
                          "detail": evt_detail}, **_trace_stat(evt_sig)),
        "prop_trace": dict({"path": trace_csv_src, "stable": csv_stable,
                            "detail": csv_detail}, **_trace_stat(csv_sig)),
    }
    trace_read_error = ""
    if not evt_stable:
        trace_read_error = "prop_evt.txt.gz not stable: %s" % evt_detail
    elif not csv_stable:
        trace_read_error = "prop_trace.csv.gz not stable: %s" % csv_detail

    _copy_if_exists(os.path.join(run_dir, "config.ini"),
                    os.path.join(outdir, "Config", "config.ini"))
    _copy_if_exists(os.path.join(run_dir, "config.json"),
                    os.path.join(outdir, "Config", "config.json"))
    _copy_if_exists(trace_src, os.path.join(outdir, "Trace",
                                            "prop_evt.txt.gz"))
    _copy_if_exists(trace_csv_src, os.path.join(outdir, "Trace",
                                                "prop_trace.csv.gz"))
    terminal = os.path.join(outdir, "Run_Log", "board.terminal")
    _copy_if_exists(os.path.join(run_dir, "board.terminal"), terminal)
    _copy_if_exists(os.path.join(run_dir, "stats.txt"),
                    os.path.join(outdir, "Run_Log", "stats.txt"))
    # This file is the FAULTED run's own terminal observation, not an
    # independent golden control.  Name it honestly.
    observed_path = os.path.join(outdir, "Run_Log", "observed_output.txt")
    observed_count = _write_golden(terminal, observed_path)

    # SHA256 manifest over the captured artifacts plus the exact provenance
    # inputs that produced them.
    hashes = []
    for rel in ("Config/config.ini", "Config/config.json",
                "Trace/prop_evt.txt.gz", "Trace/prop_trace.csv.gz",
                "Run_Log/board.terminal", "Run_Log/observed_output.txt",
                "Run_Log/gem5_stdout.log", "Run_Log/command.txt",
                "Run_Log/stats.txt", "Run_Log/gem5_exit_code.txt",
                "rcS.scoped", "disk.img"):
        path = os.path.join(outdir, rel)
        if os.path.isfile(path):
            hashes.append("%s  %s" % (_sha256(path), rel))
    if plan.get("gem5_sha256"):
        hashes.append("%s  gem5:%s" % (plan["gem5_sha256"], plan["gem5"]))
    for rel, want in (plan.get("source_sha256") or {}).items():
        hashes.append("%s  source:%s" % (want, rel))
    if plan.get("workload_sha256"):
        hashes.append("%s  workload:%s" % (plan["workload_sha256"],
                                           plan["workload_binary"]))
    with open(os.path.join(outdir, "SHA256", "SHA256SUMS.txt"), "w") as fh:
        fh.write("\n".join(hashes) + "\n")

    manifest_path = os.path.join(outdir, "sample_manifest.json")
    plan_out = dict(plan)
    plan_out.update({
        "gem5_exit_code": rc,
        "timed_out": timed_out,
        "started_at_utc": started,
        "finished_at_utc": _now(),
        "observed_line_count": observed_count,
        "observed_output": observed_path,
        "sha256_manifest": os.path.join(outdir, "SHA256", "SHA256SUMS.txt"),
        "trace_stability": trace_stability,
        "trace_read_error": trace_read_error,
    })
    with open(manifest_path, "w") as fh:
        json.dump(plan_out, fh, indent=2, sort_keys=True)

    # Automatic terminal-aware validation, only after the trace is stable.
    validation_dir = os.path.join(outdir, "Validation")
    os.makedirs(validation_dir, exist_ok=True)
    v_json = os.path.join(validation_dir, "verdict.json")
    v_md = os.path.join(validation_dir, "verdict.md")
    v_log = os.path.join(validation_dir, "validator_stdout.log")
    v_cmd = [sys.executable, validator_path, "--run-dir", outdir,
             "--model", plan["model"], "--workload", plan["run_workload"],
             "--context", plan["context"], "--report-json", v_json,
             "--report-md", v_md]
    ctrl = plan.get("control_oracle") or {}
    if ctrl.get("path"):
        v_cmd += ["--control-run", ctrl["path"]]

    if not evt_stable or not csv_stable:
        plan_out.update({
            "validator_status": "SKIPPED_TRACE_UNSTABLE",
            "validator_retry": 0,
            "validator_exit_code": None,
            "trace_read_error": trace_read_error,
        })
        with open(manifest_path, "w") as fh:
            json.dump(plan_out, fh, indent=2, sort_keys=True)
        return 6, plan_out, -1

    def _run_validator():
        with open(v_log, "w") as fh:
            return subprocess.run(v_cmd, stdout=fh,
                                  stderr=subprocess.STDOUT).returncode

    vrc = _run_validator()
    read_err = _trace_read_error(v_log)
    retry = 0
    if vrc != 0 and read_err:
        # The stream may have been truncated/EOF at first read.  Re-check
        # stability and re-validate exactly once; never hide a persisting
        # error.
        stable2, sig2, detail2 = wait_for_stable_file(
            trace_src, checks=2, poll_sec=1.0, timeout_sec=wait_sec)
        trace_stability["prop_evt_retry"] = dict(
            {"path": trace_src, "stable": stable2, "detail": detail2},
            **_trace_stat(sig2))
        if stable2:
            vrc = _run_validator()
            retry = 1
            read_err = _trace_read_error(v_log)
    if read_err:
        trace_read_error = read_err
    plan_out.update({
        "trace_stability": trace_stability,
        "trace_read_error": trace_read_error,
        "validator_retry": retry,
        "validator_exit_code": vrc,
        "validator_status": ("PASS" if vrc == 0 and not trace_read_error
                             else "FAIL"),
    })
    with open(manifest_path, "w") as fh:
        json.dump(plan_out, fh, indent=2, sort_keys=True)
    if vrc != 0 or trace_read_error:
        return 6, plan_out, vrc
    return (0 if rc == 0 else 6), plan_out, 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="MMU Phase-3 formal runner (authoritative Excel; never "
                    "generates seeds)")
    ap.add_argument("--repo-root", default=os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument("--excel", default=None,
                    help="explicit authoritative Excel override (default: "
                         "frozen authority copy, then design package)")
    ap.add_argument("--csv", default=None,
                    help="explicit MMU_Sample_Matrix.csv override (default: "
                         "frozen authority copy, then design package)")
    ap.add_argument("--out-root", default=None,
                    help="default: <repo>/runs")
    ap.add_argument("--timeout-sec", type=int, default=3600)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--sample", help="formal SampleRunID")
    mode.add_argument("--pilot", help="PILOT TEST-ID")
    ap.add_argument("--model")
    ap.add_argument("--workload")
    ap.add_argument("--context")
    ap.add_argument("--target", help="target VA (M01: target ASID)")
    ap.add_argument("--target-mode", default=None)
    ap.add_argument("--eligible-event-index", type=int, default=None)
    ap.add_argument("--extra-gem5-arg", action="append", default=[],
                    help="extra argument forwarded to gem5 (pilot)")
    ap.add_argument("--m04-decoy-pfn", default="0",
                    help="M04 decoy PFN from the W12 control run "
                         "(0 = auto-pick the first legal same-N entry)")
    ap.add_argument("--m05-decoy-table-base", default="0",
                    help="M05 decoy L3 table base PA (0 = derive from the "
                         "workload-owned decoy VA)")
    ap.add_argument("--m05-decoy-va", default=None,
                    help="pilot-only explicit M05 decoy VA; formal samples "
                         "read it from the v3.0.2 parameter authority")
    ap.add_argument("--param-authority", default=None,
                    help="v3.0.2 parameter authority JSON (default: "
                         "MMU_Parameter_Authority_v3.0.2.json next to the "
                         "authoritative Excel)")
    ap.add_argument("--control-run", default=None,
                    help="explicit independent control-run directory/file; "
                         "its SHA256 is recorded in the manifest (default: "
                         "resolved by the preflight mapping)")
    ap.add_argument("--w10-control-golden", default=None,
                    help="independent no-fault W10 control (directory, JSON "
                         "map, or golden file) used to resolve the M02 "
                         "per-context old_pfn (default: "
                         "phase3/formal/w10_pfn_map.json, then runs/)")
    ap.add_argument("--trace-wait-sec", type=float, default=120.0,
                    help="max seconds to wait for prop_evt.txt.gz size/mtime "
                         "to stabilise after gem5 exits")
    ap.add_argument("--describe", "--dry-run", dest="describe",
                    action="store_true",
                    help="print the plan/command; never launch gem5")
    args = ap.parse_args(argv)

    repo_root = os.path.abspath(args.repo_root)
    out_root = args.out_root or os.path.join(repo_root, "runs")
    validator = os.path.join(repo_root, "tools",
                             "mmu_formal_validate.py")

    # Formal seed gate runs BEFORE any workload/hook/config check so that a
    # missing authoritative seed always yields exit 3, never a different
    # blocker.  The other checks still run in --describe/preflight reports.
    if args.sample:
        try:
            excel, samples, _ctx, _hooks, _wls, _rs, _cfg = \
                pf.build_environment(repo_root, args.excel, args.csv)
            rec = _find_sample(samples, args.sample)
            _assert_triple(rec.get("ModelID", ""), rec.get("WorkloadID", ""),
                           rec.get("ContextID", ""))
        except RunRefused as exc:
            print(json.dumps({
                "run_kind": "FORMAL", "run_id": args.sample,
                "status": exc.status, "would_run": False,
                "exit_code": exc.code, "message": exc.message,
            }, indent=2, sort_keys=True))
            return exc.code
        except pf.AuthoritativeError as exc:
            print("RUNNER ERROR: %s" % exc, file=sys.stderr)
            return 2
        sid = pf.check_sample_id(rec)
        if not sid["frozen"]:
            print(json.dumps({
                "run_kind": "FORMAL",
                "run_id": args.sample,
                "status": "BLOCKED_SAMPLE_ID_NOT_FROZEN",
                "would_run": False,
                "exit_code": 5,
                "sample_id_status": sid["status_raw"],
                "message": ("the authoritative SampleIDStatus is not frozen; "
                            "the researcher must freeze SampleRunID before a "
                            "formal run"),
            }, indent=2, sort_keys=True))
            return 5
        seed = pf.check_seed(rec)
        if not seed["seed_valid"]:
            blocked_status = ("BLOCKED_MISSING_SEED"
                              if seed["status"] == "MISSING"
                              else "BLOCKED_SEED_POLICY")
            print(json.dumps({
                "run_kind": "FORMAL",
                "run_id": args.sample,
                "status": blocked_status,
                "would_run": False,
                "exit_code": 3,
                "seed_cell": seed["seed_raw"],
                "seed_policy": seed["seed_policy"],
                "seed_source": seed["seed_source"],
                "seed_used_by_gem5": False,
                "message": ("seed gate failed: " + seed["detail"] +
                            "; no seed is generated, hashed, timestamped, "
                            "coerced or passed to gem5"),
            }, indent=2, sort_keys=True))
            return 3

    try:
        plan = build_plan(
            repo_root, out_root, sample=args.sample, pilot_id=args.pilot,
            model=args.model, workload=args.workload, context=args.context,
            target=args.target, target_mode=args.target_mode,
            eligible_index=args.eligible_event_index,
            timeout=args.timeout_sec, extra=args.extra_gem5_arg,
            excel_path=args.excel, csv_path=args.csv,
            m04_decoy_pfn=args.m04_decoy_pfn,
            m05_decoy_table_base=args.m05_decoy_table_base,
            control_run=args.control_run,
            trace_wait_sec=args.trace_wait_sec,
            w10_control_golden=args.w10_control_golden,
            param_authority_path=args.param_authority,
            m05_decoy_va=args.m05_decoy_va)
    except RunRefused as exc:
        print(json.dumps({
            "run_kind": "FORMAL" if args.sample else "PILOT",
            "run_id": args.sample or args.pilot,
            "status": exc.status,
            "would_run": False,
            "exit_code": exc.code,
            "message": exc.message,
        }, indent=2, sort_keys=True))
        return exc.code
    except pf.AuthoritativeError as exc:
        print("RUNNER ERROR: %s" % exc, file=sys.stderr)
        return 2

    # Formal seed gate is evaluated before the general blockers so that a
    # missing seed is always reported as exit 3, exactly as specified.
    if plan["formal"] and not plan["seed_valid"]:
        blocked_status = ("BLOCKED_MISSING_SEED"
                          if plan["seed_status"] == "MISSING"
                          else "BLOCKED_SEED_POLICY")
        print(json.dumps({
            "run_kind": "FORMAL",
            "run_id": plan["run_id"],
            "status": blocked_status,
            "would_run": False,
            "exit_code": 3,
            "seed_cell": plan["seed"],
            "seed_policy": plan["seed_policy"],
            "seed_source": plan["seed_source"],
            "seed_used_by_gem5": False,
            "message": ("seed gate failed: " + plan["seed_status"] +
                        "; no seed is generated, hashed, timestamped, "
                        "coerced or passed to gem5"),
            "command": plan["command"],
        }, indent=2, sort_keys=True))
        return 3

    if args.describe:
        print(json.dumps({
            "status": ("READY" if plan["seed_valid"] or not plan["formal"]
                       else "BLOCKED_SEED_POLICY"),
            "would_run": False,
            "plan": plan,
        }, indent=2, sort_keys=True, default=str))
        return 0

    try:
        rc, plan_out, vrc = execute_plan(plan, validator)
    except RunRefused as exc:
        print(json.dumps({
            "run_kind": plan["run_kind"],
            "run_id": plan["run_id"],
            "status": exc.status,
            "would_run": False,
            "exit_code": exc.code,
            "message": exc.message,
        }, indent=2, sort_keys=True))
        return exc.code

    print(json.dumps({
        "run_kind": plan["run_kind"],
        "run_id": plan["run_id"],
        "seed": plan.get("seed", ""),
        "seed_policy": plan.get("seed_policy", "<unset>"),
        "seed_source": plan.get("seed_source", "<unset>"),
        "seed_used_by_gem5": plan.get("seed_used_by_gem5", False),
        "gem5_sha256": plan.get("gem5_sha256", ""),
        "workload_sha256": plan.get("workload_sha256", ""),
        "control_oracle_sha256": plan.get("control_oracle_sha256", ""),
        "validator_status": plan_out.get("validator_status", ""),
        "trace_read_error": plan_out.get("trace_read_error", ""),
        "gem5_exit_code": plan_out["gem5_exit_code"],
        "timed_out": plan_out["timed_out"],
        "validator_exit_code": vrc,
        "outdir": plan["outdir"],
        "exit_code": rc,
    }, indent=2, sort_keys=True))
    return rc


if __name__ == "__main__":
    sys.exit(main())
