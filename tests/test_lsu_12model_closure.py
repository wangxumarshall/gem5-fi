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
"""
import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from lsu_12model_closure import (  # noqa: E402
    CLOSURE_MATRIX_COLUMNS,
    FEATURE_DATASET_COLUMNS,
    MISSING_MATRIX_COLUMNS,
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
        "dyn_inst_seq": str(seq), "commit_seq": cseq,
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
                run_status="COMPLETED"):
    """Write one synthetic pilot dir; returns its Path.

    ``decoy_consumer`` adds a LATER consumer_commit with a different ptag and
    dyn_inst_seq (the time-adjacency bait). ``divergent`` flips the writeback
    and consumer into a verified corrupted delivery with an oracle FAIL.
    """
    directory = Path(directory)
    directory.mkdir(parents=True)
    suffix = directory.name.split("-")[-1]
    run_id = f"{model}-F0-W2"
    sample = f"{model}-F0-W2-S01-{suffix}"

    lines = []
    lines.append(_event(1, "lq_lifecycle", 78540, 2, 0,
                        "queue=LQ;action=alloc;index=9;generation=9"))
    if injection:
        lines.append(_event(3, "injection", 80080, 3, 1,
                            "site=executeLoad_post;family=lq04;"
                            "valid_before=1;valid_after=0;lq_idx=1;lq_gen=1;"
                            "pc=400338", inj="INJECTED", act=activation,
                            new_value="0x41ffe8"))
    if response:
        lines.append(_event(8, "memory_response", 135520, 3, 1,
                            "family=lq04;size=8;"
                            f"data_fnv={HASH};request_id=1;pa=1fe8"))
    if writeback:
        corrupt = "1" if divergent else "0"
        lines.append(_event(9, "register_writeback", 135520, 3, 1,
                            f"family=lq04;data_corruption={corrupt};"
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
    if decoy_consumer:
        # later tick, different ptag AND different dyn_inst_seq: adjacent, but
        # never on the fault's chain (identity rules of the standard)
        lines.append(_event(99, "consumer_commit", 300000, 99, 9,
                            f"pc=40034c;source_event_id=9;"
                            f"consumer_input_fnv={HASH};"
                            "consumer_input_matches_source=1",
                            source=9, commit_status="COMMITTED", cseq="99"))

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
