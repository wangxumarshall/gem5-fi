#!/usr/bin/env python3
"""OOO P1 campaign engine — plan U11 (docs/superpowers/plans/
2026-10-08-ooo-p1-injectors-observation-campaign.md).

Per-sample lifecycle (goal directive, verbatim semantics):
  seed      = low 64 bits of SHA256("ooo-fi-v1|" + RunID + "|" + phase + "|"
              + sample_index)
  run_key   = <campaign>/<phase>/<RunID>/sample_<idx:06d>_<seed:016x>_<cfg12>
  manifest  = immutable JSON in a staging dir, validated BEFORE gem5 runs
  execution = ooo_guard.py run --type experiment (4-slot cap, U1b guard_pid)
              wrapping gem5 — native/compat loader auto-detected (F-008/F-011)
  observe   = tools/ooo_observe.py classify_ooo_run (U10 L0-L5 chain)
  placement = atomic os.rename staging -> <run_root>/<run_key>, then
              ooo_recover.mark_complete (write-once COMPLETE.json)

Honesty rules (CLAUDE.md / goal directive):
  - exit.rc missing -> verdict stays None (honest unknown); never guessed
  - unimplemented models / F1-F2 tiers / unverified workloads -> LOUD reject
    (exit 2), never a silent skip or a silent zero
  - write-once: COMPLETE samples are never silently re-run; without --resume
    the engine refuses, with --resume it skips them
  - a non-COMPLETE dir at the same run_key is a crashed attempt of the SAME
    deterministic seed — replaced, with a loud log line
  - baseline (no-injection golden check) must pass before any fault sample
"""
import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
import time

TOOLS = os.path.dirname(os.path.realpath(__file__))
REPO = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)

from ooo_models import (MODELS, INJECTOR_TO_FLAG, parse_items, _read,   # noqa: E402
                        DEFAULT_CHECKLIST)                              # U1 map
from ooo_recover import mark_complete, COMPLETE_NAME                    # noqa: E402
from ooo_observe import classify_ooo_run                                # noqa: E402
from classify import extract_checksum                                   # noqa: E402
import manifest_validate                                                # noqa: E402

SEED_LABEL = "ooo-fi-v1"
PHASES = ("engineering", "pilot", "screening", "confirmatory")
DEFAULT_CAMPAIGN = "ooo-p1"
DEFAULT_RUN_ROOT = os.path.join("runs", "ooo")
# Staging lives OUTSIDE run_root (a SIBLING of it): same filesystem so the
# final os.rename is atomic, but invisible to ooo_recover.discover_run_dirs,
# which treats any dir containing manifest.json as a run dir — an in-flight
# sample must never be classified INTERRUPTED/RUNNING by a scan.
DEFAULT_STAGING_ROOT = os.path.join("runs", ".ooo-staging")
DEFAULT_BASELINE_ROOT = os.path.join("runs", "ooo-baseline")
CONFIG_SE = os.path.join("configs", "se", "ooo_proxy.py")
DEFAULT_GEM5_BIN = os.path.join("build", "ARM", "gem5.opt")
DEFAULT_COMPAT_DIR = "/home/share/suke/wangxu/lsu_keeper/compat"
HEARTBEAT_INTERVAL = 30      # s (ooo_recover stale threshold is 600 s)
HANG_TIMEOUT = 300           # s — campaign yaml hang_timeout; guard kills at it
FIRST_CLOCK_DEFAULT = 1000   # campaign yaml trigger_value (F0 fires here)

# Workloads with VERIFIED goldens (workloads/ooo/README.md W1 table, 2026-09-23
# W1.1 双跑实测). W3 (A64-DecodeProbe) is intentionally absent — its golden is
# not yet verified; requesting it is a loud reject, never a silent zero.
WORKLOADS = {
    "W6": {
        "name": "coremark",
        "binary": os.path.join("workloads", "ooo", "coremark", "coremark"),
        "binary_sha256":
            "3a252bbc717de9e73f98ba05db3387bc26025b1f95294d63111ae55e8b27b000",
        "golden": "000000000000cf56",
        "golden_id": "coremark-golden-v1",
    },
}

# Models wired END-TO-END for this engine. Everything else (D02..D61) is
# loudly rejected until the U2-U9 injector families land. D01 = Int Decode
# opcode field single-bit flip (03-design-matrix D01a; campaign yaml
# grid.sub_field=opcode_bitflip; runner.py decode dispatch consumes exactly
# these flags).
MODEL_DISPATCH = {
    "D01": {
        "mode": "opcode_bitflip",
        "sub_field": "opcode_bitflip",
        "field": "opcode",
        "width_bits": 32,
        "layer": "physical",       # decode latch is microarchitectural state
        "component": "decode",
        "fault_model": "transient_bit_flip",
    },
}


def _die(msg, code=2):
    print("[ooo_campaign] FATAL: %s" % msg, file=sys.stderr)
    sys.exit(code)


def _log(msg):
    print("[ooo_campaign %s] %s" % (time.strftime("%H:%M:%S"), msg), flush=True)


# --------------------------------------------------------------- identity

def sample_seed(run_id, phase, sample_index):
    """Goal directive, verbatim: SHA256("ooo-fi-v1|"+RunID+"|"+phase+"|"
    +sample_index), low 64 bits of the hex digest."""
    h = hashlib.sha256(
        ("%s|%s|%s|%d" % (SEED_LABEL, run_id, phase, sample_index))
        .encode("utf-8")).hexdigest()
    return int(h[:16], 16)


