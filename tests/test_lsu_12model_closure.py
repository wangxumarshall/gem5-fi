"""Tests for tools/lsu_12model_closure.py (LSU v3.2.12 Task 3).

The synthetic pilots built under ``tmp_path`` mirror the real trace contract
(record_type event/propagation_edge/summary JSONL lines, semicolon ``detail``
strings, identity fields as JSON strings, two-line oracle.log, manifest with
the recorded binary SHA256) — the same conventions as
tests/fixtures/audit/linked_lq04, so no historical 196 MB trace is needed.

The six mandatory tests pin the plan's Review Focus items:

- zero-injection / dormant pilots never grade a complete verdict (RF2);
- a time-adjacent event with a different ptag and dyn_inst_seq creates no
  causal edge (RF3);
- a HANG hard terminal beats a passing oracle (RF4);
- two binary SHAs split into two rows, never a merged verdict (RF1);
- the missing-evidence matrix has no blank cell and every missing stage has a
  root cause and an integer run count;
- the feature dataset keeps event_ordinal monotonic per pilot.

The three exception-E1 tests pin standard §6 clause 3b / §10 (frozen
amendment 2026-11-10): the runtime-proven LQ04 senderState masking chain
grades COMPLETE_CAUSAL_CHAIN/MASKED with the mechanism recorded; without the
runtime association it stays LIFECYCLE_ONLY; and the rule is model-scoped.

The exception-E2/E3/E4 tests pin standard §6 clause 3c / §11 (frozen
amendment 2026-11-10): the runtime-proven SQ-family model-record chains
(SQ01 sq01_chain / SQ03 sq03_effect / SP05 sp05_stage on the fault's own
chain) grade a complete verdict through the single-context rule —
VERIFIED_SINGLE_CONTEXT per pilot, model-level COMPLETE_CAUSAL_CHAIN with
two or more distinct frozen contexts — with the terminal and ChainMechanism
named, even though FaultEffectPropagationCoverage stays LIFECYCLE_ONLY.
Every guard of each §11.3 conjunction is pinned: removing any single
condition (a diverged flag, a hop hash, a visibility tick ordering, a skip
flag, a reload binding, the platform writeback-consumer edge, the §6
invariant set, the model-rule record itself) must drop the record back to
the generic rules; a non-SQ model carrying identical evidence never
upgrades; and SP05's honestly-null store_data_fnv never blocks the upgrade
that rests on write_skipped + the bound stale reload.

The four missing-matrix closure tests pin the v3.2.12 Task 6 semantics: every
``ORACLE_FILE_MISSING`` row closes against the frozen context's real
raw-oracle supply — a same-seed ``SUPP-<MODEL>-<Rxx>`` run remediates it
(``RequiredRunCount=0`` with the SUPP ``oracle.log`` named), a same-context
vintage or the pilot's own ``stdout.log`` checksum supplies it in-repo, and
with no causally attributable consumer it is decision-moot (no oracle outcome
can adjudicate the verdict); a ``SUPP-`` dir without any recorded model id is
inferred from its frozen name; and a model with no pilots carries its
missing pilot set as an explicit row.
"""
import csv
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from lsu_12model_closure import (  # noqa: E402
    CLOSURE_MATRIX_COLUMNS,
    FEATURE_DATASET_COLUMNS,
    FROZEN_PRIOR_AUDIT,
    MISSING_MATRIX_COLUMNS,
    build_frozen_records,
    build_pilot_record,
    final_classification,
    main,
    write_closure_matrix,
    write_feature_dataset,
    write_missing_matrix,
)

SHA_A = "f3c2a4423aab81ca565c7adcfb840a7b8f9cdb9f2a6b6b5ecc3d0e148af20694"
SHA_B = "cc33" * 16
WORK_SHA = "fa25f785a4822eb578ae8da2d26c400d7450f40d975b2d7da84de900b48d97ba"
HASH = "c6d4496e17859d5"
BAD_HASH = "0bad0bad0bad0bad"


def _event(eid, etype, tick, seq, ptag, detail, *, inj=None, act=None,
           commit_status=None, new_value=None, source=None, cseq=None):
    rec = {
        "record_type": "event", "trace_version": "v3.1",
        "event_id": str(eid), "event_type": etype, "timestamp": str(tick),
        "dyn_inst_seq": None if seq is None else str(seq),
        "commit_seq": cseq,
        "source_event_id": source, "ptag": str(ptag),
        "detail": detail,
    }
    if inj is not None:
        rec["injection_status"] = inj
    if act is not None:
        rec["activation_status"] = act
    if commit_status is not None:
        rec["commit_status"] = commit_status
    if new_value is not None:
        rec["new_value"] = new_value
    return rec


def _edge(pid, src, dst, kind):
    return {"record_type": "propagation_edge", "trace_version": "v3.1",
            "propagation_edge_id": str(pid), "source_event_id": str(src),
            "destination_event_id": str(dst), "edge_kind": kind,
            "value_hash": None, "source_value_hash": None,
            "destination_value_hash": None}


def _summary(run_id, terminal, declared="COMPLETE", activation="TRIGGERED",
             run_status="COMPLETED", reason=None):
    rec = {"record_type": "summary", "trace_version": "v3.1",
           "run_id": run_id, "sub_task_id": f"{run_id}-S01",
           "fault_id": f"{run_id[:5]}-CFG01", "fault_model_id": "LQ04",
           "run_status": run_status, "fault_activation_status": activation,
           "terminal_state": terminal, "observed_terminal": terminal,
           "trace_completeness": declared,
           "counts": {"events": 5, "edges": 3, "injections": 1,
                      "activations": 3}}
    if reason:
        rec["terminal_state_reason"] = reason
    return rec


def write_pilot(directory, *, model="LQ04", ordinal=1, binary_sha=SHA_A,
                oracle=("b097eb83f71545cb", "b097eb83f71545cb"),
                injection=True, activation="TRIGGERED", terminal="MASKED",
                response=True, writeback=True, consumer=True, commit=True,
                replay=False, decoy_consumer=False, declared="COMPLETE",
                divergent=False, truncated=False, seed=1842987246,
                run_status="COMPLETED", sender_state=False, family=None,
                store_side=False, sq_rule=None, addr_stages=None,
                a01_ea=None, a01_consumed_hash=None, a01_discarded=False,
                a03_activation=None, a03_stream=None, simulator_abort=None,
                watchdog=False, squash_record=False):
    """Write one synthetic pilot dir; returns its Path.

    ``decoy_consumer`` adds a LATER consumer_commit with a different ptag and
    dyn_inst_seq (the time-adjacency bait). ``divergent`` flips the writeback
    and consumer into a verified corrupted delivery with an oracle FAIL.
    ``sender_state`` records the LQ04 runtime senderState binding evidence
    (``association=sender_state`` on the memory_response and the
    register_writeback, exactly as the real pilots_v3_2_10 traces record it).
    ``store_side`` adds the store's own writeback/cache-write events (the
    SQ01/SQ03 structural stages). ``sq_rule`` emits the model's rule record
    on the fault's own chain (sq01_chain / sq03_effect / sp05_stage, exactly
    as the real pilots_v3_2_12 eligible-ordinal traces record it) with the
    given detail fields — the standard §11 model-record chain evidence.

    Standard §12 (exceptions E5/E6/E7) evidence knobs, mirroring the real
    pilots_v3_2_12 rerun traces: ``addr_stages`` emits the A01/A03 address
    stages (address_formed + memory_request on the fault's own chain; on by
    default for A01/A03); ``a01_ea`` emits the a01_ea wrong-EA record
    (overridable detail fields); ``a01_consumed_hash`` the a01_consumed
    runtime consumer record; ``a01_discarded`` the a01_ea_discarded record
    (applied_to_request=0); ``a03_activation`` the run-level F5 activation
    record (no chain identity); ``a03_stream`` the on-chain F5 stream record;
    ``simulator_abort`` the run-level panic node (page_table_fault_addr /
    last_injection_dyn_seq); ``watchdog`` writes the injector sidecar line
    ``CHAOS_RP01_WATCHDOG=EXPIRED fired=1 injected=1`` (overridable kv).
    """
    directory = Path(directory)
    directory.mkdir(parents=True)
    suffix = directory.name.split("-")[-1]
    run_id = f"{model}-F0-W2"
    sample = f"{model}-F0-W2-S01-{suffix}"
    family = family or model.lower()

    lines = []
    lines.append(_event(1, "lq_lifecycle", 78540, 2, 0,
                        "queue=LQ;action=alloc;index=9;generation=9"))
    if injection:
        lines.append(_event(3, "injection", 80080, 3, 1,
                            f"site=executeLoad_post;family={family};"
                            "valid_before=1;valid_after=0;lq_idx=1;lq_gen=1;"
                            "pc=400338", inj="INJECTED", act=activation,
                            new_value="0x41ffe8"))
    want_addr = (addr_stages if addr_stages is not None
                 else model in ("A01", "A03"))
    if want_addr and injection:
        lines.append(_event(4, "address_formed", 90000, 3, 1,
                            f"family={family};ea=7ffffefda0;pc=400ad0"))
        lines.append(_event(7, "memory_request", 95000, 3, 1,
                            f"family={family};va=7ffffefda0;size=8;"
                            "request_id=1"))
    if a01_ea is not None:
        fields = {"fault_id": "1", "dyn_inst_seq": "3", "pc": "400ad0",
                  "golden_ea": "7ffffefda8", "actual_ea": "7ffffefda0",
                  "xor_delta": "8", "bit": "3", "access_size": "8",
                  "affected": "1", "request_va": "7ffffefda0",
                  "fault_va": "NOT_APPLICABLE"}
        fields.update(a01_ea)
        lines.append(_event(20, "a01_ea", 100000, 3, 1,
                            ";".join(f"{k}={v}" for k, v in fields.items())))
    if a01_consumed_hash is not None:
        lines.append(_event(21, "a01_consumed", 200000, 3, 1,
                            "dyn_inst_seq=3;consumer_seq=8;"
                            f"consumer_kind=register_source;"
                            f"input_hash={a01_consumed_hash}"))
    if a01_discarded:
        fields = {"fault_id": "1", "dyn_inst_seq": "3", "pc": "400ad0",
                  "golden_ea": "7ffffefda8", "actual_ea": "7ffffefda0",
                  "applied_to_request": "0",
                  "discard_reason": "saved_request_reuse"}
        if isinstance(a01_discarded, dict):
            fields.update(a01_discarded)
        lines.append(_event(22, "a01_ea_discarded", 100000, 3, 1,
                            ";".join(f"{k}={v}" for k, v in fields.items())))
    if a03_activation is not None:
        fields = {"tick": "80080", "bit": "3", "mode": "a03_bit3_stuck0_load"}
        fields.update(a03_activation)
        # run-level: no chain identity (the real a03_activation carries none)
        lines.append(_event(2, "a03_activation", 80080, None, 0,
                            ";".join(f"{k}={v}" for k, v in fields.items())))
    if a03_stream is not None:
        fields = {"event_ordinal": str(ordinal), "dyn_inst_seq": "3",
                  "pc": "0", "eligible": "1", "affected": "1",
                  "golden_ea": "ffffffffffb73c58",
                  "actual_ea": "ffffffffffb73c50", "bit": "3",
                  "reason": "STUCK_APPLIED"}
        fields.update(a03_stream)
        lines.append(_event(23, "a03_stream", 110000, 3, 1,
                            ";".join(f"{k}={v}" for k, v in fields.items())))
    if simulator_abort is not None:
        fields = {"gzip_truncation_observed": "1",
                  "page_table_fault_addr": "0xffffffffffb73c50",
                  "last_injection_dyn_seq": "3", "address_match": "True"}
        fields.update(simulator_abort)
        # run-level: no chain identity (the real simulator_abort carries none)
        lines.append(_event(24, "simulator_abort", 120000, None, 0,
                            ";".join(f"{k}={v}" for k, v in fields.items())))
    if store_side:
        lines.append(_event(5, "store_writeback", 90000, 3, 1,
                            f"family={family};sq_idx=7;gen=1;"
                            f"data_fnv={HASH}"))
        lines.append(_event(6, "store_mem_write", 91000, 3, 1,
                            f"site=BaseCache::updateBlockData;"
                            f"family={family};blk_addr=0x1fe0;"
                            f"packet_data_fnv={HASH}"))
    if response:
        binding = ("association=sender_state;entry_valid_at_response=0;"
                   "entry_request_at_response=0;data_unchanged=1;"
                   if sender_state else "")
        lines.append(_event(8, "memory_response", 135520, 3, 1,
                            f"family={family};size=8;{binding}"
                            f"data_fnv={HASH};request_id=1;pa=1fe8"))
    if writeback:
        corrupt = "1" if divergent else "0"
        binding = ("association=sender_state;data_unchanged=1;"
                   if sender_state else "")
        lines.append(_event(9, "register_writeback", 135520, 3, 1,
                            f"family={family};{binding}"
                            f"data_corruption={corrupt};"
                            f"phys_reg=44;arch_reg=2;"
                            f"writeback_value_fnv={HASH};payload_fnv={HASH};"
                            f"value_matches_payload={'0' if divergent else '1'};"
                            f"source_value_hash={HASH}",
                            source=8, new_value="102030405060708"))
    if consumer:
        matches = "0" if divergent else "1"
        lines.append(_event(18, "consumer_commit", 203280, 8, 1,
                            f"pc=40034c;source_event_id=9;"
                            f"consumer_input_fnv={BAD_HASH if divergent else HASH};"
                            f"consumer_input_matches_source={matches}",
                            source=9, commit_status="COMMITTED", cseq="8"))
    if commit:
        lines.append(_event(10, "commit", 136290, 3, 0,
                            "trigger=fault_instruction_commit;pc=400338",
                            commit_status="COMMITTED", cseq="3"))
    if replay:
        lines.append(_event(11, "replay", 140000, 3, 0,
                            "replay_generation=1;execution_attempt_id=2;"
                            "partial_address_stall=1"))
    if squash_record:
        # the skipped load discarded by an older, unrelated LSQ squash,
        # exactly as the real RP01-R02/R03 traces record it: the squash node
        # on the fault's own dyn_inst_seq with an unlinked trigger
        lines.append(_event(12, "squash", 140500, 3, 0,
                            "record=squash_reason;dyn_inst_seq=3;"
                            "reason=lsq_squash;triggering_seq=0;"
                            "squash_cause=unrelated;fault_caused=0"))
    if decoy_consumer:
        # later tick, different ptag AND different dyn_inst_seq: adjacent, but
        # never on the fault's chain (identity rules of the standard)
        lines.append(_event(99, "consumer_commit", 300000, 99, 9,
                            f"pc=40034c;source_event_id=9;"
                            f"consumer_input_fnv={HASH};"
                            "consumer_input_matches_source=1",
                            source=9, commit_status="COMMITTED", cseq="99"))
    if sq_rule is not None:
        # the model's rule record on the fault's own chain (ptag=1, the
        # faulting store's own dyn_inst_seq), exactly as the real
        # pilots_v3_2_12 eligible-ordinal traces emit it
        kind = {"SQ01": "sq01_chain", "SQ03": "sq03_effect",
                "SP05": "sp05_stage"}.get(model, "sq01_chain")
        detail = ";".join(f"{key}={value}" for key, value in sq_rule.items())
        lines.append(_event(30, kind, 210000, 3, 1, detail))

    if injection:
        lines.append(_edge(1, 3, 8, "resp"))
        if writeback:
            lines.append(_edge(2, 8, 9, "taint_reg"))
        if consumer:
            lines.append(_edge(3, 9, 18, "taint_reg"))
    if injection:
        reason = None
        if terminal == "MASKED":
            reason = "TARGET_COMMITTED_DATA_VALUE_PRESENT"
        elif terminal == "SDC":
            reason = "ORACLE_FAIL"
        lines.append(_summary(run_id, terminal, declared=declared,
                              activation=activation, run_status=run_status,
                              reason=reason))
    else:
        lines.append(_summary(run_id, terminal, declared=declared,
                              activation="NOT_TRIGGERED",
                              run_status=run_status))

    trace = "\n".join(json.dumps(r) for r in lines) + "\n"
    (directory / "trace_v31.jsonl").write_text(trace, encoding="utf-8")

    oracle_pass = None if oracle is None else (oracle[0] == oracle[1])
    meta = {
        "pilot_id": sample, "model": model, "seed": seed,
        "excel_identity": {"run_id": run_id, "sub_task_id": f"{run_id}-S01",
                           "sample_run_id": sample, "seed": seed,
                           "event_ordinal": ordinal,
                           "event_ordinal_used": ordinal},
        "exit_code": 0, "injection_count": 1 if injection else 0,
        "oracle_expected": f"checksum=0x{oracle[0]}" if oracle else None,
        "oracle_pass": oracle_pass,
        "trace": {"validator_errors": [], "truncated": truncated},
        "classification": {
            "run_status": run_status,
            "fault_activation_status": activation,
            "observed_terminal": terminal, "terminal_state": terminal,
            "trace_completeness": declared,
            "oracle_outcome": ("PASS" if oracle_pass else "FAIL")
                              if oracle_pass is not None else "NOT_APPLICABLE",
        },
    }
    (directory / "pilot_meta.json").write_text(json.dumps(meta, indent=2),
                                               encoding="utf-8")
    manifest = {
        "schema_version": "lsu-run-manifest-v3.2", "sample_run_id": sample,
        "run_id": run_id, "sub_task_id": f"{run_id}-S01",
        "model_id": model, "seed": seed,
        "fault": {"location": "LQEntry lifetime", "target_field": "_valid",
                  "event_ordinal": ordinal},
        "workload": {"sha256": WORK_SHA, "oracle_expected":
                     f"checksum=0x{oracle[0]}" if oracle else None},
        "gem5": {"binary": "/gem5.opt", "binary_sha256": binary_sha},
    }
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2),
                                             encoding="utf-8")
    if oracle is not None:
        verdict = "ORACLE_PASS" if oracle_pass else "ORACLE_FAIL"
        (directory / "oracle.log").write_text(
            f"expected={oracle[0]} got={oracle[1]}\n{verdict}\n",
            encoding="utf-8")
    if watchdog:
        kv = {"fired": "1", "injected": "1", "eligible": "1",
              "tick": "7700000000"}
        if isinstance(watchdog, dict):
            kv.update(watchdog)
        (directory / "lsq_fwd_injections.log").write_text(
            "CHAOS_RP01_WATCHDOG=EXPIRED "
            + " ".join(f"{key}={value}" for key, value in kv.items()) + "\n",
            encoding="utf-8")
    return directory


