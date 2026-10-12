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
retention); (5) OOO_FAKE_RUNNER test hook; (6) no staging residue.
Run: python3 tools/tests/test_ooo_sample_runner.py
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

TOOLS = "/home/sdc/gem5-fi-ding/.claude/worktrees/ooo-l0l5-a/tools"
RUNS = "/home/sdc/gem5-fi-ding/runs"
SELFTEST = os.path.join(RUNS, "ooo-l0l5", "selftest", "sample-runner")
CRASH_YAML = os.path.join(SELFTEST, "selftest_crash.yaml")
MASKED_YAML = os.path.join(SELFTEST, "selftest_masked.yaml")

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
    # Crash semantics: the run died before ANY commit was flushed (the
    # CTRACE line says lines=0 bytes=0), so the L2 verdict is an honest
    # instruction_flow_change divergence at seq 0 -- NEVER no_divergence
    check("crash-l1-truncated", obs["l1"]["status"] == "truncated",
          obs["l1"]["status"])
    check("crash-l2-status", obs["l2"]["status"] in
          ("ok", "not_observed_before_crash"), obs["l2"]["status"])
    check("crash-l2-verdict-diverged",
          obs["l2"]["commit_diff"]["verdict"] == "diverged",
          obs["l2"]["commit_diff"]["verdict"])
    check("crash-l2-not-fake-no-divergence",
          obs["l2"]["commit_diff"]["verdict"] != "no_divergence")
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
    check("crash-gaps-l3-only", obs["chain_gaps"] == ["L3"],
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
          and lines[0]["chain_gaps"] == ["L3"], lines[0])
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


def main():
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
