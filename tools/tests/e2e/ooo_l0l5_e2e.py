#!/usr/bin/env python3
"""[OOO][P1] L0-L5 three-class E2E orchestration + FR02-SDC chain
validation (L0-L5 run, 2026-10-12; plan Task 7, Subagent-C).

Orchestrates FOUR e2e samples (campaign ids prefixed `e2e_`, all outputs
under /home/sdc/gem5-fi-ding/runs/ooo-l0l5/e2e/), each through the FULL
chain via tools/ooo_sample_runner.py (`run --campaign-yaml <y> --rep 0`),
then asserts the class-specific L0-L5 contract on observation.json, then
replays every sample and asserts determinism=="match":

  normal — smoke + decode imm_bitflip with a trigger far beyond the
      workload's end tick (10^9 >> smoke's 92,414,630 end tick, measured
      from the cached golden stats) -> classification Inactive, L1-L4
      inactive_no_activation, chain_complete true;
  masked — smoke + decode imm_bitflip, seed 20261013 (first Masked hit of
      the 20261012.. probe sweep; fixture selection, NOT statistics) ->
      Masked, checksum==golden, l1/l2 ok, l3 unsupported + chain_complete
      false + gaps==["L3"], l4 detector None;
  crash — smoke + decode imm_bitflip, seed 20261012 (verified Crash,
      exit=-6 SIGABRT) -> Crash, l2 in {not_observed_before_crash,
      truncated} or ok-with-divergence — NEVER a false no_divergence —
      and ctrace/msnap truncated prefixes stay readable;
  sdc — rat + local_mbu + map_bitflip2_adj_vec on dep_chain_vec, seed
      20261600 replicating runs/formal_FR02_dcv/c0000 r0000's exact fault
      geometry (verified: SDC, first divergence ⑤data_corruption at
      commit seq 165) -> SDC, l2.commit_diff.primary_class==
      "data_corruption", l4.first_detection.detector=="Application",
      checksum != golden.

Machine verdict per class + overall -> e2e_result.json. Exit 0 iff all
PASS; 1 on any FAIL; 3 BLOCKED (ooo_sample_runner.py not merged yet /
frozen-binary identity drift). Assertions are NEVER relaxed to pass.

  --self-test   offline: unit-test the assertion helpers on synthetic
                fixtures + the FR02 replication check + campaign-yaml
                generation sanity (no gem5, no sample_runner).
"""

import argparse
import glob
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

import yaml

