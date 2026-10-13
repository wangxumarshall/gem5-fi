#!/usr/bin/env python3
"""ooo_sample_runner.py -- one L0-L5 sample: staging -> gem5 -> offline
L1-L3 diffs -> observation.json -> atomic COMPLETE -> results.jsonl
(plan Task 6; task-book 2.4/2.6/3.1/3.4).

Consumes (never reimplements): tools/runner.py (the one manifest->gem5
mapper, with --ctrace/--msnap/--stats/--echo-checksum), campaign.
manifest_for_cell (the one manifest builder), tools/ooo_guard.py (host
slot + claim locks), tools/ooo_golden.py (one-shot cached baseline),
tools/micro_diff.py + tools/commit_diff.py + tools/fanout.py (the one
differs), tools/ooo_observation.py (the one observation assembler).

Exit codes: 0 done or COMPLETE-verified idempotent skip; 3 claim held
without COMPLETE (conflict); 4 no slot within 600s; 5 observation
violations -> QUARANTINE (COMPLETE is NEVER written for a violated
sample).

Honesty contract: a truncated (crashed-run) trace is salvaged by the
differs and the truncation is passed through; l2 becomes
not_observed_before_crash for a Crash/Hang with a clean prefix -- never
a fake no_divergence. [FIX-A Task 2] a Crash/Hang run with ZERO
readable trace lines (0 bytes: crash before the first commit flush) or
ZERO msnap data rows has NO observation possible: the differs are not
called, l2 is not_observed_before_crash with commit_diff=null and l1 is
no_snapshots_before_crash -- "no observation" is never dressed up as
"divergence observed" (the pre-fix commit_diff fabricated a seq-0
instruction_flow_change from every empty trace). L3 is unsupported
outside the PRF (gap L3). An inactive sample records L1-L4 as
inactive_no_activation.

Test hook: OOO_FAKE_RUNNER=1 skips gem5 and synthesizes a structurally
complete sample (classification from --rep) so the scheduler (B domain)
can dry-run -- production paths are unaffected.
"""

import argparse
import gzip
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.realpath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import ooo_guard  # noqa: E402
import campaign as campaign_mod  # noqa: E402
import ooo_golden  # noqa: E402
import ooo_observation  # noqa: E402
import runner as runner_mod  # noqa: E402

try:
    import yaml
except ImportError:
    sys.exit("ERROR: pip install pyyaml (needed for campaign yaml)")

DEFAULT_RUNS_ROOT = "/home/sdc/gem5-fi-ding/runs"
DEFAULT_GUARD_DIR = "/home/sdc/gem5-fi-ding/runs/ooo-l0l5/guard"
FROZEN_GEM5_SHA256 = ("1a618953b014514713c0ad98c7f3d69a48171d81f0463d9"
                      "34bccdfcfc0070bf3")

EXIT_CONFLICT = 3
EXIT_NO_SLOT = 4
EXIT_QUARANTINE = 5

CAMPAIGN_SCHEMA_VERSION = "arm-chaos-fi/l0l5-campaign/v1"

REQUIRED_CAMPAIGN_KEYS = ("schema_version", "campaign_id", "runid_row",
                          "submodel", "phase", "injector", "config", "mode",
                          "grid", "n_per_cell", "base_seed", "replay_pct",
                          "workload", "limits", "hang_timeout",
                          "chaos_commit", "patchset_sha256", "trace", "topup")


def sha256_file(path):
    return ooo_observation.sha256_file(path)


def load_campaign_yaml(path):
    with open(path) as f:
        camp = yaml.safe_load(f)
    if camp.get("schema_version") != CAMPAIGN_SCHEMA_VERSION:
        raise SystemExit("[sample-runner] campaign schema_version %r != %r"
                         % (camp.get("schema_version"),
                            CAMPAIGN_SCHEMA_VERSION))
    missing = [k for k in REQUIRED_CAMPAIGN_KEYS if k not in camp]
    if missing:
        raise SystemExit("[sample-runner] campaign yaml missing %s"
                         % missing)
    return camp


def check_identity():
    """The run freezes on ONE gem5 binary; drift is a blocking event."""
    sha = campaign_mod.gem5_sha256()
    if sha != FROZEN_GEM5_SHA256:
        raise SystemExit("[sample-runner] gem5.opt sha256 drift: %s... != "
                         "frozen %s... — refusing to run (identity guard)"
                         % (sha[:12], FROZEN_GEM5_SHA256[:12]))
    return sha


def campaign_dir_for(runs_root, campaign_id):
    return os.path.join(runs_root, campaign_id)


def build_manifest(camp, rep, topup_round, outdir):
    """One manifest via campaign.manifest_for_cell (single cell; the grid
    expands to one cell for this track's campaigns). Topup rounds override
    the seed to base+seed_offset+round*1000+rep (rep continues from 385)."""
    cells = campaign_mod.expand_grid(camp["grid"])
    if len(cells) != 1:
        raise SystemExit("[sample-runner] expected exactly 1 grid cell, "
                         "got %d (this runner is single-cell)" % len(cells))
    mpath, man = campaign_mod.manifest_for_cell(camp, cells[0], 0, rep,
                                                outdir)
    seed_note = None
    if topup_round:
        top = camp.get("topup") or dict()
        offset = int(top.get("seed_offset", 1000000))
        seed = int(camp["base_seed"]) + offset + int(topup_round) * 1000 \
            + rep
        man["rng"] = dict(master_seed=seed, selection_seed=seed)
        with open(mpath, "w") as f:
            yaml.safe_dump(man, f, sort_keys=False, default_flow_style=False)
        seed_note = "topup round %d: seed=%d (base+%d+%d*1000+%d)" % (
            topup_round, seed, offset, topup_round, rep)
    return mpath, man, seed_note


def _child_env(staging):
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = "0"  # forced (task-book 2.4)
    env["TMPDIR"] = os.path.join(staging, "tmp")
    os.makedirs(env["TMPDIR"], exist_ok=True)
    return env


def run_gem5_sample(manifest_path, binary, staging, hang_timeout,
                    msnap_every):
    """runner.py with L1/L2 observers, in its own process group so a
    timeout kills runner AND its gem5 child (campaign.run_one_rep's
    killpg lesson: a plain kill orphans the gem5 grandchild)."""
    runner = os.path.join(HERE, "runner.py")
    cmd = [sys.executable, runner, manifest_path,
           "--binary", binary,
           "--ctrace", os.path.join(staging, "ctrace.csv.gz"),
           "--msnap", os.path.join(staging, "msnap.csv.gz"),
           "--msnap-every", str(msnap_every),
           "--stats",
           "--echo-checksum"]
    env = _child_env(staging)
    t0 = time.time()
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         text=True, start_new_session=True, env=env)
    try:
        out, err = p.communicate(timeout=hang_timeout + 30)
        timed_out = False
    except subprocess.TimeoutExpired as e:
        try:
            os.killpg(os.getpgid(p.pid), signal.SIGKILL)
        except Exception:
            p.kill()
        p.wait()
        # preserve the PARTIAL output (the runner may already have printed
        # its RESULT line before the driver's budget kill -- found live on
        # eng2 D01-c rep0 where discarding it misclassified a fault-induced
        # hang as SimulatorError)
        def _to_str(x):
            if isinstance(x, bytes):
                return x.decode("utf-8", errors="replace")
            return x or ""
        out = _to_str(e.stdout)
        err = (_to_str(e.stderr) + "\nsample-runner: killed after %ss "
               "wall budget (process group SIGKILL)" % (hang_timeout + 30))
        timed_out = True
    return dict(rc=p.returncode, stdout=out or "", stderr=err or "",
                timed_out=timed_out, wall_s=time.time() - t0, cmd=cmd)


def find_man_dir(staging):
    tmpd = os.path.join(staging, "tmp")
    if not os.path.isdir(tmpd):
        return None
    for name in sorted(os.listdir(tmpd)):
        if name.startswith("man-"):
            return os.path.join(tmpd, name)
    return None


_CHECKSUM_RE = re.compile(r"^\[runner\] CHECKSUM: ([0-9a-f]{16}|none)$",
                          re.M)
_REASON_RE = re.compile(r"^\[runner\]\s+reason: (.*)$", re.M)


