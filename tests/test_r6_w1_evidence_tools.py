"""R6-S W1 evidence/doc tooling: parsing + end-to-end audit on the canary."""
import gzip
import json
import os
import subprocess
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "tools"))
import r6_w1_evidence as ev  # noqa: E402

CANARY = ev.CANARY_ROOT


def test_scan_events_counts_and_capture(tmp_path):
    p = tmp_path / "prop_evt.txt.gz"
    lines = [
        "PROP-EVT: kind=inj fault_id=1 event_id=0 parent_event_id= tick=10 ",
        "PROP-EVT: kind=sq_entry fault_id=1 event_id=1 parent_event_id=0 tick=10 ",
        "PROP-EVT: kind=consumer fault_id=1 event_id=2 parent_event_id=1 tick=11 ",
        "PROP-EVT: kind=chain_end fault_id=1 event_id=3 parent_event_id=2 tick=12 ",
    ]
    with gzip.open(p, "wt") as f:
        f.write("\n".join(lines) + "\n")
    out = ev.scan_events(str(p), wanted_ids=["0", "1"])
    assert out["count"] == 4
    assert out["kind_counts"] == {"inj": 1, "sq_entry": 1, "consumer": 1,
                                  "chain_end": 1}
    # wanted ids + the lifecycle whitelist are captured, plain consumer is not
    assert set(out["captured"]) == {"0", "1", "3"}
    assert out["nonmonotonic_tick"] == 0


def test_injection_log_and_funnel_parsing(tmp_path):
    log = tmp_path / "lsq_fwd_injections.log"
    log.write_text(
        "Cycle: 42, CPU: core, Site: store->load_forward, FaultType: bit_flip, "
        "Vaddr: 0xdead0, FwdSize: 8, ByteOffset: 1, Mask: 00000010, "
        "StoreSeq: 7, SqIdx: 8, LoadSeq: 9, LqIdx: 10\n"
        "CHAOS_L0_FUNNEL: CHAOSLSQFwd attempted=100 eligible=90 injected=1 activated=1\n")
    rows = ev.parse_injection_log(str(log))
    assert rows == [{"Cycle": "42", "CPU": "core", "Site": "store->load_forward",
                     "FaultType": "bit_flip", "Vaddr": "0xdead0", "FwdSize": "8",
                     "ByteOffset": "1", "Mask": "00000010", "StoreSeq": "7",
                     "SqIdx": "8", "LoadSeq": "9", "LqIdx": "10"}]
    f = ev.parse_funnel_line(log.read_text())
    assert f == {"attempted": 100, "eligible": 90, "injected": 1, "activated": 1}


needs_canary = pytest.mark.skipif(
    not os.path.isfile(os.path.join(CANARY, "manifest.json")),
    reason="canary evidence not present on this host")


@needs_canary
def test_canary_passes_evidence_audit(tmp_path):
    out = tmp_path / "audit"
    r = subprocess.run([sys.executable,
                        os.path.join(REPO, "tools", "audit_r6_w1_evidence.py"),
                        "--root", CANARY, "--out", str(out)],
                       capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, r.stdout + r.stderr
    rec = json.loads((out / "R6S_W1_EVIDENCE_AUDIT.jsonl").read_text())
    assert rec["pass"] is True
    assert rec["fault_count"] == 8
    assert rec["funnel"]["injected"] == 8


@needs_canary
def test_canary_doc_roundtrip_audits_clean(tmp_path):
    stage = tmp_path / "stage"
    r = subprocess.run([sys.executable,
                        os.path.join(REPO, "tools", "gen_r6_w1_lsqfwd_docs.py"),
                        "--root", CANARY, "--stage", str(stage)],
                       capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, r.stdout + r.stderr
    doc = stage / "S01-F1-W1" / "S01-F1-W1-seed1.md"
    assert doc.is_file()
    text = doc.read_text()
    assert "未逐行转录" in text
    r = subprocess.run([sys.executable,
                        os.path.join(REPO, "tools", "audit_r6_w1_docs.py"),
                        "--root", CANARY, "--stage", str(stage)],
                       capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "0 errors" in r.stdout
