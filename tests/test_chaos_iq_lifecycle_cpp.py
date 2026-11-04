"""Host-side verification of the §2.5 FQ08-b / FQ08-c CHAOSIQ fixes.

Two layers, both without a gem5 build:

1. Compile and run tests/unit/chaos_iq_lifecycle_test.cc with the host g++
   (-O0 -std=c++17 -Wall -Wextra -Werror). The pure model in
   CHAOS/gem5/src/cpu/o3/CHAOSIQ/chaos_iq_lifecycle.hh is standard C++, and the
   gem5-side CHAOSIQ.cc calls exactly these functions, so the tested behaviour
   is the behaviour that runs in gem5.

2. Static wiring checks: the FQ08-b injection count only moves after a real
   victim is modified, and the FQ08-c delayed wake is CHAOSIQ-owned, carries a
   value identity/generation snapshot, and validates it before re-entering
   InstructionQueue::wakeDependents. The legacy InstructionQueue
   DelayedWakeEvent path must be closed.
"""
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "tests/unit/chaos_iq_lifecycle_test.cc"
INC = ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSIQ"
IQ_HH = ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSIQ/CHAOSIQ.hh"
IQ_CC = ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSIQ/CHAOSIQ.cc"
MODEL_HH = ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSIQ/chaos_iq_lifecycle.hh"


def _code(path):
    assert path.is_file(), path
    return path.read_text(encoding="utf-8", errors="replace")


def _function_body(src, name):
    """Return one ``CHAOSIQ::<name>(...)`` body (4-space closing brace)."""
    m = re.search(rf"CHAOSIQ::{name}\(", src)
    assert m is not None, name
    end = src.find("\n    }\n", m.start())
    assert end != -1, name
    return src[m.start():end]


def test_chaos_iq_lifecycle_unit():
    cxx = shutil.which("g++")
    if not cxx:
        pytest.skip("g++ not available")
    with tempfile.TemporaryDirectory() as td:
        exe = Path(td) / "chaos_iq_lifecycle_test"
        build = subprocess.run(
            [cxx, "-O0", "-std=c++17", "-Wall", "-Wextra", "-Werror",
             "-I", str(INC), str(SRC), "-o", str(exe)],
            capture_output=True, text=True)
        assert build.returncode == 0, build.stderr
        run = subprocess.run([str(exe)], capture_output=True, text=True)
        assert run.returncode == 0, run.stdout + run.stderr
        assert "ALL CHAOS IQ LIFECYCLE CHECKS PASSED" in run.stdout
        # Pin the load-bearing semantics explicitly.
        assert "REPRO old gate counts 1 injection with no victim" in run.stdout
        assert "REPRO fixed model counts 0 injections" in run.stdout
        assert "no victim => no applied" in run.stdout
        assert "wrong source slot chosen" in run.stdout
        assert "legitimate chain slot not chosen" in run.stdout
        assert "activated" in run.stdout
        assert "three no-victim attempts consumed no budget" in run.stdout
        assert "squash => wakeDependents NOT called" in run.stdout
        assert "reused slot => new owner is NOT woken" in run.stdout
        assert "normal event still fires" in run.stdout


def test_model_header_is_pure_and_used_by_injector():
    model = _code(MODEL_HH)
    # No gem5 includes: it must compile with the host g++ alone (comments may
    # mention gem5 paths; only #include lines matter).
    includes = re.findall(r"^\s*#include\s+[<\"]([^>\"]+)[>\"]", model, re.M)
    assert includes, includes
    for inc in includes:
        assert not inc.startswith(("params/", "sim/", "cpu/", "base/",
                                   "arch/", "mem/")), inc
    for sym in ("struct Counters", "struct Attempt", "chooseWrongSlot",
                "noteApplied", "classifyWake", "struct WakeStamp",
                "struct DestStamp", "struct DelayedWakeCounters"):
        assert sym in model, sym
    # The gem5-side injector uses this exact model.
    assert '#include "cpu/o3/CHAOSIQ/chaos_iq_lifecycle.hh"' in _code(IQ_HH)
    assert "chaos_iq_lifecycle::beginAttempt(" in _code(IQ_CC)
    assert "chaos_iq_lifecycle::chooseWrongSlot(" in _code(IQ_CC)
    assert "chaos_iq_lifecycle::classifyWake(" in _code(IQ_CC)
    assert "chaos_iq_lifecycle::recordDuplicateWake(" in _code(IQ_CC)
    assert "chaos_iq_lifecycle::suppressDuplicateWake(" in _code(IQ_CC)


