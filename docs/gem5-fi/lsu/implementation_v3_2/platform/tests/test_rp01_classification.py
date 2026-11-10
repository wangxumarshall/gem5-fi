"""RP01 classification-path tests (LSU v3.2.12 Task 15 prep).

RP01 skips the ordinal-selected partial-coverage ``rescheduleMemInst`` call
(``lsq_unit.cc:2016``). The task-14 wake-up audit proved no other path
re-issues the skipped load, so the designed terminals are HANG/TIMEOUT
(watchdog fatal / external cut) or SQUASHED (an older squash discards the
entry) — never MASKED (design gate v3.2.11 section 6 / condition 4).

These tests pin the three layers the closure round grades a pilot through:

1. ``terminal_rules.adjudicate`` — a HANG observed terminal is returned
   as-is even with a passing oracle; an externally cut run
   (``observed_terminal == "TIMEOUT"``) is terminal for RP01 and can never
   be relabelled MASKED by downstream chain state; a squashed target is
   SQUASHED; a chain with no commit is never MASKED. The TIMEOUT guard is
   model-scoped: another model's adjudication is byte-identical to before.
2. ``trace_completeness`` — the RP01 profiles: the fault's own chain needs
   the injection plus the skip marker (the call-site ``replay`` record the
   branch still emits, or a dedicated ``rp01_skip`` record) for
   HANG/TIMEOUT, and the ``squash`` node for SQUASHED.
3. ``tools.lsu_12model_closure.build_pilot_record`` — the end-to-end
   per-pilot record over a synthetic pilot dir (the same shape
   ``tests/test_lsu_12model_closure.py`` uses): a HANG pilot with the
   identity-linked skip record grades a proven-trigger complete verdict;
   a SQUASHED pilot stays PARTIAL (the frozen v3.2.11 line: an unproven
   squash is never a complete verdict); a TIMEOUT pilot records
   ``RP01_EXTERNAL_TIMEOUT`` and never MASKED.
"""
import json
import sys
from pathlib import Path

PLATFORM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLATFORM))
# PLATFORM = <root>/docs/gem5-fi/lsu/implementation_v3_2/platform, so the
# repo root (holding tools/lsu_12model_closure.py) is parents[4]
sys.path.insert(0, str(PLATFORM.parents[4] / "tools"))

from terminal_rules import adjudicate  # noqa: E402
from trace_completeness import (  # noqa: E402
    check_completeness,
    expected_stages,
)
from trace_writer import TraceWriter  # noqa: E402

from lsu_12model_closure import build_pilot_record  # noqa: E402

SHA = "720eb780bc87fe5e5ec045801d314e9c5edf54c6eca59032f1b8b7887ac74070"
WORK_SHA = "ca15390f1a797c55074703dc3fe10d1e07f7704794a9abca96b2761c41d838f4"
SEQ = 69341  # the preflight's ordinal-1 load (RP01_CountOnly_Preflight §3)


def _ev(kind, seq, ptag=1, value=None, detail="", **kw):
    row = {"event_type": kind, "dyn_inst_seq": seq, "ptag": ptag,
           "new_value": value, "detail": detail}
    row.update(kw)
    return row


def _rp01_chain(marker="rp01_skip", squashed=False):
    events = [
        _ev("injection", SEQ,
            detail="site=read_partial_reschedule;skipped_call=1;"
                   "lq_idx=9201;lq_gen=9693;store_seq=69334;"
                   "replay_gen_pre=0;replay_gen_post=1;"
                   "in_instsToReplay_pre=0;in_instsToReplay_post=0;"
                   "pc=4015fc"),
        _ev(marker, SEQ,
            detail="replay_generation=1;partial_forward_mismatch=1;"
                   "in_instsToReplay_post=0"),
    ]
    if squashed:
        events.append(_ev("squash", SEQ, ptag=0,
                          detail="squash_reason=branch_mispredict"))
    return events


# ---------------------------------------------------------------------------
# layer 1: terminal_rules.adjudicate
# ---------------------------------------------------------------------------

def test_hang_with_skip_record_is_hang_even_with_passing_oracle():
    """A synthetic HANG trace with a skip record -> HANG (hard terminal wins
    over a passing oracle; the oracle never relabels it)."""
    terminal, reason = adjudicate(
        _rp01_chain(), model="RP01", observed_terminal="HANG",
        oracle_pass=True, trace_complete=True)
    assert terminal == "HANG"
    assert reason is None


