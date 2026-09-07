"""pytest for tools/diag/logparse.py (Task 4.2, plan §7.2).

Anchors (from the six core179 vmcore reports; raw logs at
/home/sdc/wangxu/vmcore0102/):
- 100% CPU179 concentration on the combined dumps (P1 > 60% HIT)
- 5/6+ reports hit the SAME instruction find_busiest_group+0x140
- ESR family 0x960000xx (DABT, L0/L3 translation faults)
- synthetic journalctl/messages forms parse too
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.join(HERE, "..", "tools", "diag", "logparse.py")
VMCORE_DIR = "/home/sdc/wangxu/vmcore0102"


def load():
    spec = importlib.util.spec_from_file_location("logparse", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _real_dumps():
    if not os.path.isdir(VMCORE_DIR):
        return []
    import glob
    return sorted(glob.glob(os.path.join(VMCORE_DIR, "*", "vmcore-dmesg.txt")))


def test_dmesg_warning_form():
    m = load()
    text = ("[104485.842931] WARNING: CPU: 179 PID: 10359 at arch/arm64/mm/fault.c:494 __do_kernel_fault+0x130/0x1b8\n"
            "[104485.843081] pc : __do_kernel_fault+0x130/0x1b8\n")
    evts = m.parse(text)
    assert evts and evts[0]["cpu"] == 179 and evts[0]["pid"] == 10359
    assert evts[0]["pc"] == "__do_kernel_fault+0x130/0x1b8"
    assert abs(evts[0]["ts"] - 104485.842931) < 1e-6


def test_oops_form_with_esr():
    m = load()
    text = ("[113997.450000] Unable to handle kernel paging request at virtual address 0036bc836a4a97df\n"
            "[113997.455264] CPU: 179 PID: 1986 Comm: kworker/179:1H Kdump: loaded\n"
            "[113997.488986] pc : find_busiest_group+0x140/0xb60\n"
            "[113997.489001] lr : find_busiest_group+0x11c/0xb60\n"
            "[113997.490000] ESR = 0x96000004: DABT(current EL)\n"
            "[113997.490100] x20: d93715ba0000ffff x19: ffff8000b722bb70\n")
    evts = m.parse(text)
    oops = [e for e in evts if e["kind"] == "Oops"]
    assert oops and oops[0]["cpu"] == 179
    assert oops[0]["esr"] == 0x96000004
    assert oops[0]["esr_decode"]["fsc"] == "0x04"
    assert oops[0]["pc"] == "find_busiest_group+0x140/0xb60"
    assert oops[0]["regs"]["x20"] == "d93715ba0000ffff"


def test_syslog_form():
    m = load()
    text = ("Aug 14 19:07:04 host kernel: WARNING: CPU: 179 PID: 1 at foo+0x1/0x2\n")
    evts = m.parse(text)
    assert evts and evts[0]["cpu"] == 179


def test_aggregate_concentration():
    m = load()
    text = ""
    for i in range(7):
        text += f"[{100+i}.0] WARNING: CPU: 179 PID: {i} at f+0x1\n"
    for i in range(3):
        text += f"[{200+i}.0] WARNING: CPU: 42 PID: {i} at f+0x1\n"
    agg = m.aggregate(m.parse(text))
    assert agg["n_anomalies"] == 10
    assert agg["top_core"] == 179 and agg["concentration"] == 0.7
    assert agg["P1_concentration_gt60pct"]


def test_uniform_distribution_P1_miss():
    m = load()
    text = ""
    for cpu in range(10):
        for i in range(2):
            text += f"[{100+cpu}.0] WARNING: CPU: {cpu} PID: {i} at f+0x1\n"
    agg = m.aggregate(m.parse(text))
    assert not agg["P1_concentration_gt60pct"]  # N1: uniform -> software


def test_real_core179_dumps():
    dumps = _real_dumps()
    if not dumps:
        import pytest
        pytest.skip("raw vmcore-dmesg dumps not present on this host")
    m = load()
    all_events = []
    per_file = []
    for fp in dumps:
        evts = m.parse(m.load_text(fp), source=fp)
        all_events.extend(evts)
        per_file.append(m.aggregate(evts))
    # SDC-signature subset: spurious translation faults + fatal Oops (the
    # general WARNING population includes unrelated software noise like the
    # 584-warning dump; the core179 family is defined by the spurious/Oops
    # signatures, per the six vmcore reports).
    sig = [e for e in all_events if e["kind"] in
           ("spurious_translation_fault", "Oops")]
    combined = m.aggregate(sig)
    # CPU179 convergence over the signature subset (P1). Events without a
    # CPU field (18 fatal Oops whose header line was separated by cut-here
    # banners) dilute the raw ratio honestly; among CPU-ATTRIBUTED events
    # the convergence is 216/217 = 99.5%.
    assert combined["top_core"] == 179
    assert combined["concentration"] > 0.85
    attributed = sum(combined["per_core"].values())
    assert attributed > 0 and combined["top_core_count"] / attributed > 0.99
    # same-instruction recurrence across the fatal cases
    assert combined["per_pc_symbol"].get("find_busiest_group+0x140/0xb60", 0) >= 5
    # ESR family: 0x960000xx DABT
    assert all(k.startswith("0x96000") for k in combined["esr_histogram"])
