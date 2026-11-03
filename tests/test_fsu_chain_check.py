"""tests/test_fsu_chain_check.py — FSU 传播链审计器（合成事件流，不运行 gem5）。"""
import gzip
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import fsu_chain_check as C
import fsu_prop_fields as P


def evt(**kw):
    d = {k: "" for k in P.PROP_EVT_FIELDS}
    d.update(kw)
    return P.PREFIX + " " + " ".join(f"{k}={d[k]}" for k in P.PROP_EVT_FIELDS)


def base(run="FSU-FP04-F0-W4", seed="s1", fid="1"):
    return dict(run_id=run, sample_run_id=seed, fault_id=fid, model_id="FP04")


def chain_full(t0=100):
    b = base()
    return [
        evt(kind="fault_applied", event_id="0", tick=str(t0), activated="1", **b),
        evt(kind="carrier_state", event_id="1", parent_event_id="0", tick=str(t0 + 1), **b),
        evt(kind="operand_read", event_id="2", parent_event_id="1", tick=str(t0 + 2), **b),
        evt(kind="execute", event_id="3", parent_event_id="2", tick=str(t0 + 3), **b),
        evt(kind="prf_writeback", event_id="4", parent_event_id="3", tick=str(t0 + 4), **b),
        evt(kind="commit", event_id="5", parent_event_id="4", tick=str(t0 + 5),
            detection_layer="L5", outcome="errant_commit",
            oracle_diff="hash_diff", **b),
    ]


def f5_root(event_id="0", sn="100", mask="0x0000000000000020",
            polarity="1", accounting=True, extra=None):
    b = base()
    fields = {}
    if accounting:
        # Install snapshot: exposure #1, no warm-up, its own post-install
        # window is exactly the installation event.
        fields.update({
            "eligible_seen_total": "1",
            "warmup_configured": "0",
            "warmup_eligible_skipped": "0",
            "install_eligible_ordinal": "1",
            "install_is_exposure": "1",
            "post_install_eligible": "1",
            "eligible_without_writable_dest": "0",
        })
    if extra:
        fields.update({k: str(v) for k, v in extra.items()})
    return evt(kind="fault_installed", event_id=event_id, tick="100",
               dyn_inst_seq=sn, first_eligible_sn=sn, fault_mask=mask,
               fixed_mask=mask, stuck_polarity=polarity,
               sample_policy="bounded_first_last(limit=4,first=2,last=2)",
               field="mant_lo", lane_width="64", lane_offset="0",
               **fields, **b)


def f5_exposure(event_id, parent, exposure_id, sn, activated,
                first_activated_sn="", mask="0x0000000000000020",
                polarity="1", activated_total="1"):
    b = base()
    # SA1 on bit5: correct_before=0 -> activated; 0x20 -> exposed-but-not.
    before = "0x0000000000000000" if activated == "1" \
        else "0x0000000000000020"
    return evt(kind="exposure", event_id=str(event_id),
               parent_event_id=str(parent), tick=str(100 + int(sn)),
               dyn_inst_seq=str(sn), install_event="0",
               exposure_id=str(exposure_id), exposure_count=str(exposure_id),
               activated_exposure_count=activated_total,
               first_activated_sn=first_activated_sn,
               last_exposure_sn=str(sn),
               affected_sn=(str(sn) if activated == "1" else ""),
               correct_before=before,
               stuck_after="0x0000000000000020",
               fixed_mask=mask, stuck_polarity=polarity,
               activated=activated, field="mant_lo",
               lane_width="64", lane_offset="0",
               sample_policy="bounded_first_last(limit=4,first=2,last=2)",
               **b)


