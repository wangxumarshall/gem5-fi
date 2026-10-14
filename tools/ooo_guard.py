#!/usr/bin/env python3
"""ooo_guard.py -- host-global guard for the OOO L0-L5 fault-injection runs
(plan docs/superpowers/plans/2026-10-12-ooo-l0l5-chain-admission-scheduling.md
Task 1; task-book §三.1).

One guard directory (default /home/sdc/gem5-fi-ding/runs/ooo-l0l5/guard)
hosts THREE lock namespaces plus the resource monitor:

  slots/    host-global gem5 slot locks (max 6 -> 8 per the task book).
            One slot == ONE concurrently-running gem5 process anywhere on
            this host, whoever owns it. Acquire is an atomic O_EXCL file
            create; the JSON body records owner/PID/PGID/starttime/heartbeat.
            Reclamation of a stale slot requires the recorded PID to be
            GONE or its /proc/<pid> starttime to no longer match (PID-reuse
            safe). A live process is never reclaimed and a non-owner can
            never release someone else's slot.
  claims/   per-(campaign, run_id) claim locks: exactly one writer per
            sample, host-wide. Key format "<campaign>__<run_id>".
  goldens/  per-baseline_key golden-generation claims (two workers must not
            trace the same no-fault reference concurrently).
  monitor/  resources.log -- 60s CSV samples (MemAvailable, swap, vmstat
            cumulative paging, load, blocked procs, disk, gem5 count/RSS).

All state lives under the guard dir on /home (NOT /tmp). Everything is
stdlib-only and shell-free (no pgrep: /proc is scanned directly, so the
guard never matches its own command line -- the E-001 pgrep lesson).

Exit codes: 0 ok; 1 usage/protocol error; 2 selftest failure.
"""

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
import time

DEFAULT_GUARD_DIR = "/home/sdc/gem5-fi-ding/runs/ooo-l0l5/guard"

# claim keys are filenames; keep them path-safe
_KEY_RE = re.compile(r"^[A-Za-z0-9._-]+$")


class GuardError(Exception):
    """Protocol violation (slots full, foreign lock, bad key, ...)."""


# --------------------------------------------------------------------------
# /proc helpers

def proc_starttime(pid):
    """Field 22 of /proc/<pid>/stat (scheduler starttime, jiffies since boot)
    -- the PID-reuse discriminator. None when the process is gone.

    comm may contain spaces and parentheses ('(python3 (vfork))'), so parse
    AFTER the last ')' rather than splitting the whole line."""
    try:
        with open(f"/proc/{pid}/stat", "r") as f:
            stat = f.read()
    except OSError:
        return None
    rp = stat.rfind(")")
    if rp < 0:
        return None
    fields = stat[rp + 2:].split()
    # fields[0] is state (field 3); starttime is field 22 -> index 19
    try:
        return int(fields[19])
    except (IndexError, ValueError):
        return None


def pid_matches(pid, starttime):
    """True iff pid exists AND its current /proc starttime == starttime."""
    if not isinstance(pid, int) or not isinstance(starttime, int):
        return False
    cur = proc_starttime(pid)
    return cur is not None and cur == starttime


def _read_meminfo():
    out = {}
    with open("/proc/meminfo", "r") as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 2 and parts[0].endswith(":"):
                try:
                    out[parts[0][:-1]] = int(parts[1])
                except ValueError:
                    pass
    return out


def _read_vmstat_paging():
    """Cumulative pswpin/pswpout page counts from /proc/vmstat."""
    vals = {"pswpin": 0, "pswpout": 0}
    try:
        with open("/proc/vmstat", "r") as f:
            for line in f:
                parts = line.split()
                if len(parts) == 2 and parts[0] in vals:
                    try:
                        vals[parts[0]] = int(parts[1])
                    except ValueError:
                        pass
    except OSError:
        pass
    return vals


def _read_loadavg():
    try:
        with open("/proc/loadavg", "r") as f:
            parts = f.read().split()
        return float(parts[0]), float(parts[1]), float(parts[2])
    except (OSError, ValueError, IndexError):
        return -1.0, -1.0, -1.0


def _read_proc_counts():
    """procs_running / procs_blocked from /proc/stat."""
    out = {"procs_running": 0, "procs_blocked": 0}
    try:
        with open("/proc/stat", "r") as f:
            for line in f:
                parts = line.split()
                if parts and parts[0] in out and len(parts) == 2:
                    try:
                        out[parts[0]] = int(parts[1])
                    except ValueError:
                        pass
    except OSError:
        pass
    return out


