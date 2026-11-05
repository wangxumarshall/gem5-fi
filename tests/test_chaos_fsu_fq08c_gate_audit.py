"""FQ08-c gate audit: positive fire, generation/identity, stale-event safety.

This file adds evidence that did not exist in the earlier FQ08 regression file:

* HOST TARGET-STATE: compile and run
  tests/unit/fq08c_delayed_wake_target_state_test.cc, which includes the SAME
  ``chaos_iq_lifecycle.hh`` that CHAOSIQ.cc calls.  It asserts not only the
  classification but the observable consequence: only ``Fire`` changes a
  dependent's ready state / calls ``wakeDependents``; squash, identity and
  generation changes are no-ops; a stale event cannot wake the new owner of a
  reused physical slot.
* SOURCE WIRING: ``iq_counts.activated`` moves only inside the Fire branch;
  the stamp snapshot is taken before scheduling; every event increments
  exactly one decision counter.
* REAL EVIDENCE: parse ``runs/fsu-gates/FQ08-*`` logs.  The existing gate is
  a real squash no-op.  Positive fire / generation / identity evidence is
  still absent, and the tests that need it SKIP with ``BLOCKED`` in the
  reason (they validate automatically once such a log exists).
"""
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
IQ_DIR = ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSIQ"
IQ_CC = IQ_DIR / "CHAOSIQ.cc"
IQ_HH = IQ_DIR / "CHAOSIQ.hh"
MODEL_HH = IQ_DIR / "chaos_iq_lifecycle.hh"
HOST_SRC = ROOT / "tests/unit/fq08c_delayed_wake_target_state_test.cc"
GATES = ROOT / "runs/fsu-gates"


def _code(path):
    assert path.is_file(), path
    return path.read_text(encoding="utf-8", errors="replace")


def _function_body(src, name, closing="\n    }\n"):
    m = re.search(rf"^\s*CHAOSIQ::{re.escape(name)}\(", src, re.M)
    assert m is not None, name
    end = src.find(closing, m.start())
    assert end != -1, name
    return src[m.start():end]


# ---------------------------------------------------------------------------
# Host target-state evidence (real g++ run, no gem5)
# ---------------------------------------------------------------------------

def test_host_target_state_model():
    cxx = shutil.which("g++")
    if not cxx:
        pytest.skip("g++ not available")
    with tempfile.TemporaryDirectory() as td:
        exe = Path(td) / "fq08c_target_state"
        build = subprocess.run(
            [cxx, "-O0", "-std=c++17", "-Wall", "-Wextra", "-Werror",
             "-I", str(IQ_DIR), str(HOST_SRC), "-o", str(exe)],
            capture_output=True, text=True)
        assert build.returncode == 0, build.stderr
        run = subprocess.run([str(exe)], capture_output=True, text=True)
        assert run.returncode == 0, run.stdout + run.stderr
        assert "ALL FQ08-C TARGET-STATE CHECKS PASSED" in run.stdout
        for needle in (
            "unsquashed producer fires",
            "fire calls wakeDependents exactly once",
            "fire changes dependent ready state false -> true",
            "squash leaves dependent ready=false",
            "stale event does not wake the new owner",
            "stale event leaves the new owner's dependent not ready",
            "identity mismatches never touch target state",
            "identity wins over squash/generation",
            "old event never wakes after squash/reuse",
            "separate current event changes target state",
            "drained run: scheduled == fired + ignored_*",
        ):
            assert needle in run.stdout, needle


# ---------------------------------------------------------------------------
# Source wiring
# ---------------------------------------------------------------------------

def test_activated_moves_only_when_the_delayed_event_fires():
    proc = _function_body(_code(IQ_CC), "DelayedWake::process")
    guard = proc.find(
        "if (decision != chaos_iq_lifecycle::WakeDecision::Fire)")
    activated = proc.find("iq_counts.activated++")
    wake = proc.find("wakeDependents(inst)")
    assert -1 not in (guard, activated, wake)
    # The guarded early return comes first, then the counter, then the wake.
    assert guard < activated < wake
    # No other exit can increment activated: it appears exactly once.
    assert proc.count("iq_counts.activated++") == 1


