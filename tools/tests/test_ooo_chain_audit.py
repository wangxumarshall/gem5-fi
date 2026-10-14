#!/usr/bin/env python3
"""[OOO][P1] unit test for tools/ooo_chain_audit.py (L0-L5 run, 2026-10-12;
semantic-gate hardening 2026-10-13, Fix-C Task 1/3).

Twelve hand-built fixtures against the ooo-observation/v1 contract (the
audit object). No gem5, no network — synthetic campaign dirs under the
sanctioned selftest area (NEVER /tmp).

  1. legal activated Masked sample with a FULL chain (l3 ok + proxy
     fanout, funnel recorded, snaps recorded) -> audits clean;
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
     -> audits clean; campaign rollup nine-class counts correct;
  9. activated>0 + l3.status=unsupported -> semantic-gate violation
     l3_unsupported_with_activation (the admission-view chain hole the
     four formal campaigns carry 100%); activated==0 must NOT fire;
 10. l0.attempted/eligible_count null without a limited reason ->
     l0_funnel_missing; a documented funnel_limited_reason is the legal
     escape hatch (no violation);
 11. verdict=diverged + run_instructions=0 -> the empty-trace FAKE
     divergence (l2_diverged_zero_instructions +
     first_divergence_from_empty_trace); run_instructions>0 with the same
     shape stays clean (honest partial trace);
 12. l1.status=ok + snaps_run=0 -> l1_valid_zero_snaps; l1.status=
     truncated + snaps_run=0 (honest crash record) stays clean.

Plus the offline correction-audit subcommand fixture (legacy-shaped
campaign -> quantified correction summary in correction_audit.json) and
CLI edge cases: nonexistent dir -> exit 1; empty samples/ -> exit 1;
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
             l2_primary_class=None, l3_status="ok",
             l4_detector=None, checksum_observed=SMOKE_GOLDEN,
             exit_code=0, submodel="decode"):
    """A schema-conformant ooo-observation/v1 dict under the STRICT
    contract (Fix-C 2026-10-13): the default happy path carries a full
    chain — l3 ok + proxy fanout, a recorded L0 funnel (attempted and
    eligible_count are ints), l1 ok with snaps_run>0, and a commit_diff
    that records run_instructions. Fixtures mutate single fields
    afterwards to build the negatives."""
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
        "run_instructions": 3000071,
        "aligned_pairs": 3000071,
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
            "observer_tool_commit": "cf9729bdf4846241a2637b71d431dfdd42"
                                   "fb2269",
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
            "attempted": 17 if activated else 0,
            "log_sha256": "11" * 32,
        },
        "l1": {
            "status": l1_status,
            "micro_diff": ({"first_divergence_snap": None,
                            "rat_divergences": 0,
                            "snaps_run": 11121}
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
        # canonical replay position: TOP-LEVEL (integration adjudication
        # 2026-10-12; see ooo_chain_audit.REQUIRED_TOP)
        "replay": {"performed": True, "determinism": "match",
                   "pass2_classification": classification,
                   "verdict_pass2": None, "checksum_pass2": None,
                   "performed_at": "2026-10-12T10:00:42"},
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
    print("[fixture 1] legal activated Masked with a FULL chain (strict "
          "contract: l3 ok, funnel recorded, snaps recorded)")
    d = fresh_campaign("f1-legal")
    obs = make_obs("e2e_fixture-c0000-r0000", 20261013)
    install_sample(d, obs)
    res = audit.audit_campaign(d)
    s = res["samples"][0]
    check("f1-not-invalid", s["violations"] == [], repr(s["violations"]))
    check("f1-classification", s["classification"] == "Masked")
    check("f1-chain-complete-true", s["chain_complete"] is True)
    check("f1-no-gaps", s["chain_gaps"] == [])
    check("f1-rollup-no-gaps", res["gaps_by_level"] == {})
    check("f1-rollout-n-invalid", res["n_invalid"] == 0)
    check("f1-l3-unsupported-count", res["n_l3_unsupported_gap"] == 0)
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


def test_fixture9_l3_unsupported_with_activation():
    print("[fixture 9] activated>0 + l3 unsupported -> admission-view "
          "chain-hole violation")
    d = fresh_campaign("f9-l3-gap")
    obs = make_obs("e2e_fixture-c0000-r0000", 20261013,
                   l3_status="unsupported")
    install_sample(d, obs)
    res = audit.audit_campaign(d)
    v = res["samples"][0]["violations"]
    check("f9-l3-unsupported-with-activation",
          "l3_unsupported_with_activation" in v, repr(v))
    check("f9-gaps-still-counted", res["gaps_by_level"].get("L3") == 1)
    check("f9-not-honest-only", res["n_l3_unsupported_gap"] == 0)
    check("f9-invalid", res["n_invalid"] == 1)
    r = run_cli(d, require_complete=True)
    check("f9-cli-require-complete-exit1", r.returncode == 1,
          f"rc={r.returncode}")
    # scope: activated==0 must NOT fire the gate (Inactive samples are
    # not in the admission gate's scope)
    obs2 = make_obs("e2e_fixture-c0000-r0001", 20261014,
                    classification="Inactive")
    obs2["l3"]["status"] = "unsupported"
    obs2["l3"]["reason"] = "no source-read association (scope fixture)"
    obs2["chain_complete"] = False
    obs2["chain_gaps"] = ["L3"]
    d2 = fresh_campaign("f9-scope")
    install_sample(d2, obs2)
    v2 = audit.audit_campaign(d2)["samples"][0]["violations"]
    check("f9-activated0-not-gated",
          "l3_unsupported_with_activation" not in v2, repr(v2))


def test_fixture10_l0_funnel_missing():
    print("[fixture 10] attempted/eligible null -> l0_funnel_missing")
    d = fresh_campaign("f10-funnel")
    obs = make_obs("e2e_fixture-c0000-r0000", 20261013)
    obs["l0"]["attempted"] = None  # eligible_count stays 17
    install_sample(d, obs)
    v = audit.audit_campaign(d)["samples"][0]["violations"]
    check("f10-attempted-null-flagged", "l0_funnel_missing" in v, repr(v))
    # legal limited reason (documented forward path) must NOT fire
    obs2 = make_obs("e2e_fixture-c0000-r0000", 20261013)
    obs2["l0"]["attempted"] = None
    obs2["l0"]["eligible_count"] = None
    obs2["l0"]["funnel_limited_reason"] = (
        "injector has no eligible/attempted counter source (documented)")
    d2 = fresh_campaign("f10-limited")
    install_sample(d2, obs2)
    v2 = audit.audit_campaign(d2)["samples"][0]["violations"]
    check("f10-limited-reason-clean", "l0_funnel_missing" not in v2,
          repr(v2))


def test_fixture11_fake_divergence():
    print("[fixture 11] diverged + run_instructions=0 -> empty-trace "
          "FAKE divergence")
    d = fresh_campaign("f11-fake-div")
    obs = make_obs("e2e_fixture-c0000-r0000", 20261013,
                   classification="Crash", l2_status="ok",
                   l2_verdict="diverged",
                   l2_primary_class="instruction_flow_change")
    obs["l2"]["commit_diff"]["run_instructions"] = 0
    obs["l2"]["commit_diff"]["aligned_pairs"] = 0
    obs["l2"]["commit_diff"]["first_divergence"] = {
        "seq": 0, "class": "instruction_flow_change", "level": "presence",
        "detail": "seq 0 only in ref (run side missing)",
        "ref_line": "0,0,73535,400d00,nop,0", "run_line": None}
    obs["l2"]["first_divergent_commit"] = \
        obs["l2"]["commit_diff"]["first_divergence"]
    install_sample(d, obs)
    v = audit.audit_campaign(d)["samples"][0]["violations"]
    check("f11-zero-instr-diverged-flagged",
          "l2_diverged_zero_instructions" in v
          and "first_divergence_from_empty_trace" in v, repr(v))
    r = run_cli(d, require_complete=True)
    check("f11-cli-require-complete-exit1", r.returncode == 1,
          f"rc={r.returncode}")
    # control: same shape but a REAL partial trace (run_instructions>0)
    # is the honest pre-crash observation and must stay clean
    obs2 = make_obs("e2e_fixture-c0000-r0000", 20261013,
                    classification="Crash", l2_status="ok",
                    l2_verdict="diverged",
                    l2_primary_class="instruction_flow_change")
    obs2["l2"]["commit_diff"]["run_instructions"] = 2297
    obs2["l2"]["commit_diff"]["aligned_pairs"] = 2297
    obs2["l2"]["commit_diff"]["first_divergence"] = {
        "seq": 5, "class": "instruction_flow_change", "level": "presence",
        "detail": "real prefix divergence", "ref_line": "x", "run_line": "y"}
    obs2["l2"]["first_divergent_commit"] = \
        obs2["l2"]["commit_diff"]["first_divergence"]
    d2 = fresh_campaign("f11-real-partial")
    install_sample(d2, obs2)
    v2 = audit.audit_campaign(d2)["samples"][0]["violations"]
    check("f11-real-partial-clean",
          "l2_diverged_zero_instructions" not in v2
          and "first_divergence_from_empty_trace" not in v2, repr(v2))


def test_fixture12_l1_zero_snaps():
    print("[fixture 12] l1 ok + snaps_run=0 -> l1_valid_zero_snaps")
    d = fresh_campaign("f12-zero-snaps")
    obs = make_obs("e2e_fixture-c0000-r0000", 20261013)
    obs["l1"]["micro_diff"]["snaps_run"] = 0
    install_sample(d, obs)
    v = audit.audit_campaign(d)["samples"][0]["violations"]
    check("f12-ok-zero-snaps-flagged", "l1_valid_zero_snaps" in v, repr(v))
    # honest truncated crash record with zero snaps must stay clean
    obs2 = make_obs("e2e_fixture-c0000-r0000", 20261013,
                    classification="Crash", l2_status="truncated",
                    l2_verdict="truncated_no_divergence_in_prefix")
    obs2["l1"]["status"] = "truncated"
    obs2["l1"]["micro_diff"]["snaps_run"] = 0
    d2 = fresh_campaign("f12-honest-truncated")
    install_sample(d2, obs2)
    v2 = audit.audit_campaign(d2)["samples"][0]["violations"]
    check("f12-truncated-zero-snaps-clean", "l1_valid_zero_snaps" not in v2,
          repr(v2))


def test_fixture13_l3_not_observed_before_crash():
    """[FIX-RB] the zero-byte crash-trace L3 marker: a legal status, an
    honest gap-L3 basis ONLY with a non-empty reason, and the gap must
    be recorded (the must-record rule extends to the new status -- the
    gate gets stricter, never looser)."""
    print("[fixture 13] l3 not_observed_before_crash semantics")
    d = fresh_campaign("f13-l3-nob")
    obs = make_obs("e2e_fixture-c0000-r0000", 20261013,
                   classification="Crash",
                   l2_status="not_observed_before_crash",
                   l2_verdict="truncated_no_divergence_in_prefix",
                   l3_status="not_observed_before_crash")
    obs["l3"]["method"] = None
    obs["l3"]["fanout"] = None
    obs["l3"]["caveat"] = None
    obs["l3"]["reason"] = ("retained commit trace is zero bytes: the run "
                           "crashed before the first trace flush")
    obs["l1"]["status"] = "no_snapshots_before_crash"
    obs["chain_complete"] = False
    obs["chain_gaps"] = ["L1", "L2", "L3"]
    install_sample(d, obs)
    v = audit.audit_campaign(d)["samples"][0]["violations"]
    check("f13-nob-with-reason-clean",
          "l3_status_invalid" not in v
          and "gap_l3_without_basis" not in v
          and "l3_not_observed_without_reason" not in v
          and "l3_gap_not_recorded" not in v, repr(v))
    # without a reason -> the basis rule fires
    obs2 = json.loads(json.dumps(obs))
    obs2["l3"]["reason"] = None
    d2 = fresh_campaign("f13-nob-noreason")
    install_sample(d2, obs2)
    v2 = audit.audit_campaign(d2)["samples"][0]["violations"]
    check("f13-nob-without-reason-flagged",
          "l3_not_observed_without_reason" in v2, repr(v2))
    # gap L3 not recorded -> the must-record rule fires
    obs3 = json.loads(json.dumps(obs))
    obs3["chain_gaps"] = ["L1", "L2"]
    obs3["chain_complete"] = False
    d3 = fresh_campaign("f13-nob-nogap")
    install_sample(d3, obs3)
    v3 = audit.audit_campaign(d3)["samples"][0]["violations"]
    check("f13-nob-gap-not-recorded-flagged",
          "l3_gap_not_recorded" in v3, repr(v3))


def test_fixture14_l4_latency_without_detection():
    """[FIX-RB round 2] no detection event (kind null) but numeric
    latency -> mandatory FAIL; with the event + non-negative latency ->
    clean; nulls under no event -> clean."""
    print("[fixture 14] l4 latency without detection")
    d = fresh_campaign("f14-lat-noevent")
    obs = make_obs("e2e_fixture-c0000-r0000", 20261013)  # Masked
    obs["l4"]["first_detection"] = dict(kind=None, detector=None,
                                        tick=None, seq=None, note="none")
    obs["l4"]["latency_from_l0"] = dict(ticks=-416955,
                                        committed_insts=24, note="")
    install_sample(d, obs)
    v = audit.audit_campaign(d)["samples"][0]["violations"]
    check("f14-noevent-numeric-latency-flagged",
          "l4_latency_without_detection" in v
          and "l4_negative_latency" in v, repr(v))
    # same shape with honest nulls -> clean of the new rules
    d2 = fresh_campaign("f14-lat-nulls")
    obs2 = json.loads(json.dumps(obs))
    obs2["l4"]["latency_from_l0"] = dict(ticks=None,
                                         committed_insts=None, note="")
    install_sample(d2, obs2)
    v2 = audit.audit_campaign(d2)["samples"][0]["violations"]
    check("f14-noevent-null-latency-clean",
          "l4_latency_without_detection" not in v2
          and "l4_negative_latency" not in v2, repr(v2))
    # a REAL detection event with a positive latency -> clean
    d3 = fresh_campaign("f14-lat-real-event")
    obs3 = make_obs("e2e_fixture-c0000-r0000", 20261013,
                    classification="SDC",
                    l2_status="ok", l2_verdict="diverged",
                    l2_primary_class="data_corruption")
    obs3["l4"]["first_detection"] = dict(
        kind="checksum_mismatch", detector="Application",
        tick=12669580, seq=5798, note="real")
    obs3["l4"]["latency_from_l0"] = dict(ticks=2731810,
                                         committed_insts=1144, note="")
    install_sample(d3, obs3)
    v3 = audit.audit_campaign(d3)["samples"][0]["violations"]
    check("f14-real-event-positive-latency-clean",
          "l4_latency_without_detection" not in v3
          and "l4_negative_latency" not in v3, repr(v3))
    # real event but NEGATIVE latency -> flagged
    d4 = fresh_campaign("f14-lat-negative")
    obs4 = json.loads(json.dumps(obs3))
    obs4["l4"]["latency_from_l0"] = dict(ticks=-9933770,
                                         committed_insts=None, note="")
    install_sample(d4, obs4)
    v4 = audit.audit_campaign(d4)["samples"][0]["violations"]
    check("f14-negative-latency-flagged",
          "l4_negative_latency" in v4, repr(v4))


def test_fixture15_l3_zero_scan_masquerade():
    """[FIX-RB round 2] an activated ok source_read chain with a located
    source, zero hops and zero rows scanned = "did not scan" masquerading
    as "scanned, no consumers" -> semantic gate FAIL; the same shape
    WITH scan evidence (rows>0, terminal_reason) is clean; the
    never-committed terminal state (source_row null) records its gap
    without a basis violation."""
    print("[fixture 15] l3 zero-scan masquerade")
    import ooo_chain_audit as oca
    base = {"l0": {"activated": 1, "attempted": 1, "eligible_count": None,
                   "limited_reason": "x", "status": "ok"},
            "l1": {"status": "ok", "micro_diff": {"snaps_run": 3}},
            "l2": {"status": "ok", "commit_diff": {
                "verdict": "diverged", "run_instructions": 100}},
            "l4": {"status": "none_detected",
                   "first_detection": {"kind": None, "detector": None,
                                       "tick": None, "seq": None,
                                       "note": ""},
                   "latency_from_l0": {"ticks": None,
                                       "committed_insts": None}}}
    zero_scan = dict(base, l3={"status": "ok", "method": "source_read",
                               "source_row": {"seq": 103,
                                              "seqencNum": 159},
                               "hops": [], "rows_scanned_after_source": 0})
    check("f15-zero-scan-gate-fires",
          "l3_zero_scan_masquerade" in oca.semantic_gate_violations(
              zero_scan),
          repr(oca.semantic_gate_violations(zero_scan)))
    scanned = dict(base, l3={"status": "ok", "method": "source_read",
                             "source_row": {"seq": 103,
                                            "seqencNum": 159},
                             "hops": [], "rows_scanned_after_source": 42,
                             "scan_range": {"first_seq": 104,
                                            "last_seq": 146},
                             "terminal_reason": "trace ended"})
    check("f15-scanned-no-consumer-clean",
          "l3_zero_scan_masquerade" not in
          oca.semantic_gate_violations(scanned),
          repr(oca.semantic_gate_violations(scanned)))
    never = dict(base, l3={"status": "ok", "method": "source_read",
                           "source_row": None, "hops": [],
                           "rows_scanned_after_source": None,
                           "caveat": "never committed"})
    check("f15-never-committed-no-masquerade",
          "l3_zero_scan_masquerade" not in
          oca.semantic_gate_violations(never),
          repr(oca.semantic_gate_violations(never)))
    # chain_completeness (producer side) agrees: zero-scan -> gap L3;
    # scanned / never-committed shapes handled by their own states
    import ooo_observation as oooobs
    cc_zero = oooobs.chain_completeness(
        dict(zero_scan, l5={"classification": "Masked",
                            "conservation": {"conserved": True,
                                             "activated": 1}}))
    check("f15-zero-scan-costs-gap-l3", "L3" in cc_zero[1], repr(cc_zero))
    cc_hops = oooobs.chain_completeness(
        dict(base, l3={"status": "ok", "method": "source_read",
                       "source_row": {"seq": 103, "seqencNum": 159},
                       "hops": [{"seq": 107}], "rows_scanned_after_source":
                       5},
             l5={"classification": "Masked",
                 "conservation": {"conserved": True, "activated": 1}}))
    check("f15-real-hop-chain-complete", cc_hops == (True, []),
          repr(cc_hops))
    # audit gap-basis: the never-committed ok chain records its gap
    # without a basis violation
    d = fresh_campaign("f15-never-committed")
    obs = make_obs("e2e_fixture-c0000-r0000", 20261013)
    obs["l3"] = {"status": "ok", "method": "source_read",
                 "source_row": None, "hops": [],
                 "rows_scanned_after_source": None,
                 "caveat": "injected DynInst never committed"}
    obs["chain_complete"] = False
    obs["chain_gaps"] = ["L3"]
    install_sample(d, obs)
    v = audit.audit_campaign(d)["samples"][0]["violations"]
    check("f15-never-committed-gap-basis-ok",
          "gap_l3_without_basis" not in v, repr(v))


def test_correction_audit():
    print("[correction-audit] legacy-shaped campaign -> quantified "
          "correction report")
    d = fresh_campaign("corr-audit")
    # one legacy Masked sample (l3 unsupported, funnel null) + one
    # fake-divergence Crash (empty run trace): the exact shapes the
    # four formal campaigns carry
    obs1 = make_obs("e2e_fixture-c0000-r0000", 20261013,
                    l3_status="unsupported")
    obs1["l0"]["attempted"] = None
    install_sample(d, obs1)
    obs2 = make_obs("e2e_fixture-c0000-r0001", 20261014,
                    classification="Crash", l2_status="ok",
                    l2_verdict="diverged",
                    l2_primary_class="instruction_flow_change",
                    l3_status="unsupported")
    obs2["l0"]["attempted"] = None  # legacy funnel hole, same as obs1
    obs2["l2"]["commit_diff"]["run_instructions"] = 0
    obs2["l2"]["commit_diff"]["first_divergence"] = {
        "seq": 0, "class": "instruction_flow_change", "level": "presence",
        "detail": "seq 0 only in ref (run side missing)",
        "ref_line": "0,0,73535,400d00,nop,0", "run_line": None}
    obs2["l2"]["first_divergent_commit"] = \
        obs2["l2"]["commit_diff"]["first_divergence"]
    install_sample(d, obs2)
    with open(os.path.join(d, "results.jsonl"), "w") as f:
        f.write(json.dumps({"run_id": "e2e_fixture-c0000-r0000"}) + "\n")
        f.write(json.dumps({"run_id": "e2e_fixture-c0000-r0001"}) + "\n")
    out = os.path.join(d, "correction_audit.json")
    r = subprocess.run([sys.executable, TOOL, "correction-audit",
                        "--campaign-dir", d], capture_output=True,
                       text=True, errors="replace", timeout=120)
    check("corr-cli-exit0", r.returncode == 0,
          f"rc={r.returncode} {r.stdout[-200:]}{r.stderr[-200:]}")
    with open(out) as f:
        rep = json.load(f)
    s = rep["summary"]
    check("corr-summary-counts",
          s["n"] == 2 and s["semantic_invalid"] == 2
          and s["l3_unsupported"] == 2 and s["l0_funnel_missing"] == 2
          and s["fake_divergence_count"] == 1
          and s["first_divergence_from_empty_trace"] == 1,
          json.dumps(s))
    check("corr-backfill-required",
          s["chain_backfill_required"] is True
          and s["chain_complete_count"] == 0
          and s["execution_complete_count"] == 2
          and s["evidence_readable_count"] == 2, json.dumps(s))
    ps = {p["run_id"]: p for p in rep["per_sample"]}
    check("corr-per-sample-flag",
          ps["e2e_fixture-c0000-r0001"]["l2_zero_trace_fake_divergence"]
          is True
          and ps["e2e_fixture-c0000-r0000"]
          ["l2_zero_trace_fake_divergence"] is False,
          json.dumps(rep["per_sample"], ensure_ascii=False))
    check("corr-classifications-recorded",
          ps["e2e_fixture-c0000-r0001"]["classification"] == "Crash")
    # originals untouched: the only artifact is correction_audit.json
    check("corr-originals-untouched",
          os.path.exists(os.path.join(d, "samples", "e2e_fixture-c0000"
                                      "-r0000", "observation.json"))
          and sorted(x for x in os.listdir(d) if x != "samples")
          == ["correction_audit.json", "results.jsonl"],
          str(os.listdir(d)))
    # a campaign with a full chain must report backfill NOT required
    d2 = fresh_campaign("corr-clean")
    install_sample(d2, make_obs("e2e_fixture-c0000-r0000", 20261013))
    with open(os.path.join(d2, "results.jsonl"), "w") as f:
        f.write(json.dumps({"run_id": "e2e_fixture-c0000-r0000"}) + "\n")
    r2 = subprocess.run([sys.executable, TOOL, "correction-audit",
                         "--campaign-dir", d2], capture_output=True,
                        text=True, errors="replace", timeout=120)
    with open(os.path.join(d2, "correction_audit.json")) as f:
        s2 = json.load(f)["summary"]
    check("corr-clean-no-backfill",
          r2.returncode == 0 and s2["chain_backfill_required"] is False
          and s2["semantic_invalid"] == 0 and s2["n"] == 1, json.dumps(s2))


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
        test_fixture9_l3_unsupported_with_activation()
        test_fixture10_l0_funnel_missing()
        test_fixture11_fake_divergence()
        test_fixture12_l1_zero_snaps()
        test_fixture13_l3_not_observed_before_crash()
        test_fixture14_l4_latency_without_detection()
        test_fixture15_l3_zero_scan_masquerade()
        test_correction_audit()
        test_cli_edges()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    n = len(FAILURES)
    print(f"\n{'ALL PASS' if n == 0 else 'FAILURES: ' + repr(FAILURES)}")
    sys.exit(1 if n else 0)


if __name__ == "__main__":
    main()
