#!/usr/bin/env python3
"""fake_sample_runner.py -- test stub mirroring the CLI contract of
tools/ooo_sample_runner.py (Subagent-A's real executor) for the
scheduler dry tests (tools/tests/test_ooo_scheduler_dry.py).

Wired in via the scheduler's OOO_SAMPLE_RUNNER env hook; never used by
production paths. CLI shape is identical to the real runner:

    run    --campaign-yaml Y --rep N [--topup-round R]
           --guard-dir G --runs-root R
    replay --sample-dir D

Exit codes (the scheduler's contract): 0 done / COMPLETE read-only skip;
3 claim conflict; 4 no slot; 5 QUARANTINE (evidence kept, no COMPLETE,
no results row).

Behavior control comes from the JSON file named by env OOO_FAKE_CTRL
(all keys optional):

  sleep: [lo, hi]      uniform sleep range while holding the slot
  simerr: [reps...]    reps whose synthesized row is SimulatorError
  reps: mapping rep(str) -> control with:
        exit: 3|4|5    scripted exit code
        times: k       only on the first k attempts (default: always)

The stub uses the REAL guard (claims + slots via tools/ooo_guard.py) so
the scheduler's admission logic is exercised against real lock files,
and self-measures its concurrency with marker files under
<campaign_dir>/.fake_concurrency/ (max observed count in max.txt) so
the dry test can prove host_max_slots is respected end-to-end.
"""

import argparse
import json
import os
import random
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", ".."))
import ooo_guard  # noqa: E402

import yaml  # noqa: E402


def _read_json(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def _load_ctrl():
    p = os.environ.get("OOO_FAKE_CTRL")
    if not p:
        return dict()
    c = _read_json(p)
    return c if isinstance(c, dict) else dict()


def _policy_max_slots(guard_dir):
    j = _read_json(os.path.join(guard_dir, "ctl", "policy.json"))
    if isinstance(j, dict) and isinstance(j.get("host_max_slots"), int):
        if j["host_max_slots"] > 0:
            return j["host_max_slots"]
    return 8


def _run_id(cid, rep):
    return f"{cid}-c0000-r{rep:04d}"


def _atomic_json(path, obj):
    tmp = path + f".tmp{os.getpid()}"
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=1, sort_keys=True)
        f.write("\n")
    os.replace(tmp, path)


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


class _Conc:
    """Self-measured concurrency via marker files (O_EXCL unique names);
    max.txt records the maximum count observed by any holder."""

    def __init__(self, campaign_dir):
        self.dir = os.path.join(campaign_dir, ".fake_concurrency")
        os.makedirs(self.dir, exist_ok=True)
        self.marker = os.path.join(
            self.dir, f"p{os.getpid()}.t{time.time_ns()}")
        fd = os.open(self.marker, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(fd)

    def count(self):
        return len([f for f in os.listdir(self.dir)
                    if f.startswith("p") and not f.endswith(".txt")])

    def record(self):
        n = self.count()
        with open(os.path.join(self.dir, "max.txt"), "a") as f:
            f.write(f"{n}\n")

    def release(self):
        try:
            os.unlink(self.marker)
        except OSError:
            pass


def _scripted_exit(ctrl, rep, attempt):
    """Return a scripted exit code for this rep/attempt, or None."""
    reps = ctrl.get("reps") or dict()
    c = reps.get(str(rep)) or reps.get(rep)
    if not isinstance(c, dict):
        return None
    times = c.get("times")
    if times is not None and attempt > int(times):
        return None
    code = c.get("exit")
    return int(code) if code in (3, 4, 5) else None


def _attempt_count(campaign_dir, rep):
    d = os.path.join(campaign_dir, ".fake_state")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, f"rep_{rep}.attempts")
    with open(p, "a") as f:
        f.write("x\n")
        f.flush()
        os.fsync(f.fileno())
    n = 0
    with open(p) as f:
        for _ in f:
            n += 1
    return n


def cmd_run(args):
    ctrl = _load_ctrl()
    with open(args.campaign_yaml) as f:
        camp = yaml.safe_load(f)
    cid = str(camp["campaign_id"])
    base_seed = int(camp["base_seed"])
    top = camp.get("topup") or dict()
    offset = int(top.get("seed_offset", 1000000) or 1000000)
    run_id = _run_id(cid, args.rep)
    campaign_dir = os.path.join(args.runs_root, cid)
    sample_dir = os.path.join(campaign_dir, "samples", run_id)
    # idempotent read-only skip (finalized sample from an earlier life)
    if os.path.isfile(os.path.join(sample_dir, "COMPLETE.json")):
        print(f"[fake] {run_id}: COMPLETE exists; read-only skip")
        return 0
    key = f"{cid}__{run_id}"
    if not ooo_guard.claim_acquire(args.guard_dir, key):
        # claim held: if the holder already finalized, this is a skip;
        # otherwise it is a genuine conflict (exit 3)
        if os.path.isfile(os.path.join(sample_dir, "COMPLETE.json")):
            return 0
        print(f"[fake] {run_id}: claim busy -> exit 3")
        return 3
    try:
        attempt = _attempt_count(campaign_dir, args.rep)
        code = _scripted_exit(ctrl, args.rep, attempt)
        if code == 5:
            qdir = os.path.join(campaign_dir, "QUARANTINE", run_id)
            os.makedirs(os.path.join(qdir, "evidence"), exist_ok=True)
            with open(os.path.join(qdir, "evidence", "why.txt"), "w") as f:
                f.write("validation failed (scripted exit 5)\n")
            print(f"[fake] {run_id}: QUARANTINE -> exit 5")
            return 5
        if code in (3, 4):
            print(f"[fake] {run_id}: scripted exit {code}")
            return code
        max_slots = _policy_max_slots(args.guard_dir)
        try:
            h = ooo_guard.slot_acquire(args.guard_dir, "fake-worker", cid,
                                       run_id, max_slots=max_slots, node=0)
        except ooo_guard.GuardError:
            print(f"[fake] {run_id}: no slot (max={max_slots}) -> exit 4")
            return 4
        try:
            conc = _Conc(campaign_dir)
            conc.record()
            lo, hi = (ctrl.get("sleep") or [0.2, 1.0])
            time.sleep(random.uniform(float(lo), float(hi)))
            conc.release()
        finally:
            ooo_guard.slot_release(h)
    finally:
        ooo_guard.claim_release(args.guard_dir, key)
    return _finalize(camp, campaign_dir, sample_dir, run_id, args, ctrl,
                     base_seed, offset)


