"""FQ08-b / FQ08-c regression tests (offline; no gem5 build/run).

Two deliberately separated layers:

SOURCE CONTRACT (keys ``source_*``/``test_fq08*``):
    Exact text assertions on the real vendored C++ (CHAOSIQ.cc/.hh and the
    pure header).  These prove the code SHAPE (who counts, what is checked in
    which order); they are NOT runtime evidence.

OFFLINE BEHAVIOUR (keys ``test_*_behavior``/``test_lifecycle_*``):
    A pure-Python replica of ``chaos_iq_lifecycle.hh`` (counters, victim
    choice, duplicate-wake suppression, classifyWake).  It validates the
    RULES with concrete values.  A passing replica is still not gem5
    evidence: real-run evidence is the existing gate logs cited in
    docs/gem5-fi/fsu/FQ08-FP08-REGRESSION.md.

The C++ host unit test (tests/unit/chaos_iq_lifecycle_test.cc) is NOT
compiled here by design.  We only inspect which semantics it covers, and
re-express the same rules in Python so this suite stays a pure pytest run.
"""
import ast
import re
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IQ_DIR = ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSIQ"
IQ_CC = IQ_DIR / "CHAOSIQ.cc"
IQ_HH = IQ_DIR / "CHAOSIQ.hh"
MODEL_HH = IQ_DIR / "chaos_iq_lifecycle.hh"
CPP_UNIT = ROOT / "tests/unit/chaos_iq_lifecycle_test.cc"


def _code(path):
    assert path.is_file(), path
    return path.read_text(encoding="utf-8", errors="replace")


def _function_body(src, name):
    """Return one CHAOSIQ method body, anchored at its column-0 definition.

    Anchoring matters: several names (e.g. ``maybeApplyWrongSourceWake`` and
    ``shouldWrongSourceWake``) also appear as indented call sites inside other
    methods, and those call sites are not definitions.
    """
    m = re.search(rf"^\s*CHAOSIQ::{re.escape(name)}\(", src, re.M)
    assert m is not None, name
    end = src.find("\n    }\n", m.start())
    assert end != -1, name
    return src[m.start():end]


def _model_body(src, name):
    """Return one column-0 inline function body from the pure model header."""
    m = re.search(rf"^{re.escape(name)}\(", src, re.M)
    assert m is not None, name
    end = src.find("\n}\n", m.start())
    assert end != -1, name
    return src[m.start():end]


def _struct_body(src, name):
    m = re.search(r"struct %s\s*\{(.*?)\n\};" % re.escape(name), src, re.S)
    assert m is not None, name
    return m.group(1)


# ---------------------------------------------------------------------------
# Offline replica of chaos_iq_lifecycle.hh (rules, not runtime evidence)
# ---------------------------------------------------------------------------

@dataclass
class Counters:
    eligible: int = 0
    attempted: int = 0
    applied: int = 0
    activated: int = 0
    no_victim: int = 0


@dataclass
class Attempt:
    pending: bool = False
    producer_sn: int = 0
    producer_tid: int = 0
    tick: int = 0


def begin_attempt(att, producer_sn, producer_tid, tick):
    att.pending = True
    att.producer_sn = producer_sn
    att.producer_tid = producer_tid
    att.tick = tick


def abort_pending_attempt(att, counters):
    if not att.pending:
        return False
    att.pending = False
    counters.no_victim += 1
    return True


@dataclass
class VictimView:
    squashed: bool = False
    issued: bool = False
    ready_regs: int = 0
    num_src_regs: int = 0
    slot: list = field(default_factory=list)
    flat: list = field(default_factory=list)
    unready: list = field(default_factory=list)


def victim_eligible(v):
    return (not v.squashed and not v.issued and
            v.ready_regs < v.num_src_regs)


