#!/usr/bin/env python3
"""[OOO][P1] unit test for tools/ooo_guard.py (L0-L5 run, 2026-10-12).

Pins the host-global guard contract from
docs/superpowers/plans/2026-10-12-ooo-l0l5-chain-admission-scheduling.md
Task 1:

  * slot locks: atomic O_EXCL acquire, identity-checked release,
    max_slots enforcement
  * stale reclamation: ONLY when the recorded pid is gone OR its
    /proc/<pid> starttime no longer matches (PID-reuse safe); a live,
    matching process is NEVER reclaimed
  * foreign locks are never released by a non-owner
  * claims: exclusive per (campaign, run_id) key, independent keys
    don't interfere
  * sample_resources(): full shape, sane values

Plain-python asserts (repo style; pytest is not installed on this host).
Run: python3 tools/tests/test_ooo_guard_l0l5.py
"""

import json
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
import ooo_guard  # noqa: E402


FAILURES = []


def check(name, cond, detail=""):
    if cond:
        print(f"  PASS {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILURES.append(name)


def test_slot_acquire_release(tmp):
    g = os.path.join(tmp, "guard_a")
    os.makedirs(os.path.join(g, "slots"), exist_ok=True)
    h1 = ooo_guard.slot_acquire(g, "worker-1", "cA", "r0001", max_slots=2)
    h2 = ooo_guard.slot_acquire(g, "worker-2", "cA", "r0002", max_slots=2)
    check("acquire-1", h1 is not None and h1["index"] != h2["index"])
    try:
        ooo_guard.slot_acquire(g, "worker-3", "cA", "r0003", max_slots=2)
        check("acquire-full-rejects", False, "third acquire unexpectedly succeeded")
    except ooo_guard.GuardError:
        check("acquire-full-rejects", True)
    ooo_guard.slot_release(h1)
    h3 = ooo_guard.slot_acquire(g, "worker-3", "cA", "r0003", max_slots=2)
    check("release-then-reacquire", h3 is not None)
    ooo_guard.slot_release(h2)
    ooo_guard.slot_release(h3)
    st = ooo_guard.slot_status(g)
    check("all-free-after-release", st["n_active"] == 0 and st["n_slots"] == 0
          and st["n_stale"] == 0,
          f"status={st}")


def test_stale_reclaim(tmp):
    g = os.path.join(tmp, "guard_b")
    slots = os.path.join(g, "slots")
    os.makedirs(slots, exist_ok=True)
    # 1) recorded pid does not exist -> stale
    dead = os.path.join(slots, "slot_0.lock")
    with open(dead, "w") as f:
        json.dump({"owner": "w", "pid": 999999, "pgid": 999999,
                   "starttime": 12345, "campaign": "c", "run_id": "r",
                   "acquired": "t", "heartbeat": "t"}, f)
    # 2) recorded pid exists but starttime mismatch (PID reuse) -> stale
    reused = os.path.join(slots, "slot_1.lock")
    with open(reused, "w") as f:
        json.dump({"owner": "w", "pid": 1, "pgid": 1,
                   "starttime": 999999999, "campaign": "c", "run_id": "r",
                   "acquired": "t", "heartbeat": "t"}, f)
    # 3) pid exists AND starttime matches -> LIVE, must NOT be reclaimed
    live = os.path.join(slots, "slot_2.lock")
    st1 = ooo_guard.proc_starttime(1)
    with open(live, "w") as f:
        json.dump({"owner": "w", "pid": 1, "pgid": 1,
                   "starttime": st1, "campaign": "c", "run_id": "r",
                   "acquired": "t", "heartbeat": "t"}, f)
    reclaimed = ooo_guard.slot_reclaim_stale(g)
    check("reclaim-dead-pid", dead not in reclaimed and not os.path.exists(dead))
    check("reclaim-pid-reuse", reused not in reclaimed and not os.path.exists(reused))
    check("keep-live-pid", os.path.exists(live) and live in [r["path"] for r in []] or os.path.exists(live))
    check("reclaim-returns-list", isinstance(reclaimed, list) and len(reclaimed) == 2,
          f"got {reclaimed}")
    # stale evidence preserved, not deleted
    stale_dir = os.path.join(slots, "stale")
    check("stale-evidence-kept", os.path.isdir(stale_dir)
          and len(os.listdir(stale_dir)) == 2)


def test_slot_release_foreign(tmp):
    g = os.path.join(tmp, "guard_c")
    os.makedirs(os.path.join(g, "slots"), exist_ok=True)
    st1 = ooo_guard.proc_starttime(1)
    foreign = {"path": os.path.join(g, "slots", "slot_0.lock"),
               "index": 0, "owner": "someone-else", "pid": 1}
    with open(foreign["path"], "w") as f:
        json.dump({"owner": "someone-else", "pid": 1, "pgid": 1,
                   "starttime": st1, "campaign": "c", "run_id": "r",
                   "acquired": "t", "heartbeat": "t"}, f)
    try:
        ooo_guard.slot_release(foreign)
        check("foreign-release-rejected", False, "released a live foreign lock")
    except ooo_guard.GuardError:
        check("foreign-release-rejected", True)
    check("foreign-lock-still-there", os.path.exists(foreign["path"]))


def test_slot_json_fields(tmp):
    g = os.path.join(tmp, "guard_d")
    os.makedirs(os.path.join(g, "slots"), exist_ok=True)
    h = ooo_guard.slot_acquire(g, "w-json", "cJ", "rJ", max_slots=4, node=1)
    with open(h["path"]) as f:
        j = json.load(f)
    need = {"owner", "pid", "pgid", "starttime", "node", "campaign",
            "run_id", "acquired", "heartbeat"}
    check("json-fields", need <= set(j), f"missing {need - set(j)}")
    check("json-pid-is-us", j["pid"] == os.getpid())
    check("json-starttime-real", j["starttime"] == ooo_guard.proc_starttime(os.getpid()))
    ooo_guard.slot_heartbeat(h)
    with open(h["path"]) as f:
        j2 = json.load(f)
    check("heartbeat-updates", j2["heartbeat"] >= j["heartbeat"] and j2["pid"] == j["pid"])
    ooo_guard.slot_release(h)


def test_claim_exclusive(tmp):
    g = os.path.join(tmp, "guard_e")
    os.makedirs(os.path.join(g, "claims"), exist_ok=True)
    k1 = "formal_D01-F0-W6-c__formal_D01-F0-W6-c-c0000-r0000"
    k2 = "formal_D02-F0-W6-b__formal_D02-F0-W6-b-c0000-r0000"
    check("claim-first", ooo_guard.claim_acquire(g, k1) is True)
    check("claim-second-rejected", ooo_guard.claim_acquire(g, k1) is False)
    check("claim-other-key-ok", ooo_guard.claim_acquire(g, k2) is True)
    ooo_guard.claim_release(g, k1)
    check("claim-release-then-reacquire", ooo_guard.claim_acquire(g, k1) is True)
    ooo_guard.claim_release(g, k1)
    ooo_guard.claim_release(g, k2)
    # golden claims are a separate namespace with the same exclusivity
    os.makedirs(os.path.join(g, "goldens"), exist_ok=True)
    check("golden-claim-first", ooo_guard.golden_claim_acquire(g, "gk1") is True)
    check("golden-claim-second", ooo_guard.golden_claim_acquire(g, "gk1") is False)
    ooo_guard.golden_claim_release(g, "gk1")


def test_resources_shape():
    r = ooo_guard.sample_resources("/home/sdc/gem5-fi-ding/runs")
    need = {"mem_available_kib", "swap_free_kib", "pswpin_cum", "pswpout_cum",
            "load1", "load5", "load15", "procs_blocked", "procs_running",
            "disk_free_bytes", "gem5_pids", "gem5_rss_kib", "ts"}
    check("resources-keys", need <= set(r), f"missing {need - set(r)}")
    check("resources-mem-positive", r["mem_available_kib"] > 1024 * 1024)
    check("resources-gem5-list", isinstance(r["gem5_pids"], list))
    check("resources-disk", r["disk_free_bytes"] > 1024 ** 3)


def main():
    with tempfile.TemporaryDirectory(prefix="ooo-guard-test-") as tmp:
        print("test_slot_acquire_release:")
        test_slot_acquire_release(tmp)
        print("test_stale_reclaim:")
        test_stale_reclaim(tmp)
        print("test_slot_release_foreign:")
        test_slot_release_foreign(tmp)
        print("test_slot_json_fields:")
        test_slot_json_fields(tmp)
        print("test_claim_exclusive:")
        test_claim_exclusive(tmp)
        print("test_resources_shape:")
        test_resources_shape()
    n = len(FAILURES)
    print(f"\n{'ALL PASS' if n == 0 else 'FAILURES: ' + repr(FAILURES)}")
    sys.exit(1 if n else 0)


if __name__ == "__main__":
    main()
