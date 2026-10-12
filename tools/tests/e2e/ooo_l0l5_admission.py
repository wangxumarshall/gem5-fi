#!/usr/bin/env python3
"""[OOO][P1] eng2 admission gate — machine assertions over the 8 eng2
samples (4 RunID x n=2) before any formal launch (L0-L5 run 2026-10-12;
plan Task 10, Subagent-C).

CLI: ooo_l0l5_admission.py --eng2-dirs <dir>... --goldens-dir G
       --guard-dir Gd [--frozen-gem5-sha S] [--frozen-chaos-commit C]
       [--repo R] [--out JSON] [--self-test]

Per sample (all six items must PASS; none is ever relaxed):
  1 identity   — gem5 sha == frozen; sha256(<repo>/<config path>) ==
                 identity.config.sha256; sha256(<repo>/<workload path>) ==
                 identity.workload.sha256 == the campaign yaml's declared
                 workload.binary_sha256; chaos_commit consistent with the
                 campaign yaml (and the frozen value when given);
  2 conservation — l5.conservation.ok AND the campaign ledger conserved
                 (five outcome classes + post-activation simulator
                 failures == activated total; reuses ooo_chain_audit);
  3 traces     — every ctrace/msnap evidence file exists and is readable
                 as a gz prefix (>0 lines) or honestly truncated;
  4 no-overwrite — samples/.staging empty; results.jsonl has no duplicate
                 run_id; every sample dir's identity.run_id == its dirname
                 and no file inside carries a foreign run-id pattern;
  5 replay     — determinism == "match" for every sample;
  6 observation — machine-parseable + files manifest re-hashed clean
                 (reuses ooo_chain_audit.audit_observation).

The goldens dir is verified for COMPLETE.json + registry-matching final
checksums. Output: per-item PASS/FAIL JSON (--out, default
/home/sdc/gem5-fi-ding/runs/ooo-l0l5/admission/admission_checks.json) for
the coordinator to merge into admission_handoff.json. Exit 0 iff 8/8
samples pass all items.
"""

import argparse
import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

import yaml