def parse_sample_result(res):
    parsed = campaign_mod.parse_runner_result(res["stdout"])
    m = _CHECKSUM_RE.search(res["stdout"])
    checksum = m.group(1) if m and m.group(1) != "none" else None
    r = _REASON_RE.search(res["stdout"])
    parsed["checksum_observed"] = checksum
    parsed["reason"] = r.group(1) if r else ""
    if parsed["classification"] is None and not res.get("timed_out"):
        # runner.py died before RESULT with NO timeout involved (tool
        # failure) -- honest SimulatorError. The timed_out case is resolved
        # by resolve_budget_kill() once the L0 injection log is parsed
        # (fault-landed budget kill = Hang/DUE, not a tool failure).
        parsed["classification"] = "SimulatorError"
    return parsed


def resolve_budget_kill(parsed, res, injected):
    """Classify a driver-budget kill with no runner RESULT line, using the
    L0 funnel (found live on eng2 D01-c rep0: decode fault on coremark
    hangs the workload; the 630s process-group kill used to fall through
    to a blanket SimulatorError, miscounting a DUE as a tool failure):
      fault landed (injected>=1)  -> Hang (timeout, no completion) / DUE
      no fault landed             -> SimulatorError (pre-activation infra
                                    failure; not a valid FI outcome)"""
    if parsed.get("classification") is not None or not res.get("timed_out"):
        return parsed
    if (injected or 0) >= 1:
        parsed["classification"] = "Hang"
        parsed["reason"] = ("exceeded wall budget with a fault landed and "
                            "no program completion (driver process-group "
                            "kill) -- control-flow corruption DUE")
        parsed["timed_out"] = True
        if parsed.get("exit") is None:
            parsed["exit"] = -9
    else:
        parsed["classification"] = "SimulatorError"
        parsed["reason"] = ("runner produced no RESULT within the wall "
                            "budget and no injection landed (pre-activation "
                            "infrastructure failure)")
    return parsed


def extract_evidence(staging, component):
    """Copy the injector log + stats.txt out of the man-* tempdir into
    staging/evidence/ (the tempdir itself is removed afterwards)."""
    ev = os.path.join(staging, "evidence")
    os.makedirs(ev, exist_ok=True)
    man_dir = find_man_dir(staging)
    copied = dict()
    if man_dir:
        log_name = ooo_observation.LOG_FOR_COMPONENT.get(component)
        if log_name:
            src = os.path.join(man_dir, log_name)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(ev, log_name))
                copied["log"] = os.path.join(ev, log_name)
        for fname in ("stats.txt", "config.ini", "config.json"):
            src = os.path.join(man_dir, fname)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(ev, fname))
                copied[fname] = os.path.join(ev, fname)
    return man_dir, copied


def run_tool_json(args, cwd=None):
    """Run a differ (micro_diff/commit_diff/fanout) as a subprocess with
    PYTHONHASHSEED=0; return (json_path_or_None, parsed_or_None)."""
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = "0"
    r = subprocess.run(args, capture_output=True, text=True, timeout=3600,
                       env=env, cwd=cwd)
    return r


def find_inj_seq(ctrace_path, l0_events):
    """Stream the run ctrace; the first line whose tick >= the L0
    injection tick gives the commit-seq anchor for the L2 window."""
    if not l0_events:
        return None
    tick0 = l0_events[0].get("tick")
    if tick0 is None:
        return None
    try:
        with gzip.open(ctrace_path, "rt", errors="replace") as f:
            for line in f:
                parts = line.split(",", 3)
                if len(parts) < 3:
                    continue
                try:
                    seq = int(parts[0])
                    tick = int(parts[2])
                except ValueError:
                    continue
                if tick >= tick0:
                    return seq
    except (OSError, EOFError):
        return None
    return None


def window_slice(ctrace_path, lo, hi, out_path):
    """Stream-filter seq in [lo, hi] into out_path; returns (full_lines,
    kept_lines, truncated). Truncated input streams (a Crash run's gz
    missing its trailer — found live on eng2 D01-c rep0, a mid-stream
    coremark crash with a NON-empty prefix) are sliced over their readable
    prefix instead of raising EOFError out of the driver (the differs
    already handle truncation honestly)."""
    full = kept = 0
    truncated = False
    with gzip.open(ctrace_path, "rt", errors="replace") as fin:
        with gzip.open(out_path, "wt") as fout:
            try:
                for line in fin:
                    full += 1
                    try:
                        seq = int(line.split(",", 1)[0])
                    except ValueError:
                        continue
                    if lo <= seq <= hi:
                        fout.write(line)
                        kept += 1
            except (OSError, EOFError):
                truncated = True
    return full, kept, truncated


def count_lines_salvage(path, comment=None):
    """[FIX-A Task 2] Truncation-salvage readable-line count: stream the
    file (gzip by magic bytes, else plain text), count non-blank lines --
    skipping lines starting with `comment` (msnap data rows exclude the
    '#' header) -- and on a truncated stream (EOFError/OSError mid-read:
    a crashed run's gzip without its trailer) keep the readable-prefix
    count and mark truncated=True instead of raising. A 0-byte file is 0
    lines (verified live: the crash-before-first-flush runs leave a
    0-byte ctrace, e.g. all 147 Crash samples of formal_D02-F0-W6-c).
    Returns (lines, truncated)."""
    n, trunc = 0, False
    try:
        with open(path, "rb") as f:
            magic = f.read(2)
        if magic == b"\x1f\x8b":
            fh = gzip.open(path, "rt", encoding="utf-8", errors="replace")
        else:
            fh = open(path, "rt", encoding="utf-8", errors="replace")
        with fh:
            try:
                for line in fh:
                    s = line.strip()
                    if not s or (comment and s.startswith(comment)):
                        continue
                    n += 1
            except (OSError, EOFError):
                trunc = True
    except (OSError, EOFError):
        trunc = True
    return n, trunc


def l1_block_for(msnap_path, golden_msnap, out_json, classification=None):
    """L1 block for one msnap pair (shared by the live do_l1 path and
    the offline reobserve path).

    [FIX-A Task 2] zero-data-row semantics: a Crash/Hang run whose msnap
    has ZERO data rows (the 116-byte header-only truncated gzip of a
    crash before the first snapshot flush) has NO observation to diff --
    micro_diff is NOT called (an empty-set "no_divergence" would
    over-claim) and the honest block is status=no_snapshots_before_crash
    with micro_diff=None. A non-Crash/Hang run with 0 data rows is an
    error (a completed run writes snapshots)."""
    if not os.path.exists(msnap_path):
        return dict(status="error",
                    reason="msnap missing (gem5 never wrote it)"), None
    rows, mtrunc = count_lines_salvage(msnap_path, comment="#")
    if rows == 0:
        if classification in ("Crash", "Hang"):
            return dict(status="no_snapshots_before_crash",
                        micro_diff=None, first_divergence=None,
                        files=dict(msnap_run="evidence/msnap.csv.gz"),
                        msnap_data_rows=0, msnap_truncated=mtrunc,
                        reason="run msnap 0 data rows - no snapshots "
                               "before crash"), None
        return dict(status="error",
                    reason="run msnap has 0 data rows but "
                           "classification=%s (a completed run writes "
                           "snapshots)" % classification,
                    micro_diff=None, first_divergence=None,
                    files=dict(msnap_run="evidence/msnap.csv.gz"),
                    msnap_data_rows=0, msnap_truncated=mtrunc), None
    r = run_tool_json([sys.executable, os.path.join(HERE, "micro_diff.py"),
                       "--ref", golden_msnap, "--run", msnap_path,
                       "--json", out_json])
    if r.returncode != 0 or not os.path.exists(out_json):
        return dict(status="error",
                    reason="micro_diff failed: %s" % r.stderr[-200:]), None
    with open(out_json) as f:
        md = json.load(f)
    if md.get("ref_truncated") or md.get("run_truncated"):
        status = "truncated"
    else:
        status = "ok"
    fd = None
    if not md.get("no_divergence"):
        fd = dict(snap_seq=md.get("rat_div_first_snap")
                  or md.get("occ_dev_first_snap")
                  or md.get("ipc_dev_first_snap"))
    blk = dict(status=status, micro_diff=md, first_divergence=fd,
               files=dict(msnap_run="evidence/msnap.csv.gz"),
               msnap_data_rows=rows, msnap_truncated=mtrunc)
    return blk, md


def do_l1(staging, golden_msnap, classification=None):
    """micro_diff on the staging msnap pair; honest statuses (the shared
    block builder is l1_block_for -- see its docstring for the
    [FIX-A Task 2] zero-data-row semantics)."""
    msnap = os.path.join(staging, "msnap.csv.gz")
    ev = os.path.join(staging, "evidence")
    os.makedirs(ev, exist_ok=True)
    return l1_block_for(msnap, golden_msnap,
                        os.path.join(ev, "micro_diff.json"), classification)


