#!/usr/bin/env python3
"""[OOO][P1] ooo_sample_runner end-to-end test (plan Task 6; REAL smoke
gem5 runs, ~40 s total).

FIXTURE DISCLOSURE (honesty): the crash seed (base 20261012) was given by
the task book as a known Crash; the Masked seed (base 20261013) was
picked by a pre-test probe of 5 seeds (20261013..20261017 -> 4x Masked,
1 Hang). Both are TEST FIXTURES chosen to exercise the pipeline's
per-classification semantics -- they are NOT statistical samples and no
outcome rate is claimed from them.

Cases: (1) crash sample full chain; (2) idempotent COMPLETE re-run;
(3) replay determinism; (4) Masked sample (full L2 mode + full
retention); (5) OOO_FAKE_RUNNER test hook; (6) no staging residue;
(7) [FIX-A Task 2] OFFLINE do_l1/do_l2 zero-line Crash semantics
(fixtures only, no gem5): a 0-line run ctrace / 0-data-row msnap on a
Crash/Hang run is "no observation possible" -- the differs are NOT
called and no divergence is fabricated.

[FIX-A] TOOLS is derived from THIS file's location so the test always
exercises the worktree it lives in (the old hardcoded
worktrees/ooo-l0l5-a path silently tested another session's code).
Run: python3 tools/tests/test_ooo_sample_runner.py
"""
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.realpath(__file__))
TOOLS = os.path.dirname(HERE)   # this worktree's tools/ dir
RUNS = "/home/sdc/gem5-fi-ding/runs"
SELFTEST = os.path.join(RUNS, "ooo-l0l5", "selftest", "sample-runner")
CRASH_YAML = os.path.join(SELFTEST, "selftest_crash.yaml")
MASKED_YAML = os.path.join(SELFTEST, "selftest_masked.yaml")
sys.path.insert(0, TOOLS)

FAILURES = []
CHECKS = []


def check(name, cond, detail=""):
    CHECKS.append(name)
    if cond:
        print(f"  PASS {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILURES.append(name)


def run_sr(args, env_extra=None):
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = "0"
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, os.path.join(TOOLS, "ooo_sample_runner.py")]
        + args, capture_output=True, text=True, timeout=900, env=env)


def fresh(campaign_id):
    d = os.path.join(RUNS, campaign_id)
    if os.path.isdir(d):
        shutil.rmtree(d)


def sample_dir(campaign_id, rep=0):
    return os.path.join(RUNS, campaign_id, "samples",
                        "%s-c0000-r%04d" % (campaign_id, rep))


