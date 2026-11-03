"""tests/test_chaos_physreg_generation_cpp.py — FR03 generation + L5 wiring.

Compiles tests/unit/chaos_physreg_generation_test.cc with the host g++ (no
gem5 build) and requires every permanent-cell generation / L5 check to pass.

The test pins the workbook ruling (table 3 FR03 + table 7/9 FR03):
the permanent key is reg_class + phys_index + lane/bit/mask + polarity;
generation is allocation/exposure identity only. Free/realloc/squash do NOT
clear the defect; a new generation restarts its exposure chain; only an
explicit end-of-run reset clears it. L5 commit/squash is a real state machine:
a squash is never a commit and a chain_end can only claim "committed" when a
real L5 commit event exists.

Static tests below also prove the O3 hooks are really wired (commit.cc /
rob.cc) and that CHAOSPhysReg has no fault-clearing path outside the run-end
terminal.
"""
import importlib.util
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "tests/unit/chaos_physreg_generation_test.cc"
INC = REPO / "CHAOS/gem5/src/cpu/o3/CHAOSPhysReg"
PHYS_CC = REPO / "CHAOS/gem5/src/cpu/o3/CHAOSPhysReg/CHAOSPhysReg.cc"
PHYS_HH = REPO / "CHAOS/gem5/src/cpu/o3/CHAOSPhysReg/CHAOSPhysReg.hh"
COMMIT_CC = REPO / "CHAOS/gem5/src/cpu/o3/commit.cc"
ROB_CC = REPO / "CHAOS/gem5/src/cpu/o3/rob.cc"


def test_chaos_physreg_generation_unit():
    cxx = shutil.which("g++")
    if not cxx:
        pytest.skip("g++ not available")
    with tempfile.TemporaryDirectory() as td:
        exe = Path(td) / "chaos_physreg_generation_test"
        build = subprocess.run(
            [cxx, "-O0", "-std=c++17", "-Wall", "-Wextra", "-Werror",
             "-I", str(INC), str(SRC), "-o", str(exe)],
            capture_output=True, text=True)
        assert build.returncode == 0, build.stderr
        run = subprocess.run([str(exe)], capture_output=True, text=True)
        assert run.returncode == 0, run.stdout + run.stderr
        assert "ALL GENERATION CHECKS PASSED" in run.stdout
        # Pin the load-bearing semantics explicitly.
        assert "PERMANENT STUCK ACROSS GENERATIONS" in run.stdout
        assert "GENERATION CHAIN RESTART: exposure_id back to 1" in run.stdout
        assert "SQUASH DOES NOT CLEAR" in run.stdout
        assert "reset clears the cell" in run.stdout
        assert "int register class does not cross-talk" in run.stdout
        assert "float register class does not cross-talk" in run.stdout
        # L5 + split read/write accounting.
        assert "write exposures exclude reads" in run.stdout
        assert "read exposures exclude writes" in run.stdout
        assert "squash does not count as a commit" in run.stdout
        assert "real commit wins the terminal" in run.stdout
        assert "old generation consumer keeps its own generation" in run.stdout
        assert "old/new generation L2 parents never merge" in run.stdout


def _function_body(src: str, name: str) -> str:
    """Return one CHAOSPhysReg::<name> body (4-space closing brace)."""
    m = re.search(rf"CHAOSPhysReg::{name}\(", src)
    assert m is not None, name
    end = src.find("\n    }\n", m.start())
    assert end != -1, name
    return src[m.start():end]


def test_o3_l5_hooks_are_wired():
    commit = COMMIT_CC.read_text(encoding="utf-8")
    rob = ROB_CC.read_text(encoding="utf-8")
    assert ('#include "cpu/o3/CHAOSPhysReg/CHAOSPhysReg.hh"' in commit)
    assert ('#include "cpu/o3/CHAOSPhysReg/CHAOSPhysReg.hh"' in rob)
    assert "cpu->chaosPhysReg->noteCommit(tid, head_inst.get());" in commit
    assert ("cpu->chaosPhysReg->noteSquash(tid, "
            "(*squashIt[tid]).get());") in rob
    # noteCommit sits at the existing FSU anchor (after chaosFPU->noteCommit).
    fpu = commit.index("cpu->chaosFPU->noteCommit(tid, head_inst.get());")
    phys = commit.index(
        "cpu->chaosPhysReg->noteCommit(tid, head_inst.get());")
    assert phys > fpu
    # noteSquash is inside the real ROB squash loop, not a side path.
    ds = rob.index("ROB::doSquash")
    ns = rob.index(
        "cpu->chaosPhysReg->noteSquash(tid, (*squashIt[tid]).get());")
    assert ns > ds
    assert rob.index("for (int numSquashed = 0;") < ns