def test_snapshot_taken_before_scheduling_and_event_is_autodelete():
    omit = _function_body(_code(IQ_CC), "shouldOmitWake")
    snap = omit.find("snapshotWakeStamp(o3cpu, completed_inst)")
    schedule = omit.find("new DelayedWake(this, completed_inst, stamp)")
    assert -1 not in (snap, schedule)
    assert snap < schedule
    # The scheduled event carries the value stamp, not a live IQ pointer.
    assert "Event(Default_Pri, AutoDelete)" in _code(IQ_CC)
    hh = _code(IQ_HH)
    m = re.search(r"class DelayedWake : public Event\s*\{(.*?)\n    \};",
                  hh, re.S)
    assert m is not None
    body = m.group(1)
    assert "o3::DynInstPtr inst;" in body
    assert "chaos_iq_lifecycle::WakeStamp stamp;" in body
    assert "InstructionQueue" not in body


def test_legacy_unchecked_event_path_stays_closed():
    body = _function_body(_code(IQ_CC), "shouldDelayWake")
    code = "\n".join(line.split("//", 1)[0] for line in body.splitlines())
    assert "return false;" in code
    assert "schedule" not in code
    assert "DelayedWakeEvent" not in code


def test_fire_target_state_count_is_not_observable_yet():
    body = _function_body(_code(IQ_CC), "DelayedWake::process")
    proc = "\n".join(line.split("//", 1)[0] for line in body.splitlines())
    if re.search(r"woken\s*=|wakeup_dependents", proc):
        return
    pytest.skip(
        "to be implemented (placeholder): the FIRED log does not record "
        "wakeDependents()'s return value, so `activated=1` proves the Fire "
        "branch ran but NOT that any dependent's ready state changed. "
        "Add `int woken = ...wakeDependents(inst); ... woken=<n>`.")


def test_wake_phase_applied_scheduled_and_activated_fired_are_distinct():
    omit = _function_body(_code(IQ_CC), "shouldOmitWake")
    # Scheduling is the injection (applied / budget), firing is activation.
    assert "dw_counts.scheduled++" in omit
    assert "iq_counts.applied++" in omit
    assert "faults_injected_count++" in omit
    assert "iq_counts.activated++" not in omit
    proc = _function_body(_code(IQ_CC), "DelayedWake::process")
    assert "dw_counts.fired" in proc
    assert "iq_counts.activated++" in proc


# ---------------------------------------------------------------------------
# Real-gate evidence parser / checker (offline)
# ---------------------------------------------------------------------------

_COUNT_KEYS = ("eligible", "attempted", "applied", "activated", "no_victim",
               "pending_attempt", "delayed_scheduled", "delayed_fired",
               "delayed_ignored_no_inst", "delayed_ignored_identity",
               "delayed_ignored_squashed", "delayed_ignored_generation")


def parse_iq_evidence(text):
    """Parse one/many iq_injections.log files into events + last summary."""
    events = []
    summary = None
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("CHAOS_IQ_COUNTS"):
            rec = {}
            for k, v in re.findall(r"(\w+)=(\d+)", line):
                if k in _COUNT_KEYS:
                    rec[k] = int(v)
            m = re.search(r"faults_injected:\s*(\d+)", line)
            rec["faults_injected"] = int(m.group(1)) if m else None
            summary = rec
            continue
        if "Site: iq_delayed_wake" in line:
            if "FIRED delayed wake" in line:
                m = re.search(r"\bwoken=(\d+)", line)
                events.append({"kind": "fire", "line": line,
                               "woken": int(m.group(1)) if m else None})
            else:
                m = re.search(r"IGNORED reason=(\w+)", line)
                if m:
                    events.append({"kind": m.group(1), "line": line})
        elif "delayed_event=scheduled" in line:
            events.append({"kind": "scheduled", "line": line})
    return {"events": events, "summary": summary}