def do_l2(staging, golden_ctrace, mode, pre, post, classification,
          l0_events):
    """commit_diff full or window; the truncation semantics live in
    ooo_observation.l2_status_from.

    [FIX-A Task 2] zero-line semantics: the run ctrace's readable lines
    are counted FIRST (truncation-salvage counting; 0 bytes = 0 lines).
    With 0 lines there is NOTHING to diff -- commit_diff's merge would
    report every ref seq as one-sided and fabricate a seq-0
    instruction_flow_change (found live: all 147 Crash samples of
    formal_D02-F0-W6-c carried verdict=diverged with 3,000,001 fabricated
    divergence points from empty traces). The honest blocks instead:
      Crash/Hang -> not_observed_before_crash, commit_diff=null,
                    first_divergent_commit=null ("no observation
                    possible" is never dressed up as "divergence
                    observed")
      other class -> error (a completed run finalizes its trace)
    With >0 lines the diff runs as before (its own salvage stops inside
    the prefix, so first_divergent_commit can only be inside the
    prefix) and coverage records the observable range: readable prefix
    line count + truncation flag + byte size (+ window seq bounds)."""
    ctrace = os.path.join(staging, "ctrace.csv.gz")
    ev = os.path.join(staging, "evidence")
    os.makedirs(ev, exist_ok=True)
    out = os.path.join(ev, "commit_diff.json")
    if not os.path.exists(ctrace):
        blk = dict(status="error", reason="run ctrace missing",
                   coverage=dict(mode=mode, seq_lo=None, seq_hi=None,
                                 note="no run trace"),
                   commit_diff=None, first_divergent_commit=None,
                   files=dict())
        return blk, None, dict(mode=mode, seq_lo=None, seq_hi=None,
                               full_trace_lines=0, kept_lines=0,
                               run_trace_lines=0)
    lines, ttrunc = count_lines_salvage(ctrace)
    tbytes = os.path.getsize(ctrace)
    if lines == 0:
        if classification in ("Crash", "Hang"):
            blk = dict(
                status="not_observed_before_crash",
                coverage=dict(mode=mode, seq_lo=None, seq_hi=None,
                              note="run trace 0 lines - no observation "
                                   "possible",
                              run_trace_lines=0,
                              run_trace_truncated=ttrunc,
                              run_trace_bytes=tbytes),
                commit_diff=None, first_divergent_commit=None,
                files=dict())
        else:
            blk = dict(
                status="error",
                reason="run trace 0 lines but classification=%s (a "
                       "completed run finalizes its gzip; only a "
                       "Crash/Hang may die before the first flush)"
                       % classification,
                coverage=dict(mode=mode, seq_lo=None, seq_hi=None,
                              note="run trace 0 lines - no observation "
                                   "possible",
                              run_trace_lines=0,
                              run_trace_truncated=ttrunc,
                              run_trace_bytes=tbytes),
                commit_diff=None, first_divergent_commit=None,
                files=dict())
        return blk, None, dict(mode=mode, seq_lo=None, seq_hi=None,
                               full_trace_lines=0, kept_lines=0,
                               run_trace_lines=0)
    args = [sys.executable, os.path.join(HERE, "commit_diff.py"),
            "--ref", golden_ctrace, "--run", ctrace,
            "--json", out]
    lo = hi = None
    note = "full trace compared"
    if mode == "window":
        inj_seq = find_inj_seq(ctrace, l0_events)
        if inj_seq is None:
            lo, hi = 0, post
            note = ("injection seq not found in run trace (no L0 event "
                    "or no tick match); window anchored at seq 0")
        else:
            lo = max(0, inj_seq - pre)
            hi = inj_seq + post
            note = "window anchored at inj_seq=%d (pre=%d post=%d)" % (
                inj_seq, pre, post)
        args += ["--seq-range", "%d:%d" % (lo, hi)]
    r = run_tool_json(args)
    if r.returncode != 0 or not os.path.exists(out):
        blk = dict(status="error", reason="commit_diff failed: %s"
                   % r.stderr[-200:],
                   coverage=dict(mode=mode, seq_lo=lo, seq_hi=hi, note=note,
                                 run_trace_lines=lines,
                                 run_trace_truncated=ttrunc,
                                 run_trace_bytes=tbytes),
                   commit_diff=None, first_divergent_commit=None,
                   files=dict())
        return blk, None, dict(mode=mode, seq_lo=lo, seq_hi=hi,
                               full_trace_lines=0, kept_lines=0,
                               run_trace_lines=lines)
    cd = json.load(open(out))
    status = ooo_observation.l2_status_from(cd, classification)
    note_full = ("%s; observable range: %d readable run-trace lines%s"
                 % (note, lines,
                    " (truncated prefix - run trace lacked its gzip "
                     "trailer)" if ttrunc else ""))
    blk = dict(status=status,
               coverage=dict(mode=mode, seq_lo=lo, seq_hi=hi,
                             note=note_full,
                             run_trace_lines=lines,
                             run_trace_truncated=ttrunc,
                             run_trace_bytes=tbytes),
               commit_diff=cd,
               first_divergent_commit=cd.get("first_divergence"),
               files=dict(commit_diff="evidence/commit_diff.json"))
    return blk, cd, dict(mode=mode, seq_lo=lo, seq_hi=hi,
                         run_trace_lines=lines)


_PHYS_RE = re.compile(r"PhysReg\[(\d+)\]")


def do_l3(component, l0_block, retained_trace):
    """L3 fanout exists ONLY for the PRF (proxy + caveat); every other
    component is honestly unsupported (task-book 2.3)."""
    if component != "physreg":
        return dict(status="unsupported", method=None, fanout=None,
                    caveat=None,
                    reason="commit trace records dest regs only; "
                           "source-read/dynamic-instruction association "
                           "not implemented for %s; PRF liveness proxy "
                           "not applicable" % component)
    phys = None
    for ev in l0_block.get("events") or []:
        m = _PHYS_RE.search(ev.get("raw") or "")
        if m:
            phys = int(m.group(1))
            break
    if phys is None:
        return dict(status="unsupported", method=None, fanout=None,
                    caveat=None,
                    reason="physreg campaign but no PhysReg[N] id in the "
                           "L0 event log -- cannot anchor the fanout")
    out = os.path.join(os.path.dirname(retained_trace), "fanout.json")
    r = run_tool_json([sys.executable, os.path.join(HERE, "fanout.py"),
                       "--trace", retained_trace, "--phys", str(phys),
                       "--json", out])
    if r.returncode != 0 or not os.path.exists(out):
        return dict(status="error", method=None, fanout=None, caveat=None,
                    reason="fanout failed: %s" % r.stderr[-200:])
    fo = json.load(open(out))
    return dict(status="ok", method="proxy", fanout=fo,
                caveat=fo.get("caveat"), reason=None)


def retain_traces(staging, mode, cov, l2_blk):
    """Retention policy (task-book 2.6): full mode keeps the whole run
    ctrace; window mode keeps ONLY the window slice (the full run trace
    is deleted). The msnap is always kept in full. Returns the trace
    path L3 should use + the coverage_scope block."""
    ev = os.path.join(staging, "evidence")
    ctrace = os.path.join(staging, "ctrace.csv.gz")
    msnap = os.path.join(staging, "msnap.csv.gz")
    if os.path.exists(msnap):
        shutil.move(msnap, os.path.join(ev, "msnap.csv.gz"))
    full_lines = kept_lines = None
    if not os.path.exists(ctrace):
        scope = dict(mode=mode, seq_lo=cov.get("seq_lo"),
                     seq_hi=cov.get("seq_hi"), full_trace_lines=0,
                     kept_lines=0, run_trace_lines=0, pruned=False,
                     note="no run trace to retain")
        return None, scope
    if mode == "window":
        lo = cov.get("seq_lo") or 0
        hi = cov.get("seq_hi") or 0
        out = os.path.join(ev, "ctrace_window.csv.gz")
        full_lines, kept_lines, wtrunc = window_slice(ctrace, lo, hi, out)
        os.remove(ctrace)
        retained = out
        note = ("window retention: full run trace pruned; kept seq "
                "[%d,%d] (%d of %d lines)%s" % (lo, hi, kept_lines,
                                                 full_lines,
                                                 " [INPUT TRUNCATED: "
                                                 "run trace lacked its "
                                                 "gzip trailer (crash "
                                                 "mid-run); sliced over "
                                                 "the readable prefix]"
                                                 if wtrunc else ""))
        pruned = True
    else:
        out = os.path.join(ev, "ctrace.csv.gz")
        shutil.move(ctrace, out)
        retained = out
        note = "full retention: whole run ctrace kept"
        pruned = False
    # [FIX-A Task 2] the observable range carries do_l2's readable-line
    # count for BOTH modes (full mode has no window_slice count of its
    # own); seq_lo/seq_hi give the window bounds when windowed
    scope = dict(mode=mode, seq_lo=cov.get("seq_lo"),
                 seq_hi=cov.get("seq_hi"), full_trace_lines=full_lines,
                 kept_lines=kept_lines,
                 run_trace_lines=cov.get("run_trace_lines"),
                 pruned=pruned, note=note)
    return retained, scope


