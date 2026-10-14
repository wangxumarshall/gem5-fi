#!/usr/bin/env python3
"""tools/ooo_scheduler.py -- OOO L0-L5 campaign scheduler (plan Task 9).

Two cooperating roles for the formal batch (guard = tools/ooo_guard.py):

  start          one single-campaign worker-loop instance. One RunAgent
                 runs ONE instance per campaign. Dispatches the campaign's
                 next unfinished rep as
                   taskset -c <cpus> python3 tools/ooo_sample_runner.py run \
                       --campaign-yaml Y --rep N [--topup-round R] \
                       --guard-dir G --runs-root R
                 The scheduler does NOT take slots itself: admission is
                 n_active < host_max_slots (guard/ctl/policy.json) AND
                 in-flight < my-max-slots; the sample_runner's internal
                 slot_acquire remains the hard gate.
  policy-daemon  the machine-unique decision maker: 60s resource sampling
                 (guard/monitor/resources.log), identity verification
                 (HEAD + gem5.opt sha256 vs batch frozen values), the
                 6->8 scale-up ladder and TRIP degrade ladder, per-campaign
                 progress snapshots into guard/state.json, and the final
                 campaign/master handoff.
  status         read-only snapshot of policy/state/slots/instances.

Exit codes (start): 0 campaign complete (valid >= n_per_cell, replays
drained, handoff attempted); 3 topup rounds exhausted with a shortfall;
1 fatal (bad campaign yaml, foreign live instance for this campaign).
Exit codes (policy-daemon): 0 all campaigns complete + master handoff;
2 identity drift (TRIP: policy zeroed to 0 slots first).

Worker exit contract (sample_runner): 0 done/COMPLETE-skip, 3 claim
conflict (rep owned elsewhere -> defer), 4 no slot (back off, retry the
SAME rep), 5 QUARANTINE (record + continue; evidence kept by the runner).

NUMA pinning: --numa-nodes "0,1" (default). Worker i of THIS instance is
taskset-pinned to nodes[i mod len] (node0 = CPU 0-47, node1 = CPU 48-95
on huawei0201), so 3 instances x 2 workers = 3 workers per node. The
batch.yaml numa.<campaign> field is the instance's PREFERRED (first)
node; the policy-daemon passes e.g. "1,0" when launching.

Deployment (phase 2, one per RunAgent):
  cd <repo> && nohup python3 tools/ooo_scheduler.py start \
      --campaign-yaml campaigns/ooo-l0l5/formal_D01-F0-W6-c.yaml \
      --my-max-slots 2 --numa-nodes 0,1 \
      --guard-dir /home/sdc/gem5-fi-ding/runs/ooo-l0l5/guard \
      --runs-root /home/sdc/gem5-fi-ding/runs/ooo-l0l5 \
      >> /home/sdc/gem5-fi-ding/runs/ooo-l0l5/scheduler-D01-c.log 2>&1 &
Policy daemon (machine-unique, nohup, ONE per host):
  nohup python3 tools/ooo_scheduler.py policy-daemon \
      --batch campaigns/ooo-l0l5/formal-batch.yaml \
      --guard-dir ... --runs-root ... --launch >> scheduler-policy.log 2>&1 &

Test hooks (production-neutral): env OOO_SAMPLE_RUNNER overrides the
dispatched runner path; env OOO_HANDOFF overrides the handoff tool path.
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ooo_guard  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_RUNS_ROOT = "/home/sdc/gem5-fi-ding/runs/ooo-l0l5"
DEFAULT_SAMPLE_RUNNER = os.path.join(REPO_ROOT, "tools", "ooo_sample_runner.py")
DEFAULT_HANDOFF = os.path.join(REPO_ROOT, "tools", "ooo_handoff.py")
TOPUP_REP_BASE = 385   # frozen: topup reps continue from 385 (task book)
SCHED_STATE_FILENAME = "scheduler_state.json"
QUARANTINE_DIRNAME = "QUARANTINE"

NUMA_CPU_RANGES = dict()
NUMA_CPU_RANGES[0] = "0-47"    # huawei0201 node 0
NUMA_CPU_RANGES[1] = "48-95"   # huawei0201 node 1


def _log(msg):
    print(f"[sched {time.strftime('%H:%M:%S')}] " + msg, flush=True)


def _now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def atomic_write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + f".tmp{os.getpid()}"
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=1, sort_keys=True)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def read_json(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def run_id_for(campaign_id, rep):
    return f"{campaign_id}-c0000-r{rep:04d}"


def rep_from_run_id(run_id):
    m = re.search(r"-r(\d+)$", run_id or "")
    return int(m.group(1)) if m else None


def load_campaign(yaml_path):
    with open(yaml_path) as f:
        c = yaml.safe_load(f)
    if not isinstance(c, dict):
        raise SystemExit(f"campaign yaml is not a mapping: {yaml_path}")
    for k in ("campaign_id", "n_per_cell", "base_seed"):
        if k not in c:
            raise SystemExit(f"campaign yaml missing {k!r}: {yaml_path}")
    if str(c.get("schema_version")) != "arm-chaos-fi/l0l5-campaign/v1":
        _log(f"WARNING: unexpected schema_version in {yaml_path}: "
             f"{c.get('schema_version')!r}")
    return c


def load_batch(yaml_path):
    with open(yaml_path) as f:
        b = yaml.safe_load(f)
    for k in ("batch_id", "frozen", "campaign_yamls"):
        if k not in b:
            raise SystemExit(f"batch yaml missing {k!r}: {yaml_path}")
    resolved = dict()
    for cid, p in (b["campaign_yamls"] or dict()).items():
        p = str(p)
        if not os.path.isabs(p):
            p = os.path.join(REPO_ROOT, p)
        resolved[cid] = p
    b["campaign_yamls"] = resolved
    return b


def parse_numa_nodes(spec):
    nodes = []
    for part in str(spec).split(","):
        part = part.strip()
        if not part:
            continue
        n = int(part)
        if n not in NUMA_CPU_RANGES:
            raise SystemExit(f"unknown NUMA node {n} (known: "
                             f"{sorted(NUMA_CPU_RANGES)})")
        nodes.append(n)
    if not nodes:
        raise SystemExit(f"empty --numa-nodes spec: {spec!r}")
    return tuple(nodes)


def policy_host_max(guard_dir, fallback):
    j = read_json(os.path.join(guard_dir, "ctl", "policy.json"))
    if isinstance(j, dict) and isinstance(j.get("host_max_slots"), int):
        if j["host_max_slots"] >= 0:
            return j["host_max_slots"]
    return fallback


def _obs_classification(oj):
    if not isinstance(oj, dict):
        return None
    if "classification" in oj:
        return oj.get("classification")
    l5 = oj.get("l5")
    if isinstance(l5, dict):
        return l5.get("classification")
    return None


class Progress:
    """Disk-truth progress for one campaign (rebuilt every loop tick)."""

    def __init__(self):
        self.valid_reps = set()
        self.attempted_reps = set()
        self.rows = []
        self.n_rows = 0

    def __repr__(self):
        return (f"Progress(valid={len(self.valid_reps)}, "
                f"attempted={len(self.attempted_reps)}, rows={self.n_rows})")


def scan_progress(campaign_dir):
    prog = Progress()
    rp = os.path.join(campaign_dir, "results.jsonl")
    if os.path.isfile(rp):
        with open(rp) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                prog.n_rows += 1
                prog.rows.append(row)
                rep = row.get("rep")
                if not isinstance(rep, int):
                    continue
                prog.attempted_reps.add(rep)
                if row.get("classification") != "SimulatorError":
                    obs = row.get("observation")
                    if obs:
                        op = os.path.join(campaign_dir, str(obs))
                        if os.path.isfile(op):
                            prog.valid_reps.add(rep)
    # COMPLETE.json dirs: a crash between atomic rename and the results
    # append still leaves a finalized sample -- recover it read-only.
    sdir = os.path.join(campaign_dir, "samples")
    if os.path.isdir(sdir):
        for name in sorted(os.listdir(sdir)):
            rep = rep_from_run_id(name)
            if rep is None:
                continue
            if not os.path.isfile(os.path.join(sdir, name, "COMPLETE.json")):
                continue
            prog.attempted_reps.add(rep)
            if rep in prog.valid_reps:
                continue
            oj = read_json(os.path.join(sdir, name, "observation.json"))
            if _obs_classification(oj) not in (None, "SimulatorError"):
                prog.valid_reps.add(rep)
    # QUARANTINE dirs: attempted-but-invalid (evidence kept by the runner).
    qdir = os.path.join(campaign_dir, QUARANTINE_DIRNAME)
    if os.path.isdir(qdir):
        for name in os.listdir(qdir):
            rep = rep_from_run_id(name)
            if rep is not None:
                prog.attempted_reps.add(rep)
    return prog


class CampaignScheduler:
    """One campaign's worker loop (one RunAgent = one instance)."""

    def __init__(self, campaign_yaml, guard_dir, runs_root,
                 my_max_slots=2, numa_nodes=(0, 1), host_max_slots_fallback=6,
                 poll_interval=0.5, exit4_backoff=10.0, claim_defer=30.0,
                 runner_path=None):
        self.camp_yaml = os.path.abspath(campaign_yaml)
        self.camp = load_campaign(self.camp_yaml)
        self.cid = str(self.camp["campaign_id"])
        self.n = int(self.camp["n_per_cell"])
        self.base_seed = int(self.camp["base_seed"])
        self.replay_pct = float(self.camp.get("replay_pct") or 0.0)
        top = self.camp.get("topup") or dict()
        self.topup_rounds_max = int(top.get("rounds_max", 0) or 0)
        self.seed_offset = int(top.get("seed_offset", 1000000) or 1000000)
        self.guard_dir = guard_dir
        self.runs_root = runs_root
        self.campaign_dir = os.path.join(runs_root, self.cid)
        self.my_max = max(1, int(my_max_slots))
        self.numa_nodes = tuple(numa_nodes)
        self.host_fallback = int(host_max_slots_fallback)
        self.poll = float(poll_interval)
        self.exit4_backoff = float(exit4_backoff)
        self.claim_defer = float(claim_defer)
        self.runner = (runner_path
                       or os.environ.get("OOO_SAMPLE_RUNNER")
                       or DEFAULT_SAMPLE_RUNNER)
        self.handoff = os.environ.get("OOO_HANDOFF") or DEFAULT_HANDOFF
        self.workers = dict()      # token -> worker record
        self.deferred = dict()     # rep -> defer-until ts
        self.quarantined = set()   # in-memory skip (restart re-attempts once)
        self.replay_skip = set()   # sample dirs that failed non-recoverably
        self.replay_backoff_until = 0.0
        self.worker_seq = 0
        self.instance_key = f"{self.cid}__SCHEDULER"
        self.pidfile = os.path.join(guard_dir, "scheduler", f"{self.cid}.json")
        self.state_path = os.path.join(self.campaign_dir,
                                       SCHED_STATE_FILENAME)
        self.topup = read_json(self.state_path) or dict()
        if not isinstance(self.topup, dict):
            self.topup = dict()

    # ---- worker launch / reap ------------------------------------------

    def _launch(self, kind, rep=None, topup_round=None, sample_dir=None):
        self.worker_seq += 1
        idx = self.worker_seq
        cpus = NUMA_CPU_RANGES[self.numa_nodes[idx % len(self.numa_nodes)]]
        if kind == "rep":
            run_id = run_id_for(self.cid, rep)
            argv = [sys.executable, self.runner, "run",
                    "--campaign-yaml", self.camp_yaml,
                    "--rep", str(rep),
                    "--guard-dir", self.guard_dir,
                    "--runs-root", self.runs_root]
            if topup_round is not None:
                argv += ["--topup-round", str(topup_round)]
            log_name = f"worker-{run_id}.log"
        else:
            argv = [sys.executable, self.runner, "replay",
                    "--sample-dir", sample_dir]
            log_name = "worker-replay-" + os.path.basename(sample_dir) + ".log"
        logdir = os.path.join(self.guard_dir, "scheduler", self.cid,
                              "worker-logs")
        os.makedirs(logdir, exist_ok=True)
        logpath = os.path.join(logdir, log_name)
        env = dict(os.environ)
        env["OOO_WORKER"] = f"{self.cid}-w{idx}"
        env["PYTHONHASHSEED"] = "0"
        lf = open(logpath, "ab")
        cmd = ["taskset", "-c", cpus] + argv
        proc = subprocess.Popen(cmd, stdout=lf, stderr=subprocess.STDOUT,
                                start_new_session=True, env=env)
        token = f"w{idx}"
        self.workers[token] = dict(proc=proc, log=lf, kind=kind, rep=rep,
                                   topup_round=topup_round,
                                   sample_dir=sample_dir, cpus=cpus)
        what = f"rep {rep}" + (f" topup-round {topup_round}"
                               if topup_round else "")
        if kind == "replay":
            what = f"replay {sample_dir}"
        _log(f"dispatched {what} (pid={proc.pid} cpus={cpus} "
             f"in-flight={len(self.workers)})")

    def _reap(self):
        for token in list(self.workers):
            w = self.workers[token]
            rc = w["proc"].poll()
            if rc is None:
                continue
            try:
                w["log"].close()
            except OSError:
                pass
            del self.workers[token]
            now = time.time()
            if w["kind"] == "rep":
                rep = w["rep"]
                if rc == 0:
                    _log(f"rep {rep} finished (exit 0)")
                elif rc == 3:
                    _log(f"rep {rep} claim held elsewhere (exit 3); "
                         f"deferring {self.claim_defer}s")
                    self.deferred[rep] = now + self.claim_defer
                elif rc == 4:
                    _log(f"rep {rep} got no slot (exit 4); retrying the same "
                         f"rep after {self.exit4_backoff}s")
                    self.deferred[rep] = now + self.exit4_backoff
                elif rc == 5:
                    _log(f"rep {rep} QUARANTINED (exit 5); evidence kept, "
                         f"continuing with other reps")
                    self.quarantined.add(rep)
                    self._record_quarantine(rep, "worker exit 5")
                else:
                    _log(f"rep {rep} worker exited rc={rc}; dead-claim sweep "
                         f"will free its claim for re-dispatch")
            else:
                if rc == 0:
                    _log(f"replay done: {w['sample_dir']}")
                elif rc == 4:
                    _log(f"replay got no slot (exit 4); backing off "
                         f"{self.exit4_backoff}s")
                    self.replay_backoff_until = now + self.exit4_backoff
                else:
                    _log(f"replay rc={rc} for {w['sample_dir']}; WARNING, "
                         f"not retried by this instance")
                    self.replay_skip.add(w["sample_dir"])

    # ---- guard interactions --------------------------------------------

    def _sweep_dead_claims(self):
        cdir = os.path.join(self.guard_dir, "claims")
        if not os.path.isdir(cdir):
            return 0
        prefix = self.cid + "__"
        freed = 0
        for name in os.listdir(cdir):
            if not (name.startswith(prefix) and name.endswith(".claim")):
                continue
            path = os.path.join(cdir, name)
            j = read_json(path)
            if j is None:
                continue
            if ooo_guard.pid_matches(j.get("pid"), j.get("starttime")):
                continue  # live owner (mine or foreign): never touch
            key = name[:-len(".claim")]
            try:
                ooo_guard.claim_release(self.guard_dir, key, force=True)
                freed += 1
                _log(f"force-released dead-owner claim {key} "
                     f"(pid={j.get('pid')})")
            except ooo_guard.GuardError:
                pass
        return freed

    def _record_quarantine(self, rep, detail):
        entry = dict(campaign=self.cid, rep=rep,
                     run_id=run_id_for(self.cid, rep), ts=_now_iso(),
                     detail=detail)
        qpath = os.path.join(self.guard_dir, "quarantine.jsonl")
        with open(qpath, "a") as f:
            f.write(json.dumps(entry) + "\n")
            f.flush()
            os.fsync(f.fileno())
        spath = os.path.join(self.guard_dir, "state.json")
        st = read_json(spath) or dict()
        if not isinstance(st.get("quarantine"), list):
            st["quarantine"] = []
        st["quarantine"] = st["quarantine"] + [entry]
        atomic_write_json(spath, st)

    def _capacity_ok(self):
        if len(self.workers) >= self.my_max:
            return False
        host_max = policy_host_max(self.guard_dir, self.host_fallback)
        if host_max <= 0:
            return False  # TRIP: policy daemon zeroed the host slots
        st = ooo_guard.slot_status(self.guard_dir)
        if st["n_active"] >= host_max:
            return False
        return True

    # ---- task selection --------------------------------------------------

    def _save_topup(self):
        atomic_write_json(self.state_path, self.topup)

    def _maybe_open_topup(self, prog):
        if self.topup.get("exhausted"):
            return
        if self.topup.get("round") is None:
            if self.topup_rounds_max < 1:
                self.topup["exhausted"] = True
                self.topup["round"] = 0
                _log("topup not allowed (rounds_max=0): marking exhausted")
                self._save_topup()
                return
            gap = self.n - len(prog.valid_reps)
            self.topup["round"] = 1
            self.topup["gap_at_start"] = gap
            self.topup["dispatched"] = []
            _log(f"topup round 1 open: gap={gap} "
                 f"(seed={self.base_seed}+{self.seed_offset}+round*1000+rep)")
            self._save_topup()

    def _topup_round_closed(self, prog):
        d = self.topup.get("dispatched") or []
        if not d:
            return False   # round just opened, nothing dispatched yet
        for rep in d:
            if rep not in prog.attempted_reps:
                return False
        for w in self.workers.values():
            if w["kind"] == "rep" and w.get("rep") in d:
                return False
        return True

    def _advance_topup(self, prog):
        if len(prog.valid_reps) >= self.n:
            return
        r = self.topup.get("round") or 0
        if r >= self.topup_rounds_max:
            self.topup["exhausted"] = True
            _log(f"topup EXHAUSTED after round {r}: "
                 f"valid={len(prog.valid_reps)} < target={self.n}")
        else:
            gap = self.n - len(prog.valid_reps)
            self.topup["round"] = r + 1
            self.topup["gap_at_start"] = gap
            self.topup["dispatched"] = []
            _log(f"topup round {r + 1} open: gap={gap}")
        self._save_topup()

    def _next_rep_task(self, prog, now):
        in_flight = set(w["rep"] for w in self.workers.values()
                        if w["kind"] == "rep")
        # phase 1: next unattempted normal rep (0..n-1)
        for rep in range(self.n):
            if rep in prog.attempted_reps or rep in in_flight:
                continue
            if rep in self.quarantined:
                continue
            if self.deferred.get(rep, 0) > now:
                continue
            return rep, None
        if len(prog.valid_reps) >= self.n:
            return None, None
        # topup only when every normal rep is attempted or quarantined
        for rep in range(self.n):
            if (rep not in prog.attempted_reps
                    and rep not in self.quarantined):
                return None, None  # some rep still cooling down / in flight
        if self.topup.get("exhausted"):
            return None, None
        self._maybe_open_topup(prog)
        if self.topup.get("exhausted"):
            return None, None
        if self._topup_round_closed(prog):
            self._advance_topup(prog)
            if self.topup.get("exhausted"):
                return None, None
        r = self.topup.get("round")
        if r is None:
            return None, None
        budget = int(self.topup.get("gap_at_start") or 0)
        dispatched = list(self.topup.get("dispatched") or [])
        if len(dispatched) >= budget:
            return None, None  # round fully dispatched; wait for outcomes
        rep = TOPUP_REP_BASE
        while True:
            if (rep in prog.attempted_reps or rep in in_flight
                    or rep in self.quarantined
                    or self.deferred.get(rep, 0) > now):
                rep += 1
                continue
            break
        if rep not in dispatched:
            dispatched.append(rep)
            self.topup["dispatched"] = dispatched
            self._save_topup()
        return rep, r

    def _replay_target(self, prog):
        """Ordered valid sample dirs needing replay: the first
        round(replay_pct% x n_valid) in results order whose observation has
        no replay block yet (idempotent across restarts)."""
        n_replay = int(round(self.replay_pct / 100.0
                             * len(prog.valid_reps)))
        if n_replay <= 0:
            return []
        out = []
        counted = set()
        for row in prog.rows:
            rep = row.get("rep")
            if not isinstance(rep, int) or rep in counted:
                continue
            if rep not in prog.valid_reps:
                continue
            run_id = str(row.get("run_id") or run_id_for(self.cid, rep))
            sdir = os.path.join(self.campaign_dir, "samples", run_id)
            if sdir in self.replay_skip:
                continue
            oj = read_json(os.path.join(sdir, "observation.json"))
            if isinstance(oj, dict) and isinstance(oj.get("replay"), dict):
                continue  # already replayed
            out.append(sdir)
            counted.add(rep)
            if len(out) >= n_replay:
                break
        return out

    # ---- main loop ---------------------------------------------------------

    def _prune_deferred(self, prog, now):
        for rep in list(self.deferred):
            if self.deferred[rep] <= now or rep in prog.attempted_reps:
                del self.deferred[rep]

    def _main_loop(self):
        while True:
            now = time.time()
            self._sweep_dead_claims()
            self._reap()
            prog = scan_progress(self.campaign_dir)
            self._prune_deferred(prog, now)
            valid = len(prog.valid_reps)
            dispatched = False
            if valid < self.n:
                if self._capacity_ok():
                    task = self._next_rep_task(prog, now)
                    if task is not None and task[0] is not None:
                        rep, tr = task
                        self._launch("rep", rep=rep, topup_round=tr)
                        dispatched = True
            else:
                todo = self._replay_target(prog)
                if todo:
                    if (not self.workers and self._capacity_ok()
                            and now >= self.replay_backoff_until):
                        self._launch("replay", sample_dir=todo[0])
                        dispatched = True
                elif not self.workers:
                    _log(f"campaign {self.cid} complete: valid={valid} "
                         f"target={self.n}; replays done")
                    return 0
            if not self.workers and not dispatched and valid < self.n:
                if self.deferred:
                    pass  # cooldowns pending -- keep waiting
                else:
                    _log(f"stopping: valid={valid} < target={self.n}, "
                         f"nothing dispatchable "
                         f"(topup exhausted={bool(self.topup.get('exhausted'))})")
                    return 3
            time.sleep(self.poll)

    def _cleanup(self):
        try:
            os.unlink(self.pidfile)
        except OSError:
            pass
        try:
            ooo_guard.claim_release(self.guard_dir, self.instance_key)
        except ooo_guard.GuardError:
            pass

    def _handoff_campaign(self):
        if os.path.exists(os.path.join(self.campaign_dir, "handoff.json")):
            _log("campaign handoff already present; skipping")
            return
        cmd = [sys.executable, self.handoff, "campaign",
               "--dir", self.campaign_dir,
               "--campaign-yaml", self.camp_yaml]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True,
                               timeout=1800)
            if p.returncode == 0:
                _log("campaign handoff generated")
            else:
                _log(f"WARNING: campaign handoff rc={p.returncode}: "
                     f"{(p.stderr or p.stdout or '').strip()[:200]}")
        except (OSError, subprocess.TimeoutExpired) as e:
            _log(f"WARNING: campaign handoff failed: {e}")

    def run(self):
        self._sweep_dead_claims()
        if not ooo_guard.claim_acquire(self.guard_dir, self.instance_key):
            _log(f"another scheduler instance for {self.cid} is ALIVE "
                 f"(claim {self.instance_key}); refusing to run")
            return 1
        atomic_write_json(self.pidfile, dict(
            pid=os.getpid(),
            starttime=ooo_guard.proc_starttime(os.getpid()),
            campaign=self.cid, ts=_now_iso(),
            numa_nodes=list(self.numa_nodes)))
        _log(f"start campaign={self.cid} n={self.n} "
             f"base_seed={self.base_seed} my_max={self.my_max} "
             f"numa={list(self.numa_nodes)} runner={self.runner}")
        try:
            rc = self._main_loop()
        finally:
            self._cleanup()
        self._handoff_campaign()
        return rc


