#!/usr/bin/env python3
"""[OOO][P1] dry-run tests for tools/ooo_scheduler.py (no gem5 involved).

Everything runs against tools/tests/stubs/fake_sample_runner.py (the
sample_runner CLI contract stub) via the scheduler's OOO_SAMPLE_RUNNER
test hook, with the REAL guard locks underneath, so dispatch/admission/
recovery logic is exercised end-to-end without a single gem5 process.

  D1  single campaign n=6, policy host_max_slots=2, my-max-slots=3:
      exactly 6 results rows, no duplicate reps, stub-measured peak
      concurrency <= 2 (the HOST gate binds, not the instance gate),
      campaign handoff invoked exactly once (fake handoff recorder).
  D2  restart idempotency: SIGKILL the scheduler mid-run, restart:
      completed reps are skipped, total rows exactly n, no duplicates.
  D3  exit 5 -> QUARANTINE recorded (guard/state.json + quarantine.jsonl
      + campaign QUARANTINE/ evidence), other reps not blocked, topup
      fills the shortfall (quarantined rep counts as attempted).
  D4  topup: 2 forced SimulatorError rows -> round 1 dispatches rep
      385/386 with the frozen topup seed formula.
  D5  policy ladder (in-process, injected sampler/prober/launcher):
      6 -> 8 after after_s compressed to 2 good ticks (scaleup launches
      the add campaign with preferred-numa node list), TRIP degrade
      8 -> 6 -> 4 via MemAvailable floor; paging and blocked paths each
      step down after 3 consecutive ticks; identity drift -> policy
      zeroed + exit 2 with a TRIP record.
  D6  handoff failure is a warning only (missing handoff tool): the
      daemon still exits 0 after campaign+master handoff attempts; with
      a fake handoff: exactly one campaign call per campaign + one
      master call.
  D7  replay: replay_pct=100 -> every valid sample gets an
      observation.replay block (idempotent), scheduler exits 0.
  D0  read-only validation against the REAL spec drafts under
      runs/ooo-l0l5/specs/ (frozen seeds, n_per_cell, batch fields).

Scratch dirs live under /home/sdc/gem5-fi-ding/runs/ooo-l0l5/tests-b
(never /tmp). Run: python3 tools/tests/test_ooo_scheduler_dry.py
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                ".."))
import ooo_scheduler as S  # noqa: E402
import ooo_guard  # noqa: E402

TESTS_ROOT = "/home/sdc/gem5-fi-ding/runs/ooo-l0l5/tests-b"
SPECS = "/home/sdc/gem5-fi-ding/runs/ooo-l0l5/specs"
PY = sys.executable
FAILURES = []


def check(name, cond, detail=""):
    if cond:
        print(f"  PASS {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILURES.append(name)


def _wait_until(pred, timeout, what):
    t0 = time.time()
    while time.time() - t0 < timeout:
        v = pred()
        if v:
            return v
        time.sleep(0.05)
    print(f"  [timeout] {what} ({timeout}s)")
    return None


def _read_rows(campaign_dir):
    rows = []
    p = os.path.join(campaign_dir, "results.jsonl")
    if os.path.isfile(p):
        with open(p) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        rows.append(json.loads(line))
                    except ValueError:
                        pass
    return rows


def _write_policy(guard_dir, host_max):
    os.makedirs(os.path.join(guard_dir, "ctl"), exist_ok=True)
    S.atomic_write_json(os.path.join(guard_dir, "ctl", "policy.json"),
                        dict(host_max_slots=host_max, ts="dry-test"))


def _make_campaign(tmp, cid, n, base_seed, replay_pct, rounds_max=3):
    """Campaign yaml derived from the REAL eng2 spec (schema fidelity)."""
    with open(os.path.join(SPECS, "eng2_D01-F0-W6-c.yaml")) as f:
        c = S.yaml.safe_load(f)
    c["campaign_id"] = cid
    c["n_per_cell"] = n
    c["base_seed"] = base_seed
    c["replay_pct"] = replay_pct
    c["topup"] = dict(seed_offset=1000000, rounds_max=rounds_max)
    p = os.path.join(tmp, f"{cid}.yaml")
    with open(p, "w") as f:
        S.yaml.safe_dump(c, f, sort_keys=True)
    return p


HANDOFF_SCRIPT = """#!/usr/bin/env python3
import json, os, sys
log = os.environ["OOO_HANDOFF_LOG"]
with open(log, "a") as f:
    f.write(json.dumps(sys.argv[1:]) + "\\n")
