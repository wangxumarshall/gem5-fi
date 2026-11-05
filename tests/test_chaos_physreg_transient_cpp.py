"""tests/test_chaos_physreg_transient_cpp.py — FR01/FR02 transient Vec flips.

Compiles tests/unit/chaos_vec_transient_test.cc with the host g++ (no gem5
build) and requires every FR01/FR02 check to pass. Static checks below prove
the transient model is really wired into CHAOSPhysReg:

  * the Vec bit_flip path selects/validates DISTINCT bits (FR02 can never
    collapse into a one-bit fault) and fails closed on an impossible request;
  * the bit_flip path never arms the FR03 permanent write-path mask;
  * L0/L1/L2/L5 evidence is emitted with model_id FR01/FR02 and freq F0;
  * real consumer reads and the real overwrite are observed on the existing
    post-execute hook, and the overwrite freezes the read trace.
"""
import shutil
import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "tests/unit/chaos_vec_transient_test.cc"
INC = REPO / "CHAOS/gem5/src/cpu/o3/CHAOSPhysReg"
HEADER = INC / "chaos_vec_transient.hh"
PHYS_CC = REPO / "CHAOS/gem5/src/cpu/o3/CHAOSPhysReg/CHAOSPhysReg.cc"
PHYS_HH = REPO / "CHAOS/gem5/src/cpu/o3/CHAOSPhysReg/CHAOSPhysReg.hh"
REGFILE_HH = REPO / "CHAOS/gem5/src/cpu/o3/regfile.hh"


def test_chaos_vec_transient_unit():
    cxx = shutil.which("g++")
    if not cxx:
        raise AssertionError("g++ is required for the FR01/FR02 host test")
    with tempfile.TemporaryDirectory() as td:
        exe = Path(td) / "chaos_vec_transient_test"
        build = subprocess.run(
            [cxx, "-O0", "-std=c++17", "-Wall", "-Wextra", "-Werror",
             "-I", str(INC), str(SRC), "-o", str(exe)],
            capture_output=True, text=True)
        assert build.returncode == 0, build.stderr
        run = subprocess.run([str(exe)], capture_output=True, text=True)
        assert run.returncode == 0, run.stdout + run.stderr
        out = run.stdout
        assert "ALL TRANSIENT CHECKS PASSED" in out
        # Pin the load-bearing semantics explicitly.
        assert "FR01 single-bit: only target bit changes" in out
        assert "FR01 non-target lanes/bytes unchanged" in out
        assert "FR01 overwrite terminates the transient" in out
        assert "FR01 overwrite: reads return the written value, not the flip" in out
        assert "FR01 no permanent/stuck re-apply on later reads" in out
        assert "FR02 two bits are always distinct" in out
        assert "FR02 collision in explicit mask rejected (fail closed)" in out
        assert "FR02 insufficient lane width rejected (fail closed)" in out
        assert "FR02 out-of-range lane rejected (fail closed)" in out
        assert "FR02 explicit two-bit mask has two distinct identities" in out
        assert "FR02 cross-lane geometry is in-range and only target bits change" in out
        assert "FR02 cross-field geometry uses two 32-bit fields" in out
        assert "FR02 cross-field inside a directed 64-bit lane" in out
        assert "FR02 cross-field anchored on a directed 32-bit lane" in out
        assert "FR02 adjacent geometry: distance exactly 1 in one lane" in out
        assert "FR02 non-adjacent geometry: distance >= 2 in one lane" in out
        assert "128-bit boundary bit 127 is addressable" in out


def test_transient_really_wired_into_chaosphysreg():
    header = HEADER.read_text(encoding="utf-8")
    phys = PHYS_CC.read_text(encoding="utf-8")
    hh = PHYS_HH.read_text(encoding="utf-8")
    rf = REGFILE_HH.read_text(encoding="utf-8")

    # Pure model is used by the injector, not a dead header.
    assert "chaos_vec_transient.hh" in hh
    assert "selectionFromMask(" in phys
    assert "select(rng, lw, vec_lane_offset" in phys
    assert "applyToVec(buf.data(), buf.size(), sel)" in phys
    assert "noteVecTransientInstalled(" in phys
    assert "observeVecTransient(inst)" in phys
    assert "noteVecTransientCommit(tid, inst)" in phys
    assert "noteVecTransientSquash(tid, inst)" in phys
    assert "finalizeVecTransient(nullptr)" in phys

    # FR02 collision cannot collapse: the explicit-mask path validates the
    # popcount/geometry and fails closed.
    assert "mask_popcount_mismatch" in header
    assert "VecFaultFailClosed" in phys
    assert "vec_transient_fatal = true;" in phys
    assert "if (vec_transient_fatal)" in phys

    # No permanent arm in the transient path: exactly the two FR03 stuck
    # branches arm the permanent Vec cell.
    assert phys.count("armVecStuck(") == 2
    assert "no permanent arm" in phys
    transient_block = phys[phys.index("if (chosen == FaultType::BitFlip)"):
                           phys.index("noteVecTransientInstalled(")]
    assert "armVecStuck" not in transient_block

    # Model identity and bit identities are emitted.
    assert 'sel.bits.size() == 1 ? "FR01" : "FR02"' in phys
    assert '"fault_applied"' in phys
    assert '"bit_indices"' in phys
    assert '{"fault_mask", mask_os.str()}' in phys
    assert '"overwrite"' in phys
    assert '"phys_cell_rewritten"' in phys
    assert '{"detection_layer", "L5"}' in phys

    # The real overwrite is observed on the post-execute hook and freezes the
    # container read trace (vector dest writes bypass setReg()).
    assert "noteTraceOverwrite" in rf
    assert "rf.noteTraceOverwrite();" in phys