HERE = os.path.dirname(os.path.realpath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
TOOLS = os.path.join(REPO, "tools")
SAMPLE_RUNNER = os.path.join(TOOLS, "ooo_sample_runner.py")
GEM5_OPT = os.path.join(REPO, "build", "ARM", "gem5.opt")

E2E_ROOT = "/home/sdc/gem5-fi-ding/runs/ooo-l0l5/e2e"
SELFTEST_ROOT = os.environ.get(
    "OOO_E2E_SELFTEST_ROOT",
    "/home/sdc/gem5-fi-ding/runs/ooo-l0l5/selftest/e2e-selftest")
FR02_RESULTS = ("/home/sdc/gem5-fi-ding/runs/formal_FR02_dcv/c0000/"
                "results.jsonl")
FR02_MANIFEST_DIR = "/home/sdc/gem5-fi-ding/runs/formal_FR02_dcv/c0000"

FROZEN_GEM5_SHA = ("1a618953b014514713c0ad98c7f3d69a48171d81f0463d934b"
                   "ccdfcfc0070bf3")
SMOKE_SHA = ("30cd303815735206e697df0163887bceecec2388a26d22cfc27a4dc8cb"
             "98e85d")
DCV_SHA = ("1016473f55bdfb1227c9bc7ab334d95f71bdb1fb5703d99bab08e87fe54b"
           "4d51")

# E2E fixture seeds — pinned by REAL probe runs (2026-10-12, probe_results
# .jsonl under runs/ooo-l0l5/selftest/c-probe/): fixture selection, not
# statistical samples.
SEED_MASKED = 20261013   # first Masked hit after the sweep start
SEED_CRASH = 20261012    # Crash, exit=-6 (SIGABRT)
SEED_SDC = 20261600      # FR02 formal_FR02_dcv-c0000-r0000 SDC replica
SEED_NORMAL = 20261012   # trigger never fires; seed irrelevant, kept fixed
# smoke golden end tick = 92,414,630 (goldens/9859154dd47e7e734bbb27a7/
# stats_ref.txt) -> 10^9 is far beyond it: the trigger can never fire.
TRIGGER_LATE = 10 ** 9

sys.path.insert(0, TOOLS)
import ooo_chain_audit  # noqa: E402  (audit library reuse)


# ------------------------------------------------------------ helpers

def sha256_file(path, _buf=1024 * 1024):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(_buf)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def gzip_prefix_readable(path):
    """Line-wise read with the truncated-gzip rescue semantics of
    micro_diff/commit_diff: a crashed run's .gz lacks the trailer; the
    complete rows before the EOFError are the honest readable prefix.
    Returns (n_data_lines, truncated)."""
    rows, truncated = 0, False
    with gzip.open(path, "rt", errors="replace") as f:
        try:
            for line in f:
                if line.startswith("#"):
                    continue
                rows += 1
        except (EOFError, OSError):
            truncated = True
    return rows, truncated


def load_observation(sample_dir):
    with open(os.path.join(sample_dir, "observation.json")) as f:
        return json.load(f)


def replay_determinism(obs):
    """Determinism verdict from the observation's replay block. The
    contract nests it under l2.replay; the plan text also allows a
    top-level replay block — both are accepted, neither is invented."""
    for block in (obs.get("l2", {}).get("replay"), obs.get("replay")):
        if isinstance(block, dict) and "determinism" in block:
            return block["determinism"]
    return "missing"


def detector_of(obs):
    fd = obs.get("l4", {}).get("first_detection")
    if fd is None:
        return None
    if isinstance(fd, dict):
        return fd.get("detector")
    return None


def audit_clean(sample_dir):
    """Independent audit gate: the observation must carry zero audit
    violations (files shas re-hashed, schema keys, chain flags...)."""
    try:
        obs = load_observation(sample_dir)
    except (ValueError, OSError) as e:
        return ["observation_unloadable:%s" % e]
    rec = ooo_chain_audit.audit_observation(
        obs, sample_dir, frozen_gem5_sha=FROZEN_GEM5_SHA)
    return list(rec["violations"])


def trace_evidence_readable(obs, sample_dir):
    """Every ctrace/msnap evidence file in the files manifest must exist
    and be readable as a gz prefix (>0 lines) or honestly truncated."""
    fails = []
    files = obs.get("files", {})
    cands = [r for r in files
             if any(k in r.lower() for k in
                    ("ctrace", "msnap", "micro_snap", "microsnap"))]
    if not cands:
        return ["no_trace_evidence_file_in_manifest"]
    for rel in sorted(cands):
        p = os.path.join(sample_dir, rel)
        if not os.path.isfile(p):
            fails.append("trace_file_missing:%s" % rel)
            continue
        rows, truncated = gzip_prefix_readable(p)
        if rows == 0 and not truncated:
            fails.append("trace_unreadable_empty:%s" % rel)
    return fails


# ----------------------------------------------- class assertions
# Each returns a list of failure strings; empty list == PASS.

def assert_normal(obs):
    f = []
    if obs.get("l5", {}).get("classification") != "Inactive":
        f.append("classification!=Inactive (%r)"
                 % obs.get("l5", {}).get("classification"))
    l0 = obs.get("l0", {})
    if l0.get("activated") != 0 or l0.get("injected") != 0:
        f.append("late-trigger sample must have injected==activated==0 "
                 "(injected=%r activated=%r)"
                 % (l0.get("injected"), l0.get("activated")))
    for lk in ("l1", "l2", "l3", "l4"):
        st = obs.get(lk, {}).get("status")
        if st != "inactive_no_activation":
            f.append("%s.status!=inactive_no_activation (%r)" % (lk, st))
    if obs.get("chain_complete") is not True:
        f.append("chain_complete!=true")
    if obs.get("chain_gaps") != []:
        f.append("chain_gaps!=[] (%r)" % obs.get("chain_gaps"))
    return f


def assert_masked(obs):
    f = []
    l5, l0 = obs.get("l5", {}), obs.get("l0", {})
    if l5.get("classification") != "Masked":
        f.append("classification!=Masked (%r)" % l5.get("classification"))
    if l5.get("checksum_observed") is None \
            or l5.get("checksum_observed") != l5.get("checksum_golden"):
        f.append("masked checksum must equal golden "
                 "(obs=%r golden=%r)" % (l5.get("checksum_observed"),
                                         l5.get("checksum_golden")))
    if not (isinstance(l0.get("activated"), int) and l0["activated"] >= 1):
        f.append("masked sample must be activated "
                 "(activated=%r)" % l0.get("activated"))
    for lk in ("l1", "l2"):
        if obs.get(lk, {}).get("status") != "ok":
            f.append("%s.status!=ok (%r)" % (lk,
                                             obs.get(lk, {}).get("status")))
    if obs.get("l3", {}).get("status") != "unsupported":
        f.append("decode l3.status must be unsupported (%r)"
                 % obs.get("l3", {}).get("status"))
    if obs.get("chain_complete") is not False:
        f.append("chain_complete must be false (L3 gap)")
    if obs.get("chain_gaps") != ["L3"]:
        f.append("chain_gaps must be [L3] (%r)" % obs.get("chain_gaps"))
    if detector_of(obs) not in (None, "None", "n/a"):
        f.append("masked l4 detector must be None (%r)" % detector_of(obs))
    return f


def assert_crash(obs, sample_dir):
    f = []
    l5 = obs.get("l5", {})
    if l5.get("classification") != "Crash":
        f.append("classification!=Crash (%r)" % l5.get("classification"))
    if l5.get("exit") != -6:
        f.append("exit!=-6 (%r)" % l5.get("exit"))
    l2 = obs.get("l2", {})
    status, cd = l2.get("status"), (l2.get("commit_diff") or {})
    verdict = cd.get("verdict")
    if status == "ok" and verdict == "no_divergence":
        f.append("FALSE no_divergence claim on Crash "
                 "(l2.status=ok, verdict=no_divergence)")
    elif status in ("not_observed_before_crash", "truncated"):
        pass  # honest truncation records
    elif status == "ok" and verdict == "diverged":
        pass  # divergence observed before the crash
    else:
        f.append("l2 not in honest set {not_observed_before_crash,"
                 "truncated, ok-with-divergence} (status=%r verdict=%r)"
                 % (status, verdict))
    f += trace_evidence_readable(obs, sample_dir)
    return f


def assert_sdc(obs):
    f = []
    l5, l0 = obs.get("l5", {}), obs.get("l0", {})
    if l5.get("classification") != "SDC":
        f.append("classification!=SDC (%r)" % l5.get("classification"))
    if l5.get("checksum_observed") is None \
            or l5.get("checksum_observed") == l5.get("checksum_golden"):
        f.append("SDC checksum must differ from golden "
                 "(obs=%r golden=%r)" % (l5.get("checksum_observed"),
                                         l5.get("checksum_golden")))
    if not (isinstance(l0.get("activated"), int) and l0["activated"] >= 1):
        f.append("SDC sample must be activated")
    cd = obs.get("l2", {}).get("commit_diff") or {}
    if cd.get("primary_class") != "data_corruption":
        f.append("l2.commit_diff.primary_class!=data_corruption (%r)"
                 % cd.get("primary_class"))
    if detector_of(obs) != "Application":
        f.append("l4.first_detection.detector!=Application (%r)"
                 % detector_of(obs))
    return f


# --------------------------------------------------- campaign yamls

def campaign_dict(campaign_id, injector, grid, base_seed, workload,
                  trigger_value, binary_sha, l2_mode="full",
                  window_pre=None, window_post=None):
    trace = {"enabled": True, "l2_mode": l2_mode, "msnap_every": 1000}
    if l2_mode == "window":
        trace["window_pre_seq"] = window_pre
        trace["window_post_seq"] = window_post
    return {
        "campaign_id": campaign_id,
        # integration fix 2026-10-12 (lead): the sample_runner campaign gate
        # requires the L0-L5 campaign schema (Subagent-A contract); these
        # are E2E validation campaigns, phase=engineering (never formal).
        "schema_version": "arm-chaos-fi/l0l5-campaign/v1",
        "runid_row": "E2E-L0L5",
        "submodel": injector,
        "phase": "engineering",
        "injector": injector,
        "config": "C3",
        "mode": "SE",
        "cpu_model": "ArmO3CPU",
        "grid": grid,
        "n_per_cell": 1,
        "base_seed": base_seed,
        "replay_pct": 100,
        "workload": dict(workload, trigger_mode="cycle",
                         trigger_value=trigger_value,
                         binary_sha256=binary_sha),
        "limits": {"max_faults": 1},
        "hang_timeout": 650,
        "chaos_commit": "e2e-2026-10-12",
        "patchset_sha256": "e2e-2026-10-12",
        "trace": trace,
        "topup": {"seed_offset": 1000000, "rounds_max": 0},
        "ooo": {"design_unit_id": "E2E-L0L5",
                "submodel": injector},
    }


DECODE_GRID = {
    "target_index": -1, "field": "imm", "width_bits": 32,
    "sub_field": "imm_bitflip", "fault_model": "transient_bit_flip",
    "protection_model": "none",
}
SDC_GRID = {
    "target_index": -1, "field": "map", "width_bits": 7,
    "sub_field": "map_bitflip2_adj_vec", "fault_model": "local_mbu",
    "protection_model": "none",
}
SMOKE_WL = {"binary": "workloads/ooo/smoke/smoke",
            "golden_id": "smoke-golden-v1"}
DCV_WL = {"binary": "workloads/ooo/dep_chain/dep_chain_vec",
          "golden_id": "depchainvec-golden-v1"}

E2E_CLASSES = {
    # class -> (campaign_id, campaign_dict, assert_fn, needs_sample_dir)
    "normal": ("e2e_normal_late_trigger",
               campaign_dict("e2e_normal_late_trigger", "decode",
                             DECODE_GRID, SEED_NORMAL, SMOKE_WL,
                             TRIGGER_LATE, SMOKE_SHA),
               lambda obs, sd: assert_normal(obs), False),
    "masked": ("e2e_masked_smoke_decode",
               campaign_dict("e2e_masked_smoke_decode", "decode",
                             DECODE_GRID, SEED_MASKED, SMOKE_WL,
                             1000, SMOKE_SHA),
               lambda obs, sd: assert_masked(obs), False),
    "crash": ("e2e_crash_smoke_decode",
              campaign_dict("e2e_crash_smoke_decode", "decode",
                            DECODE_GRID, SEED_CRASH, SMOKE_WL,
                            1000, SMOKE_SHA),
              assert_crash, True),
    "sdc": ("e2e_sdc_fr02_replica",
            campaign_dict("e2e_sdc_fr02_replica", "rat", SDC_GRID,
                          SEED_SDC, DCV_WL, 1000, DCV_SHA,
                          l2_mode="window", window_pre=10000,
                          window_post=100000),
            lambda obs, sd: assert_sdc(obs), False),
}


def write_campaign_yaml(campaign, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, campaign["campaign_id"] + ".yaml")
    with open(path, "w") as f:
        yaml.safe_dump(campaign, f, sort_keys=False)
    return path


def find_sample_dir(campaign_id, rep=0):
    run_id = "%s-c0000-r%04d" % (campaign_id, rep)
    pat = os.path.join(E2E_ROOT, "**", "samples", run_id)
    hits = [p for p in glob.glob(pat, recursive=True) if os.path.isdir(p)]
    return (hits[0] if len(hits) == 1 else None), run_id


# ------------------------------------------------------- FR02 replica

def extract_fr02_sdc_row():
    """Read-only query of the FR02 dcv results for the FIRST SDC row;
    returns (manifest_name, row) or (None, None)."""
    if not os.path.isfile(FR02_RESULTS):
        return None, None
    with open(FR02_RESULTS) as f:
        for line in f:
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if row.get("classification") == "SDC":
                return row["manifest"], row
    return None, None


def check_fr02_replication():
    """Offline: the e2e SDC campaign must regenerate the EXACT fault
    geometry of the FR02 first-SDC manifest (identity fields excluded).
    Returns (failures, info)."""
    fails, info = [], {}
    manifest_name, row = extract_fr02_sdc_row()
    if manifest_name is None:
        return ["fr02_sdc_row_not_found"], info
    info["fr02_manifest"] = manifest_name
    ref_path = os.path.join(FR02_MANIFEST_DIR, manifest_name)
    with open(ref_path) as f:
        ref = yaml.safe_load(f)
    _, man = _manifest_for(E2E_CLASSES["sdc"][1])
    for section in ("platform", "trigger", "target", "fault", "rng",
                    "limits", "oracle"):
        a, b = man.get(section, {}), ref.get(section, {})
        for k in sorted(set(a) | set(b)):
            if a.get(k) != b.get(k):
                fails.append("fr02_geometry_diff:%s.%s e2e=%r fr02=%r"
                             % (section, k, a.get(k), b.get(k)))
    info["e2e_seed"] = man["rng"]["master_seed"]
    info["fr02_seed"] = ref["rng"]["master_seed"]
    return fails, info


def _manifest_for(campaign, outdir=None):
    import campaign as campaign_mod
    outdir = outdir or tempfile.mkdtemp(prefix="e2e-manifest-",
                                        dir=SELFTEST_ROOT)
    return campaign_mod.manifest_for_cell(campaign, campaign["grid"], 0, 0,
                                          outdir)


# ------------------------------------------------------------ runner

def run_sample_runner(args, timeout=2400):
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = "0"
    env["TMPDIR"] = os.path.join(E2E_ROOT, "tmp")
    os.makedirs(env["TMPDIR"], exist_ok=True)
    cmd = [sys.executable, SAMPLE_RUNNER] + args
    return subprocess.run(cmd, capture_output=True, text=True,
                          errors="replace", timeout=timeout, env=env)


def run_class(name, spec, results):
    campaign_id, campaign, assert_fn, needs_dir = spec
    print("\n[e2e] === class %s (campaign %s) ===" % (name, campaign_id))
    entry = {"campaign_id": campaign_id, "status": "FAIL"}
    ypath = write_campaign_yaml(campaign, os.path.join(E2E_ROOT,
                                                       "campaigns"))
    entry["campaign_yaml"] = ypath
    print("[e2e] campaign yaml: %s" % ypath)

    r = run_sample_runner(["run", "--campaign-yaml", ypath, "--rep", "0",
                           "--runs-root", E2E_ROOT])
    print("[e2e] sample_runner run rc=%d" % r.returncode)
    tail = (r.stdout or "").strip().splitlines()[-8:]
    for line in tail:
        print("[e2e]   | %s" % line)
    entry["sample_runner_rc"] = r.returncode
    entry["sample_runner_tail"] = tail
    if r.returncode != 0:
        entry["status"] = "FAIL"
        entry["reason"] = "sample_runner run rc=%d" % r.returncode
        results[name] = entry
        return

    sdir, run_id = find_sample_dir(campaign_id)
    entry["run_id"] = run_id
    entry["sample_dir"] = sdir
    if sdir is None:
        entry["reason"] = "sample dir not found for %s" % run_id
        results[name] = entry
        return
    obs = load_observation(sdir)
    entry["classification"] = obs.get("l5", {}).get("classification")

    fails = assert_fn(obs, sdir)
    entry["assertions"] = fails
    entry["audit_violations"] = audit_clean(sdir)
    if fails or entry["audit_violations"]:
        entry["status"] = "FAIL"
        results[name] = entry
        return

    r2 = run_sample_runner(["replay", "--sample-dir", sdir])
    print("[e2e] sample_runner replay rc=%d" % r2.returncode)
    entry["replay_rc"] = r2.returncode
    if r2.returncode != 0:
        entry["status"] = "FAIL"
        entry["reason"] = "replay rc=%d" % r2.returncode
        results[name] = entry
        return
    obs2 = load_observation(sdir)
    det = replay_determinism(obs2)
    entry["replay_determinism"] = det
    if det != "match":
        entry["status"] = "FAIL"
        entry["reason"] = "replay determinism=%r" % det
        results[name] = entry
        return
    entry["status"] = "PASS"
    results[name] = entry
    print("[e2e] class %s: PASS" % name)


def check_identity():
    if not os.path.isfile(GEM5_OPT):
        return "gem5.opt missing: %s" % GEM5_OPT
    got = sha256_file(GEM5_OPT)
    if got != FROZEN_GEM5_SHA:
        return "gem5.opt sha drift: %s != %s" % (got, FROZEN_GEM5_SHA)
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--self-test", action="store_true",
                    help="offline assertion-helper unit tests (no gem5)")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    return run_e2e()


