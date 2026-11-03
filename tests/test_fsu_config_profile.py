"""Pure-Python tests for the B0 config.ini gate (no gem5 run)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import fsu_config_profile as CP


def _ini(**overrides):
    core = {
        "fetchWidth": 3, "decodeWidth": 3, "renameWidth": 3,
        "dispatchWidth": 6, "issueWidth": 8, "wbWidth": 8,
        "commitWidth": 8, "numROBEntries": 40,
        "numPhysIntRegs": 128, "numPhysFloatRegs": 192,
        "numPhysVecRegs": 48, "LQEntries": 16, "SQEntries": 16,
        "fetchBufferSize": 16, "squashWidth": 8,
    }
    core.update(overrides)
    lines = ["[board.processor.cores.core]", "type=BaseO3CPU"]
    lines += [f"{k}={v}" for k, v in core.items()]
    lines += ["[board.processor.cores.core.instQueues]", "type=IQUnit",
              "numEntries=32"]
    return "\n".join(lines) + "\n"


def test_b0_config_matches(tmp_path):
    p = tmp_path / "config.ini"
    p.write_text(_ini(), encoding="utf-8")
    chk = CP.verify_config_profile(p, "B0")
    assert chk["ok"] is True, chk["errors"]
    assert chk["actual"]["numROBEntries"] == 40
    assert chk["actual"]["iqEntries"] == 32
    assert chk["actual"]["dispatchWidth"] == 6


def test_b0_mismatches_fail_closed(tmp_path):
    for bad in ({"numROBEntries": 128}, {"iqEntries": 64},
                {"fetchWidth": 4}, {"dispatchWidth": 4},
                {"issueWidth": 4}, {"wbWidth": 4}, {"commitWidth": 4},
                {"numPhysFloatRegs": 128}, {"numPhysVecRegs": 256}):
        text = _ini(**bad)
        if "iqEntries" in bad:
            text = text.replace("numEntries=32",
                                f"numEntries={bad['iqEntries']}")
        p = tmp_path / "config.ini"
        p.write_text(text, encoding="utf-8")
        chk = CP.verify_config_profile(p, "B0")
        assert chk["ok"] is False, bad


def test_missing_or_unknown_profile(tmp_path):
    chk = CP.verify_config_profile(tmp_path / "missing.ini", "B0")
    assert chk["ok"] is False
    p = tmp_path / "config.ini"
    p.write_text(_ini(), encoding="utf-8")
    assert CP.verify_config_profile(p, "B9")["ok"] is False


def test_c3_profile_matches_legacy_actual(tmp_path):
    text = _ini(fetchWidth=4, decodeWidth=4, renameWidth=4,
                dispatchWidth=4, issueWidth=4, wbWidth=8, commitWidth=4,
                numROBEntries=128)
    text = text.replace("numEntries=32", "numEntries=64")
    p = tmp_path / "config.ini"
    p.write_text(text, encoding="utf-8")
    assert CP.verify_config_profile(p, "C3")["ok"] is True