def test_hang_with_replay_marker_is_hang():
    """The call-site replay record (noteReplay fires before the guarded call)
    is the other accepted skip marker on the chain."""
    terminal, _ = adjudicate(
        _rp01_chain(marker="replay"), model="RP01", observed_terminal="HANG",
        oracle_pass=True, trace_complete=True)
    assert terminal == "HANG"


def test_external_timeout_is_terminal_for_rp01_never_masked():
    """An externally cut run is TIMEOUT for RP01 even when the chain carries
    commit + consumer state and the oracle passed — the exact shape that
    would otherwise be adjudicated MASKED."""
    events = _rp01_chain() + [
        _ev("register_writeback", SEQ, value="0x1"),
        _ev("commit", SEQ, ptag=0),
        _ev("consumer_commit", SEQ + 1, value="0x1"),
    ]
    terminal, reason = adjudicate(
        events, model="RP01", observed_terminal="TIMEOUT",
        oracle_pass=True, trace_complete=True)
    assert terminal == "TIMEOUT"
    assert reason == "RP01_EXTERNAL_TIMEOUT"
    assert terminal != "MASKED"


def test_timeout_guard_is_model_scoped():
    """No other model changes: a TIMEOUT-observed LQ04 chain adjudicates
    exactly as before (through the chain, to MASKED here) — the guard never
    fires for a non-RP01 model."""
    events = [
        _ev("injection", 50),
        _ev("memory_response", 50, value="0000000000000001"),
        _ev("register_writeback", 50, value="0000000000000001"),
        _ev("commit", 50, ptag=0),
    ]
    terminal, reason = adjudicate(
        events, model="LQ04", observed_terminal="TIMEOUT",
        oracle_pass=True, trace_complete=True)
    assert (terminal, reason) == ("MASKED", "TARGET_COMMITTED_DATA_VALUE_PRESENT")


def test_squashed_trace_is_squashed():
    """A SQUASHED trace -> SQUASHED (the squash discards the skipped load
    before commit; audit P5 exit)."""
    terminal, reason = adjudicate(
        _rp01_chain(squashed=True), model="RP01", observed_terminal="MASKED",
        oracle_pass=True, trace_complete=True)
    assert terminal == "SQUASHED"
    assert reason == "TARGET_SQUASHED_NO_COMMIT"


def test_uncommitted_chain_is_never_masked():
    """A chain whose target never commits can never be MASKED: with the skip
    marker present and no commit node the adjudication is UNRESOLVED with
    the store-not-committed reason, whatever the oracle says."""
    terminal, reason = adjudicate(
        _rp01_chain(), model="RP01", observed_terminal="MASKED",
        oracle_pass=True, trace_complete=True)
    assert terminal == "UNRESOLVED"
    assert reason == "STORE_NOT_COMMITTED"
    assert terminal != "MASKED"


# ---------------------------------------------------------------------------
# layer 2: trace_completeness profiles
# ---------------------------------------------------------------------------

def test_expected_stages_rp01():
    assert expected_stages("RP01", "HANG") == [
        ("injection", "replay"), ("injection", "rp01_skip")]
    assert expected_stages("RP01", "TIMEOUT") == [
        ("injection", "replay"), ("injection", "rp01_skip")]
    assert expected_stages("RP01", "SQUASHED") == [("injection", "squash")]
    # an unknown terminal falls back to the minimal default profile
    assert expected_stages("RP01", "MASKED") == [("injection",)]
    assert expected_stages("RP01", None) == [("injection",)]


def _write_trace(path, model, terminal, run_status, kinds):
    w = TraceWriter(path, "RP01-F6-W7-S01-R01", "RP01-F6-W7", "S01",
                    "RP01-CFG01", model)
    for i, kind in enumerate(kinds, start=1):
        w.event(kind, dyn_inst_seq=SEQ, ptag=1,
                injection_status=("INJECTED" if kind == "injection"
                                  else "NOT_APPLICABLE"),
                activation_status="TRIGGERED",
                detail=f"site=read_partial_reschedule;ordinal={i}",
                trace_completeness="COMPLETE")
    w.close(run_status=run_status, activation="TRIGGERED",
            terminal=terminal, completeness="COMPLETE",
            observed_terminal=terminal)
    return path