def run_e2e():
    os.makedirs(E2E_ROOT, exist_ok=True)
    results = {"tool": "ooo_l0l5_e2e",
               "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
               "repo": REPO, "frozen_gem5_sha": FROZEN_GEM5_SHA}
    ident = check_identity()
    if ident:
        results["status"] = "BLOCKED"
        results["reason"] = ident
        _write_result(results)
        print("[e2e] BLOCKED: %s" % ident)
        return 3
    if not os.path.isfile(SAMPLE_RUNNER):
        results["status"] = "BLOCKED"
        results["reason"] = ("tools/ooo_sample_runner.py not present — "
                             "A branch (Task 6) not merged yet")
        _write_result(results)
        print("[e2e] BLOCKED: %s" % results["reason"])
        return 3

    # FR02 replication precheck (offline, read-only)
    rep_fails, rep_info = check_fr02_replication()
    results["fr02_replication"] = {"info": rep_info, "failures": rep_fails}

    for name in ("normal", "masked", "crash", "sdc"):
        run_class(name, E2E_CLASSES[name], results)

    results["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    statuses = [results[c]["status"] for c in
                ("normal", "masked", "crash", "sdc")]
    results["overall"] = ("PASS" if all(s == "PASS" for s in statuses)
                          else "FAIL")
    _write_result(results)
    print("\n[e2e] OVERALL: %s" % results["overall"])
    return 0 if results["overall"] == "PASS" else 1