def f5_chain_end(parent, total=3, sampled=2, dropped=1,
                 activated_total="1", first_activated_sn="102",
                 first_eligible_sn="100", last_exposure_sn="105",
                 terminal="committed", mask="0x0000000000000020",
                 polarity="1", accounting=True, extra=None):
    b = base()
    fields = {}
    if accounting:
        # Default: warm-up 0, install ordinal 1, every eligible event after
        # the warm-up is an exposure (no writable-dest misses). The census
        # reference is omitted unless a fixture asks for it.
        fields.update({
            "eligible_seen_total": str(total),
            "warmup_configured": "0",
            "warmup_eligible_skipped": "0",
            "install_eligible_ordinal": "1",
            "install_is_exposure": "1",
            "post_install_eligible": str(total),
            "eligible_without_writable_dest": "0",
            "sampled_unique": str(sampled),
            "omitted": str(dropped),
            "applied_to_all_exposures": "1",
            "sampled_is_observation_only": "1",
            "cell_sources_overflow": "0",
        })
    if extra:
        fields.update({k: str(v) for k, v in extra.items()})
    return evt(kind="chain_end", event_id="9", parent_event_id=str(parent),
               tick="9999", install_event="0", fault_mask=mask,
               fixed_mask=mask, stuck_polarity=polarity,
               first_eligible_sn=first_eligible_sn,
               exposure_count=str(total),
               activated_exposure_count=activated_total,
               first_activated_sn=first_activated_sn,
               last_exposure_sn=last_exposure_sn,
               exposures_total=str(total), exposures_sampled=str(sampled),
               exposures_dropped=str(dropped),
               sample_policy="bounded_first_last(limit=4,first=2,last=2)",
               terminal=terminal, outcome=terminal, **fields, **b)


def f5_full(t0=100):
    """One install, two exposures (one non-activated, one activated), the
    first activated exposure's real L2-L5 chain, and capacity accounting."""
    b = base()
    return [
        f5_root(),
        evt(kind="carrier_state", event_id="1", parent_event_id="0",
            tick="100", **b),
        f5_exposure(2, 1, 1, 101, "0", activated_total="0"),
        f5_exposure(3, 1, 2, 102, "1", first_activated_sn="102",
                    activated_total="1"),
        evt(kind="operand_read", event_id="4", parent_event_id="3",
            tick="202", dyn_inst_seq="102", activated="1", **b),
        evt(kind="execute", event_id="5", parent_event_id="4",
            tick="203", dyn_inst_seq="102", **b),
        evt(kind="prf_writeback", event_id="6", parent_event_id="5",
            tick="204", dyn_inst_seq="102", **b),
        evt(kind="commit", event_id="7", parent_event_id="6", tick="205",
            dyn_inst_seq="102", detection_layer="L5",
            outcome="errant_commit", **b),
        f5_chain_end(7, total=3, sampled=2, dropped=1,
                     activated_total="1", first_activated_sn="102"),
    ]


def f5_accounted(root_extra=None, end_extra=None, operand_extra=None,
                 activated_total="1", accounting=True):
    """f5_full() plus the optional eligible/sampling accounting fields."""
    b = base()
    op = dict(kind="operand_read", event_id="4", parent_event_id="3",
              tick="202", dyn_inst_seq="102", activated="1")
    if operand_extra:
        op.update(operand_extra)
    return [
        f5_root(accounting=accounting, extra=root_extra),
        evt(kind="carrier_state", event_id="1", parent_event_id="0",
            tick="100", **b),
        f5_exposure(2, 1, 1, 101, "0", activated_total="0"),
        f5_exposure(3, 1, 2, 102, "1", first_activated_sn="102",
                    activated_total="1"),
        evt(**op, **b),
        evt(kind="execute", event_id="5", parent_event_id="4",
            tick="203", dyn_inst_seq="102", **b),
        evt(kind="prf_writeback", event_id="6", parent_event_id="5",
            tick="204", dyn_inst_seq="102", **b),
        evt(kind="commit", event_id="7", parent_event_id="6", tick="205",
            dyn_inst_seq="102", detection_layer="L5",
            outcome="errant_commit", **b),
        f5_chain_end(7, total=3, sampled=2, dropped=1,
                     activated_total=activated_total,
                     first_activated_sn="102", accounting=accounting,
                     extra=end_extra),
    ]


def write(tmp_path, lines, name="ev.txt", gz=False):
    p = tmp_path / name
    text = "\n".join(lines) + "\n"
    if gz:
        p.write_bytes(gzip.compress(text.encode()))
    else:
        p.write_text(text, encoding="utf-8")
    return p


def check(tmp_path, lines, **kw):
    p = write(tmp_path, lines, **{k: v for k, v in kw.items() if k in ("name", "gz")})
    return C.check_stream(p, **{k: v for k, v in kw.items() if k in ("run_id", "sample_run_id")})


# ---------- parser ----------