# ---------------------------------------------------------------------------
# RF2: zero-injection and dormant pilots never grade a complete verdict
# ---------------------------------------------------------------------------

def test_zero_injection_is_never_complete(tmp_path):
    control = write_pilot(tmp_path / "LQ04-CONTROL-R01", injection=False,
                          terminal=None)
    record = build_pilot_record(control, "LQ04")
    assert record["InjectionVerified"] == "no"
    assert record["ObservedTerminal"] == "NO_INJECTION"
    assert record["FaultEffectPropagationCoverage"] == "NOT_APPLICABLE"
    assert record["FinalClassification"] == "UNRESOLVED"
    assert record["FinalClassification"] not in (
        "COMPLETE_CAUSAL_CHAIN", "VERIFIED_SINGLE_CONTEXT")

    # a dormant injection (present but never triggered) caps at PARTIAL
    dormant = write_pilot(tmp_path / "LQ04-R02", activation="DORMANT")
    dormant_record = build_pilot_record(dormant, "LQ04")
    assert dormant_record["ActivationVerified"] == "no"
    assert dormant_record["FinalClassification"] == "PARTIAL"
    assert dormant_record["FinalClassification"] not in (
        "COMPLETE_CAUSAL_CHAIN", "VERIFIED_SINGLE_CONTEXT")

    # the writer rejects a complete verdict over an unverified injection
    poison = dict(dormant_record)
    poison["FinalClassification"] = "COMPLETE_CAUSAL_CHAIN"
    with pytest.raises(ValueError):
        write_closure_matrix([poison], tmp_path / "poison.csv")


# ---------------------------------------------------------------------------
# RF3: time adjacency is not causality
# ---------------------------------------------------------------------------

def test_time_adjacent_off_chain_event_is_not_an_edge(tmp_path):
    pilot = write_pilot(tmp_path / "LQ04-R01", consumer=False,
                        decoy_consumer=True)
    record = build_pilot_record(pilot, "LQ04")

    # the decoy (ptag=9, dyn_inst_seq=99, later tick) is excluded from the
    # chain: only injection, response, writeback and commit share an identity
    assert record["ChainEventCount"] == 4
    assert "consumer_commit" not in record["ChainKinds"]
    assert record["Stages"]["consumer_verified"] == "missing"
    assert "NO_CONSUMER_EDGE" in record["MissingCodes"]
    assert record["ConsumerInputFnv"] == "NOT_APPLICABLE"
    assert record["VerifiedChainCount"] == 0
    assert record["FinalClassification"] not in (
        "COMPLETE_CAUSAL_CHAIN", "VERIFIED_SINGLE_CONTEXT")
    # the decoy event id never appears as a fragment of the fault's path
    fragment_ids = {str(f["event_id"]) for f in record["PathFragments"]}
    assert "99" not in fragment_ids


# ---------------------------------------------------------------------------
# RF4: a HANG hard terminal beats a passing oracle
# ---------------------------------------------------------------------------

def test_hang_beats_passing_oracle(tmp_path):
    pilot = write_pilot(tmp_path / "LQ04-R01", terminal="HANG", replay=True,
                        run_status="HANG")
    record = build_pilot_record(pilot, "LQ04")
    assert record["ObservedTerminal"] == "HANG"
    assert record["ApplicationOracle"] == "PASS"
    assert record["FinalClassification"] not in ("MASKED", "UNRESOLVED")
    # the identity-linked replay record proves the trigger (rule 2); one
    # complete chain in this pilot -> VERIFIED_SINGLE_CONTEXT, never upgraded
    assert record["FaultCausality"] == "PROVEN"
    assert record["FinalClassification"] == "VERIFIED_SINGLE_CONTEXT"

    # without the identity-linked record the hang is not proven fault-caused:
    # an unproven hard terminal stays PARTIAL, never MASKED
    unproven = write_pilot(tmp_path / "LQ04-R02", terminal="HANG",
                           run_status="HANG")
    unproven_record = build_pilot_record(unproven, "LQ04")
    assert unproven_record["ObservedTerminal"] == "HANG"
    assert unproven_record["FaultCausality"] in ("PARTIAL", "UNPROVEN")
    assert unproven_record["FinalClassification"] == "PARTIAL"


# ---------------------------------------------------------------------------
# RF1: two binary SHAs -> two rows, never a merged verdict
# ---------------------------------------------------------------------------

