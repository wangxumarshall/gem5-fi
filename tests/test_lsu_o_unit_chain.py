"""R6-O unit chain contract (O01/O02 monitor faults).

These tests pin the admission shape the O-unit emitter must produce:
  * the corrupted monitor is CONSUMED by the paired STXR, and the STXR
    failure is the containment witness at the unit's L3 consumption layer;
  * an injected-but-unconsumed monitor is NOT admissible (the matrix's
    activation clause);
  * stamping the STXR's own request id on the consumption nodes opens a
    sibling sub-chain (emitPropEvt's request-scoped cursor), orphaning L2/L3
    from the L0/L1 witnesses — the exact defect fixed on 2026-11-03.

Run: python3 -m pytest tests/test_lsu_o_unit_chain.py -q
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import lsu_chain_check as CC  # noqa: E402
import lsu_prop_fields as PF  # noqa: E402


def ev(**kw):
    base = {f: "" for f in PF.PROP_EVT_FIELDS}
    base.update({k: str(v) for k, v in kw.items()})
    return base


COMMON = dict(fault_id=1, sample_run_id="s1", run_id="O01-F0-W7")


def monitor_chain(stxr_request_id=1000, consumed=True):
    """inj L0 -> addr_form L1 -> exmon_monitor L1 -> exmon_rmw L2 -> exmon_stxr.

    stxr_request_id: the chain-owner id stamped on the STXR nodes. The fix
    uses the faulted LDXR's id (1000); the old defect used the STXR's own id
    (1002), which makes those nodes a sibling branch.
    """
    events = [
        ev(kind="inj", event_id=0, tick=100, dyn_inst_seq=1000,
           pa="835e9df0", cache_line="835e9dc0", corr="origin", **COMMON),
        ev(kind="addr_form", event_id=1, parent_event_id=0, tick=100,
           dyn_inst_seq=1000, pa="1000835e9df0", corr="origin", **COMMON),
        ev(kind="exmon_monitor", event_id=2, parent_event_id=1, tick=100,
           dyn_inst_seq=1000, request_id=1000, pa="835e9df0",
           va="835e9df0", before="835e9df0", after="1000835e9df0",
           field="o01_monitor_addr_bitflip", state_before="1",
           state_after="1", **COMMON),
        # Emitter-faithful parent: emitPropEvt's request-scoped cursor gives
        # a NEW stamped request no parent (no fabricated bridge). Only the
        # chain-owner request descends from the L1 witnesses.
        ev(kind="exmon_rmw", event_id=3,
           parent_event_id=(2 if stxr_request_id == 1000 else ""),
           tick=200, dyn_inst_seq=1002, request_id=stxr_request_id,
           pa="835e9df0", field="reservation_compare",
           state_before="reserved", state_after="mismatch_fail", **COMMON),
    ]
    if consumed:
        events.append(
            ev(kind="exmon_stxr", event_id=4, parent_event_id=3, tick=200,
               dyn_inst_seq=1002, request_id=stxr_request_id,
               pa="835e9df0", entry_index=1, field="stxr_consume",
               state_before="reserved", state_after="fail_retry",
               detection_layer="L3", contained=1,
               outcome="corrupted_monitor_blocks_sc", corr="addr_fallback",
               containment_layer="L3",
               containment_reason="sc_mismatch_against_corrupted_monitor",
               **COMMON))
    events.append(ev(kind="chain_end", event_id=5, tick=999,
                     detection_layer="None", contained=0,
                     outcome="run_end", corr="none", **COMMON))
    return events


def admit(events, activated=1, oracle="Masked"):
    cont = CC.containment_from_events(events, "O01-F0-W7", truncated=False)
    return CC.check_admission({
        "run_id": "O01-F0-W7", "activated": activated, "events": events,
        "rc": 0, "oracle_outcome": oracle, "containment": cont})


def test_consumed_monitor_is_contained_and_admitted():
    res = admit(monitor_chain())
    assert res["admitted"] is True, res["violations"]
    assert res["path"] == "contained"
    assert res["terminal"] == "detected_contained"
    assert res["violations"] == []


def test_unconsumed_monitor_is_not_admitted():
    # Injection happened, but no STXR ever consumed the corrupted monitor.
    res = admit(monitor_chain(consumed=False))
    assert res["admitted"] is False
    assert res["terminal"].startswith("provable_to_")


def test_stxr_own_request_id_orphans_the_consumption_nodes():
    # Old defect: request_id = the STXR's own seq -> sibling sub-chain.
    res = admit(monitor_chain(stxr_request_id=1002))
    assert res["admitted"] is False
    # The witness exists but cannot descend from the L0/L1 witnesses.
    assert CC.containment_from_events(
        monitor_chain(stxr_request_id=1002), "O01-F0-W7",
        truncated=False) is None
