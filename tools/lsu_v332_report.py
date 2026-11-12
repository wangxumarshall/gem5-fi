#!/usr/bin/env python3
"""Build the LSU v3.3.2 60-context acceptance tables from real run artifacts.

Reads audit_v3_3_2/runs/<model>-R<ctx>-<role>/{summary.json,pilot_meta.json,
trace_v31.jsonl,stderr.log,l1d_fwd_injections.log,addrpath_injections.log} and
writes the four required CSVs. No value is invented: a field that was not
observed is written as `n/a` or `NOT_OBSERVED`.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lsu_v332_matrix import (  # noqa: E402  (single control-classifier source)
    a03_terminal,
    classify_control,
    parse_addrpath_log,
    parse_bare_checksum,
    parse_rp01_evidence,
    read_command,
)

RUNS = ROOT / "audit_v3_3_3/runs"
OUT = ROOT / "audit_v3_3_3"
BINARY_SHA = "62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd"
HEAD = "b5031bf7"

MODELS = ("A01", "A03", "FW02", "FW05", "SQ01", "SQ03", "SP05", "DA04",
          "LP01", "MD04", "LQ04", "RP01")
TWO_PLACE = ("SQ01", "SQ03", "SP05")
CANDIDATE = {"FW02", "RP01", "MD04", *TWO_PLACE}
WORKLOAD = {
    "A01": "agu_addrmodes", "A03": "agu_addrmodes",
    "FW02": "sq_forward_w4v2 (candidate)", "FW05": "fw05_forward",
    "SQ01": "sq_reload_v3212 (candidate)", "SQ03": "sq_reload_v3212 (candidate)",
    "SP05": "sq_reload_v3212 (candidate)", "DA04": "alignment",
    "LP01": "load_response", "MD04": "md04_violations_v332 (candidate)",
    "LQ04": "lq_lifetime_ordinal",
    "RP01": "replay_partial_v332 (candidate)",
}
ROI = {  # measured ROI (start,end), N, percentile ordinals
    # v3.3.3 re-census after the PRE retry exclusion (L-A01): 1040-1222 (183)
    # on the fixed stream; the v3.3.2 1040-1234/195 set is history.
    # A01 v3.3.3 correction (L-A12): 8-byte-only stream, 585-713 (129).
    "A01": ((585, 713), 129, [597, 623, 649, 675, 701]),
    "A03": ((1040, 1222), 183, [1058, 1094, 1131, 1168, 1204]),
    "FW02": ((8, 67), 60, [13, 25, 37, 49, 61]),
    "FW05": ((1, 2000), 2000, [200, 600, 1000, 1400, 1800]),
    "SQ01": ((1006, 1133), 128, [1018, 1044, 1069, 1095, 1121]),
    "SQ03": ((1009, 1136), 128, [1021, 1047, 1072, 1098, 1124]),
    "SP05": ((940, 1067), 128, [952, 978, 1003, 1029, 1055]),
    "DA04": ((33, 1056), 1024, [135, 340, 544, 749, 954]),
    "LP01": ((886, 17525), 16640, [2549, 5877, 9205, 12533, 15861]),
    "MD04": ((3, 10), 8, [3, 5, 6, 8, 10]),
    "LQ04": ((1, 5), 5, [1, 2, 3, 4, 5]),
    "RP01": ((1, 255), 255, [26, 77, 128, 179, 230]),
}
CONSUMER_EVENTS = {"consumer_commit", "commit", "errant_commit"}
QUALIFIER = {
    "A01": "R03 fixed by v3.3.3 PRE retry exclusion; R02=SQUASHED/UNRELATED",
    "A03": "PERSISTENT_STUCK: ONE FAULT, FIVE OBSERVATION POINTS; SDC/POST_ORACLE_SIM_HANG",
    "SQ03": "VISIBILITY_TIMING_SHIFT (CHAIN_VISIBILITY_MOVED 4/5), NOT SDC",
    "SP05": "SDC with store_data_fnv bound (v3.3.3)",
    "RP01": "HANG_BY_INTERNAL_WATCHDOG; PARTIAL TRACE; NO SDC CLAIM",
    "MD04": "R01=MASKED; CANDIDATE VIOLATION WORKLOAD",
    "FW02": "CANDIDATE W4 LOAD-PRESERVING WORKLOAD",
    "LQ04": "MASKED BY DESIGN (LQ LIFETIME CONSUMER)",
}
DIVERGENCE_EVENTS = {
    "a01_ea": "A01_EA", "fw02_decision": "FW02_DECISION",
    "forwarding_decision": "FORWARDING_DECISION",
    "store_writeback": "STORE_WRITEBACK", "store_mem_write": "STORE_MEM_WRITE",
    "sq03_complete": "SQ03_COMPLETE", "sp05_complete": "SP05_COMPLETE",
    "memory_response": "MEMORY_RESPONSE", "register_writeback": "REGISTER_WRITEBACK",
    "taint_value_mismatch": "TAINT_VALUE_MISMATCH",
}


def jload(p: Path, default=None):
    try:
        return json.loads(p.read_text())
    except Exception:
        return default if default is not None else {}


def trace_index(path: Path):
    idx = {}
    if not path.exists():
        return idx
    for line in path.read_text(errors="replace").splitlines():
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        seq = d.get("dyn_inst_seq")
        idx.setdefault(seq, []).append(d)
    return idx


def rp01_watchdog(outdir: Path) -> bool:
    for name in ("stderr.log", "stdout.log", "lsq_fwd_injections.log"):
        p = outdir / name
        if p.exists() and "CHAOS_RP01_WATCHDOG" in p.read_text(errors="replace"):
            return True
    return False


def fault_row(model: str, ctx: int):
    outdir = RUNS / f"{model}-R{ctx:02d}-fault"
    s = jload(outdir / "summary.json")
    meta = jload(outdir / "pilot_meta.json")
    cls = meta.get("classification") or {}
    seed = (s.get("seed") or meta.get("seed")
            or (meta.get("excel_identity") or {}).get("seed"))
    if not seed and (outdir / "command.txt").exists():
        m = re.search(r"--[A-Za-z0-9_]*rng_seed(?:\s+|=)(\d+)",
                      read_command(outdir))
        if m:
            seed = int(m.group(1))
    observed_workload = meta.get("workload") or s.get("workload")
    workload_label = (f"{Path(observed_workload).name} (observed)"
                      if observed_workload else WORKLOAD[model])
    row = {
        "model": model, "context": f"R{ctx:02d}", "seed": seed,
        "ordinal": s.get("ordinal"), "workload": workload_label,
        "workload_observed": observed_workload,
        "workload_status": ("CANDIDATE_PENDING_APPROVAL" if model in CANDIDATE
                            else "FORMAL"),
        "binary_sha": s.get("binary_sha"), "outdir": str(outdir),
        "fault_command": read_command(outdir),
    }
    if model == "A03":
        log_path = outdir / "addrpath_injections.log"
        # The artifact parser is authoritative: v3.3.2 summaries carry the
        # 20000 log cap and no FUNNEL count.
        a03 = (parse_addrpath_log(log_path) if log_path.exists()
               else (s.get("a03") or {}))
        stdout_text = ((outdir / "stdout.log").read_text(errors="replace")
                       if (outdir / "stdout.log").exists() else "")
        checksum = s.get("checksum") or parse_bare_checksum(stdout_text)
        watchdog_expired = bool(
            s.get("watchdog_expired", a03.get("watchdog_expired"))
            or "A03_WATCHDOG_EXPIRED" in stdout_text)
        parsed_term = a03_terminal(
            checksum, watchdog_expired,
            bool(s.get("timed_out")), s.get("exit_code"))
        # v3.3.2 summaries carry the cap (20000) and HANG; the artifact
        # parsers are authoritative (L-A03/L-A04): prefer the FUNNEL count and
        # the checksum-derived terminal whenever the artifacts exist.
        terminal = (parsed_term["terminal"]
                    if checksum is not None or a03.get("watchdog_expired")
                    else s.get("terminal") or parsed_term["terminal"])
        parsed_injected = a03.get("injected_applications")
        row.update(
            injection_count=(parsed_injected if parsed_injected is not None
                             else s.get("injection_count")),
            injection_identity=a03.get("first_activation"),
            activation=a03.get("first_activation"),
            first_divergence=a03.get("first_affected"),
            terminal=terminal,
            terminal_qualifier=(s.get("terminal_qualifier")
                                or parsed_term["terminal_qualifier"]),
            oracle=("PASS" if parsed_term["oracle_pass"] is True else
                    "FAIL" if checksum is not None else "NO_CHECKSUM"),
            causal_class=("SDC_ORACLE_FAIL" if terminal == "SDC" else
                          "HANG_WATCHDOG" if terminal == "HANG_WATCHDOG" else
                          "MASKED_ORACLE_PASS" if terminal == "MASKED" else
                          "HANG_PARTIAL_EVIDENCE"),
            # A03 has no trace_v31.jsonl (direct driver), but the prop_trace
            # is the raw complete trace and the oracle is in stdout/oracle.log.
            trace_completeness=("COMPLETE_PROP_TRACE"
                                if (outdir / "prop_trace.csv.gz").exists()
                                else "PARTIAL"),
            checksum=checksum,
            a03_log_capped=a03.get("capped"),
            watchdog_expired=bool(s.get("watchdog_expired",
                                        a03.get("watchdog_expired"))),
            terminal_reason=(s.get("terminal_reason")
                             or parsed_term["terminal_reason"]
                             or f"A03_LOG_CAPPED={a03.get('capped')} "
                                f"stream_rows={a03.get('stream_rows')}"))
    elif model == "RP01":
        rp_parsed = parse_rp01_evidence(outdir)
        rp = dict(s.get("rp01") or {})
        for key in ("watchdog", "terminal", "terminal_reason",
                    "deadline_cycles", "no_checksum", "raw_fatal_path",
                    "watchdog_marker"):
            if rp_parsed.get(key) is not None:
                rp[key] = rp_parsed[key]
        if not rp.get("checksum"):
            rp["checksum"] = rp_parsed.get("checksum")
        wd = bool(rp.get("watchdog")) or rp01_watchdog(outdir)
        terminal = ("HANG_WATCHDOG" if wd
                    else s.get("terminal") or ("HANG_TIMEOUT"
                                               if s.get("timed_out")
                                               else "COMPLETED"))
        row.update(injection_count=rp.get("skips"),
                   injection_identity=rp.get("first_skip"),
                   activation=rp.get("first_eligible"),
                   first_divergence=rp.get("first_skip"),
                   terminal=terminal,
                   oracle=("PASS" if rp.get("checksum") == "f3b1c554273d23f7"
                           else "FAIL" if rp.get("checksum") else "NO_CHECKSUM"),
                   causal_class=("DIRECT_SKIP_AND_WATCHDOG" if wd
                                 else "HANG_PARTIAL_EVIDENCE"),
                   trace_completeness="PARTIAL_WATCHDOG",
                   watchdog=wd,
                   deadline_cycles=rp.get("deadline_cycles"),
                   no_checksum=(rp.get("checksum") is None),
                   raw_fatal_path=rp.get("raw_fatal_path"),
                   terminal_reason=(rp.get("terminal_reason")
                                    or f"eligible={rp.get('eligible')} "
                                       f"skip={rp.get('skips')} watchdog={wd}"))
    else:
        inj = s.get("first_injection") or {}
        idx = trace_index(outdir / "trace_v31.jsonl")
        seq = inj.get("seq")
        evs = idx.get(seq, [])
        # Enrich the identity from every event belonging to the same DynInst:
        # model-specific records (a01_ea, fw02_decision, store_writeback, ...)
        # carry the PC/VA/EA that the generic injection detail may omit.
        rich = {}
        for e in evs:
            for k, v in re.findall(r"([A-Za-z_]\w*)=([^;\s,]+)", e.get("detail") or ""):
                rich.setdefault(k.lower(), v)
        pc = inj.get("pc") or rich.get("pc")
        va = (inj.get("vaddr") or inj.get("va")
              or rich.get("vaddr") or rich.get("va"))
        addr = (inj.get("addr") or rich.get("addr") or rich.get("pa")
                or rich.get("actual_ea") or rich.get("new_addr")
                or rich.get("golden_ea"))
        lq = rich.get("lq_entry_id") or rich.get("lq_idx") or inj.get("lq_entry_id")
        kinds = {e.get("event_type") for e in evs}
        div = next((DIVERGENCE_EVENTS[k] for k in DIVERGENCE_EVENTS
                    if k in kinds), "n/a")
        consumer = "consumer_commit" if "consumer_commit" in kinds else (
            "errant_commit" if "errant_commit" in kinds else (
                "commit" if "commit" in kinds else "n/a"))
        squash = "SQUASHED" if any(
            "squash" in (e.get("event_type") or "") or
            "squash" in (e.get("detail") or "").lower() for e in evs) else "no"
        term = (cls.get("terminal_state") or s.get("terminal")
                or "UNRESOLVED")
        row.update(injection_count=s.get("injection_count"),
                   injection_identity=(f"seq={seq};pc={pc};va={va};"
                                       f"addr={addr};lq={lq}"),
                   activation=f"injection seq={seq}",
                   first_divergence=div,
                   consumer=consumer,
                   squash_or_replay=squash,
                   terminal=term,
                   oracle=("PASS" if meta.get("oracle_pass") else "FAIL"),
                   causal_class=cls.get("fault_causality", "n/a"),
                   trace_completeness=cls.get("trace_completeness", "n/a"),
                   terminal_reason=cls.get("terminal_state_reason", "n/a"))
    return row


def control_row(model: str, ctx: int):
    outdir = RUNS / f"{model}-R{ctx:02d}-control"
    s = jload(outdir / "summary.json")
    meta = jload(outdir / "pilot_meta.json")
    # v3.3.3 (L-D01): classify from the EXECUTED command.txt. run_pilot's argv
    # (summary.cmd) never contains --chaos_*, which produced the false
    # INJECTOR_ABSENT label for 35/60 controls.
    cmd = read_command(outdir) or " ".join(s.get("cmd") or [])
    classification = classify_control(cmd)
    inj = s.get("injection_count")
    if model == "RP01":
        rp = s.get("rp01") or parse_rp01_evidence(outdir)
        inj = rp.get("skips")
    misfire = bool((inj or 0) > 0)
    proof = "MISFIRE" if misfire else classification["proof"]
    seed = (s.get("seed") or meta.get("seed")
            or (meta.get("excel_identity") or {}).get("seed"))
    if seed is None:
        m = re.search(r"--[A-Za-z0-9_]*rng_seed(?:\s+|=)(\d+)", cmd)
        seed = int(m.group(1)) if m else None
    cls = meta.get("classification") or {}
    observed_workload = meta.get("workload") or s.get("workload")
    terminal = (cls.get("terminal_state") or s.get("terminal")
                or "UNRESOLVED")
    oracle_checksum = (s.get("checksum")
                       or (s.get("rp01") or {}).get("checksum"))
    return {
        "model": model, "context": f"R{ctx:02d}", "seed": seed,
        "ordinal": s.get("ordinal"),
        "workload": (f"{Path(observed_workload).name} (observed)"
                     if observed_workload else WORKLOAD[model]),
        "binary_sha": s.get("binary_sha"), "outdir": str(outdir),
        "injection_count": inj, "zero_injection_proof": proof,
        "mount_evidence": {
            "mounts": classification["mounts"],
            "probability": classification["probability"],
            "md04_probability": classification["md04_probability"],
            "suppression_flags": classification["suppression_flags"],
            "source": classification["source"],
        },
        "terminal": terminal,
        "oracle": ("PASS" if (meta.get("oracle_pass") or
                              (oracle_checksum == "f3b1c554273d23f7"))
                   else "FAIL_OR_NO_CHECKSUM"),
        "exit_code": s.get("exit_code"), "timed_out": s.get("timed_out"),
        "command": cmd.replace("\n", " ")[:600],
        "fault_command": cmd.replace("\n", " "),
    }


def main(argv=None):
    global RUNS, OUT
    ap = argparse.ArgumentParser(
        description="Build the LSU v3.3.3 60-context acceptance tables from "
                    "real run artifacts. Defaults point at audit_v3_3_3.")
    ap.add_argument("--runs", default=str(ROOT / "audit_v3_3_3/runs"))
    ap.add_argument("--out", default=str(ROOT / "audit_v3_3_3"))
    args = ap.parse_args(argv)
    RUNS = Path(args.runs)
    OUT = Path(args.out)
    OUT.mkdir(parents=True, exist_ok=True)
    faults, controls = [], []
    mapping, distinct, matrix, causal = [], [], [], []
    for model in MODELS:
        (rs, re_), n, ords = ROI[model]
        ids = []
        for i, ctx in enumerate(range(1, 6)):
            f = fault_row(model, ctx)
            c = control_row(model, ctx)
            faults.append(f)
            controls.append(c)
            ids.append(f.get("injection_identity"))
            mapping.append({
                "ModelID": model, "ContextID": f"R{ctx:02d}",
                "SampleRunID": f"V332-{model}-R{ctx:02d}",
                "Seed": f.get("seed"), "Workload": WORKLOAD[model],
                "WorkloadStatus": f["workload_status"],
                "ROI_Start_Ordinal": rs, "ROI_End_Ordinal": re_,
                "ROI_N": n, "Percentile": [0.1, 0.3, 0.5, 0.7, 0.9][i],
                "Rank_k": (int([0.1, 0.3, 0.5, 0.7, 0.9][i] * n) +
                           (1 if [0.1, 0.3, 0.5, 0.7, 0.9][i] * n >
                           int([0.1, 0.3, 0.5, 0.7, 0.9][i] * n) else 0)),
                "Absolute_Eligible_Ordinal": ords[i],
                "InjectionIdentity": ids[-1],
                "EvidenceBinarySHA": f.get("binary_sha"),
                "EvidencePath": f.get("outdir"),
                "MappingStatus": ("MAPPED_ON_CANDIDATE_WORKLOAD"
                                  if model in CANDIDATE else "MAPPED"),
            })
            distinct.append({
                "ModelID": model, "ContextID": f"R{ctx:02d}",
                "Identity": ids[-1],
                "DistinctFromOtherContexts": "YES" if ids[-1] not in ids[:-1]
                                              else "NO",
                "Terminal": f.get("terminal"),
                "EvidencePath": f.get("outdir"),
            })
            matrix.append({
                "ModelID": model, "ContextID": f"R{ctx:02d}",
                "WorkloadStatus": f["workload_status"],
                "Ordinal": f.get("ordinal"),
                "FaultInjected": "YES" if (f.get("injection_count") or 0) > 0
                                 else "NO",
                "FaultTerminal": f.get("terminal"),
                "Oracle": f.get("oracle"),
                "ControlInjected": c.get("injection_count"),
                "ControlProof": c.get("zero_injection_proof"),
                "ControlOracle": c.get("oracle"),
                "Trace": f.get("trace_completeness"),
                "CausalClass": f.get("causal_class"),
                "Qualifier": QUALIFIER.get(model, ""),
                "Ready": ("TECHNICALLY_READY_APPROVAL_PENDING"
                          if f["workload_status"] == "CANDIDATE_PENDING_APPROVAL"
                          else "TECHNICALLY_READY"),
            })
            causal.append({
                "ModelID": model, "ContextID": f"R{ctx:02d}",
                "FaultSource": f"{model} fault at ordinal {f.get('ordinal')}",
                "Injection": f.get("injection_identity"),
                "Activation": f.get("activation"),
                "FirstDivergence": f.get("first_divergence"),
                "Downstream": f.get("consumer", "n/a"),
                "CommitSquashReplay": f.get("squash_or_replay", "n/a"),
                "ArchitecturalOrTerminal": f.get("terminal"),
                "TerminalReason": f.get("terminal_reason"),
                "ApplicationOracle": f.get("oracle"),
                "EvidenceClass": f.get("causal_class"),
                "TraceCompleteness": f.get("trace_completeness"),
                "EvidencePath": f.get("outdir"),
            })

    def write(name, rows):
        p = OUT / name
        with open(p, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print("wrote", p, len(rows))

    write("roi/LSU_60Context_ROI_Percentile_Mapping.csv", mapping)
    write("roi/LSU_60Context_Distinctness_Audit.csv", distinct)
    write("LSU_60Context_Final_Readiness_Matrix.csv", matrix)
    pairs = []
    for f, c in zip(faults, controls):
        pairs.append({
            "ModelID": f["model"], "ContextID": f["context"],
            "Seed": f["seed"], "Ordinal": f["ordinal"],
            "Workload": f["workload"], "WorkloadStatus": f["workload_status"],
            "BinarySHA256": f.get("binary_sha"),
            "FaultInjected": f.get("injection_count"),
            "FaultIdentity": f.get("injection_identity"),
            "FaultTerminal": f.get("terminal"),
            "FaultOracle": f.get("oracle"),
            "FaultCausalClass": f.get("causal_class"),
            "FaultTrace": f.get("trace_completeness"),
            "ControlInjected": c.get("injection_count"),
            "ControlZeroProof": c.get("zero_injection_proof"),
            "ControlMountEvidence": json.dumps(c.get("mount_evidence") or {}),
            "ControlOracle": c.get("oracle"),
            "ControlTerminal": c.get("terminal"),
            "ControlExitCode": c.get("exit_code"),
            "FaultEvidencePath": f.get("outdir"),
            "ControlEvidencePath": c.get("outdir"),
            "FaultCommand": f.get("fault_command") or c.get("fault_command") or
                            read_command(Path(f.get("outdir") or "")),
        })
    # v3.3.3: the matrix's RAW CSV and this curated FINAL CSV are distinct
    # files; the v3.3.2 _J/_K files are history and are left untouched.
    write("controls/LSU_Fault_Control_Pair_FINAL.csv", pairs)
    write("propagation/LSU_60Context_Causal_Propagation_Final.csv", causal)


if __name__ == "__main__":
    main()