def build_identity(camp, man, rep, seed_note, manifest_path, gem5_sha,
                   golden_handle, started, finished, wall_s):
    cfg_key = camp.get("config", "C3")
    cfg_path = runner_mod.CONFIG_FAMILY.get(cfg_key)
    if cfg_path is None:
        raise SystemExit("[sample-runner] unknown config family %r"
                         % cfg_key)
    wl = camp["workload"]
    ident = dict(
        run_id=man["run_id"], campaign_id=camp["campaign_id"],
        runid_row=camp["runid_row"], submodel=camp["submodel"],
        sample_index=rep, phase=camp.get("phase", "formal"),
        seed=man["rng"]["selection_seed"],
        manifest_sha256=sha256_file(manifest_path),
        gem5_sha256=gem5_sha,
        config=dict(path=os.path.relpath(cfg_path, REPO),
                    sha256=sha256_file(cfg_path)),
        workload=dict(path=wl["binary"], sha256=wl.get("binary_sha256"),
                      golden_id=wl.get("golden_id")),
        golden_key=golden_handle["key"],
        chaos_commit=camp.get("chaos_commit", "HEAD"),
        patchset_sha256=camp.get("patchset_sha256", "n/a"),
        pythonhashseed=0,
        host=os.uname().nodename,
        started=started, finished=finished, wall_s=round(wall_s, 1))
    if seed_note:
        ident["seed_note"] = seed_note
    return ident


def hash_tree(root, exclude=None):
    """relpath -> sha256 for every file under root (evidence index).
    `exclude` is a set of root-relative paths to skip (used for
    observation.json: a file cannot contain its own sha256)."""
    excl = set(exclude or ())
    out = dict()
    for dirpath, _dirs, names in os.walk(root):
        for n in sorted(names):
            p = os.path.join(dirpath, n)
            rel = os.path.relpath(p, root)
            if rel in excl:
                continue
            out[rel] = sha256_file(p)
    return out


def write_json_atomic(path, obj):
    tmp = path + ".tmp.%d" % os.getpid()
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def append_results_jsonl(campaign_d, line):
    path = os.path.join(campaign_d, "results.jsonl")
    with open(path, "a") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def _verify_complete_readonly(final_dir):
    """Idempotent skip: the sample is COMPLETE on disk -- verify it
    read-only (observation parses, COMPLETE parses) and exit 0."""
    obs_p = os.path.join(final_dir, "observation.json")
    comp_p = os.path.join(final_dir, "COMPLETE.json")
    for p in (obs_p, comp_p):
        if not os.path.exists(p):
            return False
    try:
        json.load(open(obs_p))
        json.load(open(comp_p))
    except ValueError:
        return False
    return True


def _acquire_slot_blocking(guard_dir, campaign_id, run_id, max_slots,
                           budget_s=600.0):
    """slot_acquire with blocking retry (<=600s, every 2s). Returns the
    handle or None."""
    deadline = time.time() + budget_s
    while True:
        try:
            return ooo_guard.slot_acquire(guard_dir,
                                          "sample-runner:%d" % os.getpid(),
                                          campaign_id, run_id, max_slots)
        except ooo_guard.GuardError:
            if time.time() >= deadline:
                return None
            time.sleep(2)


def _golden_for(camp, campaign_yaml_path, gem5_sha, runs_root, guard_dir,
                hang_timeout):
    """Derive the golden spec FROM the campaign (no drift) and ensure it
    (cached; cross-binary reuse is refused inside ensure_golden)."""
    wl = camp["workload"]
    cfg_key = camp.get("config", "C3")
    cfg_path = runner_mod.CONFIG_FAMILY.get(cfg_key)
    spec = ooo_golden.spec_from_campaign(campaign_yaml_path, gem5_sha,
                                         sha256_file(cfg_path),
                                         wl.get("binary_sha256"))
    return ooo_golden.ensure_golden(spec, runs_root, guard_dir,
                                    hang_timeout=hang_timeout)


def _fake_res_and_blocks(staging, camp, man, rep, component, golden):
    """OOO_FAKE_RUNNER=1 test hook (B-domain scheduler dry runs): NO gem5,
    NO differs -- synthetic but STRUCTURALLY complete evidence. The
    classification is a pseudo value picked by --rep; nothing here is
    real measurement and production paths never call this."""
    cls = ["Masked", "Inactive", "Crash"][rep % 3]
    ev = os.path.join(staging, "evidence")
    os.makedirs(ev, exist_ok=True)
    log_name = ooo_observation.LOG_FOR_COMPONENT.get(component,
                                                     "decode_injections.log")
    activated = cls != "Inactive"
    with open(os.path.join(ev, log_name), "w") as f:
        if activated:
            f.write("Tick: 423115, Site: fetch_decode, mode=imm_bitflip, "
                    "pc=0x4195f0, orig_enc=0xf900dfe0, new_enc=0xf900dfe4,"
                    " bits=[2], faults_injected: 1\n")
        else:
            f.write("Tick: 423115, Site: fetch_decode, mode=imm_bitflip, "
                    "pc=0x4195f0, orig_mnemonic=ldr (skipped, no "
                    "injection), faults_injected: 0\n")
    lines = []
    for i in range(24):
        lines.append("%d,0,%d,4195f0,add,1,1,5,12,0000000000000000"
                     % (i, 1000 + i))
    with gzip.open(os.path.join(ev, "ctrace.csv.gz"), "wt") as f:
        f.write("\n".join(lines) + "\n")
    res = dict(rc=0, stdout="[runner] RESULT: run_id=%s classification=%s "
              "faults_injected=%d exit=0 timed_out=False oracle=exact_hash"
              "\n[runner]   reason: fake\n[runner] CHECKSUM: %s\n"
              % (man["run_id"], cls, 1 if activated else 0,
                 golden["final_checksum"] if cls != "SDC"
                 else "ffffffffffffffff"),
              stderr="", timed_out=False, wall_s=0.0, cmd=["FAKE"])
    return res


def _fake_blocks(cls, component, mode):
    activated = cls != "Inactive"
    if not activated:
        l1 = dict(status="inactive_no_activation", micro_diff=None,
                  first_divergence=None, files=dict())
        l2 = dict(status="inactive_no_activation",
                  coverage=dict(mode=mode, seq_lo=None, seq_hi=None,
                                note="fake inactive"),
                  commit_diff=None, first_divergent_commit=None,
                  files=dict())
        l3 = dict(status="inactive_no_activation")
        l4 = dict(status="inactive_no_activation",
                  first_detection=dict(kind=None, detector="n/a",
                                       tick=None, seq=None, note="fake"),
                  latency_from_l0=dict(ticks=None, committed_insts=None,
                                       note="fake"),
                  oracle=dict(kind="exact_hash", golden=None, observed=None,
                              match=None))
    else:
        l1 = dict(status="ok", micro_diff=dict(fake=True),
                  first_divergence=None, files=dict())
        cd = dict(verdict="no_divergence", run_truncated=False,
                  first_divergence=None, fake=True)
        l2 = dict(status="ok" if cls != "Crash"
                  else "not_observed_before_crash",
                  coverage=dict(mode=mode, seq_lo=0, seq_hi=23,
                                note="fake"),
                  commit_diff=cd, first_divergent_commit=None,
                  files=dict())
        l3 = (dict(status="ok", method="proxy", fanout=dict(fake=True),
                   caveat="fake proxy caveat")
              if component == "physreg" else
              dict(status="unsupported", reason="fake: %s has no L3"
                   % component))
        l4 = dict(status="none_detected" if cls == "Masked" else "ok",
                  first_detection=dict(kind=None, detector=None, tick=None,
                                       seq=None, note="fake"),
                  latency_from_l0=dict(ticks=None, committed_insts=None,
                                       note="fake"),
                  oracle=dict(kind="exact_hash", golden=None, observed=None,
                              match=None))
    return l1, l2, l3, l4