def evaluate_iq_evidence(parsed):
    """Turn parsed logs into gate facts; never upgrades 'absent' to a pass."""
    ev = parsed["events"]
    s = parsed["summary"] or {}
    fired = sum(1 for e in ev if e["kind"] == "fire")
    # Trust the event lines, but cross-check them against the summary.
    facts = {
        "scheduled_events": sum(1 for e in ev if e["kind"] == "scheduled"),
        "fire_events": fired,
        "fire_woken": [e.get("woken") for e in ev if e["kind"] == "fire"],
        "squash_events": sum(1 for e in ev if e["kind"] == "ignore_squashed"),
        "generation_events": sum(
            1 for e in ev if e["kind"] == "ignore_generation"),
        "identity_events": sum(
            1 for e in ev if e["kind"] == "ignore_identity"),
        "no_inst_events": sum(
            1 for e in ev if e["kind"] == "ignore_no_inst"),
        "summary": s,
        "issues": [],
    }
    if s:
        ignored = sum(s.get(k, 0) for k in (
            "delayed_ignored_no_inst", "delayed_ignored_identity",
            "delayed_ignored_squashed", "delayed_ignored_generation"))
        facts["ignored_total"] = ignored
        if s.get("delayed_fired", 0) != fired:
            facts["issues"].append(
                "summary delayed_fired=%s but %d FIRED event lines" %
                (s.get("delayed_fired"), fired))
        for key, name in (
                ("delayed_ignored_squashed", "squash_events"),
                ("delayed_ignored_generation", "generation_events"),
                ("delayed_ignored_identity", "identity_events"),
                ("delayed_ignored_no_inst", "no_inst_events")):
            if s.get(key, 0) != facts[name]:
                facts["issues"].append(
                    "summary %s=%s but %d event lines" %
                    (key, s.get(key), facts[name]))
        scheduled = s.get("delayed_scheduled", 0)
        processed = s.get("delayed_fired", 0) + ignored
        # A run may end with a scheduled event still pending, so only the
        # <= direction is universally valid; equality is required here
        # because the gate waits for the event (criteria in the audit doc).
        if processed > scheduled:
            facts["issues"].append(
                "processed %d > scheduled %d" % (processed, scheduled))
        facts["drained"] = processed == scheduled
    return facts


def _all_iq_logs():
    if not GATES.is_dir():
        return []
    return sorted(GATES.glob("FQ08-*/iq_injections.log")) + \
        sorted(GATES.glob("FQ08-*/**/iq_injections.log"))


def _search_evidence(kind):
    """Return (path, facts) for the first log proving ``kind``."""
    for path in _all_iq_logs():
        facts = evaluate_iq_evidence(parse_iq_evidence(_code(path)))
        if kind == "fire" and facts["fire_events"]:
            return path, facts
        if kind == "generation" and facts["generation_events"]:
            return path, facts
        if kind == "identity" and facts["identity_events"]:
            return path, facts
    return None, None


def test_existing_gate_is_a_real_squash_noop():
    path = GATES / "FQ08-C-GATE/iq_injections.log"
    if not path.is_file():
        pytest.skip("FQ08-C-GATE evidence not present")
    facts = evaluate_iq_evidence(parse_iq_evidence(_code(path)))
    assert facts["issues"] == [], facts["issues"]
    s = facts["summary"]
    assert s is not None
    # Real observed facts (see the audit document for the raw lines).
    assert s["delayed_scheduled"] == 1
    assert s["delayed_fired"] == 0
    assert s["delayed_ignored_squashed"] == 1
    assert s["faults_injected"] == 1
    assert facts["fire_events"] == 0
    assert facts["squash_events"] == 1
    # The run drained its single delayed event: conservation is exact.
    assert facts["drained"] is True
    # wake_phase counts the injection at schedule time, so for a drained run
    # applied == fired + ignored_* (the event has exactly one terminal state).
    assert s["applied"] == s["delayed_fired"] + facts["ignored_total"]


def test_positive_fire_evidence():
    path, facts = _search_evidence("fire")
    if path is None:
        pytest.skip(
            "BLOCKED: no real gem5 log shows FIRED delayed wake "
            "(delayed_fired>=1). FQ08-c positive activation is unproven. "
            "Run the dep_chain gate in docs/gem5-fi/fsu/"
            "FQ08-FP08-GATE-AUDIT.md section 3.1 and re-run this test.")
    s = facts["summary"]
    assert facts["issues"] == [], facts["issues"]
    assert s["delayed_fired"] >= 1
    assert s["activated"] >= 1        # Fire branch reached
    assert s["faults_injected"] >= 1
    # A FIRED line alone proves only that wakeDependents() was re-entered.
    # Target-state evidence requires the dependent count (woken) that the
    # current C++ discards: DelayedWake::process calls
    # wakeDependents(inst) without logging its return value.
    if not any(w is not None and w > 0 for w in facts["fire_woken"]):
        pytest.skip(
            "BLOCKED: a FIRED delayed wake exists, but no fired event records "
            "how many dependents were actually woken (woken>0). The current "
            "CHAOSIQ.cc discards wakeDependents()'s return; add `woken=<n>` "
            "to the FIRED line (FQ08-FP08-GATE-AUDIT.md section 3.1).")