def _find_gem5_processes():
    """PIDs whose cmdline references build/ARM/gem5.opt (path substring, not
    pgrep -f: we scan /proc ourselves and never match our own args)."""
    pids = []
    for ent in os.listdir("/proc"):
        if not ent.isdigit():
            continue
        try:
            with open(f"/proc/{ent}/cmdline", "rb") as f:
                cmd = f.read().split(b"\x00")
        except OSError:
            continue
        if any(b"build/ARM/gem5.opt" in a for a in cmd if a):
            pids.append(int(ent))
    return pids


def _pid_rss_kib(pid):
    """Resident set size in KiB via /proc/<pid>/statm (pages 2..resident)."""
    try:
        with open(f"/proc/{pid}/statm", "r") as f:
            parts = f.read().split()
        return int(parts[1]) * (os.sysconf("SC_PAGE_SIZE") // 1024)
    except (OSError, ValueError, IndexError):
        return 0


def sample_resources(paths=("/home/sdc/gem5-fi-ding/runs",)):
    """One resource sample for the monitor log / TRIP ladder. All fields
    measured, none fabricated; unreadable -> sentinel -1."""
    mem = _read_meminfo()
    paging = _read_vmstat_paging()
    l1, l5, l15 = _read_loadavg()
    counts = _read_proc_counts()
    g5 = _find_gem5_processes()
    disk_free = -1
    for p in paths:
        try:
            st = os.statvfs(p)
            disk_free = max(disk_free, st.f_bavail * st.f_frsize)
        except OSError:
            continue
    return {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "mem_available_kib": mem.get("MemAvailable", -1),
        "swap_free_kib": mem.get("SwapFree", -1),
        "pswpin_cum": paging["pswpin"],
        "pswpout_cum": paging["pswpout"],
        "load1": l1, "load5": l5, "load15": l15,
        "procs_running": counts["procs_running"],
        "procs_blocked": counts["procs_blocked"],
        "disk_free_bytes": disk_free,
        "gem5_pids": g5,
        "gem5_rss_kib": sum(_pid_rss_kib(p) for p in g5),
    }


# --------------------------------------------------------------------------
# slot locks

def _slots_dir(guard_dir):
    d = os.path.join(guard_dir, "slots")
    os.makedirs(d, exist_ok=True)
    return d


def _now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%S") + f".{int(time.time() * 1000) % 1000:03d}"


def _write_lock_file(path, payload):
    """Create+fill a lock file atomically: O_EXCL create, one write, fsync.
    Returns the open fd's file or raises GuardError if the slot is taken
    (FileExistsError is caught by the caller)."""
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(payload, f)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
    except BaseException:
        try:
            os.unlink(path)
        except OSError:
            pass
        raise


def slot_acquire(guard_dir, owner, campaign, run_id, max_slots, node=None):
    """Acquire one of the host-global gem5 slots (blocking-free: raises
    GuardError('slots full') when all max_slots are held). Returns a handle
    dict for slot_release/slot_heartbeat. Stale slots are NOT auto-reclaimed
    here -- the scheduler calls slot_reclaim_stale() on its own cadence so
    every reclamation is an explicit, logged decision."""
    sd = _slots_dir(guard_dir)
    me = os.getpid()
    payload_base = {
        "owner": str(owner), "pid": me, "pgid": os.getpgid(me),
        "starttime": proc_starttime(me), "node": node,
        "campaign": campaign, "run_id": run_id,
        "acquired": _now_iso(), "heartbeat": _now_iso(),
    }
    for i in range(max_slots):
        path = os.path.join(sd, f"slot_{i}.lock")
        try:
            _write_lock_file(path, dict(payload_base))
        except FileExistsError:
            continue
        return {"path": path, "index": i, "owner": payload_base["owner"],
                "pid": me}
    raise GuardError(
        f"slots full: all {max_slots} host-global slots held "
        f"(status: {json.dumps(slot_status(guard_dir))})")


def _load_lock(path):
    with open(path, "r") as f:
        return json.load(f)


def slot_release(handle, force=False):
    """Release a slot. Refuses to unlink a lock that does not belong to the
    CALLING process unless force=True AND the recorded pid is verifiably
    dead/mismatched (the same stale rule as slot_reclaim_stale)."""
    path = handle["path"]
    if not os.path.exists(path):
        return  # already gone (e.g. reclaimed after our death) -- idempotent
    j = _load_lock(path)
    mine = j.get("pid") == os.getpid() and \
        j.get("starttime") == proc_starttime(os.getpid())
    if not mine:
        if force and not pid_matches(j.get("pid"), j.get("starttime")):
            os.unlink(path)
            return
        raise GuardError(
            f"refusing to release foreign slot lock {path} "
            f"(recorded pid={j.get('pid')} owner={j.get('owner')}; "
            f"caller pid={os.getpid()})")
    os.unlink(path)


def slot_heartbeat(handle):
    """Refresh the heartbeat timestamp in place (atomic tmp+rename), keeping
    every identity field untouched."""
    path = handle["path"]
    j = _load_lock(path)
    mine = j.get("pid") == os.getpid() and \
        j.get("starttime") == proc_starttime(os.getpid())
    if not mine:
        raise GuardError(f"heartbeat on foreign/changed lock {path}")
    j["heartbeat"] = _now_iso()
    tmp = path + f".hb.{os.getpid()}"
    with open(tmp, "w") as f:
        json.dump(j, f)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def slot_status(guard_dir):
    """Read-only snapshot: per-slot liveness + active count. Never mutates."""
    sd = _slots_dir(guard_dir)
    slots = []
    for name in sorted(os.listdir(sd)):
        if not (name.startswith("slot_") and name.endswith(".lock")):
            continue
        path = os.path.join(sd, name)
        try:
            j = _load_lock(path)
        except (OSError, ValueError):
            slots.append({"path": path, "state": "unreadable"})
            continue
        alive = pid_matches(j.get("pid"), j.get("starttime"))
        slots.append({"path": path, "index": int(name[5:-5]),
                      "owner": j.get("owner"), "campaign": j.get("campaign"),
                      "run_id": j.get("run_id"), "pid": j.get("pid"),
                      "node": j.get("node"), "heartbeat": j.get("heartbeat"),
                      "state": "live" if alive else "stale"})
    n_slots = len([s for s in slots if "index" in s])
    return {"n_slots": n_slots,
            "n_active": len([s for s in slots if s.get("state") == "live"]),
            "n_stale": len([s for s in slots if s.get("state") == "stale"]),
            "slots": slots}


def slot_reclaim_stale(guard_dir):
    """Reclaim slots whose recorded process is gone or whose PID was reused.
    Evidence is MOVED to slots/stale/ (never deleted). A live, matching
    process is never touched. Returns the list of reclaimed paths."""
    sd = _slots_dir(guard_dir)
    stale_dir = os.path.join(sd, "stale")
    reclaimed = []
    for name in sorted(os.listdir(sd)):
        if not (name.startswith("slot_") and name.endswith(".lock")):
            continue
        path = os.path.join(sd, name)
        try:
            j = _load_lock(path)
        except (OSError, ValueError):
            continue  # unreadable is not proof of death -- leave it
        if pid_matches(j.get("pid"), j.get("starttime")):
            continue  # live owner: NEVER reclaim
        os.makedirs(stale_dir, exist_ok=True)
        dst = os.path.join(stale_dir, f"{name}.{int(time.time())}")
        os.rename(path, dst)
        reclaimed.append(dst)
    return reclaimed


# --------------------------------------------------------------------------
# claim locks (campaign, run_id) and golden-generation claims

def _claim_path(guard_dir, key, namespace):
    if not _KEY_RE.match(key or ""):
        raise GuardError(f"invalid claim key {key!r} (allowed [A-Za-z0-9._-])")
    d = os.path.join(guard_dir, namespace)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, f"{key}.claim")