def default_identity_probe():
    """(HEAD, gem5.opt sha256) of this worktree; None where unreadable."""
    head = None
    try:
        p = subprocess.run(["git", "-C", REPO_ROOT, "rev-parse", "HEAD"],
                           capture_output=True, text=True, timeout=60)
        head = p.stdout.strip() if p.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        head = None
    sha = None
    gem5 = os.path.join(REPO_ROOT, "build", "ARM", "gem5.opt")
    try:
        h = hashlib.sha256()
        with open(gem5, "rb") as f:
            for chunk in iter(lambda: f.read(4 * 1024 * 1024), b""):
                h.update(chunk)
        sha = h.hexdigest()
    except OSError:
        sha = None
    return head, sha


def default_scheduler_launcher(cid, campaign_yaml, numa_nodes):
    """Launch one detached single-campaign scheduler instance; returns pid."""
    argv = [sys.executable, os.path.abspath(__file__), "start",
            "--campaign-yaml", campaign_yaml,
            "--my-max-slots", "2",
            "--numa-nodes", ",".join(str(n) for n in numa_nodes)]
    proc = subprocess.Popen(argv, start_new_session=True)
    return proc.pid


class PolicyDaemon:
    """Machine-unique decision maker: monitor + identity + slot ladder +
    progress snapshots + handoff. sampler/prober/launcher are injectable
    for the dry tests; production uses the /proc-based defaults."""

    def __init__(self, batch, batch_path, guard_dir, runs_root, launch=False,
                 sampler=None, prober=None, launcher=None, handoff_path=None):
        self.b = batch
        self.batch_path = batch_path
        self.guard_dir = guard_dir
        self.runs_root = runs_root
        self.launch = launch
        self.sampler = sampler or ooo_guard.sample_resources
        self.prober = prober or default_identity_probe
        self.launcher = launcher or default_scheduler_launcher
        self.handoff = handoff_path or os.environ.get("OOO_HANDOFF") \
            or DEFAULT_HANDOFF
        self.policy_path = os.path.join(guard_dir, "ctl", "policy.json")
        self.state_path = os.path.join(guard_dir, "state.json")
        self.log_path = os.path.join(guard_dir, "monitor", "resources.log")
        self.tick_s = float(batch.get("tick_s") or 60)
        self.good_ticks = 0
        self.paging_streak = 0
        self.blocked_streak = 0
        self.last_paging = None
        self.scaleup_done = False
        self.launched = set()
        self.trips = []
        self.peaks = dict(min_mem_available_kib=None, max_gem5_rss_kib=0,
                          max_gem5_count=0)

    # ---- policy file / ladders -------------------------------------------

    def _write_policy(self, host_max, why):
        atomic_write_json(self.policy_path, dict(
            host_max_slots=int(host_max), batch_id=self.b.get("batch_id"),
            reason=why, ts=_now_iso()))
        _log(f"policy: host_max_slots={int(host_max)} ({why})")

    def _host_max(self):
        j = read_json(self.policy_path)
        if isinstance(j, dict) and isinstance(j.get("host_max_slots"), int):
            return j["host_max_slots"]
        return None

    def _ladder(self):
        top = int(self.b.get("host_max_slots_max") or 8)
        trip = self.b.get("trip") or dict()
        deg = trip.get("degrade") or [6, 4]
        return [top] + sorted((int(x) for x in deg), reverse=True)

    def _append_monitor(self, r):
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        row = dict(r)
        row["gem5_count"] = len(r.get("gem5_pids") or [])
        row.pop("gem5_pids", None)
        new = not os.path.exists(self.log_path)
        with open(self.log_path, "a") as f:
            if new:
                f.write(",".join(ooo_guard.MONITOR_FIELDS) + "\n")
            f.write(",".join(str(row.get(k, "")) for k in
                             ooo_guard.MONITOR_FIELDS) + "\n")
            f.flush()

    def _update_peaks(self, r):
        mem = r.get("mem_available_kib")
        if isinstance(mem, int) and mem > 0:
            cur = self.peaks.get("min_mem_available_kib")
            if cur is None or mem < cur:
                self.peaks["min_mem_available_kib"] = mem
        rss = r.get("gem5_rss_kib") or 0
        self.peaks["max_gem5_rss_kib"] = max(
            self.peaks.get("max_gem5_rss_kib") or 0, rss)
        cnt = len(r.get("gem5_pids") or [])
        self.peaks["max_gem5_count"] = max(
            self.peaks.get("max_gem5_count") or 0, cnt)

    def _instance_alive(self, cid):
        j = read_json(os.path.join(self.guard_dir, "scheduler",
                                   f"{cid}.json"))
        if not isinstance(j, dict):
            return False
        return ooo_guard.pid_matches(j.get("pid"), j.get("starttime"))

    def _scaleup(self):
        su = self.b.get("scaleup") or dict()
        top = int(self.b.get("host_max_slots_max") or 8)
        self._write_policy(top, f"stable for {su.get('after_s')}s -- scale up")
        self.scaleup_done = True
        yamls = self.b.get("campaign_yamls") or dict()
        for cid in (su.get("add") or []):
            if cid in self.launched or self._instance_alive(cid):
                _log(f"scaleup: {cid} instance already running; "
                     f"not launched again")
                continue
            ypath = yamls.get(cid)
            if not ypath or not os.path.isfile(ypath):
                _log(f"WARNING: scaleup campaign {cid} yaml missing "
                     f"({ypath}); NOT launched")
                continue
            numa = self.b.get("numa") or dict()
            node = numa.get(cid, 0)
            nodes = [int(node)] + [n for n in sorted(NUMA_CPU_RANGES)
                                   if n != int(node)]
            if self.launch:
                pid = self.launcher(cid, ypath, nodes)
                self.launched.add(cid)
                _log(f"scaleup: launched scheduler for {cid} "
                     f"(pid={pid}, numa={nodes})")
            else:
                _log(f"scaleup: host_max raised to {top}; {cid} instance "
                     f"NOT launched (no --launch); start it manually")

    def _degrade(self, why):
        ladder = self._ladder()
        cur = self._host_max()
        if cur is None:
            cur = ladder[0]
        if cur <= ladder[-1]:
            _log(f"TRIP {why}: already at floor {ladder[-1]}")
            return False
        idx = ladder.index(cur) if cur in ladder else 0
        nxt = ladder[min(idx + 1, len(ladder) - 1)]
        self._write_policy(nxt, f"resource TRIP ({why})")
        return True

    def tick(self):
        """One decision tick. Returns None to continue, or an exit code."""
        r = self.sampler()
        self._append_monitor(r)
        self._update_peaks(r)
        head, gem5_sha = self.prober()
        frozen = self.b.get("frozen") or dict()
        if (head != frozen.get("head")
                or gem5_sha != frozen.get("gem5_sha256")):
            trip = dict(kind="identity_drift", ts=_now_iso(),
                        expected_head=frozen.get("head"),
                        observed_head=head,
                        expected_gem5=frozen.get("gem5_sha256"),
                        observed_gem5=gem5_sha)
            self.trips.append(trip)
            self._write_policy(0, "identity drift -- dispatch halted")
            self._write_state(r)
            _log(f"TRIP identity drift: head {head} vs frozen "
                 f"{frozen.get('head')}, gem5 {gem5_sha} vs frozen "
                 f"{frozen.get('gem5_sha256')}; policy zeroed; exiting 2")
            return 2
        if self._host_max() is None:
            init = int(self.b.get("host_max_slots_initial") or 6)
            self._write_policy(init, "initial policy")
        # ---- ladder inputs
        mem = r.get("mem_available_kib") or -1
        paging_now = (r.get("pswpin_cum") or 0, r.get("pswpout_cum") or 0)
        if self.last_paging is None:
            paging_delta = 0   # baseline tick
        else:
            paging_delta = ((paging_now[0] - self.last_paging[0])
                            + (paging_now[1] - self.last_paging[1]))
        self.last_paging = paging_now
        blocked = r.get("procs_blocked") or 0
        disk = r.get("disk_free_bytes") or -1
        self.paging_streak = self.paging_streak + 1 if paging_delta > 0 else 0
        self.blocked_streak = self.blocked_streak + 1 if blocked > 0 else 0
        trip = self.b.get("trip") or dict()
        mem_floor = int(trip.get("mem_below_kib") or 10485760)
        degraded = False
        if 0 < mem < mem_floor:
            degraded = self._degrade(f"MemAvailable={mem}KiB < "
                                     f"{mem_floor}KiB")
        elif self.paging_streak >= 3:
            degraded = self._degrade(f"paging {self.paging_streak} "
                                     f"consecutive ticks")
        elif self.blocked_streak >= 3:
            degraded = self._degrade(f"blocked>0 {self.blocked_streak} "
                                     f"consecutive ticks")
        if degraded:
            self.paging_streak = 0
            self.blocked_streak = 0
        # ---- good-tick accounting + scaleup
        su = self.b.get("scaleup") or dict()
        need_mem = int(su.get("min_mem_available_kib") or 12582912)
        after_s = float(su.get("after_s") or 900)
        good = (mem >= need_mem and paging_delta == 0 and blocked == 0
                and disk > 200 * 1024 ** 3)
        self.good_ticks = self.good_ticks + 1 if (good and not degraded) else 0
        if (not self.scaleup_done and self.good_ticks > 0
                and self.good_ticks * self.tick_s >= after_s):
            self._scaleup()
        self._write_state(r)
        return self._completion_check()

    # ---- progress snapshot / state / completion -------------------------

    def _campaign_progress_snapshot(self):
        out = dict()
        for cid, ypath in (self.b.get("campaign_yamls") or dict()).items():
            cdir = os.path.join(self.runs_root, cid)
            prog = scan_progress(cdir)
            camp = dict()
            try:
                with open(ypath) as f:
                    loaded = yaml.safe_load(f)
                if isinstance(loaded, dict):
                    camp = loaded
            except (OSError, yaml.YAMLError):
                camp = dict()
            target = camp.get("n_per_cell")
            valid = len(prog.valid_reps)
            out[cid] = dict(valid=valid,
                            attempted=len(prog.attempted_reps),
                            target=target,
                            rows=prog.n_rows,
                            complete=(isinstance(target, int)
                                      and valid >= int(target)))
        return out

    def _scheduler_instances(self):
        out = dict()
        sdir = os.path.join(self.guard_dir, "scheduler")
        if not os.path.isdir(sdir):
            return out
        for name in sorted(os.listdir(sdir)):
            if not name.endswith(".json"):
                continue
            j = read_json(os.path.join(sdir, name))
            if not isinstance(j, dict):
                continue
            alive = ooo_guard.pid_matches(j.get("pid"), j.get("starttime"))
            out[name[:-5]] = dict(pid=j.get("pid"), alive=bool(alive))
        return out

    def _write_state(self, r):
        quar = []
        qpath = os.path.join(self.guard_dir, "quarantine.jsonl")
        if os.path.isfile(qpath):
            with open(qpath) as f:
                for line in f:
                    try:
                        quar.append(json.loads(line))
                    except ValueError:
                        continue
        state = dict(
            ts=_now_iso(), batch_id=self.b.get("batch_id"),
            policy=read_json(self.policy_path) or dict(),
            campaigns=self._campaign_progress_snapshot(),
            schedulers=self._scheduler_instances(),
            resource_peaks=dict(self.peaks),
            trips=list(self.trips), quarantine=quar,
            scaleup_done=self.scaleup_done,
            launched=sorted(self.launched))
        atomic_write_json(self.state_path, state)

    def _handoff_one(self, cid, cdir):
        yamls = self.b.get("campaign_yamls") or dict()
        cmd = [sys.executable, self.handoff, "campaign",
               "--dir", cdir, "--campaign-yaml", str(yamls.get(cid))]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True,
                               timeout=1800)
            if p.returncode == 0:
                _log(f"handoff campaign {cid}: ok")
            else:
                _log(f"WARNING: handoff campaign {cid} rc={p.returncode}: "
                     f"{(p.stderr or p.stdout or '').strip()[:200]}")
        except (OSError, subprocess.TimeoutExpired) as e:
            _log(f"WARNING: handoff campaign {cid} failed: {e}")

    def _handoff_master(self, snaps):
        dirs = [os.path.join(self.runs_root, cid) for cid in snaps]
        cmd = [sys.executable, self.handoff, "master", "--dirs"] + dirs \
            + ["--batch", self.batch_path]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True,
                               timeout=1800)
            if p.returncode == 0:
                _log("handoff master: ok")
            else:
                _log(f"WARNING: handoff master rc={p.returncode}: "
                     f"{(p.stderr or p.stdout or '').strip()[:200]}")
        except (OSError, subprocess.TimeoutExpired) as e:
            _log(f"WARNING: handoff master failed: {e}")

    def _completion_check(self):
        snaps = self._campaign_progress_snapshot()
        if not snaps:
            return None
        if not all(s["complete"] for s in snaps.values()):
            return None
        _log("all campaigns complete -- running handoffs")
        for cid in snaps:
            cdir = os.path.join(self.runs_root, cid)
            if os.path.exists(os.path.join(cdir, "handoff.json")):
                continue
            self._handoff_one(cid, cdir)
        self._handoff_master(snaps)
        return 0

    def run(self):
        _log(f"policy-daemon start: batch={self.b.get('batch_id')} "
             f"guard={self.guard_dir} tick_s={self.tick_s} "
             f"launch={self.launch}")
        while True:
            rc = self.tick()
            if rc is not None:
                _log(f"policy-daemon exiting rc={rc}")
                return rc
            time.sleep(self.tick_s)