def choose_wrong_slot(v, chain_flat):
    if not victim_eligible(v):
        return -1
    for i, slot in enumerate(v.slot):
        if not v.unready[i]:
            continue
        if i < len(v.flat) and v.flat[i] == chain_flat:
            continue
        return slot
    return -1


def note_applied(counters, issueable_before, issueable_after):
    counters.applied += 1
    activated = (not issueable_before) and issueable_after
    if activated:
        counters.activated += 1
    return activated


@dataclass
class DuplicateWake:
    tracked: bool = False
    victim_sn: int = 0
    victim_tid: int = 0
    corrupt_flat: int = 0


def record_duplicate_wake(d, victim_sn, victim_tid, corrupt_flat):
    d.tracked = True
    d.victim_sn = victim_sn
    d.victim_tid = victim_tid
    d.corrupt_flat = corrupt_flat


def suppress_duplicate_wake(d, dep_sn, dep_tid, chain_flat):
    if not d.tracked:
        return False
    if (dep_sn != d.victim_sn or dep_tid != d.victim_tid or
            chain_flat != d.corrupt_flat):
        return False
    d.tracked = False
    return True


@dataclass(frozen=True)
class DestStamp:
    flat: int = (1 << 64) - 1
    generation: int = 0


@dataclass
class WakeStamp:
    seq_num: int = 0
    tid: int = 0
    dests: list = field(default_factory=list)


@dataclass
class WakeObserved:
    has_inst: bool = False
    seq_num: int = 0
    tid: int = 0
    squashed: bool = False
    dests: list = field(default_factory=list)


@dataclass
class DelayedWakeCounters:
    scheduled: int = 0
    fired: int = 0
    ignored_no_inst: int = 0
    ignored_identity: int = 0
    ignored_squashed: int = 0
    ignored_generation: int = 0


FIRE = "fire"
NO_INST = "ignore_no_inst"
IDENTITY = "ignore_identity"
SQUASHED = "ignore_squashed"
GENERATION = "ignore_generation"


def classify_wake(stamp, now):
    """Mirror classifyWake: identity -> squash -> dest count -> generation."""
    if not now.has_inst:
        return NO_INST
    if now.seq_num != stamp.seq_num or now.tid != stamp.tid:
        return IDENTITY
    if now.squashed:
        return SQUASHED
    if len(now.dests) != len(stamp.dests):
        return IDENTITY
    for old, new in zip(stamp.dests, now.dests):
        if old != new:
            return GENERATION
    return FIRE


def note_wake_decision(c, decision):
    if decision == FIRE:
        c.fired += 1
    elif decision == NO_INST:
        c.ignored_no_inst += 1
    elif decision == IDENTITY:
        c.ignored_identity += 1
    elif decision == SQUASHED:
        c.ignored_squashed += 1
    elif decision == GENERATION:
        c.ignored_generation += 1


def _stamp():
    return WakeStamp(seq_num=4242, tid=0,
                     dests=[DestStamp(96, 3), DestStamp(97, 5)])


def _now(stamp):
    return WakeObserved(has_inst=True, seq_num=stamp.seq_num, tid=stamp.tid,
                        squashed=False, dests=list(stamp.dests))


# ---------------------------------------------------------------------------
# FQ08-b source contract
# ---------------------------------------------------------------------------

def test_fq08b_counters_are_separate_in_model():
    model = _code(MODEL_HH)
    c = _struct_body(model, "Counters")
    for f in ("eligible", "attempted", "applied", "activated", "no_victim"):
        assert re.search(r"uint64_t %s\s*=" % f, c), f

    abort = _model_body(model, "abortPendingAttempt")
    assert "++c.no_victim;" in abort
    assert "applied" not in abort and "activated" not in abort

    applied = _model_body(model, "noteApplied")
    assert "++c.applied;" in applied
    assert "++c.activated;" in applied
    assert "no_victim" not in applied