def claim_acquire(guard_dir, key):
    """Atomic exclusive claim. True when this caller created it; False when
    it already exists (someone else owns the sample)."""
    path = _claim_path(guard_dir, key, "claims")
    try:
        _write_lock_file(path, {"owner": os.environ.get("OOO_WORKER", "cli"),
                                "pid": os.getpid(),
                                "starttime": proc_starttime(os.getpid()),
                                "ts": _now_iso()})
    except FileExistsError:
        return False
    return True


def claim_release(guard_dir, key, force=False):
    """Release a claim. force=True releases a claim whose owner is provably
    dead (scheduler cleanup of an interrupted worker); the live-owner claim
    of another process is never released."""
    path = _claim_path(guard_dir, key, "claims")
    if not os.path.exists(path):
        return
    j = _load_lock(path)
    mine = j.get("pid") == os.getpid()
    if not mine and not force:
        # allow same-pid-any-starttime (forked tooling) plus the dead-owner
        # force path; a LIVE foreign owner must never be released
        if pid_matches(j.get("pid"), j.get("starttime")):
            raise GuardError(f"refusing to release live foreign claim {path}")
    if not mine and force:
        if pid_matches(j.get("pid"), j.get("starttime")):
            raise GuardError(f"refusing to force-release live claim {path}")
    os.unlink(path)


def golden_claim_acquire(guard_dir, golden_key):
    path = _claim_path(guard_dir, golden_key, "goldens")
    try:
        _write_lock_file(path, {"owner": os.environ.get("OOO_WORKER", "cli"),
                                "pid": os.getpid(),
                                "starttime": proc_starttime(os.getpid()),
                                "ts": _now_iso()})
    except FileExistsError:
        return False
    return True