if len(sys.argv) > 2 and sys.argv[1] == "campaign":
    d = sys.argv[sys.argv.index("--dir") + 1]
    with open(os.path.join(d, "handoff.json"), "w") as f:
        json.dump(dict(fake_handoff=True), f)
sys.exit(0)
"""


def _make_fake_handoff(tmp):
    script = os.path.join(tmp, "fake_handoff.py")
    with open(script, "w") as f:
        f.write(HANDOFF_SCRIPT)
    os.chmod(script, 0o755)
    return script


def _sched_env(tmp, guard_dir, ctrl=None, handoff=None):
    env = dict(os.environ)
    stub = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                        "stubs", "fake_sample_runner.py")
    env["OOO_SAMPLE_RUNNER"] = stub
    env["OOO_FAKE_GUARD_DIR"] = guard_dir
    if ctrl is not None:
        ctrl_path = os.path.join(tmp, "ctrl.json")
        with open(ctrl_path, "w") as f:
            json.dump(ctrl, f)
        env["OOO_FAKE_CTRL"] = ctrl_path
    if handoff is not None:
        env["OOO_HANDOFF"] = handoff
        env["OOO_HANDOFF_LOG"] = os.path.join(tmp, "handoff_calls.log")
    return env


def _run_scheduler(env, campaign_yaml, guard_dir, runs_root, my_max=2,
                   numa="0,1", timeout=120):
    argv = [PY, os.path.join(os.path.dirname(os.path.dirname(
        os.path.realpath(__file__))), "ooo_scheduler.py"),
        "start", "--campaign-yaml", campaign_yaml,
        "--my-max-slots", str(my_max), "--numa-nodes", numa,
        "--guard-dir", guard_dir, "--runs-root", runs_root,
        "--poll-interval", "0.1", "--exit4-backoff", "0.3",
        "--claim-defer", "0.3", "--host-max-slots", "6"]
    return subprocess.run(argv, env=env, capture_output=True, text=True,
                          timeout=timeout)


def _peak_concurrency(campaign_dir):
    p = os.path.join(campaign_dir, ".fake_concurrency", "max.txt")
    if not os.path.isfile(p):
        return 0
    peak = 0
    with open(p) as f:
        for line in f:
            try:
                peak = max(peak, int(line.strip()))
            except ValueError:
                continue
    return peak


def _handoff_log(tmp, name="handoff_calls.log"):
    p = os.path.join(tmp, name)
    calls = []
    if os.path.isfile(p):
        with open(p) as f:
            for line in f:
                try:
                    calls.append(json.loads(line))
                except ValueError:
                    pass
    return calls


# --------------------------------------------------------------------------
# D0: read-only validation of the REAL spec drafts

def test_specs_readonly():
    frozen_seeds = dict()
    frozen_seeds["formal_D01-F0-W6-c"] = 44072336
    frozen_seeds["formal_D02-F0-W6-b"] = 41211122
    frozen_seeds["formal_D02-F0-W6-c"] = 47470573
    frozen_seeds["formal_D04-F0-W4-d"] = 42729898
    ids = set()
    for cid, seed in frozen_seeds.items():
        c = S.load_campaign(os.path.join(SPECS, f"{cid}.yaml"))
        check(f"spec-{cid}-identity", c["campaign_id"] == cid)
        check(f"spec-{cid}-n385", c["n_per_cell"] == 385)
        check(f"spec-{cid}-seed", c["base_seed"] == seed,
              f"got {c['base_seed']}")
        check(f"spec-{cid}-replay5", float(c["replay_pct"]) == 5.0)
        check(f"spec-{cid}-topup", c["topup"]["rounds_max"] == 3
              and c["topup"]["seed_offset"] == 1000000)
        for rep in range(385):
            ids.add(S.run_id_for(cid, rep))
    check("spec-run-ids-unique", len(ids) == 4 * 385, f"got {len(ids)}")
    # eng2 seeds: 52000000 + k*1000 in RunID order c, b, c, d
    eng2_order = ["eng2_D01-F0-W6-c", "eng2_D02-F0-W6-b",
                  "eng2_D02-F0-W6-c", "eng2_D04-F0-W4-d"]
    for k, cid in enumerate(eng2_order):
        e = S.load_campaign(os.path.join(SPECS, f"{cid}.yaml"))
        check(f"spec-{cid}-n2-replay100",
              e["n_per_cell"] == 2 and float(e["replay_pct"]) == 100.0)
        check(f"spec-{cid}-seed", e["base_seed"] == 52000000 + k * 1000,
              f"got {e['base_seed']}")
    b = S.load_batch(os.path.join(SPECS, "formal-batch.yaml"))
    check("spec-batch-initial", b["initial"] == [
        "formal_D01-F0-W6-c", "formal_D02-F0-W6-b", "formal_D02-F0-W6-c"])
    check("spec-batch-scaleup-add", b["scaleup"]["add"] == ["formal_D04-F0-W4-d"])
    check("spec-batch-scaleup-900s", float(b["scaleup"]["after_s"]) == 900.0)
    check("spec-batch-host-ladder", b["host_max_slots_initial"] == 6
          and b["host_max_slots_max"] == 8)
    check("spec-batch-trip", b["trip"]["mem_below_kib"] == 10485760
          and b["trip"]["degrade"] == [6, 4])
    check("spec-batch-tick60", float(b["tick_s"]) == 60.0)
    check("spec-batch-gem5-frozen",
          b["frozen"]["gem5_sha256"] ==
          "1a618953b014514713c0ad98c7f3d69a48171d81f0463d934bccdfcfc0070bf3")
    check("spec-batch-head-placeholder",
          isinstance(b["frozen"]["head"], str) and len(b["frozen"]["head"]) > 0)
    check("spec-batch-numa", b["numa"] == dict()
          or sorted(b["numa"].values()) == [0, 0, 1, 1],
          f"numa={b['numa']}")


# --------------------------------------------------------------------------
# D1: single campaign n=6, host gate binds

def test_single_campaign(tmp):
    guard = os.path.join(tmp, "g1")
    runs_root = os.path.join(tmp, "r1")
    os.makedirs(runs_root, exist_ok=True)
    _write_policy(guard, 2)
    y = _make_campaign(tmp, "dry_s1", 6, 44070000, 0)
    handoff = _make_fake_handoff(tmp)
    env = _sched_env(tmp, guard, ctrl=dict(sleep=[0.15, 0.35]),
                     handoff=handoff)
    r = _run_scheduler(env, y, guard, runs_root, my_max=3)
    check("d1-exit0", r.returncode == 0, f"rc={r.returncode} "
          f"stderr={r.stderr[-300:] if r.stderr else ''}")
    cdir = os.path.join(runs_root, "dry_s1")
    rows = _read_rows(cdir)
    check("d1-six-rows", len(rows) == 6, f"rows={len(rows)}")
    reps = sorted(row["rep"] for row in rows)
    check("d1-no-dup-reps", reps == [0, 1, 2, 3, 4, 5], f"reps={reps}")
    check("d1-all-valid", all(row["classification"] == "Masked"
                              for row in rows))
    check("d1-seeds", sorted(row["seed"] for row in rows) ==
          [44070000 + i for i in range(6)])
    peak = _peak_concurrency(cdir)
    check("d1-host-gate-le2", peak <= 2, f"peak={peak}")
    check("d1-host-gate-reached2", peak >= 2, f"peak={peak}")
    calls = _handoff_log(tmp)
    check("d1-handoff-once", len(calls) == 1 and calls[0][0] == "campaign"
          and calls[0][1] == "--dir", f"calls={calls}")
    check("d1-handoff-json", os.path.isfile(os.path.join(cdir,
                                                         "handoff.json")))


# --------------------------------------------------------------------------
# D2: restart idempotency (SIGKILL mid-run, restart, no duplicates)

def test_restart_idempotent(tmp):
    guard = os.path.join(tmp, "g2")
    runs_root = os.path.join(tmp, "r2")
    os.makedirs(runs_root, exist_ok=True)
    _write_policy(guard, 2)
    y = _make_campaign(tmp, "dry_s2", 6, 44071000, 0)
    env = _sched_env(tmp, guard, ctrl=dict(sleep=[0.3, 0.5]))
    cdir = os.path.join(runs_root, "dry_s2")
    argv = [PY, os.path.join(os.path.dirname(os.path.dirname(
        os.path.realpath(__file__))), "ooo_scheduler.py"),
        "start", "--campaign-yaml", y, "--my-max-slots", "2",
        "--numa-nodes", "0,1", "--guard-dir", guard,
        "--runs-root", runs_root, "--poll-interval", "0.1",
        "--exit4-backoff", "0.3", "--claim-defer", "0.3"]
    logf = open(os.path.join(tmp, "sched2.log"), "wb")
    p1 = subprocess.Popen(argv, env=env, stdout=logf, stderr=logf)
    got2 = _wait_until(lambda: len(_read_rows(cdir)) >= 2, 60,
                       "two samples before kill")
    check("d2-pre-kill-2rows", got2 is not None,
          f"rows={len(_read_rows(cdir))}")
    p1.kill()          # REAL SIGKILL of the scheduler process
    p1.wait(10)
    check("d2-scheduler-killed", p1.returncode < 0,
          f"rc={p1.returncode}")
    # orphan workers finish on their own (start_new_session)
    _wait_until(lambda: ooo_guard.slot_status(guard)["n_active"] == 0,
                30, "orphan workers to finish")
    r2 = _run_scheduler(env, y, guard, runs_root, my_max=2)
    check("d2-restart-exit0", r2.returncode == 0,
          f"rc={r2.returncode} stderr={r2.stderr[-300:] if r2.stderr else ''}")
    rows = _read_rows(cdir)
    reps = sorted(row["rep"] for row in rows)
    check("d2-exact-six-rows", len(rows) == 6, f"rows={len(rows)} reps={reps}")
    check("d2-no-duplicates", reps == [0, 1, 2, 3, 4, 5], f"reps={reps}")
    ids = [row["run_id"] for row in rows]
    check("d2-unique-run-ids", len(set(ids)) == 6, f"ids={ids}")


# --------------------------------------------------------------------------
# D3: exit 5 -> QUARANTINE recorded, others proceed, topup fills the gap

def test_quarantine(tmp):
    guard = os.path.join(tmp, "g3")
    runs_root = os.path.join(tmp, "r3")
    os.makedirs(runs_root, exist_ok=True)
    _write_policy(guard, 2)
    y = _make_campaign(tmp, "dry_s3", 6, 44072000, 0)
    env = _sched_env(tmp, guard, ctrl=dict(
        sleep=[0.1, 0.2],
        reps=dict(**dict.fromkeys(["2"], dict(exit=5)))))
    r = _run_scheduler(env, y, guard, runs_root, my_max=2)
    check("d3-exit0", r.returncode == 0,
          f"rc={r.returncode} stderr={r.stderr[-400:] if r.stderr else ''}")
    cdir = os.path.join(runs_root, "dry_s3")
    rows = _read_rows(cdir)
    reps = sorted(row["rep"] for row in rows)
    check("d3-others-not-blocked", [x for x in reps if x != 385] ==
          [0, 1, 3, 4, 5], f"reps={reps}")
    check("d3-topup-385", 385 in reps, f"reps={reps}")
    qdir = os.path.join(cdir, "QUARANTINE", "dry_s3-c0000-r0002")
    check("d3-quarantine-evidence", os.path.isdir(qdir)
          and os.path.isfile(os.path.join(qdir, "evidence", "why.txt")))
    state = S.read_json(os.path.join(guard, "state.json")) or dict()
    quar = state.get("quarantine") or []
    check("d3-state-quarantine", any(e.get("rep") == 2 and
                                     e.get("campaign") == "dry_s3"
                                     for e in quar), f"quar={quar}")
    qlines = []
    qp = os.path.join(guard, "quarantine.jsonl")
    if os.path.isfile(qp):
        with open(qp) as f:
            qlines = [json.loads(line) for line in f if line.strip()]
    check("d3-quarantine-jsonl", len(qlines) == 1
          and qlines[0].get("rep") == 2, f"qlines={qlines}")


# --------------------------------------------------------------------------
# D4: topup -- 2 forced SimulatorError rows -> round 1 dispatches rep 385/386

def test_topup(tmp):
    guard = os.path.join(tmp, "g4")
    runs_root = os.path.join(tmp, "r4")
    os.makedirs(runs_root, exist_ok=True)
    _write_policy(guard, 2)
    y = _make_campaign(tmp, "dry_s4", 6, 44073000, 0)
    ctrl = dict(sleep=[0.1, 0.2], simerr=[0, 1])
    env = _sched_env(tmp, guard, ctrl=ctrl)
    r = _run_scheduler(env, y, guard, runs_root, my_max=2)
    check("d4-exit0", r.returncode == 0,
          f"rc={r.returncode} stderr={r.stderr[-400:] if r.stderr else ''}")
    cdir = os.path.join(runs_root, "dry_s4")
    rows = _read_rows(cdir)
    by_rep = dict()
    for row in rows:
        by_rep[row["rep"]] = row
    check("d4-round1-reps", 385 in by_rep and 386 in by_rep,
          f"reps={sorted(by_rep)}")
    base = 44073000
    check("d4-topup-seed-385",
          by_rep.get(385, dict()).get("seed") == base + 1000000 + 1000 + 385,
          f"seed385={by_rep.get(385, dict()).get('seed')}")
    check("d4-topup-seed-386",
          by_rep.get(386, dict()).get("seed") == base + 1000000 + 1000 + 386,
          f"seed386={by_rep.get(386, dict()).get('seed')}")
    check("d4-simerr-rows",
          by_rep.get(0, dict()).get("classification") == "SimulatorError"
          and by_rep.get(1, dict()).get("classification") == "SimulatorError",
          f"by_rep={by_rep}")
    st = S.read_json(os.path.join(cdir, "scheduler_state.json")) or dict()
    check("d4-topup-round-1", st.get("round") == 1
          and sorted(st.get("dispatched") or []) == [385, 386], f"st={st}")
    valid = [rep for rep, row in by_rep.items()
             if row["classification"] != "SimulatorError"]
    check("d4-six-valid", len(valid) == 6, f"valid={sorted(valid)}")


# --------------------------------------------------------------------------
# D5: policy ladder (in-process daemon, injected sampler/prober/launcher)

GIB16 = 16 * 1024 * 1024   # 16 GiB expressed in KiB
GIB8 = 8 * 1024 * 1024     # 8 GiB expressed in KiB


def _res(mem_kib, pswpin=0, pswpout=0, blocked=0):
    return dict(mem_available_kib=mem_kib, swap_free_kib=1048576,
                pswpin_cum=pswpin, pswpout_cum=pswpout, load1=1.0,
                load5=1.0, load15=1.0, procs_running=1,
                procs_blocked=blocked, disk_free_bytes=300 * 1024 ** 3,
                gem5_pids=[], gem5_rss_kib=0,
                ts=time.strftime("%Y-%m-%dT%H:%M:%S"))


class FakeSampler:
    def __init__(self, seq):
        self.seq = list(seq)
        self.calls = 0

    def __call__(self):
        self.calls += 1
        if self.seq:
            return self.seq.pop(0)
        return self.seq_last

    @property
    def seq_last(self):
        return _res(16 * 1024 * 1024)


def _ladder_batch(tmp, c1, c2):
    yamls = dict()
    yamls["dry_c1"] = c1
    yamls["dry_c2"] = c2
    numa = dict()
    numa["dry_c1"] = 0
    numa["dry_c2"] = 1
    return dict(batch_id="dry-batch", initial=["dry_c1"],
                my_max_slots_per_agent=2, host_max_slots_initial=6,
                host_max_slots_max=8,
                scaleup=dict(after_s=2.0, min_mem_available_kib=12582912,
                             add=["dry_c2"]),
                trip=dict(mem_below_kib=10485760, degrade=[6, 4]),
                tick_s=1.0, campaign_yamls=yamls, numa=numa,
                frozen=dict(head="dryhead", gem5_sha256="drysha"))


def test_policy_ladder(tmp):
    runs_root = os.path.join(tmp, "r5")
    os.makedirs(runs_root, exist_ok=True)
    guard = os.path.join(tmp, "g5")
    c1 = _make_campaign(tmp, "dry_c1", 2, 50000001, 0)
    c2 = _make_campaign(tmp, "dry_c2", 2, 50000002, 0)
    batch = _ladder_batch(tmp, c1, c2)
    launches = []

    def fake_launcher(cid, ypath, nodes):
        launches.append(dict(cid=cid, yaml=ypath, nodes=list(nodes)))
        return 424242

    ok_prober = lambda: ("dryhead", "drysha")
    # 6 -> 8 (two good ticks, after_s=2.0 with tick_s=1.0), then
    # MemAvailable floor degrades 8 -> 6 -> 4 (floor 4)
    sampler = FakeSampler([_res(GIB16), _res(GIB16),
                           _res(GIB8), _res(GIB8),
                           _res(GIB8)])
    d = S.PolicyDaemon(batch, "batch.yaml", guard, runs_root, launch=True,
                       sampler=sampler, prober=ok_prober,
                       launcher=fake_launcher)
    seq = []
    for _ in range(5):
        rc = d.tick()
        seq.append((rc, d._host_max()))
    check("d5-policy-sequence", [h for _, h in seq] == [6, 8, 6, 4, 4],
          f"seq={[h for _, h in seq]}")
    check("d5-no-early-exit", all(rc is None for rc, _ in seq),
          f"rcs={[rc for rc, _ in seq]}")
    check("d5-scaleup-launched", len(launches) == 1
          and launches[0]["cid"] == "dry_c2"
          and launches[0]["nodes"] == [1, 0], f"launches={launches}")
    state = S.read_json(os.path.join(guard, "state.json")) or dict()
    check("d5-state-written", state.get("batch_id") == "dry-batch"
          and state.get("policy", dict()).get("host_max_slots") == 4
          and state.get("scaleup_done") is True, f"state={state}")
    check("d5-monitor-log", os.path.isfile(
        os.path.join(guard, "monitor", "resources.log")))
    check("d5-trips-empty", state.get("trips") == [])

    # paging path: 3 consecutive paging ticks step down one rung
    sampler2 = FakeSampler([_res(GIB16), _res(GIB16),
                            _res(GIB16, pswpin=10),
                            _res(GIB16, pswpin=20),
                            _res(GIB16, pswpin=30)])
    guard2 = os.path.join(tmp, "g5b")
    d2 = S.PolicyDaemon(batch, "batch.yaml", guard2, runs_root, launch=False,
                        sampler=sampler2, prober=ok_prober,
                        launcher=fake_launcher)
    seq2 = []
    for _ in range(5):
        rc = d2.tick()
        seq2.append((rc, d2._host_max()))
    check("d5-paging-degrade", [h for _, h in seq2] == [6, 8, 8, 8, 6],
          f"seq2={[h for _, h in seq2]}")

    # blocked path: 3 consecutive blocked ticks step down one rung
    sampler3 = FakeSampler([_res(GIB16), _res(GIB16),
                            _res(GIB16, blocked=1),
                            _res(GIB16, blocked=1),
                            _res(GIB16, blocked=1)])
    guard3 = os.path.join(tmp, "g5c")
    d3 = S.PolicyDaemon(batch, "batch.yaml", guard3, runs_root, launch=False,
                        sampler=sampler3, prober=ok_prober,
                        launcher=fake_launcher)
    seq3 = []
    for _ in range(5):
        rc = d3.tick()
        seq3.append((rc, d3._host_max()))
    check("d5-blocked-degrade", [h for _, h in seq3] == [6, 8, 8, 8, 6],
          f"seq3={[h for _, h in seq3]}")

    # identity drift -> TRIP: policy zeroed, exit code 2, TRIP recorded
    guard4 = os.path.join(tmp, "g5d")
    d4 = S.PolicyDaemon(batch, "batch.yaml", guard4, runs_root,
                        sampler=FakeSampler([_res(GIB16)]),
                        prober=lambda: ("WRONG-HEAD", "WRONG-SHA"),
                        launcher=fake_launcher)
    rc = d4.tick()
    check("d5-drift-exit2", rc == 2, f"rc={rc}")
    pol = S.read_json(os.path.join(guard4, "ctl", "policy.json")) or dict()
    check("d5-drift-policy-zero", pol.get("host_max_slots") == 0,
          f"pol={pol}")
    state = S.read_json(os.path.join(guard4, "state.json")) or dict()
    trips = state.get("trips") or []
    check("d5-drift-trip-recorded", len(trips) == 1
          and trips[0].get("kind") == "identity_drift"
          and trips[0].get("observed_head") == "WRONG-HEAD",
          f"trips={trips}")


# --------------------------------------------------------------------------
# D6: completion -> handoff; failure is warning-only

def _seed_valid_samples(runs_root, cid, n, base_seed):
    cdir = os.path.join(runs_root, cid)
    for rep in range(n):
        run_id = S.run_id_for(cid, rep)
        sdir = os.path.join(cdir, "samples", run_id)
        os.makedirs(sdir, exist_ok=True)
        S.atomic_write_json(os.path.join(sdir, "observation.json"),
                            dict(classification="Masked"))
        S.atomic_write_json(os.path.join(sdir, "COMPLETE.json"),
                            dict(run_id=run_id))
        row = dict(manifest=f"samples/{run_id}/manifest.yaml",
                   run_id=run_id, rep=rep, seed=base_seed + rep,
                   classification="Masked", faults_injected=1, exit=0,
                   timed_out=False, chain_complete=True, chain_gaps=[],
                   observation=f"samples/{run_id}/observation.json",
                   ts="dry")
        with open(os.path.join(cdir, "results.jsonl"), "a") as f:
            f.write(json.dumps(row, sort_keys=True) + "\n")


def test_completion_handoff(tmp):
    runs_root = os.path.join(tmp, "r6")
    os.makedirs(runs_root, exist_ok=True)
    guard = os.path.join(tmp, "g6")
    c1 = _make_campaign(tmp, "dry_c1", 2, 50000001, 0)
    c2 = _make_campaign(tmp, "dry_c2", 2, 50000002, 0)
    batch = _ladder_batch(tmp, c1, c2)
    _seed_valid_samples(runs_root, "dry_c1", 2, 50000001)
    _seed_valid_samples(runs_root, "dry_c2", 2, 50000002)
    # (a) handoff tool MISSING -> warnings only, daemon still exits 0
    d = S.PolicyDaemon(batch, "batch.yaml", guard, runs_root,
                       sampler=FakeSampler([_res(GIB16)]),
                       prober=lambda: ("dryhead", "drysha"),
                       handoff_path=os.path.join(tmp, "no_such_handoff.py"))
    rc = d.tick()
    check("d6-missing-handoff-still-0", rc == 0, f"rc={rc}")
    # (b) fake handoff recorder -> exactly 2 campaign + 1 master calls
    guard = os.path.join(tmp, "g6b")
    os.environ["OOO_HANDOFF_LOG"] = os.path.join(tmp, "h6.log")
    handoff = _make_fake_handoff(tmp)
    d2 = S.PolicyDaemon(batch, "batch.yaml", guard, runs_root,
                        sampler=FakeSampler([_res(GIB16)]),
                        prober=lambda: ("dryhead", "drysha"),
                        handoff_path=handoff)
    rc2 = d2.tick()
    check("d6-fake-handoff-0", rc2 == 0, f"rc={rc2}")
    calls = _handoff_log(tmp, "h6.log")
    camps = [c for c in calls if c and c[0] == "campaign"]
    masters = [c for c in calls if c and c[0] == "master"]
    check("d6-two-campaign-handoffs", len(camps) == 2, f"calls={calls}")
    check("d6-one-master-handoff", len(masters) == 1
          and masters[0][1] == "--dirs"
          and masters[0][-1] == "batch.yaml", f"masters={masters}")
    h1 = os.path.join(runs_root, "dry_c1", "handoff.json")
    check("d6-handoff-json-written", os.path.isfile(h1))


# --------------------------------------------------------------------------
# D7: replay (replay_pct=100 -> all valid samples replayed, idempotent)

def test_replay(tmp):
    guard = os.path.join(tmp, "g7")
    runs_root = os.path.join(tmp, "r7")
    os.makedirs(runs_root, exist_ok=True)
    _write_policy(guard, 2)
    y = _make_campaign(tmp, "dry_s7", 3, 44074000, 100)
    env = _sched_env(tmp, guard, ctrl=dict(sleep=[0.1, 0.2]))
    r = _run_scheduler(env, y, guard, runs_root, my_max=2, timeout=120)
    check("d7-exit0", r.returncode == 0,
          f"rc={r.returncode} stderr={r.stderr[-400:] if r.stderr else ''}")
    cdir = os.path.join(runs_root, "dry_s7")
    rows = _read_rows(cdir)
    check("d7-three-rows", len(rows) == 3, f"rows={len(rows)}")
    replayed = 0
    for row in rows:
        op = os.path.join(cdir, row["observation"])
        oj = S.read_json(op) or dict()
        rp = oj.get("replay")
        if isinstance(rp, dict) and rp.get("determinism") == "match":
            replayed += 1
    check("d7-all-replayed", replayed == 3, f"replayed={replayed}")
    # second scheduler run must NOT redo replays (idempotent skip)
    r2 = _run_scheduler(env, y, guard, runs_root, my_max=2, timeout=60)
    check("d7-rerun-exit0", r2.returncode == 0,
          f"rc={r2.returncode} stderr={r2.stderr[-300:] if r2.stderr else ''}")
    mtime = os.path.getmtime(os.path.join(
        cdir, "samples", "dry_s7-c0000-r0000", "observation.json"))
    time.sleep(0.3)
    r3 = _run_scheduler(env, y, guard, runs_root, my_max=2, timeout=60)
    check("d7-third-run-exit0", r3.returncode == 0, f"rc={r3.returncode}")
    mtime2 = os.path.getmtime(os.path.join(
        cdir, "samples", "dry_s7-c0000-r0000", "observation.json"))
    check("d7-replay-not-redone", mtime == mtime2)


def main():
    os.makedirs(TESTS_ROOT, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="sched-dry-", dir=TESTS_ROOT)
    try:
        print("D0 real-spec read-only validation:")
        test_specs_readonly()
        print("D1 single campaign (host gate binds):")
        test_single_campaign(tmp)
        print("D2 restart idempotency:")
        test_restart_idempotent(tmp)
        print("D3 exit-5 quarantine:")
        test_quarantine(tmp)
        print("D4 topup round:")
        test_topup(tmp)
        print("D5 policy ladder:")
        test_policy_ladder(tmp)
        print("D6 completion + handoff:")
        test_completion_handoff(tmp)
        print("D7 replay:")
        test_replay(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    n = len(FAILURES)
    print(f"\n{'ALL PASS' if n == 0 else 'FAILURES: ' + repr(FAILURES)}")
    return 1 if n else 0


if __name__ == "__main__":
    sys.exit(main())