def test_fq08b_gate_only_records_an_attempt():
    src = _code(IQ_CC)
    body = _function_body(src, "shouldWrongSourceWake")
    assert "if (fi_mode != Mode::SrcReadyBitflip) return false;" in body
    assert "abortPendingAttempt(ws_attempt, iq_counts)" in body
    assert "beginAttempt(ws_attempt" in body
    assert "iq_counts.attempted++" in body
    assert "faults_injected_count++" not in body
    assert "iq_counts.applied++" not in body
    assert "return false" in body
    assert "return true" not in body


def test_fq08b_apply_requires_a_real_victim_and_order_is_victim_first():
    src = _code(IQ_CC)
    body = _function_body(src, "maybeApplyWrongSourceWake")
    assert "if (!ws_attempt.pending || !dep_inst) return;" in body
    choose = body.find("chooseWrongSlot(")
    apply = body.find("markSrcRegReady(")
    count = body.find("faults_injected_count++")
    assert -1 not in (choose, apply, count)
    assert choose < apply < count
    assert "if (slot < 0) return;" in body
    assert "ws_attempt.pending = false;" in body
    assert "recordDuplicateWake(" in body
    for f in ("victim_sn", "victim_pc", "victim_op_class", "victim_src_slot",
              "victim_src_phys", "victim_src_class", "victim_src_flat",
              "victim_src_generation", "wrong_of_chain_flat", "producer_sn",
              "producer_wake_tick"):
        assert f in body, f
    # Real state change is logged, not inferred.
    assert "ready_regs " in body and "-> " in body


def test_fq08b_budget_is_consumed_only_when_applied():
    src = _code(IQ_CC)
    gate = _function_body(src, "shouldWrongSourceWake")
    apply = _function_body(src, "maybeApplyWrongSourceWake")
    # The budget guard reads the same counter that only apply increments.
    assert ("max_faults != 0 && faults_injected_count >= max_faults" in gate)
    assert "faults_injected_count++" in apply
    # The FQ08-b suppression branch does not touch the budget. (The later
    # D48/D49 ready_never branch in the same callback legitimately does; it is
    # a different mode and is checked separately below.)
    suppress = _function_body(src, "shouldSuppressReadyMark")
    fq08b_part = suppress[:suppress.find("// W5.10 D48/D49")]
    assert fq08b_part and "faults_injected_count++" not in fq08b_part


def test_fq08b_duplicate_genuine_wake_suppressed_once():
    src = _code(IQ_CC)
    body = _function_body(src, "shouldSuppressReadyMark")
    assert "Mode::SrcReadyBitflip" in body
    assert "chaos_iq_lifecycle::suppressDuplicateWake(" in body
    # FQ08-b must be handled before the ready_never branch (which also
    # consumes the same dependent-loop callback).
    assert body.find("Mode::SrcReadyBitflip") < body.find("Mode::ReadyNever")
    model = _code(MODEL_HH)
    track = _model_body(model, "suppressDuplicateWake")
    assert "d.tracked = false;" in track
    assert "return true;" in track


def test_fq08b_summary_line_exposes_all_separate_counters():
    src = _code(IQ_CC)
    dump = _function_body(src, "dumpIqCounts")
    assert "CHAOS_IQ_COUNTS" in dump
    for f in ("eligible=", "attempted=", "applied=", "activated=",
              "no_victim=", "pending_attempt=", "faults_injected: "):
        assert f in dump, f
    assert "registerExitCallback([this]() { dumpIqCounts(); });" in src


# ---------------------------------------------------------------------------
# FQ08-c source contract
# ---------------------------------------------------------------------------

def test_fq08c_legacy_delayed_wake_path_is_closed():
    src = _code(IQ_CC)
    delay = _function_body(src, "shouldDelayWake")
    assert "return false;" in delay
    assert "cpu->schedule" not in delay
    assert "new DelayedWakeEvent" not in delay
    omit = _function_body(src, "shouldOmitWake")
    assert "new DelayedWake(" in omit
    assert "snapshotWakeStamp(" in omit
    assert "faults_injected_count++" in omit
    assert "delayed_event=scheduled" in omit