def test_parse_line_and_layers():
    line = evt(kind="fault_applied", event_id="0", tick="7", run_id="FSU-X-F0-W1")
    e = P.parse_line(line)
    assert e["kind"] == "fault_applied" and e["tick"] == "7"
    assert P.parse_line("plain text") is None
    e2 = P.parse_line("PROP-EVT: kind=execute event_id=3 tick=9 model_id=FP04")
    assert e2["kind"] == "execute" and e2["model_id"] == "FP04"
    assert P.layer_of(e2) == "L3"
    assert P.layer_of(e) == "L0"
    assert P.layer_of({"kind": "commit"}) == "L5"
    assert P.layer_of({"kind": "chain_end"}) is None
    assert P.layer_of({"kind": "contain", "detection_layer": "L3"}) == "L3"
    assert P.layer_of({"kind": "contain"}) is None


# ---------- full / contained ----------

def test_full_chain_admitted(tmp_path):
    r = check(tmp_path, chain_full())
    f = r["faults"]["1"]
    assert f["terminal"] == "full"
    assert f["layers"] == ["L0", "L1", "L2", "L3", "L4", "L5"]
    assert f["l5_witness_event_id"] == "5"
    assert f["layers_na"] == []
    assert f["beyond"] == "N/A"
    assert f["violations"] == []
    assert f["admitted"] is True
    assert r["admitted_faults"] == ["1"]


def test_contained_at_L3(tmp_path):
    b = base()
    lines = [
        evt(kind="fault_applied", event_id="0", tick="100", activated="1", **b),
        evt(kind="carrier_state", event_id="1", parent_event_id="0", tick="101", **b),
        evt(kind="operand_read", event_id="2", parent_event_id="1", tick="102", **b),
        evt(kind="execute", event_id="3", parent_event_id="2", tick="103", **b),
        evt(kind="contain", event_id="4", parent_event_id="3", tick="104",
            detection_layer="L3", contained="1", outcome="recovered", **b),
    ]
    f = check(tmp_path, lines)["faults"]["1"]
    assert f["terminal"] == "contained_L3"
    assert f["containment_layer"] == "L3"
    assert f["beyond"] == "N/A"
    assert f["layers_na"] == ["L4", "L5"]
    assert f["admitted"] is True
    assert "L4" not in f["layers"] and "L5" not in f["layers"]


def test_explicit_mask_is_not_unknown(tmp_path):
    b = base()
    lines = [
        evt(kind="fault_applied", event_id="0", tick="100", activated="1", **b),
        evt(kind="carrier_state", event_id="1", parent_event_id="0", tick="101", **b),
        evt(kind="mask", event_id="2", parent_event_id="1", tick="102",
            detection_layer="L1", contained="1", outcome="masked", **b),
    ]
    f = check(tmp_path, lines)["faults"]["1"]
    assert f["terminal"] == "contained_L1"
    assert f["admitted"] is True


def test_not_activated_is_not_contained(tmp_path):
    b = base()
    lines = [
        evt(kind="fault_applied", event_id="0", tick="100", activated="0", **b),
        evt(kind="carrier_state", event_id="1", parent_event_id="0", tick="101", **b),
    ]
    f = check(tmp_path, lines)["faults"]["1"]
    assert f["terminal"] == "not_activated"
    assert f["admitted"] is False


def test_not_activated_event_terminal(tmp_path):
    b = base()
    lines = [
        evt(kind="fault_applied", event_id="0", tick="100", **b),
        evt(kind="carrier_state", event_id="1", parent_event_id="0", tick="101", **b),
        evt(kind="not_activated", event_id="2", parent_event_id="1", tick="102",
            activated="0", **b),
    ]
    f = check(tmp_path, lines)["faults"]["1"]
    assert f["terminal"] == "not_activated"
    assert f["admitted"] is False


# ---------- 负向 ----------

def test_missing_parent_rejected(tmp_path):
    b = base()
    lines = chain_full()
    lines[2] = evt(kind="operand_read", event_id="2", parent_event_id="99",
                   tick="102", **b)
    f = check(tmp_path, lines)["faults"]["1"]
    assert any(v.startswith("orphan_parent:2->99") for v in f["violations"])
    assert f["admitted"] is False


def test_tick_regression_rejected(tmp_path):
    lines = chain_full()
    lines[2] = evt(kind="operand_read", event_id="2", parent_event_id="1",
                   tick="50", **base())
    f = check(tmp_path, lines)["faults"]["1"]
    assert any(v.startswith("tick_regression:2") for v in f["violations"])
    assert f["admitted"] is False