def test_fr01_fr02_runids_exist_and_are_f0_w1():
    import json
    reg = json.loads(
        (REPO / "docs/gem5-fi/fsu/runids.json").read_text(encoding="utf-8"))
    rows = {r["RunID"]: r for r in reg["runids"]}
    for rid, model in (("FSU-FR01-F0-W1", "FR01"),
                       ("FSU-FR02-F0-W1", "FR02")):
        assert rid in rows, rid
        r = rows[rid]
        assert r["模型ID"] == model
        assert r["频率"] == "F0"
        assert r["负载ID"] == "W1"
        assert r["负载名称"] == "FP-ScalarProbe"
        assert "每次运行只注入1次" in r["采样说明"]


def test_fr01_fr02_consumer_identity_and_precision_wiring():
    """[FR01/FR02] The W1 identity audit must stay wired end-to-end."""
    phys = PHYS_CC.read_text(encoding="utf-8")
    hh = PHYS_HH.read_text(encoding="utf-8")
    py = (REPO / "CHAOS/gem5/src/cpu/o3/CHAOSPhysReg/CHAOSPhysReg.py").read_text(
        encoding="utf-8")
    iq = (REPO / "CHAOS/gem5/src/cpu/o3/inst_queue.cc").read_text(
        encoding="utf-8")
    iqh = (REPO / "CHAOS/gem5/src/cpu/o3/inst_queue.hh").read_text(
        encoding="utf-8")
    dyn = (REPO / "CHAOS/gem5/src/cpu/o3/dyn_inst.hh").read_text(
        encoding="utf-8")
    dyncc = (REPO / "CHAOS/gem5/src/cpu/o3/dyn_inst.cc").read_text(
        encoding="utf-8")
    runner = (REPO / "tools/fsu_seed_runner.py").read_text(encoding="utf-8")
    cfg = (REPO / "configs/fsu/FR01-F0-W1-seed1.json").read_text(
        encoding="utf-8")

    # ARM has no real FloatRegClass: scalar FP sources are VecRegClass.
    isa = (REPO / "CHAOS/gem5/src/arch/arm/isa.cc").read_text(encoding="utf-8")
    assert "Not applicable to ARM" in isa
    assert "RegClass floatRegClass(FloatRegClass, FloatRegClassName, 0" in isa

    # Ready pending sources are collected as EVENTS (instruction, operand).
    assert "collectReadyPendingSources" in iqh and "collectReadyPendingSources" in iq
    assert "readySrcIdx" in iq

    # The read hook is at the exact getRegOperand point, not post-execute.
    assert "noteChaosVecRead" in dyn and "noteChaosVecRead" in dyncc
    assert "cpu->chaosPhysReg->noteVecOperandRead" in dyncc
    assert "noteVecOperandRead" in phys
    # Generation is provenance, not a read filter.
    assert "generationOf(src) !=" not in phys
    assert "Generation is provenance, NOT a filter" in phys
    # Store data reads happen in initiateAcc, after the post-execute hook.
    assert "inst->isStore()" in phys

    # Event-driven arm at the consumer's execute boundary.
    assert "maybeInjectBeforeExecute" in phys and "maybeInjectBeforeExecute" in hh
    assert "cpu->chaosPhysReg->maybeInjectBeforeExecute(this)" in dyncc

    # Precision is decoded from the REAL AArch64 encoding.
    assert "decodedConsumerPrecision" in phys
    assert "ArmStaticInst" in phys and "encoding()" in phys
    assert "targetPrecision" in py and "loadId" in py

    # Runner/config wiring + frozen values.
    assert "--phys_target_selection" in runner
    assert "--phys_target_precision" in runner
    assert "--phys_load_id" in runner
    assert '"target_selection": "ready_consumer"' in cfg
    assert '"target_precision": 64' in cfg