def test_fq08c_event_is_refcounted_value_snapshot_without_iq_pointer():
    hh = _code(IQ_HH)
    m = re.search(r"class DelayedWake : public Event\s*\{(.*?)\n    \};",
                  hh, re.S)
    assert m is not None
    ev = m.group(1)
    assert "o3::DynInstPtr inst;" in ev
    assert "chaos_iq_lifecycle::WakeStamp stamp;" in ev
    assert "InstructionQueue" not in ev
    # AutoDelete is set by the constructor in CHAOSIQ.cc.
    assert "Event(Default_Pri, AutoDelete)" in _code(IQ_CC)
    # The pure stamp is a value snapshot: flat id + allocation generation.
    model = _code(MODEL_HH)
    dst = _struct_body(model, "DestStamp")
    assert "uint64_t flat" in dst and "uint32_t generation" in dst
    wake = _struct_body(model, "WakeStamp")
    assert "seq_num" in wake and "tid" in wake and "dests" in wake


def test_fq08c_classify_before_wake_and_order_is_documented_and_coded():
    src = _code(IQ_CC)
    proc = _function_body(src, "DelayedWake::process")
    classify = proc.find("chaos_iq_lifecycle::classifyWake(stamp, now)")
    wake = proc.find("wakeDependents(inst)")
    assert -1 not in (classify, wake)
    assert classify < wake
    assert "WakeDecision::Fire" in proc
    assert "noteDelayedWakeIgnored(decision, inst)" in proc

    model = _code(MODEL_HH)
    cls = _model_body(model, "classifyWake")
    order = [cls.find("!now.has_inst"),
             cls.find("now.seq_num != stamp.seq_num"),
             cls.find("now.squashed"),
             cls.find("now.dests.size() != stamp.dests.size()"),
             cls.find("stamp.dests[i] != now.dests[i]")]
    assert -1 not in order
    assert order == sorted(order)


def test_fq08c_ignored_events_are_logged_without_counting_as_injection():
    src = _code(IQ_CC)
    body = _function_body(src, "noteDelayedWakeIgnored")
    assert "IGNORED reason=" in body
    assert "faults_injected: " in body
    for f in ("delayed_ignored_squashed=", "delayed_ignored_generation=",
              "delayed_ignored_identity="):
        assert f in body, f
    dump = _function_body(src, "dumpIqCounts")
    for f in ("delayed_scheduled=", "delayed_fired=",
              "delayed_ignored_no_inst=", "delayed_ignored_identity=",
              "delayed_ignored_squashed=", "delayed_ignored_generation="):
        assert f in dump, f


def test_fq08c_replay_guard_and_end_of_run_cleanup():
    src = _code(IQ_CC)
    om = _function_body(src, "shouldOmitWake")
    assert "if (replaying_delayed_wake) return false;" in om
    proc = _function_body(src, "DelayedWake::process")
    assert "replaying_delayed_wake = true;" in proc
    assert "replaying_delayed_wake = false;" in proc
    # AutoDelete is set in the event constructor: an ignored/fired event is
    # deleted by the event queue, no explicit owner cleanup required.
    assert "Event(Default_Pri, AutoDelete)" in src
    # An ignored event returns before any queue access.
    ignore_ret = proc.find("if (decision != chaos_iq_lifecycle::WakeDecision::Fire)")
    assert ignore_ret != -1
    assert ignore_ret < proc.find("wakeDependents(inst)")


# ---------------------------------------------------------------------------
# Other CHAOSIQ modes must be unaffected by the FQ08 changes
# ---------------------------------------------------------------------------