def test_layer_regression_rejected(tmp_path):
    b = base()
    lines = [
        evt(kind="fault_applied", event_id="0", tick="100", activated="1", **b),
        evt(kind="execute", event_id="1", parent_event_id="0", tick="101", **b),
        evt(kind="carrier_state", event_id="2", parent_event_id="1", tick="102", **b),
    ]
    f = check(tmp_path, lines)["faults"]["1"]
    assert "layer_regression" in f["violations"]
    assert f["admitted"] is False


def test_chain_end_cannot_impersonate_l5(tmp_path):
    b = base()
    lines = [
        evt(kind="fault_applied", event_id="0", tick="100", activated="1", **b),
        evt(kind="carrier_state", event_id="1", parent_event_id="0", tick="101", **b),
        evt(kind="chain_end", event_id="2", parent_event_id="1", tick="102",
            detection_layer="L5", outcome="errant_commit_seen", **b),
    ]
    f = check(tmp_path, lines)["faults"]["1"]
    assert f["terminal"] == "provable_to_L1_then_unknown"
    assert f["beyond"] == "Unknown"
    assert any(v.startswith("chain_end_claimed_l5") for v in f["violations"])
    assert f["admitted"] is False


def test_l5_without_witness_rejected(tmp_path):
    lines = chain_full()
    b = base()
    lines[5] = evt(kind="commit", event_id="5", parent_event_id="4", tick="105",
                   detection_layer="L5", outcome="", **b)
    f = check(tmp_path, lines)["faults"]["1"]
    assert any(v.startswith("l5_without_witness:5") for v in f["violations"])
    assert f["terminal"] != "full"
    assert f["admitted"] is False


def test_missing_L2_is_full_with_na(tmp_path):
    """真实未到达的 L2 记 N/A，不算跳接凑层；L0/L1/L5 齐全仍为 full。"""
    b = base()
    lines = [
        evt(kind="fault_applied", event_id="0", tick="100", activated="1", **b),
        evt(kind="carrier_state", event_id="1", parent_event_id="0", tick="101", **b),
        evt(kind="execute", event_id="2", parent_event_id="1", tick="102", **b),
        evt(kind="prf_writeback", event_id="3", parent_event_id="2", tick="103", **b),
        evt(kind="commit", event_id="4", parent_event_id="3", tick="104",
            detection_layer="L5", outcome="errant_commit", **b),
    ]
    f = check(tmp_path, lines)["faults"]["1"]
    assert f["terminal"] == "full"
    assert f["layers_na"] == ["L2"]
    assert f["admitted"] is True


def test_missing_carrier_not_full(tmp_path):
    b = base()
    lines = [
        evt(kind="fault_applied", event_id="0", tick="100", activated="1", **b),
        evt(kind="execute", event_id="1", parent_event_id="0", tick="101", **b),
        evt(kind="prf_writeback", event_id="2", parent_event_id="1", tick="102", **b),
        evt(kind="commit", event_id="3", parent_event_id="2", tick="103",
            detection_layer="L5", outcome="errant_commit", **b),
    ]
    f = check(tmp_path, lines)["faults"]["1"]
    assert f["terminal"].startswith("provable_to_L5_then_unknown")
    assert "incomplete_carrier_sequence" in f["violations"]
    assert f["admitted"] is False


def test_branch_is_off_chain(tmp_path):
    b = base()
    lines = chain_full() + [
        evt(kind="carrier_state", event_id="b1", parent_event_id="0",
            tick="101", **b),
    ]
    f = check(tmp_path, lines)["faults"]["1"]
    assert f["terminal"] == "full"
    assert "b1" in f["off_chain_event_ids"]
    assert "b1" not in f["path_event_ids"]


def test_duplicate_event_id_rejected(tmp_path):
    b = base()
    lines = [
        evt(kind="fault_applied", event_id="0", tick="100", activated="1", **b),
        evt(kind="carrier_state", event_id="1", parent_event_id="0", tick="101", **b),
        evt(kind="operand_read", event_id="1", parent_event_id="0", tick="102", **b),
    ]
    f = check(tmp_path, lines)["faults"]["1"]
    assert any(v.startswith("duplicate_event_id:1") for v in f["violations"])
    assert f["admitted"] is False