def _cmd_status(guard_dir, runs_root):
    pol = read_json(os.path.join(guard_dir, "ctl", "policy.json"))
    print("policy:", json.dumps(pol, sort_keys=True))
    st = read_json(os.path.join(guard_dir, "state.json"))
    if st:
        camps = st.get("campaigns") or dict()
        for cid in sorted(camps):
            c = camps[cid]
            print(f"campaign {cid}: valid={c.get('valid')} "
                  f"attempted={c.get('attempted')} target={c.get('target')} "
                  f"complete={c.get('complete')}")
        print("schedulers:", json.dumps(st.get("schedulers") or dict(),
                                        sort_keys=True))
        print("trips:", json.dumps(st.get("trips") or []))
    else:
        print("state: (none yet)")
    slots = ooo_guard.slot_status(guard_dir)
    print(f"slots: n_active={slots['n_active']} "
          f"n_stale={slots['n_stale']} n_slots={slots['n_slots']}")
    for s in slots["slots"]:
        print(f"  slot {s.get('index')}: {s.get('state')} "
              f"owner={s.get('owner')} campaign={s.get('campaign')}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="OOO L0-L5 scheduler")
    sub = ap.add_subparsers(dest="cmd", required=True)

    st = sub.add_parser("start", help="single-campaign worker loop")
    st.add_argument("--guard-dir", default=ooo_guard.DEFAULT_GUARD_DIR)
    st.add_argument("--campaign-yaml", required=True)
    st.add_argument("--my-max-slots", type=int, default=2)
    st.add_argument("--numa-nodes", default="0,1")
    st.add_argument("--runs-root", default=DEFAULT_RUNS_ROOT)
    st.add_argument("--host-max-slots", type=int, default=6)
    st.add_argument("--poll-interval", type=float, default=0.5)
    st.add_argument("--exit4-backoff", type=float, default=10.0)
    st.add_argument("--claim-defer", type=float, default=30.0)

    pd = sub.add_parser("policy-daemon", help="machine-unique policy maker")
    pd.add_argument("--guard-dir", default=ooo_guard.DEFAULT_GUARD_DIR)
    pd.add_argument("--batch", required=True)
    pd.add_argument("--runs-root", default=DEFAULT_RUNS_ROOT)
    pd.add_argument("--launch", action="store_true",
                    help="allow spawning scheduler instances (initial + "
                         "scaleup); without it the daemon only manages "
                         "policy and reports pending launches")
    pd.add_argument("--tick-s", type=float, default=None)

    sa = sub.add_parser("status", help="read-only snapshot")
    sa.add_argument("--guard-dir", default=ooo_guard.DEFAULT_GUARD_DIR)
    sa.add_argument("--runs-root", default=DEFAULT_RUNS_ROOT)

    args = ap.parse_args(argv)

    if args.cmd == "start":
        nodes = parse_numa_nodes(args.numa_nodes)
        sched = CampaignScheduler(
            campaign_yaml=args.campaign_yaml, guard_dir=args.guard_dir,
            runs_root=args.runs_root, my_max_slots=args.my_max_slots,
            numa_nodes=nodes,
            host_max_slots_fallback=args.host_max_slots,
            poll_interval=args.poll_interval,
            exit4_backoff=args.exit4_backoff,
            claim_defer=args.claim_defer)
        return sched.run()
    if args.cmd == "policy-daemon":
        batch = load_batch(args.batch)
        if args.tick_s is not None:
            batch["tick_s"] = args.tick_s
        daemon = PolicyDaemon(batch, os.path.abspath(args.batch),
                              args.guard_dir, args.runs_root,
                              launch=args.launch)
        return daemon.run()
    if args.cmd == "status":
        _cmd_status(args.guard_dir, args.runs_root)
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