def test_other_modes_still_initialize_and_count_normally():
    src = _code(IQ_CC)
    # Mode parser still accepts every previously supported mode.
    parser = _function_body(src, "stringToMode")
    for m in ("src_ready_bitflip", "wake_phase", "ready_early",
              "ready_never", "ready_never_event", "tag_swap", "tag_bitflip",
              "tag_bitflip2", "tag_stuck", "tag_stale_read",
              "dispatch_misroute"):
        assert '"%s"' % m in parser, m

    # wake_omit still drops a broadcast AND consumes one budget unit.
    omit = _function_body(src, "shouldOmitWake")
    assert "iq_counts.applied++" in omit
    assert "faults_injected_count++" in omit
    assert "return true;  // caller skips the wakeup broadcast" in omit

    # The insert/wake/issue hooks keep their own counters.
    early = _function_body(src, "maybeReadyEarly")
    assert "faults_injected_count++" in early
    never = _function_body(src, "shouldSuppressReadyMark")
    assert "faults_injected_count++" in never
    misroute = _function_body(src, "maybeMisrouteFU")
    assert "faults_injected_count++" in misroute
    assert "gateEligible()" in src


def test_fq08b_does_not_capture_tag_stuck_wake_accounting():
    src = _code(IQ_CC)
    body = _function_body(src, "noteTagWake")
    assert "if (fi_mode == Mode::SrcReadyBitflip)" in body
    assert "maybeApplyWrongSourceWake(dep_inst, chain_flat);" in body
    # The tag_stuck evidence path is still below and still gated on its mode.
    assert "fi_mode != Mode::TagStuck || !tag_stuck_armed" in body


# ---------------------------------------------------------------------------
# C++ host unit test: inspect coverage only (NO g++ invocation)
# ---------------------------------------------------------------------------

def test_cpp_host_unit_test_covers_the_same_semantics_without_compiling():
    unit = _code(CPP_UNIT)
    assert "ALL CHAOS IQ LIFECYCLE CHECKS PASSED" in unit
    # Pure model: no gem5 includes.
    for inc in re.findall(r"^\s*#include\s+[<\"]([^>\"]+)[>\"]", unit, re.M):
        assert not inc.startswith(("params/", "sim/", "cpu/", "base/",
                                   "arch/", "mem/")), inc
    for needle in (
        "REPRO old gate counts 1 injection with no victim",
        "REPRO fixed model counts 0 injections",
        "chain slot rejected as victim",
        "wrong source slot chosen",
        "wrong write makes victim issueable",
        "three no-victim attempts consumed no budget",
        "squash => wakeDependents NOT called",
        "reused slot => new owner is NOT woken",
        "all destinations must match",
        "old event never fired after squash/reuse",
        "genuine wake of the corrupted source suppressed",
        "suppression is one-shot",
    ):
        assert needle in unit, needle
    # This suite intentionally never compiles it (the task forbids g++/scons
    # here); the behaviour is re-derived in Python below instead. Parse the
    # module AST rather than grepping text (the word appears in this comment).
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
    assert "subprocess" not in imported


# ---------------------------------------------------------------------------
# FQ08-b offline behaviour
# ---------------------------------------------------------------------------

def test_no_victim_behavior_touches_no_applied_or_activated():
    c = Counters()
    att = Attempt()
    c.eligible += 1
    begin_attempt(att, 100, 0, 500)
    c.attempted += 1
    assert abort_pending_attempt(att, c)
    assert c.applied == 0
    assert c.activated == 0
    assert c.no_victim == 1
    assert not att.pending


def test_only_the_woken_chain_is_not_a_victim_behavior():
    c = Counters()
    att = Attempt()
    begin_attempt(att, 101, 0, 600)
    v = VictimView(ready_regs=1, num_src_regs=2,
                   slot=[0], flat=[7], unready=[1])
    assert choose_wrong_slot(v, chain_flat=7) == -1
    abort_pending_attempt(att, c)
    assert c.applied == 0 and c.no_victim == 1