def test_no_clear_on_generation_free_or_squash_paths():
    src = PHYS_CC.read_text(encoding="utf-8")
    # The only permanent-cell clear call is the run-end terminal.
    assert src.count("clearPermanentFaults()") == 1
    terminal = _function_body(src, "emitVecTerminal")
    assert "clearPermanentFaults()" in terminal
    for fn in ("observeVecGeneration", "noteCommit", "noteSquash",
               "maybeReapplyStuck", "noteVecStuckInstalled"):
        body = _function_body(src, fn)
        assert "clearPermanentFaults" not in body, fn
        assert "clearVecStuck" not in body, fn
        assert "clearStuckTarget" not in body, fn
    assert "clearVecStuck" not in src
    # A squash emits kind=squash and never kind=commit.
    squash = _function_body(src, "noteSquash")
    assert 'emitFsuProp("squash"' in squash
    assert 'emitFsuProp("commit"' not in squash
    assert '{"squashed", "1"}' in squash
    # A commit is a real L5 witness.
    commit = _function_body(src, "noteCommit")
    assert '"commit", vec_emit.fault_id' in commit
    assert '{"detection_layer", "L5"}' in commit
    assert '{"outcome", "errant_commit"}' in commit
    # Honest terminal vocabulary; "committed" is not a hard-coded claim.
    assert 'l5.terminal(vec_emit.activated_total)' in terminal
    assert "first_impact_sn" in terminal
    assert "l5_witness_event" in terminal
    assert "squash_events" in terminal
    assert "read_exposures_total" in terminal
    assert "write_exposures_total" in terminal
    header = PHYS_HH.read_text(encoding="utf-8")
    assert "void noteCommit(ThreadID tid, o3::DynInst *inst);" in header
    assert "void noteSquash(ThreadID tid, o3::DynInst *inst);" in header
    assert "bool require_allocated;" in header
    py = (REPO / "CHAOS/gem5/src/cpu/o3/CHAOSPhysReg/CHAOSPhysReg.py").read_text(
        encoding="utf-8")
    assert "requireAllocated = Param.Bool(" in py


def _load_gate_assert():
    path = REPO / "tests/unit/fr03_gate_assert.py"
    spec = importlib.util.spec_from_file_location("fr03_gate_assert", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _events(commit=True, squash=False, commit_generation="1"):
    evts = [
        {"kind": "fault_installed", "fault_id": "1", "event_id": "1",
         "field": "permanent_stuck", "reg_class": "vec", "phys_reg": "0",
         "fixed_mask": "0x1", "stuck_polarity": "0", "lane_width": "32",
         "lane_offset": "2", "bit_in_lane": "0", "install_event": "1"},
        {"kind": "carrier_state", "fault_id": "1", "event_id": "2",
         "parent_event_id": "1", "reg_class": "vec", "phys_reg": "0"},
        {"kind": "phys_write", "fault_id": "1", "event_id": "7",
         "tick": "5", "reg_class": "vec", "phys_reg": "0",
         "reg_generation": "1", "fixed_mask": "0x1",
         "stuck_polarity": "0", "before": "0x3", "after": "0x2"},
        {"kind": "operand_read", "fault_id": "1", "event_id": "3",
         "parent_event_id": "2", "consumer_seq": "10",
         "dyn_inst_seq": "10", "reg_class": "vec", "phys_reg": "0",
         "reg_generation": "1", "fixed_mask": "0x1",
         "stuck_polarity": "0"},
    ]
    if commit:
        evts.append(
            {"kind": "commit", "fault_id": "1", "event_id": "4",
             "parent_event_id": "3", "consumer_seq": "10",
             "dyn_inst_seq": "10", "commit_seq": "1",
             "detection_layer": "L5", "outcome": "errant_commit",
             "install_event": "1", "reg_class": "vec", "phys_reg": "0",
             "reg_generation": commit_generation, "fixed_mask": "0x1",
             "stuck_polarity": "0"})
    if squash:
        evts.append(
            {"kind": "squash", "fault_id": "1", "event_id": "6",
             "tick": "10", "parent_event_id": "3", "consumer_seq": "10",
             "dyn_inst_seq": "10", "squashed": "1",
             "reg_class": "vec", "phys_reg": "0", "reg_generation": "1",
             "fixed_mask": "0x1", "stuck_polarity": "0"})
        # The permanent defect survives the squash: a later write is still
        # forced to the same mask/polarity.
        evts.append(
            {"kind": "phys_write", "fault_id": "1", "event_id": "8",
             "tick": "20", "reg_class": "vec", "phys_reg": "0",
             "reg_generation": "1", "fixed_mask": "0x1",
             "stuck_polarity": "0", "before": "0x3", "after": "0x2"})
    terminal = "committed" if commit else ("squashed" if squash
                                           else "exposed_unconsumed")
    evts.append(
        {"kind": "chain_end", "fault_id": "1", "event_id": "9",
         "terminal": terminal, "l5_witness_event": "4" if commit else "0",
         "first_impact_sn": "10" if commit else "0",
         "first_impact_latency": "100" if commit else "0",
         "write_exposures_total": "3", "read_exposures_total": "2",
         "exposures_total": "3", "commit_events": "1" if commit else "0",
         "squash_events": "1" if squash else "0",
         "consumers_recorded": "1"})
    return evts


def test_gate_assert_accepts_real_commit_chain():
    ga = _load_gate_assert()
    report = ga.analyze(_events(commit=True))
    assert report["ok"], report["violations"]
    assert report["l5"]["terminal"] == "committed"
    assert report["counts"]["read_exposures_total"] == 2
    assert report["counts"]["write_exposures_total"] == 3


def test_gate_assert_rejects_commit_claim_without_l5():
    ga = _load_gate_assert()
    evts = _events(commit=False)
    # Falsely claim a commit in chain_end without any real L5 witness.
    end = evts[-1]
    end["terminal"] = "committed"
    end["l5_witness_event"] = "4"
    report = ga.analyze(evts)
    assert not report["ok"]
    assert "chain_end_claims_commit_without_L5" in report["violations"]


def test_gate_assert_rejects_generation_join():
    ga = _load_gate_assert()
    report = ga.analyze(_events(commit=True, commit_generation="2"))
    assert not report["ok"]
    assert any(x.startswith("commit_generation_join")
               for x in report["violations"])


def test_gate_assert_accepts_squash_chain():
    ga = _load_gate_assert()
    report = ga.analyze(_events(commit=False, squash=True))
    assert report["ok"], report["violations"]
    assert report["l5"]["terminal"] == "squashed"
    assert report["counts"]["squash_events"] == 1
    assert report["counts"]["commit_events"] == 0