def test_cross_seed_identity_rejected(tmp_path):
    r = check(tmp_path, chain_full(), sample_run_id="s2")
    f = r["faults"]["1"]
    assert r["identity_violations"]
    assert f["admitted"] is False


def test_wrong_run_id_rejected(tmp_path):
    r = check(tmp_path, chain_full(), run_id="FSU-OTHER-F0-W4")
    assert r["identity_violations"]
    assert r["admitted_faults"] == []


# ---------- 截断 / 容量 ----------

def test_truncated_gzip_detected(tmp_path):
    p = write(tmp_path, chain_full(), name="ev.txt.gz", gz=True)
    data = p.read_bytes()
    p.write_bytes(data[:-12])           # 破坏 gzip 尾部/CRC
    events, truncated, reason = P.read_stream(p)
    assert truncated is True
    assert reason


def test_truncation_blocks_admission(tmp_path, monkeypatch):
    p = write(tmp_path, chain_full())
    orig = P.read_stream
    monkeypatch.setattr(P, "read_stream",
                        lambda _p: (orig(p)[0], True, "forced"))
    r = C.check_stream(p)
    assert r["truncated"] is True
    assert r["admitted_faults"] == []
    assert any("truncated_stream" in f["violations"] for f in r["faults"].values())


def test_event_cap_marks_truncated(tmp_path, monkeypatch):
    p = write(tmp_path, chain_full())
    monkeypatch.setattr(P, "EVENT_CAP", 2)
    events, truncated, reason = P.read_stream(p)
    assert len(events) == 2
    assert truncated is True
    assert reason.startswith("event_cap_exceeded")


# ---------- [FSU][F5] one permanent fault, many exposures ----------

def test_f5_layer_mapping():
    assert P.layer_of({"kind": "fault_installed"}) == "L0"
    assert P.layer_of({"kind": "exposure"}) is None
    assert P.layer_of({"kind": "activation"}) == "L2"
    assert P.layer_of({"kind": "first_impact"}) == "L5"
    assert P.layer_of({"kind": "chain_end"}) is None


def test_f5_full_chain_admitted(tmp_path):
    r = check(tmp_path, f5_full())
    assert r["fault_count"] == 1
    assert r["admitted_faults"] == ["1"]
    f = r["faults"]["1"]
    assert f["terminal"] == "full"
    assert f["layers"] == ["L0", "L1", "L2", "L3", "L4", "L5"]
    assert f["violations"] == []
    assert f["admitted"] is True
    assert f["f5"]["exposures_total"] == 3
    assert f["f5"]["exposures_sampled"] == 2
    assert f["f5"]["exposures_dropped"] == 1
    assert f["f5"]["activated_exposure_count"] == 1
    # The non-activated exposure is branch evidence, not a fault.
    assert "2" in f["off_chain_event_ids"]
    assert "3" in f["path_event_ids"]      # first activated exposure


def test_f5_many_exposures_are_one_fault(tmp_path):
    b = base()
    lines = [f5_root(), evt(kind="carrier_state", event_id="1",
                            parent_event_id="0", tick="100", **b)]
    # 20 sampled exposures of the SAME fault_id: still one fault.
    for i in range(20):
        lines.append(f5_exposure(10 + i, 1, i + 1, 200 + i,
                                 "0" if i % 2 else "1",
                                 first_activated_sn="200",
                                 activated_total="10"))
    lines.append(f5_chain_end(29, total=20000, sampled=20, dropped=19980,
                              activated_total="10",
                              first_activated_sn="200",
                              last_exposure_sn="20199",
                              terminal="exposed_unconsumed"))
    r = check(tmp_path, lines)
    assert r["fault_count"] == 1
    assert r["faults"]["1"]["f5"]["exposures_total"] == 20000
    assert r["faults"]["1"]["f5"]["exposures_sampled"] == 20
    assert r["faults"]["1"]["f5"]["exposures_dropped"] == 19980


def test_f5_exposure_without_install_is_not_a_fault(tmp_path):
    lines = [f5_exposure(0, 1, 1, 101, "0", activated_total="0")]
    r = check(tmp_path, lines)
    assert r["fault_count"] == 0
    assert r["faults"] == {}
    assert r["orphan_exposure_violations"]
    assert r["admitted"] is False