def test_fq08b_gate_does_not_count_an_injection():
    body = _function_body(_code(IQ_CC), "shouldWrongSourceWake")
    # FQ08-b: the gate records an ATTEMPT only; the old counter increment and
    # "return true" (inject without a victim) are gone.
    assert "faults_injected_count++" not in body
    assert "chaos_iq_lifecycle::beginAttempt(" in body
    assert "iq_counts.attempted++" in body
    assert "return false" in body
    assert "return true" not in body


def test_fq08b_duplicate_genuine_wake_is_suppressed():
    body = _function_body(_code(IQ_CC), "shouldSuppressReadyMark")
    # The injected source stays in the victim's dependency chain (no
    # dependGraph access), so the genuine wake must be suppressed once.
    assert "Mode::SrcReadyBitflip" in body
    assert "chaos_iq_lifecycle::suppressDuplicateWake(" in body
    assert body.find("Mode::SrcReadyBitflip") < \
        body.find("Mode::ReadyNever")


def test_fq08b_apply_requires_a_real_victim():
    src = _code(IQ_CC)
    body = _function_body(src, "maybeApplyWrongSourceWake")
    choose_at = body.find("chooseWrongSlot(")
    apply_at = body.find("markSrcRegReady(")
    count_at = body.find("faults_injected_count++")
    assert choose_at != -1 and apply_at != -1 and count_at != -1
    # The victim must be chosen first, modified second, counted third.
    assert choose_at < apply_at < count_at
    assert "if (slot < 0) return;" in body
    # Identity evidence required by FQ08-b.
    for field in ("victim_sn", "victim_src_phys", "victim_src_flat",
                  "victim_src_generation", "producer_sn",
                  "wrong_of_chain_flat"):
        assert field in body, field
    # The hook really runs from the dependent loop callback.
    assert "maybeApplyWrongSourceWake(dep_inst, chain_flat)" in _code(IQ_CC)


def test_fq08c_delayed_wake_is_chaos_owned():
    hh = _code(IQ_HH)
    src = _code(IQ_CC)
    # The event holds a refcounted instruction and a value stamp, not a bare
    # InstructionQueue pointer.
    m = re.search(r"class DelayedWake : public Event\s*\{(.*?)\n    \};", hh,
                  re.S)
    assert m is not None
    event = m.group(1)
    assert "o3::DynInstPtr inst;" in event
    assert "chaos_iq_lifecycle::WakeStamp stamp;" in event
    assert "InstructionQueue" not in event

    # wake_phase is scheduled by CHAOSIQ with the generation snapshot, and
    # the legacy caller-side event is permanently closed.
    omit = _function_body(src, "shouldOmitWake")
    assert "new DelayedWake(" in omit
    assert "snapshotWakeStamp(" in omit
    assert "faults_injected_count++" in omit
    delay = _function_body(src, "shouldDelayWake")
    assert "return false" in delay
    assert "cpu->schedule" not in delay
    assert "new DelayedWakeEvent" not in delay

    # process() classifies the snapshot BEFORE touching wakeDependents.
    proc = _function_body(src, "DelayedWake::process")
    classify_at = proc.find("classifyWake(")
    wake_at = proc.find("wakeDependents(")
    assert classify_at != -1 and wake_at != -1
    assert classify_at < wake_at
    assert "IgnoreSquashed" not in proc  # decision comes from the model
    assert "WakeDecision::Fire" in proc


def test_fq08c_ignored_event_is_logged_without_counting_as_injection():
    body = _function_body(_code(IQ_CC), "noteDelayedWakeIgnored")
    assert "IGNORED reason=" in body
    # Log parsers (tools/runner.py, tools/fsu_seed_runner.py) treat any line
    # without an explicit count as an injection; every new line must carry it.
    assert "faults_injected: " in body
    dump = _function_body(_code(IQ_CC), "dumpIqCounts")
    assert "CHAOS_IQ_COUNTS" in dump
    for field in ("eligible=", "attempted=", "applied=", "activated=",
                  "no_victim="):
        assert field in dump, field
    assert "faults_injected: " in dump


def test_fq08c_replay_does_not_reinject():
    src = _code(IQ_CC)
    # A delayed wake re-entering wakeDependents must not schedule another
    # injection (unlimited-fault wake_phase would otherwise feed itself).
    assert "replaying_delayed_wake = true;" in src
    assert "injector->replaying_delayed_wake = false;" in src
    assert "if (replaying_delayed_wake) return false;" in src