def _finalize(camp, campaign_dir, sample_dir, run_id, args, ctrl, base_seed,
              offset):
    cid = str(camp["campaign_id"])
    rep = args.rep
    simerr = rep in (ctrl.get("simerr") or [])
    classification = "SimulatorError" if simerr else "Masked"
    if args.topup_round is not None:
        seed = base_seed + offset + int(args.topup_round) * 1000 + rep
        topup = dict(round=int(args.topup_round))
    else:
        seed = base_seed + rep
        topup = None
    os.makedirs(os.path.join(sample_dir, "evidence"), exist_ok=True)
    with open(os.path.join(sample_dir, "manifest.yaml"), "w") as f:
        f.write(f"# synthetic manifest for {run_id}\n"
                f"campaign_id: {cid}\nrep: {rep}\nseed: {seed}\n")
    observation = dict(
        schema_version="ooo-observation/v1",
        classification=classification,
        identity=dict(campaign_id=cid, run_id=run_id, rep=rep, seed=seed),
        l0=dict(injected=0 if simerr else 1),
        l1=dict(status="ok"), l2=dict(status="ok"),
        l3=dict(status="unsupported"),
        l4=dict(status="none_detected"), l5=dict(classification=classification),
        chain_complete=(not simerr), chain_gaps=[],
        files=dict())
    _atomic_json(os.path.join(sample_dir, "observation.json"), observation)
    _atomic_json(os.path.join(sample_dir, "COMPLETE.json"),
                 dict(run_id=run_id, ts=_now(), fake=True))
    row = dict(
        manifest=f"samples/{run_id}/manifest.yaml", run_id=run_id, rep=rep,
        seed=seed, classification=classification,
        faults_injected=0 if simerr else 1, exit=0, timed_out=False,
        chain_complete=(not simerr), chain_gaps=[],
        observation=f"samples/{run_id}/observation.json", ts=_now())
    if topup:
        row["topup"] = topup
    with open(os.path.join(campaign_dir, "results.jsonl"), "a") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")
        f.flush()
        os.fsync(f.fileno())
    print(f"[fake] {run_id}: finalized classification={classification} "
          f"seed={seed}")
    return 0


def cmd_replay(args):
    guard_dir = os.environ.get("OOO_FAKE_GUARD_DIR", "")
    sample_dir = args.sample_dir
    obs_path = os.path.join(sample_dir, "observation.json")
    obs = _read_json(obs_path)
    if not isinstance(obs, dict):
        print(f"[fake] replay: no observation in {sample_dir}")
        return 5
    if isinstance(obs.get("replay"), dict):
        print(f"[fake] replay: already replayed (idempotent skip)")
        return 0
    max_slots = _policy_max_slots(guard_dir) if guard_dir else 8
    h = None
    if guard_dir:
        try:
            h = ooo_guard.slot_acquire(guard_dir, "fake-replay", "replay",
                                       os.path.basename(sample_dir),
                                       max_slots=max_slots, node=0)
        except ooo_guard.GuardError:
            print(f"[fake] replay: no slot -> exit 4")
            return 4
    try:
        time.sleep(0.1)
        obs["replay"] = dict(determinism="match",
                             pass2_classification=obs.get("classification"),
                             verdict_pass2="no_divergence",
                             checksum_pass2="match", ts=_now())
        _atomic_json(obs_path, obs)
    finally:
        if h is not None:
            ooo_guard.slot_release(h)
    print(f"[fake] replay: {sample_dir} done")
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--campaign-yaml", required=True)
    r.add_argument("--rep", type=int, required=True)
    r.add_argument("--topup-round", type=int, default=None)
    r.add_argument("--guard-dir", required=True)
    r.add_argument("--runs-root", required=True)
    p = sub.add_parser("replay")
    p.add_argument("--sample-dir", required=True)
    args = ap.parse_args()
    if args.cmd == "run":
        return cmd_run(args)
    return cmd_replay(args)


if __name__ == "__main__":
    sys.exit(main())