def test_generation_reuse_evidence():
    path, facts = _search_evidence("generation")
    if path is None:
        pytest.skip(
            "BLOCKED: no real gem5 log shows IGNORED reason=ignore_generation "
            "(free/realloc inside the delay window unproven). See "
            "docs/gem5-fi/fsu/FQ08-FP08-GATE-AUDIT.md section 3.2.")
    assert facts["issues"] == [], facts["issues"]
    assert facts["summary"]["delayed_ignored_generation"] >= 1
    assert facts["summary"]["delayed_fired"] == 0


def test_identity_mismatch_evidence():
    path, facts = _search_evidence("identity")
    if path is None:
        pytest.skip(
            "BLOCKED: no real gem5 log shows IGNORED reason=ignore_identity. "
            "Identity is covered by the host model and source order only; see "
            "docs/gem5-fi/fsu/FQ08-FP08-GATE-AUDIT.md section 3.3.")
    assert facts["issues"] == [], facts["issues"]
    assert facts["summary"]["delayed_ignored_identity"] >= 1


# ---------------------------------------------------------------------------
# The checker itself must be able to recognise positives
# ---------------------------------------------------------------------------

def test_evaluator_recognises_synthetic_fire_and_generation():
    fire = parse_iq_evidence("\n".join([
        "Tick: 10, Site: iq_wakeDependents, mode=wake_phase, tid=0, "
        "completed_sn=5, phase_offset=+1, delayed_event=scheduled, "
        "faults_injected: 1",
        "Tick: 20, Site: iq_delayed_wake, mode=wake_phase, FIRED delayed wake "
        "(producer live, generation stable), completed_sn=5, "
        "delayed_fired=1, activated=1, faults_injected: 1",
        "CHAOS_IQ_COUNTS mode=wake_phase, eligible=1, attempted=1, applied=1, "
        "activated=1, no_victim=0, pending_attempt=0, delayed_scheduled=1, "
        "delayed_fired=1, delayed_ignored_no_inst=0, "
        "delayed_ignored_identity=0, delayed_ignored_squashed=0, "
        "delayed_ignored_generation=0, faults_injected: 1",
    ]))
    f = evaluate_iq_evidence(fire)
    assert f["fire_events"] == 1 and f["scheduled_events"] == 1
    assert f["drained"] is True and f["issues"] == []

    gen = parse_iq_evidence("\n".join([
        "Tick: 10, Site: iq_wakeDependents, mode=wake_phase, tid=0, "
        "completed_sn=5, phase_offset=+64, delayed_event=scheduled, "
        "faults_injected: 1",
        "Tick: 32010, Site: iq_delayed_wake, mode=wake_phase, IGNORED "
        "reason=ignore_generation, completed_sn=5, delayed_fired=0, "
        "delayed_ignored_generation=1, faults_injected: 1",
        "CHAOS_IQ_COUNTS mode=wake_phase, eligible=1, attempted=1, applied=1, "
        "activated=0, no_victim=0, pending_attempt=0, delayed_scheduled=1, "
        "delayed_fired=0, delayed_ignored_no_inst=0, "
        "delayed_ignored_identity=0, delayed_ignored_squashed=0, "
        "delayed_ignored_generation=1, faults_injected: 1",
    ]))
    g = evaluate_iq_evidence(gen)
    assert g["generation_events"] == 1 and g["drained"] is True
    assert g["issues"] == []


def test_evaluator_rejects_summary_event_disagreement():
    bad = parse_iq_evidence("\n".join([
        "Tick: 20, Site: iq_delayed_wake, mode=wake_phase, FIRED delayed wake",
        "CHAOS_IQ_COUNTS mode=wake_phase, eligible=1, attempted=1, applied=1, "
        "activated=0, no_victim=0, pending_attempt=0, delayed_scheduled=1, "
        "delayed_fired=0, delayed_ignored_no_inst=0, "
        "delayed_ignored_identity=0, delayed_ignored_squashed=0, "
        "delayed_ignored_generation=0, faults_injected: 1",
    ]))
    facts = evaluate_iq_evidence(bad)
    assert facts["issues"]
    assert any("FIRED" in i for i in facts["issues"])
