"""RP01 log-bridge tests (LSU v3.2.12 Task 15).

The committed RP01 hook (binary SHA 68c6ce73...) prints
``RP01_SKIP_REPLAY`` to the run log only — the prop trace carries the
skipped load's ``replay`` marker (``noteReplay`` fires before the guarded
call at ``lsq_unit.cc:2016``) but **no injection record**, so the audit
pipeline would grade ``NO_INJECTION_EVENT``. The bridge
(``--rp01-skip-log`` on ``prop_trace_to_v31.py``) parses the single real
skip line and emits it as the trace injection record.

These tests pin, over a synthetic log sample in the exact real C++ format
(``CHAOSLSQFwd.cc`` ``maybeSkipPartialReplay``):

1. the emitted injection record carries every field of the real line plus
   the raw line, the log path and the log SHA256 as provenance — nothing
   is fabricated;
2. the end-to-end closure record over the bridged pilot dir grades a HANG
   pilot with the identity-linked replay marker as a proven complete
   context (no ``NO_INJECTION_EVENT``);
3. the honest caps: a truncated (watchdog-fatal) trace stays HANG with
   PROVEN causality while the FinalClassification caps at UNRESOLVED
   (RecordIntegrity=TRUNCATED — prep concern C2); an externally cut run
   records ObservedTerminal=TIMEOUT / RP01_EXTERNAL_TIMEOUT, never MASKED;
4. the refusals: a control log (no skip line), multiple skip lines, an
   incomplete line, and a trace that already carries an injection record
   are never bridged.
"""
import gzip
import hashlib
import json
import sys
from pathlib import Path

PLATFORM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLATFORM))
sys.path.insert(0, str(PLATFORM.parents[4] / "tools"))

import pytest  # noqa: E402

from tools.prop_trace_to_v31 import convert, parse_rp01_skip_line  # noqa: E402
from lsu_12model_closure import build_pilot_record  # noqa: E402

SHA = "68c6ce737a95747e5f35be06fea160b4f461baead2c0b4d85cf900c4d047e4e8"
WORK_SHA = "ca15390f1a797c55074703dc3fe10d1e07f7704794a9abca96b2761c41d838f4"
SEQ = 69341
PC_DEC = 4199932          # 0x4015fc, printed decimal by the C++ hook
TICK = 31072965

# The exact real line format (CHAOSLSQFwd.cc, stdout): one line, key=value
# tokens, load_pc decimal, in_instsToReplay_pre/post=0 because the guarded
# call was skipped.
SKIP_LINE = (
    "RP01_SKIP_REPLAY ordinal=1 load_seq=69341 load_pc=4199932 "
    "lq_idx=9201 lq_gen=9693 store_seq=69334 replay_gen_pre=0 "
    "replay_gen_post=1 in_instsToReplay_pre=0 in_instsToReplay_post=0 "
    "tick=31072965")

SYNTHETIC_LOG = "\n".join([
    "RP01_ELIGIBLE ordinal=1 load_seq=69341 load_pc=4199932 lq_idx=9201 "
    "lq_gen=9693 store_seq=69334 replay_gen_pre=0 replay_gen_post=1 "
    "in_instsToReplay_pre=0 in_instsToReplay_post=0 tick=31072965",
    SKIP_LINE,
    "CHAOS_RP01_WATCHDOG=EXPIRED fired=1 injected=1 eligible=1 "
    "tick=77129665",
    "fatal: CHAOS_RP01_WATCHDOG_EXPIRED tick=77129665 injected=1 eligible=1",
]) + "\n"