def test_mixed_binary_splits_verdicts(tmp_path):
    binary_a = write_pilot(tmp_path / "LQ04-R01", binary_sha=SHA_A)
    binary_b = write_pilot(tmp_path / "LQ04-R02", binary_sha=SHA_B,
                           divergent=True,
                           oracle=("b097eb83f71545cb", "deadbeefdeadbeef"))
    records_json = tmp_path / "records.json"
    rc = main(["record", "--model", "LQ04",
               "--pilot-dir", str(binary_a),
               "--pilot-dir", str(binary_b),
               "--json", str(records_json)])
    assert rc == 0
    records = json.loads(records_json.read_text())["records"]
    assert len(records) == 2
    by_pilot = {r["PilotID"]: r for r in records}
    assert by_pilot["LQ04-R01"]["FinalClassification"] == "LIFECYCLE_ONLY"
    assert by_pilot["LQ04-R02"]["FinalClassification"] == (
        "VERIFIED_SINGLE_CONTEXT")

    out = tmp_path / "closure.csv"
    assert main(["matrix", "--records", str(records_json),
                 "--out", str(out)]) == 0
    with open(out, newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    assert rows[0] == CLOSURE_MATRIX_COLUMNS
    assert len(rows[0]) == 24
    data = rows[1:]
    # two SHAs -> exactly two rows, one per binary, never a merged verdict
    assert len(data) == 2
    model_ids = {row[0] for row in data}
    assert model_ids == {f"LQ04@{SHA_A[:8]}", f"LQ04@{SHA_B[:8]}"}
    verdicts = {row[0]: row[CLOSURE_MATRIX_COLUMNS.index(
        "FinalClassification")] for row in data}
    assert verdicts[f"LQ04@{SHA_A[:8]}"] == "LIFECYCLE_ONLY"
    assert verdicts[f"LQ04@{SHA_B[:8]}"] == "VERIFIED_SINGLE_CONTEXT"


# ---------------------------------------------------------------------------
# missing-evidence matrix: no blank cell, root cause + run count everywhere
# ---------------------------------------------------------------------------

def test_missing_matrix_has_no_blank_cell(tmp_path):
    root = tmp_path / "pilots_root"
    control = write_pilot(root / "LQ04-CONTROL-R01", injection=False,
                          terminal=None)
    gap = write_pilot(root / "LQ04-R02", response=False, writeback=False,
                      consumer=False, commit=False, oracle=None)
    out = tmp_path / "missing.csv"
    assert main(["missing", "--pilots-root", str(root),
                 "--out", str(out)]) == 0

    with open(out, newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    assert rows[0] == MISSING_MATRIX_COLUMNS
    data = rows[1:]
    assert len(data) >= 8  # every missing code of both pilots has a row
    seen_codes = set()
    for row in data:
        cells = dict(zip(MISSING_MATRIX_COLUMNS, row))
        for column, cell in cells.items():
            assert cell.strip() != "", (column, row)
            assert cell.strip().upper() != "PASS", (column, row)
        assert cells["MissingStage"].strip() not in ("", "NULL")
        assert cells["RootCause"].strip() not in ("", "NULL",
                                                  "NOT_APPLICABLE")
        assert cells["RequiredRunCount"].isdigit()
        assert int(cells["RequiredRunCount"]) >= 0
        seen_codes.add((cells["PilotID"], cells["MissingStage"],
                        cells["MissingEvent"]))
    stages = {pilot: {stage for pilot2, stage, _ in seen_codes
                      if pilot2 == pilot} for pilot, _, _ in seen_codes}
    # the zero-injection control's absence is a named INJECTION row
    assert ("LQ04-CONTROL-R01", "INJECTION", "injection") in seen_codes
    assert "LQ04-R02" in stages
    # a determinism control needs no run to close its (by-design) absence;
    # its other honest absences (e.g. an unresolvable terminal) still name
    # what a real fault pilot would need
    control_rows = [dict(zip(MISSING_MATRIX_COLUMNS, r)) for r in data
                    if dict(zip(MISSING_MATRIX_COLUMNS, r))["PilotID"]
                    == "LQ04-CONTROL-R01"]
    assert control_rows
    control_injection = [r for r in control_rows
                         if r["MissingStage"] == "INJECTION"]
    assert control_injection
    assert all(r["RequiredRunCount"] == "0" for r in control_injection)

    # writer rejects an empty cell and a bare PASS anywhere outside the
    # mandated ApplicationOracle enum (an absent-but-recorded value is the
    # literal NULL, never a blank — a blank cell is still a defect)
    gap_record = build_pilot_record(gap, "LQ04")
    gap_record["ModelID"] = ""
    with pytest.raises(ValueError):
        write_missing_matrix([gap_record], tmp_path / "bad1.csv")
    bad_pass = build_pilot_record(control, "LQ04")
    bad_pass["ChainEventCount"] = "PASS"
    with pytest.raises(ValueError):
        write_feature_dataset([bad_pass], tmp_path / "bad2.csv")


def _missing_rows(out):
    with open(out, newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    assert rows[0] == MISSING_MATRIX_COLUMNS
    return [dict(zip(MISSING_MATRIX_COLUMNS, row)) for row in rows[1:]]


# ---------------------------------------------------------------------------
# ORACLE_FILE_MISSING rows close against the context's real raw-oracle supply
# (v3.2.12 Task 5: SUPP-<MODEL>-<Rxx> raw-oracle runs under the original seed)
# ---------------------------------------------------------------------------

def test_oracle_row_remediated_by_same_seed_supp_run(tmp_path):
    root = tmp_path / "pilots_root"
    # the original pilot keeps only a meta-recorded oracle (no oracle.log)
    write_pilot(root / "LQ04-R04", oracle=None, seed=4711)
    # the Task 5 SUPP re-run of the SAME frozen context carries the raw
    # oracle.log and remediates the original's ORACLE_FILE_MISSING row
    write_pilot(root / "SUPP-LQ04-R04", oracle=(HASH, HASH), seed=4711)
    # a different-seed context gets no supply from that SUPP run: its row
    # stays open with RequiredRunCount=1
    write_pilot(root / "LQ04-R05", oracle=None, seed=9999)
    out = tmp_path / "missing.csv"
    assert main(["missing", "--pilots-root", str(root),
                 "--out", str(out)]) == 0
    oracle_rows = [r for r in _missing_rows(out)
                   if r["MissingStage"] == "ORACLE"]
    by_pilot: dict = {}
    for row in oracle_rows:
        by_pilot.setdefault(row["PilotID"], []).append(row)
    assert set(by_pilot) == {"LQ04-R04", "LQ04-R05"}
    remediated = by_pilot["LQ04-R04"]
    assert len(remediated) == 1
    assert remediated[0]["RequiredRunCount"] == "0"
    assert "SUPP-LQ04-R04/oracle.log" in remediated[0]["ExpectedEvidence"]
    assert "remediated by the v3.2.12 SUPP raw-oracle run" \
        in remediated[0]["RootCause"]
    # the SUPP run itself supplies nothing else and adds no open row
    assert not any(r["PilotID"] == "SUPP-LQ04-R04" for r in oracle_rows)
    open_row = by_pilot["LQ04-R05"]
    assert len(open_row) == 1
    assert open_row[0]["RequiredRunCount"] == "1"
    assert open_row[0]["RootCause"].startswith(
        "the raw oracle artifact is absent")


def test_oracle_row_supplied_by_vintage_stdout_or_moot(tmp_path):
    first_root = tmp_path / "pilots_v3_2_6"
    second_root = tmp_path / "pilots_v3_2_7"
    # (2) another original vintage of the same (model, seed) context whose
    # raw oracle.log parsed supplies the row in-repo
    write_pilot(first_root / "MD04-R01", model="MD04", oracle=None,
                seed=777)
    write_pilot(second_root / "MD04-R01", model="MD04",
                oracle=(HASH, HASH), seed=777)
    # (3) the pilot's own stdout.log raw checksum line supplies its row
    stdout_pilot = write_pilot(first_root / "SQ01-R02", model="SQ01",
                               oracle=None, consumer=False, seed=888)
    (stdout_pilot / "stdout.log").write_text(
        "info: workload done\nchecksum=0x99c106541150be0e\n",
        encoding="utf-8")
    # (4) no supply anywhere + no causally attributable consumer -> the
    # oracle outcome cannot adjudicate the verdict: decision-moot, runs=0
    write_pilot(first_root / "DA04-R01", model="DA04", oracle=None,
                consumer=False, seed=1234)
    out = tmp_path / "missing.csv"
    assert main(["missing", "--pilots-root", str(first_root),
                 "--pilots-root", str(second_root),
                 "--out", str(out)]) == 0
    oracle_rows = [r for r in _missing_rows(out)
                   if r["MissingStage"] == "ORACLE"]
    by_pilot = {r["PilotID"]: r for r in oracle_rows}
    assert set(by_pilot) == {"MD04-R01", "SQ01-R02", "DA04-R01"}
    vintage = by_pilot["MD04-R01"]
    assert vintage["RequiredRunCount"] == "0"
    assert "supplied in-repo by the same-context original vintage" \
        in vintage["RootCause"]
    # the supplier row names the OTHER vintage's dir, never its own
    assert f"pilots_v3_2_7{os.sep}MD04-R01" in vintage["ExpectedEvidence"]
    stdout_row = by_pilot["SQ01-R02"]
    assert stdout_row["RequiredRunCount"] == "0"
    assert "SQ01-R02/stdout.log" in stdout_row["ExpectedEvidence"]
    moot = by_pilot["DA04-R01"]
    assert moot["RequiredRunCount"] == "0"
    assert moot["RootCause"].startswith("decision-moot")
    assert "NO_CONSUMER_EDGE" in moot["RootCause"]
    # a determinism control never supplies another pilot's raw oracle
    # (its golden-checksum artifact is not the fault run's)
    control_root = tmp_path / "pilots_controls"
    write_pilot(control_root / "LQ04-CONTROL-R01", injection=False,
                terminal=None, seed=4711)
    gap = write_pilot(control_root / "LQ04-R04", oracle=None, seed=4711)
    assert main(["missing", "--pilots-root", str(control_root),
                 "--out", str(out)]) == 0
    oracle_rows = [r for r in _missing_rows(out)
                   if r["MissingStage"] == "ORACLE"]
    gap_row = [r for r in oracle_rows if r["PilotID"] == "LQ04-R04"]
    assert len(gap_row) == 1
    # the consumer-verified gap pilot has no supply: its row stays open
    assert gap_row[0]["RequiredRunCount"] == "1"
    assert not any("CONTROL" in r["ExpectedEvidence"] for r in oracle_rows)


def test_supp_dir_without_recorded_model_is_inferred_from_its_name(tmp_path):
    root = tmp_path / "pilots_root"
    supp = write_pilot(root / "SUPP-SP05-R01", model="SP05", consumer=False,
                       oracle=None)
    # strip every recorded model id: the frozen SUPP-<MODEL>-<Rxx> naming
    # (schema section 3) is the only remaining inference source
    manifest = json.loads((supp / "manifest.json").read_text())
    manifest.pop("model_id", None)
    (supp / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    meta = json.loads((supp / "pilot_meta.json").read_text())
    meta.pop("model", None)
    (supp / "pilot_meta.json").write_text(json.dumps(meta), encoding="utf-8")
    out = tmp_path / "missing.csv"
    assert main(["missing", "--pilots-root", str(root),
                 "--out", str(out)]) == 0
    rows = _missing_rows(out)
    supp_rows = [r for r in rows if r["PilotID"] == "SUPP-SP05-R01"]
    # recognized from the name, audited, and contributing its own missing
    # items -- never silently skipped as "no 12-model id"
    assert supp_rows
    assert all(r["ModelID"] == "SP05" for r in supp_rows)
    # and SP05 is no longer a model without pilots: no PILOT-set row for it
    assert not any(r["ModelID"] == "SP05" and r["PilotID"] == "NONE"
                   for r in rows)


def test_missing_matrix_names_models_without_pilots(tmp_path):
    root = tmp_path / "pilots_root"
    write_pilot(root / "LQ04-R01", oracle=None)
    out = tmp_path / "missing.csv"
    assert main(["missing", "--pilots-root", str(root),
                 "--out", str(out)]) == 0
    rows = _missing_rows(out)
    for model in ("SP05", "RP01"):
        absent = [r for r in rows if r["ModelID"] == model]
        assert len(absent) == 1, model
        assert absent[0]["PilotID"] == "NONE"
        assert absent[0]["MissingStage"] == "PILOT"
        assert absent[0]["RequiredRunCount"].isdigit()
        assert int(absent[0]["RequiredRunCount"]) >= 1
        assert "no pilot directory for this model exists" \
            in absent[0]["RootCause"]
    # a model whose pilots exist never gets the PILOT-set row
    assert not any(r["ModelID"] == "LQ04" and r["PilotID"] == "NONE"
                   for r in rows)


# ---------------------------------------------------------------------------
# feature dataset: event_ordinal monotonic per pilot, explicit absences
# ---------------------------------------------------------------------------

def test_feature_dataset_keeps_event_order(tmp_path):
    first = write_pilot(tmp_path / "LQ04-R01", ordinal=1, consumer=False)
    second = write_pilot(tmp_path / "LQ04-R02", ordinal=2, consumer=False)
    records_json = tmp_path / "records.json"
    assert main(["record", "--model", "LQ04",
                 "--pilot-dir", str(first),
                 "--pilot-dir", str(second),
                 "--json", str(records_json)]) == 0
    out = tmp_path / "features.csv"
    assert main(["features", "--records", str(records_json),
                 "--out", str(out)]) == 0

    with open(out, newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    assert rows[0] == FEATURE_DATASET_COLUMNS
    data = [dict(zip(FEATURE_DATASET_COLUMNS, r)) for r in rows[1:]]

    blocks = {}
    for row in data:
        blocks.setdefault(row["PilotID"], []).append(row)
    assert set(blocks) == {"LQ04-R01", "LQ04-R02"}
    for pilot_id, block in blocks.items():
        ordinals = [row["EventOrdinal"] for row in block]
        # event_ordinal is the frozen per-pilot ordinal: constant (hence
        # monotonic) on every row of the pilot's block
        assert len(set(ordinals)) == 1, pilot_id
        fragments = [int(row["FragmentOrdinal"]) for row in block]
        assert fragments == sorted(fragments)
        assert fragments[0] == 0  # the PILOT row precedes its fragments
        assert len(set(fragments)) == len(fragments)
        for row in block:
            assert row["ModelID"] == "LQ04"
            assert row["PrimaryFaultModel"] == "LQ04"
            assert row["InjectionTick"] == "80080"
            assert row["ObservedTerminal"] == "MASKED"
            # no consumer stage occurred: explicit NOT_APPLICABLE, never a
            # blank and never a silent zero
            assert row["ConsumerInputFnv"] == "NOT_APPLICABLE"
            assert row["ConsumerSourceLinked"] == "NOT_APPLICABLE"
        # fragments appear in canonical chain order: injection first, the
        # writeback before the commit
        stages = [row["FragmentStage"] for row in block[1:]]
        assert stages[0] == "injection"
        assert stages.index("register_writeback") < stages.index("commit")

    # the two pilot blocks appear in record order (ordinal 1 before 2)
    first_pos = min(i for i, row in enumerate(data)
                    if row["PilotID"] == "LQ04-R01")
    second_pos = min(i for i, row in enumerate(data)
                     if row["PilotID"] == "LQ04-R02")
    assert first_pos < second_pos
    assert data[first_pos]["EventOrdinal"] == "1"
    assert data[second_pos]["EventOrdinal"] == "2"


# ---------------------------------------------------------------------------
# per-model corroboration counts distinct frozen contexts, never records
# ---------------------------------------------------------------------------

def test_corroboration_counts_distinct_contexts_not_records(tmp_path):
    """Standard §4 per-model rule: two or more DISTINCT frozen contexts with
    a verified complete chain are required for COMPLETE_CAUSAL_CHAIN.  The
    same pilot supplied twice, and an original plus its SUPP re-run of the
    same frozen context, are ONE context — a SUPP run corroborates the
    oracle, never a second context."""
    # a genuinely complete single-context pilot (divergent delivery with a
    # failing oracle) grades VERIFIED_SINGLE_CONTEXT per pilot
    pilot = write_pilot(tmp_path / "LQ04-R01", divergent=True,
                        oracle=("b097eb83f71545cb", "deadbeefdeadbeef"))
    record = build_pilot_record(pilot, "LQ04")
    assert record["FinalClassification"] == "VERIFIED_SINGLE_CONTEXT"

    def matrix_final(records):
        out = tmp_path / "closure.csv"
        write_closure_matrix(records, out)
        with open(out, newline="", encoding="utf-8") as fh:
            rows = list(csv.reader(fh))
        data = [dict(zip(CLOSURE_MATRIX_COLUMNS, r)) for r in rows[1:]]
        assert len(data) == 1  # same model, same binary: exactly one row
        return data[0]["FinalClassification"]

    # (a) the same pilot supplied twice is still one context: no upgrade
    twin = build_pilot_record(pilot, "LQ04")
    assert twin["SampleRunID"] == record["SampleRunID"]
    assert matrix_final([record, twin]) == "VERIFIED_SINGLE_CONTEXT"

    # (b) the original plus its SUPP re-run of the same frozen context: the
    # sidecar maps the SUPP back to the original SampleRunID, and the SUPP
    # record is excluded from the corroboration count outright
    supp_dir = write_pilot(tmp_path / "SUPP-LQ04-S01", divergent=True,
                           oracle=("b097eb83f71545cb", "deadbeefdeadbeef"))
    (supp_dir / "supplementary.json").write_text(
        json.dumps({"supplementary_of": record["SampleRunID"]}),
        encoding="utf-8")
    supp = build_pilot_record(supp_dir, "LQ04")
    assert supp["SupplementaryOf"] == record["SampleRunID"]
    # the SUPP is a different run identity mapped back only by the sidecar
    assert supp["SampleRunID"] != record["SampleRunID"]
    assert supp["FinalClassification"] == "VERIFIED_SINGLE_CONTEXT"
    assert matrix_final([record, supp]) == "VERIFIED_SINGLE_CONTEXT"

    # (c) two genuinely distinct frozen contexts still upgrade the model
    other = write_pilot(tmp_path / "LQ04-R02", divergent=True,
                        oracle=("b097eb83f71545cb", "deadbeefdeadbeef"))
    other_record = build_pilot_record(other, "LQ04")
    assert other_record["SampleRunID"] != record["SampleRunID"]
    assert matrix_final([record, other_record]) == "COMPLETE_CAUSAL_CHAIN"


# ---------------------------------------------------------------------------
# the feature writer applies the same hard-invariant rejection as the matrix
# ---------------------------------------------------------------------------

def test_feature_dataset_rejects_poisoned_complete_verdict(tmp_path):
    """Schema §2 hard invariant: FinalClassification complete while
    ActivationVerified=no is a defect.  The feature dataset must reject the
    poisoned row as loudly as the closure matrix does — never emit it
    silently."""
    dormant = write_pilot(tmp_path / "LQ04-R01", activation="DORMANT")
    record = build_pilot_record(dormant, "LQ04")
    assert record["ActivationVerified"] == "no"
    assert record["FinalClassification"] == "PARTIAL"

    poison = dict(record)
    poison["FinalClassification"] = "COMPLETE_CAUSAL_CHAIN"
    with pytest.raises(ValueError):
        write_feature_dataset([poison], tmp_path / "poison_features.csv")
    with pytest.raises(ValueError):
        write_closure_matrix([poison], tmp_path / "poison_matrix.csv")

    # the unpolluted record still writes cleanly through the feature writer
    # (the validation rejects the defect, not the honest PARTIAL verdict)
    write_feature_dataset([record], tmp_path / "clean_features.csv")


# ---------------------------------------------------------------------------
# standard §6 exception E1 (§10): the LQ04 senderState masking rule
# ---------------------------------------------------------------------------

def test_lq04_sender_state_chain_upgrades_to_complete_and_masked(tmp_path):
    """Standard §6 exception E1: an LQ04 record whose chain carries the
    runtime senderState association on the memory_response AND the
    register_writeback, with causality proven over a valid, complete,
    structurally complete record and a hash-equal consumer edge, grades
    COMPLETE_CAUSAL_CHAIN with ObservedTerminal=MASKED and carries the
    mechanism — even though FaultEffectPropagationCoverage stays
    LIFECYCLE_ONLY (the effect itself stayed inside the LQ lifecycle)."""
    pilot = write_pilot(tmp_path / "LQ04-R01", sender_state=True)
    record = build_pilot_record(pilot, "LQ04")
    # the runtime senderState binding evidence is exported on the record
    assert record["MemoryResponseAssociation"] == "sender_state"
    assert record["WritebackAssociation"] == "sender_state"
    assert record["ObservedTerminal"] == "MASKED"
    assert record["FaultCausality"] == "PROVEN"
    # coverage is NOT changed by the exception; it no longer forces the
    # classification down
    assert record["FaultEffectPropagationCoverage"] == "LIFECYCLE_ONLY"
    assert record["FinalClassification"] == "COMPLETE_CAUSAL_CHAIN"
    assert record["MaskingMechanism"] == (
        "RESPONSE_ASSOCIATED_VIA_PACKET_SENDERSTATE")
    # the writeback-vs-consumer hash equality is load-bearing: flipping the
    # consumer hash alone drops the record back to the generic rule 4
    mismatch = dict(record, ConsumerInputFnv="0bad0bad0bad0bad")
    assert final_classification(mismatch) == "LIFECYCLE_ONLY"


def test_lq04_without_sender_state_association_stays_lifecycle(tmp_path):
    """Without the runtime senderState association on the memory_response
    and the register_writeback, exception E1 does not fire (no upgrade on
    inference alone): the record stays LIFECYCLE_ONLY exactly as before and
    honestly carries no masking mechanism."""
    pilot = write_pilot(tmp_path / "LQ04-R01")  # no association details
    record = build_pilot_record(pilot, "LQ04")
    assert record["MemoryResponseAssociation"] is None
    assert record["WritebackAssociation"] is None
    assert record["ObservedTerminal"] == "MASKED"
    assert record["FaultEffectPropagationCoverage"] == "LIFECYCLE_ONLY"
    assert record["FinalClassification"] == "LIFECYCLE_ONLY"
    assert record["FinalClassification"] not in (
        "COMPLETE_CAUSAL_CHAIN", "VERIFIED_SINGLE_CONTEXT")
    assert record["MaskingMechanism"] == "NOT_APPLICABLE"


def test_sender_state_exception_is_model_scoped(tmp_path):
    """Exception E1 upgrades no other model: an identical evidence
    signature (senderState association on both hops, hash-equal consumer)
    under a non-LQ04 model id keeps the generic rules — the record stays
    LIFECYCLE_ONLY and carries no mechanism."""
    pilot = write_pilot(tmp_path / "LP01-R01", model="LP01",
                        sender_state=True)
    record = build_pilot_record(pilot, "LP01")
    assert record["ModelID"] == "LP01"
    assert record["MemoryResponseAssociation"] == "sender_state"
    assert record["WritebackAssociation"] == "sender_state"
    assert record["ObservedTerminal"] == "MASKED"
    assert record["FaultEffectPropagationCoverage"] == "LIFECYCLE_ONLY"
    assert record["FinalClassification"] == "LIFECYCLE_ONLY"
    assert record["FinalClassification"] not in (
        "COMPLETE_CAUSAL_CHAIN", "VERIFIED_SINGLE_CONTEXT")
    assert record["MaskingMechanism"] == "NOT_APPLICABLE"


# ---------------------------------------------------------------------------
# standard §6 clause 3c / §11 — exceptions E2/E3/E4, the SQ-family
# model-record chains (frozen amendment 2026-11-10)
# ---------------------------------------------------------------------------

# the sq01_chain / sq03_effect / sp05_stage rule-record detail fields,
# mirroring the real pilots_v3_2_12/SUPP-{SQ01,SQ03,SP05}-R0xB traces
SQ01_RULE = {
    "record": "sq01_chain", "family": "store_data", "model": "SQ01",
    "store_seq": "3", "sq_idx": "7", "gen": "1",
    "data_before": "0x61", "data_after": "0x69", "data_diverged": "1",
    "mem_write_hash": HASH, "reload_seq": "5",
    "reload_data_hash": HASH, "consumer_seq": "8",
    "consumer_hash": HASH, "chain_verdict": "COMPLETE_CHAIN",
}
SQ03_RULE = {
    "record": "sq03_effect", "family": "sq03_canwb", "model": "SQ03",
    "store_seq": "3", "sq_idx": "7", "gen": "1",
    "canwb_before": "0", "canwb_after": "1", "canwb_state_changed": "1",
    "writeback_tick": "90000", "drain_tick": "95000",
    "commit_tick": "100000", "resource_reuse_tick": "0",
    "reload_seq": "5", "reload_data_hash": HASH,
    "visible_before_commit": "1", "phantom_drain": "0",
    "effect_outcome": "CHAIN_VISIBILITY_MOVED",
    "effect_reason": "DRAIN_BEFORE_COMMIT_WITH_RELOAD_CONSUMER",
}
SP05_RULE = {
    "record": "sp05_stage", "family": "sp05_complete", "model": "SP05",
    "store_seq": "3", "sq_idx": "7", "gen": "1",
    "completion_tick": "91000", "commit_tick": "0",
    "writeback_tick": "91000", "drain_tick": "0", "write_skipped": "1",
    "reload_seq": "5", "reload_data_hash": HASH,
    "store_data_fnv": "null", "data_correct": "null",
    "stage_outcome": "RELOAD_UNVERIFIABLE",
    "masking_mechanism": "NOT_APPLICABLE",
}

_SQ_RULE_KINDS = {"SQ01": "sq01_chain", "SQ03": "sq03_effect",
                  "SP05": "sp05_stage"}


def _write_sq_pilot(tmp_path, model, rule, name="R01", **kwargs):
    """One synthetic SQ-family fault pilot: the store's own structural
    stages (omitted for SP05, whose write was skipped — the honest
    NO_EARLY_ANOMALY_EVENT of the real runs), the reload's delivery edge,
    and the model's rule record on the fault's own chain."""
    defaults = dict(
        store_side=model != "SP05", sq_rule=rule,
        terminal="MASKED" if model == "SQ03" else "SDC",
        oracle=(("b097eb83f71545cb", "b097eb83f71545cb")
                if model == "SQ03"
                else ("b097eb83f71545cb", "deadbeefdeadbeef")),
    )
    defaults.update(kwargs)
    return write_pilot(Path(tmp_path) / f"{model}-{name}", model=model,
                       **defaults)


def _mutated(record, **fields):
    """A deep copy of the record with top-level fields replaced (one guard
    removed at a time; never the tool's own output)."""
    copy = json.loads(json.dumps(record))
    copy.update(fields)
    return copy


def _mutated_rule(record, **fields):
    """A deep copy of the record with model-rule-record fields replaced."""
    copy = json.loads(json.dumps(record))
    copy["ModelRuleRecord"]["fields"].update(fields)
    return copy


_NOT_COMPLETE = ("COMPLETE_CAUSAL_CHAIN", "VERIFIED_SINGLE_CONTEXT")


@pytest.mark.parametrize("model,rule,mechanism,terminal", [
    ("SQ01", SQ01_RULE, "SQ_ENTRY_DATA_CORRUPTION_MEM_RELOAD_CONSUMER",
     "SDC"),
    ("SQ03", SQ03_RULE, "SQ_CANWB_VISIBILITY_MOVED_DRAIN_BEFORE_COMMIT",
     "MASKED"),
    ("SP05", SP05_RULE, "STORE_COMPLETION_SKIPPED_STALE_RELOAD_CONSUMED",
     "SDC"),
])
def test_sq_model_record_chain_upgrades(tmp_path, model, rule, mechanism,
                                        terminal):
    """Standard §6 clause 3c / §11: a record whose model rule record on the
    fault's own chain proves every hop of the §11 conjunction grades a
    complete verdict through the single-context rule — VERIFIED_SINGLE_
    CONTEXT for the pilot's one verified chain — with the terminal and
    ChainMechanism named, while FaultEffectPropagationCoverage honestly
    stays LIFECYCLE_ONLY (the generic value_divergence analysis does not
    bind the model-record hops) and E1's MaskingMechanism stays
    NOT_APPLICABLE."""
    pilot = _write_sq_pilot(tmp_path, model, rule)
    record = build_pilot_record(pilot, model)
    # the model rule record is exported from the fault's own chain
    assert record["ModelRuleRecord"]["event_type"] == _SQ_RULE_KINDS[model]
    assert record["ObservedTerminal"] == terminal
    assert record["FaultCausality"] == "PROVEN"
    assert record["InjectionVerified"] == "yes"
    assert record["ActivationVerified"] == "yes"
    # coverage is NOT changed by the exception; it no longer forces the
    # classification down
    assert record["FaultEffectPropagationCoverage"] == "LIFECYCLE_ONLY"
    assert record["FinalClassification"] == "VERIFIED_SINGLE_CONTEXT"
    assert record["ChainMechanism"] == mechanism
    assert record["MaskingMechanism"] == "NOT_APPLICABLE"
    # the proven model-record chain is one verified complete chain
    assert record["VerifiedChainCount"] == 1


def test_sq01_every_guard_removed_means_no_upgrade(tmp_path):
    """Exception E2 is a conjunction of proven fields: removing any single
    condition — the divergence flag, any hop of the hash triple, the reload
    or consumer binding, the writeback-consumer data edge, the terminal, the
    causality, the §6 invariant set, or the model rule record itself — must
    drop the record back to the generic rules (never a complete verdict)."""
    pilot = _write_sq_pilot(tmp_path, "SQ01", SQ01_RULE)
    record = build_pilot_record(pilot, "SQ01")
    assert record["FinalClassification"] == "VERIFIED_SINGLE_CONTEXT"
    guards = [
        _mutated_rule(record, data_diverged="0"),
        _mutated_rule(record, mem_write_hash=BAD_HASH),
        _mutated_rule(record, reload_data_hash=BAD_HASH),
        _mutated_rule(record, consumer_hash=BAD_HASH),
        _mutated_rule(record, mem_write_hash="null"),
        _mutated_rule(record, reload_data_hash="null"),
        _mutated_rule(record, consumer_hash="0"),
        _mutated_rule(record, reload_seq="null"),
        _mutated_rule(record, consumer_seq="null"),
        _mutated(record, ModelRuleRecord=None),
        _mutated(record, ObservedTerminal="MASKED"),
        _mutated(record, FaultCausality="PARTIAL"),
        _mutated(record, RecordIntegrity="INVALID"),
        _mutated(record, TraceCompleteness="INCOMPLETE"),
        _mutated(record, StructuralChainCompleteness="PARTIAL"),
        _mutated(record, InjectionVerified="no"),
        _mutated(record, ActivationVerified="no"),
        _mutated(record, WritebackValueFnv=BAD_HASH),
        _mutated(record, ConsumerInputFnv="null"),
    ]
    for guard in guards:
        final = final_classification(guard)
        assert final not in _NOT_COMPLETE, guard.get("ModelRuleRecord")
    # the honest fallback is rule 4 (LIFECYCLE_ONLY) for the coverage-shaped
    # guards, never a silent complete verdict
    assert final_classification(guards[0]) == "LIFECYCLE_ONLY"
    assert final_classification(guards[1]) == "LIFECYCLE_ONLY"


def test_sq03_every_guard_removed_means_no_upgrade(tmp_path):
    """Exception E3 is a conjunction of proven fields: removing any single
    condition — the canWB state change, the drain-before-commit ordering
    (including the zero-tick "not observed" and the non-numeric cases), the
    visibility flag, the bound reload with its real hash, the terminal, the
    causality, the §6 invariant set, or the model rule record itself — must
    drop the record back to the generic rules."""
    pilot = _write_sq_pilot(tmp_path, "SQ03", SQ03_RULE)
    record = build_pilot_record(pilot, "SQ03")
    assert record["FinalClassification"] == "VERIFIED_SINGLE_CONTEXT"
    guards = [
        _mutated_rule(record, canwb_state_changed="0"),
        _mutated_rule(record, drain_tick="0"),
        _mutated_rule(record, commit_tick="0"),
        _mutated_rule(record, drain_tick="150000"),  # drain >= commit
        _mutated_rule(record, drain_tick="null"),  # non-numeric tick
        _mutated_rule(record, visible_before_commit="0"),
        _mutated_rule(record, reload_seq="null"),
        _mutated_rule(record, reload_data_hash="null"),
        _mutated_rule(record, reload_data_hash="0"),
        _mutated(record, ModelRuleRecord=None),
        _mutated(record, ObservedTerminal="SDC"),  # E3 never relabels SDC
        _mutated(record, FaultCausality="PARTIAL"),
        _mutated(record, RecordIntegrity="TRUNCATED"),
        _mutated(record, TraceCompleteness="MISSING"),
        _mutated(record, StructuralChainCompleteness="NONE"),
        _mutated(record, InjectionVerified="no"),
        _mutated(record, ActivationVerified="no"),
        _mutated(record, WritebackValueFnv=BAD_HASH),
    ]
    for guard in guards:
        final = final_classification(guard)
        assert final not in _NOT_COMPLETE, guard.get("ModelRuleRecord")
    assert final_classification(guards[0]) == "LIFECYCLE_ONLY"
    assert final_classification(guards[10]) == "LIFECYCLE_ONLY"


def test_sp05_every_guard_removed_means_no_upgrade(tmp_path):
    """Exception E4 is a conjunction of proven fields: removing any single
    condition — the skipped write, the bound reload with its real (stale)
    hash, the terminal, the causality, the §6 invariant set, or the model
    rule record itself — must drop the record back to the generic rules."""
    pilot = _write_sq_pilot(tmp_path, "SP05", SP05_RULE)
    record = build_pilot_record(pilot, "SP05")
    assert record["FinalClassification"] == "VERIFIED_SINGLE_CONTEXT"
    guards = [
        _mutated_rule(record, write_skipped="0"),
        _mutated_rule(record, reload_seq="null"),
        _mutated_rule(record, reload_data_hash="null"),
        _mutated_rule(record, reload_data_hash="0"),
        _mutated(record, ModelRuleRecord=None),
        _mutated(record, ObservedTerminal="MASKED"),
        _mutated(record, FaultCausality="UNPROVEN"),
        _mutated(record, RecordIntegrity="INVALID"),
        _mutated(record, TraceCompleteness="INCOMPLETE"),
        _mutated(record, StructuralChainCompleteness="PARTIAL"),
        _mutated(record, InjectionVerified="no"),
        _mutated(record, ActivationVerified="no"),
        _mutated(record, WritebackValueFnv=BAD_HASH),
        _mutated(record, ConsumerInputFnv="null"),
    ]
    for guard in guards:
        final = final_classification(guard)
        assert final not in _NOT_COMPLETE, guard.get("ModelRuleRecord")
    assert final_classification(guards[0]) == "LIFECYCLE_ONLY"


def test_sp05_null_store_data_still_upgrades_on_skip_and_stale_reload(
        tmp_path):
    """SP05's store-side hash is honestly null in this binary (the
    store_data_fnv wiring is unimplemented, so data_correct stays null and
    the rule's own stage_outcome is RELOAD_UNVERIFIABLE): the upgrade rests
    only on write_skipped + the bound stale reload + the platform
    writeback-consumer edge, and the honest missing early anomaly stays
    recorded — never silently dropped, never a blocker."""
    pilot = _write_sq_pilot(tmp_path, "SP05", SP05_RULE)
    record = build_pilot_record(pilot, "SP05")
    fields = record["ModelRuleRecord"]["fields"]
    assert fields["store_data_fnv"] == "null"
    assert fields["data_correct"] == "null"
    assert fields["stage_outcome"] == "RELOAD_UNVERIFIABLE"
    assert "NO_EARLY_ANOMALY_EVENT" in record["MissingCodes"]
    assert record["FinalClassification"] == "VERIFIED_SINGLE_CONTEXT"
    assert record["ChainMechanism"] == (
        "STORE_COMPLETION_SKIPPED_STALE_RELOAD_CONSUMED")
    # remove either leg of the skip+stale-reload evidence and no upgrade
    for guard in (_mutated_rule(record, write_skipped="0"),
                  _mutated_rule(record, reload_data_hash="null"),
                  _mutated_rule(record, reload_seq="null")):
        assert final_classification(guard) not in _NOT_COMPLETE
        assert final_classification(guard) == "LIFECYCLE_ONLY"


def test_sq_exceptions_are_model_scoped(tmp_path):
    """Exceptions E2/E3/E4 upgrade no other model.  A non-SQ model audited
    over the identical evidence shape never even reads the sq01_chain
    record (the model-rule export is model-keyed), and a completed SQ01
    record whose ModelID is flipped keeps the generic rules: the
    classification gate is the model id, never the evidence shape alone."""
    pilot = _write_sq_pilot(tmp_path, "SQ01", SQ01_RULE)
    da04 = build_pilot_record(pilot, "DA04")
    assert da04["ModelID"] == "DA04"
    assert da04["ModelRuleRecord"] is None  # the export is model-keyed
    assert da04["ObservedTerminal"] == "SDC"
    assert da04["FaultEffectPropagationCoverage"] == "LIFECYCLE_ONLY"
    assert da04["FinalClassification"] == "LIFECYCLE_ONLY"
    assert da04["FinalClassification"] not in _NOT_COMPLETE
    assert da04["ChainMechanism"] == "NOT_APPLICABLE"

    # the record carries the verbatim sq01_chain evidence, but the model id
    # is the gate: an impostor model never upgrades
    sq01 = build_pilot_record(pilot, "SQ01")
    assert sq01["FinalClassification"] == "VERIFIED_SINGLE_CONTEXT"
    impostor = _mutated(sq01, ModelID="DA04")
    assert impostor["ModelRuleRecord"] == sq01["ModelRuleRecord"]
    assert final_classification(impostor) == "LIFECYCLE_ONLY"


def test_sq_pilot_without_model_rule_record_stays_lifecycle(tmp_path):
    """Without the model rule record on the fault's own chain there is no
    §11 evidence at all: the record follows the generic rules exactly as
    before (rule 4 LIFECYCLE_ONLY) and carries no mechanism — no upgrade on
    inference alone."""
    pilot = _write_sq_pilot(tmp_path, "SQ01", None)
    record = build_pilot_record(pilot, "SQ01")
    assert record["ModelRuleRecord"] is None
    assert record["ObservedTerminal"] == "SDC"
    assert record["FaultEffectPropagationCoverage"] == "LIFECYCLE_ONLY"
    assert record["FinalClassification"] == "LIFECYCLE_ONLY"
    assert record["FinalClassification"] not in _NOT_COMPLETE
    assert record["ChainMechanism"] == "NOT_APPLICABLE"


def test_sq_model_level_complete_needs_two_distinct_contexts(tmp_path):
    """Standard §11.4: E2/E3/E4 do not bypass §4.  Per pilot the verdict is
    VERIFIED_SINGLE_CONTEXT; the model-level closure row upgrades the fault
    runs to COMPLETE_CAUSAL_CHAIN only with two or more distinct frozen
    contexts, and the zero-injection control stays UNRESOLVED, never
    contributing a context."""
    records = []
    for ordinal, (name, seed) in enumerate((("R01", 111), ("R02", 222)),
                                           start=1):
        pilot = _write_sq_pilot(tmp_path, "SQ01", SQ01_RULE, name=name,
                                ordinal=ordinal, seed=seed)
        records.append(build_pilot_record(pilot, "SQ01"))
    control = write_pilot(Path(tmp_path) / "SQ01-C01", model="SQ01",
                          injection=False, terminal=None, seed=111)
    control_record = build_pilot_record(control, "SQ01")
    assert control_record["FinalClassification"] == "UNRESOLVED"
    records.append(control_record)
    assert {r["SampleRunID"] for r in records} == {
        "SQ01-F0-W2-S01-R01", "SQ01-F0-W2-S01-R02", "SQ01-F0-W2-S01-C01"}

    def matrix_final(records, out):
        write_closure_matrix(records, out)
        with open(out, newline="", encoding="utf-8") as fh:
            rows = list(csv.reader(fh))
        data = [dict(zip(CLOSURE_MATRIX_COLUMNS, r)) for r in rows[1:]]
        assert len(data) == 1  # same model, same binary: exactly one row
        return data[0]["FinalClassification"]

    # two distinct frozen contexts with a proven model-record chain: the
    # fault runs read COMPLETE_CAUSAL_CHAIN at model level, the control
    # stays UNRESOLVED in the honest mixed aggregate
    two = matrix_final(records, Path(tmp_path) / "closure_two.csv")
    assert "COMPLETE_CAUSAL_CHAIN=2" in two
    assert "UNRESOLVED=1" in two

    # one context never upgrades the model (§4, unchanged)
    single = matrix_final(
        [r for r in records if r["PilotID"] != "SQ01-R02"],
        Path(tmp_path) / "closure_one.csv")
    assert "COMPLETE_CAUSAL_CHAIN" not in single
    assert "VERIFIED_SINGLE_CONTEXT=1" in single
    assert "UNRESOLVED=1" in single


# ---------------------------------------------------------------------------
# standard §6 clause 3d / §12 — exception E5, the RP01 watchdog-timed-out
# skipped-replay load (frozen amendment 2026-11-11)
# ---------------------------------------------------------------------------

def _write_rp01_hang_pilot(tmp_path, name="RP01-R01", **kwargs):
    """One synthetic RP01 watchdog-HANG pilot mirroring the real
    pilots_v3_2_12/RP01-R01..R05 traces: the bridged skip-replay injection
    plus the identity-linked replay marker on the fault's own chain, the
    injector sidecar's CHAOS_RP01_WATCHDOG=EXPIRED record, and the
    crash-durability-truncated gz stream (RecordIntegrity=TRUNCATED,
    TraceCompleteness=INCOMPLETE — both kept honest by the exception)."""
    defaults = dict(
        model="RP01", terminal="HANG", run_status="HANG", replay=True,
        truncated=True, declared="INCOMPLETE", watchdog=True,
        response=False, writeback=False, consumer=False, commit=False,
        oracle=None, addr_stages=False,
    )
    defaults.update(kwargs)
    return write_pilot(Path(tmp_path) / name, **defaults)


def test_rp01_watchdog_timeout_upgrades_despite_truncation(tmp_path):
    """Standard §6 exception E5: an RP01 record whose injector sidecar
    carries the CHAOS_RP01_WATCHDOG=EXPIRED fired=1 injected=1 record, with
    the injection identity-linked to the skipped load through the replay
    marker on the fault's own chain (FaultCausality=PROVEN) and the partial
    trace retained, grades a complete verdict (one verified chain ->
    VERIFIED_SINGLE_CONTEXT; the model-level row upgrades with two or more
    distinct frozen contexts) with ObservedTerminal=HANG and
    TerminalMechanism=REPLAY_TRIGGER_SUPPRESSED_WATCHDOG_TIMEOUT — even
    though RecordIntegrity=TRUNCATED and TraceCompleteness stays
    INCOMPLETE (both fields keep their honest platform values)."""
    pilot = _write_rp01_hang_pilot(tmp_path)
    record = build_pilot_record(pilot, "RP01")
    assert record["InjectionVerified"] == "yes"
    assert record["ActivationVerified"] == "yes"
    assert record["FaultCausality"] == "PROVEN"
    assert record["ObservedTerminal"] == "HANG"
    assert record["RecordIntegrity"] == "TRUNCATED"
    assert record["TraceCompleteness"] == "INCOMPLETE"
    assert record["RP01Watchdog"]["expired"] is True
    assert record["RP01Watchdog"]["injected"] == "1"
    # the exception fires and the integrity fields stay what the platform
    # graded — never relabelled, never upgraded by hand
    assert record["TerminalMechanism"] == (
        "REPLAY_TRIGGER_SUPPRESSED_WATCHDOG_TIMEOUT")
    assert record["VerifiedChainCount"] == 1
    assert record["FinalClassification"] == "VERIFIED_SINGLE_CONTEXT"

    # the model-level row upgrades with two or more distinct frozen contexts
    other = _write_rp01_hang_pilot(tmp_path, name="RP01-R04", ordinal=4,
                                   seed=99)
    other_record = build_pilot_record(other, "RP01")
    out = Path(tmp_path) / "closure.csv"
    write_closure_matrix([record, other_record], out)
    with open(out, newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    data = [dict(zip(CLOSURE_MATRIX_COLUMNS, r)) for r in rows[1:]]
    assert len(data) == 1
    # both contexts complete: the uniform model-level verdict
    assert data[0]["FinalClassification"] == "COMPLETE_CAUSAL_CHAIN"
    assert data[0]["ObservedTerminal"] == "HANG(2/2)"


def test_rp01_every_guard_removed_means_no_upgrade(tmp_path):
    """Exception E5 is a conjunction of proven runtime records: removing
    any single condition — the watchdog sidecar record, its injected=1
    flag, the identity-linked replay marker (causality), the HANG/TIMEOUT
    terminal, the verified injection, or the retained partial trace —
    must drop the record back to the generic rules (never a complete
    verdict; the honest TRUNCATED shape caps at UNRESOLVED)."""
    pilot = _write_rp01_hang_pilot(tmp_path)
    record = build_pilot_record(pilot, "RP01")
    assert record["FinalClassification"] == "VERIFIED_SINGLE_CONTEXT"

    # a SQUASHED RP01 run never fires E5: the unproven squash stays PARTIAL
    # (the frozen v3.2.11 line) unless its trigger is identity-linked
    squashed = _write_rp01_hang_pilot(tmp_path, name="RP01-R02",
                                      terminal="SQUASHED",
                                      run_status="COMPLETED",
                                      declared="COMPLETE", truncated=False,
                                      watchdog=False, squash_record=True)
    squashed_record = build_pilot_record(squashed, "RP01")
    assert squashed_record["ObservedTerminal"] == "SQUASHED"
    assert squashed_record["FinalClassification"] == "PARTIAL"
    assert squashed_record["TerminalMechanism"] == "NOT_APPLICABLE"

    # the same pilot without the watchdog sidecar: no record, no upgrade
    no_watchdog = _write_rp01_hang_pilot(tmp_path, name="RP01-R03",
                                         watchdog=False)
    no_watchdog_record = build_pilot_record(no_watchdog, "RP01")
    assert no_watchdog_record["RP01Watchdog"] is None
    assert no_watchdog_record["FinalClassification"] == "UNRESOLVED"

    # the watchdog line without injected=1 never fires E5
    not_injected = _write_rp01_hang_pilot(
        tmp_path, name="RP01-R05", watchdog={"injected": "0"})
    not_injected_record = build_pilot_record(not_injected, "RP01")
    assert not_injected_record["RP01Watchdog"]["injected"] == "0"
    assert not_injected_record["FinalClassification"] == "UNRESOLVED"

    # without the identity-linked replay marker the hang is not proven
    no_replay = _write_rp01_hang_pilot(tmp_path, name="RP01-R06",
                                        replay=False)
    no_replay_record = build_pilot_record(no_replay, "RP01")
    assert no_replay_record["FaultCausality"] != "PROVEN"
    assert no_replay_record["FinalClassification"] == "UNRESOLVED"

    # record-level guards (the conjunction re-checked on the built record)
    guards = [
        _mutated(record, FaultCausality="PARTIAL"),
        _mutated(record, InjectionVerified="no"),
        _mutated(record, ActivationVerified="no"),
        _mutated(record, ObservedTerminal="MASKED"),
        _mutated(record, RecordIntegrity="INVALID"),
        _mutated(record, ModelID="LQ04"),
        _mutated(record, RP01Watchdog=None),
        _mutated(record, RP01Watchdog={"expired": True, "injected": "0"}),
        _mutated(record, ChainKinds=[]),
        _mutated(record, ChainEventCount=0),
    ]
    for guard in guards:
        final = final_classification(guard)
        assert final not in _NOT_COMPLETE, guard.get("RP01Watchdog")
    # a zero-injection record is never upgraded by any exception
    control = write_pilot(Path(tmp_path) / "RP01-CONTROL-R01",
                          model="RP01", injection=False, terminal=None,
                          watchdog=True, addr_stages=False)
    control_record = build_pilot_record(control, "RP01")
    assert control_record["ObservedTerminal"] == "NO_INJECTION"
    assert control_record["FinalClassification"] == "UNRESOLVED"


# ---------------------------------------------------------------------------
# standard §6 clause 3d / §12 — exception E6, the A03 panic direct address
# match (frozen amendment 2026-11-11)
# ---------------------------------------------------------------------------

def _write_a03_crash_pilot(tmp_path, name="SUPP-A03-R01C", **kwargs):
    """One synthetic A03 crash pilot mirroring the real
    pilots_v3_2_12/SUPP-A03-R0xC traces: the F5 activation record
    (run-level, no chain identity), the on-chain a03_stream record of the
    crash-linked affected load (golden_ea != actual_ea), and the run-level
    simulator_abort panic node whose page_table_fault_va equals the
    on-chain actual_ea with last_injection_dyn_seq tying the pair."""
    defaults = dict(
        model="A03", terminal="CRASH", run_status="CRASH", truncated=True,
        response=False, writeback=False, consumer=False, commit=False,
        oracle=None, a03_activation={}, a03_stream={},
        simulator_abort={},
    )
    defaults.update(kwargs)
    return write_pilot(Path(tmp_path) / name, **defaults)


def test_a03_panic_direct_match_upgrades_despite_truncation(tmp_path):
    """Standard §6 exception E6: an A03 record whose panic page-table fault
    VA equals the on-chain a03_stream actual_ea of the crash-linked,
    F5-affected load (the identity-linked DIRECT_ADDRESS_MATCH, the abort's
    last_injection_dyn_seq tying the pair), with the F5 activation and
    stream records present, grades a complete verdict with
    ObservedTerminal=CRASH and
    TerminalMechanism=STUCK_EA_PANIC_VA_DIRECT_ADDRESS_MATCH — even though
    the crash cut the record (RecordIntegrity=TRUNCATED, structural chain
    PARTIAL because the panic terminated the run)."""
    pilot = _write_a03_crash_pilot(tmp_path)
    record = build_pilot_record(pilot, "A03")
    assert record["InjectionVerified"] == "yes"
    assert record["ActivationVerified"] == "yes"
    assert record["ObservedTerminal"] == "CRASH"
    assert record["RecordIntegrity"] == "TRUNCATED"
    # the run-level records are exported though they carry no chain identity
    assert record["ModelRunRecords"]["a03_activation"]["fields"]["mode"] == (
        "a03_bit3_stuck0_load")
    assert record["ModelRunRecords"]["simulator_abort"]["fields"][
        "page_table_fault_addr"] == "0xffffffffffb73c50"
    stream = record["ModelStreamRecords"][0]
    assert stream["event_type"] == "a03_stream"
    assert stream["fields"]["actual_ea"] == "ffffffffffb73c50"
    assert record["TerminalMechanism"] == (
        "STUCK_EA_PANIC_VA_DIRECT_ADDRESS_MATCH")
    assert record["VerifiedChainCount"] == 1
    assert record["FinalClassification"] == "VERIFIED_SINGLE_CONTEXT"

    # the model-level row upgrades with two or more distinct frozen contexts
    other = _write_a03_crash_pilot(tmp_path, name="SUPP-A03-R02C",
                                   ordinal=2, seed=99)
    other_record = build_pilot_record(other, "A03")
    out = Path(tmp_path) / "closure.csv"
    write_closure_matrix([record, other_record], out)
    with open(out, newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    data = [dict(zip(CLOSURE_MATRIX_COLUMNS, r)) for r in rows[1:]]
    assert data[0]["FinalClassification"] == "COMPLETE_CAUSAL_CHAIN"


def test_a03_every_guard_removed_means_no_upgrade(tmp_path):
    """Exception E6 is a conjunction of proven runtime records: removing
    any single condition — the F5 activation record, the on-chain stream
    record, the affected flag, the panic VA (or its equality with the
    on-chain actual_ea), the crash-linked dyn-seq tie, the CRASH terminal,
    the verified injection, or an INVALID stream — must drop the record
    back to the generic rules (the honest TRUNCATED crash cut caps at
    UNRESOLVED)."""
    pilot = _write_a03_crash_pilot(tmp_path)
    record = build_pilot_record(pilot, "A03")
    assert record["FinalClassification"] == "VERIFIED_SINGLE_CONTEXT"

    # no F5 activation record: the exception never fires on inference
    no_activation = _write_a03_crash_pilot(tmp_path,
                                           name="SUPP-A03-R03C",
                                           a03_activation=None)
    assert build_pilot_record(
        no_activation, "A03")["FinalClassification"] == "UNRESOLVED"

    # no on-chain stream record
    no_stream = _write_a03_crash_pilot(tmp_path, name="SUPP-A03-R04C",
                                       a03_stream=None)
    assert build_pilot_record(
        no_stream, "A03")["FinalClassification"] == "UNRESOLVED"

    # the fault was not applied on the crashing load (affected=0)
    unaffected = _write_a03_crash_pilot(
        tmp_path, name="SUPP-A03-R05C", a03_stream={"affected": "0"})
    assert build_pilot_record(
        unaffected, "A03")["FinalClassification"] == "UNRESOLVED"

    # a panic VA that matches nothing on the chain (the A01 temporal shape)
    mismatch = _write_a03_crash_pilot(
        tmp_path, name="SUPP-A03-R06C",
        simulator_abort={"page_table_fault_addr": "0x0",
                         "address_match": "False"})
    mismatch_record = build_pilot_record(mismatch, "A03")
    assert mismatch_record["ModelRunRecords"]["simulator_abort"]["fields"][
        "page_table_fault_addr"] == "0x0"
    assert mismatch_record["FinalClassification"] == "UNRESOLVED"

    # the abort does not name the matched load: not identity-linked
    unlinked = _write_a03_crash_pilot(
        tmp_path, name="SUPP-A03-R07C",
        simulator_abort={"last_injection_dyn_seq": "999"})
    assert build_pilot_record(
        unlinked, "A03")["FinalClassification"] == "UNRESOLVED"

    # no panic node at all
    no_abort = _write_a03_crash_pilot(tmp_path, name="SUPP-A03-R08C",
                                       simulator_abort=None)
    assert build_pilot_record(
        no_abort, "A03")["FinalClassification"] == "UNRESOLVED"

    # record-level guards (the conjunction re-checked on the built record)
    guards = [
        _mutated(record, ObservedTerminal="MASKED"),
        _mutated(record, InjectionVerified="no"),
        _mutated(record, ActivationVerified="no"),
        _mutated(record, RecordIntegrity="INVALID"),
        _mutated(record, ModelID="A01"),
        _mutated(record, ModelStreamRecords=[]),
        _mutated(record, ModelRunRecords={}),
    ]
    for guard in guards:
        final = final_classification(guard)
        assert final not in _NOT_COMPLETE
    # the E6 exception is model-scoped: an A01-labeled record with the same
    # a03 evidence shape never fires it (the stream export is model-keyed)
    impostor = build_pilot_record(pilot, "A01")
    assert [r["event_type"] for r in impostor["ModelStreamRecords"]] == []
    assert impostor["FinalClassification"] not in _NOT_COMPLETE


# ---------------------------------------------------------------------------
# standard §6 clause 3d / §12 — exception E7, the A01 wrong-EA delivery
# chain and its discard companion (frozen amendment 2026-11-11)
# ---------------------------------------------------------------------------

def _write_a01_masked_pilot(tmp_path, name="SUPP-A01-R02C", **kwargs):
    """One synthetic A01 MASKED pilot mirroring the real
    pilots_v3_2_12/SUPP-A01-R02C/R04C/R05C traces: the on-chain a01_ea
    wrong-EA record (golden_ea != actual_ea, affected=1), the delivered
    response/writeback/consumer chain, and the a01_consumed runtime record
    whose input_hash equals the writeback value hash."""
    defaults = dict(
        model="A01", terminal="MASKED", a01_ea={}, a01_consumed_hash=HASH,
    )
    defaults.update(kwargs)
    return write_pilot(Path(tmp_path) / name, **defaults)


def test_a01_wrong_ea_chain_upgrades(tmp_path):
    """Standard §6 exception E7: an A01 record whose on-chain a01_ea record
    proves a wrong EA (golden != actual, affected=1) that was delivered
    (an on-chain memory_response and register_writeback) and consumed (the
    consumer hash equal to the writeback hash and the a01_consumed record's
    input_hash matching both) with terminal MASKED, grades a complete
    verdict with TerminalMechanism=WRONG_EA_LOAD_DELIVERED_AND_CONSUMED."""
    pilot = _write_a01_masked_pilot(tmp_path)
    record = build_pilot_record(pilot, "A01")
    ea = [r for r in record["ModelStreamRecords"]
          if r["event_type"] == "a01_ea"][0]
    assert ea["fields"]["golden_ea"] == "7ffffefda8"
    assert ea["fields"]["actual_ea"] == "7ffffefda0"
    assert ea["fields"]["affected"] == "1"
    assert record["ObservedTerminal"] == "MASKED"
    assert record["FaultCausality"] == "PROVEN"
    assert record["StructuralChainCompleteness"] == "COMPLETE"
    assert record["TerminalMechanism"] == (
        "WRONG_EA_LOAD_DELIVERED_AND_CONSUMED")
    assert record["VerifiedChainCount"] == 1
    assert record["FinalClassification"] == "VERIFIED_SINGLE_CONTEXT"

    # the model-level row upgrades with two or more distinct frozen contexts
    # (R02/R04/R05 shape: three wrong-EA MASKED contexts)
    others = [build_pilot_record(
        _write_a01_masked_pilot(tmp_path, name=f"SUPP-A01-R0{n}C",
                                ordinal=n, seed=100 + n), "A01")
        for n in (4, 5)]
    out = Path(tmp_path) / "closure.csv"
    write_closure_matrix([record] + others, out)
    with open(out, newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    data = [dict(zip(CLOSURE_MATRIX_COLUMNS, r)) for r in rows[1:]]
    assert data[0]["FinalClassification"] == "COMPLETE_CAUSAL_CHAIN"


def test_a01_wrong_ea_every_guard_removed_means_no_upgrade(tmp_path):
    """Exception E7's complete branch is a conjunction of proven runtime
    records: removing any single condition — the wrong-EA pair, the
    affected flag, the delivered response, the writeback, the consumer hash
    (either side), the a01_consumed record, the MASKED terminal, the §6
    invariant set, or the model id — must drop the record back to the
    generic rules (rule 4 LIFECYCLE_ONLY / rule 1 UNRESOLVED)."""
    pilot = _write_a01_masked_pilot(tmp_path)
    record = build_pilot_record(pilot, "A01")
    assert record["FinalClassification"] == "VERIFIED_SINGLE_CONTEXT"

    # golden == actual: no wrong EA, no upgrade
    right_ea = _write_a01_masked_pilot(
        tmp_path, name="SUPP-A01-R09C", a01_ea={"actual_ea": "7ffffefda8"})
    assert build_pilot_record(right_ea, "A01")[
        "FinalClassification"] == "LIFECYCLE_ONLY"

    # the fault was not applied on this load
    unaffected = _write_a01_masked_pilot(
        tmp_path, name="SUPP-A01-R10C", a01_ea={"affected": "0"})
    assert build_pilot_record(unaffected, "A01")[
        "FinalClassification"] == "LIFECYCLE_ONLY"

    # no runtime record of the consumed wrong-EA value
    unconsumed = _write_a01_masked_pilot(tmp_path,
                                         name="SUPP-A01-R11C",
                                         a01_consumed_hash=None)
    assert build_pilot_record(unconsumed, "A01")[
        "FinalClassification"] == "LIFECYCLE_ONLY"

    # the a01_consumed record's input hash does not match the writeback
    wrong_consumer = _write_a01_masked_pilot(
        tmp_path, name="SUPP-A01-R12C", a01_consumed_hash=BAD_HASH)
    assert build_pilot_record(wrong_consumer, "A01")[
        "FinalClassification"] == "LIFECYCLE_ONLY"

    # no delivered response on the fault's own chain
    undelivered = _write_a01_masked_pilot(tmp_path,
                                          name="SUPP-A01-R13C",
                                          response=False, writeback=False,
                                          consumer=False)
    assert build_pilot_record(undelivered, "A01")[
        "FinalClassification"] == "UNRESOLVED"

    # record-level guards (the conjunction re-checked on the built record)
    guards = [
        _mutated(record, ObservedTerminal="SDC"),
        _mutated(record, FaultCausality="PARTIAL"),
        _mutated(record, RecordIntegrity="INVALID"),
        _mutated(record, TraceCompleteness="INCOMPLETE"),
        _mutated(record, StructuralChainCompleteness="PARTIAL"),
        _mutated(record, InjectionVerified="no"),
        _mutated(record, ActivationVerified="no"),
        _mutated(record, WritebackValueFnv=BAD_HASH),
        _mutated(record, ConsumerInputFnv="null"),
        _mutated(record, ModelStreamRecords=[]),
        _mutated(record, ModelID="A03"),
    ]
    for guard in guards:
        final = final_classification(guard)
        assert final not in _NOT_COMPLETE
    assert final_classification(guards[0]) == "LIFECYCLE_ONLY"
    # the E7 export is model-keyed: an A03 audit of the same pilot reads no
    # a01 records at all
    impostor = build_pilot_record(pilot, "A03")
    assert [r["event_type"] for r in impostor["ModelStreamRecords"]] == []
    assert impostor["FinalClassification"] not in _NOT_COMPLETE


def test_a01_crash_direct_match_and_temporal_only_crash(tmp_path):
    """E7's CRASH branch: the panic VA equal to the on-chain a01_ea
    actual_ea (the direct match) upgrades even the TRUNCATED crash-cut
    record; the temporal-association-only crash (panic VA 0, off the
    fault's EA) never fires E7 and stays UNRESOLVED — the real R01C shape."""
    direct = _write_a01_masked_pilot(
        tmp_path, name="SUPP-A01-R14C", terminal="CRASH",
        run_status="CRASH", truncated=True, response=False, writeback=False,
        consumer=False, oracle=None,
        simulator_abort={"page_table_fault_addr": "0x7ffffefda0",
                          "last_injection_dyn_seq": "3",
                          "address_match": "True"})
    direct_record = build_pilot_record(direct, "A01")
    assert direct_record["ObservedTerminal"] == "CRASH"
    assert direct_record["RecordIntegrity"] == "TRUNCATED"
    assert direct_record["TerminalMechanism"] == (
        "WRONG_EA_LOAD_DELIVERED_AND_CONSUMED")
    assert direct_record["FinalClassification"] == "VERIFIED_SINGLE_CONTEXT"

    temporal = _write_a01_masked_pilot(
        tmp_path, name="SUPP-A01-R01C", terminal="CRASH",
        run_status="CRASH", truncated=True, response=False, writeback=False,
        consumer=False, oracle=None,
        simulator_abort={"page_table_fault_addr": "0x0",
                          "last_injection_dyn_seq": "3",
                          "address_match": "False"})
    temporal_record = build_pilot_record(temporal, "A01")
    assert temporal_record["ObservedTerminal"] == "CRASH"
    assert temporal_record["TerminalMechanism"] == "NOT_APPLICABLE"
    assert temporal_record["FinalClassification"] == "UNRESOLVED"


def test_a01_discard_context_grades_injection_not_activated(tmp_path):
    """v3.3.3 L-A10: an A01 record whose corrupted EA was discarded before
    any request (the on-chain a01_ea_discarded record, applied_to_request=0)
    is graded INJECTION_NOT_ACTIVATED / LIFECYCLE_ONLY — the fault never
    reached a Request, so there is no writeback to grade and no complete
    verdict. This supersedes the v3.2.x PARTIAL re-grade. Without the
    discard record the same shape stays honestly UNRESOLVED (rule 1)."""
    pilot = _write_a01_masked_pilot(
        tmp_path, name="SUPP-A01-R03C", terminal="UNRESOLVED",
        response=False, writeback=False, consumer=False,
        a01_consumed_hash=None, a01_discarded=True)
    record = build_pilot_record(pilot, "A01")
    assert record["ObservedTerminal"] == "INJECTION_NOT_ACTIVATED"
    assert record["FaultCausality"] == "UNPROVEN"
    discarded = [r for r in record["ModelStreamRecords"]
                 if r["event_type"] == "a01_ea_discarded"]
    assert discarded[0]["fields"]["applied_to_request"] == "0"
    assert record["FinalClassification"] == "LIFECYCLE_ONLY"
    assert record["FinalClassification"] not in _NOT_COMPLETE
    assert record["TerminalMechanism"] == "NOT_APPLICABLE"

    # without the discard record the honestly-UNRESOLVED terminal caps at
    # UNRESOLVED exactly as before (rule 1)
    no_discard = _write_a01_masked_pilot(
        tmp_path, name="SUPP-A01-R03D", terminal="UNRESOLVED",
        response=False, writeback=False, consumer=False,
        a01_consumed_hash=None)
    no_discard_record = build_pilot_record(no_discard, "A01")
    assert no_discard_record["ObservedTerminal"] == "UNRESOLVED"
    assert no_discard_record["FinalClassification"] == "UNRESOLVED"

    # a zero-injection terminal remains the clean rule-1 cap
    assert final_classification(
        _mutated(record, ObservedTerminal="NO_INJECTION")) == "UNRESOLVED"


# ---------------------------------------------------------------------------
# standard §12.5 — the frozen prior-audit import (keyed by model + binary
# SHA + evidence path; the frozen-four are never re-graded)
# ---------------------------------------------------------------------------

def _write_prior_verdict(path, model, pilots, model_row=None):
    """Write a synthetic v3.2.11-shaped verdict JSON (model/pilots/
    model_row with the per-pilot binary_sha/stages/terminal/oracle/
    classification/evidence_path fields)."""
    payload = {
        "model": model, "sub_unit": "n/a", "fault_definition": "n/a",
        "pilot_count": len(pilots), "pilots": pilots,
        "model_row": model_row or {"SubUnit": "L1D",
                                   "FaultDefinition": "prior audit row"},
        "supplementary_pilot_required": "no",
        "evidence_paths": [p["evidence_path"] for p in pilots],
    }
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return Path(path)


def _prior_pilot(pilot_id, sha, classification, terminal="MASKED",
                 oracle="PASS", evidence_path="pilots_v3_2_6/x",
                 missing=None):
    return {
        "pilot_id": pilot_id, "sample_run_id": f"{pilot_id}-S01",
        "seed": "4711", "event_ordinal": "1", "binary_sha": sha,
        "stages": {"injection_verified": "yes",
                   "activation_verified": "yes",
                   "early_anomaly_verified": "yes",
                   "intermediate_propagation_verified": "yes",
                   "register_writeback_verified": "yes",
                   "consumer_verified": "yes",
                   "commit_verified": "yes",
                   "terminal_verified": "yes",
                   "oracle_verified": "missing"},
        "terminal": terminal, "terminal_reason": "PRIOR_REASON",
        "oracle": oracle, "classification": classification,
        "classification_rule": "PRIOR_RULE",
        "missing": missing or [], "evidence_path": evidence_path,
    }


def test_frozen_import_carries_verdicts_verbatim(tmp_path):
    """Standard §12.5: the frozen import carries the prior audit's
    per-pilot verdicts verbatim — FinalClassification IS the prior
    classification, ObservedTerminal/ApplicationOracle the prior
    terminal/oracle, with the PriorAudit provenance marker and the prior
    rule named — while the four v3.2.12 standard fields the prior audit
    did not record per pilot are the literal NULL, never re-derived."""
    prior = _write_prior_verdict(
        tmp_path / "LP01_verdict.json", "LP01",
        [_prior_pilot("LP01-R01", SHA_A, "COMPLETE_CAUSAL_CHAIN",
                      evidence_path="pilots_v3_2_6/LP01-R01"),
         _prior_pilot("LP01-R02", SHA_A, "PARTIAL", terminal="SQUASHED",
                      evidence_path="pilots_v3_2_6/LP01-R02")])
    out = tmp_path / "LP01_frozen.json"
    assert main(["frozen", "--prior", str(prior), "--model", "LP01",
                 "--json", str(out)]) == 0
    records = json.loads(out.read_text())["records"]
    assert len(records) == 2
    by_pilot = {r["PilotID"]: r for r in records}
    complete = by_pilot["LP01-R01"]
    assert complete["PriorAudit"] == FROZEN_PRIOR_AUDIT
    assert complete["FinalClassification"] == "COMPLETE_CAUSAL_CHAIN"
    assert complete["ObservedTerminal"] == "MASKED"
    assert complete["ApplicationOracle"] == "PASS"
    assert complete["PriorAuditRule"] == "PRIOR_RULE"
    assert complete["BinarySHA256"] == SHA_A
    assert complete["EvidencePath"] == "pilots_v3_2_6/LP01-R01"
    assert complete["InjectionVerified"] == "yes"
    assert complete["ActivationVerified"] == "yes"
    # the standard fields the prior audit did not record: literal NULL
    for column in ("RecordIntegrity", "TraceCompleteness",
                   "StructuralChainCompleteness",
                   "FaultEffectPropagationCoverage", "FaultCausality"):
        assert complete[column] == "NULL", column
    assert by_pilot["LP01-R02"]["FinalClassification"] == "PARTIAL"
    assert by_pilot["LP01-R02"]["ObservedTerminal"] == "SQUASHED"

    # the imported records write cleanly through the matrix writer (the
    # NULL absences aggregate honestly, never as blanks)
    matrix_out = tmp_path / "closure.csv"
    write_closure_matrix(records, matrix_out)
    with open(matrix_out, newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    data = [dict(zip(CLOSURE_MATRIX_COLUMNS, r)) for r in rows[1:]]
    assert len(data) == 1
    assert data[0]["FinalClassification"] == (
        "mixed(COMPLETE_CAUSAL_CHAIN=1;PARTIAL=1)")
    assert data[0]["RecordIntegrity"] == "NULL(2/2)"


def test_frozen_import_is_keyed_by_model_and_binary(tmp_path):
    """The import's key (model + binary SHA + evidence path) is enforced
    loudly: a model key that does not match the verdict file is refused; a
    binary key the file carries no pilot under is refused (the import can
    never bend the key to reach another binary's verdicts); and with a
    valid binary key only that binary's pilots import."""
    prior = _write_prior_verdict(
        tmp_path / "DA04_verdict.json", "DA04",
        [_prior_pilot("DA04-R04", SHA_A, "COMPLETE_CAUSAL_CHAIN",
                      terminal="SDC", oracle="FAIL"),
         _prior_pilot("DA04-R01", SHA_B, "PARTIAL", terminal="SQUASHED",
                      evidence_path="pilots_v3_2_4/DA04-R01")])
    # model key mismatch: refused
    with pytest.raises(ValueError, match="keyed to model"):
        build_frozen_records(prior, model="LP01")
    # a pilot without a binary SHA or evidence path breaks the key: refused
    broken = _write_prior_verdict(
        tmp_path / "MD04_verdict.json", "MD04",
        [_prior_pilot("MD04-R01", None, "PARTIAL")])
    with pytest.raises(ValueError, match="binary SHA256"):
        build_frozen_records(broken)
    no_path = _write_prior_verdict(
        tmp_path / "FW05_verdict.json", "FW05",
        [_prior_pilot("FW05-R01", SHA_A, "PARTIAL", evidence_path="")])
    with pytest.raises(ValueError, match="evidence path"):
        build_frozen_records(no_path)
    # binary key the file carries no pilot under: refused
    with pytest.raises(ValueError, match="refuses to import a different"):
        build_frozen_records(prior, binary_sha="ab" * 32)
    # a valid binary key imports only that binary's pilots
    records = build_frozen_records(prior, binary_sha=SHA_A)
    assert [r["PilotID"] for r in records] == ["DA04-R04"]
    assert records[0]["BinarySHA256"] == SHA_A
    records_b = build_frozen_records(prior, binary_sha=SHA_B)
    assert [r["PilotID"] for r in records_b] == ["DA04-R01"]
    # without a binary key every pilot imports under its own recorded binary
    assert {r["PilotID"] for r in build_frozen_records(prior)} == {
        "DA04-R04", "DA04-R01"}


def test_frozen_import_supersedes_only_the_same_binary_key(tmp_path):
    """The matrix merge is keyed by (ModelID, BinarySHA256): a frozen group
    supersedes the generic records of the SAME key (the prior audit already
    verified that group — no double count, a loud note), and never touches
    any other binary's records (a frozen import cannot silently override a
    different binary)."""
    generic_a = write_pilot(tmp_path / "LP01-R01", model="LP01",
                           binary_sha=SHA_A)
    generic_b = write_pilot(tmp_path / "LP01-R02", model="LP01",
                            binary_sha=SHA_B)
    records_json = tmp_path / "records.json"
    assert main(["record", "--model", "LP01",
                 "--pilot-dir", str(generic_a),
                 "--pilot-dir", str(generic_b),
                 "--json", str(records_json)]) == 0
    prior = _write_prior_verdict(
        tmp_path / "LP01_verdict.json", "LP01",
        [_prior_pilot("LP01-R01", SHA_A, "COMPLETE_CAUSAL_CHAIN",
                      evidence_path="pilots_v3_2_6/LP01-R01")])
    frozen_json = tmp_path / "LP01_frozen.json"
    assert main(["frozen", "--prior", str(prior),
                 "--json", str(frozen_json)]) == 0

    out = tmp_path / "closure.csv"
    assert main(["matrix", "--records", str(records_json),
                 "--frozen-prior", str(frozen_json),
                 "--out", str(out)]) == 0
    with open(out, newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    data = [dict(zip(CLOSURE_MATRIX_COLUMNS, r)) for r in rows[1:]]
    by_model = {row["ModelID"]: row for row in data}
    assert set(by_model) == {f"LP01@{SHA_A[:8]}", f"LP01@{SHA_B[:8]}"}
    # the frozen verdict supersedes the SAME binary's generic record (no
    # double count: PilotCount is the frozen set's size, the verdict is the
    # prior classification, never the generic one)
    frozen_row = by_model[f"LP01@{SHA_A[:8]}"]
    assert frozen_row["PilotCount"] == "1"
    assert frozen_row["FinalClassification"] == "COMPLETE_CAUSAL_CHAIN"
    assert frozen_row["EvidencePath"] == "pilots_v3_2_6/LP01-R01"
    # the different binary's generic record is untouched — never overridden
    other_row = by_model[f"LP01@{SHA_B[:8]}"]
    assert other_row["PilotCount"] == "1"
    assert other_row["FinalClassification"] == "LIFECYCLE_ONLY"
    assert other_row["EvidencePath"] == str(generic_b)

    # --frozen-prior accepts only frozen imports: a generic records file
    # passed there is refused loudly
    with pytest.raises(ValueError, match="PriorAudit"):
        main(["matrix", "--records", str(records_json),
              "--frozen-prior", str(records_json),
              "--out", str(tmp_path / "bad.csv")])

    # the same merge drives the feature dataset (the frozen group's rows
    # carry the prior verdicts; the other binary's rows are untouched)
    features_out = tmp_path / "features.csv"
    assert main(["features", "--records", str(records_json),
                 "--frozen-prior", str(frozen_json),
                 "--out", str(features_out)]) == 0
    with open(features_out, newline="", encoding="utf-8") as fh:
        feature_rows = list(csv.DictReader(fh))
    frozen_pilot_rows = [r for r in feature_rows
                         if r["BinarySHA256"] == SHA_A]
    assert len(frozen_pilot_rows) == 1
    assert frozen_pilot_rows[0]["FinalClassification"] == (
        "COMPLETE_CAUSAL_CHAIN")
    assert frozen_pilot_rows[0]["RecordIntegrity"] == "NULL"
    for row in feature_rows:
        for column, cell in row.items():
            assert cell.strip() != "", (column, row["PilotID"])