def test_crash_sample():
    fresh("selftest-ooo-crash")
    t0 = time.time()
    r = run_sr(["run", "--campaign-yaml", CRASH_YAML, "--rep", "0"])
    check("crash-run-rc0", r.returncode == 0, r.stdout[-300:] + r.stderr[-300:])
    d = sample_dir("selftest-ooo-crash")
    check("crash-final-dir", os.path.isdir(d))
    check("crash-complete-json",
          os.path.exists(os.path.join(d, "COMPLETE.json")))
    obs = json.load(open(os.path.join(d, "observation.json")))
    check("crash-l0-injected-1", obs["l0"]["injected"] == 1, obs["l0"])
    check("crash-l0-log", obs["l0"]["log_name"] == "decode_injections.log")
    # [FIX-A Task 2] Crash semantics for a run that died before ANY
    # commit was flushed (the CTRACE line says lines=0 bytes=0, the msnap
    # has 0 data rows): NO observation was possible, so the differs are
    # NOT run and NO divergence is fabricated. The old behavior (call
    # commit_diff on the empty trace -> "diverged", first divergence
    # seq=0 instruction_flow_change, 3,000,001 fabricated points on the
    # formal campaigns) masqueraded "no observation" as "divergence
    # observed" and is superseded by the central fix-A mandate.
    check("crash-l1-no-snapshots",
          obs["l1"]["status"] == "no_snapshots_before_crash",
          obs["l1"]["status"])
    check("crash-l1-micro-diff-null",
          obs["l1"]["micro_diff"] is None, obs["l1"].get("micro_diff"))
    check("crash-l2-status",
          obs["l2"]["status"] == "not_observed_before_crash",
          obs["l2"]["status"])
    check("crash-l2-commit-diff-null",
          obs["l2"]["commit_diff"] is None,
          obs["l2"].get("commit_diff"))
    check("crash-l2-fdc-null",
          obs["l2"]["first_divergent_commit"] is None,
          obs["l2"].get("first_divergent_commit"))
    check("crash-l2-zero-line-note",
          "run trace 0 lines" in obs["l2"]["coverage"]["note"],
          obs["l2"]["coverage"]["note"])
    check("crash-l4-first-detection-no-fabricated-seq",
          obs["l4"]["first_detection"]["seq"] is None,
          obs["l4"]["first_detection"])
    check("crash-l3-unsupported", obs["l3"]["status"] == "unsupported")
    check("crash-l0-activated", obs["l0"]["activated"] == 1, obs["l0"])
    check("crash-l3-null-keys",
          obs["l3"]["method"] is None and obs["l3"]["fanout"] is None
          and obs["l3"]["caveat"] is None and bool(obs["l3"]["reason"]),
          obs["l3"])
    ccons = obs["l5"]["conservation"]
    check("crash-conservation-schema",
          ccons["ok"] is True and ccons["five_primary_sum"] == 1
          and ccons["activated"] == obs["l0"]["activated"], ccons)
    check("crash-chain-false", obs["chain_complete"] is False)
    # [FIX-A Task 2] the two zero-observation statuses are honest (NOT
    # violations) but are absence-of-observation: they cost gaps L1/L2
    # on top of the L3 rule
    check("crash-gaps-l1-l2-l3", obs["chain_gaps"] == ["L1", "L2", "L3"],
          obs["chain_gaps"])
    check("crash-l5", obs["l5"]["classification"] == "Crash"
          and obs["l5"]["exit"] == -6
          and obs["l5"]["checksum_observed"] is None, obs["l5"])
    check("crash-detector-os", obs["l5"]["detector"] == "OS")
    check("crash-conservation", obs["l5"]["conservation"]["conserved"]
          is True)
    check("crash-violations-empty", obs["violations"] == [])
    # results.jsonl: exactly one line with the full record
    rl = os.path.join(RUNS, "selftest-ooo-crash", "results.jsonl")
    lines = [json.loads(x) for x in open(rl) if x.strip()]
    check("crash-results-one-line", len(lines) == 1, len(lines))
    check("crash-results-fields",
          lines[0]["run_id"] == "selftest-ooo-crash-c0000-r0000"
          and lines[0]["classification"] == "Crash"
          and lines[0]["seed"] == 20261012
          and lines[0]["chain_gaps"] == ["L1", "L2", "L3"], lines[0])
    # files BACKFILL (contract fix 4): observation.files lists the
    # evidence (incl. the kept 0-line ctrace window of this
    # crash-before-first-flush sample); observation.json itself excluded
    fkeys = obs["files"]
    check("crash-files-backfilled", len(fkeys) >= 5, sorted(fkeys))
    check("crash-files-ctrace-window",
          "evidence/ctrace_window.csv.gz" in fkeys, sorted(fkeys))
    check("crash-files-msnap", "evidence/msnap.csv.gz" in fkeys)
    check("crash-files-exclude-self", "observation.json" not in fkeys)
    # files sha256 spot-check (3 files) against the disk
    comp = json.load(open(os.path.join(d, "COMPLETE.json")))
    obs_sha = hashlib.sha256(
        open(os.path.join(d, "observation.json"), "rb").read()).hexdigest()
    check("crash-complete-sha-final-obs",
          comp["observation_sha256"] == obs_sha,
          (comp["observation_sha256"], obs_sha))
    names = sorted(comp["files"])
    picked = [n for n in names if n.endswith(".json")][:2] + \
             [n for n in names if n.endswith(".log")][:1]
    ok3 = True
    for n in picked:
        h = hashlib.sha256()
        with open(os.path.join(d, n), "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        if h.hexdigest() != comp["files"][n]:
            ok3 = False
    check("crash-files-sha-spotcheck", ok3 and len(picked) == 3, picked)
    print("  [info] crash sample wall=%.1fs" % (time.time() - t0))


def test_idempotent_rerun():
    d = sample_dir("selftest-ooo-crash")
    obs_p = os.path.join(d, "observation.json")
    before = os.stat(obs_p).st_mtime_ns
    rl = os.path.join(RUNS, "selftest-ooo-crash", "results.jsonl")
    n_before = sum(1 for _ in open(rl))
    r = run_sr(["run", "--campaign-yaml", CRASH_YAML, "--rep", "0"])
    check("idem-rc0", r.returncode == 0, r.stdout[-200:])
    check("idem-skip-message", "idempotent skip" in r.stdout, r.stdout[-200:])
    check("idem-mtime-unchanged",
          os.stat(obs_p).st_mtime_ns == before)
    check("idem-no-new-line",
          sum(1 for _ in open(rl)) == n_before == 1)


def test_masked_sample():
    # FIXTURE (see module docstring): base 20261013 probes as Masked.
    # This campaign uses l2_mode=full -> whole-run diff + full retention.
    fresh("selftest-ooo-masked")
    r = run_sr(["run", "--campaign-yaml", MASKED_YAML, "--rep", "0"])
    check("masked-run-rc0", r.returncode == 0, r.stdout[-300:])
    d = sample_dir("selftest-ooo-masked")
    obs = json.load(open(os.path.join(d, "observation.json")))
    check("masked-l5", obs["l5"]["classification"] == "Masked", obs["l5"])
    check("masked-checksum-matches-golden",
          obs["l5"]["checksum_observed"] == "45737cc9a76c0dce"
          == obs["l5"]["checksum_golden"], obs["l5"]["checksum_observed"])
    check("masked-l0-injected", obs["l0"]["injected"] == 1)
    check("masked-l1-ok", obs["l1"]["status"] == "ok")
    check("masked-l2-ok", obs["l2"]["status"] == "ok")
    check("masked-l2-full-mode", obs["l2"]["coverage"]["mode"] == "full")
    check("masked-l4-none-detected", obs["l4"]["status"] == "none_detected")
    check("masked-detector-none", obs["l5"]["detector"] is None)
    check("masked-chain-gap-l3", obs["chain_gaps"] == ["L3"]
          and obs["chain_complete"] is False, obs["chain_gaps"])
    check("masked-violations-empty", obs["violations"] == [])
    check("masked-full-retention",
          obs["coverage_scope"]["pruned"] is False
          and os.path.exists(os.path.join(d, "evidence", "ctrace.csv.gz")))
    check("masked-l0-activated", obs["l0"]["activated"] == 1)
    check("masked-files-backfilled",
          "evidence/ctrace.csv.gz" in obs["files"]
          and "evidence/msnap.csv.gz" in obs["files"], sorted(obs["files"]))
    check("masked-conservation-ok-key",
          obs["l5"]["conservation"]["ok"] is True
          and obs["l5"]["conservation"]["five_primary_sum"] == 1)
    check("masked-replay-default",
          obs["replay"]["performed"] is False
          and obs["replay"]["determinism"] is None)


def test_replay():
    for cid in ("selftest-ooo-crash", "selftest-ooo-masked"):
        d = sample_dir(cid)
        r = run_sr(["replay", "--sample-dir", d])
        check("replay-%s-rc0" % cid, r.returncode == 0,
              r.stdout[-300:] + r.stderr[-300:])
        obs = json.load(open(os.path.join(d, "observation.json")))
        check("replay-%s-match" % cid,
              obs["replay"]["determinism"] == "match"
              and obs["replay"]["performed"] is True, obs["replay"])
        check("replay-%s-fields" % cid,
              obs["replay"]["pass2_classification"] is not None
              and obs["replay"]["performed_at"] is not None)
        check("replay-%s-evidence" % cid,
              os.path.exists(os.path.join(d, "evidence", "replay",
                                          "runner.stdout")))
        # the replay must NOT append to results.jsonl
        rl = os.path.join(RUNS, cid, "results.jsonl")
        check("replay-%s-no-jsonl" % cid, sum(1 for _ in open(rl)) == 1)
        # post-replay invariant: COMPLETE's sha pin follows the mutated
        # observation.json (refreshed by the replay itself)
        comp = json.load(open(os.path.join(d, "COMPLETE.json")))
        cur_sha = hashlib.sha256(
            open(os.path.join(d, "observation.json"), "rb").read()
        ).hexdigest()
        check("replay-%s-sha-pin-refreshed" % cid,
              comp["observation_sha256"] == cur_sha,
              (comp["observation_sha256"], cur_sha))


def test_fake_runner_hook():
    # OOO_FAKE_RUNNER=1 (documented TEST hook for the B-domain scheduler
    # dry runs): rep 1 -> pseudo classification "Inactive" and a
    # structurally complete sample WITHOUT gem5
    r = run_sr(["run", "--campaign-yaml", CRASH_YAML, "--rep", "1"],
               env_extra=dict(OOO_FAKE_RUNNER="1"))
    check("fake-rc0", r.returncode == 0, r.stdout[-300:])
    d = sample_dir("selftest-ooo-crash", rep=1)
    obs = json.load(open(os.path.join(d, "observation.json")))
    check("fake-pseudo-inactive", obs["l5"]["classification"] == "Inactive",
          obs["l5"]["classification"])
    check("fake-chain-complete-inactive",
          obs["chain_complete"] is True and obs["chain_gaps"] == [],
          (obs["chain_complete"], obs["chain_gaps"]))
    check("fake-l0-activated-zero", obs["l0"]["activated"] == 0, obs["l0"])
    check("fake-l3-five-keys",
          all(k in obs["l3"] for k in
              ("status", "method", "fanout", "caveat", "reason")))
    check("fake-files-backfilled", len(obs["files"]) >= 3,
          sorted(obs["files"]))
    check("fake-complete-json",
          os.path.exists(os.path.join(d, "COMPLETE.json")))
    rl = os.path.join(RUNS, "selftest-ooo-crash", "results.jsonl")
    check("fake-jsonl-two-lines", sum(1 for _ in open(rl)) == 2)


def test_no_staging_residue():
    for cid in ("selftest-ooo-crash", "selftest-ooo-masked"):
        st = os.path.join(RUNS, cid, "samples", ".staging")
        residue = os.listdir(st) if os.path.isdir(st) else []
        check("no-residue-%s" % cid, residue == [], residue)


# ---- [FIX-A Task 2] OFFLINE fixtures (no gem5) --------------------------

MSNAP_HDR = ("# micro_snap v1: snap_seq,commit_seq,tick,rob_occ,iq_occ,"
             "fl_int,fl_fp,fl_vec,rob_head,rob_tail,rat_int_hash,"
             "rat_fp_hash,rat_vec_hash,rat_int_table,rat_fp_table,"
             "rat_vec_table\n")


def _msnap_row(snap, commit, tick):
    return ("%d,%d,%d,1,2,3,4,5,0,1,11,22,33,0:1,1:2,2:3\n"
            % (snap, commit, tick))


def _ctrace_line(seq, tick, val="0000000000000000"):
    return "%d,0,%d,4195f0,add,1,1,5,12,%s" % (seq, tick, val)


def _mk_goldens(td):
    """Golden ref pair: 50-line ctrace + 2-row msnap (both clean gz)."""
    gctrace = os.path.join(td, "golden_ctrace.csv.gz")
    with gzip.open(gctrace, "wt") as f:
        f.write("\n".join(_ctrace_line(i, 1000 + i) for i in range(50))
                + "\n")
    gmsnap = os.path.join(td, "golden_msnap.csv.gz")
    with gzip.open(gmsnap, "wt") as f:
        f.write(MSNAP_HDR)
        f.write(_msnap_row(0, 0, 100))
        f.write(_msnap_row(1000, 1000, 1100))
    return gctrace, gmsnap


def _mk_staging(td, name):
    st = os.path.join(td, name)
    os.makedirs(st)
    return st


def test_do_l1_do_l2_zero_line_crash_semantics():
    """[FIX-A Task 2] zero-observation Crash semantics, OFFLINE (no gem5):
    a Crash/Hang run whose ctrace has 0 readable lines (0 bytes or an
    empty gzip) or whose msnap has 0 data rows crashed BEFORE any
    observation was flushed -- calling the differs would fabricate
    divergences (commit_diff reports every ref seq as one-sided), so
    do_l2/do_l1 must return honest no-observation blocks instead."""
    import ooo_sample_runner as sr
    td = tempfile.mkdtemp(prefix="fixa-zero-")
    gctrace, gmsnap = _mk_goldens(td)

    # (1) 0-byte ctrace + Crash: no commit_diff call, honest block
    st = _mk_staging(td, "st1")
    open(os.path.join(st, "ctrace.csv.gz"), "wb").close()
    blk, cd, cov = sr.do_l2(st, gctrace, "full", 100, 1000, "Crash", [])
    check("z1-l2-status", blk["status"] == "not_observed_before_crash",
          blk["status"])
    check("z1-l2-cd-null", blk["commit_diff"] is None and cd is None,
          (blk.get("commit_diff"), cd))
    check("z1-l2-fdc-null", blk["first_divergent_commit"] is None,
          blk.get("first_divergent_commit"))
    check("z1-l2-note", "run trace 0 lines" in blk["coverage"]["note"],
          blk["coverage"]["note"])
    check("z1-no-commit-diff-json",
          not os.path.exists(os.path.join(st, "evidence",
                                          "commit_diff.json")))
    # (2) 0-byte ctrace + Hang: same honest state
    st = _mk_staging(td, "st2")
    open(os.path.join(st, "ctrace.csv.gz"), "wb").close()
    blk, cd, _ = sr.do_l2(st, gctrace, "full", 100, 1000, "Hang", [])
    check("z2-hang-status", blk["status"] == "not_observed_before_crash",
          blk["status"])
    # (3) 0-byte ctrace + Masked: error (a completed run finalizes its
    # trace; a 0-line trace with a non-crash class is unexpected)
    st = _mk_staging(td, "st3")
    open(os.path.join(st, "ctrace.csv.gz"), "wb").close()
    blk, cd, _ = sr.do_l2(st, gctrace, "full", 100, 1000, "Masked", [])
    check("z3-masked-error", blk["status"] == "error", blk["status"])
    check("z3-masked-cd-null", blk["commit_diff"] is None,
          blk.get("commit_diff"))
    # (4) header-only msnap (0 data rows, truncated gz like the real
    # 116-byte crash msnap) + Crash: no micro_diff call
    st = _mk_staging(td, "st4")
    blob = MSNAP_HDR.encode()
    gz = gzip.compress(blob)
    with open(os.path.join(st, "msnap.csv.gz"), "wb") as f:
        f.write(gz[: int(len(gz) * 0.7)])   # crash mid-write: no trailer
    l1 = sr.do_l1(st, gmsnap, "Crash")
    check("z4-l1-status", l1[0]["status"] == "no_snapshots_before_crash",
          l1[0]["status"])
    check("z4-l1-md-null", l1[0]["micro_diff"] is None and l1[1] is None,
          l1[0].get("micro_diff"))
    check("z4-no-micro-diff-json",
          not os.path.exists(os.path.join(st, "evidence",
                                          "micro_diff.json")))
    # (5) 0-data-row msnap + Masked: error (unexpected for a completed
    # run)
    st = _mk_staging(td, "st5")
    with gzip.open(os.path.join(st, "msnap.csv.gz"), "wt") as f:
        f.write(MSNAP_HDR)
    l1 = sr.do_l1(st, gmsnap, "Masked")
    check("z5-l1-error", l1[0]["status"] == "error", l1[0]["status"])
    # (6) prefix-truncated ctrace (NON-empty prefix) + Crash: commit_diff
    # IS called, salvages the prefix, stops at the truncation -- verdict
    # truncated_no_divergence_in_prefix, fdc null, coverage records the
    # readable prefix line count
    st = _mk_staging(td, "st6")
    full = ("\n".join(_ctrace_line(i, 1000 + i) for i in range(50))
            + "\n").encode()
    gz = gzip.compress(full)
    with open(os.path.join(st, "ctrace.csv.gz"), "wb") as f:
        f.write(gz[: int(len(gz) * 0.7)])
    blk, cd, cov = sr.do_l2(st, gctrace, "full", 100, 1000, "Crash", [])
    check("z6-prefix-status",
          blk["status"] == "not_observed_before_crash", blk["status"])
    check("z6-prefix-verdict",
          cd["verdict"] == "truncated_no_divergence_in_prefix",
          cd["verdict"])
    check("z6-prefix-fdc-null", blk["first_divergent_commit"] is None,
          blk.get("first_divergent_commit"))
    check("z6-prefix-coverage-lines",
          blk["coverage"]["run_trace_lines"] > 0
          and blk["coverage"]["run_trace_lines"] <= 50,
          blk["coverage"])
    check("z6-prefix-coverage-truncated",
          blk["coverage"]["run_trace_truncated"] is True,
          blk["coverage"])
    check("z6-commit-diff-json-exists",
          os.path.exists(os.path.join(st, "evidence",
                                      "commit_diff.json")))
    # (7) prefix WITH a real divergence + Crash: status ok, fdc INSIDE
    # the prefix (observation happened before the crash)
    st = _mk_staging(td, "st7")
    bad = [_ctrace_line(i, 1000 + i,
                        "deadbeefdeadbeef" if i == 5 else
                        "0000000000000000") for i in range(50)]
    gz = gzip.compress(("\n".join(bad) + "\n").encode())
    with open(os.path.join(st, "ctrace.csv.gz"), "wb") as f:
        f.write(gz[: int(len(gz) * 0.7)])
    blk, cd, _ = sr.do_l2(st, gctrace, "full", 100, 1000, "Crash", [])
    check("z7-div-status-ok", blk["status"] == "ok", blk["status"])
    check("z7-div-fdc-in-prefix",
          blk["first_divergent_commit"] is not None
          and blk["first_divergent_commit"]["seq"] == 5,
          blk["first_divergent_commit"])
    # (8) clean full ctrace + Masked: unchanged legacy behavior (diff
    # runs, verdict no_divergence, coverage records 50 lines)
    st = _mk_staging(td, "st8")
    with gzip.open(os.path.join(st, "ctrace.csv.gz"), "wt") as f:
        f.write("\n".join(_ctrace_line(i, 1000 + i) for i in range(50))
                + "\n")
    blk, cd, _ = sr.do_l2(st, gctrace, "full", 100, 1000, "Masked", [])
    check("z8-clean-ok", blk["status"] == "ok", blk["status"])
    check("z8-clean-no-div", cd["verdict"] == "no_divergence", cd["verdict"])
    check("z8-clean-lines", blk["coverage"]["run_trace_lines"] == 50,
          blk["coverage"])
    # (9) >0-data-row msnap + Masked: micro_diff still runs (legacy path)
    st = _mk_staging(td, "st9")
    with gzip.open(os.path.join(st, "msnap.csv.gz"), "wt") as f:
        f.write(MSNAP_HDR)
        f.write(_msnap_row(0, 0, 100))
        f.write(_msnap_row(1000, 1000, 1100))
    l1 = sr.do_l1(st, gmsnap, "Masked")
    check("z9-l1-ok", l1[0]["status"] == "ok", l1[0]["status"])
    check("z9-md-ran", isinstance(l1[1], dict)
          and l1[1]["no_divergence"] is True, l1[1] if l1[1] else None)
    # (10) count_lines_salvage contract: 0-byte file = 0 lines, comment
    # lines excluded for msnap data rows
    zpath = os.path.join(td, "zero")
    open(zpath, "wb").close()
    check("z10-zero-bytes",
          sr.count_lines_salvage(zpath) == (0, False))
    cpath = os.path.join(td, "clean.gz")
    with gzip.open(cpath, "wt") as f:
        f.write(MSNAP_HDR)
        f.write(_msnap_row(0, 0, 100))
    check("z10-msnap-rows",
          sr.count_lines_salvage(cpath, comment="#") == (1, False))


# ---- [FIX-A Task 3] OFFLINE reobserve fixtures (no gem5) ----------------

def _mk_old_crash_sample(td):
    """A published-sample lookalike carrying the PRE-fix observation of a
    0-line Crash (fabricated diverged verdict, null funnel) plus its
    retained evidence, verbatim-shaped after
    formal_D02-F0-W6-c-c0000-r0007."""
    sd = os.path.join(td, "old-crash-sample")
    ev = os.path.join(sd, "evidence")
    os.makedirs(ev)
    gctrace, gmsnap = _mk_goldens(td)
    with open(os.path.join(ev, "decode_injections.log"), "w") as f:
        f.write("Tick: 475090, Site: fetch_decode, mode=bitflip2_cross, "
                "pc=0x415758, orig_enc=0xd503201f, new_enc=0xd521201f, "
                "bits=[21,17], field=cross, dist=4, orig_mnemonic=nop, "
                "new_mnemonic=unknown, macroop_new=0, faults_injected: 1\n")
    # 0-line window trace (clean empty gz, like the 43-byte real one)
    with gzip.open(os.path.join(ev, "ctrace_window.csv.gz"), "wt"):
        pass
    # header-only truncated msnap (the 116-byte real shape)
    gz = gzip.compress(MSNAP_HDR.encode())
    with open(os.path.join(ev, "msnap.csv.gz"), "wb") as f:
        f.write(gz[: int(len(gz) * 0.7)])
    # the FABRICATED pre-fix commit_diff (verdict diverged from an empty
    # trace) -- reobserve must DISCARD it for the 0-line case
    with open(os.path.join(ev, "commit_diff.json"), "w") as f:
        json.dump(dict(tool="commit_diff", verdict="diverged",
                       run_truncated=False, run_instructions=0,
                       first_divergence=dict(seq=0,
                                             class_="instruction_flow"
                                                    "_change"),
                       primary_class="instruction_flow_change"), f)
    with open(os.path.join(ev, "replay_config.json"), "w") as f:
        json.dump(dict(component="decode", l2_mode="window",
                       window_pre_seq=100, window_post_seq=1000,
                       golden_ctrace=gctrace, golden_msnap=gmsnap,
                       golden_final="45737cc9a76c0dce",
                       hang_timeout=600, msnap_every=1000,
                       binary="/bin/true"), f)
    with open(os.path.join(sd, "runner.stdout"), "w") as f:
        f.write("[runner] RESULT: run_id=old-crash-c0000-r0007 "
                "classification=Crash faults_injected=1 exit=-6 "
                "timed_out=False oracle=exact_hash\n"
                "[runner]   reason: fixture\n"
                "[runner] CHECKSUM: none\n")
    # pre-fix observation: null funnel + fabricated l2
    old_obs = dict(
        schema_version="ooo-observation/v1",
        identity=dict(run_id="old-crash-c0000-r0007", campaign_id="fixture",
                      runid_row="D02-F0-W6-c", submodel="decode",
                      sample_index=7, phase="formal", seed=1,
                      manifest_sha256="0" * 64, gem5_sha256="0" * 64,
                      config=dict(path="configs/se/ooo_proxy.py",
                                  sha256="0" * 64),
                      workload=dict(path="w", sha256="0" * 64,
                                    golden_id="g"), golden_key="k",
                      chaos_commit="x", patchset_sha256="n/a",
                      pythonhashseed=0, host="h",
                      started="2026-10-12T00:00:00",
                      finished="2026-10-12T00:01:00", wall_s=60.0),
        l0=dict(status="ok", component="decode",
                log_name="decode_injections.log",
                log_sha256="0" * 64, injected=1, activated=1,
                eligible_count=None, attempted=None, events=[], skips=[],
                skip_lines=0, truncated=False),
        l1=dict(status="truncated", micro_diff=dict(fake=True),
                first_divergence=None, files=dict()),
        l2=dict(status="ok",
                coverage=dict(mode="window", seq_lo=0, seq_hi=1000,
                              note="fixture"),
                commit_diff=dict(verdict="diverged",
                                 first_divergence=dict(seq=0),
                                 run_truncated=False, fake=True),
                first_divergent_commit=dict(seq=0), files=dict()),
        l3=dict(status="unsupported", method=None, fanout=None,
                caveat=None, reason="commit trace records dest regs only"),
        l4=dict(status="ok",
                first_detection=dict(kind="abnormal_termination",
                                     detector="OS", tick=None, seq=0,
                                     note=""),
                latency_from_l0=dict(ticks=None, committed_insts=None,
                                     note=""),
                oracle=dict(kind="exact_hash", golden="45737cc9a76c0dce",
                            observed=None, match=None)),
        l5=dict(classification="Crash", reason="fixture", exit=-6,
                timed_out=False, faults_injected=1, checksum_observed=None,
                checksum_golden="45737cc9a76c0dce", detector=None,
                conservation=None),
        replay=dict(performed=False, pass2_classification=None,
                    determinism=None, verdict_pass2=None,
                    checksum_pass2=None, performed_at=None),
        files=dict(), coverage_scope=dict(mode="window", note="fixture"),
        audit=dict(built_at="2026-10-12T00:01:00", builder_sha256="0" * 64))
    with open(os.path.join(sd, "observation.json"), "w") as f:
        json.dump(old_obs, f, indent=1)
    return sd, old_obs


def test_reobserve_zero_line_crash_sample():
    """[FIX-A Task 3] reobserve re-derives the revised observation view
    from retained evidence WITHOUT gem5: real L0 funnel, honest 0-line
    Crash L1/L2, no fabricated divergence, original observation.json
    untouched, observation.revised.json written on demand."""
    import ooo_sample_runner as sr
    td = tempfile.mkdtemp(prefix="fixa-reobs-")
    sd, old_obs = _mk_old_crash_sample(td)
    obs_p = os.path.join(sd, "observation.json")
    before = open(obs_p, "rb").read()
    rev = sr.reobserve_sample(sd)
    # original untouched
    check("r-orig-untouched", open(obs_p, "rb").read() == before)
    # revised view: real funnel (Task 1) + honest zero-observation
    # statuses (Task 2)
    check("r-l0-attempted", rev["l0"]["attempted"] == 1, rev["l0"])
    check("r-l0-eligible", rev["l0"]["eligible"] == 1, rev["l0"])
    check("r-l0-injected", rev["l0"]["injected"] == 1, rev["l0"])
    check("r-l0-limited-note", bool(rev["l0"].get("limited")), rev["l0"])
    check("r-l1-status",
          rev["l1"]["status"] == "no_snapshots_before_crash",
          rev["l1"]["status"])
    check("r-l1-md-null", rev["l1"]["micro_diff"] is None)
    check("r-l2-status",
          rev["l2"]["status"] == "not_observed_before_crash",
          rev["l2"]["status"])
    check("r-l2-cd-null", rev["l2"]["commit_diff"] is None,
          rev["l2"].get("commit_diff"))
    check("r-l2-fdc-null", rev["l2"]["first_divergent_commit"] is None,
          rev["l2"].get("first_divergent_commit"))
    check("r-l2-note", "run trace 0 lines" in rev["l2"]["coverage"]["note"],
          rev["l2"]["coverage"]["note"])
    # the fabricated pre-fix first_detection seq=0 is gone
    check("r-l4-fd-seq-null", rev["l4"]["first_detection"]["seq"] is None,
          rev["l4"]["first_detection"])
    # classification re-derived from runner.stdout
    check("r-l5-classification", rev["l5"]["classification"] == "Crash",
          rev["l5"]["classification"])
    check("r-chain-gaps", rev["chain_gaps"] == ["L1", "L2", "L3"],
          rev["chain_gaps"])
    check("r-violations-empty", rev["violations"] == [], rev["violations"])
    # provenance: the revised view names what it revised
    check("r-reobserve-block",
          rev["reobserve"]["based_on_observation_sha256"] ==
          hashlib.sha256(before).hexdigest()
          and rev["reobserve"]["classification_pass1"] == "Crash",
          rev.get("reobserve"))
    # files manifest re-hashed over the sample dir (no self-hash)
    check("r-files-manifest",
          "evidence/decode_injections.log" in rev["files"]
          and "observation.json" not in rev["files"], sorted(rev["files"]))
    # no revised file written by the pure function
    check("r-no-revised-file",
          not os.path.exists(os.path.join(sd, "observation.revised.json")))
    # CLI: writes observation.revised.json, original still untouched
    r = run_sr(["reobserve", "--sample-dir", sd])
    check("r-cli-rc0", r.returncode == 0, r.stdout[-300:] + r.stderr[-300:])
    rev_p = os.path.join(sd, "observation.revised.json")
    check("r-cli-wrote-revised", os.path.exists(rev_p))
    check("r-cli-orig-untouched", open(obs_p, "rb").read() == before)
    check("r-cli-revised-parses",
          json.load(open(rev_p))["l2"]["status"] ==
          "not_observed_before_crash")
    # CLI --no-write: no file, original untouched
    os.remove(rev_p)
    r = run_sr(["reobserve", "--sample-dir", sd, "--no-write"])
    check("r-cli-nowrite-rc0", r.returncode == 0, r.stdout[-200:])
    check("r-cli-nowrite-no-file", not os.path.exists(rev_p))
    check("r-cli-nowrite-orig", open(obs_p, "rb").read() == before)


def test_reobserve_window_and_full_modes():
    """>0-line samples: window mode reuses the retained (honest)
    commit_diff.json; full mode re-runs commit_diff on the retained full
    trace."""
    import ooo_sample_runner as sr
    td = tempfile.mkdtemp(prefix="fixa-reobs2-")
    gctrace, gmsnap = _mk_goldens(td)
    # --- window-mode Masked sample with a NON-empty window ---
    sd = os.path.join(td, "win-sample")
    ev = os.path.join(sd, "evidence")
    os.makedirs(ev)
    with open(os.path.join(ev, "decode_injections.log"), "w") as f:
        f.write("Tick: 1100, Site: fetch_decode, mode=reg_bitflip, "
                "pc=0x4195f0, orig_enc=0xf900dfe0, new_enc=0xf900dfe4, "
                "bits=[2], orig_mnemonic=str, new_mnemonic=str, "
                "regs_moved=1, macroop_new=0, faults_injected: 1\n")
    with gzip.open(os.path.join(ev, "ctrace_window.csv.gz"), "wt") as f:
        f.write("\n".join(_ctrace_line(i, 1000 + i) for i in range(10))
                + "\n")
    with gzip.open(os.path.join(ev, "msnap.csv.gz"), "wt") as f:
        f.write(MSNAP_HDR)
        f.write(_msnap_row(0, 0, 100))
    honest_cd = dict(tool="commit_diff", verdict="no_divergence",
                     run_truncated=False, first_divergence=None,
                     ref_instructions=10, run_instructions=10)
    with open(os.path.join(ev, "commit_diff.json"), "w") as f:
        json.dump(honest_cd, f)
    with open(os.path.join(ev, "replay_config.json"), "w") as f:
        json.dump(dict(component="decode", l2_mode="window",
                       window_pre_seq=100, window_post_seq=1000,
                       golden_ctrace=gctrace, golden_msnap=gmsnap,
                       golden_final="45737cc9a76c0dce",
                       hang_timeout=600, msnap_every=1000,
                       binary="/bin/true"), f)
    with open(os.path.join(sd, "runner.stdout"), "w") as f:
        f.write("[runner] RESULT: run_id=win-c0000-r0000 "
                "classification=Masked faults_injected=1 exit=0 "
                "timed_out=False oracle=exact_hash\n"
                "[runner] CHECKSUM: 45737cc9a76c0dce\n")
    base, _ = _mk_old_crash_sample(td)   # reuse the identity builder
    old = json.load(open(os.path.join(base, "observation.json")))
    old["identity"]["run_id"] = "win-c0000-r0000"
    old["l5"].update(dict(classification="Masked", exit=0,
                          checksum_observed="45737cc9a76c0dce"))
    with open(os.path.join(sd, "observation.json"), "w") as f:
        json.dump(old, f, indent=1)
    rev = sr.reobserve_sample(sd)
    check("w-l2-ok", rev["l2"]["status"] == "ok", rev["l2"]["status"])
    check("w-l2-reuses-retained-cd",
          rev["l2"]["commit_diff"]["verdict"] == "no_divergence"
          and rev["l2"]["commit_diff"].get("ref_instructions") == 10,
          rev["l2"]["commit_diff"])
    check("w-l2-lines", rev["l2"]["coverage"]["run_trace_lines"] == 10,
          rev["l2"]["coverage"])
    check("w-l1-ok", rev["l1"]["status"] == "ok", rev["l1"]["status"])
    check("w-chain-gaps", rev["chain_gaps"] == ["L3"], rev["chain_gaps"])
    # --- full-mode Masked sample: re-runs commit_diff on the retained
    # full trace against the golden ---
    sd2 = os.path.join(td, "full-sample")
    ev2 = os.path.join(sd2, "evidence")
    os.makedirs(ev2)
    shutil.copy(os.path.join(ev, "decode_injections.log"),
                os.path.join(ev2, "decode_injections.log"))
    with gzip.open(os.path.join(ev2, "ctrace.csv.gz"), "wt") as f:
        f.write("\n".join(_ctrace_line(i, 1000 + i) for i in range(50))
                + "\n")
    shutil.copy(os.path.join(ev, "msnap.csv.gz"),
                os.path.join(ev2, "msnap.csv.gz"))
    with open(os.path.join(ev2, "replay_config.json"), "w") as f:
        json.dump(dict(component="decode", l2_mode="full",
                       window_pre_seq=100, window_post_seq=1000,
                       golden_ctrace=gctrace, golden_msnap=gmsnap,
                       golden_final="45737cc9a76c0dce",
                       hang_timeout=600, msnap_every=1000,
                       binary="/bin/true"), f)
    with open(os.path.join(sd2, "runner.stdout"), "w") as f:
        f.write("[runner] RESULT: run_id=full-c0000-r0000 "
                "classification=Masked faults_injected=1 exit=0 "
                "timed_out=False oracle=exact_hash\n"
                "[runner] CHECKSUM: 45737cc9a76c0dce\n")
    old2 = json.loads(json.dumps(old))
    old2["identity"]["run_id"] = "full-c0000-r0000"
    with open(os.path.join(sd2, "observation.json"), "w") as f:
        json.dump(old2, f, indent=1)
    rev2 = sr.reobserve_sample(sd2)
    check("f-l2-ok", rev2["l2"]["status"] == "ok", rev2["l2"]["status"])
    check("f-l2-reran-diff",
          rev2["l2"]["commit_diff"]["verdict"] == "no_divergence"
          and rev2["l2"]["commit_diff"]["ref_instructions"] == 50,
          rev2["l2"]["commit_diff"])
    # --- missing replay_config.json: loud honest failure ---
    sd3 = os.path.join(td, "no-rcfg")
    ev3 = os.path.join(sd3, "evidence")
    os.makedirs(ev3)
    shutil.copy(os.path.join(sd, "observation.json"),
                os.path.join(sd3, "observation.json"))
    r = run_sr(["reobserve", "--sample-dir", sd3])
    check("no-rcfg-loud-failure", r.returncode != 0
          and "replay_config" in (r.stdout + r.stderr),
          (r.returncode, r.stderr[-200:]))


def main():
    print("test_do_l1_do_l2_zero_line_crash_semantics:")
    test_do_l1_do_l2_zero_line_crash_semantics()
    print("test_reobserve_zero_line_crash_sample:")
    test_reobserve_zero_line_crash_sample()
    print("test_reobserve_window_and_full_modes:")
    test_reobserve_window_and_full_modes()
    print("test_crash_sample:")
    test_crash_sample()
    print("test_idempotent_rerun:")
    test_idempotent_rerun()
    print("test_masked_sample:")
    test_masked_sample()
    print("test_replay:")
    test_replay()
    print("test_fake_runner_hook:")
    test_fake_runner_hook()
    print("test_no_staging_residue:")
    test_no_staging_residue()
    n = len(FAILURES)
    print("\n%s (%d checks)" % ("ALL PASS" if n == 0 else
                                "FAILURES: " + repr(FAILURES),
                                len(CHECKS)))
    sys.exit(1 if n else 0)


if __name__ == "__main__":
    main()
