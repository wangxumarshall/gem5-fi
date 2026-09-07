"""pytest for tools/diag/esr_decode.py (Task 4.1, plan §7.3).

Anchors:
- 0x96000044 / 0x96000004: core179 repeated-WARN/Oops signature — DABT
  current EL, WnR 1/0, FSC L0 translation fault, 4-star SDC weight.
- 0x2000000: instruction abort lower EL.
- 0xBF000000: SError (AET path; 5-star — nested-SError 59.35x reference).
- 0x3C000000-style BRK family? EC 0x3C has ISS bits used by BRK — but EC
  decode itself is what we test here.
- log-text extraction: 'ESR = 0x96000044' lines.
"""
import importlib.util
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.join(HERE, "..", "tools", "diag", "esr_decode.py")


def load():
    spec = importlib.util.spec_from_file_location("esr_decode", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_core179_write_signature():
    m = load()
    d = m.decode(0x96000044)
    assert d["ec"].lower() == "0x25" and "Data Abort" in d["ec_name"]
    assert d["wnr"] == 1 and d["wnr_text"] == "write"
    assert d["fsc"] == "0x04" and "level 0" in d["fsc_text"]
    assert d["sdc_weight_stars"] == 4


def test_core179_read_signature():
    m = load()
    d = m.decode(0x96000004)
    assert d["ec"].lower() == "0x25"
    assert d["wnr"] == 0 and d["wnr_text"] == "read"
    assert d["fsc"] == "0x04"


def test_instruction_abort():
    m = load()
    d = m.decode(0x20 << 26)  # EC=0x20
    assert d["ec"].lower() == "0x20" and "Instruction Abort" in d["ec_name"]


def test_serror_weight():
    m = load()
    d = m.decode(0x2F << 26)  # EC=0x2F SError
    assert d["ec"].lower() == "0x2f" and d["sdc_weight_stars"] == 5
    assert "RAS" in d["note"]


def test_undef_and_brk():
    m = load()
    assert m.decode(0x0)["ec"].lower() == "0x00"              # Undefined Instruction
    assert m.decode(0x3C << 26)["ec"].lower() == "0x3c"   # BRK family


def test_log_text_extraction():
    m = load()
    text = ("Unable to handle kernel paging request\n"
            "ESR = 0x96000004: DABT(current EL)\n"
            "esr_el1 0x96000044 somewhere else\n")
    vals = m.parse_esr_text(text)
    assert 0x96000004 in vals and 0x96000044 in vals


def test_cli_json():
    r = subprocess.run([sys.executable, TOOL, "--json", "0x96000044"],
                       capture_output=True, text=True)
    assert r.returncode == 0
    d = json.loads(r.stdout)[0]
    assert d["fsc"] == "0x04" and d["wnr"] == 1
