#!/usr/bin/env python3
"""[OOO][P1] concurrency race tests for tools/ooo_guard.py (OOO L0-L5, Subagent-B).

Phase-1 barrier G: the guard's atomicity claims must hold under REAL
process concurrency, not just sequential unit calls (plan
docs/superpowers/plans/2026-10-12-ooo-l0l5-chain-admission-scheduling.md
Task 1, Review Focus #2/#4).

  R1  8 processes race claim_acquire on ONE key      -> exactly 1 True.
  R2  8 processes race slot_acquire, max_slots=2     -> at every poll
      n_active <= 2 (holders heartbeat while holding; parent polls
      slot_status continuously); 2 is actually reached; after release
      n_active == 0 and the slots dir is empty.
  R3  A holder subprocess is REALLY SIGKILLed        -> slot_status flips
      its slot to stale; slot_reclaim_stale reclaims EXACTLY that slot,
      evidence kept under slots/stale/, live holders untouched.
  R4  50 iterations of random kill / reclaim / acquire / release churn
      -> the number of slot lock files NEVER exceeds max_slots.

Honesty note on R2/R4: the parent polls at ~10 ms, so it samples a lower
bound of the true concurrency; the guard's O_EXCL slot files make an
overrun structurally impossible, and these tests prove empirically that
no overrun is ever OBSERVED while real processes fight for the locks.

Plain-python asserts (repo style; pytest is not installed on this host).
Scratch dirs live under /home/sdc/gem5-fi-ding/runs/ooo-l0l5/tests-b
(NOT /tmp, per the L0-L5 run discipline), and are removed on exit.

Run: python3 tools/tests/test_ooo_guard_race.py
"""

import json
import os
import random
import shutil
import signal
import sys
import tempfile
import time
from multiprocessing import get_context

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
import ooo_guard  # noqa: E402

TESTS_ROOT = "/home/sdc/gem5-fi-ding/runs/ooo-l0l5/tests-b"
MP = get_context("fork")

FAILURES = []