def test_f5_multiple_install_roots_rejected(tmp_path):
    b = base()
    lines = [
        f5_root(),
        f5_root(event_id="10"),
        evt(kind="carrier_state", event_id="1", parent_event_id="0",
            tick="100", **b),
    ]
    f = check(tmp_path, lines)["faults"]["1"]
    assert "multiple_fault_installed_roots" in f["violations"]
    assert f["admitted"] is False


def test_f5_exposure_wrong_install_event_rejected(tmp_path):
    lines = f5_full()
    lines[3] = f5_exposure(3, 1, 2, 102, "1", first_activated_sn="102",
                           activated_total="1")
    lines[3] = lines[3].replace("install_event=0", "install_event=77")
    f = check(tmp_path, lines)["faults"]["1"]
    assert any(v.startswith("exposure_wrong_install_event:3")
               for v in f["violations"])
    assert f["admitted"] is False


def test_f5_stuck_apply_is_audited(tmp_path):
    """The event stream itself must prove forced SA1, not XOR/random."""
    lines = f5_full()
    lines[2] = lines[2].replace(
        "stuck_after=0x0000000000000020",
        "stuck_after=0x0000000000000000")
    f = check(tmp_path, lines)["faults"]["1"]
    assert any(v.startswith("f5_stuck_apply_mismatch:2")
               for v in f["violations"])
    assert f["admitted"] is False


def test_f5_capacity_mismatch_rejected(tmp_path):
    lines = f5_full()
    lines[-1] = f5_chain_end(7, total=3, sampled=2, dropped=7,
                              activated_total="1", first_activated_sn="102")
    f = check(tmp_path, lines)["faults"]["1"]
    assert any(v.startswith("f5_capacity_mismatch")
               for v in f["violations"])
    assert f["admitted"] is False


def test_f5_sampled_mismatch_rejected(tmp_path):
    lines = f5_full()
    lines[-1] = f5_chain_end(7, total=3, sampled=9, dropped=0,
                              activated_total="1", first_activated_sn="102")
    f = check(tmp_path, lines)["faults"]["1"]
    # total == sampled + dropped would also fail, but the observed-sample
    # count is an independent check.
    assert any(v.startswith("f5_sampled_mismatch")
               or v.startswith("f5_capacity_mismatch")
               for v in f["violations"])
    assert f["admitted"] is False


def test_f5_activation_chain_must_pass_exposure(tmp_path):
    """A commit hanging directly off L1 bypasses the first activated
    exposure and must not certify the activation chain."""
    lines = f5_full()
    lines[4] = evt(kind="operand_read", event_id="4", parent_event_id="1",
                   tick="202", dyn_inst_seq="102", activated="1", **base())
    f = check(tmp_path, lines)["faults"]["1"]
    assert "activation_chain_not_through_first_activated" in f["violations"]
    assert f["admitted"] is False


def test_f5_no_activation_is_not_activated(tmp_path):
    b = base()
    lines = [
        f5_root(),
        evt(kind="carrier_state", event_id="1", parent_event_id="0",
            tick="100", **b),
        f5_exposure(2, 1, 1, 101, "0", activated_total="0"),
        f5_chain_end(2, total=1, sampled=1, dropped=0,
                     activated_total="0", first_activated_sn="",
                     last_exposure_sn="101", terminal="not_activated"),
    ]
    f = check(tmp_path, lines)["faults"]["1"]
    assert f["terminal"] == "not_activated"
    assert f["admitted"] is False


def test_f5_activated_without_commit_is_honest_unknown(tmp_path):
    b = base()
    lines = [
        f5_root(),
        evt(kind="carrier_state", event_id="1", parent_event_id="0",
            tick="100", **b),
        f5_exposure(2, 1, 1, 101, "1", first_activated_sn="101",
                    activated_total="1"),
        f5_chain_end(2, total=2, sampled=1, dropped=1,
                     activated_total="1", first_activated_sn="101",
                     last_exposure_sn="102", terminal="exposed_unconsumed"),
    ]
    f = check(tmp_path, lines)["faults"]["1"]
    assert f["terminal"] == "exposed_unconsumed"
    assert f["beyond"] == "Unknown"
    assert f["admitted"] is False


