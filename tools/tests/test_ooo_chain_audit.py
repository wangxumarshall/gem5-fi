#!/usr/bin/env python3
"""[OOO][P1] unit test for tools/ooo_chain_audit.py (L0-L5 run, 2026-10-12).

Eight hand-built fixtures against the ooo-observation/v1 contract (the
audit object). No gem5, no network — synthetic campaign dirs under the
sanctioned selftest area (NEVER /tmp).

  1. legal decode-activated Masked sample (l3 unsupported, chain_complete
     false, gaps=["L3"]) -> audits clean, NOT invalid (the L3 gap is an
     honest record, counted separately, never "invalid");
  2. missing l1 key -> missing_layers contains L1 (+ violation, exit 1
     under --require-complete);
  3. Crash sample with l2.status==ok AND commit_diff.verdict==no_divergence
     -> violation crash_claimed_no_divergence;
  4. duplicate run_id across two samples -> violation duplicate_run_id;
  5. files sha drift (one byte flipped in a referenced file) -> violation
     file_sha_mismatch;
  6. identity.gem5_sha256 != --frozen-gem5-sha -> violation gem5_sha_mismatch;
  7. inactive sample (L1-L4 = inactive_no_activation) -> audits clean;
  8. SDC sample (detector=Application, l2 first divergence ⑤data_corruption)
     -> audits clean; campaign rollup nine-class counts correct.

Plus CLI edge cases: nonexistent dir -> exit 1; empty samples/ -> exit 1;
--require-complete exit codes per fixture class.

Run: python3 tools/tests/test_ooo_chain_audit.py
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.realpath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
TOOL = os.path.join(REPO, "tools", "ooo_chain_audit.py")
SELFTEST_ROOT = os.environ.get(
    "OOO_SELFTEST_ROOT",
    "/home/sdc/gem5-fi-ding/runs/ooo-l0l5/selftest/chain-audit-test")

FROZEN_GEM5 = "1a618953b014514713c0ad98c7f3d69a48171d81f0463d934bccdfcfc0070bf3"
OTHER_GEM5 = "deadbeef" * 8
SMOKE_GOLDEN = "45737cc9a76c0dce"

sys.path.insert(0, os.path.join(REPO, "tools"))
import ooo_chain_audit as audit  # noqa: E402

FAILURES = []


def check(name, cond, detail=""):
    if cond:
        print(f"  PASS {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILURES.append(name)


# ---------------------------------------------------------------- fixtures

def make_obs(run_id, seed, classification="Masked", activated=1,
             gem5_sha=FROZEN_GEM5,
             l2_status="ok", l2_verdict="no_divergence",
             l2_primary_class=None, l3_status="unsupported",
             l4_detector=None, checksum_observed=SMOKE_GOLDEN,
             exit_code=0, submodel="decode"):
    """A schema-conformant ooo-observation/v1 dict (the happy path for the
    given classification); fixtures mutate single fields afterwards."""
    inactive = classification == "Inactive"
    if inactive:
        activated = 0
    if classification == "SDC":
        checksum_observed = "0f0f0f0f0f0f0f0f"
    if classification == "Crash":
        exit_code = -6
        checksum_observed = None
    injected = 1 if activated else 0
    l1_status = "inactive_no_activation" if inactive else "ok"
    l2s = "inactive_no_activation" if inactive else l2_status
    l3s = "inactive_no_activation" if inactive else l3_status
    l4s = "inactive_no_activation" if inactive else "ok"
    first_detection = None if (inactive or l4_detector is None) else {
        "kind": "checksum_mismatch" if classification == "SDC" else "n/a",
        "detector": l4_detector,
        "tick": 423115 if not inactive else None,
        "seq": None,
        "note": "fixture",
    }
    commit_diff = None if inactive else {
        "tool": "commit_diff",
        "verdict": l2_verdict,
        "primary_class": l2_primary_class,
        "latency_seq": None,
        "first_divergence": ({
            "seq": 4102, "class": l2_primary_class,
            "class_zh": "⑤数据损坏"} if l2_primary_class else None),
        "divergence_counts": {},
        "run_truncated": classification in ("Crash", "Hang"),
    }
    obs = {
        "schema_version": "ooo-observation/v1",
        "identity": {
            "run_id": run_id,
            "campaign_id": "e2e_fixture",
            "runid_row": "E2E-FIX",
            "submodel": submodel,
            "sample_index": 0,
            "phase": "e2e",
            "seed": seed,
            "manifest_sha256": "ab" * 32,
            "gem5_sha256": gem5_sha,
            "config": {"path": "configs/se/ooo_proxy.py",
                       "sha256": "cd" * 32},
            "workload": {"path": "workloads/ooo/smoke/smoke",
                         "sha256": "ef" * 32,
                         "golden_id": "smoke-golden-v1"},
            "golden_key": "fixturegoldenkey0000000000",
            "chaos_commit": "fixturecommit",
            "patchset_sha256": "ff" * 32,
            "pythonhashseed": 0,
            "host": "huawei0201",
            "started": "2026-10-12T10:00:00",
            "finished": "2026-10-12T10:00:42",
            "wall_s": 42.0,
        },
        "l0": {
            "injected": injected,
            "activated": activated,
            "events": ([{"tick": 423115, "site": "fetch_decode",
                         "faults_injected": 1}] if activated else []),
            "skip_lines": 0 if activated else 2,
            "eligible_count": 17,
            "attempted": None,
            "log_sha256": "11" * 32,
        },
        "l1": {
            "status": l1_status,
            "micro_diff": ({"first_divergence_snap": None,
                            "rat_divergences": 0}
                           if not inactive else None),
            "first_divergence": None,
            "files": ["evidence/micro_diff.json"],
        },
        "l2": {
            "status": l2s,
            "coverage": {"mode": "full", "seq_lo": None, "seq_hi": None,
                         "note": "fixture full"},
            "commit_diff": commit_diff,
            "first_divergent_commit": (commit_diff or {}).get(
                "first_divergence"),
            "replay": {"determinism": "match", "pass2_classification":
                       classification},
            "files": ["evidence/commit_diff.json"],
        },
        "l3": {
            "status": l3s,
            "method": "proxy" if l3s == "ok" else None,
            "fanout": {"upper_bound": 3} if l3s == "ok" else None,
            "caveat": "PRF liveness proxy upper bound" if l3s == "ok"
                      else None,
            "reason": None if l3s == "ok" else (
                "commit trace records dest regs only; source-read/"
                "dynamic-instruction association not implemented for "
                "decode; PRF liveness proxy not applicable"),
        },
        "l4": {
            "status": l4s,
            "first_detection": first_detection,
            "latency_from_l0": None,
            "oracle": {"kind": "exact_hash", "golden": SMOKE_GOLDEN,
                       "observed": checksum_observed,
                       "match": checksum_observed == SMOKE_GOLDEN},
        },
        "l5": {
            "classification": classification,
            "reason": "fixture",
            "exit": exit_code,
            "timed_out": False,
            "faults_injected": injected,
            "checksum_observed": checksum_observed,
            "checksum_golden": SMOKE_GOLDEN,
            "detector": l4_detector,
            "conservation": {"ok": True},
        },
        "violations": [],
        "chain_complete": inactive or l3s != "unsupported",
        "chain_gaps": [] if (inactive or l3s != "unsupported") else ["L3"],
        "files": {},
        "coverage_scope": {"mode": "full", "seq_lo": None, "seq_hi": None,
                           "pruned": False, "note": "fixture"},
        "audit": {"built_at": "2026-10-12T10:00:42",
                  "builder_sha256": "22" * 32},
    }
    return obs


def install_sample(campaign_dir, obs, extra_files=None, dir_name=None):
    """Write samples/<identity.run_id>/observation.json plus every file the
    observation references (real content, real sha256 in obs['files']).
    dir_name overrides the on-disk sample dir (fixture 4 needs two dirs
    carrying the same identity.run_id)."""
    run_id = dir_name or obs["identity"]["run_id"]
    sdir = os.path.join(campaign_dir, "samples", run_id)
    os.makedirs(sdir, exist_ok=True)
    files = {
        "evidence/decode_chaos.log": "Tick: 423115, Site: fetch_decode, "
                                     "faults_injected: 1\n",
        "evidence/micro_diff.json": '{"fixture": true}\n',
        "evidence/commit_diff.json": '{"fixture": true}\n',
        "runner.stdout": "RESULT: fixture\n",
    }
    if extra_files:
        files.update(extra_files)
    manifest = {}
    for rel, content in files.items():
        p = os.path.join(sdir, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            f.write(content)
        manifest[rel] = audit.sha256_file(p)
    obs["files"] = manifest
    with open(os.path.join(sdir, "observation.json"), "w") as f:
        json.dump(obs, f, indent=1)
    return sdir


def fresh_campaign(name):
    root = os.path.join(SELFTEST_ROOT, name)
    if os.path.exists(root):
        shutil.rmtree(root)
    os.makedirs(os.path.join(root, "samples"))
    return root


def run_cli(campaign_dir, require_complete=False, frozen=None):
    cmd = [sys.executable, TOOL, "audit", "--campaign-dir", campaign_dir]
    if require_complete:
        cmd.append("--require-complete")
    if frozen:
        cmd += ["--frozen-gem5-sha", frozen]
    return subprocess.run(cmd, capture_output=True, text=True,
                          errors="replace", timeout=120)


# ------------------------------------------------------------------ tests

def test_fixture1_legal_decode_masked():
    print("[fixture 1] legal decode-activated Masked (L3 unsupported gap)")
    d = fresh_campaign("f1-legal")
    obs = make_obs("e2e_fixture-c0000-r0000", 20261013)
    install_sample(d, obs)
    res = audit.audit_campaign(d)
    s = res["samples"][0]
    check("f1-not-invalid", s["violations"] == [], repr(s["violations"]))
    check("f1-classification", s["classification"] == "Masked")
    check("f1-chain-complete-false", s["chain_complete"] is False)
    check("f1-gaps-L3", s["chain_gaps"] == ["L3"])
    check("f1-rollup-gaps-L3", res["gaps_by_level"].get("L3") == 1)
    check("f1-rollout-n-invalid", res["n_invalid"] == 0)
    check("f1-l3-unsupported-count", res["n_l3_unsupported_gap"] == 1)
    r = run_cli(d, require_complete=True)
    check("f1-cli-require-complete-exit0", r.returncode == 0,
          f"rc={r.returncode} {r.stdout[-200:]} {r.stderr[-200:]}")
    check("f1-chain-audit-json-written",
          os.path.exists(os.path.join(d, "chain_audit.json")))
    check("f1-chain-audit-md-written",
          os.path.exists(os.path.join(d, "chain_audit.md")))


def test_fixture2_missing_l1():
    print("[fixture 2] missing l1 key")
    d = fresh_campaign("f2-missing-l1")
    obs = make_obs("e2e_fixture-c0000-r0000", 20261013)
    del obs["l1"]
    install_sample(d, obs)
    res = audit.audit_campaign(d)
    s = res["samples"][0]
    check("f2-missing-layers-L1", "L1" in s["missing_layers"],
          repr(s["missing_layers"]))
    check("f2-has-violation", len(s["violations"]) > 0,
          repr(s["violations"]))
    r = run_cli(d, require_complete=True)
    check("f2-cli-exit1", r.returncode == 1, f"rc={r.returncode}")
    r0 = run_cli(d)
    check("f2-cli-no-require-exit0", r0.returncode == 0,
          f"rc={r0.returncode}")


def test_fixture3_crash_no_divergence():
    print("[fixture 3] Crash + l2 ok + verdict no_divergence (false claim)")
    d = fresh_campaign("f3-crash-false")
    obs = make_obs("e2e_fixture-c0000-r0000", 20261012,
                   classification="Crash", l2_status="ok",
                   l2_verdict="no_divergence")
    install_sample(d, obs)
    res = audit.audit_campaign(d)
    s = res["samples"][0]
    check("f3-violation-crash-claimed",
          "crash_claimed_no_divergence" in s["violations"],
          repr(s["violations"]))
    check("f3-invalid", len(s["violations"]) > 0)
    r = run_cli(d, require_complete=True)
    check("f3-cli-exit1", r.returncode == 1, f"rc={r.returncode}")
    # honest variants must NOT trip the violation:
    for status in ("not_observed_before_crash", "truncated"):
        d2 = fresh_campaign("f3-honest-" + status)
        obs2 = make_obs("e2e_fixture-c0000-r0000", 20261012,
                        classification="Crash", l2_status=status,
                        l2_verdict="truncated_no_divergence_in_prefix")
        install_sample(d2, obs2)
        res2 = audit.audit_campaign(d2)
        v = res2["samples"][0]["violations"]
        check("f3-honest-%s-clean" % status,
              "crash_claimed_no_divergence" not in v, repr(v))
    d3 = fresh_campaign("f3-crash-diverged-ok")
    obs3 = make_obs("e2e_fixture-c0000-r0000", 20261012,
                    classification="Crash", l2_status="ok",
                    l2_verdict="diverged",
                    l2_primary_class="instruction_substitution")
    install_sample(d3, obs3)
    res3 = audit.audit_campaign(d3)
    v3 = res3["samples"][0]["violations"]
    check("f3-crash-ok-diverged-clean",
          "crash_claimed_no_divergence" not in v3
          and "crash_l2_status_ok_without_divergence" not in v3, repr(v3))


def test_fixture4_duplicate_run_id():
    print("[fixture 4] duplicate run_id (and seed)")
    d = fresh_campaign("f4-dup")
    install_sample(d, make_obs("e2e_fixture-c0000-r0000", 20261013),
                   dir_name="dup-first")
    install_sample(d, make_obs("e2e_fixture-c0000-r0000", 20261013),
                   dir_name="dup-second")
    res = audit.audit_campaign(d)
    dupd = [s for s in res["samples"]
            if "duplicate_run_id" in s["violations"]]
    check("f4-duplicate-run-id-flagged", len(dupd) >= 1,
          json.dumps(res["samples"], ensure_ascii=False))
    check("f4-rollup-dup-run-ids",
          res["duplicate_run_ids"] == ["e2e_fixture-c0000-r0000"],
          repr(res["duplicate_run_ids"]))
    r = run_cli(d, require_complete=True)
    check("f4-cli-exit1", r.returncode == 1, f"rc={r.returncode}")


def test_fixture5_files_sha_drift():
    print("[fixture 5] files sha drift (one byte)")
    d = fresh_campaign("f5-drift")
    obs = make_obs("e2e_fixture-c0000-r0000", 20261013)
    sdir = install_sample(d, obs)
    target = os.path.join(sdir, "evidence", "decode_chaos.log")
    with open(target, "a") as f:
        f.write("X")  # one-byte drift AFTER the sha was recorded
    res = audit.audit_campaign(d)
    s = res["samples"][0]
    check("f5-sha-mismatch-flagged",
          any(v.startswith("file_sha_mismatch") for v in s["violations"]),
          repr(s["violations"]))
    # a referenced-but-missing file is also a violation
    d2 = fresh_campaign("f5-missing")
    obs2 = make_obs("e2e_fixture-c0000-r0000", 20261013)
    sdir2 = install_sample(d2, obs2)
    os.unlink(os.path.join(sdir2, "runner.stdout"))
    res2 = audit.audit_campaign(d2)
    v2 = res2["samples"][0]["violations"]
    check("f5-missing-file-flagged",
          any(v.startswith("file_missing") for v in v2), repr(v2))
    r = run_cli(d, require_complete=True)
    check("f5-cli-exit1", r.returncode == 1, f"rc={r.returncode}")


def test_fixture6_gem5_sha_mismatch():
    print("[fixture 6] identity.gem5_sha256 vs --frozen-gem5-sha")
    d = fresh_campaign("f6-sha")
    obs = make_obs("e2e_fixture-c0000-r0000", 20261013,
                   gem5_sha=OTHER_GEM5)
    install_sample(d, obs)
    res = audit.audit_campaign(d, frozen_gem5_sha=FROZEN_GEM5)
    s = res["samples"][0]
    check("f6-gem5-sha-mismatch", "gem5_sha_mismatch" in s["violations"],
          repr(s["violations"]))
    r = run_cli(d, require_complete=True, frozen=FROZEN_GEM5)
    check("f6-cli-exit1", r.returncode == 1, f"rc={r.returncode}")
    # same campaign WITHOUT the frozen flag must not flag (opt-in check)
    res2 = audit.audit_campaign(d)
    check("f6-no-flag-no-violation",
          "gem5_sha_mismatch" not in res2["samples"][0]["violations"])


def test_fixture7_inactive():
    print("[fixture 7] inactive sample (L1-L4 inactive_no_activation)")
    d = fresh_campaign("f7-inactive")
    obs = make_obs("e2e_fixture-c0000-r0000", 20261012,
                   classification="Inactive")
    install_sample(d, obs)
    res = audit.audit_campaign(d)
    s = res["samples"][0]
    check("f7-clean", s["violations"] == [], repr(s["violations"]))
    check("f7-chain-complete-true", s["chain_complete"] is True)
    check("f7-no-gaps", s["chain_gaps"] == [])
    r = run_cli(d, require_complete=True)
    check("f7-cli-exit0", r.returncode == 0, f"rc={r.returncode}")


def test_fixture8_sdc_rollup():
    print("[fixture 8] SDC sample + nine-class rollup over a mixed campaign")
    d = fresh_campaign("f8-sdc")
    install_sample(d, make_obs("e2e_fixture-c0000-r0000", 20261013,
                               classification="Masked"))
    install_sample(d, make_obs("e2e_fixture-c0000-r0001", 20261012,
                               classification="Inactive"))
    install_sample(d, make_obs("e2e_fixture-c0000-r0002", 20261600,
                               classification="SDC",
                               l2_verdict="diverged",
                               l2_primary_class="data_corruption",
                               l4_detector="Application",
                               submodel="rat"))
    res = audit.audit_campaign(d)
    check("f8-all-clean",
          all(s["violations"] == [] for s in res["samples"]),
          json.dumps(res["samples"], ensure_ascii=False))
    cc = res["classification_counts"]
    check("f8-nine-class-counts",
          cc.get("Masked") == 1 and cc.get("Inactive") == 1
          and cc.get("SDC") == 1, repr(cc))
    check("f8-conservation-ledger",
          res["conservation"]["activated_total"] == 2
          and res["conservation"]["five_outcome_sum"] == 2
          and res["conservation"]["conserved"] is True,
          repr(res["conservation"]))
    sdc = [s for s in res["samples"] if s["classification"] == "SDC"][0]
    check("f8-sdc-clean", sdc["violations"] == [], repr(sdc["violations"]))
    r = run_cli(d, require_complete=True)
    check("f8-cli-exit0", r.returncode == 0, f"rc={r.returncode}")
    # negative conservation: activated=1 but classification Inactive
    d2 = fresh_campaign("f8-conservation-negative")
    obs = make_obs("e2e_fixture-c0000-r0000", 20261013,
                   classification="Inactive")
    obs["l0"]["activated"] = 1  # inconsistent with Inactive
    obs["l0"]["injected"] = 1
    install_sample(d2, obs)
    res2 = audit.audit_campaign(d2)
    check("f8-conservation-negative-flagged",
          any("conservation" in v for v in res2["samples"][0]["violations"]),
          repr(res2["samples"][0]["violations"]))


def test_cli_edges():
    print("[CLI edges] missing dir / no samples / unparseable observation")
    r = run_cli("/nonexistent/dir/for/audit")
    check("edge-missing-dir-exit1", r.returncode == 1, f"rc={r.returncode}")
    d = fresh_campaign("edge-empty")
    r = run_cli(d)
    check("edge-empty-campaign-exit1", r.returncode == 1, f"rc={r.returncode}")
    d2 = fresh_campaign("edge-unparseable")
    sdir = os.path.join(d2, "samples", "e2e_fixture-c0000-r0000")
    os.makedirs(sdir)
    with open(os.path.join(sdir, "observation.json"), "w") as f:
        f.write("{not json")
    res = audit.audit_campaign(d2)
    s = res["samples"][0]
    check("edge-unparseable-all-missing", s["missing_layers"] == ["ALL"],
          repr(s["missing_layers"]))
    check("edge-unparseable-violation",
          "observation_unparseable" in s["violations"],
          repr(s["violations"]))
    r2 = run_cli(d2, require_complete=True)
    check("edge-unparseable-exit1", r2.returncode == 1, f"rc={r2.returncode}")
    # missing observation.json entirely
    d3 = fresh_campaign("edge-no-obs")
    os.makedirs(os.path.join(d3, "samples", "e2e_fixture-c0000-r0000"))
    res3 = audit.audit_campaign(d3)
    check("edge-no-obs-violation",
          "observation_unparseable" in res3["samples"][0]["violations"],
          repr(res3["samples"][0]["violations"]))
    r3 = run_cli(d3, require_complete=True)
    check("edge-no-obs-exit1", r3.returncode == 1, f"rc={r3.returncode}")


def main():
    global SELFTEST_ROOT  # redirected below: keep artifacts in the tmp dir
    os.makedirs(SELFTEST_ROOT, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="chain-audit-test-", dir=SELFTEST_ROOT)
    SELFTEST_ROOT = tmp
    try:
        test_fixture1_legal_decode_masked()
        test_fixture2_missing_l1()
        test_fixture3_crash_no_divergence()
        test_fixture4_duplicate_run_id()
        test_fixture5_files_sha_drift()
        test_fixture6_gem5_sha_mismatch()
        test_fixture7_inactive()
        test_fixture8_sdc_rollup()
        test_cli_edges()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    n = len(FAILURES)
    print(f"\n{'ALL PASS' if n == 0 else 'FAILURES: ' + repr(FAILURES)}")
    sys.exit(1 if n else 0)


if __name__ == "__main__":
    main()