def cmd_run(args):
    camp = load_campaign_yaml(args.campaign_yaml)
    gem5_sha = check_identity()
    trace_cfg = camp["trace"]
    mode = trace_cfg.get("l2_mode", "full")
    pre = int(trace_cfg.get("window_pre_seq", 10000))
    post = int(trace_cfg.get("window_post_seq", 3000000))
    msnap_every = int(trace_cfg.get("msnap_every", 1000))
    hang_timeout = int(camp["hang_timeout"])
    max_slots = int(os.environ.get("OOO_MAX_SLOTS", "8"))
    fake = os.environ.get("OOO_FAKE_RUNNER") == "1"

    run_id = "%s-c0000-r%04d" % (camp["campaign_id"], args.rep)
    cdir = campaign_dir_for(args.runs_root, camp["campaign_id"])
    final_dir = os.path.join(cdir, "samples", run_id)
    claim_key = "%s__%s" % (camp["campaign_id"], run_id)

    # idempotent skip FIRST (read-only, no claim touched): a published
    # COMPLETE sample is never re-run, never re-appended
    if _verify_complete_readonly(final_dir):
        print("[sample-runner] %s: COMPLETE verified read-only -- "
              "idempotent skip" % run_id)
        return 0
    if not ooo_guard.claim_acquire(args.guard_dir, claim_key):
        print("[sample-runner] %s: claim held WITHOUT COMPLETE -- conflict"
              % run_id)
        return EXIT_CONFLICT

    staging = os.path.join(cdir, "samples", ".staging",
                           "%s.p%d" % (run_id, os.getpid()))
    if os.path.isdir(staging):
        shutil.rmtree(staging)
    os.makedirs(staging)
    started = time.strftime("%Y-%m-%dT%H:%M:%S")
    t0 = time.time()
    try:
        mpath, man, seed_note = build_manifest(
            camp, args.rep, args.topup_round,
            os.path.join(staging, "manifests"))
        component = man["target"]["component"]
        binary = os.path.join(REPO, camp["workload"]["binary"])
        golden = _golden_for(camp, args.campaign_yaml, gem5_sha,
                             args.runs_root, args.guard_dir, hang_timeout)

        if fake:
            res = _fake_res_and_blocks(staging, camp, man, args.rep,
                                       component, golden)
        else:
            slot = _acquire_slot_blocking(args.guard_dir,
                                          camp["campaign_id"], run_id,
                                          max_slots)
            if slot is None:
                print("[sample-runner] %s: no slot within 600s" % run_id)
                return EXIT_NO_SLOT
            try:
                res = run_gem5_sample(mpath, binary, staging, hang_timeout,
                                      msnap_every)
            finally:
                # the slot guards GEM5; post-processing runs un-slotted
                ooo_guard.slot_release(slot)
        with open(os.path.join(staging, "runner.stdout"), "w") as f:
            f.write(res["stdout"])
        with open(os.path.join(staging, "runner.stderr"), "w") as f:
            f.write(res["stderr"])
        parsed = parse_sample_result(res)
        classification = parsed["classification"]

        if fake:
            l0 = ooo_observation.l0_block_from(
                os.path.join(staging, "evidence"), component)
            l1_blk, l2_blk, l3_blk, l4_blk = _fake_blocks(
                classification, component, mode)
            cd = l2_blk.get("commit_diff")
            cov = dict(mode=mode, seq_lo=l2_blk["coverage"]["seq_lo"],
                       seq_hi=l2_blk["coverage"]["seq_hi"])
            retained = os.path.join(staging, "evidence", "ctrace.csv.gz")
            coverage_scope = dict(mode=mode, seq_lo=cov["seq_lo"],
                                  seq_hi=cov["seq_hi"], full_trace_lines=24,
                                  kept_lines=24, pruned=False,
                                  note="fake runner: synthetic sample")
        else:
            man_dir, _copied = extract_evidence(staging, component)
            if man_dir:
                shutil.rmtree(man_dir, ignore_errors=True)
            l0 = ooo_observation.l0_block_from(
                os.path.join(staging, "evidence"), component)
            # budget-kill resolution needs the L0 funnel (fault landed?)
            parsed = resolve_budget_kill(parsed, res, l0.get("injected"))
            classification = parsed["classification"]
            activated = 1 if (l0["injected"] or 0) >= 1 else 0
            if activated:
                l1_blk, _md = do_l1(staging, golden["msnap_path"],
                                    classification)
                l2_blk, cd, cov = do_l2(
                    staging, golden["ctrace_path"], mode, pre, post,
                    classification, l0["events"])
            else:
                l1_blk = dict(status="inactive_no_activation",
                              micro_diff=None, first_divergence=None,
                              files=dict(),
                              reason="no injection landed -- L1 not "
                                     "attempted (n/a, honest)")
                l2_blk = dict(status="inactive_no_activation",
                              coverage=dict(mode=mode, seq_lo=None,
                                            seq_hi=None,
                                            note="no injection landed -- "
                                                 "L2 not attempted"),
                              commit_diff=None,
                              first_divergent_commit=None, files=dict())
                cd = None
                cov = dict(mode=mode, seq_lo=None, seq_hi=None)
            retained, coverage_scope = retain_traces(staging, mode, cov,
                                                     l2_blk)
            if not activated:
                l3_blk = dict(status="inactive_no_activation", method=None,
                              fanout=None, caveat=None,
                              reason="no injection landed -- L3 not "
                                     "attempted (n/a, honest)")
            elif retained:
                l3_blk = do_l3(component, l0, retained)
            else:
                l3_blk = dict(status="error", method=None, fanout=None,
                              caveat=None,
                              reason="no retained run trace for L3")

        # ---- L4 (first detection + latency from the L0 anchor) --------
        first_detection = ooo_observation.first_detection_for(
            classification, cd)
        latency = dict(ticks=None, committed_insts=None, note="")
        if (l0.get("events") and isinstance(cd, dict)
                and cd.get("first_divergence")):
            div = cd["first_divergence"]
            tick0 = l0["events"][0].get("tick")
            # RUN-side tick only (one-sided divergences have no run line;
            # the ref-side tick would fabricate a negative latency)
            dtick = ooo_observation.tick_from_ctrace_raw(
                div.get("run_line"))
            if dtick is not None and tick0 is not None:
                latency["ticks"] = dtick - tick0
            if retained:
                inj_seq = find_inj_seq(retained, l0["events"])
                if inj_seq is not None and div.get("seq") is not None:
                    latency["committed_insts"] = div["seq"] - inj_seq
        if (l0.get("injected") or 0) >= 1 or fake:
            if classification in ("SimulatorError", "Inactive"):
                l4_status = "ok" if (l0.get("injected") or 0) >= 1 \
                    else "inactive_no_activation"
            elif classification == "Masked":
                l4_status = "none_detected"
            else:
                l4_status = "ok"
            if not fake and (l0.get("injected") or 0) == 0:
                l4_status = "inactive_no_activation"
        else:
            l4_status = "inactive_no_activation"
        l4_blk = dict(status=l4_status, first_detection=first_detection,
                      latency_from_l0=latency,
                      oracle=dict(kind="exact_hash",
                                  golden=golden["final_checksum"],
                                  observed=parsed["checksum_observed"],
                                  match=(parsed["checksum_observed"]
                                         == golden["final_checksum"]
                                         if parsed["checksum_observed"]
                                         else None)))

        # ---- L5 + identity + assembly ---------------------------------
        faults = parsed["faults_injected"]
        if faults is None:
            faults = l0.get("injected", 0)
        l5_blk = dict(classification=classification,
                      reason=parsed.get("reason", ""),
                      exit=parsed["exit"], timed_out=parsed["timed_out"],
                      faults_injected=faults,
                      checksum_observed=parsed["checksum_observed"],
                      checksum_golden=golden["final_checksum"],
                      detector=None, conservation=None)
        finished = time.strftime("%Y-%m-%dT%H:%M:%S")
        ident = build_identity(camp, man, args.rep, seed_note, mpath,
                               gem5_sha, golden, started, finished,
                               time.time() - t0)
        replay_cfg = dict(campaign_yaml=os.path.abspath(args.campaign_yaml),
                          hang_timeout=hang_timeout,
                          msnap_every=msnap_every, l2_mode=mode,
                          window_pre_seq=pre, window_post_seq=post,
                          binary=binary, component=component,
                          golden_dir=golden["dir"],
                          golden_ctrace=golden["ctrace_path"],
                          golden_msnap=golden["msnap_path"],
                          golden_final=golden["final_checksum"])
        write_json_atomic(os.path.join(staging, "evidence",
                                       "replay_config.json"), replay_cfg)
        ctx = dict(identity=ident, l0=l0, l1=l1_blk, l2=l2_blk, l3=l3_blk,
                   l4=l4_blk, l5=l5_blk, files=dict(),
                   coverage_scope=coverage_scope)
        obs = ooo_observation.build_observation(ctx)
        if obs["violations"]:
            qdir = os.path.join(cdir, "QUARANTINE")
            os.makedirs(qdir, exist_ok=True)
            dst = os.path.join(qdir, "%s.%d" % (run_id, int(time.time())))
            write_json_atomic(os.path.join(staging, "observation.json"),
                              obs)
            os.rename(staging, dst)
            print("[sample-runner] %s: VIOLATIONS %s -> QUARANTINE %s"
                  % (run_id, obs["violations"], dst))
            return EXIT_QUARANTINE

        # ---- atomic publish -------------------------------------------
        if os.path.exists(final_dir):
            raise SystemExit("[sample-runner] %s: final dir already exists "
                             "without a claim -- refusing to overwrite %s"
                             % (run_id, final_dir))
        write_json_atomic(os.path.join(staging, "observation.json"), obs)
        os.rename(staging, final_dir)
        # files-manifest BACKFILL: hash every file in the published dir
        # EXCEPT observation.json itself (a file cannot contain its own
        # sha256 -- the exclusion is deliberate and auditable), then
        # atomically rewrite observation.json carrying the manifest, and
        # only then write COMPLETE.json whose observation_sha256 is the
        # sha of the FINAL backfilled observation. The 0-byte ctrace of
        # a crash-before-first-flush sample is kept and listed -- it IS
        # the honest evidence of where the crash happened.
        obs_p = os.path.join(final_dir, "observation.json")
        files = hash_tree(final_dir, exclude=("observation.json",))
        obs["files"] = files
        write_json_atomic(obs_p, obs)
        write_json_atomic(os.path.join(final_dir, "COMPLETE.json"),
                          dict(run_id=run_id,
                               gem5_sha256=gem5_sha,
                               observation_sha256=sha256_file(obs_p),
                               files=files,
                               completed=time.strftime(
                                   "%Y-%m-%dT%H:%M:%S")))
        append_results_jsonl(cdir, dict(
            manifest="samples/%s/manifests/%s.yaml" % (run_id, run_id),
            run_id=run_id, rep=args.rep, seed=man["rng"]["selection_seed"],
            classification=obs["l5"]["classification"],
            faults_injected=obs["l5"]["faults_injected"],
            exit=obs["l5"]["exit"], timed_out=obs["l5"]["timed_out"],
            chain_complete=obs["chain_complete"],
            chain_gaps=obs["chain_gaps"],
            observation="samples/%s/observation.json" % run_id,
            ts=time.strftime("%Y-%m-%dT%H:%M:%S")))
        print("[sample-runner] %s: COMPLETE classification=%s "
              "chain_complete=%s gaps=%s wall=%.1fs"
              % (run_id, obs["l5"]["classification"],
                 obs["chain_complete"], obs["chain_gaps"],
                 time.time() - t0))
        return 0
    finally:
        ooo_guard.claim_release(args.guard_dir, claim_key)


