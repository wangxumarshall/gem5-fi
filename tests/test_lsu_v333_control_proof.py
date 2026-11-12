"""Tests for tools/lsu_v333_control_proof.py (Agent C).

All fixtures are synthetic run directories under pytest's ``tmp_path``; the one
integration test reads the real pre-formal controls under
``audit_v3_3_3/runs`` (skipped if absent).  Nothing here invokes gem5.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import lsu_v333_control_proof as cp  # noqa: E402

REAL_RUNS = ROOT / "audit_v3_3_3/runs"

INTERFACE_KEYS = {
    "injector_mounted",
    "fault_enabled",
    "suppression_reason",
    "injection_attempt_count",
    "injection_applied_count",
    "proof_class",
    "status",
    "evidence",
}

def _cmd(probability="0.0", mount=None, extra=None):
    tokens = [
        "build/ARM/gem5.opt",
        "--outdir=/tmp/x",
        "configs/se/lsu_proxy.py",
        "--cmd=/tmp/wl",
        "--cpu", "O3",
        "--variant", "B0",
    ]
    if mount:
        tokens.append(mount)
    tokens.extend(extra or [])
    tokens.extend(["--probability", probability,
                   "--chaos_propagation",
                   "--prop_trace_file", "prop_trace.csv.gz"])
    return tokens


ABSENT_CMD = _cmd()


def _mounted_cmd(flag="--chaos_addrpath", probability="0.0", extra=None):
    return _cmd(probability=probability, mount=flag, extra=extra)


def _mk_run(
    tmp_path: Path,
    name: str = "M-R01-control",
    *,
    tokens=None,
    write_command: bool = True,
    summary=None,
    write_summary: bool = True,
    pilot_meta=None,
    manifest=None,
    trace_present: bool = True,
    trace_events: int = 0,
    trace_summary_injections=0,
    logs=None,
):
    run = tmp_path / name
    run.mkdir()
    if write_command:
        (run / "command.txt").write_text("\n".join(tokens or ABSENT_CMD) + "\n")
    if write_summary and summary is not None:
        (run / "summary.json").write_text(json.dumps(summary))
    if pilot_meta is not None:
        (run / "pilot_meta.json").write_text(json.dumps(pilot_meta))
    if manifest is not None:
        (run / "manifest.json").write_text(json.dumps(manifest))
    if trace_present:
        lines = [
            json.dumps({"record_type": "event", "event_type": "injection"})
            for _ in range(trace_events)
        ]
        if trace_summary_injections is not None:
            lines.append(json.dumps({
                "record_type": "summary",
                "counts": {"injections": trace_summary_injections,
                           "events": 1, "edges": 0, "activations": 0},
            }))
        (run / "trace_v31.jsonl").write_text("\n".join(lines) + "\n")
    for fname, text in (logs or {}).items():
        (run / fname).write_text(text)
    return run


def _summary(injection_count=0, **extra):
    data = {"injection_count": injection_count, "oracle": True, "exit_code": 0}
    data.update(extra)
    return data


# --------------------------------------------------------------------------
# interface shape
# --------------------------------------------------------------------------
def test_interface_keys_are_exact(tmp_path):
    run = _mk_run(tmp_path, summary=_summary())
    result = cp.classify_control_run(run)
    assert set(result) == INTERFACE_KEYS


# --------------------------------------------------------------------------
# 1. injector absent
# --------------------------------------------------------------------------
def test_injector_absent_is_pass_and_does_not_default_attempt(tmp_path):
    run = _mk_run(tmp_path, summary=_summary())
    result = cp.classify_control_run(run)
    assert result["injector_mounted"] is False
    assert result["fault_enabled"] is False
    assert result["proof_class"] == cp.PROOF_INJECTOR_ABSENT
    assert result["injection_applied_count"] == 0
    # No trigger/log counter exists in this fixture => must be UNKNOWN, not 0.
    assert result["injection_attempt_count"] == cp.UNKNOWN
    assert result["status"] == cp.STATUS_PASS
    assert any("absent" in line.lower() for line in result["evidence"])


# --------------------------------------------------------------------------
# 2. mounted but probability 0.0 (global and md04)
# --------------------------------------------------------------------------
def test_mounted_probability_zero_is_disabled_and_pass(tmp_path):
    run = _mk_run(
        tmp_path,
        tokens=_mounted_cmd(probability="0.0"),
        summary=_summary(),
        logs={"stdout.log":
              "CHAOS_LSU_TRIGGER: injector=CHAOSAddrPath tier=F0 "
              "attempted=0 eligible=597 injected=0\n"},
    )
    result = cp.classify_control_run(run)
    assert result["injector_mounted"] is True
    assert result["fault_enabled"] is False
    assert result["proof_class"] == cp.PROOF_MOUNTED_BUT_DISABLED
    assert result["suppression_reason"] == "probability=0.0"
    assert result["injection_attempt_count"] == 0  # real counter, not a default
    assert result["injection_applied_count"] == 0
    assert result["status"] == cp.STATUS_PASS


def test_md04_probability_zero_is_disabled(tmp_path):
    run = _mk_run(
        tmp_path,
        tokens=_mounted_cmd(
            flag="--chaos_md04", probability="1.0",
            extra=["--md04_probability", "0.0"],
        ),
        summary=_summary(),
    )
    result = cp.classify_control_run(run)
    assert result["injector_mounted"] is True
    assert result["proof_class"] == cp.PROOF_MOUNTED_BUT_DISABLED
    assert "md04_probability=0.0" in result["suppression_reason"]
    assert result["fault_enabled"] is False
    assert result["status"] == cp.STATUS_PASS


def test_mounted_without_gate_probability_is_incomplete(tmp_path):
    # Mounted, but no --probability token and no recorded gate value: cannot
    # prove the injector was disabled, so this must not be PASS.
    tokens = [
        "build/ARM/gem5.opt", "--outdir=/tmp/x",
        "configs/se/lsu_proxy.py", "--cmd=/tmp/wl",
        "--cpu", "O3", "--variant", "B0",
        "--chaos_addrpath", "--chaos_propagation",
    ]
    run = _mk_run(tmp_path, tokens=tokens, summary=_summary())
    result = cp.classify_control_run(run)
    assert result["injector_mounted"] is True
    assert result["proof_class"] == cp.PROOF_INCOMPLETE
    assert result["status"] == cp.STATUS_INCOMPLETE


# --------------------------------------------------------------------------
# 3. explicit suppression
# --------------------------------------------------------------------------
def test_explicit_suppression_flag_is_suppressed_and_pass(tmp_path):
    run = _mk_run(
        tmp_path,
        tokens=_mounted_cmd(probability="1.0", extra=["--chaos_suppress"]),
        summary=_summary(),
    )
    result = cp.classify_control_run(run)
    assert result["injector_mounted"] is True
    assert result["proof_class"] == cp.PROOF_MOUNTED_BUT_SUPPRESSED
    assert result["fault_enabled"] is False
    assert result["status"] == cp.STATUS_PASS


def test_recorded_suppression_rule_is_suppressed(tmp_path):
    run = _mk_run(
        tmp_path,
        tokens=_mounted_cmd(probability="1.0"),
        summary=_summary(),
        pilot_meta={"injector": {
            "mount_flags": ["--chaos_addrpath"],
            "mounted": True,
            "probability": 1.0,
            "suppression_flags": ["--fw02_suppress_forward"],
        }},
    )
    result = cp.classify_control_run(run)
    assert result["proof_class"] == cp.PROOF_MOUNTED_BUT_SUPPRESSED
    assert result["status"] == cp.STATUS_PASS


# --------------------------------------------------------------------------
# 4. an applied injection is FAIL, never PASS
# --------------------------------------------------------------------------
def test_applied_injection_is_fail(tmp_path):
    run = _mk_run(
        tmp_path,
        tokens=_mounted_cmd(probability="1.0"),
        summary=_summary(injection_count=1),
        logs={"lsq_fwd_injections.log": "faults_injected: 1\n"},
    )
    result = cp.classify_control_run(run)
    assert result["injection_applied_count"] == 1
    assert result["status"] == cp.STATUS_FAIL
    assert result["status"] != cp.STATUS_PASS


def test_trace_injection_event_is_fail_even_if_summary_says_zero(tmp_path):
    run = _mk_run(
        tmp_path,
        tokens=_mounted_cmd(probability="1.0"),
        summary=_summary(injection_count=0),
        trace_events=1,
        trace_summary_injections=0,
    )
    result = cp.classify_control_run(run)
    assert result["injection_applied_count"] == 1
    assert result["status"] == cp.STATUS_FAIL


# --------------------------------------------------------------------------
# 5. missing summary => INCOMPLETE, never 0/PASS
# --------------------------------------------------------------------------
def test_missing_summary_is_incomplete_not_zero(tmp_path):
    run = _mk_run(
        tmp_path,
        summary=None,
        write_summary=False,
        trace_summary_injections=None,
    )
    result = cp.classify_control_run(run)
    assert result["injection_applied_count"] == cp.UNKNOWN
    assert result["injection_applied_count"] != 0
    assert result["status"] == cp.STATUS_INCOMPLETE
    assert result["status"] != cp.STATUS_PASS


# --------------------------------------------------------------------------
# 6. missing applied count => INCOMPLETE, never 0/PASS
# --------------------------------------------------------------------------
def test_missing_count_is_unknown_not_zero(tmp_path):
    summary = {"oracle": True, "exit_code": 0}  # no injection_count
    run = _mk_run(
        tmp_path,
        summary=summary,
        trace_summary_injections=None,
    )
    result = cp.classify_control_run(run)
    assert result["injection_applied_count"] == cp.UNKNOWN
    assert result["injection_applied_count"] != 0
    assert result["status"] == cp.STATUS_INCOMPLETE


# --------------------------------------------------------------------------
# 7. missing trace for a *mounted* control => INCOMPLETE
# --------------------------------------------------------------------------
def test_missing_trace_for_mounted_control_is_incomplete(tmp_path):
    run = _mk_run(
        tmp_path,
        tokens=_mounted_cmd(probability="0.0"),
        summary=_summary(injection_count=0),
        trace_present=False,
    )
    result = cp.classify_control_run(run)
    # The summary count is real (0) and is not defaulted, but a mounted zero
    # without a trace cannot be corroborated, so it must not be PASS.
    assert result["injection_applied_count"] == 0
    assert result["status"] == cp.STATUS_INCOMPLETE
    assert result["status"] != cp.STATUS_PASS


def test_missing_trace_for_absent_injector_remains_pass(tmp_path):
    # RP01's real shape: no trace exists because the injector was never
    # mounted; the command itself is the proof and summary is authoritative.
    run = _mk_run(
        tmp_path,
        summary=_summary(injection_count=0),
        trace_present=False,
    )
    result = cp.classify_control_run(run)
    assert result["proof_class"] == cp.PROOF_INJECTOR_ABSENT
    assert result["injection_applied_count"] == 0
    assert result["status"] == cp.STATUS_PASS


# --------------------------------------------------------------------------
# 8. command evidence: executed command.txt, never summary["cmd"]
# --------------------------------------------------------------------------
def test_command_txt_is_used_and_summary_cmd_is_ignored(tmp_path):
    # summary["cmd"] is the run_pilot driver argv and never carries the mount
    # (the historical mislabel source).  command.txt does.
    run = _mk_run(
        tmp_path,
        tokens=_mounted_cmd(probability="0.0"),
        summary=_summary(cmd=["python3", "run_pilot.py", "--probability", "0.0"]),
    )
    result = cp.classify_control_run(run)
    assert result["injector_mounted"] is True
    assert result["proof_class"] == cp.PROOF_MOUNTED_BUT_DISABLED


def test_missing_command_evidence_is_incomplete(tmp_path):
    summary = _summary(
        cmd=["python3", "run_pilot.py", "--probability", "0.0"],
    )
    run = _mk_run(
        tmp_path,
        write_command=False,
        summary=summary,
    )
    result = cp.classify_control_run(run)
    assert result["injector_mounted"] is None
    assert result["proof_class"] == cp.PROOF_INCOMPLETE
    assert result["status"] == cp.STATUS_INCOMPLETE
    assert result["status"] != cp.STATUS_PASS


def test_manifest_command_is_an_executed_command_fallback(tmp_path):
    run = _mk_run(
        tmp_path,
        write_command=False,
        summary=_summary(),
        manifest={"command": _mounted_cmd(probability="0.0")},
    )
    result = cp.classify_control_run(run)
    assert result["injector_mounted"] is True
    assert result["proof_class"] == cp.PROOF_MOUNTED_BUT_DISABLED
    assert result["status"] == cp.STATUS_PASS


# --------------------------------------------------------------------------
# 9. conflicting gate records are not a pass
# --------------------------------------------------------------------------
def test_conflicting_probability_is_incomplete(tmp_path):
    run = _mk_run(
        tmp_path,
        tokens=_mounted_cmd(probability="0.0"),
        summary=_summary(mount_evidence={"probability": 1.0}),
    )
    result = cp.classify_control_run(run)
    assert result["status"] == cp.STATUS_INCOMPLETE


# --------------------------------------------------------------------------
# integration: the real 60 pre-formal controls via the CLI
# --------------------------------------------------------------------------
@pytest.mark.skipif(not REAL_RUNS.is_dir(), reason="pre-formal runs absent")
def test_cli_real_pre_formal_controls(tmp_path):
    out = tmp_path / "LSU_Control_Zero_Proof.csv"
    rc = cp.main(["--runs", str(REAL_RUNS), "--out", str(out)])
    assert rc == 0

    with out.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 60

    by_proof: dict[str, int] = {}
    by_status: dict[str, int] = {}
    mounted = 0
    for row in rows:
        by_proof[row["ControlZeroProof"]] = by_proof.get(row["ControlZeroProof"], 0) + 1
        by_status[row["ControlProofStatus"]] = by_status.get(row["ControlProofStatus"], 0) + 1
        assert row["EvidenceKind"] == "PRE_FORMAL"
        if row["InjectorMounted"] == "YES":
            mounted += 1
        # Applied is a real number or UNKNOWN -- never blank / fabricated.
        assert row["InjectionAppliedCount"] in (cp.UNKNOWN, "0")

    assert mounted == 35
    assert by_proof.get(cp.PROOF_MOUNTED_BUT_DISABLED) == 35
    assert by_proof.get(cp.PROOF_INJECTOR_ABSENT) == 25
    assert by_proof.get(cp.PROOF_MOUNTED_BUT_SUPPRESSED, 0) == 0
    assert by_proof.get(cp.PROOF_INCOMPLETE, 0) == 0
    assert by_status == {cp.STATUS_PASS: 60}