def test_coverage_rp01_hang_complete(tmp_path):
    path = _write_trace(tmp_path / "hang.jsonl", "RP01", "HANG", "TIMEOUT",
                        ["injection", "rp01_skip"])
    report = check_completeness(path)
    assert report["propagation_coverage"] == "COMPLETE"
    assert report["missing_stages"] == []
    assert "rp01_skip" in report["propagation_stages"]
    # the replay-marker alternative is equally complete
    alt = _write_trace(tmp_path / "hang_replay.jsonl", "RP01", "HANG",
                       "TIMEOUT", ["injection", "replay"])
    alt_report = check_completeness(alt)
    assert alt_report["propagation_coverage"] == "COMPLETE"


def test_coverage_rp01_hang_partial_without_marker(tmp_path):
    path = _write_trace(tmp_path / "bare.jsonl", "RP01", "HANG", "TIMEOUT",
                        ["injection"])
    report = check_completeness(path)
    assert report["propagation_coverage"] == "PARTIAL"
    assert report["missing_stages"] == ["rp01_skip"] or \
        report["missing_stages"] == ["replay"]


def test_coverage_rp01_squashed_complete(tmp_path):
    path = _write_trace(tmp_path / "squash.jsonl", "RP01", "SQUASHED",
                        "COMPLETED", ["injection", "rp01_skip", "squash"])
    report = check_completeness(path)
    assert report["propagation_coverage"] == "COMPLETE"
    assert report["missing_stages"] == []


# ---------------------------------------------------------------------------
# layer 3: the closure record (end-to-end over a synthetic pilot dir)
# ---------------------------------------------------------------------------

def _write_pilot(directory, *, terminal, observed, run_status,
                  marker="rp01_skip", squashed=False, oracle=False):
    directory = Path(directory)
    directory.mkdir(parents=True)
    sample = f"RP01-F6-W7-S01-{directory.name.split('-')[-1]}"
    lines = []

    def ev(eid, etype, tick, seq, ptag, detail, **extra):
        rec = {"record_type": "event", "trace_version": "v3.1",
               "event_id": str(eid), "event_type": etype,
               "timestamp": str(tick), "dyn_inst_seq": str(seq),
               "ptag": str(ptag), "detail": detail}
        rec.update(extra)
        return rec

    lines.append(ev(1, "injection", 31072965, SEQ, 1,
                    "site=read_partial_reschedule;skipped_call=1;"
                    "lq_idx=9201;lq_gen=9693;store_seq=69334;pc=4015fc;"
                    "replay_gen_pre=0;replay_gen_post=1;"
                    "in_instsToReplay_pre=0;in_instsToReplay_post=0",
                    injection_status="INJECTED",
                    activation_status="TRIGGERED"))
    lines.append(ev(2, marker, 31072965, SEQ, 1,
                    "replay_generation=1;partial_forward_mismatch=1;"
                    "in_instsToReplay_post=0",
                    activation_status="TRIGGERED"))
    if squashed:
        lines.append(ev(3, "squash", 32000000, SEQ, 0,
                        "squash_reason=branch_mispredict"))
    lines.append({"record_type": "summary", "trace_version": "v3.1",
                  "run_id": "RP01-F6-W7", "sub_task_id": "RP01-F6-W7-S01",
                  "fault_id": "RP01-CFG01", "fault_model_id": "RP01",
                  "run_status": run_status,
                  "fault_activation_status": "TRIGGERED",
                  "terminal_state": terminal,
                  "observed_terminal": observed,
                  "trace_completeness": "COMPLETE",
                  "counts": {"events": len(lines), "edges": 0,
                             "injections": 1, "activations": 1}})
    trace = "\n".join(json.dumps(r) for r in lines) + "\n"
    (directory / "trace_v31.jsonl").write_text(trace, encoding="utf-8")

    meta = {
        "pilot_id": sample, "model": "RP01",
        "run_type": "pilot", "seed": 3135797961,
        "excel_identity": {"run_id": "RP01-F6-W7",
                           "sub_task_id": "RP01-F6-W7-S01",
                           "sample_run_id": sample, "seed": 3135797961,
                           "event_ordinal": 1, "event_ordinal_used": 1},
        "exit_code": 1 if terminal in ("HANG", "TIMEOUT") else 0,
        "injection_count": 1,
        "trace": {"validator_errors": [], "truncated": False},
        "classification": {
            "run_status": run_status,
            "fault_activation_status": "TRIGGERED",
            "observed_terminal": observed, "terminal_state": terminal,
            "trace_completeness": "COMPLETE",
            "oracle_outcome": ("NOT_APPLICABLE" if not oracle
                               else ("PASS" if terminal == "SQUASHED"
                                     else "NOT_APPLICABLE")),
        },
    }
    (directory / "pilot_meta.json").write_text(json.dumps(meta, indent=2),
                                               encoding="utf-8")
    manifest = {
        "schema_version": "lsu-run-manifest-v3.2", "sample_run_id": sample,
        "run_id": "RP01-F6-W7", "sub_task_id": "RP01-F6-W7-S01",
        "model_id": "RP01", "seed": 3135797961,
        "fault": {"location": "LSQUnit::read() partial-coverage "
                              "rescheduleMemInst (lsq_unit.cc:2016)",
                  "target_field": "replay trigger",
                  "event_ordinal": 1},
        "workload": {"sha256": WORK_SHA},
        "gem5": {"binary": "/build/ARM/gem5.opt", "binary_sha256": SHA},
    }
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2),
                                              encoding="utf-8")
    return directory