HERE = os.path.dirname(os.path.realpath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
TOOLS = os.path.join(REPO, "tools")
sys.path.insert(0, TOOLS)
sys.path.insert(0, HERE)
import ooo_chain_audit  # noqa: E402
import ooo_l0l5_e2e as e2e  # noqa: E402  (gzip readability + replay lookup)

DEFAULT_OUT = ("/home/sdc/gem5-fi-ding/runs/ooo-l0l5/admission/"
               "admission_checks.json")
SELFTEST_ROOT = os.environ.get(
    "OOO_ADMISSION_SELFTEST_ROOT",
    "/home/sdc/gem5-fi-ding/runs/ooo-l0l5/selftest/admission-selftest")
FROZEN_GEM5_SHA = ("1a618953b014514713c0ad98c7f3d69a48171d81f0463d934b"
                   "ccdfcfc0070bf3")

RUN_ID_RE = re.compile(r"^[A-Za-z0-9_.\-]+-c\d{4}-r\d{4}$")
RUN_ID_ANY_RE = re.compile(r"([A-Za-z0-9_.\-]+)-c(\d{4})-r(\d{4})")

FAILURES = []


def check(name, cond, detail=""):
    if cond:
        print("  PASS %s" % name)
    else:
        print("  FAIL %s %s" % (name, detail))
        FAILURES.append(name)


def sha256_file(path, _buf=1024 * 1024):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(_buf)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


# ------------------------------------------------------------- per-sample

def find_campaign_yaml(repo, campaign_id):
    p = os.path.join(repo, "campaigns", "ooo-l0l5",
                     campaign_id + ".yaml")
    return p if os.path.isfile(p) else None


def check_identity(repo, obs, campaign_yaml, frozen_gem5, frozen_chaos):
    fails = []
    ident = obs.get("identity", {})
    if frozen_gem5 and ident.get("gem5_sha256") != frozen_gem5:
        fails.append("gem5_sha_mismatch")
    cfg, wl = ident.get("config", {}), ident.get("workload", {})
    for label, blk in (("config", cfg), ("workload", wl)):
        p = blk.get("path")
        want = blk.get("sha256")
        if not p or not want:
            fails.append("%s_sha_missing" % label)
            continue
        disk = os.path.join(repo, p)
        if not os.path.isfile(disk):
            fails.append("%s_file_missing:%s" % (label, p))
        elif sha256_file(disk) != want:
            fails.append("%s_sha_mismatch:%s" % (label, p))
    if campaign_yaml:
        with open(campaign_yaml) as f:
            camp = yaml.safe_load(f)
        declared = (camp.get("workload") or {}).get("binary_sha256")
        if declared and declared != wl.get("sha256"):
            fails.append("workload_sha_differs_from_yaml_declared")
        ycc = camp.get("chaos_commit")
        if ycc and ident.get("chaos_commit") != ycc:
            fails.append("chaos_commit_differs_from_yaml")
        if frozen_chaos and ident.get("chaos_commit") != frozen_chaos:
            fails.append("chaos_commit_differs_from_frozen")
    else:
        fails.append("campaign_yaml_not_found")
    return fails


def check_no_overwrite(eng2_dir):
    """Campaign-level overwrite audit: staging residue, results.jsonl
    duplicate run_ids, per-sample dir ownership."""
    fails = []
    staging = os.path.join(eng2_dir, "samples", ".staging")
    if os.path.isdir(staging) and os.listdir(staging):
        fails.append("staging_residue:%d entries" % len(os.listdir(staging)))
    rl = os.path.join(eng2_dir, "results.jsonl")
    if os.path.isfile(rl):
        seen = {}
        with open(rl) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except ValueError:
                    fails.append("results_jsonl_unparseable_line")
                    continue
                rid = row.get("run_id")
                seen[rid] = seen.get(rid, 0) + 1
        dups = [r for r, n in seen.items() if n > 1]
        if dups:
            fails.append("results_jsonl_duplicate_run_id:%s" % dups)
    else:
        fails.append("results_jsonl_missing")
    return fails


def check_sample_dir_ownership(sample_dir, run_id):
    fails = []
    if os.path.basename(sample_dir) != run_id:
        fails.append("dir_name_mismatch:%s" % os.path.basename(sample_dir))
    for root, _dirs, files in os.walk(sample_dir):
        for fn in files:
            for m in RUN_ID_ANY_RE.finditer(fn):
                if m.group(0) != run_id:
                    fails.append("foreign_run_id_file:%s" % fn)
    return fails


def check_goldens_dir(goldens_dir, frozen_gem5=None):
    """Every golden dir must be COMPLETE with a registry-matching final
    checksum (golden_id lives in provenance.json) and, when given, the
    frozen gem5 sha."""
    fails = []
    if not os.path.isdir(goldens_dir):
        return ["goldens_dir_missing:%s" % goldens_dir], 0
    from runner import GOLDEN_IDS  # noqa: E402  (repo registry)
    n = 0
    for name in sorted(os.listdir(goldens_dir)):
        d = os.path.join(goldens_dir, name)
        if not os.path.isdir(d) or name == "specs":
            continue
        comp = os.path.join(d, "COMPLETE.json")
        if not os.path.isfile(comp):
            fails.append("golden_incomplete:%s" % name)
            continue
        with open(comp) as f:
            cj = json.load(f)
        final = cj.get("final") or cj.get("final_checksum")
        gid, prov_final = None, None
        prov = os.path.join(d, "provenance.json")
        if os.path.isfile(prov):
            try:
                with open(prov) as f:
                    pj = json.load(f)
                gid = (pj.get("spec") or {}).get("golden_id")
                prov_final = pj.get("final_checksum")
            except (ValueError, OSError):
                pass
        if prov_final and final and prov_final != final:
            fails.append("golden_provenance_final_mismatch:%s" % name)
        n += 1
        if frozen_gem5 and cj.get("gem5_sha256") \
                and cj["gem5_sha256"] != frozen_gem5:
            fails.append("golden_gem5_sha_mismatch:%s" % name)
        if gid and gid in GOLDEN_IDS and final != GOLDEN_IDS[gid]:
            fails.append("golden_final_mismatch:%s" % name)
    if n == 0:
        fails.append("goldens_dir_empty")
    return fails, n


# ------------------------------------------------------------ admission

def run_admission(eng2_dirs, goldens_dir, guard_dir, frozen_gem5,
                  frozen_chaos, repo, out_path, expect_samples=8):
    print("[admission] repo=%s guard=%s goldens=%s" % (repo, guard_dir,
                                                       goldens_dir))
    if frozen_gem5:
        got = sha256_file(os.path.join(repo, "build", "ARM", "gem5.opt")) \
            if os.path.isfile(os.path.join(repo, "build", "ARM",
                                           "gem5.opt")) else None
        if got != frozen_gem5:
            print("[admission] BLOCKED: gem5.opt identity drift (%r)" % got)
            return 2
    report = {"tool": "ooo_l0l5_admission",
              "frozen_gem5_sha": frozen_gem5,
              "frozen_chaos_commit": frozen_chaos,
              "eng2_dirs": [os.path.abspath(d) for d in eng2_dirs],
              "expect_samples": expect_samples,
              "samples": [], "items": {}}
    gfails, n_goldens = check_goldens_dir(goldens_dir, frozen_gem5)
    report["goldens"] = {"n_complete": n_goldens, "failures": gfails}

    total_samples = 0
    item_fails = {k: [] for k in ("identity", "conservation", "traces",
                                  "no_overwrite", "replay", "observation")}
    for eng2_dir in eng2_dirs:
        eng2_dir = os.path.abspath(eng2_dir)
        campaign_id = os.path.basename(eng2_dir)
        camp_yaml = find_campaign_yaml(repo, campaign_id)
        print("[admission] eng2 dir %s (yaml=%s)" % (eng2_dir, camp_yaml))
        ow_fails = check_no_overwrite(eng2_dir)
        for f in ow_fails:
            item_fails["no_overwrite"].append("%s:%s" % (campaign_id, f))
        # campaign ledger (conservation) via the audit library
        try:
            rollup = ooo_chain_audit.audit_campaign(
                eng2_dir, frozen_gem5_sha=frozen_gem5)
            if not rollup["conservation"]["conserved"]:
                item_fails["conservation"].append(
                    "%s:ledger %s" % (campaign_id,
                                      json.dumps(
                                          rollup["conservation"])))
        except ooo_chain_audit.AuditError as e:
            item_fails["observation"].append("%s:%s" % (campaign_id, e))
            rollup = None
        sample_dirs = sorted(
            d for d in glob.glob(os.path.join(eng2_dir, "samples", "*"))
            if os.path.isdir(d) and not os.path.basename(d).startswith(".")
            and os.path.basename(d) != "QUARANTINE")
        for sd in sample_dirs:
            total_samples += 1
            entry = {"sample_dir": sd, "campaign_id": campaign_id}
            opath = os.path.join(sd, "observation.json")
            try:
                with open(opath) as f:
                    obs = json.load(f)
            except (ValueError, OSError) as e:
                entry["observation"] = ["unloadable:%s" % e]
                item_fails["observation"].append("%s" % sd)
                report["samples"].append(entry)
                continue
            run_id = obs.get("identity", {}).get("run_id") \
                or os.path.basename(sd)
            entry["run_id"] = run_id

            idf = check_identity(repo, obs, camp_yaml, frozen_gem5,
                                 frozen_chaos)
            entry["identity"] = idf
            for f in idf:
                item_fails["identity"].append("%s:%s" % (run_id, f))

            cons = obs.get("l5", {}).get("conservation")
            cf = [] if (isinstance(cons, dict) and cons.get("ok") is True) \
                else ["l5_conservation_not_ok"]
            entry["conservation"] = cf
            item_fails["conservation"].extend(
                "%s:%s" % (run_id, f) for f in cf)

            tf = e2e.trace_evidence_readable(obs, sd)
            entry["traces"] = tf
            item_fails["traces"].extend("%s:%s" % (run_id, f) for f in tf)

            of = check_sample_dir_ownership(sd, run_id)
            entry["no_overwrite"] = of
            item_fails["no_overwrite"].extend(
                "%s:%s" % (run_id, f) for f in of)

            det = e2e.replay_determinism(obs)
            entry["replay"] = det
            if det != "match":
                item_fails["replay"].append("%s:%s" % (run_id, det))

            rec = ooo_chain_audit.audit_observation(
                obs, sd, frozen_gem5_sha=frozen_gem5)
            entry["observation"] = rec["violations"]
            item_fails["observation"].extend(
                "%s:%s" % (run_id, v) for v in rec["violations"])
            report["samples"].append(entry)

    report["n_samples"] = total_samples
    report["items"] = {k: ({"status": "PASS"} if not v
                           else {"status": "FAIL", "failures": v})
                       for k, v in item_fails.items()}
    report["goldens"]["status"] = "PASS" if not gfails else "FAIL"
    ok = (total_samples == expect_samples
          and not any(item_fails.values()) and not gfails)
    report["overall"] = "PASS" if ok else "FAIL"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(report, f, indent=1, ensure_ascii=False)
    print("[admission] samples=%d goldens_complete=%d" % (total_samples,
                                                          n_goldens))
    for k, v in report["items"].items():
        print("[admission] item %-13s %s" % (k, v["status"]))
    print("[admission] item %-13s %s" % ("goldens",
                                         report["goldens"]["status"]))
    print("[admission] OVERALL: %s -> %s" % (report["overall"], out_path))
    return 0 if ok else 1


# ------------------------------------------------------------- self-test

FIXTURE_GEM5 = FROZEN_GEM5_SHA


def _mk_fixture_repo(tmp):
    """A tiny repo tree: campaigns/ooo-l0l5/*.yaml + the config/workload
    files the fixture observations reference (real files, real shas) +
    build/ARM/gem5.opt symlinked to the REAL frozen binary (read-only
    link; its sha256 is the frozen value, so the identity precheck
    exercises the genuine path)."""
    repo = os.path.join(tmp, "repo")
    os.makedirs(os.path.join(repo, "campaigns", "ooo-l0l5"))
    os.makedirs(os.path.join(repo, "configs", "se"))
    os.makedirs(os.path.join(repo, "workloads", "ooo", "smoke"))
    os.makedirs(os.path.join(repo, "build", "ARM"))
    real_gem5 = os.path.join(REPO, "build", "ARM", "gem5.opt")
    if os.path.isfile(real_gem5):
        os.symlink(os.path.realpath(real_gem5),
                   os.path.join(repo, "build", "ARM", "gem5.opt"))
    cfg = os.path.join(repo, "configs", "se", "proxy.py")
    with open(cfg, "w") as f:
        f.write("# fixture config\n")
    wl = os.path.join(repo, "workloads", "ooo", "smoke", "smoke")
    with open(wl, "w") as f:
        f.write("# fixture workload elf\n")
    return repo, sha256_file(cfg), sha256_file(wl)


def _mk_eng2_obs(run_id, seed, cfg_sha, wl_sha, chaos="frozencommithash",
                 classification="Masked"):
    inactive = classification == "Inactive"
    obs = {
        "schema_version": "ooo-observation/v1",
        "identity": {
            "run_id": run_id, "campaign_id": run_id.rsplit("-c", 1)[0],
            "runid_row": "D01-F0-W6-c", "submodel": "decode",
            "sample_index": 0, "phase": "eng2", "seed": seed,
            "manifest_sha256": "ab" * 32, "gem5_sha256": FIXTURE_GEM5,
            "config": {"path": "configs/se/proxy.py", "sha256": cfg_sha},
            "workload": {"path": "workloads/ooo/smoke/smoke",
                         "sha256": wl_sha, "golden_id": "smoke-golden-v1"},
            "golden_key": "k" * 24, "chaos_commit": chaos,
            "patchset_sha256": "ff" * 32, "pythonhashseed": 0,
            "host": "huawei0201", "started": "t0", "finished": "t1",
            "wall_s": 1.0,
        },
        "l0": {"injected": 0 if inactive else 1,
               "activated": 0 if inactive else 1,
               "events": [] if inactive else [{"tick": 1}],
               "skip_lines": 2, "eligible_count": 5, "attempted": None,
               "log_sha256": "11" * 32},
        "l1": {"status": "inactive_no_activation" if inactive else "ok",
               "micro_diff": None if inactive else {"x": 1},
               "first_divergence": None, "files": ["evidence/micro.json"]},
        "l2": {"status": "inactive_no_activation" if inactive else "ok",
               "coverage": {"mode": "full"}, "commit_diff": None if
               inactive else {"verdict": "no_divergence",
                              "primary_class": None},
               "first_divergent_commit": None,
               "files": []},
        "l3": {"status": "inactive_no_activation" if inactive
               else "unsupported", "method": None, "fanout": None,
               "caveat": None, "reason": None if inactive else
               "commit trace records dest regs only"},
        "l4": {"status": "inactive_no_activation" if inactive else "ok",
               "first_detection": None, "latency_from_l0": None,
               "oracle": {"kind": "exact_hash", "golden": "g",
                          "observed": "g", "match": True}},
        "l5": {"classification": classification, "reason": "fixture",
               "exit": 0, "timed_out": False,
               "faults_injected": 0 if inactive else 1,
               "checksum_observed": "g", "checksum_golden": "g",
               "detector": None, "conservation": {"ok": True}},
        "violations": [],
        "chain_complete": inactive,
        "chain_gaps": [] if inactive else ["L3"],
        # canonical top-level replay (integration adjudication 2026-10-12)
        "replay": {"performed": True, "determinism": "match",
                   "pass2_classification": None, "verdict_pass2": None,
                   "checksum_pass2": None, "performed_at": "t1"},
        "files": {},
        "coverage_scope": {"mode": "full"},
        "audit": {"built_at": "t1", "builder_sha256": "22" * 32},
    }
    return obs


def _install_eng2_sample(eng2_dir, obs, cfg_sha, wl_sha, drift=False,
                         replay=None):
    sdir = os.path.join(eng2_dir, "samples", obs["identity"]["run_id"])
    os.makedirs(os.path.join(sdir, "evidence"), exist_ok=True)
    files = {"evidence/decode_chaos.log": "Tick: 1, faults_injected: 1\n",
             "evidence/micro.json": "{}\n", "runner.stdout": "R\n"}
    if replay:
        # canonical top-level position (integration adjudication)
        obs["replay"] = {"determinism": replay}
    manifest = {}
    for rel, content in files.items():
        p = os.path.join(sdir, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            f.write(content)
        manifest[rel] = sha256_file(p)
    import gzip as _gz
    with _gz.open(os.path.join(sdir, "evidence", "ctrace.csv.gz"),
                  "wt") as f:
        f.write("# t\n" + "1,2\n" * 10)
    with _gz.open(os.path.join(sdir, "evidence", "msnap.csv.gz"),
                  "wt") as f:
        f.write("# m\n" + "3,4\n" * 10)
    manifest["evidence/ctrace.csv.gz"] = sha256_file(
        os.path.join(sdir, "evidence", "ctrace.csv.gz"))
    manifest["evidence/msnap.csv.gz"] = sha256_file(
        os.path.join(sdir, "evidence", "msnap.csv.gz"))
    obs["files"] = manifest
    with open(os.path.join(sdir, "observation.json"), "w") as f:
        json.dump(obs, f, indent=1)
    if drift:  # flip one byte AFTER the sha was recorded
        with open(os.path.join(sdir, "evidence", "decode_chaos.log"),
                  "a") as f:
            f.write("X")
    return sdir


def _mk_goldens(root):
    """Fixture goldens dir shaped like ooo_golden.py's real layout:
    COMPLETE.json {key,final,gem5_sha256,completed} + provenance.json
    (spec.golden_id, final_checksum)."""
    gd = os.path.join(root, "goldens")
    key = "a" * 24
    d = os.path.join(gd, key)
    os.makedirs(d)
    with open(os.path.join(d, "COMPLETE.json"), "w") as f:
        json.dump({"key": key, "final": "45737cc9a76c0dce",
                   "gem5_sha256": FIXTURE_GEM5,
                   "completed": "2026-10-12T00:00:00"}, f)
    with open(os.path.join(d, "provenance.json"), "w") as f:
        json.dump({"key": key,
                   "spec": {"golden_id": "smoke-golden-v1"},
                   "final_checksum": "45737cc9a76c0dce"}, f)
    return gd


def _run_admission_cli(repo, eng2_dirs, goldens, out, expect=4):
    cmd = [sys.executable, os.path.realpath(__file__),
           "--eng2-dirs"] + eng2_dirs + [
        "--goldens-dir", goldens, "--guard-dir",
        os.path.join(os.path.dirname(goldens), "guard"),
        "--frozen-gem5-sha", FIXTURE_GEM5,
        "--frozen-chaos-commit", "frozencommithash",
        "--expect-samples", str(expect),
        "--repo", repo, "--out", out]
    return subprocess.run(cmd, capture_output=True, text=True,
                          errors="replace", timeout=120)


def self_test():
    global SELFTEST_ROOT
    os.makedirs(SELFTEST_ROOT, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="admission-selftest-", dir=SELFTEST_ROOT)
    SELFTEST_ROOT = tmp
    try:
        return _self_test_body(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _self_test_body(tmp):
    print("[self-test] happy path: 2 eng2 dirs x 2 samples, all items PASS")
    repo, cfg_sha, wl_sha = _mk_fixture_repo(tmp)
    root = os.path.join(tmp, "runs")
    goldens = _mk_goldens(root)
    dirs = []
    for cid in ("eng2_D01-F0-W6-c", "eng2_D02-F0-W6-b"):
        d = os.path.join(root, cid)
        os.makedirs(os.path.join(d, "samples"))
        with open(os.path.join(repo, "campaigns", "ooo-l0l5",
                               cid + ".yaml"), "w") as f:
            yaml.safe_dump({"campaign_id": cid,
                            "workload": {"binary_sha256": wl_sha},
                            "chaos_commit": "frozencommithash"}, f)
        for rep, cls in ((0, "Masked"), (1, "Inactive")):
            rid = "%s-c0000-r%04d" % (cid, rep)
            obs = _mk_eng2_obs(rid, 52000000 + rep, cfg_sha, wl_sha,
                               classification=cls)
            _install_eng2_sample(d, obs, cfg_sha, wl_sha)
        with open(os.path.join(d, "results.jsonl"), "w") as f:
            f.write(json.dumps({"run_id": "%s-c0000-r0000" % cid}) + "\n")
            f.write(json.dumps({"run_id": "%s-c0000-r0001" % cid}) + "\n")
        dirs.append(d)
    out = os.path.join(tmp, "admission_happy.json")
    r = _run_admission_cli(repo, dirs, goldens, out)
    check("happy-exit0", r.returncode == 0,
          "rc=%d %s" % (r.returncode, r.stdout[-400:]))
    with open(out) as f:
        rep = json.load(f)
    check("happy-overall-pass", rep["overall"] == "PASS")
    check("happy-4-samples-fixture",
          rep["n_samples"] == 4 and rep["expect_samples"] == 4,
          "n=%d" % rep["n_samples"])
    check("happy-all-items-pass",
          all(rep["items"][k]["status"] == "PASS" for k in rep["items"]))

    print("[self-test] negatives (each must FAIL its item)")

    def fresh_negative(name):
        d = os.path.join(root, name)
        if os.path.exists(d):
            shutil.rmtree(d)
        os.makedirs(os.path.join(d, "samples"))
        with open(os.path.join(repo, "campaigns", "ooo-l0l5",
                               name + ".yaml"), "w") as f:
            yaml.safe_dump({"campaign_id": name,
                            "workload": {"binary_sha256": wl_sha},
                            "chaos_commit": "frozencommithash"}, f)
        rid = "%s-c0000-r0000" % name
        obs = _mk_eng2_obs(rid, 77, cfg_sha, wl_sha)
        return d, obs

    # duplicate run_id in results.jsonl
    d, obs = fresh_negative("eng2_neg_dup")
    _install_eng2_sample(d, obs, cfg_sha, wl_sha)
    with open(os.path.join(d, "results.jsonl"), "w") as f:
        f.write(json.dumps({"run_id": "eng2_neg_dup-c0000-r0000"}) + "\n")
        f.write(json.dumps({"run_id": "eng2_neg_dup-c0000-r0000"}) + "\n")
    out = os.path.join(tmp, "neg_dup.json")
    r = _run_admission_cli(repo, [d], goldens, out)
    with open(out) as f:
        rep = json.load(f)
    check("neg-dup-results-fails", rep["items"]["no_overwrite"]["status"]
          == "FAIL" and any("duplicate_run_id" in x for x in
                            rep["items"]["no_overwrite"]["failures"]))

    # .staging residue
    d, obs = fresh_negative("eng2_neg_staging")
    _install_eng2_sample(d, obs, cfg_sha, wl_sha)
    os.makedirs(os.path.join(d, "samples", ".staging", "leftover.p9"))
    with open(os.path.join(d, "results.jsonl"), "w") as f:
        f.write(json.dumps({"run_id": "eng2_neg_staging-c0000-r0000"}) + "\n")
    out = os.path.join(tmp, "neg_staging.json")
    _run_admission_cli(repo, [d], goldens, out)
    with open(out) as f:
        rep = json.load(f)
    check("neg-staging-fails", rep["items"]["no_overwrite"]["status"]
          == "FAIL" and any("staging_residue" in x for x in
                            rep["items"]["no_overwrite"]["failures"]))

    # replay mismatch
    d, obs = fresh_negative("eng2_neg_replay")
    _install_eng2_sample(d, obs, cfg_sha, wl_sha, replay="mismatch")
    with open(os.path.join(d, "results.jsonl"), "w") as f:
        f.write(json.dumps({"run_id": "eng2_neg_replay-c0000-r0000"}) + "\n")
    out = os.path.join(tmp, "neg_replay.json")
    _run_admission_cli(repo, [d], goldens, out)
    with open(out) as f:
        rep = json.load(f)
    check("neg-replay-fails", rep["items"]["replay"]["status"] == "FAIL")

    # files sha drift
    d, obs = fresh_negative("eng2_neg_drift")
    _install_eng2_sample(d, obs, cfg_sha, wl_sha, drift=True)
    with open(os.path.join(d, "results.jsonl"), "w") as f:
        f.write(json.dumps({"run_id": "eng2_neg_drift-c0000-r0000"}) + "\n")
    out = os.path.join(tmp, "neg_drift.json")
    _run_admission_cli(repo, [d], goldens, out)
    with open(out) as f:
        rep = json.load(f)
    check("neg-drift-fails-observation",
          rep["items"]["observation"]["status"] == "FAIL")

    # chaos_commit mismatch vs yaml
    d, obs = fresh_negative("eng2_neg_cc")
    obs["identity"]["chaos_commit"] = "OTHER"
    _install_eng2_sample(d, obs, cfg_sha, wl_sha)
    with open(os.path.join(d, "results.jsonl"), "w") as f:
        f.write(json.dumps({"run_id": "eng2_neg_cc-c0000-r0000"}) + "\n")
    out = os.path.join(tmp, "neg_cc.json")
    _run_admission_cli(repo, [d], goldens, out)
    with open(out) as f:
        rep = json.load(f)
    check("neg-chaos-commit-fails",
          rep["items"]["identity"]["status"] == "FAIL"
          and any("chaos_commit" in x for x in
                  rep["items"]["identity"]["failures"]))

    # gem5 sha mismatch
    d, obs = fresh_negative("eng2_neg_gem5")
    obs["identity"]["gem5_sha256"] = "dead" * 16
    _install_eng2_sample(d, obs, cfg_sha, wl_sha)
    with open(os.path.join(d, "results.jsonl"), "w") as f:
        f.write(json.dumps({"run_id": "eng2_neg_gem5-c0000-r0000"}) + "\n")
    out = os.path.join(tmp, "neg_gem5.json")
    _run_admission_cli(repo, [d], goldens, out)
    with open(out) as f:
        rep = json.load(f)
    check("neg-gem5-sha-fails",
          rep["items"]["identity"]["status"] == "FAIL"
          and any("gem5_sha_mismatch" in x for x in
                  rep["items"]["identity"]["failures"]))

    n = len(FAILURES)
    print("\n%s" % ("ALL PASS" if n == 0 else "FAILURES: %r" % FAILURES))
    return 1 if n else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--eng2-dirs", nargs="+", default=None)
    ap.add_argument("--goldens-dir", default=None)
    ap.add_argument("--guard-dir",
                    default="/home/sdc/gem5-fi-ding/runs/ooo-l0l5/guard")
    ap.add_argument("--frozen-gem5-sha", default=FROZEN_GEM5_SHA)
    ap.add_argument("--frozen-chaos-commit", default=None)
    ap.add_argument("--repo", default=REPO)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--expect-samples", type=int, default=8,
                    help="the real eng2 gate is 8 (4 RunID x n=2)")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if not args.eng2_dirs or not args.goldens_dir:
        ap.error("--eng2-dirs and --goldens-dir are required "
                 "(or use --self-test)")
    return run_admission(args.eng2_dirs, args.goldens_dir, args.guard_dir,
                         args.frozen_gem5_sha, args.frozen_chaos_commit,
                         args.repo, args.out,
                         expect_samples=args.expect_samples)


if __name__ == "__main__":
    sys.exit(main())