def test_real_victim_gets_wrong_slot_and_state_change_behavior():
    c = Counters()
    v = VictimView(ready_regs=0, num_src_regs=2,
                   slot=[0, 1], flat=[100, 200], unready=[1, 1])
    slot = choose_wrong_slot(v, chain_flat=100)
    assert slot == 1, "must not pick the chain being woken"
    # The write changes ready 0 -> 1 of 2: applied but not issueable.
    activated = note_applied(c, issueable_before=False,
                             issueable_after=(0 + 1 == 2))
    assert c.applied == 1 and c.activated == 0 and activated is False


def test_activated_is_a_strict_subset_of_applied_behavior():
    c = Counters()
    v = VictimView(ready_regs=1, num_src_regs=2,
                   slot=[0], flat=[200], unready=[1])
    assert choose_wrong_slot(v, 100) == 0
    assert note_applied(c, False, True) is True
    assert (c.applied, c.activated) == (1, 1)
    # A later applied-but-not-issueable event must not move activated.
    note_applied(c, False, False)
    assert (c.applied, c.activated) == (2, 1)


def test_squashed_issued_fully_ready_rejected_behavior():
    base = dict(ready_regs=1, num_src_regs=2, slot=[0], flat=[200],
                unready=[1])
    assert choose_wrong_slot(VictimView(squashed=True, **base), 100) == -1
    assert choose_wrong_slot(VictimView(issued=True, **base), 100) == -1
    assert choose_wrong_slot(
        VictimView(ready_regs=2, num_src_regs=2, slot=[0], flat=[200],
                   unready=[0]), 100) == -1


def test_budget_only_consumed_on_apply_behavior():
    c = Counters()
    att = Attempt()
    budget = 0
    for i in range(3):
        c.attempted += 1
        begin_attempt(att, 200 + i, 0, 900 + i)
        empty = VictimView(ready_regs=1, num_src_regs=1)
        if choose_wrong_slot(empty, 0) < 0:
            abort_pending_attempt(att, c)
        else:
            budget += 1
    assert budget == 0 and c.no_victim == 3 and c.applied == 0

    v = VictimView(ready_regs=1, num_src_regs=2,
                   slot=[0], flat=[300], unready=[1])
    c.attempted += 1
    begin_attempt(att, 300, 0, 1000)
    if choose_wrong_slot(v, 100) >= 0:
        if note_applied(c, False, True):
            budget += 1
        else:
            budget += 1
    assert budget == 1
    assert (c.attempted, c.applied) == (4, 1)


def test_duplicate_wake_suppression_is_one_shot_behavior():
    d = DuplicateWake()
    record_duplicate_wake(d, 777, 0, 200)
    assert not suppress_duplicate_wake(d, 778, 0, 200)
    assert not suppress_duplicate_wake(d, 777, 1, 200)
    assert not suppress_duplicate_wake(d, 777, 0, 300)
    assert d.tracked
    assert suppress_duplicate_wake(d, 777, 0, 200)
    assert not d.tracked
    assert not suppress_duplicate_wake(d, 777, 0, 200)


# ---------------------------------------------------------------------------
# FQ08-c offline behaviour
# ---------------------------------------------------------------------------

def test_lifecycle_normal_fire_behavior():
    s = _stamp()
    d = DelayedWakeCounters()
    decision = classify_wake(s, _now(s))
    note_wake_decision(d, decision)
    assert decision == FIRE
    assert d.fired == 1
    assert (d.ignored_no_inst, d.ignored_identity, d.ignored_squashed,
            d.ignored_generation) == (0, 0, 0, 0)


def test_lifecycle_squash_ignored_behavior():
    s = _stamp()
    now = _now(s)
    now.squashed = True
    d = DelayedWakeCounters()
    decision = classify_wake(s, now)
    note_wake_decision(d, decision)
    assert decision == SQUASHED
    assert d.ignored_squashed == 1 and d.fired == 0