def _write_result(results):
    path = os.path.join(E2E_ROOT, "e2e_result.json")
    with open(path, "w") as f:
        json.dump(results, f, indent=1, ensure_ascii=False)
    print("[e2e] wrote %s" % path)


# ------------------------------------------------------------ selftest

def _obs_min(**over):
    """A minimal but schema-shaped observation for the assert helpers."""
    obs = {
        "l0": {"injected": 1, "activated": 1, "events": [{"tick": 1}]},
        "l1": {"status": "ok"},
        "l2": {"status": "ok", "commit_diff": {"verdict": "no_divergence",
                                               "primary_class": None}},
        "l3": {"status": "unsupported"},
        "l4": {"status": "ok", "first_detection": None},
        "l5": {"classification": "Masked", "exit": 0,
               "checksum_observed": "45737cc9a76c0dce",
               "checksum_golden": "45737cc9a76c0dce"},
        "chain_complete": False, "chain_gaps": ["L3"],
        "files": {"evidence/ctrace.csv.gz": "00" * 32,
                  "evidence/msnap.csv.gz": "11" * 32},
    }
    for k, v in over.items():
        top = k.split(".")[0]
        if "." in k:
            obs[top] = dict(obs[top], **{k.split(".", 1)[1]: v})
        else:
            obs[k] = v
    return obs


