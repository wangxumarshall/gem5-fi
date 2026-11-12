#!/usr/bin/env python3
"""Deterministic builder for the LSU v3.3.3 synthetic acceptance fixtures.

The fixtures are intentionally tiny (every file is a few hundred bytes) and
contain **no gem5 output**.  They encode the *shape* of a campaign run dir plus
one controlled defect per scenario so the runner/collector/control/qualified
modules can be exercised without gem5.

Layout (regenerated on every invocation, never hand-edited):

    payload/                     tiny fake gem5 binary / config / ELFs
    design/                      synthetic --design-matrix/--design-mapping CSVs
    campaign/                    mixed formal root: 12 fault/control pairs,
                                 one defect per scenario except the clean pairs
    campaign_clean/              all-good root (positive control)
    campaign_partial/            partial success (2 good dirs, 2 broken dirs)
    historical_evidence/         HISTORICAL campaign_id; must never be FORMAL

Identity values (SampleRunID seeds, ROI ordinals) are copied from the frozen
60_SAMPLE_MATRIX.csv / LSU_60Context_ROI_Percentile_Mapping.csv so the synthetic
design inputs stay schema- and value-compatible with the real ones.  They are
design metadata only; no run evidence is taken from the historical run dirs.

Usage:
    python3 tests/fixtures/lsu_v333_synthetic/build_fixtures.py [--root DIR]
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import shutil
from pathlib import Path

FIXTURE_ROOT = Path(__file__).resolve().parent

# README_INTERFACES.md baseline SHAs (the campaign this fixture emulates).
BINARY_SHA = ("62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7"
              "581467a6cd")
CONFIG_SHA = ("8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b8"
              "1992cb225")
BAD_BINARY_SHA = "deadbeef" * 8
BAD_ELF_SHA = "feedface" * 8

CAMPAIGN_ID = "SYNTH-V333-FORMAL"
CLEAN_ID = "SYNTH-V333-CLEAN"
PARTIAL_ID = "SYNTH-V333-PARTIAL"
HISTORICAL_ID = "SYNTH-V332-PRE-FORMAL"

STARTED = "2026-11-12T00:00:00Z"
ENDED = "2026-11-12T00:01:00Z"

# (model, context) -> frozen seed / ROI ordinal (from the real frozen design).
IDENTITY = {
    ("A01", "R01"): (2108120075, 597),
    ("A01", "R02"): (1113826800, 623),
    ("A01", "R03"): (1302709433, 649),
    ("A01", "R04"): (2194451614, 675),
    ("A01", "R05"): (3228552887, 701),
    ("A03", "R01"): (663646247, 1058),
    ("A03", "R02"): (1626885462, 1094),
    ("A03", "R03"): (110775855, 1131),
    ("A03", "R04"): (2766846323, 1168),
    ("FW02", "R01"): (2941542370, 13),
    ("SP05", "R01"): (1489155957, 952),
    ("RP01", "R01"): (3135797961, 26),
}
ROI = {
    "A01": (585, 713, 129, "0.1"),
    "A03": (1040, 1222, 183, "0.1"),
    "FW02": (8, 67, 60, "0.1"),
    "SP05": (940, 1067, 128, "0.1"),
    "RP01": (1, 255, 255, "0.1"),
}
WORKLOAD = {
    "A01": "agu_addromodes",
    "A03": "agu_addromodes",
    "FW02": "sq_forward",
    "SP05": "store_path",
    "RP01": "replay_dependency",
}
MOUNTED = {"A01", "A03", "FW02", "SP05"}
EXPECTED_TERMINAL = {
    "A01": "SDC",
    "A03": "SDC",
    "FW02": "SDC",
    "SP05": "SDC",
    "RP01": "HANG_WATCHDOG",
}

MATRIX_COLS = [
    "SampleRunID", "RunID", "SubTaskID", "Seed", "FaultModelID",
    "FaultLocation", "TargetField", "BitEntryByteIndex", "NormalValue",
    "FaultValue", "InjectionMode", "InjectionTiming", "FaultDuration",
    "TargetInstruction", "EligibleEventCondition", "EventOrdinal",
    "FaultConfigID", "ContextDifferenceRule", "WorkloadPath",
    "BinarySHA256", "InputHash", "Oracle", "WarmUp", "ROI", "gem5Commit",
    "BinaryPath", "ConfigScript", "FullCommand", "Timeout", "OutputDir",
    "RequiredLogs", "PreflightStatus", "ExecutionStatus",
    "TerminalState_LEGACY_DEPRECATED", "TraceCompleteness_LEGACY_DEPRECATED",
    "EvidencePath", "DecisionStatus", "ConfigFrozen", "RunStatus",
    "FaultActivationStatus", "TerminalState_v31", "TraceCompleteness_v31",
    "v3.2_ConfigProvenance",
]
MAPPING_COLS = [
    "ModelID", "ContextID", "SampleRunID", "Seed", "Workload",
    "WorkloadStatus", "ROI_Start_Ordinal", "ROI_End_Ordinal", "ROI_N",
    "Percentile", "Rank_k", "Absolute_Eligible_Ordinal", "InjectionIdentity",
    "EvidenceBinarySHA", "EvidencePath", "MappingStatus",
]

BROKEN = "broken"          # sentinel used by the tests to build the scenario table
COMPLETE = "complete"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _json(path: Path, payload) -> None:
    _write(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _command(root: Path, run: Path, model: str, role: str, seed: int,
             ordinal: int) -> str:
    wl = root / "payload" / WORKLOAD[model]
    parts = [
        str(root / "payload" / "gem5.opt"),
        f"--outdir={run}",
        str(root / "payload" / "lsu_proxy.py"),
        f"--cmd={wl}",
        "--cpu", "O3", "--variant", "B0",
        "--probability", "1.0" if role == "fault" else "0.0",
        "--chaos_propagation", "--prop_trace_file", "prop_trace.csv.gz",
    ]
    if model in MOUNTED:
        parts += ["--chaos_addrpath", "--agu_pre_mode", "a01_bit3_load",
                  "--addrpath_lsu_tier", "F0", "--addrpath_max_faults",
                  "1" if role == "fault" else "0",
                  "--addrpath_rng_seed", str(seed),
                  "--addrpath_event_ordinal", str(ordinal)]
    else:
        parts += ["--chaos_lsqfwd", "--rng_seed", str(seed),
                  "--rp01_event_ordinal", str(ordinal)]
    return " ".join(parts) + "\n"


def _summary_record(model: str, role: str, ctx: str) -> str:
    injections = 0 if role == "control" else 1
    return json.dumps({
        "record_type": "summary",
        "trace_version": "v3.1",
        "sample_run_id": f"SYNTH-{model}-{ctx}",
        "fault_model_id": model,
        "run_status": "COMPLETED",
        "fault_activation_status":
            "NOT_TRIGGERED" if role == "control" else "TRIGGERED",
        "terminal_state": "UNRESOLVED" if role == "control" else
            EXPECTED_TERMINAL[model],
        "trace_completeness": "COMPLETE",
        "counts": {"events": 2, "injections": injections,
                   "activations": injections},
    }) + "\n"


def _trace_lines(model: str, role: str, ctx: str,
                 scenario: str = COMPLETE) -> str:
    if scenario == "control_missing_count":
        # No summary record => no trace-side count either: the missing-count
        # defect must not be silently repaired from another evidence source.
        return (json.dumps({"record_type": "event",
                            "event_type": "inventory", "events": 1,
                            "note": "control: count intentionally absent"})
                + "\n")
    if role == "control":
        return (json.dumps({"record_type": "event",
                            "event_type": "inventory", "events": 1,
                            "note": "control: no injection event"}) + "\n"
                + _summary_record(model, role, ctx))
    if model == "RP01":
        return (json.dumps({"record_type": "event",
                            "event_type": "injection",
                            "dyn_inst_seq": 9001,
                            "detail": "rp01_skip_replay;ordinal=26"}) + "\n"
                + _summary_record(model, role, ctx))
    return (json.dumps({"record_type": "event",
                        "event_type": "injection", "dyn_inst_seq": 12909,
                        "detail": "pc=400578;va=493028;pa=78028;"
                                  "eligible_ordinal=597;lq=756"}) + "\n"
            + json.dumps({"record_type": "event",
                          "event_type": "consumer_commit",
                          "dyn_inst_seq": 12911,
                          "detail": "pc=40057c"}) + "\n"
            + _summary_record(model, role, ctx))


def _prop_trace(path: Path, role: str) -> None:
    rows = "seq,event\n"
    if role == "fault":
        rows += "12909,injection\n12911,consumer_commit\n"
    # mtime=0 keeps the fixture byte-for-byte reproducible.
    with open(path, "wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as fh:
            fh.write(rows.encode())


def _pilot_meta(model: str, ctx: str, role: str, seed: int, ordinal: int,
                applied: int | None, terminal: str,
                reason: str) -> dict:
    mounted = model in MOUNTED
    if role == "control":
        proof = "MOUNTED_BUT_DISABLED" if mounted else "INJECTOR_ABSENT"
        gate = "probability_zero"
        enabled = False
        prob = 0.0
    else:
        proof = "MOUNTED_BUT_ACTIVE" if mounted else "INJECTOR_ABSENT"
        gate = "ordinal"
        enabled = True
        prob = 1.0
    meta = {
        "pilot_id": f"{model}-{ctx}-{role}",
        "model": model,
        "run_role": "CONTROL" if role == "control" else "FAULT",
        "driver": "synthetic_fixture",
        "seed": seed,
        "event_ordinal": ordinal,
        "oracle_pass": role == "control",
        "terminal": terminal,
        "terminal_state": terminal,
        "classification": {
            "terminal_state": terminal,
            "terminal_state_reason": reason,
            "oracle_outcome": "n/a" if role == "fault" and model == "RP01"
            else ("PASS" if role == "control" else "FAIL"),
        },
        "injector": {
            "mounted": mounted,
            "mount_flags": ["--chaos_addrpath"] if mounted else [],
            "probability": prob,
            "gate": gate,
            "gate_enabled": enabled,
            "zero_injection_proof": proof,
            "attach_mechanism": "self_attach_at_startup",
        },
    }
    if role == "fault":
        meta["injection_count"] = applied
    else:
        if applied is not None:
            meta["injection_count"] = applied
            meta["injection_attempt_count"] = applied
            meta["injection_applied_count"] = applied
    return meta


def _summary(root: Path, run: Path, model: str, ctx: str, role: str,
             seed: int, ordinal: int, *, injection_count, terminal: str,
             reason: str, oracle, binary_sha: str, elf_sha: str,
             exit_code: int = 0, timed_out: bool = False,
             trace_complete: bool = True, extra: dict | None = None) -> dict:
    trace = run / "trace_v31.jsonl"
    summary = {
        "model": model,
        "context": ctx,
        "ctx_index": int(ctx[1:]),
        "role": role,
        "seed": seed,
        "ordinal": ordinal,
        "workload": str(root / "payload" / WORKLOAD[model]),
        "outdir": str(run),
        "exit_code": exit_code,
        "timed_out": timed_out,
        "binary_sha": binary_sha,
        "elf_sha": elf_sha,
        "oracle": oracle,
        "terminal": terminal,
        "terminal_reason": reason,
        "trace_completeness": {
            "trace": str(trace),
            "trace_completeness": "COMPLETE" if trace_complete else "PARTIAL",
            "record_integrity": "VALID",
            "run_status": "COMPLETED" if not timed_out else "TIMEOUT",
        },
    }
    if injection_count is not None:
        summary["injection_count"] = injection_count
    if role == "control":
        summary["control_proof"] = ("MOUNTED_BUT_DISABLED"
                                    if model in MOUNTED else
                                    "INJECTOR_ABSENT")
        if injection_count is not None:
            summary["injection_attempt_count"] = injection_count
            summary["injection_applied_count"] = injection_count
    summary.update(extra or {})
    return summary


def _campaign_json(model: str, ctx: str, role: str, seed: int, *,
                   campaign_id: str, status: str, binary_sha: str,
                   elf_sha: str, exit_code: int = 0,
                   timed_out: bool = False) -> dict:
    return {
        "campaign_id": campaign_id,
        "model": model,
        "context": ctx,
        "role": role,
        "sample_run_id": f"SYNTH-{model}-{ctx}",
        "seed": seed,
        "status": status,
        "binary_sha": binary_sha,
        "config_sha": CONFIG_SHA,
        "elf_sha": elf_sha,
        "started_at": STARTED,
        "ended_at": ENDED,
        "exit_code": exit_code,
        "timed_out": timed_out,
    }


def _make_run(root: Path, run_root: str, model: str, ctx: str, role: str, *,
              campaign_id: str, scenario: str = COMPLETE,
              status: str = "COMPLETED") -> Path:
    """Write one run dir.  ``scenario`` selects the injected defect."""
    seed, ordinal = IDENTITY[(model, ctx)]
    run = root / run_root / f"{model}-{ctx}-{role}"
    run.mkdir(parents=True, exist_ok=True)
    elf = root / "payload" / WORKLOAD[model]
    elf_sha = _sha(elf)

    binary_sha = BAD_BINARY_SHA if scenario == "binary_sha_mismatch" else BINARY_SHA
    if scenario == "elf_sha_mismatch":
        elf_sha = BAD_ELF_SHA

    exit_code = 124 if scenario == "external_timeout" else (
        1 if scenario == "child_exception" else 0)
    timed_out = scenario == "external_timeout"

    # --- per-scenario terminal / count / campaign status -------------------
    if role == "control":
        terminal, reason, oracle = ("UNRESOLVED", "NO_INJECTION_EVENT", True)
        applied = 0
        if scenario == "control_applied":
            applied = 1
            status = "CONTROL_PROOF_INCOMPLETE"
        elif scenario == "control_missing_count":
            applied = None
            status = "CONTROL_PROOF_INCOMPLETE"
        elif scenario in ("missing_summary", "missing_control_trace"):
            status = "OUTPUT_INCOMPLETE"
        elif scenario == "external_timeout":
            terminal, reason, oracle = ("HANG", "NO_CHECKSUM_EXTERNAL_TIMEOUT",
                                        None)
        elif scenario == "child_exception":
            terminal, reason, oracle = ("CRASH", "CHILD_EXCEPTION", None)
        injection_count = applied
    else:
        terminal = EXPECTED_TERMINAL[model]
        reason = ("INTERNAL_WATCHDOG_DEADLINE" if model == "RP01"
                  else "ORACLE_FAIL")
        oracle = None if model == "RP01" else False
        applied = 1
        if scenario in ("missing_summary", "missing_fault_trace"):
            status = "OUTPUT_INCOMPLETE"
        elif scenario in ("binary_sha_mismatch", "elf_sha_mismatch"):
            status = "HASH_MISMATCH"
        elif scenario == "external_timeout":
            status = "TIMEOUT"
            terminal, reason, oracle = ("HANG",
                                        "NO_CHECKSUM_EXTERNAL_TIMEOUT", None)
        elif scenario == "child_exception":
            status = "FAILED"
            terminal, reason, oracle = ("CRASH", "CHILD_EXCEPTION", None)
        elif scenario == "internal_watchdog":
            status = "COMPLETED"
            if model != "RP01":
                terminal = "HANG_WATCHDOG"
                reason = "WATCHDOG_EXPIRED_NO_CHECKSUM"
                oracle = None
        injection_count = applied

    _json(run / "campaign.json",
          _campaign_json(model, ctx, role, seed, campaign_id=campaign_id,
                         status=status, binary_sha=binary_sha, elf_sha=elf_sha,
                         exit_code=exit_code, timed_out=timed_out))

    # summary.json is intentionally absent for the missing_summary scenario.
    if scenario != "missing_summary":
        extra = {}
        if model == "SP05" and role == "fault":
            extra = {"complete_store_count": 1, "sp05_complete_store": 1}
        if model == "RP01" and role == "fault":
            extra = {"watchdog": True, "deadline_cycles": 20000000,
                     "raw_fatal_path": str(run / "lsq_fwd_injections.log")}
        # The missing-trace defect leaves the summary claiming COMPLETE on
        # purpose: a collector must stat the trace file, not trust the claim.
        summary = _summary(
            root, run, model, ctx, role, seed, ordinal,
            injection_count=injection_count, terminal=terminal, reason=reason,
            oracle=oracle, binary_sha=binary_sha, elf_sha=elf_sha,
            exit_code=exit_code, timed_out=timed_out, extra=extra)
        _json(run / "summary.json", summary)

    # pilot_meta mirrors the summary; missing for the missing-count scenario
    # (the missing-count defect must not be silently repaired to 0).
    if scenario != "control_missing_count":
        _json(run / "pilot_meta.json",
              _pilot_meta(model, ctx, role, seed, ordinal,
                          injection_count, terminal, reason))

    # traces: absent for the missing-<role>-trace scenarios
    missing_trace = scenario in ("missing_fault_trace",
                                 "missing_control_trace")
    if not missing_trace:
        _write(run / "trace_v31.jsonl",
               _trace_lines(model, role, ctx, scenario))
    if not missing_trace:
        _prop_trace(run / "prop_trace.csv.gz", role)

    # command.txt always present (the executed command is evidence).
    _write(run / "command.txt",
           _command(root, run, model, role, seed, ordinal))

    if scenario == "external_timeout":
        stdout = ""
    elif model == "RP01" and role == "fault":
        stdout = ("RP01_ELIGIBLE ordinal=26 seq=9001\n"
                  "RP01_SKIP_REPLAY ordinal=26\n")
    elif role == "control":
        stdout = "728e604ffcec539d\n"
    else:
        stdout = "0000000000000001\n"
    _write(run / "stdout.log", stdout)

    if scenario == "child_exception":
        stderr = ("Traceback (most recent call last):\n"
                  "  File \"run_pilot.py\", line 1, in <module>\n"
                  "RuntimeError: synthetic child exception\n")
    else:
        stderr = ""
    _write(run / "stderr.log", stderr)

    if role == "control":
        oracle_log = "ORACLE_PASS: checksum=728e604ffcec539d\n"
    elif model == "RP01" or scenario == "internal_watchdog":
        oracle_log = "ORACLE_SKIPPED: no checksum (watchdog terminal)\n"
    else:
        oracle_log = ("ORACLE_FAIL: expected 728e604ffcec539d got "
                      "0000000000000001\n")
    _write(run / "oracle.log", oracle_log)

    if model == "RP01" and role == "fault":
        _write(run / "lsq_fwd_injections.log",
               "CHAOS_RP01_WATCHDOG=EXPIRED tick=123456789 "
               "deadline_cycles=20000000\n")
    if model == "SP05" and role == "fault":
        _write(run / "lsq_fwd_injections.log",
               "SP05_COMPLETE_STORE count=1 ordinal=952\n")
    if scenario == "internal_watchdog":
        _write(run / "addrpath_injections.log",
               "FUNNEL: candidates=7 injected=0\n"
               "A03_WATCHDOG_EXPIRED tick=385000000 cycles=1000000\n")
    return run


def _write_design(root: Path, name: str, pairs,
                  run_root: str = "campaign") -> tuple[Path, Path]:
    design = root / "design"
    matrix = design / f"{name}_SAMPLE_MATRIX.csv"
    mapping = design / f"{name}_ROI_MAPPING.csv"
    matrix.parent.mkdir(parents=True, exist_ok=True)
    with open(matrix, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=MATRIX_COLS)
        w.writeheader()
        for model, ctx in pairs:
            seed, ordinal = IDENTITY[(model, ctx)]
            start, end, n, pct = ROI[model]
            wl = root / "payload" / WORKLOAD[model]
            row = {k: "n/a" for k in MATRIX_COLS}
            row.update({
                "SampleRunID": f"SYNTH-{model}-{ctx}",
                "RunID": f"SYNTH-{model}",
                "SubTaskID": f"SYNTH-{model}-{ctx}",
                "Seed": seed,
                "FaultModelID": model,
                "EventOrdinal": ordinal,
                "WorkloadPath": str(wl),
                "BinarySHA256": BINARY_SHA,
                "BinaryPath": str(root / "payload" / "gem5.opt"),
                "ConfigScript": str(root / "payload" / "lsu_proxy.py"),
                "Timeout": 300,
                "EvidencePath": f"{run_root}/{model}-{ctx}-fault",
                "PreflightStatus": "PILOT_ONLY_NOT_FORMAL",
                "ExecutionStatus": "NOT_RUN",
                "TerminalState_v31": "NOT_RUN",
                "TraceCompleteness_v31": "NONE",
            })
            w.writerow(row)
    with open(mapping, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=MAPPING_COLS)
        w.writeheader()
        for model, ctx in pairs:
            seed, ordinal = IDENTITY[(model, ctx)]
            start, end, n, pct = ROI[model]
            w.writerow({
                "ModelID": model,
                "ContextID": ctx,
                "SampleRunID": f"SYNTH-{model}-{ctx}",
                "Seed": seed,
                "Workload": WORKLOAD[model],
                "WorkloadStatus": "FORMAL",
                "ROI_Start_Ordinal": start,
                "ROI_End_Ordinal": end,
                "ROI_N": n,
                "Percentile": pct,
                "Rank_k": 1,
                "Absolute_Eligible_Ordinal": ordinal,
                "InjectionIdentity": ("seq=12909;pc=400578;va=493028;"
                                      "pa=78028;lq=756"),
                "EvidenceBinarySHA": BINARY_SHA,
                "EvidencePath": f"{run_root}/{model}-{ctx}-fault",
                "MappingStatus": "MAPPED",
            })
    return matrix, mapping


def _payload(root: Path) -> None:
    payload = root / "payload"
    payload.mkdir(parents=True, exist_ok=True)
    # Tiny stand-ins; never executed.  Real byte content is not needed.
    (payload / "gem5.opt").write_bytes(b"\x7fELF synthetic gem5.opt\n")
    (payload / "lsu_proxy.py").write_text(
        "# synthetic lsu_proxy config stand-in\n", encoding="utf-8")
    for name in sorted(set(WORKLOAD.values())):
        (payload / name).write_bytes(
            f"\x7fELF synthetic workload {name}\n".encode())


SCENARIOS = {
    # campaign root, run dir, scenario name
    "complete_fault": ("campaign", "A01-R01-fault", COMPLETE),
    "complete_control": ("campaign", "A01-R01-control", COMPLETE),
    "missing_summary": ("campaign", "A01-R02-fault", "missing_summary"),
    "missing_fault_trace": ("campaign", "A01-R03-fault", "missing_fault_trace"),
    "missing_control_trace": ("campaign", "A01-R03-control",
                              "missing_control_trace"),
    "control_applied_gt0": ("campaign", "A01-R04-control", "control_applied"),
    "control_missing_count": ("campaign", "A01-R05-control",
                              "control_missing_count"),
    "binary_sha_mismatch": ("campaign", "A03-R01-fault", "binary_sha_mismatch"),
    "elf_sha_mismatch": ("campaign", "A03-R02-fault", "elf_sha_mismatch"),
    "external_timeout": ("campaign", "A03-R03-fault", "external_timeout"),
    "internal_rp01_watchdog": ("campaign", "RP01-R01-fault", "internal_watchdog"),
    "internal_a03_watchdog": ("campaign", "A03-R04-fault", "internal_watchdog"),
    "python_child_exception": ("campaign", "FW02-R01-fault",
                               "child_exception"),
    "formal_matching_campaign_id": ("campaign", "SP05-R01-fault", COMPLETE),
    "historical_preformal": ("historical_evidence", "A01-R01-fault", COMPLETE),
}

# Every run dir that must exist, with the defect that created it.
CAMPAIGN_RUNS = {
    ("A01", "R01", "fault"): COMPLETE,
    ("A01", "R01", "control"): COMPLETE,
    ("A01", "R02", "fault"): "missing_summary",
    ("A01", "R02", "control"): COMPLETE,
    ("A01", "R03", "fault"): "missing_fault_trace",
    ("A01", "R03", "control"): "missing_control_trace",
    ("A01", "R04", "fault"): COMPLETE,
    ("A01", "R04", "control"): "control_applied",
    ("A01", "R05", "fault"): COMPLETE,
    ("A01", "R05", "control"): "control_missing_count",
    ("A03", "R01", "fault"): "binary_sha_mismatch",
    ("A03", "R01", "control"): COMPLETE,
    ("A03", "R02", "fault"): "elf_sha_mismatch",
    ("A03", "R02", "control"): COMPLETE,
    ("A03", "R03", "fault"): "external_timeout",
    ("A03", "R03", "control"): COMPLETE,
    ("A03", "R04", "fault"): "internal_watchdog",
    ("A03", "R04", "control"): COMPLETE,
    ("RP01", "R01", "fault"): "internal_watchdog",
    ("RP01", "R01", "control"): COMPLETE,
    ("FW02", "R01", "fault"): "child_exception",
    ("FW02", "R01", "control"): COMPLETE,
    ("SP05", "R01", "fault"): COMPLETE,
    ("SP05", "R01", "control"): COMPLETE,
}


def build(root: Path = FIXTURE_ROOT) -> Path:
    root = Path(root)
    for sub in ("campaign", "campaign_clean", "campaign_partial",
                "historical_evidence", "design", "payload"):
        shutil.rmtree(root / sub, ignore_errors=True)
    _payload(root)

    # 1. mixed formal root: one defect per scenario + clean pairs
    for (model, ctx, role), scenario in CAMPAIGN_RUNS.items():
        _make_run(root, "campaign", model, ctx, role,
                  campaign_id=CAMPAIGN_ID, scenario=scenario)
    pairs = sorted({(m, c) for (m, c, r) in CAMPAIGN_RUNS})
    matrix, mapping = _write_design(root, "SYNTH", pairs)
    _json(root / "campaign" / "campaign_identity.json", {
        "campaign_id": CAMPAIGN_ID, "binary_sha": BINARY_SHA,
        "config_sha": CONFIG_SHA,
        "elf_sha": {name: _sha(root / "payload" / name)
                    for name in sorted(set(WORKLOAD.values()))},
    })

    # 2. all-good positive control
    for model, ctx in (("A01", "R01"), ("SP05", "R01")):
        for role in ("fault", "control"):
            _make_run(root, "campaign_clean", model, ctx, role,
                      campaign_id=CLEAN_ID)
    _write_design(root, "CLEAN", [("A01", "R01"), ("SP05", "R01")],
                  run_root="campaign_clean")

    # 3. partial success: 2 good, 2 broken
    _make_run(root, "campaign_partial", "A01", "R01", "fault",
              campaign_id=PARTIAL_ID)
    _make_run(root, "campaign_partial", "A01", "R01", "control",
              campaign_id=PARTIAL_ID)
    _make_run(root, "campaign_partial", "A01", "R02", "fault",
              campaign_id=PARTIAL_ID, scenario="missing_summary")
    _make_run(root, "campaign_partial", "A01", "R02", "control",
              campaign_id=PARTIAL_ID, scenario="external_timeout")
    _write_design(root, "PARTIAL", [("A01", "R01"), ("A01", "R02")],
                  run_root="campaign_partial")

    # 4. historical PRE_FORMAL evidence: complete files, different campaign id
    for role in ("fault", "control"):
        _make_run(root, "historical_evidence", "A01", "R01", role,
                  campaign_id=HISTORICAL_ID)
    _write_design(root, "HISTORICAL", [("A01", "R01")],
                  run_root="historical_evidence")

    _write(root / "README.md", _readme(root))
    return root


def _readme(root: Path) -> str:
    lines = [
        "# LSU v3.3.3 synthetic launch-acceptance fixtures",
        "",
        "Generated by `build_fixtures.py`; do not hand-edit.  No gem5 output,",
        "every file is a few hundred bytes.",
        "",
        "Campaign roots:",
        "",
        "| root | campaign_id | purpose |",
        "|---|---|---|",
        f"| `campaign/` | `{CAMPAIGN_ID}` | one defect per scenario, plus clean pairs |",
        f"| `campaign_clean/` | `{CLEAN_ID}` | all-good positive control |",
        f"| `campaign_partial/` | `{PARTIAL_ID}` | partial success (2 good, 2 broken) |",
        f"| `historical_evidence/` | `{HISTORICAL_ID}` | must never be FORMAL |",
        "",
        "Scenario dirs inside `campaign/`:",
        "",
        "| scenario | run dir | injected defect |",
        "|---|---|---|",
    ]
    for name, (rootname, dirname, scenario) in SCENARIOS.items():
        lines.append(f"| {name} | `{rootname}/{dirname}` | `{scenario}` |")
    lines += [
        "",
        "`design/` holds schema-compatible synthetic `--design-matrix` and",
        "`--design-mapping` CSVs (identity only, never evidence).",
        "",
        "Baseline identity: binary_sha "
        "`1126e0fd...b4f338`, config_sha `8309da72...92cb225`.",
        "",
    ]
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(FIXTURE_ROOT))
    args = ap.parse_args(argv)
    build(Path(args.root))
    print(f"built synthetic fixtures under {args.root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