def config_sha256():
    with open(os.path.join(REPO, CONFIG_SE), "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def make_run_key(campaign, phase, run_id, sample_index, seed, config_sha):
    return "%s/%s/%s/sample_%06d_%016x_%s" % (
        campaign, phase, run_id, sample_index, seed, config_sha[:12])


def resolve_item(item_spec):
    """ITEM-xxx -> (model_id, freq, workload) via the U1 mapping table
    (tools/ooo_models.py, 310-item cross-checked)."""
    items = parse_items(_read(DEFAULT_CHECKLIST))
    hits = [t for t in items if "ITEM-" + t[0] == item_spec]
    if len(hits) != 1:
        _die("item %s: %d hits in checklist (expect exactly 1)"
             % (item_spec, len(hits)))
    _num, model_id, freq, wl = hits[0]
    return model_id, freq, wl


def check_dispatchable(model_id, freq, workload):
    """Loud gate before anything runs: model wired? tier wired? workload
    golden verified? Dies (exit 2) on any 'no'."""
    if model_id not in MODEL_DISPATCH:
        _die("model %s not wired in MODEL_DISPATCH — its injector family "
             "lands in U2-U9; refusing to run an unwired model" % model_id)
    if freq != "F0":
        _die("tier %s not wired: CHAOSDecode py params expose only "
             "first/last/max/seed (F0 single-shot). F1/F2 need the U2/U3 "
             "trigger work; refusing to silently degrade" % freq)
    if workload not in WORKLOADS:
        _die("workload %s has no verified golden in WORKLOADS (W3 "
             "A64-DecodeProbe pending golden verification) — refusing"
             % workload)
    m = MODELS[model_id]
    if m["impl_status"] != "implemented":
        _die("model %s impl_status=%s in ooo_models"
             % (model_id, m["impl_status"]))
    if freq not in m["freqs"]:
        _die("tier %s not in model %s freqs %s"
             % (freq, model_id, m["freqs"]))
    if INJECTOR_TO_FLAG[m["injector"]] != "--chaos_decode":
        _die("model %s injector %s maps to %s, not --chaos_decode"
             % (model_id, m["injector"], INJECTOR_TO_FLAG[m["injector"]]))


# --------------------------------------------------------------- manifest

def _git_head():
    try:
        out = subprocess.run(["git", "-C", REPO, "rev-parse", "HEAD"],
                             capture_output=True, text=True, timeout=60)
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    _die("cannot read git HEAD (git rev-parse failed) — manifest source."
         "chaos_commit would be a guess")


def _gem5_base_commit():
    """CHAOS/gem5_base_version.md 'Commit:' line. The vendored tree has no
    nested .git — this file IS the provenance record."""
    path = os.path.join(REPO, "CHAOS", "gem5_base_version.md")
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                m = re.match(r"^Commit:\s+([0-9a-f]{7,40})\s*$", line.strip())
                if m:
                    return m.group(1)
    except OSError:
        pass
    _die("cannot parse gem5 base commit from %s" % path)


def build_manifest(run_id, run_key, model_id, freq, workload, seed,
                   first_clock, chaos_commit, gem5_commit):
    d = MODEL_DISPATCH[model_id]
    w = WORKLOADS[workload]
    return {
        "schema_version": "arm-chaos-fi/v1",
        "run_id": run_id,
        "run_key": run_key,      # binds manifest <-> COMPLETE marker (U9)
        "item": {"model": model_id, "freq": freq, "workload": workload},
        "source": {"chaos_commit": chaos_commit,
                   "gem5_commit": gem5_commit},
        "platform": {"isa": "ARM64", "mode": "SE",
                     "cpu_model": "ArmO3CPU", "config_family": "C3"},
        "workload": {"binary": w["binary"],
                     "binary_sha256": w["binary_sha256"],
                     "golden": w["golden"], "golden_id": w["golden_id"]},
        "trigger": {"mode": "cycle", "value": first_clock},
        "target": {"layer": d["layer"], "component": d["component"],
                   "instance": "-1", "index": -1,
                   "field": d["field"], "width_bits": d["width_bits"],
                   "sub_field": d["sub_field"]},
        "fault": {"model": d["fault_model"], "duration_events": 1,
                  "stage": "raw_pre_protection"},
        "rng": {"master_seed": seed, "selection_seed": seed},
        "limits": {"max_faults": 1},
    }


# ------------------------------------------------------------ gem5 launch

def _probe(argv, env=None, timeout=120):
    e = dict(os.environ)
    e.pop("PYTHONHOME", None)     # F-011: stale 3.11 PYTHONHOME breaks 3.9
    if env:
        e.update(env)
    try:
        return subprocess.run(argv, capture_output=True, env=e,
                              timeout=timeout).returncode
    except (OSError, subprocess.TimeoutExpired):
        return 126


def resolve_invocation(gem5_bin, compat_dir):
    """F-008/F-011 loader auto-detect. Native first (post-U1c norm: the
    rebuilt py3.9 binary runs with NO loader and NO PYTHONHOME), compat
    loader fallback. Probe is `--help` (gem5 v25 has no --version option;
    it exits 2 on it — empirically hit 2026-10-08). Returns (prefix_argv,
    env_extra); dies if both fail."""
    bin_abs = gem5_bin if os.path.isabs(gem5_bin) else os.path.join(
        REPO, gem5_bin)
    if not os.access(bin_abs, os.X_OK):
        _die("gem5 binary %s missing or not executable" % bin_abs)
    if _probe([bin_abs, "--help"]) == 0:
        _log("gem5 invocation: NATIVE %s" % bin_abs)
        return [bin_abs], {}
    ld = os.path.join(compat_dir, "lib", "ld-linux-aarch64.so.1")
    libpath = os.path.join(compat_dir, "lib64") + ":/usr/lib64"
    if os.access(ld, os.X_OK) and _probe(
            [ld, "--library-path", libpath, bin_abs, "--help"],
            env={"PYTHONHOME": compat_dir}) == 0:
        _log("gem5 invocation: COMPAT loader %s (PYTHONHOME=%s)"
             % (ld, compat_dir))
        return [ld, "--library-path", libpath, bin_abs], \
               {"PYTHONHOME": compat_dir}
    _die("neither native (%s --help, PYTHONHOME cleared) nor compat "
         "loader (%s) can run the gem5 binary — BLOCKED per F-008/F-011; "
         "see docs/gem5-fi/ooo/findings.md" % (bin_abs, ld))


def build_config_args(manifest, extra=()):
    """Mirror of runner.py's decode dispatch (tools/runner.py:1276): exactly
    the flags ooo_proxy.py mounts for CHAOSDecode."""
    d = MODEL_DISPATCH[manifest["item"]["model"]]
    w = WORKLOADS[manifest["item"]["workload"]]
    return [
        "--cmd", os.path.join(REPO, w["binary"]),
        "--cpu", "O3",
        "--chaos_decode",
        "--decode_mode", d["mode"],
        "--decode_first_clock", str(manifest["trigger"]["value"]),
        "--decode_max_faults", str(manifest["limits"]["max_faults"]),
        "--decode_rng_seed", str(manifest["rng"]["selection_seed"]),
    ] + list(extra)


def build_inner_script(prefix_argv, env_extra, outdir, config_args,
                       simout, simerr, exitrc):
    """bash -c payload: cd repo, set env, run gem5 with runner-convention
    redirects (gem5 itself only writes stats.txt/config.* — simout/simerr
    are the runner's redirect conventions), record exit.rc."""
    parts = ["cd %s" % shlex.quote(REPO)]
    if env_extra:
        for k in sorted(env_extra):
            parts.append("export %s=%s" % (k, shlex.quote(env_extra[k])))
    else:
        parts.append("unset PYTHONHOME")
    argv = [shlex.quote(a) for a in prefix_argv]
    argv.append("--outdir=" + shlex.quote(outdir))
    argv.append(shlex.quote(os.path.join(REPO, CONFIG_SE)))
    argv.extend(shlex.quote(a) for a in config_args)
    parts.append("%s > %s 2> %s" % (" ".join(argv), shlex.quote(simout),
                                    shlex.quote(simerr)))
    # ';' not '&&': a fault-induced abort (SIGABRT/SIGSEGV, exit 134/139)
    # must STILL record exit.rc — that rc is the evidence for the
    # Crash/SimulatorError verdict (empirically hit 2026-10-08: sample
    # seed 12845743019780264421 aborted and the && form ate the rc).
    parts.append("echo $? > %s" % shlex.quote(exitrc))
    return " && ".join(parts[:-1]) + "; " + parts[-1]


# ------------------------------------------------------------- heartbeat

class Heartbeat(threading.Thread):
    """Touches <sample_dir>/heartbeat every HEARTBEAT_INTERVAL s and appends
    resource.log — the file mtime is what ooo_recover reads (fresh ->
    RUNNING, stale -> INTERRUPTED); resource.log records loadavg + memory."""

    def __init__(self, sample_dir):
        super().__init__(daemon=True)
        self.dir = sample_dir
        self.stop_evt = threading.Event()

    def _beat(self):
        with open(os.path.join(self.dir, "heartbeat"), "w",
                  encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%dT%H:%M:%S") + "\n")
        load1 = ""
        try:
            load1 = open("/proc/loadavg").read().split()[0]
        except OSError:
            pass
        mem = ""
        try:
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemAvailable:"):
                        mem = line.split()[1]
                        break
        except OSError:
            pass
        with open(os.path.join(self.dir, "resource.log"), "a",
                  encoding="utf-8") as f:
            f.write(json.dumps({"t": time.strftime("%H:%M:%S"),
                                "load1": load1,
                                "mem_available_kb": mem}) + "\n")

    def run(self):
        while not self.stop_evt.wait(HEARTBEAT_INTERVAL):
            try:
                self._beat()
            except OSError:
                pass


# ------------------------------------------------------------- execution

def _guard_execute(desc, item, runid, log_path, inner_script, hang_timeout):
    """Wrap one gem5 run in ooo_guard run --type experiment (4-slot cap,
    U1b guard_pid race handling, heartbeat sampling, hang kill).

    Returns (guard_rc, target_ran). target_ran is positive evidence: the
    guard prints a '"action": "run-finish"' summary line on stdout when
    (and only when) it spawned and reaped the target. Gate/acquire
    refusals (GATE BLOCKED / ACQUIRE REFUSED, e.g. a stale slot left by a
    killed campaign) and guard crashes leave no run-finish — the sample
    did not run and must never be COMPLETE (defect (3), hit live
    2026-10-08: a stale-slot refusal was recorded as verdict=None
    rc=None l0=absent COMPLETE). Guard/target output is captured and
    replayed so the campaign log keeps SPAWNED / run-finish / refusal
    evidence."""
    guard_argv = [sys.executable, os.path.join(TOOLS, "ooo_guard.py"), "run",
                  "--type", "experiment", "--desc", desc,
                  "--item", item or "-", "--runid", runid or "-",
                  "--log", log_path,
                  "--max-seconds", str(hang_timeout),
                  "--", "bash", "-c", inner_script]
    _log("guard exec: %s ... bash -c <inner script (%d chars)>"
         % (" ".join(shlex.quote(a) for a in guard_argv[:14]),
            len(inner_script)))
    proc = subprocess.run(guard_argv, cwd=REPO, capture_output=True,
                          text=True, errors="replace")
    if proc.stdout:
        sys.stdout.write(proc.stdout)
        sys.stdout.flush()
    if proc.stderr:
        sys.stderr.write(proc.stderr)
        sys.stderr.flush()
    ran = '"action": "run-finish"' in (proc.stdout or "")
    return proc.returncode, ran


def _guard_timeout_evidence(stage_dir, elapsed):
    """Positive evidence the guard killed the run (vs a plain crash that
    never wrote exit.rc). No evidence -> rc stays an honest unknown."""
    glog = os.path.join(stage_dir, "guard.log")
    tail = ""
    try:
        with open(glog, "r", errors="replace") as f:
            tail = f.read()[-4000:]
    except OSError:
        pass
    if re.search(r"trip|max.?seconds|timeout|SIGTERM|SIGKILL", tail, re.I):
        return True
    return elapsed >= HANG_TIMEOUT


def run_one_sample(ctx, sample_index, execute_fn=None):
    """Full sample lifecycle. execute_fn(stage_dir, inner_script, ctx) is
    injectable so --selftest can drive the placement machinery with a fake
    gem5 (the real path goes through ooo_guard). Returns a result dict."""
    seed = sample_seed(ctx["run_id"], ctx["phase"], sample_index)
    run_key = make_run_key(ctx["campaign"], ctx["phase"], ctx["run_id"],
                           sample_index, seed, ctx["config_sha"])
    final_dir = os.path.join(ctx["run_root"], *run_key.split("/"))
    if os.path.exists(os.path.join(final_dir, COMPLETE_NAME)):
        return {"status": "skip-complete", "run_key": run_key}

    stage_root = os.path.join(ctx["staging_root"], str(os.getpid()))
    stage_dir = os.path.join(stage_root, *run_key.split("/"))
    if os.path.isdir(stage_dir):    # our own pid's earlier crashed attempt
        shutil.rmtree(stage_dir)
    os.makedirs(stage_dir)

    manifest = build_manifest(
        ctx["run_id"], run_key, ctx["model"], ctx["freq"], ctx["workload"],
        seed, ctx["first_clock"], ctx["chaos_commit"], ctx["gem5_commit"])
    with open(os.path.join(stage_dir, "manifest.json"), "w",
              encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    ok, errs = manifest_validate.validate(manifest)
    if not ok:
        _die("manifest validation failed for %s: %s"
             % (run_key, "; ".join(errs)))

    config_args = build_config_args(manifest, ctx.get("extra_args", ()))
    # --outdir IS the run dir (runner.py convention): injector logs land
    # beside simout/simerr where collect_l0 scans (m5out/ subdir would
    # hide them — empirically hit 2026-10-08, sample seed 6566880900823253577
    # read l0=absent with decode_injections.log sitting in m5out/).
    inner = build_inner_script(
        ctx["prefix"], ctx["env_extra"], stage_dir,
        config_args, os.path.join(stage_dir, "simout"),
        os.path.join(stage_dir, "simerr"), os.path.join(stage_dir, "exit.rc"))

    hb = Heartbeat(stage_dir)
    hb.start()
    t0 = time.time()
    try:
        if execute_fn is not None:
            # selftest injection; None keeps the legacy fake-run meaning
            target_ran = execute_fn(stage_dir, inner, ctx)
            if target_ran is None:
                target_ran = True
        else:
            _grc, target_ran = _guard_execute(
                run_key.replace("/", "_"), ctx["item"], ctx["run_id"],
                os.path.join(stage_dir, "guard.log"), inner,
                ctx["hang_timeout"])
    finally:
        hb.stop_evt.set()
        hb.join(timeout=10)
    if not target_ran:
        # Guard refused (GATE BLOCKED / ACQUIRE REFUSED, e.g. a stale
        # slot left by a killed campaign) or died before spawning the
        # target: the sample did NOT run. Marking it COMPLETE with
        # verdict=None would dress "never executed" as an honest unknown
        # (defect (3), hit live 2026-10-08). No observation, no COMPLETE,
        # no placement; staging stays for forensics (dead-pid cleanup on
        # the next start).
        return {"status": "blocked-guard", "run_key": run_key}
    elapsed = time.time() - t0

    rc = None
    exitrc_path = os.path.join(stage_dir, "exit.rc")
    if os.path.exists(exitrc_path):
        try:
            rc = int(open(exitrc_path).read().strip())
        except (OSError, ValueError):
            rc = None
    timed_out = rc is None and _guard_timeout_evidence(stage_dir, elapsed)
    obs = classify_ooo_run(stage_dir, golden=ctx["golden"],
                           timed_out=timed_out)
    obs["run_key"] = run_key
    obs["seed"] = seed
    obs["sample_index"] = sample_index
    obs["wall_seconds"] = round(elapsed, 1)
    obs["timed_out"] = timed_out
    with open(os.path.join(stage_dir, "observation.json"), "w",
              encoding="utf-8") as f:
        json.dump(obs, f, ensure_ascii=False, indent=1, sort_keys=True)

    verdict = (obs.get("L5") or {}).get("verdict")
    if os.path.isdir(final_dir):
        _log("REPLACING non-COMPLETE dir at %s (earlier interrupted attempt "
             "of the same deterministic seed)" % final_dir)
        shutil.rmtree(final_dir)
    os.makedirs(os.path.dirname(final_dir), exist_ok=True)
    os.rename(stage_dir, final_dir)          # same fs: atomic

    mark_complete(
        final_dir, run_key, rc, verdict or "Unknown",
        ["manifest.json", "observation.json", "simout", "simerr",
         "exit.rc" if rc is not None else "(exit.rc absent)",
         "guard.log" if os.path.exists(os.path.join(final_dir, "guard.log"))
         else "(no guard.log)",
         "l0_evidence=%s" % ((obs.get("L0") or {}).get("evidence"))],
        note="phase=%s seed=%d wall=%.0fs timed_out=%s"
             % (ctx["phase"], seed, elapsed, timed_out))
    _log("COMPLETE %s verdict=%s rc=%s l0=%s"
         % (run_key, verdict, rc, (obs.get("L0") or {}).get("evidence")))
    return {"status": "ran", "run_key": run_key, "verdict": verdict,
            "rc": rc, "seed": seed,
            "l0_evidence": (obs.get("L0") or {}).get("evidence")}


# -------------------------------------------------------------- baseline

def ensure_baseline(ctx):
    """No-injection golden gate before ANY fault sample: same binary, same
    config, zero injector flags; the FINAL checksum must equal the recorded
    golden. Lives outside run_root (nothing is injected -> no FI manifest).
    A mismatch is BLOCKED, never a warning."""
    w = WORKLOADS[ctx["workload"]]
    bdir = os.path.join(ctx["baseline_root"], ctx["campaign"], w["name"],
                        ctx["config_sha"][:12])
    marker = os.path.join(bdir, "baseline.json")
    if os.path.isfile(marker):
        try:
            with open(marker, "r", encoding="utf-8") as f:
                m = json.load(f)
            if (m.get("golden") == w["golden"] and m.get("golden_match")
                    and m.get("rc") == 0):
                _log("baseline reuse (golden verified): %s" % bdir)
                return bdir
            _log("baseline marker present but not a pass — re-running")
        except (OSError, ValueError):
            _log("baseline marker unreadable — re-running")
    os.makedirs(bdir, exist_ok=True)
    config_args = ["--cmd", os.path.join(REPO, w["binary"]), "--cpu", "O3"]
    inner = build_inner_script(
        ctx["prefix"], ctx["env_extra"], bdir,
        config_args, os.path.join(bdir, "simout"), os.path.join(bdir, "simerr"),
        os.path.join(bdir, "exit.rc"))
    _log("baseline run: %s" % bdir)
    _guard_execute("baseline-%s-%s" % (ctx["campaign"], w["name"]), "-",
                   ctx["run_id"], os.path.join(bdir, "guard.log"), inner,
                   ctx["hang_timeout"] * 3)
    rc = None
    if os.path.exists(os.path.join(bdir, "exit.rc")):
        try:
            rc = int(open(os.path.join(bdir, "exit.rc")).read().strip())
        except (OSError, ValueError):
            rc = None
    simout_txt = ""
    try:
        with open(os.path.join(bdir, "simout"), "r", errors="replace") as f:
            simout_txt = f.read()
    except OSError:
        pass
    checksum = extract_checksum(simout_txt)
    match = (rc == 0 and checksum == w["golden"])
    with open(marker, "w", encoding="utf-8") as f:
        json.dump({"campaign": ctx["campaign"], "workload": ctx["workload"],
                   "golden": w["golden"], "golden_id": w["golden_id"],
                   "checksum": checksum, "rc": rc, "golden_match": match,
                   "config_sha12": ctx["config_sha"][:12],
                   "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                time.gmtime())},
                  f, ensure_ascii=False, indent=1, sort_keys=True)
    if not match:
        _die("BASELINE GOLDEN MISMATCH for %s: rc=%s checksum=%s golden=%s "
             "(simout: %s) — fault samples would be uninterpretable; BLOCKED"
             % (w["name"], rc, checksum or "(none)", w["golden"],
                os.path.join(bdir, "simout")))
    _log("baseline PASS: checksum=%s == golden" % checksum)
    return bdir


# -------------------------------------------------------------- selftest

def _fake_execute_factory(final_hex, faults_injected, rc="0"):
    """Fake gem5 for --selftest: writes runner-convention outputs into the
    staging dir. faults_injected=None writes no injector log."""
    def fx(stage_dir, inner_script, ctx):
        with open(os.path.join(stage_dir, "simout"), "w") as f:
            f.write("fake simout for selftest\nFINAL=%s\n" % final_hex)
        with open(os.path.join(stage_dir, "simerr"), "w") as f:
            f.write("fake simerr for selftest\n")
        with open(os.path.join(stage_dir, "exit.rc"), "w") as f:
            f.write(rc + "\n")
        if faults_injected is not None:
            with open(os.path.join(stage_dir, "decode_injections.log"),
                      "w") as f:
                f.write("CHAOSDecode detail line, "
                        "faults_injected: %d\n" % faults_injected)
    return fx


def _selftest_ctx(tmp):
    return {
        "campaign": "selftest-camp", "phase": "engineering",
        "run_id": "D01-F0-W6", "item": "ITEM-002",
        "model": "D01", "freq": "F0", "workload": "W6",
        "golden": WORKLOADS["W6"]["golden"],
        "config_sha": "a" * 64,
        "chaos_commit": "deadbeef" * 5,
        "gem5_commit": "62c7bf284864b83f7308b5e14ca9c80812621c29",
        "first_clock": 1000, "hang_timeout": HANG_TIMEOUT,
        "prefix": ["/nonexistent-gem5-for-selftest"], "env_extra": {},
        "run_root": os.path.join(tmp, "runs-ooo"),
        "staging_root": os.path.join(tmp, "runs-staging"),
        "baseline_root": os.path.join(tmp, "runs-baseline"),
        "extra_args": (),
    }


def cmd_selftest(args):
    n = [0]
    fails = []

    def check(name, cond, detail=""):
        n[0] += 1
        print("  [%s] T%d %s%s" % ("PASS" if cond else "FAIL", n[0], name,
              (" — " + detail) if (detail and not cond) else ""))
        if not cond:
            fails.append(name)

    tmp = tempfile.mkdtemp(prefix="ooo-campaign-st-")
    try:
        ctx = _selftest_ctx(tmp)
        golden = ctx["golden"]

        # T1 seed formula — goal directive, hardcoded expected values.
        check("seed(D01-F0-W3,pilot,7)==1972644234533854552",
              sample_seed("D01-F0-W3", "pilot", 7) == 1972644234533854552,
              "got %d" % sample_seed("D01-F0-W3", "pilot", 7))
        check("seed(D01-F0-W6,engineering,0)==12845743019780264421",
              sample_seed("D01-F0-W6", "engineering", 0)
              == 12845743019780264421)
        check("seed(D01-F0-W6,engineering,1)==6566880900823253577",
              sample_seed("D01-F0-W6", "engineering", 1)
              == 6566880900823253577)

        # T2 run_key uniqueness (deterministic per (run_id,phase,i); config
        # drift must produce a DIFFERENT key).
        keys = set()
        for i in range(64):
            s = sample_seed("D01-F0-W6", "engineering", i)
            keys.add(make_run_key("c", "engineering", "D01-F0-W6", i, s,
                                  "b" * 64))
        check("64 distinct run_keys for 64 indices", len(keys) == 64)
        s0 = sample_seed("D01-F0-W6", "engineering", 0)
        k1 = make_run_key("c", "engineering", "D01-F0-W6", 0, s0, "b" * 64)
        k2 = make_run_key("c", "engineering", "D01-F0-W6", 0, s0, "c" * 64)
        check("config drift changes run_key", k1 != k2)
        check("run_key path shape",
              k1 == "c/engineering/D01-F0-W6/sample_000000_%016x_%s"
              % (s0, "b" * 12), k1)

        # T3 manifest build + real validator (manifest_validate.validate).
        man = build_manifest("D01-F0-W6", k1, "D01", "F0", "W6", s0, 1000,
                             "deadbeef" * 5,
                             "62c7bf284864b83f7308b5e14ca9c80812621c29")
        ok, errs = manifest_validate.validate(man)
        check("manifest validates (component=decode accepted)",
              ok, "; ".join(errs))
        check("manifest shape (sub_field/trigger/seed)",
              man["target"]["sub_field"] == "opcode_bitflip"
              and man["trigger"] == {"mode": "cycle", "value": 1000}
              and man["rng"]["selection_seed"] == s0)

        # T4 loud rejects (each must SystemExit(2), never a silent skip).
        def expect_die(fn, needle):
            try:
                fn()
            except SystemExit as e:
                return e.code == 2
            return False
        check("F1 tier loudly rejected",
              expect_die(lambda: check_dispatchable("D01", "F1", "W6"),
                         "F1"))
        check("unwired model (D02) loudly rejected",
              expect_die(lambda: check_dispatchable("D02", "F0", "W6"),
                         "D02"))
        check("unverified workload (W3) loudly rejected",
              expect_die(lambda: check_dispatchable("D01", "F0", "W3"),
                         "W3"))
        check("bogus item rejected",
              expect_die(lambda: resolve_item("ITEM-999"), "999"))

        # T6 full lifecycle with fake gem5: staging -> atomic placement ->
        # COMPLETE marker; legacy L0 evidence scanned; verdict Masked
        # (fault landed, checksum unchanged).
        r = run_one_sample(ctx, 0,
                           execute_fn=_fake_execute_factory(golden, 1))
        fdir = os.path.join(ctx["run_root"], *r["run_key"].split("/"))
        check("lifecycle status=ran", r["status"] == "ran", str(r))
        check("final dir placed with all evidence files",
              all(os.path.isfile(os.path.join(fdir, x)) for x in
                  ("manifest.json", "observation.json", "simout", "simerr",
                   "exit.rc", COMPLETE_NAME)))
        with open(os.path.join(fdir, COMPLETE_NAME)) as f:
            marker = json.load(f)
        check("COMPLETE marker binds run_key + verdict",
              marker["run_key"] == r["run_key"]
              and marker["classification"] == "Masked",
              json.dumps(marker))
        check("legacy L0 evidence recorded",
              r["l0_evidence"] == "legacy" or r["l0_evidence"] == "absent",
              str(r["l0_evidence"]))
        with open(os.path.join(fdir, "manifest.json")) as f:
            on_disk = json.load(f)
        check("manifest on disk is the validated one",
              on_disk.get("run_key") == r["run_key"]
              and on_disk.get("target", {}).get("component") == "decode")

        # T7 write-once: re-requesting the same sample skips; a hand-made
        # non-COMPLETE dir at the same key gets REPLACED (same seed).
        r2 = run_one_sample(ctx, 0,
                            execute_fn=_fake_execute_factory(golden, 1))
        check("second request for COMPLETE sample -> skip-complete",
              r2["status"] == "skip-complete", str(r2))
        os.remove(os.path.join(fdir, COMPLETE_NAME))
        r3 = run_one_sample(ctx, 0,
                            execute_fn=_fake_execute_factory(golden, 1))
        check("non-COMPLETE dir at same key replaced, status=ran",
              r3["status"] == "ran"
              and os.path.isfile(os.path.join(fdir, COMPLETE_NAME)),
              str(r3))
        check("mark_complete refuses overwrite of an existing marker",
              expect_die(lambda: mark_complete(
                  fdir, r["run_key"], 0, "Masked", ["evidence"]), "exists"))

        # T24 (U11 defect-3): guard refusal (no run-finish evidence —
        # execute_fn returns False) must NOT write observation/COMPLETE
        # or place the run dir: "never executed" is not an Unknown.
        r24 = run_one_sample(ctx, 5, execute_fn=lambda sd, inner, c: False)
        f24 = os.path.join(ctx["run_root"], *r24["run_key"].split("/"))
        check("guard refusal -> blocked-guard, no placement",
              r24.get("status") == "blocked-guard"
              and not os.path.exists(f24), str(r24))

        # T8 command builder — exact mirror of runner.py decode dispatch.
        ca = build_config_args(man)
        check("config args mirror runner decode dispatch",
              ca[ca.index("--chaos_decode") + 1] == "--decode_mode"
              and ca[ca.index("--decode_mode") + 1] == "opcode_bitflip"
              and ca[ca.index("--decode_rng_seed") + 1] == str(s0)
              and ca[ca.index("--decode_first_clock") + 1] == "1000"
              and ca[ca.index("--decode_max_faults") + 1] == "1",
              " ".join(ca))
        inner_native = build_inner_script(
            ["/fake/gem5.opt"], {}, "/tmp/m5out", ca, "/tmp/so", "/tmp/se",
            "/tmp/rc")
        check("inner script (native): redirects + rc + PYTHONHOME unset",
              "unset PYTHONHOME" in inner_native
              and "> /tmp/so 2> /tmp/se" in inner_native
              and "echo $? > /tmp/rc" in inner_native
              and "--chaos_decode" in inner_native, inner_native)
        inner_compat = build_inner_script(
            ["/c/lib/ld-linux-aarch64.so.1", "--library-path",
             "/c/lib64:/usr/lib64", "/fake/gem5.opt"],
            {"PYTHONHOME": "/c"}, "/tmp/m5out", ca, "/tmp/so", "/tmp/se",
            "/tmp/rc")
        check("inner script (compat): PYTHONHOME exported",
              "export PYTHONHOME=/c" in inner_compat
              and "unset PYTHONHOME" not in inner_compat, inner_compat)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("SELFTEST %s (%d checks, %d failed)"
          % ("PASS" if not fails else "FAIL", n[0], len(fails)))
    return 0 if not fails else 1


# ------------------------------------------------------------------ CLI

def _clean_stale_staging(staging_root):
    """Remove staging dirs owned by dead pids (crashed campaign attempts).
    A LIVE pid's dir is never touched (pid reuse risk -> keep, harmless)."""
    if not os.path.isdir(staging_root):
        return
    for name in sorted(os.listdir(staging_root)):
        path = os.path.join(staging_root, name)
        if not name.isdigit() or not os.path.isdir(path):
            continue
        try:
            os.kill(int(name), 0)
            alive = True
        except OSError:
            alive = False
        if not alive:
            _log("removing stale staging %s (owner pid dead)" % path)
            shutil.rmtree(path, ignore_errors=True)


def cmd_run(args):
    model_id, freq, wl = resolve_item(args.item)
    check_dispatchable(model_id, freq, wl)
    run_id = "%s-%s-%s" % (model_id, freq, wl)
    cfg_sha = config_sha256()
    gem5_bin = (args.gem5_bin or os.environ.get("OOO_GEM5_BIN")
                or DEFAULT_GEM5_BIN)
    compat_dir = (args.compat_dir or os.environ.get("OOO_COMPAT_DIR")
                  or DEFAULT_COMPAT_DIR)
    prefix, env_extra = resolve_invocation(gem5_bin, compat_dir)

    ctx = {
        "campaign": args.campaign, "phase": args.phase, "run_id": run_id,
        "item": args.item, "model": model_id, "freq": freq, "workload": wl,
        "golden": WORKLOADS[wl]["golden"], "config_sha": cfg_sha,
        "chaos_commit": _git_head(), "gem5_commit": _gem5_base_commit(),
        "first_clock": args.first_clock, "hang_timeout": args.hang_timeout,
        "prefix": prefix, "env_extra": env_extra,
        "run_root": args.run_root, "staging_root": args.staging_root,
        "baseline_root": args.baseline_root, "extra_args": (),
    }

    if args.sample_index is not None:
        indices = [args.sample_index]
    else:
        indices = list(range(args.samples))

    done, todo = [], []
    for i in sorted(indices):
        seed = sample_seed(run_id, args.phase, i)
        rk = make_run_key(args.campaign, args.phase, run_id, i, seed, cfg_sha)
        fin = os.path.join(args.run_root, *rk.split("/"))
        if os.path.exists(os.path.join(fin, COMPLETE_NAME)):
            done.append(rk)
        else:
            todo.append(i)
    if done and not args.resume:
        _die("refusing to touch COMPLETE samples (write-once): %s — pass "
             "--resume to skip them" % ", ".join(done))

    if args.dry_run:
        print("DRY-RUN %s item=%s phase=%s" % (args.campaign, args.item,
                                               args.phase))
        print("  gem5: %s%s" % (" ".join(prefix),
              (" (PYTHONHOME=%s)" % env_extra["PYTHONHOME"])
              if env_extra else " (native)"))
        print("  config_sha12=%s  COMPLETE-on-disk=%d  to-run=%d"
              % (cfg_sha[:12], len(done), len(todo)))
        for i in todo[:3]:
            s = sample_seed(run_id, args.phase, i)
            rk = make_run_key(args.campaign, args.phase, run_id, i, s, cfg_sha)
            print("  sample %d: seed=%d run_key=%s" % (i, s, rk))
        man = build_manifest(run_id, "dry-run", model_id, freq, wl,
                             sample_seed(run_id, args.phase, 0),
                             args.first_clock, "(dry-run)", "(dry-run)")
        print("  gem5 args: %s" % " ".join(build_config_args(man)))
        return 0

    _clean_stale_staging(ctx["staging_root"])
    ensure_baseline(ctx)

    results = []
    blocked = None
    for i in todo:
        r = run_one_sample(ctx, i)
        results.append(r)
        if r.get("status") == "blocked-guard":
            blocked = r
            break   # every later sample would hit the same refusal

    if blocked is not None:
        print("BLOCKED: guard did not run %s — gate/acquire refusal or "
              "guard failure (see GATE BLOCKED / ACQUIRE REFUSED above); "
              "no COMPLETE written. Stale slots: python3 tools/ooo_guard.py "
              "clear-stale, then re-run with --resume."
              % blocked["run_key"], file=sys.stderr)
        return 2

    verdicts = {}
    for r in results:
        v = r.get("verdict") or "Unknown"
        verdicts[v] = verdicts.get(v, 0) + 1
    print("CAMPAIGN SUMMARY %s %s %s: ran=%d skipped-complete=%d verdicts=%s"
          % (args.campaign, args.phase, run_id, len(results), len(done),
             json.dumps(verdicts, sort_keys=True)))
    print("  run_root=%s  (evidence: <run_root>/<run_key>/{manifest.json,"
          " observation.json, simout, simerr, exit.rc, guard.log,"
          " COMPLETE.json})" % args.run_root)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true",
                    help="fixture tests (no gem5, no real run_root)")
    ap.add_argument("--item", help="checklist item, e.g. ITEM-002")
    ap.add_argument("--phase", choices=PHASES)
    ap.add_argument("--samples", type=int, default=1,
                    help="sample count (indices 0..N-1)")
    ap.add_argument("--sample-index", type=int, default=None,
                    help="run a single sample index only (debug)")
    ap.add_argument("--resume", action="store_true",
                    help="skip COMPLETE samples instead of refusing")
    ap.add_argument("--campaign", default=DEFAULT_CAMPAIGN)
    ap.add_argument("--run-root", default=DEFAULT_RUN_ROOT)
    ap.add_argument("--staging-root", default=DEFAULT_STAGING_ROOT)
    ap.add_argument("--baseline-root", default=DEFAULT_BASELINE_ROOT)
    ap.add_argument("--gem5-bin", default=None,
                    help="default $OOO_GEM5_BIN or build/ARM/gem5.opt")
    ap.add_argument("--compat-dir", default=None,
                    help="default $OOO_COMPAT_DIR or lsu_keeper/compat")
    ap.add_argument("--first-clock", type=int, default=FIRST_CLOCK_DEFAULT)
    ap.add_argument("--hang-timeout", type=int, default=HANG_TIMEOUT)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return cmd_selftest(args)
    if not args.item or not args.phase:
        ap.error("--item and --phase are required (or --selftest)")
    return cmd_run(args)


if __name__ == "__main__":
    sys.exit(main())