def check(name, cond, detail=""):
    if cond:
        print(f"  PASS {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILURES.append(name)


def _write(path, data):
    with open(path, "w") as f:
        f.write(data)


def _read(path):
    with open(path, "r") as f:
        return f.read().strip()


def _wait_for(pred, timeout, what):
    """Return the first truthy pred() value, or None on timeout."""
    t0 = time.time()
    while time.time() - t0 < timeout:
        v = pred()
        if v:
            return v
        time.sleep(0.01)
    print(f"  [timeout] {what} ({timeout}s)")
    return None


# --------------------------------------------------------------------------
# child targets (fork context; they only use the args passed to them)

def _claim_racer(guard, key, result_file, release_file):
    got = ooo_guard.claim_acquire(guard, key)
    _write(result_file, "True" if got else "False")
    if got:
        while not os.path.exists(release_file):
            time.sleep(0.01)
        ooo_guard.claim_release(guard, key)


def _slot_racer(guard, owner, idx, stop_file, release_file, marker):
    """Hammer slot_acquire until a slot is won; hold + heartbeat until the
    release signal; then release. Exits without acquiring once stop is set."""
    while not os.path.exists(stop_file):
        try:
            h = ooo_guard.slot_acquire(guard, owner, "raceC",
                                       f"racer{idx:02d}", max_slots=2)
        except ooo_guard.GuardError:
            time.sleep(0.002 + random.random() * 0.01)
            continue
        _write(marker, h["path"])
        n = 0
        while not os.path.exists(release_file):
            if n % 3 == 0:
                try:
                    ooo_guard.slot_heartbeat(h)
                except ooo_guard.GuardError:
                    break  # lock lost/reclaimed -- stop holding
            time.sleep(0.02)
            n += 1
        try:
            ooo_guard.slot_release(h)
        except (OSError, ooo_guard.GuardError):
            pass
        return
    _write(marker + ".nostart", "")


def _slot_holder(guard, owner, run_id, ready_file, max_slots):
    """Acquire one slot, report the handle, hold forever (until killed)."""
    h = ooo_guard.slot_acquire(guard, owner, "raceS", run_id,
                               max_slots=max_slots)
    info = dict(path=h["path"], pid=os.getpid())
    _write(ready_file, json.dumps(info))
    while True:
        time.sleep(0.05)


# ----- R1: 8-way claim race -----------------------------------------------

def test_claim_race_8p(tmp):
    g = os.path.join(tmp, "g_claim")
    os.makedirs(os.path.join(g, "claims"), exist_ok=True)
    key = "raceC__raceC-c0000-r0000"
    resdir = os.path.join(tmp, "claim_res")
    os.makedirs(resdir)
    release = os.path.join(tmp, "claim_release.flag")
    procs = []
    for i in range(8):
        p = MP.Process(target=_claim_racer,
                       args=(g, key, os.path.join(resdir, f"c{i}.res"), release))
        p.start()
        procs.append(p)
        time.sleep(random.uniform(0, 0.01))  # de-sync the starters
    for i in range(8):
        rf = os.path.join(resdir, f"c{i}.res")
        got = _wait_for(lambda rf=rf: os.path.exists(rf), 10,
                        f"claim result {rf}")
        check(f"claim-racer{i}-reported", got is not None)
    trues = falses = 0
    for i in range(8):
        v = _read(os.path.join(resdir, f"c{i}.res"))
        if v == "True":
            trues += 1
        elif v == "False":
            falses += 1
    check("claim-race-exactly-one-true", trues == 1 and falses == 7,
          f"trues={trues} falses={falses}")
    claim_path = os.path.join(g, "claims", f"{key}.claim")
    check("claim-file-held-by-winner", os.path.exists(claim_path))
    _write(release, "")
    for p in procs:
        p.join(5)
    check("claim-released-after-signal",
          _wait_for(lambda: not os.path.exists(claim_path), 5,
                    "claim release") is not None)
    check("claim-racers-exited", all(not p.is_alive() for p in procs))


# ----- R2: 8-way slot race, max_slots=2 ------------------------------------

def test_slot_race_max2(tmp):
    g = os.path.join(tmp, "g_slots")
    os.makedirs(os.path.join(g, "slots"), exist_ok=True)
    stop = os.path.join(tmp, "slot_stop.flag")
    release = os.path.join(tmp, "slot_release.flag")
    markers = []
    for i in range(8):
        markers.append(os.path.join(tmp, f"slot_r{i}.got"))
    procs = []
    for i in range(8):
        p = MP.Process(target=_slot_racer,
                       args=(g, f"racer-{i}", i, stop, release, markers[i]))
        p.start()
        procs.append(p)
        time.sleep(random.uniform(0, 0.005))

    max_active = 0
    hb_seen = dict()   # lock path -> set of heartbeat values observed
    ok2 = _wait_for(lambda: ooo_guard.slot_status(g)["n_active"] >= 2,
                    10, "two slots held")
    check("slot-race-two-held", ok2 is not None)
    # keep polling for 1s under full pressure (race coverage + heartbeat)
    t_end = time.time() + 1.0
    while time.time() < t_end:
        st = ooo_guard.slot_status(g)
        max_active = max(max_active, st["n_active"])
        for s in st["slots"]:
            if s.get("state") == "live":
                hb_seen.setdefault(s["path"], set()).add(s.get("heartbeat"))
        time.sleep(0.01)
    check("slot-race-max-active-le-2", max_active <= 2, f"max_active={max_active}")
    check("slot-race-two-actually-held", max_active >= 2,
          f"max_active={max_active}")
    n_hb = max((len(v) for v in hb_seen.values()), default=0)
    check("slot-race-heartbeats-fresh", n_hb >= 2, f"hb_values={n_hb}")
    winners = [m for m in markers if os.path.exists(m)]
    check("slot-race-at-least-2-winners", len(winners) >= 2,
          f"winners={len(winners)}")

    _write(stop, "")
    time.sleep(0.3)
    _write(release, "")
    for p in procs:
        p.join(5)
    final = _wait_for(_slots_empty(g), 5, "all slots released")
    check("slot-race-all-released", final is not None)
    check("slot-race-procs-exited", all(not p.is_alive() for p in procs))


def _slots_empty(g):
    def pred():
        st = ooo_guard.slot_status(g)
        if st["n_active"] == 0 and st["n_slots"] == 0:
            return st
        return None
    return pred


# ----- R3: SIGKILL a real holder -> reclaim exactly its slot ----------------

def test_stale_reclaim_sigkill(tmp):
    g = os.path.join(tmp, "g_stale")
    os.makedirs(os.path.join(g, "slots"), exist_ok=True)
    h_mine1 = ooo_guard.slot_acquire(g, "parent", "raceS", "parentA",
                                     max_slots=4)
    h_mine2 = ooo_guard.slot_acquire(g, "parent", "raceS", "parentB",
                                     max_slots=4)
    ready_a = os.path.join(tmp, "holderA.ready")
    ready_b = os.path.join(tmp, "holderB.ready")
    p_a = MP.Process(target=_slot_holder,
                     args=(g, "victim", "childA", ready_a, 4))
    p_b = MP.Process(target=_slot_holder,
                     args=(g, "survivor", "childB", ready_b, 4))
    p_a.start()
    p_b.start()
    got_a = _wait_for(lambda: os.path.exists(ready_a), 10, "victim ready")
    got_b = _wait_for(lambda: os.path.exists(ready_b), 10, "survivor ready")
    check("stale-holders-started", got_a is not None and got_b is not None)
    victim_path = json.loads(_read(ready_a))["path"]
    survivor_path = json.loads(_read(ready_b))["path"]
    st = ooo_guard.slot_status(g)
    check("stale-pre-kill-4-active",
          st["n_active"] == 4 and st["n_stale"] == 0, f"status={st}")
    # REAL kill of the victim subprocess
    os.kill(p_a.pid, signal.SIGKILL)
    p_a.join(5)
    check("victim-sigkilled", not p_a.is_alive())
    flipped = _wait_for(_one_stale(g), 5, "victim slot flips stale")
    check("victim-slot-stale",
          flipped is not None and flipped["n_active"] == 3, f"st={flipped}")
    check("survivor-lock-intact", os.path.exists(survivor_path))
    check("parent-locks-intact", os.path.exists(h_mine1["path"])
          and os.path.exists(h_mine2["path"]))

    reclaimed = ooo_guard.slot_reclaim_stale(g)
    check("reclaim-exactly-victim",
          len(reclaimed) == 1
          and os.path.basename(reclaimed[0]).startswith(
              os.path.basename(victim_path) + ".")
          and not os.path.exists(victim_path),
          f"reclaimed={reclaimed} victim={victim_path}")
    stale_dir = os.path.join(g, "slots", "stale")
    ev = os.listdir(stale_dir) if os.path.isdir(stale_dir) else []
    check("reclaim-evidence-kept", len(ev) == 1, f"stale dir={ev}")
    with open(os.path.join(stale_dir, ev[0])) as f:
        evj = json.load(f)
    check("reclaim-evidence-pid-is-victim", evj.get("pid") == p_a.pid,
          f"evidence pid={evj.get('pid')} victim={p_a.pid}")
    st = ooo_guard.slot_status(g)
    check("reclaim-live-holders-unaffected",
          st["n_active"] == 3 and st["n_slots"] == 3, f"status={st}")

    # cleanup: kill the survivor too, reclaim, release the parent slots
    os.kill(p_b.pid, signal.SIGKILL)
    p_b.join(5)
    reclaimed2 = ooo_guard.slot_reclaim_stale(g)
    check("reclaim-survivor-after-kill",
          len(reclaimed2) == 1
          and os.path.basename(reclaimed2[0]).startswith(
              os.path.basename(survivor_path) + ".")
          and not os.path.exists(survivor_path),
          f"reclaimed={reclaimed2}")
    ooo_guard.slot_release(h_mine1)
    ooo_guard.slot_release(h_mine2)
    final = _wait_for(_slots_empty(g), 5, "stale test final cleanup")
    check("stale-final-clean", final is not None)


def _one_stale(g):
    def pred():
        st = ooo_guard.slot_status(g)
        if st["n_stale"] == 1:
            return st
        return None
    return pred


# ----- R4: 50-iteration kill/reclaim/acquire churn --------------------------

def test_churn_50(tmp):
    g = os.path.join(tmp, "g_churn")
    os.makedirs(os.path.join(g, "slots"), exist_ok=True)
    MAX = 3
    children = dict()   # pid -> proc handle
    parent_handles = []
    violations = []
    counters = dict(acquire=0, kill=0, reclaim=0, parent=0,
                    parent_release=0, reclaimed_total=0)

    def lock_count():
        sd = os.path.join(g, "slots")
        if not os.path.isdir(sd):
            return 0
        names = os.listdir(sd)
        return len([f for f in names if f.startswith("slot_")
                    and f.endswith(".lock")])

    def invariant(tag):
        n = lock_count()
        st = ooo_guard.slot_status(g)
        if n > MAX or st["n_active"] > MAX:
            violations.append(f"iter{tag}: locks={n} active={st['n_active']}")
    random.seed(20261012)
    for it in range(50):
        act = random.choice(["acquire", "acquire", "kill", "reclaim",
                             "parent", "parent_release"])
        if act == "acquire" and lock_count() < MAX:
            ready = os.path.join(tmp, f"churn_{it}.ready")
            p = MP.Process(target=_slot_holder,
                           args=(g, f"churn{it}", f"run{it}", ready, MAX))
            p.start()
            children[p.pid] = p
            counters["acquire"] += 1
        elif act == "kill" and children:
            pid = random.choice(list(children))
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            children[pid].join(2)
            del children[pid]
            counters["kill"] += 1
        elif act == "reclaim":
            reclaimed = ooo_guard.slot_reclaim_stale(g)
            counters["reclaim"] += 1
            counters["reclaimed_total"] += len(reclaimed)
        elif act == "parent" and lock_count() < MAX:
            h = ooo_guard.slot_acquire(g, "parentchurn", "churnP", f"p{it}",
                                       max_slots=MAX)
            parent_handles.append(h)
            counters["parent"] += 1
        elif act == "parent_release" and parent_handles:
            h = parent_handles.pop(random.randrange(len(parent_handles)))
            ooo_guard.slot_release(h)
            counters["parent_release"] += 1
        invariant(it)

    check("churn-coverage", counters["acquire"] >= 1 and counters["kill"] >= 1
          and counters["reclaim"] >= 1, f"counters={counters}")
    check("churn-no-slot-overrun", not violations,
          f"violations={violations[:5]}")
    print(f"  [churn] counters={counters}")
    # teardown: kill every child, reclaim, release parent-held slots
    for pid in list(children):
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        children[pid].join(2)
    ooo_guard.slot_reclaim_stale(g)
    for h in parent_handles:
        ooo_guard.slot_release(h)
    final = _wait_for(_slots_empty(g), 5, "churn final cleanup")
    check("churn-final-clean", final is not None)


def main():
    os.makedirs(TESTS_ROOT, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="guard-race-", dir=TESTS_ROOT)
    try:
        print("test_claim_race_8p (R1):")
        test_claim_race_8p(tmp)
        print("test_slot_race_max2 (R2):")
        test_slot_race_max2(tmp)
        print("test_stale_reclaim_sigkill (R3):")
        test_stale_reclaim_sigkill(tmp)
        print("test_churn_50 (R4):")
        test_churn_50(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    n = len(FAILURES)
    print(f"\n{'ALL PASS' if n == 0 else 'FAILURES: ' + repr(FAILURES)}")
    return 1 if n else 0


if __name__ == "__main__":
    sys.exit(main())