def cmd_replay(args):
    """Same manifest, same seed, independent staging (no claim, no
    sample slot consumed, no results.jsonl). Compares classification +
    commit_diff verdict + checksum, then atomically rewrites the
    observation's top-level replay block."""
    sample_dir = os.path.realpath(args.sample_dir)
    obs_p = os.path.join(sample_dir, "observation.json")
    if not os.path.exists(obs_p):
        raise SystemExit("[replay] no observation.json in %s" % sample_dir)
    obs = json.load(open(obs_p))
    ident = obs["identity"]
    run_id = ident["run_id"]
    campaign_id = ident["campaign_id"]
    manifest = os.path.join(sample_dir, "manifests", "%s.yaml" % run_id)
    if not os.path.exists(manifest):
        raise SystemExit("[replay] manifest copy missing: %s" % manifest)
    rcfg_p = os.path.join(sample_dir, "evidence", "replay_config.json")
    if not os.path.exists(rcfg_p):
        raise SystemExit("[replay] replay_config.json missing (pre-contract"
                         " sample?)")
    rcfg = json.load(open(rcfg_p))
    check_identity()
    cdir = campaign_dir_for(args.runs_root, campaign_id)
    staging = os.path.join(cdir, "samples", ".staging",
                           "replay-%s.p%d" % (run_id, os.getpid()))
    if os.path.isdir(staging):
        shutil.rmtree(staging)
    os.makedirs(staging)
    max_slots = int(os.environ.get("OOO_MAX_SLOTS", "8"))
    slot = _acquire_slot_blocking(args.guard_dir, campaign_id,
                                  "replay:%s" % run_id, max_slots)
    if slot is None:
        raise SystemExit("[replay] no slot within 600s")
    try:
        res = run_gem5_sample(manifest, rcfg["binary"], staging,
                              int(rcfg["hang_timeout"]),
                              int(rcfg["msnap_every"]))
    finally:
        ooo_guard.slot_release(slot)
    parsed = parse_sample_result(res)
    # budget-kill resolution mirrors pass 1 (same funnel, same L0 evidence)
    parsed = resolve_budget_kill(
        parsed, res, (obs.get("l0") or {}).get("injected"))
    # L2 pass2 with the SAME window policy (the same seed reproduces the
    # same injection point, so the anchor is identical) — and the same
    # INACTIVE policy as pass 1: when the original observation ran no L2
    # diff (l2.commit_diff is None, e.g. inactive_no_activation), pass 2
    # must not produce a comparable verdict either. Found live on the
    # E2E normal-class sample: pass1 verdict None vs pass2
    # no_divergence was a category-error MISMATCH, not a determinism
    # failure (integration fix 2026-10-12).
    if isinstance(obs.get("l2", dict).get("commit_diff"), dict):
        _l2_blk, cd, _cov = do_l2(staging, rcfg["golden_ctrace"],
                                  rcfg["l2_mode"],
                                  int(rcfg["window_pre_seq"]),
                                  int(rcfg["window_post_seq"]),
                                  parsed["classification"], [])
    else:
        cd = None  # pass-1 ran no diff: mirror the policy, compare nothing
    p2_cls = parsed["classification"]
    p2_verdict = cd.get("verdict") if isinstance(cd, dict) else None
    p2_checksum = parsed["checksum_observed"]
    prev_verdict = None
    if isinstance(obs.get("l2", dict()).get("commit_diff"), dict):
        prev_verdict = obs["l2"]["commit_diff"].get("verdict")
    mism = []
    if p2_cls != obs["l5"]["classification"]:
        mism.append("classification %s->%s" % (obs["l5"]["classification"],
                                                p2_cls))
    if p2_verdict != prev_verdict:
        mism.append("verdict %s->%s" % (prev_verdict, p2_verdict))
    if p2_checksum != obs["l5"]["checksum_observed"]:
        mism.append("checksum %s->%s" % (obs["l5"]["checksum_observed"],
                                          p2_checksum))
    determinism = "match" if not mism else "MISMATCH(%s)" % ";".join(mism)
    # keep pass2 evidence next to the sample
    rdir = os.path.join(sample_dir, "evidence", "replay")
    os.makedirs(rdir, exist_ok=True)
    with open(os.path.join(rdir, "runner.stdout"), "w") as f:
        f.write(res["stdout"])
    if os.path.exists(os.path.join(staging, "evidence",
                                   "commit_diff.json")):
        shutil.copy2(os.path.join(staging, "evidence", "commit_diff.json"),
                     os.path.join(rdir, "commit_diff.json"))
    shutil.rmtree(staging, ignore_errors=True)
    obs["replay"] = dict(performed=True, pass2_classification=p2_cls,
                         determinism=determinism, verdict_pass2=p2_verdict,
                         checksum_pass2=p2_checksum,
                         performed_at=time.strftime("%Y-%m-%dT%H:%M:%S"))
    write_json_atomic(obs_p, obs)
    # replay legitimately MUTATES observation.json (that is its purpose);
    # refresh COMPLETE.json's sha pin so the invariant
    # "COMPLETE.observation_sha256 == sha(current observation.json)"
    # holds for verifiers at ALL times, before and after replay
    comp_p = os.path.join(sample_dir, "COMPLETE.json")
    if os.path.exists(comp_p):
        comp = json.load(open(comp_p))
        comp["observation_sha256"] = sha256_file(obs_p)
        comp["replay_refreshed"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        write_json_atomic(comp_p, comp)
    print("[replay] %s: %s" % (run_id, determinism))
    return 0 if determinism == "match" else 1


def reobserve_sample(sample_dir):
    """[FIX-A Task 3] Offline re-derivation of a published sample's
    observation view from RETAINED EVIDENCE ONLY -- no gem5, no guard
    slot, no claim, no results.jsonl. Returns the revised observation
    dict in memory; NEVER writes or overwrites anything (the caller may
    publish it as observation.revised.json).

    Reuses the fix-A semantics: Task 1 (real L0 funnel from the retained
    injector log) and Task 2 (zero-line Crash/Hang L1/L2 -- no fabricated
    divergence). Evidence consumed:
      evidence/<injector log>          -> l0 (real attempted/eligible)
      runner.stdout                    -> classification/checksum re-parse
      evidence/msnap.csv.gz            -> l1 (0 data rows + Crash/Hang =
                                          no_snapshots_before_crash;
                                          >0 rows -> micro_diff re-run)
      evidence/ctrace_window.csv.gz (window) / evidence/ctrace.csv.gz
        (full)                         -> l2 line count; 0 lines +
                                          Crash/Hang = not_observed_
                                          before_crash with commit_diff
                                          null (the pre-fix commit_diff.
                                          json verdict was fabricated
                                          from an empty trace and is
                                          DISCARDED)
      evidence/commit_diff.json        -> window mode with >0 lines: the
                                          RETAINED diff is reused verbatim
                                          -- the window slice is a
                                          re-sliced CLEAN gzip, so re-
                                          running commit_diff on it would
                                          count the ref tail as one-sided
                                          divergences for a truncated-
                                          prefix sample (the exact
                                          fabrication Task 2 fixes).
                                          Full mode keeps the whole run
                                          trace (truncation state
                                          preserved) and re-runs
                                          commit_diff against the golden.
      evidence/replay_config.json      -> component, l2 mode, golden
                                          paths (required; a pre-contract
                                          sample without it is a loud
                                          refusal, not a guess)
      observation.json                 -> identity / l3 / replay /
                                          checksum_golden passthrough (l3
                                          fanout re-derivation is outside
                                          fix-A scope; the pass1 block is
                                          evidence-frozen and passed
                                          through)
    """
    sample_dir = os.path.realpath(sample_dir)
    obs_p = os.path.join(sample_dir, "observation.json")
    if not os.path.exists(obs_p):
        raise SystemExit("[reobserve] no observation.json in %s"
                         % sample_dir)
    with open(obs_p) as f:
        old = json.load(f)
    old_sha = sha256_file(obs_p)
    ev = os.path.join(sample_dir, "evidence")
    rcfg_p = os.path.join(ev, "replay_config.json")
    if not os.path.exists(rcfg_p):
        raise SystemExit("[reobserve] evidence/replay_config.json missing "
                         "in %s (pre-contract sample: the golden paths and "
                         "L2 mode needed for offline re-derivation are not "
                         "recoverable) -- refusing to guess" % sample_dir)
    with open(rcfg_p) as f:
        rcfg = json.load(f)
    notes = []
    component = rcfg.get("component") or (old.get("l0") or {}).get(
        "component")
    mode = rcfg.get("l2_mode", "full")
    old_l5 = old.get("l5") or dict()
    old_l2 = old.get("l2") or dict()

    # ---- L0: real funnel from the retained injector log (Task 1) ----
    l0 = ooo_observation.l0_block_from(ev, component)

    # ---- classification: re-parse the retained runner stdout ----
    stdout = ""
    so_p = os.path.join(sample_dir, "runner.stdout")
    if os.path.exists(so_p):
        with open(so_p, "r", errors="replace") as f:
            stdout = f.read()
    res = dict(rc=old_l5.get("exit"), stdout=stdout, stderr="",
               timed_out=bool(old_l5.get("timed_out")))
    parsed = parse_sample_result(res)
    parsed = resolve_budget_kill(parsed, res, l0.get("injected"))
    classification = parsed.get("classification")
    if classification is None:
        classification = old_l5.get("classification")
        notes.append("classification not re-derivable from runner.stdout; "
                     "pass1 value %r kept" % classification)
    elif old_l5.get("classification") != classification:
        notes.append("re-derived classification %r != pass1 %r"
                     % (classification, old_l5.get("classification")))

    activated = 1 if (l0.get("injected") or 0) >= 1 else 0
    retained = None
    scope_lines = None
    if not activated:
        l1_blk = dict(status="inactive_no_activation", micro_diff=None,
                      first_divergence=None, files=dict(),
                      reason="no injection landed -- L1 not attempted "
                             "(n/a, honest)")
        l2_blk = dict(status="inactive_no_activation",
                      coverage=dict(mode=mode, seq_lo=None, seq_hi=None,
                                    note="no injection landed -- L2 not "
                                         "attempted"),
                      commit_diff=None, first_divergent_commit=None,
                      files=dict())
        cd = None
    else:
        # ---- L1 (Task 2 semantics; msnap is retained in full) ----
        with tempfile.TemporaryDirectory(prefix="reobs-l1-") as tdir:
            l1_blk, _md = l1_block_for(
                os.path.join(ev, "msnap.csv.gz"), rcfg["golden_msnap"],
                os.path.join(tdir, "micro_diff.json"), classification)
        # ---- L2 ----
        trace_name = ("ctrace_window.csv.gz" if mode == "window"
                      else "ctrace.csv.gz")
        trace_path = os.path.join(ev, trace_name)
        old_cov = old_l2.get("coverage") or dict()
        seq_lo, seq_hi = old_cov.get("seq_lo"), old_cov.get("seq_hi")
        cd = None
        if not os.path.exists(trace_path):
            l2_blk = dict(status="error",
                          reason="retained run trace missing (%s)"
                                 % trace_name,
                          coverage=dict(mode=mode, seq_lo=seq_lo,
                                        seq_hi=seq_hi,
                                        note="no retained run trace"),
                          commit_diff=None, first_divergent_commit=None,
                          files=dict())
        else:
            retained = trace_path
            lines, ttrunc = count_lines_salvage(trace_path)
            tbytes = os.path.getsize(trace_path)
            scope_lines = lines
            cov = dict(mode=mode, seq_lo=seq_lo, seq_hi=seq_hi,
                       run_trace_lines=lines, run_trace_truncated=ttrunc,
                       run_trace_bytes=tbytes)
            if lines == 0:
                cov["note"] = ("run trace 0 lines - no observation "
                               "possible")
                if classification in ("Crash", "Hang"):
                    l2_blk = dict(status="not_observed_before_crash",
                                  coverage=cov, commit_diff=None,
                                  first_divergent_commit=None, files=dict())
                else:
                    l2_blk = dict(
                        status="error",
                        reason="run trace 0 lines but classification=%s "
                               "(a completed run finalizes its gzip; only "
                               "a Crash/Hang may die before the first "
                               "flush)" % classification,
                        coverage=cov, commit_diff=None,
                        first_divergent_commit=None, files=dict())
            elif mode == "window":
                # >0 lines: reuse the retained honest full-trace windowed
                # diff (see docstring for why re-running on the re-sliced
                # window would fabricate one-sided divergences)
                cd_p = os.path.join(ev, "commit_diff.json")
                if not os.path.exists(cd_p):
                    l2_blk = dict(
                        status="error",
                        reason="window-mode sample without retained "
                               "commit_diff.json -- cannot re-derive L2 "
                               "offline (the window slice alone cannot "
                               "reproduce the truncation semantics)",
                        coverage=dict(cov,
                                      note="no retained commit_diff.json"),
                        commit_diff=None, first_divergent_commit=None,
                        files=dict())
                else:
                    with open(cd_p) as f:
                        cd = json.load(f)
                    status = ooo_observation.l2_status_from(cd,
                                                            classification)
                    l2_blk = dict(
                        status=status,
                        coverage=dict(
                            cov, note="reobserved from the retained "
                                      "commit_diff.json (the honest "
                                      "full-trace windowed diff); "
                                      "observable range: %d readable "
                                      "window lines" % lines),
                        commit_diff=cd,
                        first_divergent_commit=cd.get("first_divergence"),
                        files=dict(commit_diff="evidence/commit_diff.json"))
            else:
                # full mode: the whole run trace is retained with its
                # truncation state -- re-run commit_diff honestly
                with tempfile.TemporaryDirectory(prefix="reobs-l2-") as tdir:
                    out = os.path.join(tdir, "commit_diff.json")
                    r = run_tool_json(
                        [sys.executable, os.path.join(HERE, "commit_diff.py"),
                         "--ref", rcfg["golden_ctrace"], "--run", trace_path,
                         "--json", out])
                    if r.returncode == 0 and os.path.exists(out):
                        with open(out) as f:
                            cd = json.load(f)
                if cd is None:
                    l2_blk = dict(
                        status="error",
                        reason="commit_diff re-run failed on the retained "
                               "full trace",
                        coverage=dict(cov, note="commit_diff re-run failed"),
                        commit_diff=None, first_divergent_commit=None,
                        files=dict())
                else:
                    status = ooo_observation.l2_status_from(cd,
                                                            classification)
                    l2_blk = dict(
                        status=status,
                        coverage=dict(
                            cov, note="reobserved: commit_diff re-run on "
                                      "the retained full trace; observable "
                                      "range: %d readable lines%s"
                                      % (lines, " (truncated prefix)"
                                         if ttrunc else "")),
                        commit_diff=cd,
                        first_divergent_commit=cd.get("first_divergence"),
                        files=dict(commit_diff=None))

    # ---- L3: pass1 block passthrough (fanout re-derivation is outside
    # fix-A scope; the block is evidence-frozen) ----
    l3_blk = old.get("l3") or dict(status="error",
                                   reason="pass1 l3 block missing")

    # ---- L4: mirror cmd_run's derivation over the new cd ----
    first_detection = ooo_observation.first_detection_for(classification, cd)
    latency = dict(ticks=None, committed_insts=None, note="")
    if (l0.get("events") and isinstance(cd, dict)
            and cd.get("first_divergence")):
        div = cd["first_divergence"]
        tick0 = l0["events"][0].get("tick")
        dtick = ooo_observation.tick_from_ctrace_raw(div.get("run_line"))
        if dtick is not None and tick0 is not None:
            latency["ticks"] = dtick - tick0
        if retained:
            inj_seq = find_inj_seq(retained, l0["events"])
            if inj_seq is not None and div.get("seq") is not None:
                latency["committed_insts"] = div["seq"] - inj_seq
    if not activated:
        l4_status = "inactive_no_activation"
    elif classification in ("SimulatorError", "Inactive"):
        l4_status = "ok"
    elif classification == "Masked":
        l4_status = "none_detected"
    else:
        l4_status = "ok"
    l4_blk = dict(status=l4_status, first_detection=first_detection,
                  latency_from_l0=latency,
                  oracle=dict(kind="exact_hash",
                              golden=rcfg.get("golden_final"),
                              observed=parsed.get("checksum_observed"),
                              match=(parsed.get("checksum_observed")
                                     == rcfg.get("golden_final")
                                     if parsed.get("checksum_observed")
                                     else None)))

    # ---- L5: rebuilt; conservation recomputed by build_observation ----
    faults = parsed.get("faults_injected")
    if faults is None:
        faults = l0.get("injected", 0)
    l5_blk = dict(classification=classification,
                  reason=parsed.get("reason", ""),
                  exit=parsed.get("exit"), timed_out=parsed.get("timed_out"),
                  faults_injected=faults,
                  checksum_observed=parsed.get("checksum_observed"),
                  checksum_golden=old_l5.get("checksum_golden")
                  or rcfg.get("golden_final"),
                  detector=None, conservation=None)

    # ---- coverage_scope / files / audit ----
    scope = dict(old.get("coverage_scope") or dict(mode=mode))
    scope["run_trace_lines"] = scope_lines
    scope["reobserve_note"] = ("reobserved offline from retained "
                               "evidence (fix-A); run_trace_lines is the "
                               "retained trace's readable-line count")
    files = hash_tree(sample_dir, exclude=("observation.json",
                                           "observation.revised.json"))
    audit = dict(old.get("audit") or {})
    audit["reobserved_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    audit["reobserve_builder_sha256"] = sha256_file(__file__)

    ctx = dict(identity=old.get("identity") or dict(), l0=l0, l1=l1_blk,
               l2=l2_blk, l3=l3_blk, l4=l4_blk, l5=l5_blk, files=files,
               coverage_scope=scope, audit=audit,
               replay=old.get("replay"))
    revised = ooo_observation.build_observation(ctx)
    revised["reobserve"] = dict(
        performed=True,
        reobserved_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
        semantics="fix-A: Task1 real L0 funnel + Task2 zero-line "
                  "Crash/Hang L1/L2 (no fabricated divergence)",
        based_on_observation_sha256=old_sha,
        classification_pass1=old_l5.get("classification"),
        l0_attempted_pass1=(old.get("l0") or {}).get("attempted"),
        l0_eligible_pass1=(old.get("l0") or {}).get("eligible"),
        l2_status_pass1=old_l2.get("status"),
        l2_verdict_pass1=(old_l2.get("commit_diff") or dict()).get("verdict")
        if isinstance(old_l2.get("commit_diff"), dict) else None,
        notes=notes)
    return revised


def cmd_reobserve(args):
    """reobserve CLI: re-derive the revised view, optionally write it as
    observation.revised.json (NEVER observation.json), print the pass1
    -> pass2 delta summary. Exit 0 clean; 5 when the revised view still
    carries violations (mirrors the quarantine convention -- the caller
    decides what to do; nothing is quarantined here)."""
    sample_dir = os.path.realpath(args.sample_dir)
    rev = reobserve_sample(sample_dir)
    ro = rev["reobserve"]
    print("[reobserve] %s:" % (rev.get("identity") or {}).get("run_id",
                                                              sample_dir))
    print("[reobserve]   l0 funnel: attempted %r -> %r, eligible %r -> %r, "
          "injected %r" % (ro["l0_attempted_pass1"], rev["l0"]["attempted"],
                           ro["l0_eligible_pass1"], rev["l0"]["eligible"],
                           rev["l0"]["injected"]))
    print("[reobserve]   l1: %r -> %r" % (
        "n/a", rev["l1"]["status"]))
    print("[reobserve]   l2: %r (verdict %r) -> %r (commit_diff %s)" % (
        ro["l2_status_pass1"], ro["l2_verdict_pass1"], rev["l2"]["status"],
        "null" if rev["l2"]["commit_diff"] is None else "dict"))
    print("[reobserve]   chain: gaps %s, violations %d"
          % (rev["chain_gaps"], len(rev["violations"])))
    for n in ro["notes"]:
        print("[reobserve]   note: %s" % n)
    if args.no_write:
        print("[reobserve]   --no-write: revised view kept in memory only")
    else:
        rev_p = os.path.join(sample_dir, "observation.revised.json")
        write_json_atomic(rev_p, rev)
        print("[reobserve]   wrote %s (observation.json untouched)"
              % rev_p)
    return 0 if not rev["violations"] else EXIT_QUARANTINE


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="ooo_sample_runner.py",
        description="One L0-L5 sample: staging -> gem5 -> offline diffs "
                    "-> observation.json -> atomic COMPLETE.")
    ap.add_argument("cmd", choices=["run", "replay", "reobserve"])
    ap.add_argument("--campaign-yaml", default=None,
                    help="run: the l0l5 campaign yaml")
    ap.add_argument("--rep", type=int, default=0,
                    help="run: rep index (>=385 continues the topup "
                         "numbering)")
    ap.add_argument("--topup-round", type=int, default=0,
                    help="run: topup round (seed block base+1e6+round*1000"
                         "+rep)")
    ap.add_argument("--guard-dir", default=DEFAULT_GUARD_DIR)
    ap.add_argument("--runs-root", default=DEFAULT_RUNS_ROOT)
    ap.add_argument("--sample-dir", default=None,
                    help="replay/reobserve: the published sample directory")
    ap.add_argument("--no-write", action="store_true",
                    help="reobserve: keep the revised view in memory only "
                         "(do not write observation.revised.json)")
    args = ap.parse_args(argv)
    if args.cmd == "run":
        if not args.campaign_yaml:
            ap.error("run requires --campaign-yaml")
        return cmd_run(args)
    if args.cmd == "reobserve":
        if not args.sample_dir:
            ap.error("reobserve requires --sample-dir")
        return cmd_reobserve(args)
    if not args.sample_dir:
        ap.error("replay requires --sample-dir")
    return cmd_replay(args)


if __name__ == "__main__":
    sys.exit(main())
