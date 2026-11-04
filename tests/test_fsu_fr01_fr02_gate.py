"""tests/test_fsu_fr01_fr02_gate.py — FR01/FR02 transient lifecycle gate.

Fully offline: every test builds a synthetic attempt directory under tmp_path
(or reads the already-existing real gate evidence under runs/fsu-gates).
No gem5 run, no build, no write under runs/.

Covered:
  * FR01 single bit (identity, mask, non-target bits, lifecycle closure)
  * FR02 two different bits, cross-lane classification, popcount==2
  * FR02 collision rejected before injection (VecFaultFailClosed)
  * an inconsistent command that still injected -> FAIL
  * a changed non-target bit -> FAIL
  * pre-consumer overwrite closure; Masked is NOT certified from it alone
  * squash closure (and the current emitter's terminal misclassification)
  * no consumer -> not_consumed, never Masked
  * lane / precision mismatch -> FAIL or evidence_missing
  * out-of-range directed lane -> fail closed before injection
  * consecutive writes do not re-stick; stuck_reapplied/reflip -> FAIL
  * committed chain -> L5 witness certified
  * truncated stream -> FAIL
  * the real FR01-FR02-F0-W1 gate evidence still passes
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import fsu_fr01_fr02_gate as G  # noqa: E402

RUN = "FSU-FR01-F0-W1"
SID = "s1"
REAL_GATE = ROOT / "runs/fsu-gates/FR01-FR02-F0-W1"

def hx(value):
    return "0x%032x" % value


HEX0 = hx(0)
HEX20 = hx(0x20)
HEX_2BIT = hx((1 << 5) | (1 << 37))   # bits 5 and 37
HEX_40 = hx(0x40)
HEX_80 = hx(0x80)


# ---------------------------------------------------------------------------
# Synthetic attempt builders
# ---------------------------------------------------------------------------
def evt(kind, **kw):
    base = {
        "kind": kind,
        "run_id": RUN,
        "sample_run_id": SID,
        "fault_id": "1",
        "event_id": "0",
        "parent_event_id": "",
        "tick": "10",
        "cycle": "10",
        "core_id": "0",
        "thread_id": "0",
    }
    base.update({k: ("" if v is None else v) for k, v in kw.items()})
    return "PROP-EVT: " + " ".join("%s=%s" % (k, v) for k, v in base.items())


def root_fr01(**over):
    d = dict(
        kind="fault_applied", event_id="0", parent_event_id="",
        tick="10", model_id="FR01", submodel="FR01-a", unit="PRF_Vec",
        freq="F0", field="transient_bit_flip", corr="origin",
        reg_class="vec", phys_reg="1", arch_reg="1", thread_id="0",
        reg_generation="1", lane_width="64", lane_offset="0",
        lane_mask="0x20", bit_in_lane="5", bit_indices="5",
        fault_mask=HEX20, before="0x0", after="0x20",
        full_before=HEX0, full_after=HEX20,
        activated="1", sample_policy="one_shot", contained="0",
        state_before="cell_correct", state_after="transient_bit_flipped",
        precision="",
    )
    d.update(over)
    return evt(**d)


def root_fr02(**over):
    d = dict(
        kind="fault_applied", event_id="0", parent_event_id="",
        tick="10", model_id="FR02", submodel="FR02-c", unit="PRF_Vec",
        freq="F0", field="transient_bit_flip", corr="origin",
        reg_class="vec", phys_reg="1", arch_reg="1", thread_id="0",
        reg_generation="1", lane_width="32", lane_offset="0",
        lane_mask="0x20", bit_in_lane="5", bit_indices="5,37",
        fault_mask=HEX_2BIT, before="0x0", after="0x20",
        full_before=HEX0, full_after=HEX_2BIT,
        activated="1", sample_policy="one_shot", contained="0",
        state_before="cell_correct", state_after="transient_bit_flipped",
        precision="",
    )
    d.update(over)
    return evt(**d)


def carrier(event_id="1", parent="0", model="FR01", lw="64", lo="0",
            lane_mask="0x20", bits="5", after="0x20", **over):
    d = dict(
        kind="carrier_state", event_id=event_id, parent_event_id=parent,
        tick="10", model_id=model, submodel="FR01-a", unit="PRF_Vec",
        freq="F0", reg_class="vec", phys_reg="1", reg_generation="1",
        lane_width=lw, lane_offset=lo, lane_mask=lane_mask,
        bit_indices=bits, before=after, after=after, install_event="0",
        cell_allocated="1", state_before="fault_installed",
        state_after="carrier_ready",
    )
    d.update(over)
    return evt(**d)


def read(event_id="2", parent="1", model="FR01", seq="50", gen="1",
         value="0x20", tick="20", lw="64", lo="0", lane_mask="0x20",
         bits="5", **over):
    d = dict(
        kind="operand_read", event_id=event_id, parent_event_id=parent,
        tick=tick, model_id=model, submodel="FR01-a", unit="PRF_Vec",
        freq="F0", reg_class="vec", phys_reg="1", arch_reg="1",
        reg_generation=gen, dyn_inst_seq=seq, consumer_seq=seq,
        lane_width=lw, lane_offset=lo, lane_mask=lane_mask,
        bit_indices=bits, before=value, after=value,
        install_event="0", activated="1", state_before="cell_flipped",
        state_after="operand_read_flipped",
    )
    d.update(over)
    return evt(**d)


def overwrite(event_id="2", parent="1", model="FR01", sn="7", gen="2",
              before="0x20", after="0x40", tick="30", lw="64", lo="0",
              lane_mask="0x20", bits="5", full_after=HEX_40, **over):
    d = dict(
        kind="overwrite", event_id=event_id, parent_event_id=parent,
        tick=tick, model_id=model, submodel="FR01-a", unit="PRF_Vec",
        freq="F0", reg_class="vec", phys_reg="1", arch_reg="2",
        reg_generation=gen, dyn_inst_seq=sn, producer_seq=sn,
        lane_width=lw, lane_offset=lo, lane_mask=lane_mask,
        bit_indices=bits, before=before, after=after, full_after=full_after,
        detection_layer="L1", contained="1", containment_layer="L1",
        containment_reason="phys_cell_rewritten", outcome="contained",
        install_event="0", activated="1",
        state_before="transient_flipped",
        state_after="overwritten_by_real_write",
    )
    d.update(over)
    return evt(**d)


def commit(event_id="3", parent="2", model="FR01", seq="50", gen="1",
           value="0x20", tick="40", lw="64", lo="0", lane_mask="0x20",
           bits="5", ordinal="1", **over):
    d = dict(
        kind="commit", event_id=event_id, parent_event_id=parent,
        tick=tick, model_id=model, submodel="FR01-a", unit="PRF_Vec",
        freq="F0", reg_class="vec", phys_reg="1", reg_generation=gen,
        dyn_inst_seq=seq, consumer_seq=seq, commit_seq=ordinal,
        lane_width=lw, lane_offset=lo, lane_mask=lane_mask,
        bit_indices=bits, before=value, after=value,
        detection_layer="L5", outcome="errant_commit", contained="0",
        install_event="0", activated="1", commit_events="1",
        squash_events="0", consumers_recorded="1",
        state_before="operand_read_flipped", state_after="committed",
    )
    d.update(over)
    return evt(**d)


def squash(event_id="3", parent="2", model="FR01", seq="50", gen="1",
           value="0x20", tick="40", lw="64", lo="0", lane_mask="0x20",
           bits="5", **over):
    d = dict(
        kind="squash", event_id=event_id, parent_event_id=parent,
        tick=tick, model_id=model, submodel="FR01-a", unit="PRF_Vec",
        freq="F0", reg_class="vec", phys_reg="1", reg_generation=gen,
        dyn_inst_seq=seq, consumer_seq=seq, lane_width=lw, lane_offset=lo,
        lane_mask=lane_mask, bit_indices=bits, before=value, after=value,
        detection_layer="", outcome="squashed", contained="0",
        squashed="1", install_event="0", activated="1",
        squash_events="1", commit_events="0", consumers_recorded="1",
        state_before="operand_read_flipped", state_after="squashed",
    )
    d.update(over)
    return evt(**d)


def chain_end(event_id="3", parent="2", model="FR01", terminal="overwritten",
              tick="100", lw="64", lo="0", lane_mask="0x20", bits="5",
              gen="1", contained="1", outcome="detected_contained",
              read_exp="0", write_exp="2", commit_events="0",
              squash_events="0", consumers="0", affected_sn="7",
              first_impact_sn="0", l5_witness="0", **over):
    d = dict(
        kind="chain_end", event_id=event_id, parent_event_id=parent,
        tick=tick, model_id=model, submodel="FR01-a", unit="PRF_Vec",
        freq="F0", field="transient_bit_flip", reg_class="vec",
        phys_reg="1", reg_generation=gen, lane_width=lw, lane_offset=lo,
        lane_mask=lane_mask, bit_indices=bits, install_event="0",
        terminal=terminal, contained=contained, outcome=outcome,
        detection_layer="", read_exposures_total=read_exp,
        write_exposures_total=write_exp, commit_events=commit_events,
        squash_events=squash_events, consumers_recorded=consumers,
        affected_sn=affected_sn, first_impact_sn=first_impact_sn,
        l5_witness_event=l5_witness, first_impact_tick="0",
        first_impact_latency="0", phys_reads="0",
        state_before="transient_lifecycle", state_after=terminal,
    )
    d.update(over)
    return evt(**d)


def stats_text(**over):
    values = {
        "simTicks": 1000,
        "simInsts": 500,
        "board.chaos_phys.numFaultsInjected": 1,
        "board.chaos_phys.numBitFlips": 1,
        "board.chaos_phys.numStuckAtZero": 0,
        "board.chaos_phys.numStuckAtOne": 0,
        "board.chaos_phys.numPermanentFaults": 0,
    }
    values.update(over)
    return "".join("%s %s # synthetic\n" % (k, v) for k, v in values.items())


def fr01_expect(**over):
    d = {
        "model_id": "FR01",
        "bits": 1,
        "fault_mask": "0x20",
        "lane_width": 64,
        "lane_offset": 0,
        "semantic_role": "FR01-a",
        "phys_reg": 1,
        "run_id": RUN,
        "sample_run_id": SID,
        "fault_type": "bit_flip",
        "injection_mode": "phys",
        "reg_target_class": "vector",
        "max_faults": 1,
    }
    d.update(over)
    return d


def fr02_expect(**over):
    d = {
        "model_id": "FR02",
        "bits": 2,
        "fault_mask": "0x2000000020",
        "lane_width": 32,
        "lane_offset": -1,
        "semantic_role": "FR02-c",
        "phys_reg": 1,
        "run_id": RUN,
        "sample_run_id": SID,
        "fault_type": "bit_flip",
        "injection_mode": "phys",
        "reg_target_class": "vector",
        "max_faults": 1,
    }
    d.update(over)
    return d


def install_log(model="FR01", phys="1", gen="1", lane="0", lw="64",
                bits="5", mask="0x20", before="0x0", after="0x20",
                role="FR01-a"):
    return (
        "VecTransientInstall: cycle=10 fault=1 model=%s phys=%s gen=%s "
        "lane=%s lane_width=%s bits=%s mask=%s before=%s after=%s\n"
        "Cycle: 10, CPU: board.processor.cores.core, Thread: 0, Mode: phys, "
        "RegClass: vec, PhysReg[%s] (Active, mapped from ArchReg[1]), "
        "semanticRole: %s, FaultType: bit_flip, Mask: %s\n"
        % (model, phys, gen, lane, lw, bits, mask, before, after, phys,
           role, "0" * 34 + "1" * 8)
    )


def make_attempt(tmp_path, events, expect, log="", stats=None,
                 bad_gzip=False, name="a"):
    d = Path(tmp_path) / name
    d.mkdir(parents=True, exist_ok=True)
    if bad_gzip:
        (d / "prop_evt.txt.gz").write_bytes(b"not a gzip stream")
    else:
        (d / "prop_evt.txt").write_text(
            "# synthetic prop-evt\n" + "\n".join(events) + "\n",
            encoding="utf-8")
    if expect is not None:
        (d / "expect.json").write_text(json.dumps(expect), encoding="utf-8")
    if log:
        (d / "fault_injections.log").write_text(log, encoding="utf-8")
    if stats is not None:
        (d / "stats.txt").write_text(stats, encoding="utf-8")
    return d


def analyze(tmp_path, events, expect, **kw):
    # A real attempt always has stats.txt; default to a completed one-shot run
    # so the run-boundary/permanent counters are exercised unless a test
    # deliberately supplies its own (e.g. a fail-closed zero-injection run).
    kw.setdefault("stats", stats_text())
    d = make_attempt(tmp_path, events, expect, **kw)
    return G.analyze_attempt(d)


def check(report, name):
    for item in report["checks"]:
        if item["check"] == name:
            return item
    raise AssertionError("check %r not found in %r"
                         % (name, [i["check"] for i in report["checks"]]))


# ---------------------------------------------------------------------------
# FR01 / FR02 happy paths
# ---------------------------------------------------------------------------
def test_fr01_single_bit_valid(tmp_path):
    events = [
        root_fr01(),
        carrier(),
        overwrite(),
        chain_end(),
    ]
    rep = analyze(tmp_path, events, fr01_expect(),
                  log=install_log(), stats=stats_text())
    assert rep["status"] == "PASS", rep["reason"]
    assert rep["model_id"] == "FR01"
    assert rep["lifecycle"]["closure"] == "overwritten"
    assert rep["lifecycle"]["recorded_terminal"] == "overwritten"
    assert rep["identity"]["flats"] == [5]
    assert rep["identity"]["fault_mask"] == 0x20
    assert rep["identity"]["lane_width"] == 64
    assert rep["identity"]["lane_offset"] == 0
    assert rep["identity"]["bit_in_lane"] == 5
    assert check(rep, "mask_identity")["status"] == "PASS"
    assert check(rep, "lane_identity")["status"] == "PASS"
    assert check(rep, "non_target_bits")["status"] == "PASS"
    # An L1 overwrite alone must never be certified as Masked.
    assert rep["masked_certification"]["certified"] is False
    assert rep["masked_certification"]["verdict"] == "BLOCKED"
    assert rep["certification"]["status"] == "BLOCKED"
    # Evidence paths + sha256 are reported.
    ev = rep["evidence"]["event_stream"]
    assert len(ev["sha256"]) == 64
    assert rep["expectation_sources"]["phys_reg"] == "expect.json"


def test_fr02_two_distinct_bits_cross_lane(tmp_path):
    events = [
        root_fr02(),
        carrier(model="FR02", lw="32", lane_mask="0x20", bits="5,37"),
        overwrite(model="FR02", lw="32", lo="0", bits="5,37",
                  full_after=hx((1 << 5) | (1 << 38))),
        chain_end(model="FR02", lw="32", lo="0", bits="5,37"),
    ]
    rep = analyze(tmp_path, events, fr02_expect(), name="fr02")
    assert rep["status"] == "PASS", rep["reason"]
    assert rep["identity"]["flats"] == [5, 37]
    assert rep["identity"]["fault_mask"] == 0x2000000020
    assert rep["identity"]["geometry"]["cross_lane"] is True
    assert check(rep, "mask_identity")["status"] == "PASS"
    assert check(rep, "non_target_bits")["status"] == "PASS"
    assert check(rep, "role_geometry")["status"] == "PASS"


# ---------------------------------------------------------------------------
# Collision / non-target / fail-closed
# ---------------------------------------------------------------------------
def test_fr02_collision_rejected_before_injection(tmp_path):
    expect = fr02_expect(fault_mask="0x20")  # popcount 1, bits says 2
    log = ("VecFaultFailClosed: cycle=10000 model=FR02 phys=34 "
           "lane_width=32 lane_offset=-1 bits=2 explicit_mask=0x20 "
           "reason=mask_popcount_mismatch (no injection; fault not consumed)\n")
    rep = analyze(tmp_path, [], expect, log=log,
                  stats=stats_text(**{
                      "board.chaos_phys.numFaultsInjected": 0,
                      "board.chaos_phys.numBitFlips": 0,
                  }))
    assert rep["status"] == "PASS", rep["reason"]
    assert rep["mode"] == "fail_closed"
    assert rep["certification"]["status"] == "CERTIFIED"
    assert check(rep, "fail_closed_log")["status"] == "PASS"
    assert "mask_popcount_mismatch" in check(rep, "fail_closed_log")["detail"]


def test_collision_that_still_injected_fails(tmp_path):
    expect = fr02_expect(fault_mask="0x20")
    events = [root_fr01(), carrier(),
              chain_end(event_id="2", parent="1", terminal="not_consumed",
                        contained="0", outcome="run_end", write_exp="1",
                        affected_sn="0")]
    rep = analyze(tmp_path, events, expect)
    assert rep["status"] == "FAIL"
    assert check(rep, "no_fault_applied")["status"] == "FAIL"


def test_non_target_bit_changed_is_rejected(tmp_path):
    bad_after = hx((1 << 5) | (1 << 14) | (1 << 37))  # bit 14 is not selected
    events = [
        root_fr02(full_after=bad_after),
        carrier(model="FR02", lw="32", lane_mask="0x20", bits="5,37"),
        chain_end(model="FR02", lw="32", lo="0", bits="5,37"),
    ]
    rep = analyze(tmp_path, events, fr02_expect())
    assert rep["status"] == "FAIL"
    nt = check(rep, "non_target_bits")
    assert nt["status"] == "FAIL"
    assert "full_before^full_after" in nt["detail"]


def test_duplicate_bit_positions_are_rejected(tmp_path):
    # Two mask bits are requested, but the event claims the same flat bit
    # twice: the identity is internally inconsistent even though the command
    # itself is valid (no fail-closed expectation).
    two = hx(0x60)
    events = [
        root_fr02(bit_indices="5,5", fault_mask=two,
                  lane_mask="0x60", after="0x60", full_after=two),
        carrier(model="FR02", lw="32", lane_mask="0x60", bits="5,5",
                after="0x60"),
        chain_end(model="FR02", lw="32", lo="0", lane_mask="0x60",
                  bits="5,5"),
    ]
    rep = analyze(tmp_path, events,
                  fr02_expect(fault_mask=two, semantic_role=""))
    assert rep["status"] == "FAIL"
    assert check(rep, "bit_identity")["status"] == "FAIL"


# ---------------------------------------------------------------------------
# Lifecycle closures
# ---------------------------------------------------------------------------
def test_preconsumer_overwrite_closure(tmp_path):
    events = [
        root_fr01(),
        carrier(),
        overwrite(),          # no operand_read came first
        chain_end(),
    ]
    rep = analyze(tmp_path, events, fr01_expect())
    assert rep["status"] == "PASS", rep["reason"]
    assert rep["lifecycle"]["closure"] == "overwritten"
    assert rep["lifecycle"]["events"]["counts"]["operand_read"] == 0
    assert rep["lifecycle"]["events"]["counts"]["commit"] == 0
    assert rep["lifecycle"]["certified_closure"] is True
    assert rep["lifecycle"]["events"]["overwrite_phase"] == \
        "before_any_consumer_read"
    # ... but "fault is gone" is still BLOCKED on a legacy stream that has
    # no target-restoration / post-overwrite observation fields.
    assert rep["masked_certification"]["certified"] is False
    assert "post-overwrite" in rep["masked_certification"]["reason"].lower()


def test_overwrite_containment_certified_with_full_visibility(tmp_path):
    """The new evidence closes the chain: target bits restored, every
    post-overwrite read/write observed and clean."""
    events = [
        root_fr01(),
        carrier(),
        overwrite(event_id="2", parent="1", tick="30", sn="7", gen="1",
                  full_before=HEX20, fault_mask=HEX20,
                  target_bits_before="0x20", target_bits_after="0x0",
                  target_bits_restored="1"),
        evt(kind="post_overwrite_read", event_id="3", parent_event_id="2",
            tick="40", model_id="FR01", submodel="FR01-a",
            reg_class="vec", phys_reg="1", reg_generation="1",
            dyn_inst_seq="8", consumer_seq="8", lane_width="64",
            lane_offset="0", lane_mask="0x20", bit_indices="5",
            before="0x0", after="0x0", target_bits_flipped="0",
            same_generation="1", activated="0", install_event="0",
            state_before="cell_clean", state_after="clean_read"),
        evt(kind="write_after_overwrite", event_id="4", parent_event_id="3",
            tick="50", model_id="FR01", submodel="FR01-a",
            reg_class="vec", phys_reg="1", reg_generation="1",
            dyn_inst_seq="9", lane_width="64", lane_offset="0",
            lane_mask="0x20", bit_indices="5", before="0x0", after="0x0",
            target_bits_flipped="0", activated="0", install_event="0",
            state_before="cell_clean", state_after="clean_write"),
        chain_end(event_id="5", parent="4", tick="100",
                  post_overwrite_reads_total="1",
                  post_overwrite_reads_emitted="1",
                  post_overwrite_affected_reads="0",
                  post_overwrite_writes_total="1",
                  post_overwrite_writes_emitted="1",
                  post_overwrite_writes_affected="0",
                  generation_changes="0"),
    ]
    rep = analyze(tmp_path, events, fr01_expect())
    assert rep["status"] == "PASS", rep["reason"]
    assert rep["containment"]["certified"] is True, rep["containment"]
    assert rep["certification"]["status"] == "CERTIFIED"
    assert rep["masked_certification"]["certified"] is True
    assert rep["masked_certification"]["verdict"] == "CONTAINED_BY_OVERWRITE"


def test_overwrite_containment_blocked_when_a_post_read_is_affected(
        tmp_path):
    events = [
        root_fr01(),
        carrier(),
        overwrite(event_id="2", parent="1", tick="30", sn="7", gen="1",
                  full_before=HEX20, fault_mask=HEX20,
                  target_bits_restored="1"),
        evt(kind="post_overwrite_read", event_id="3", parent_event_id="2",
            tick="40", model_id="FR01", submodel="FR01-a",
            reg_class="vec", phys_reg="1", reg_generation="1",
            dyn_inst_seq="8", consumer_seq="8", lane_width="64",
            lane_offset="0", lane_mask="0x20", bit_indices="5",
            before="0x20", after="0x20", target_bits_flipped="1",
            same_generation="1", activated="0", install_event="0",
            state_before="cell_clean", state_after="affected_read"),
        chain_end(event_id="5", parent="3", tick="100",
                  post_overwrite_reads_total="1",
                  post_overwrite_reads_emitted="1",
                  post_overwrite_affected_reads="1",
                  post_overwrite_writes_total="0",
                  post_overwrite_writes_emitted="0",
                  post_overwrite_writes_affected="0",
                  generation_changes="0"),
    ]
    rep = analyze(tmp_path, events, fr01_expect())
    assert rep["masked_certification"]["certified"] is False
    assert any("affected read" in m
               for m in rep["containment"]["missing"])


def test_overwrite_after_read_before_commit(tmp_path):
    """A consumer read happened, but no commit: contained by a later write."""
    events = [
        root_fr01(),
        carrier(),
        read(event_id="2", parent="1", tick="20"),
        overwrite(event_id="3", parent="2", tick="30", sn="7"),
        chain_end(event_id="4", parent="3", write_exp="2", read_exp="1",
                  consumers="1", affected_sn="7"),
    ]
    rep = analyze(tmp_path, events, fr01_expect())
    assert rep["status"] == "PASS", rep["reason"]
    assert rep["lifecycle"]["closure"] == "overwritten"
    assert rep["lifecycle"]["events"]["overwrite_phase"] == \
        "after_consumer_reads_no_commit"
    assert rep["masked_certification"]["certified"] is False


def test_post_overwrite_read_fails(tmp_path):
    """The known emitter suppresses post-overwrite reads; if one appears the
    stream cannot be treated as a contained closure."""
    events = [
        root_fr01(),
        carrier(),
        overwrite(event_id="2", parent="1", tick="30", sn="7"),
        read(event_id="3", parent="2", tick="40"),
        chain_end(event_id="4", parent="3", write_exp="2", read_exp="1",
                  consumers="1", affected_sn="7"),
    ]
    rep = analyze(tmp_path, events, fr01_expect())
    assert rep["status"] == "FAIL"
    ph = check(rep, "overwrite_phase")
    assert ph["status"] == "FAIL"
    assert "after the overwrite tick" in ph["detail"]


def test_squash_closure_with_correct_terminal(tmp_path):
    events = [
        root_fr01(),
        carrier(),
        read(),
        squash(),
        chain_end(event_id="4", parent="3", terminal="squashed",
                   contained="0", outcome="run_end", read_exp="1",
                   write_exp="1", squash_events="1", consumers="1",
                   affected_sn="0"),
    ]
    rep = analyze(tmp_path, events, fr01_expect())
    assert rep["status"] == "PASS", rep["reason"]
    assert rep["lifecycle"]["closure"] == "squashed"
    assert rep["lifecycle"]["recorded_terminal"] == "squashed"
    assert rep["certification"]["status"] == "BLOCKED"
    assert "squash" in rep["certification"]["verdict"]


def test_squash_terminal_misclassification_fails(tmp_path):
    """finalizeVecTransient() currently emits exposed_unconsumed for a squash."""
    events = [
        root_fr01(),
        carrier(),
        read(),
        squash(),
        chain_end(event_id="4", parent="3", terminal="exposed_unconsumed",
                   contained="0", outcome="run_end", read_exp="1",
                   write_exp="1", squash_events="1", consumers="1",
                   affected_sn="0"),
    ]
    rep = analyze(tmp_path, events, fr01_expect())
    assert rep["status"] == "FAIL"
    th = check(rep, "terminal_honesty")
    assert th["status"] == "FAIL"
    assert "derive 'squashed'" in th["detail"]


def test_no_consumer_is_not_masked(tmp_path):
    events = [
        root_fr01(),
        carrier(),
        chain_end(event_id="2", parent="1", terminal="not_consumed",
                  contained="0", outcome="run_end", write_exp="1",
                  affected_sn="0"),
    ]
    rep = analyze(tmp_path, events, fr01_expect())
    assert rep["status"] == "PASS", rep["reason"]
    assert rep["lifecycle"]["closure"] == "not_consumed"
    assert rep["masked_certification"]["certified"] is False
    assert rep["masked_certification"]["verdict"] == "BLOCKED"
    assert rep["masked_certification"]["final_hash_equality_alone_insufficient"]


def test_committed_chain_is_certified(tmp_path):
    events = [
        root_fr01(),
        carrier(),
        read(event_id="2", parent="1"),
        commit(event_id="3", parent="2"),
        chain_end(event_id="4", parent="3", terminal="committed",
                  contained="0", outcome="errant_commit_seen",
                  read_exp="1", write_exp="1", commit_events="1",
                  consumers="1", affected_sn="0", first_impact_sn="50",
                  l5_witness="3"),
    ]
    rep = analyze(tmp_path, events, fr01_expect())
    assert rep["status"] == "PASS", rep["reason"]
    assert rep["lifecycle"]["closure"] == "committed"
    assert rep["certification"]["status"] == "CERTIFIED"
    assert rep["masked_certification"]["verdict"] == "NOT_MASKED"
    assert "oracle" in rep["certification"]["missing"][0]


# ---------------------------------------------------------------------------
# Lane / precision
# ---------------------------------------------------------------------------
def test_lane_width_mismatch_is_rejected(tmp_path):
    events = [
        root_fr01(lane_width="32", lane_offset="0", lane_mask="0x20",
                  bit_in_lane="5"),
        carrier(lw="32"),
        chain_end(lw="32"),
    ]
    rep = analyze(tmp_path, events, fr01_expect())  # expects lane_width=64
    assert rep["status"] == "FAIL"
    assert check(rep, "lane_identity")["status"] == "FAIL"
    assert check(rep, "config_conforms")["status"] == "FAIL"
    assert check(rep, "role_geometry")["status"] == "FAIL"


def test_precision_mismatch_is_rejected(tmp_path):
    events = [
        root_fr01(precision="fp64"),
        carrier(),
        chain_end(),
    ]
    rep = analyze(tmp_path, events, fr01_expect(precision="fp32"))
    assert rep["status"] == "FAIL"
    assert check(rep, "precision")["status"] == "FAIL"


def test_precision_not_emitted_is_evidence_missing(tmp_path):
    events = [
        root_fr01(precision=""),
        carrier(),
        chain_end(event_id="2", parent="1", terminal="not_consumed",
                  contained="0", outcome="run_end", write_exp="1",
                  affected_sn="0"),
    ]
    rep = analyze(tmp_path, events, fr01_expect(precision="fp64"))
    assert rep["status"] == "PASS", rep["reason"]
    assert check(rep, "precision")["status"] == "SKIP"
    assert "does not emit" in check(rep, "precision")["detail"]


def test_directed_lane_out_of_range_fails_closed(tmp_path):
    expect = fr01_expect(lane_offset=9)  # 128/64 == 2 lanes -> 9 is invalid
    log = ("VecFaultFailClosed: cycle=10000 model=FR01 phys=7 "
           "lane_width=64 lane_offset=9 bits=1 explicit_mask=0x20 "
           "reason=lane_offset_out_of_range (no injection; fault not "
           "consumed)\n")
    rep = analyze(tmp_path, [], expect, log=log,
                  stats=stats_text(**{
                      "board.chaos_phys.numFaultsInjected": 0,
                      "board.chaos_phys.numBitFlips": 0,
                  }))
    assert rep["status"] == "PASS", rep["reason"]
    assert rep["mode"] == "fail_closed"
    assert check(rep, "fail_closed_log")["status"] == "PASS"


# ---------------------------------------------------------------------------
# Consecutive writes / no permanent stuck
# ---------------------------------------------------------------------------
def test_consecutive_writes_do_not_restick(tmp_path):
    events = [
        root_fr01(),
        carrier(),
        overwrite(event_id="2", parent="1", sn="7", before="0x20",
                  after="0x40", full_after=HEX_40),
        overwrite(event_id="3", parent="2", sn="9", gen="2",
                  before="0x40", after="0x80", full_after=HEX_80),
        chain_end(event_id="4", parent="3", write_exp="3", affected_sn="9"),
    ]
    rep = analyze(tmp_path, events,
                  fr01_expect(allow_multiple_overwrites=True))
    assert rep["status"] == "PASS", rep["reason"]
    assert check(rep, "consecutive_writes_not_stuck")["status"] == "PASS"
    assert check(rep, "no_permanent_arm")["status"] == "PASS"


def test_reflip_between_writes_fails(tmp_path):
    events = [
        root_fr01(),
        carrier(),
        overwrite(event_id="2", parent="1", sn="7", before="0x20",
                  after="0x40", full_after=HEX_40),
        # before must be the previous written value 0x40; 0x60 re-applies the
        # flip (0x40 ^ 0x20), i.e. a permanent-stuck regression.
        overwrite(event_id="3", parent="2", sn="9", before="0x60",
                  after="0x80", full_after=HEX_80),
        chain_end(event_id="4", parent="3", write_exp="3", affected_sn="9"),
    ]
    rep = analyze(tmp_path, events,
                  fr01_expect(allow_multiple_overwrites=True))
    assert rep["status"] == "FAIL"
    assert check(rep, "consecutive_writes_not_stuck")["status"] == "FAIL"
    assert "re-applied" in check(rep, "consecutive_writes_not_stuck")["detail"]


def test_stuck_reapplied_event_fails(tmp_path):
    events = [
        root_fr01(),
        carrier(),
        overwrite(),
        evt(kind="stuck_reapplied", event_id="3", parent_event_id="2",
            tick="40", model_id="FR01", reg_class="vec", phys_reg="1",
            reg_generation="2"),
        chain_end(event_id="4", parent="3"),
    ]
    rep = analyze(tmp_path, events, fr01_expect())
    assert rep["status"] == "FAIL"
    np = check(rep, "no_permanent_arm")
    assert np["status"] == "FAIL"
    assert "stuck_reapplied" in np["detail"]


def test_second_overwrite_without_opt_in_fails(tmp_path):
    events = [
        root_fr01(),
        carrier(),
        overwrite(event_id="2", parent="1", sn="7"),
        overwrite(event_id="3", parent="2", sn="9", before="0x40",
                  after="0x80", full_after=HEX_80),
        chain_end(event_id="4", parent="3", write_exp="3", affected_sn="9"),
    ]
    rep = analyze(tmp_path, events, fr01_expect())
    assert rep["status"] == "FAIL"
    assert check(rep, "write_sequence")["status"] == "FAIL"


# ---------------------------------------------------------------------------
# Physical identity / evidence integrity
# ---------------------------------------------------------------------------
def test_phys_reg_mismatch_with_manifest_fails(tmp_path):
    events = [
        root_fr01(phys_reg="2"),
        carrier(),
        chain_end(),
    ]
    rep = analyze(tmp_path, events, fr01_expect(phys_reg=1))
    assert rep["status"] == "FAIL"
    assert check(rep, "config_conforms")["status"] == "FAIL"


def test_truncated_stream_fails(tmp_path):
    rep = analyze(tmp_path, [], fr01_expect(), bad_gzip=True)
    assert rep["status"] == "FAIL"
    assert check(rep, "stream_integrity")["status"] == "FAIL"


def test_missing_stats_is_skip_not_fail(tmp_path):
    """Missing evidence must be SKIP/evidence_missing, never a fabricated
    zero or a FAIL."""
    events = [
        root_fr01(),
        carrier(),
        chain_end(event_id="2", parent="1", terminal="not_consumed",
                  contained="0", outcome="run_end", write_exp="1",
                  affected_sn="0"),
    ]
    d = make_attempt(tmp_path, events, fr01_expect(), stats=None)
    rep = G.analyze_attempt(d)
    assert rep["status"] == "SKIP", rep["reason"]
    assert check(rep, "run_boundary")["status"] == "SKIP"
    assert check(rep, "permanent_counters")["status"] == "SKIP"
    assert rep["certification"]["status"] == "BLOCKED"


CONFIG_INI = """[board.chaos_phys]
type=CHAOSPhysReg
bitsToChange=1
faultMask=32
faultType=bit_flip
firstClock=10000
injectionMode=phys
lastClock=0
maxFaults=1
probability=1.0
regTargetClass=vector
requireAllocated=true
rngSeed=1
semanticRole=FR01-a
targetArchRegIdx=0
targetPhysRegIdx=1
vecLaneOffset=0
vecLaneWidth=64