def golden_claim_release(guard_dir, golden_key):
    path = _claim_path(guard_dir, golden_key, "goldens")
    if os.path.exists(path):
        os.unlink(path)


# --------------------------------------------------------------------------
# monitor

MONITOR_FIELDS = ["ts", "mem_available_kib", "swap_free_kib", "pswpin_cum",
                  "pswpout_cum", "load1", "load5", "load15", "procs_running",
                  "procs_blocked", "disk_free_bytes", "gem5_count",
                  "gem5_rss_kib"]


def monitor_once(guard_dir, log_path, paths):
    r = sample_resources(paths)
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    row = dict(r)
    row["gem5_count"] = len(r["gem5_pids"])
    del row["gem5_pids"]
    new = not os.path.exists(log_path)
    with open(log_path, "a") as f:
        if new:
            f.write(",".join(MONITOR_FIELDS) + "\n")
        f.write(",".join(str(row.get(k, "")) for k in MONITOR_FIELDS) + "\n")
        f.flush()
    return r


def run_monitor(guard_dir, interval, paths):
    log_path = os.path.join(guard_dir, "monitor", "resources.log")
    print(f"[guard] monitor -> {log_path} every {interval}s (Ctrl-C to stop)")
    while True:
        r = monitor_once(guard_dir, log_path, paths)
        print(f"[guard] {r['ts']} MemAvail={r['mem_available_kib']//1024}MiB "
              f"SwapFree={r['swap_free_kib']//1024}MiB "
              f"blocked={r['procs_blocked']} gem5={len(r['gem5_pids'])} "
              f"gem5RSS={r['gem5_rss_kib']//1024}MiB "
              f"disk={r['disk_free_bytes']//(1024**3)}G")
        time.sleep(interval)


# --------------------------------------------------------------------------
# CLI

def _cmd_status(guard_dir):
    st = slot_status(guard_dir)
    print(json.dumps(st, indent=2, ensure_ascii=False))
    n_claims = 0
    cdir = os.path.join(guard_dir, "claims")
    if os.path.isdir(cdir):
        n_claims = len([f for f in os.listdir(cdir) if f.endswith(".claim")])
    print(f"claims held: {n_claims}")


def _cmd_selftest(guard_dir):
    """Full protocol cycle in a THROWAWAY subdir of the guard dir (the real
    slots/claims namespaces stay untouched), plus one real resources sample."""
    tmp = tempfile.mkdtemp(prefix="selftest-", dir=guard_dir)
    ok = True
    try:
        h = slot_acquire(tmp, "selftest", "c", "r", max_slots=1)
        ok &= h is not None
        slot_heartbeat(h)
        try:
            slot_acquire(tmp, "selftest2", "c", "r2", max_slots=1)
            ok = False
            print("[selftest] FAIL: second acquire on max_slots=1 succeeded")
        except GuardError:
            pass
        slot_release(h)
        st = slot_status(tmp)
        ok &= st["n_active"] == 0
        ok &= claim_acquire(tmp, "k1") and not claim_acquire(tmp, "k1")
        claim_release(tmp, "k1")
        ok &= golden_claim_acquire(tmp, "gk") and not golden_claim_acquire(tmp, "gk")
        golden_claim_release(tmp, "gk")
        r = sample_resources()
        ok &= r["mem_available_kib"] > 0
        print(f"[selftest] resources sample: MemAvail="
              f"{r['mem_available_kib']//1024}MiB gem5={len(r['gem5_pids'])}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"[selftest] {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 2


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--guard-dir", default=DEFAULT_GUARD_DIR)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status", help="read-only lock snapshot")
    m = sub.add_parser("monitor", help="60s resource sampling loop")
    m.add_argument("--interval", type=float, default=60.0)
    m.add_argument("--path", action="append", default=None,
                   help="path for disk-free sampling (repeatable)")
    sub.add_parser("reclaim-stale", help="reclaim provably-dead slot locks")
    sub.add_parser("selftest", help="full protocol cycle in a throwaway dir")
    args = ap.parse_args()

    if args.cmd == "status":
        _cmd_status(args.guard_dir)
    elif args.cmd == "monitor":
        paths = args.path or ["/home/sdc/gem5-fi-ding/runs"]
        run_monitor(args.guard_dir, args.interval, paths)
    elif args.cmd == "reclaim-stale":
        for p in slot_reclaim_stale(args.guard_dir):
            print(f"[guard] reclaimed {p}")
    elif args.cmd == "selftest":
        os.makedirs(args.guard_dir, exist_ok=True)
        return _cmd_selftest(args.guard_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