def _write_log(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def _write_csv(path: Path, rows: list[str]) -> Path:
    """A synthetic CHAOSPropagation CSV in the real writeNode column order
    (node_id,tick,ptag,kind,dyn_seq,req_id,addr,phys,arch,detail). The
    replay node is the one noteReplay emits before the guarded call."""
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        for row in rows:
            fh.write(row + "\n")
    return path


def _replay_rows() -> list[str]:
    return [
        "1,%d,0,replay,%d,,,,,"
        "reason=partial_forward_mismatch;pc=4015fc;execution_attempt_id=0;"
        "replay_generation=1;lq_entry_id=9201;sq_entry_id=0;"
        "entry_generation=9693" % (TICK, SEQ),
        "2,%d,0,replay,%d,,,,,"
        "reason=translation_delayed;pc=42a6d8;execution_attempt_id=0;"
        "replay_generation=1;lq_entry_id=9349;sq_entry_id=0;"
        "entry_generation=9915" % (35427700, 71013),
    ]


def _records(trace: Path) -> list[dict]:
    return [json.loads(line) for line in
            trace.read_text(encoding="utf-8").splitlines()]


# ---------------------------------------------------------------------------
# parse: every field comes from the real line
# ---------------------------------------------------------------------------

def test_parse_extracts_every_field(tmp_path):
    log = _write_log(tmp_path / "stdout.log", SYNTHETIC_LOG)
    parsed = parse_rp01_skip_line(log)
    assert parsed["raw_line"] == SKIP_LINE
    assert parsed == {
        "raw_line": SKIP_LINE, "ordinal": 1, "load_seq": SEQ,
        "load_pc": PC_DEC, "lq_idx": 9201, "lq_gen": 9693,
        "store_seq": 69334, "replay_gen_pre": 0, "replay_gen_post": 1,
        "in_instsToReplay_pre": 0, "in_instsToReplay_post": 0,
        "tick": TICK}


def test_parse_refuses_control_log(tmp_path):
    """A control run has no skip line: the bridge must refuse, not emit."""
    log = _write_log(tmp_path / "stdout.log",
                     "RP01_ELIGIBLE ordinal=1 load_seq=1\n"
                     "checksum=0x59fc61c040618747\n")
    with pytest.raises(SystemExit, match="REFUSE.*no RP01_SKIP_REPLAY"):
        parse_rp01_skip_line(log)


def test_parse_refuses_multiple_skip_lines(tmp_path):
    log = _write_log(tmp_path / "stdout.log",
                     SKIP_LINE + "\n" + SKIP_LINE.replace("ordinal=1",
                                                          "ordinal=2")
                     + "\n")
    with pytest.raises(SystemExit, match="REFUSE.*expected exactly 1"):
        parse_rp01_skip_line(log)


def test_parse_refuses_incomplete_line(tmp_path):
    line = ("RP01_SKIP_REPLAY ordinal=1 load_seq=69341 load_pc=4199932 "
            "lq_idx=9201 store_seq=69334 tick=31072965")  # lq_gen missing
    log = _write_log(tmp_path / "stdout.log", line + "\n")
    with pytest.raises(SystemExit, match="REFUSE.*missing fields"):
        parse_rp01_skip_line(log)


def test_parse_refuses_non_integer_field(tmp_path):
    line = SKIP_LINE.replace("lq_gen=9693", "lq_gen=broken")
    log = _write_log(tmp_path / "stdout.log", line + "\n")
    with pytest.raises(SystemExit, match="REFUSE.*not an integer"):
        parse_rp01_skip_line(log)


# ---------------------------------------------------------------------------
# convert: the bridged injection record
# ---------------------------------------------------------------------------

def _convert(tmp_path, log, csv=None, **kw):
    out = tmp_path / "trace_v31.jsonl"
    args = dict(
        sample_run_id="RP01-F6-W7-S01-R01", run_id="RP01-F6-W7",
        sub_task_id="RP01-F6-W7-S01", fault_id="RP01-CFG01",
        fault_model_id="RP01", run_status="TIMEOUT", activation="TRIGGERED",
        terminal="HANG", completeness="COMPLETE")
    args.update(kw)
    convert(csv or _write_csv(tmp_path / "prop_trace.csv.gz",
                             _replay_rows()),
            out, rp01_skip_log=log, **args)
    return out


def test_bridge_emits_injection_record_from_real_log_line(tmp_path):
    log = _write_log(tmp_path / "stdout.log", SYNTHETIC_LOG)
    out = _convert(tmp_path, log)
    recs = _records(out)
    injections = [r for r in recs
                  if r.get("record_type") == "event"
                  and r["event_type"] == "injection"]
    assert len(injections) == 1
    inj = injections[0]
    # every field of the real line, verbatim
    assert inj["dyn_inst_seq"] == SEQ
    assert inj["timestamp"] == TICK
    assert inj["event_ordinal"] == 1
    assert inj["store_seq"] == 69334
    assert inj["lq_entry_id"] == 9201
    assert inj["entry_generation"] == 9693
    assert inj["replay_generation"] == 1
    assert inj["rp01_replay_gen_pre"] == 0
    assert inj["rp01_in_instsToReplay_pre"] == 0
    assert inj["rp01_in_instsToReplay_post"] == 0
    assert inj["rp01_load_pc"] == PC_DEC
    assert inj["unit"] == "LSQ"
    assert inj["sub_unit"] == "partial_replay_reschedule"
    assert inj["injection_status"] == "INJECTED"
    assert inj["activation_status"] == "TRIGGERED"
    # the record has no CSV node: chain identity is the load's dyn_inst_seq
    assert inj["ptag"] == 0
    assert inj["source_node_id"] is None
    assert inj["parent_event_id"] is None
    # provenance: the raw line, the log path, the log SHA256
    assert inj["rp01_skip_replay_line"] == SKIP_LINE
    assert inj["source_log"].endswith("stdout.log")
    assert inj["source_log_sha256"] == hashlib.sha256(
        log.read_bytes()).hexdigest()
    assert "bridge=rp01_skip_replay_log" in inj["detail"]
    assert "skipped_call=1" in inj["detail"]
    # the summary counts exactly one injection and one activation
    summary = [r for r in recs if r.get("record_type") == "summary"][0]
    assert summary["counts"]["injections"] == 1
    assert summary["counts"]["activations"] == 1


def test_bridge_refuses_when_trace_already_has_injection(tmp_path):
    """A trace that already carries an injection record must not be bridged
    twice. Present-day shape: a generic ``inj`` row. Future shape: a binary
    that emits ``inj_rp01`` nodes together with the converter map row the
    prep report proposed — simulated here by monkey-patching KIND_MAP."""
    from tools import prop_trace_to_v31 as conv_mod
    log = _write_log(tmp_path / "stdout.log", SYNTHETIC_LOG)

    # present-day: any KIND_MAP row mapping to "injection"
    rows = _replay_rows() + [
        "3,%d,1,inj,%d,,,,,family=other" % (TICK, SEQ)]
    csv = _write_csv(tmp_path / "prop_trace.csv.gz", rows)
    with pytest.raises(SystemExit, match="REFUSE.*already carries"):
        _convert(tmp_path, log, csv=csv)

    # future: the dedicated inj_rp01 kind with its proposed map row
    conv_mod.KIND_MAP["inj_rp01"] = "injection"
    try:
        rows = _replay_rows() + [
            "3,%d,0,inj_rp01,%d,,,,,site=read_partial_reschedule"
            % (TICK, SEQ)]
        csv = _write_csv(tmp_path / "prop_trace.csv.gz", rows)
        with pytest.raises(SystemExit, match="REFUSE.*already carries"):
            _convert(tmp_path, log, csv=csv)
    finally:
        del conv_mod.KIND_MAP["inj_rp01"]


def test_control_trace_without_bridge_has_no_injection(tmp_path):
    """Without the flag the converter's behavior is unchanged: a control
    trace (replay markers only) carries zero injection records and the
    closure tool honestly reports NO_INJECTION_EVENT."""
    out = tmp_path / "trace_v31.jsonl"
    convert(_write_csv(tmp_path / "prop_trace.csv.gz", _replay_rows()),
            out, sample_run_id="RP01-F6-W7-S01-C01", run_id="RP01-F6-W7",
            sub_task_id="RP01-F6-W7-S01", fault_id="RP01-CFG01",
            fault_model_id="RP01", run_status="COMPLETED",
            activation="NOT_TRIGGERED", terminal="UNRESOLVED",
            completeness="COMPLETE")
    assert not [r for r in _records(out)
                if r.get("event_type") == "injection"]


# ---------------------------------------------------------------------------
# the closure record over a bridged pilot dir (end-to-end)
# ---------------------------------------------------------------------------

def _write_pilot(tmp_path, *, observed="HANG", truncated=False,
                  oracle_outcome="NOT_APPLICABLE", run_status="TIMEOUT"):
    pilot = tmp_path / "RP01-R01"
    pilot.mkdir(parents=True)
    log = _write_log(pilot / "stdout.log", SYNTHETIC_LOG)
    out = pilot / "trace_v31.jsonl"
    csv = _write_csv(pilot / "prop_trace.csv.gz", _replay_rows())
    if truncated:
        # a watchdog fatal leaves the gz stream without its trailer: the
        # crash-durability flush keeps every completed node readable but
        # the stream reads as truncated
        data = csv.read_bytes()
        csv.write_bytes(data[:-8])
    convert(csv, out, sample_run_id="RP01-F6-W7-S01-R01",
            run_id="RP01-F6-W7", sub_task_id="RP01-F6-W7-S01",
            fault_id="RP01-CFG01", fault_model_id="RP01",
            run_status=run_status, activation="TRIGGERED", terminal="HANG",
            completeness="COMPLETE", observed_terminal=observed,
            terminal_reason=("RP01_EXTERNAL_TIMEOUT"
                             if observed == "TIMEOUT" else None),
            rp01_skip_log=log)
    meta = {
        "pilot_id": "RP01-F6-W7-S01-R01", "model": "RP01",
        "run_type": "pilot", "seed": 3135797961,
        "excel_identity": {"run_id": "RP01-F6-W7",
                           "sub_task_id": "RP01-F6-W7-S01",
                           "sample_run_id": "RP01-F6-W7-S01-R01",
                           "seed": 3135797961,
                           "event_ordinal": 1, "event_ordinal_used": 1},
        "exit_code": 1, "injection_count": 1,
        "trace": {"validator_errors": [], "truncated": truncated},
        "classification": {
            "run_status": run_status,
            "fault_activation_status": "TRIGGERED",
            "observed_terminal": observed, "terminal_state": "HANG",
            "trace_completeness": ("INCOMPLETE" if truncated
                                   else "COMPLETE"),
            "oracle_outcome": oracle_outcome},
    }
    (pilot / "pilot_meta.json").write_text(json.dumps(meta, indent=2),
                                           encoding="utf-8")
    manifest = {
        "schema_version": "lsu-run-manifest-v3.2",
        "sample_run_id": "RP01-F6-W7-S01-R01", "run_id": "RP01-F6-W7",
        "sub_task_id": "RP01-F6-W7-S01", "model_id": "RP01",
        "seed": 3135797961,
        "fault": {"location": "LSQUnit::read() PartialAddrRangeCoverage "
                              "rescheduleMemInst (lsq_unit.cc:2016)",
                  "target_field": "replay trigger (skip one "
                                  "ordinal-selected call)",
                  "event_ordinal": 1},
        "workload": {"sha256": WORK_SHA},
        "gem5": {"binary": "build/ARM/gem5.opt", "binary_sha256": SHA},
    }
    (pilot / "manifest.json").write_text(json.dumps(manifest, indent=2),
                                         encoding="utf-8")
    return pilot


def test_bridged_hang_pilot_record_is_proven(tmp_path):
    """A clean-skip pilot (not truncated): the bridged injection + the
    identity-linked replay marker -> proven HANG, structural chain
    COMPLETE, no NO_INJECTION_EVENT, VERIFIED_SINGLE_CONTEXT."""
    pilot = _write_pilot(tmp_path)
    record = build_pilot_record(pilot, "RP01", binary_sha=SHA)
    assert record["ObservedTerminal"] == "HANG"
    assert record["FaultCausality"] == "PROVEN"
    assert record["StructuralChainCompleteness"] == "COMPLETE"
    assert record["InjectionVerified"] == "yes"
    assert record["ActivationVerified"] == "yes"
    assert "NO_INJECTION_EVENT" not in record["MissingCodes"]
    assert sorted(record["ChainKinds"]) == ["injection", "replay"]
    assert record["InjectionSeq"] == str(SEQ)
    assert record["InjectionTick"] == str(TICK)
    assert record["FinalClassification"] == "VERIFIED_SINGLE_CONTEXT"
    assert record["ObservedTerminal"] != "MASKED"


def test_bridged_truncated_hang_stays_hang_with_proven_chain(tmp_path):
    """The watchdog-fatal shape (prep concern C2): the retained partial
    trace is truncated, so RecordIntegrity=TRUNCATED and the
    FinalClassification honestly caps at UNRESOLVED — but the ObservedTerminal
    stays HANG, the bridged chain stays PROVEN and the record is never
    MASKED."""
    pilot = _write_pilot(tmp_path, truncated=True)
    record = build_pilot_record(pilot, "RP01", binary_sha=SHA)
    assert record["ObservedTerminal"] == "HANG"
    assert record["FaultCausality"] == "PROVEN"
    assert record["StructuralChainCompleteness"] == "COMPLETE"
    assert record["RecordIntegrity"] == "TRUNCATED"
    assert record["TraceCompleteness"] == "INCOMPLETE"
    assert "TRACE_INCOMPLETE" in record["MissingCodes"]
    assert record["FinalClassification"] == "UNRESOLVED"
    assert record["ObservedTerminal"] != "MASKED"


def test_bridged_external_timeout_records_timeout_never_masked(tmp_path):
    """The externally cut shape: the summary is written terminal HANG with
    observed TIMEOUT + reason RP01_EXTERNAL_TIMEOUT; the closure record
    carries ObservedTerminal=TIMEOUT and never MASKED."""
    pilot = _write_pilot(tmp_path, observed="TIMEOUT", truncated=True)
    record = build_pilot_record(pilot, "RP01", binary_sha=SHA)
    assert record["ObservedTerminal"] == "TIMEOUT"
    assert record["TerminalReason"] == "RP01_EXTERNAL_TIMEOUT"
    assert record["FaultCausality"] == "PROVEN"
    assert record["ObservedTerminal"] != "MASKED"