def test_rp01_hang_pilot_record(tmp_path):
    """The watchdog-fatal HANG pilot: proven via the identity-linked skip
    record, one complete context -> VERIFIED_SINGLE_CONTEXT, oracle
    NOT_APPLICABLE (a hung run has no checksum)."""
    pilot = _write_pilot(tmp_path / "RP01-R01", terminal="HANG",
                         observed="HANG", run_status="TIMEOUT")
    record = build_pilot_record(pilot, "RP01", binary_sha=SHA)
    assert record["ObservedTerminal"] == "HANG"
    assert record["FaultCausality"] == "PROVEN"
    assert record["StructuralChainCompleteness"] == "COMPLETE"
    assert record["ApplicationOracle"] == "NOT_APPLICABLE"
    assert record["FinalClassification"] == "VERIFIED_SINGLE_CONTEXT"
    assert record["MaskingMechanism"] == "NOT_APPLICABLE"


def test_rp01_hang_causality_follows_the_marker_kind(tmp_path):
    """Without the identity-linked marker on the chain the same HANG is not
    fault-proven (the closure tool's conservative PARTIAL line)."""
    pilot = _write_pilot(tmp_path / "RP01-R02", terminal="HANG",
                         observed="HANG", run_status="TIMEOUT",
                         marker="replay")
    record = build_pilot_record(pilot, "RP01", binary_sha=SHA)
    assert record["ObservedTerminal"] == "HANG"
    assert record["FaultCausality"] == "PROVEN"  # replay is a hang marker
    bare = _write_pilot(tmp_path / "RP01-R03", terminal="HANG",
                        observed="HANG", run_status="TIMEOUT",
                        marker="lq_lifecycle")
    bare_record = build_pilot_record(bare, "RP01", binary_sha=SHA)
    assert bare_record["FaultCausality"] != "PROVEN"
    assert bare_record["FinalClassification"] == "PARTIAL"
    assert bare_record["ObservedTerminal"] == "HANG"


def test_rp01_timeout_pilot_record_never_masked(tmp_path):
    """An externally cut pilot (observed TIMEOUT via pilot_meta): the
    record carries RP01_EXTERNAL_TIMEOUT and the terminal is TIMEOUT,
    never MASKED."""
    pilot = _write_pilot(tmp_path / "RP01-R04", terminal="TIMEOUT",
                         observed="TIMEOUT", run_status="TIMEOUT")
    record = build_pilot_record(pilot, "RP01", binary_sha=SHA)
    assert record["ObservedTerminal"] == "TIMEOUT"
    assert record["TerminalReason"] == "RP01_EXTERNAL_TIMEOUT"
    assert record["FinalClassification"] == "VERIFIED_SINGLE_CONTEXT"
    assert record["ObservedTerminal"] != "MASKED"


def test_rp01_squashed_pilot_record_is_partial(tmp_path):
    """A SQUASHED pilot: the squash node is the target's own but nothing
    proves the squash is fault-CAUSED, so the frozen v3.2.11 line keeps it
    PARTIAL (never a complete verdict, never MASKED)."""
    pilot = _write_pilot(tmp_path / "RP01-R05", terminal="SQUASHED",
                         observed="SQUASHED", run_status="COMPLETED",
                         squashed=True)
    record = build_pilot_record(pilot, "RP01", binary_sha=SHA)
    assert record["ObservedTerminal"] == "SQUASHED"
    assert record["FaultCausality"] == "PARTIAL"
    assert record["FinalClassification"] == "PARTIAL"
    assert record["ObservedTerminal"] != "MASKED"