[board.chaos_propagation]
type=CHAOSPropagation
runId=FSU-FR01-F0-W1
sampleRunId=s1

[board.processor.cores.core]
numPhysVecRegs=48
"""


def test_config_ini_only_expectations(tmp_path):
    events = [root_fr01(), carrier(), overwrite(), chain_end()]
    d = make_attempt(tmp_path, events, expect=None, stats=stats_text(),
                     log=install_log())
    (d / "config.ini").write_text(CONFIG_INI, encoding="utf-8")
    rep = G.analyze_attempt(d)
    assert rep["status"] == "PASS", rep["reason"]
    assert rep["expectations"]["bits"] == 1
    assert rep["expectations"]["fault_mask"] == 32
    assert rep["expectations"]["num_phys_vec_regs"] == 48
    assert rep["expectation_sources"]["lane_width"] == "config.ini"
    assert check(rep, "config_conforms")["status"] == "PASS"


# ---------------------------------------------------------------------------
# Real evidence (offline, already on disk)
# ---------------------------------------------------------------------------
@pytest.mark.skipif(not REAL_GATE.exists(),
                    reason="real FR01-FR02-F0-W1 gate evidence not present")
def test_real_gate_evidence_passes():
    report = G.analyze_path([REAL_GATE])
    assert report["summary"]["attempts_total"] == 11
    assert report["summary"]["PASS"] == 11
    assert report["summary"]["FAIL"] == 0
    assert report["summary"]["SKIP"] == 0
    by_name = {a["attempt"]: a for a in report["attempts"]}
    # seed2 is the only real write-overwrite closure in this gate.
    assert by_name["FR01-a/seed2"]["lifecycle"]["closure"] == "overwritten"
    assert by_name["FR02-c/seed2"]["lifecycle"]["closure"] == "overwritten"
    # Other seeds have no consumer and no write: UNKNOWN, never Masked.
    assert by_name["FR01-a/seed1"]["lifecycle"]["closure"] == "not_consumed"
    assert by_name["FR01-a/seed1"]["masked_certification"]["certified"] is False
    # The collision negative is a certified pre-injection rejection.
    neg = by_name["FR02-collision-neg"]
    assert neg["mode"] == "fail_closed"
    assert neg["certification"]["status"] == "CERTIFIED"
    # No real overwrite is certified as Masked.
    assert all(not a["masked_certification"]["certified"]
               for a in report["attempts"])
    assert report["summary"]["certification"]["CERTIFIED"] == 1
    assert report["summary"]["certification"]["BLOCKED"] == 10


def test_cli_exit_codes(tmp_path):
    ok = make_attempt(tmp_path, [root_fr01(), carrier(),
                                 chain_end(event_id="2", parent="1",
                                           terminal="not_consumed",
                                           contained="0", outcome="run_end",
                                           write_exp="1", affected_sn="0")],
                      fr01_expect(), name="ok", stats=stats_text())
    bad = make_attempt(tmp_path, [root_fr01()], fr01_expect(),
                       name="bad", stats=stats_text())
    out = tmp_path / "report.json"
    assert G.main([str(ok), "--json-out", str(out)]) == 0
    assert json.loads(out.read_text())["summary"]["PASS"] == 1
    assert G.main([str(bad), "--json-out", str(out)]) == 1
    assert G.main([str(tmp_path / "does-not-exist")]) == 2
