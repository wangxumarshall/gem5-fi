"""pytest for tools/diag/sdc_diagnose.py (Task 4.3, plan §7.4–§7.6).

Anchors:
- core179 six-case replay -> HIGH confidence (P1+P2+P3+P4+P5, N3 miss),
  action = isolate + FA + RMA (plan §7.8)
- fabricated uniform-distribution evidence -> N1 EXCLUDED
- RAS-with-CPU-record -> N3 EXCLUDED (loud fault)
- medium path: P1+P2+P5 without P3/P4
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.join(HERE, "..", "tools", "diag", "sdc_diagnose.py")
VMCORE_DIR = "/home/sdc/wangxu/vmcore0102"

CORE179_EXTRA = {
    "reboot_unplanned_30d": 16,      # 16 kdump crashes in the window
    "ras_cpu_records": 0,
    "edac_ce_count": 0,
    "edac_ue_count": 0,
    "serror_with_valid_record": False,
}


def load():
    spec = importlib.util.spec_from_file_location("sdc_diagnose", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_core179_replay_high_confidence():
    if not os.path.isdir(VMCORE_DIR):
        import pytest
        pytest.skip("raw vmcore dumps not present")
    m = load()
    ev = m.evidence_from_logparse(VMCORE_DIR, CORE179_EXTRA)
    v = m.evaluate(ev)
    assert v["confidence"] == "HIGH"
    assert "隔离" in v["action"] and "FA" in v["action"]
    rules = {r["rule"] for r in v["rules_hit"]}
    assert {"P1", "P2", "P3", "P4", "P5"} <= rules
    assert all(r["rule"] != "N3" for r in v["rules_negative"])


def test_core179_evidence_dict_high_confidence():
    """Same verdict from a hand-built evidence dict (no raw logs needed)."""
    m = load()
    ev = {
        "n_anomalies": 88, "concentration": 1.0, "top_core": 179,
        "P2_multi_app_on_top_core": True,
        "esr_histogram": {"0x96000044": 40, "0x96000004": 48},
        "reboot_unplanned_30d": 6, "ras_cpu_records": 0,
        "edac_ce_count": 0, "edac_ue_count": 0,
    }
    v = m.evaluate(ev)
    assert v["confidence"] == "HIGH"
    rules = {r["rule"] for r in v["rules_hit"]}
    assert {"P1", "P2", "P3", "P4", "P5"} <= rules


def test_uniform_distribution_excluded_N1():
    m = load()
    ev = {
        "n_anomalies": 100, "concentration": 0.09, "top_core": 3,
        "P2_multi_app_on_top_core": False,
        "esr_histogram": {}, "reboot_unplanned_30d": 0,
        "ras_cpu_records": 0, "edac_ce_count": 0, "edac_ue_count": 0,
    }
    v = m.evaluate(ev)
    assert v["confidence"] == "EXCLUDED"
    assert any(r["rule"] == "N1" for r in v["rules_negative"])


def test_ras_loud_fault_excluded_N3():
    m = load()
    ev = {
        "n_anomalies": 50, "concentration": 0.9, "top_core": 5,
        "P2_multi_app_on_top_core": True,
        "esr_histogram": {"0x96000004": 50},
        "reboot_unplanned_30d": 8,
        "ras_cpu_records": 3,   # loud: RAS recorded CPU faults
        "edac_ce_count": 0, "edac_ue_count": 1,
    }
    v = m.evaluate(ev)
    assert v["confidence"] == "EXCLUDED"
    assert any(r["rule"] == "N3" for r in v["rules_negative"])


def test_medium_confidence_path():
    m = load()
    ev = {
        "n_anomalies": 30, "concentration": 0.7, "top_core": 12,
        "P2_multi_app_on_top_core": True,
        "esr_histogram": {},            # no P4 typed evidence
        "reboot_unplanned_30d": 0,      # no P3
        "ras_cpu_records": 0, "edac_ce_count": 0, "edac_ue_count": 0,
    }
    v = m.evaluate(ev)
    assert v["confidence"] == "MEDIUM"
    assert "延长观察" in v["action"] or "测试覆盖" in v["action"]