def test_lifecycle_generation_reuse_ignored_behavior():
    s = _stamp()
    now = _now(s)
    now.dests[0] = DestStamp(96, s.dests[0].generation + 1)
    d = DelayedWakeCounters()
    decision = classify_wake(s, now)
    note_wake_decision(d, decision)
    assert decision == GENERATION
    assert d.ignored_generation == 1 and d.fired == 0


def test_lifecycle_all_destinations_must_match_behavior():
    s = _stamp()
    now = _now(s)
    now.dests[1] = DestStamp(97, 6)
    assert classify_wake(s, now) == GENERATION


def test_lifecycle_identity_and_no_inst_behavior():
    s = _stamp()
    n = _now(s)
    n.seq_num += 1
    assert classify_wake(s, n) == IDENTITY
    n = _now(s)
    n.tid = 1
    assert classify_wake(s, n) == IDENTITY
    n = _now(s)
    n.dests.pop()
    assert classify_wake(s, n) == IDENTITY
    assert classify_wake(s, WakeObserved()) == NO_INST


def test_lifecycle_identity_beats_squash_and_generation():
    # Order matters: a mismatched object is not "our squashed producer".
    s = _stamp()
    n = _now(s)
    n.seq_num += 1
    n.squashed = True
    n.dests[0] = DestStamp(96, 99)
    assert classify_wake(s, n) == IDENTITY


def test_lifecycle_stale_event_cannot_wake_reused_slot_behavior():
    # Old event for (flat 96, gen 3). The cell is freed and reallocated to a
    # NEW producer (gen 4). Firing the stale event must not wake the new
    # occupant: classify ignores it and the wake call count stays 0.
    s = _stamp()
    new_owner = _now(s)
    new_owner.seq_num = 999      # new producer
    new_owner.dests[0] = DestStamp(96, 4)
    wake_calls = 0
    decision = classify_wake(s, new_owner)
    if decision == FIRE:
        wake_calls += 1
    assert decision == IDENTITY   # identity is checked before generation
    assert wake_calls == 0

    # Same identity, only the generation moved: the event belongs to the old
    # allocation and is still ignored.
    same_inst = _now(s)
    same_inst.dests[0] = DestStamp(96, 4)
    assert classify_wake(s, same_inst) == GENERATION
    assert wake_calls == 0


def test_lifecycle_one_counter_per_event_behavior():
    s = _stamp()
    d = DelayedWakeCounters()
    events = [
        (s, _now(s)),
        (s, WakeObserved()),
        (s, WakeObserved(has_inst=True, seq_num=1, tid=0,
                         dests=list(s.dests))),
        (s, WakeObserved(has_inst=True, seq_num=s.seq_num, tid=0,
                         squashed=True, dests=list(s.dests))),
        (s, WakeObserved(has_inst=True, seq_num=s.seq_num, tid=0,
                         dests=[DestStamp(96, 8), DestStamp(97, 9)])),
    ]
    for stamp, now in events:
        note_wake_decision(d, classify_wake(stamp, now))
    assert d.fired == 1
    assert d.ignored_no_inst == 1
    assert d.ignored_identity == 1
    assert d.ignored_squashed == 1
    assert d.ignored_generation == 1
    assert sum(vars(d).values()) == 5


def test_lifecycle_squash_then_reuse_then_local_event_fires():
    # Sequence from the host unit test: one old event sees squash, then slot
    # reuse; a separate, normal event still fires. The old event never
    # resurrects.
    s = _stamp()
    d = DelayedWakeCounters()
    squashed = _now(s)
    squashed.squashed = True
    note_wake_decision(d, classify_wake(s, squashed))
    reused = _now(s)
    reused.dests[0] = DestStamp(96, s.dests[0].generation + 1)
    note_wake_decision(d, classify_wake(s, reused))
    normal = _now(s)
    note_wake_decision(d, classify_wake(s, normal))
    assert d.ignored_squashed == 1
    assert d.ignored_generation == 1
    assert d.fired == 1