def test_f5_chain_end_cannot_claim_commit_without_l5(tmp_path):
    b = base()
    lines = [
        f5_root(),
        evt(kind="carrier_state", event_id="1", parent_event_id="0",
            tick="100", **b),
        f5_exposure(2, 1, 1, 101, "1", first_activated_sn="101",
                    activated_total="1"),
        f5_chain_end(2, total=1, sampled=1, dropped=0,
                     activated_total="1", first_activated_sn="101",
                     last_exposure_sn="101", terminal="committed"),
    ]
    f = check(tmp_path, lines)["faults"]["1"]
    assert "f5_chain_end_claims_commit_without_l5" in f["violations"]
    assert f["admitted"] is False


def test_f5_truncated_stream_blocks_admission(tmp_path, monkeypatch):
    p = write(tmp_path, f5_full())
    orig = P.read_stream
    monkeypatch.setattr(P, "read_stream",
                        lambda _p: (orig(p)[0], True, "forced"))
    r = C.check_stream(p)
    assert r["truncated"] is True
    assert r["admitted_faults"] == []
    assert any("truncated_stream" in f["violations"]
               for f in r["faults"].values())


# ---------- [FSU][F5] hardened counting / sampling / multi-source ----------

def test_f5_accounting_fields_conserved(tmp_path):
    f = check(tmp_path, f5_accounted())["faults"]["1"]
    assert f["violations"] == []
    assert f["admitted"] is True
    acc = f["f5"]
    assert acc["eligible_seen_total"] == 3
    assert acc["warmup_eligible_skipped"] == 0
    assert acc["post_install_eligible"] == 3
    assert acc["install_eligible_ordinal"] == 1
    assert acc["exposures_total"] == acc["sampled_unique"] + acc["omitted"]
    assert acc["sampled_unique"] == 2
    assert acc["unique_exposure_ids"] == 2


def test_f5_warmup_one_install_ordinal_and_conservation(tmp_path):
    root = {"warmup_configured": 1, "warmup_eligible_skipped": 1,
            "install_eligible_ordinal": 2, "eligible_seen_total": 2,
            "post_install_eligible": 1}
    end = {"warmup_configured": 1, "warmup_eligible_skipped": 1,
           "install_eligible_ordinal": 2, "eligible_seen_total": 4,
           "post_install_eligible": 3}
    f = check(tmp_path, f5_accounted(root_extra=root,
                                     end_extra=end))["faults"]["1"]
    assert f["violations"] == []
    assert f["admitted"] is True
    assert f["f5"]["install_eligible_ordinal"] == 2
    assert f["f5"]["warmup_eligible_skipped"] == 1
    assert f["f5"]["eligible_seen_total"] == 4


def test_f5_warmup_beyond_eligible_emits_no_fault(tmp_path):
    # warm-up > eligible: the run ends before installation, so the injector
    # emits no fault_installed root and no chain_end. The checker must not
    # invent a permanent fault or fabricate accounting from nothing.
    r = check(tmp_path, [])
    assert r["fault_count"] == 0
    assert r["faults"] == {}
    assert r["admitted"] is False


def test_f5_install_ordinal_must_be_warmup_plus_one(tmp_path):
    end = {"install_eligible_ordinal": 3, "warmup_configured": 1,
           "warmup_eligible_skipped": 1, "eligible_seen_total": 4,
           "post_install_eligible": 3}
    f = check(tmp_path, f5_accounted(end_extra=end))["faults"]["1"]
    assert any(v.startswith("f5_install_ordinal_mismatch")
               for v in f["violations"])
    assert f["admitted"] is False


def test_f5_install_is_exposure_flag(tmp_path):
    end = {"install_is_exposure": 0}
    f = check(tmp_path, f5_accounted(end_extra=end))["faults"]["1"]
    assert any(v.startswith("f5_install_is_exposure_not_1")
               for v in f["violations"])
    assert f["admitted"] is False


def test_f5_post_install_conservation_mismatch(tmp_path):
    end = {"post_install_eligible": 5}
    f = check(tmp_path, f5_accounted(end_extra=end))["faults"]["1"]
    assert any(v.startswith("f5_eligible_seen_mismatch")
               for v in f["violations"])
    assert any(v.startswith("f5_post_install_mismatch")
               for v in f["violations"])
    assert f["admitted"] is False


def test_f5_sampled_unique_must_match_unique_exposure_ids(tmp_path):
    end = {"sampled_unique": 3}
    f = check(tmp_path, f5_accounted(end_extra=end))["faults"]["1"]
    assert any(v.startswith("f5_sampled_unique_mismatch")
               for v in f["violations"])
    assert any(v.startswith("f5_sampled_unique_disagrees_sampled")
               for v in f["violations"])
    assert f["admitted"] is False