FAILURES = []


def check(name, cond, detail=""):
    if cond:
        print("  PASS %s" % name)
    else:
        print("  FAIL %s %s" % (name, detail))
        FAILURES.append(name)


def self_test():
    global SELFTEST_ROOT
    os.makedirs(SELFTEST_ROOT, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="e2e-selftest-", dir=SELFTEST_ROOT)
    SELFTEST_ROOT = tmp
    try:
        return _self_test_body(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _self_test_body(tmp):
    print("[self-test] gzip truncation readability")
    good = os.path.join(tmp, "good.csv.gz")
    with gzip.open(good, "wt") as f:
        f.write("# comment\n" + "a,b\n" * 10)
    rows, trunc = gzip_prefix_readable(good)
    check("gz-good-readable", rows == 10 and trunc is False,
          "rows=%d trunc=%r" % (rows, trunc))
    trunc_path = os.path.join(tmp, "trunc.csv.gz")
    with gzip.open(trunc_path, "wt") as f:
        f.write("# comment\n" + "a,b\n" * 5000)  # big enough that early
        # buffered reads emit lines before the corrupt tail is reached
    with open(trunc_path, "rb") as f:
        data = f.read()
    with open(trunc_path, "wb") as f:
        f.write(data[:-6])  # chop the gz trailer -> EOFError mid-read
    rows, trunc = gzip_prefix_readable(trunc_path)
    check("gz-truncated-flagged", trunc is True and rows >= 1,
          "rows=%d trunc=%r" % (rows, trunc))

    print("[self-test] assert_normal")
    ok = _obs_min(l5={"classification": "Inactive", "exit": 0,
                      "checksum_observed": "x", "checksum_golden": "x"},
                  l0={"injected": 0, "activated": 0, "events": []},
                  l1={"status": "inactive_no_activation"},
                  l2={"status": "inactive_no_activation"},
                  l3={"status": "inactive_no_activation"},
                  l4={"status": "inactive_no_activation"},
                  chain_complete=True, chain_gaps=[])
    check("normal-pass", assert_normal(ok) == [])
    bad = _obs_min(l5={"classification": "Masked", "exit": 0,
                       "checksum_observed": "x", "checksum_golden": "x"},
                   l0={"injected": 0, "activated": 0, "events": []},
                   l1={"status": "inactive_no_activation"},
                   l2={"status": "inactive_no_activation"},
                   l3={"status": "inactive_no_activation"},
                   l4={"status": "inactive_no_activation"},
                   chain_complete=True, chain_gaps=[])
    check("normal-negative", assert_normal(bad) != [])

    print("[self-test] assert_masked")
    check("masked-pass", assert_masked(_obs_min()) == [])
    check("masked-negative-checksum",
          assert_masked(_obs_min(l5={"classification": "Masked", "exit": 0,
                                     "checksum_observed": "dead",
                                     "checksum_golden": "gold"})) != [])
    check("masked-negative-l3",
          assert_masked(_obs_min(l3={"status": "ok"},
                                 chain_complete=True, chain_gaps=[])) != [])
    check("masked-negative-detector",
          assert_masked(_obs_min(l4={"status": "ok",
                                     "first_detection": {
                                         "detector": "Application"}})) != [])

    print("[self-test] assert_crash")
    crash_l5 = {"classification": "Crash", "exit": -6,
                "checksum_observed": None, "checksum_golden": "gold"}

    def crash_obs(status, verdict):
        return _obs_min(l5=crash_l5,
                        l2={"status": status,
                            "commit_diff": {"verdict": verdict,
                                            "primary_class": None}})

    sd = _make_trace_sample_dir(tmp, "crash-ok")
    check("crash-pass-honest-truncated",
          assert_crash(crash_obs("truncated",
                                 "truncated_no_divergence_in_prefix"),
                       sd) == [])
    sd2 = _make_trace_sample_dir(tmp, "crash-nob")
    check("crash-pass-not-observed",
          assert_crash(crash_obs("not_observed_before_crash",
                                 "truncated_no_divergence_in_prefix"),
                       sd2) == [])
    sd3 = _make_trace_sample_dir(tmp, "crash-div")
    check("crash-pass-ok-diverged",
          assert_crash(crash_obs("ok", "diverged"), sd3) == [])
    sd4 = _make_trace_sample_dir(tmp, "crash-false")
    check("crash-negative-false-no-divergence",
          assert_crash(crash_obs("ok", "no_divergence"), sd4) != [])
    sd5 = _make_trace_sample_dir(tmp, "crash-empty-trace", empty=True)
    check("crash-negative-unreadable-trace",
          assert_crash(crash_obs("truncated",
                                 "truncated_no_divergence_in_prefix"),
                       sd5) != [])

    print("[self-test] assert_sdc")
    sdc_obs = _obs_min(
        l5={"classification": "SDC", "exit": 0,
            "checksum_observed": "deadbeefdeadbeef",
            "checksum_golden": "gold"},
        l2={"status": "ok", "commit_diff": {
            "verdict": "diverged", "primary_class": "data_corruption"}},
        l4={"status": "ok", "first_detection": {
            "kind": "checksum_mismatch", "detector": "Application",
            "tick": 1, "seq": None, "note": ""}},
        l3={"status": "unsupported"}, chain_complete=False,
        chain_gaps=["L3"])
    check("sdc-pass", assert_sdc(sdc_obs) == [])
    check("sdc-negative-class",
          assert_sdc(_obs_min(l5={"classification": "SDC", "exit": 0,
                                  "checksum_observed": "a",
                                  "checksum_golden": "b"},
                              l2={"status": "ok", "commit_diff": {
                                  "verdict": "diverged",
                                  "primary_class": "operand_forced_switch"}},
                              l4={"status": "ok", "first_detection": {
                                  "detector": "Application"}},
                              l3={"status": "unsupported"},
                              chain_complete=False,
                              chain_gaps=["L3"])) != [])
    check("sdc-negative-checksum-equal",
          assert_sdc(_obs_min(l5={"classification": "SDC", "exit": 0,
                                  "checksum_observed": "same",
                                  "checksum_golden": "same"},
                              l2={"status": "ok", "commit_diff": {
                                  "verdict": "diverged",
                                  "primary_class": "data_corruption"}},
                              l4={"status": "ok", "first_detection": {
                                  "detector": "Application"}},
                              l3={"status": "unsupported"},
                              chain_complete=False,
                              chain_gaps=["L3"])) != [])

    print("[self-test] replay determinism lookup")
    check("replay-l2-block",
          replay_determinism(_obs_min(l2={"status": "ok",
                                          "commit_diff": {},
                                          "replay": {
                                              "determinism": "match"}}))
          == "match")
    check("replay-top-block",
          replay_determinism(_obs_min(replay={"determinism": "match"}))
          == "match")
    check("replay-missing", replay_determinism(_obs_min()) == "missing")

    print("[self-test] FR02 SDC replication (offline, read-only)")
    fails, info = check_fr02_replication()
    print("  info: %s" % json.dumps(info, ensure_ascii=False))
    check("fr02-replication-exact", fails == [],
          "; ".join(fails) or "ok")

    print("[self-test] e2e campaign yaml generation")
    ydir = os.path.join(tmp, "campaigns")
    for cls, (cid, camp, _fn, _nd) in E2E_CLASSES.items():
        p = write_campaign_yaml(camp, ydir)
        with open(p) as f:
            back = yaml.safe_load(f)
        check("yaml-roundtrip-%s" % cls,
              back["campaign_id"] == cid
              and back["grid"] == camp["grid"]
              and back["base_seed"] == camp["base_seed"]
              and back["trace"]["enabled"] is True
              and back["workload"]["binary_sha256"] ==
              camp["workload"]["binary_sha256"]
              and back["workload"]["trigger_value"] ==
              camp["workload"]["trigger_value"], p)
    _, man = _manifest_for(E2E_CLASSES["sdc"][1])
    check("sdc-manifest-seed", man["rng"]["master_seed"] == SEED_SDC)
    _, man_n = _manifest_for(E2E_CLASSES["normal"][1])
    check("normal-manifest-late-trigger",
          man_n["trigger"]["value"] == TRIGGER_LATE)
    check("normal-trigger-beyond-smoke-end",
          TRIGGER_LATE > 92414630,
          "smoke golden end tick = 92,414,630")

    ident = check_identity()
    check("frozen-gem5-identity", ident is None, ident or "ok")

    n = len(FAILURES)
    print("\n%s" % ("ALL PASS" if n == 0 else "FAILURES: %r" % FAILURES))
    return 1 if n else 0


def _make_trace_sample_dir(tmp, name, empty=False):
    sd = os.path.join(tmp, "sd-" + name)
    os.makedirs(os.path.join(sd, "evidence"), exist_ok=True)
    if empty:
        open(os.path.join(sd, "evidence", "ctrace.csv.gz"), "wb").close()
    else:
        with gzip.open(os.path.join(sd, "evidence", "ctrace.csv.gz"),
                       "wt") as f:
            f.write("# c\n" + "1,2\n" * 5)
    # every file listed in _obs_min's manifest must exist on disk
    with gzip.open(os.path.join(sd, "evidence", "msnap.csv.gz"),
                   "wt") as f:
        f.write("# m\n" + "3,4\n" * 5)
    return sd


if __name__ == "__main__":
    sys.exit(main())