def test_f5_first_last_overlap_is_counted_once(tmp_path):
    # Two exposures total, but only one event is in the stream: the first
    # and last sample policies selected the SAME exposure_id. It must count
    # once (sampled_unique=1), never twice.
    b = base()
    lines = [
        f5_root(),
        evt(kind="carrier_state", event_id="1", parent_event_id="0",
            tick="100", **b),
        f5_exposure(2, 1, 1, 101, "1", first_activated_sn="101",
                    activated_total="1"),
        f5_chain_end(2, total=2, sampled=1, dropped=1,
                     activated_total="1", first_activated_sn="101",
                     last_exposure_sn="102", terminal="exposed_unconsumed"),
    ]
    f = check(tmp_path, lines)["faults"]["1"]
    assert f["violations"] == []
    assert f["f5"]["unique_exposure_ids"] == 1
    assert f["f5"]["sampled_unique"] == 1
    assert f["f5"]["exposures_total"] == 2


def test_f5_duplicate_exposure_id_is_not_double_counted(tmp_path):
    lines = f5_accounted()
    lines[3] = lines[3].replace("exposure_id=2", "exposure_id=1")
    f = check(tmp_path, lines)["faults"]["1"]
    assert "duplicate_exposure_id" in f["violations"]
    assert any(v.startswith("f5_sampled_mismatch")
               for v in f["violations"])
    assert f["f5"]["unique_exposure_ids"] == 1
    assert f["admitted"] is False


def test_f5_census_delta_is_arithmetic_not_equality(tmp_path):
    # A fault-run eligible total of 3 vs a pre-registered census of 100 is
    # NOT an error, as long as the delta is recorded correctly.
    ok = {"selected_eligible_total": 100,
          "eligible_delta_vs_census": -97,
          "census_reference": "pre_registered_countOnly"}
    f = check(tmp_path, f5_accounted(end_extra=ok))["faults"]["1"]
    assert f["violations"] == []
    assert f["admitted"] is True
    assert f["f5"]["eligible_delta_vs_census"] == -97

    bad = dict(ok, eligible_delta_vs_census=-96)
    f = check(tmp_path, f5_accounted(end_extra=bad))["faults"]["1"]
    assert any(v.startswith("f5_census_delta_mismatch")
               for v in f["violations"])
    assert f["admitted"] is False

    no_ref = {"selected_eligible_total": 100,
              "eligible_delta_vs_census": -97}
    f = check(tmp_path, f5_accounted(end_extra=no_ref))["faults"]["1"]
    assert "f5_missing_census_reference" in f["violations"]
    assert f["admitted"] is False


def test_f5_multi_source_summary_is_bounded(tmp_path):
    op = {"merged_activated_exposures": 2,
          "observed_exposure_ids": "2:3",
          "sources_expanded": 1, "sources_unexpanded": 1,
          "observation_scope": "first_activated_chain"}
    f = check(tmp_path, f5_accounted(operand_extra=op,
                                     activated_total="2"))["faults"]["1"]
    assert f["violations"] == []
    assert f["admitted"] is True

    # The summary must account for every merged source exactly once: one
    # expanded + the rest unexpanded.
    bad = dict(op, sources_unexpanded=0)
    f = check(tmp_path, f5_accounted(operand_extra=bad,
                                     activated_total="2"))["faults"]["1"]
    assert any(v.startswith("f5_multi_source_mismatch")
               for v in f["violations"])
    assert f["admitted"] is False


def test_f5_observation_only_flags_are_explicit(tmp_path):
    end = {"applied_to_all_exposures": 0,
           "sampled_is_observation_only": 0}
    f = check(tmp_path, f5_accounted(end_extra=end))["faults"]["1"]
    assert any(v.startswith("f5_flag_not_1")
               for v in f["violations"])
    assert f["admitted"] is False


def test_f5_legacy_fixture_without_new_fields_still_passes(tmp_path):
    # Old certified evidence has none of the new fields; it must keep
    # passing (the new checks are conditional on field presence).
    f = check(tmp_path, f5_accounted(accounting=False))["faults"]["1"]
    assert f["violations"] == []
    assert f["admitted"] is True
    assert f["f5"]["eligible_seen_total"] is None
