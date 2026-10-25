#!/usr/bin/env python3
"""Frequency-policy overlay contract test."""
import json, sys
from pathlib import Path
REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
import lsu_freq_policy as P

fails = []
def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else f"  <- {detail}"))
    if not cond: fails.append(name)

def test_policy_covers_all_runids():
    pol = P.load_policy()
    ids = {e["run_id"] for e in pol["entries"]}
    rm = json.loads((REPO/"docs/gem5-fi/lsu/mdspec/runid_map.json").read_text("utf-8"))
    check("policy_covers_325", len(rm["entries"]) == 325 and all(e["run_id"] in ids for e in rm["entries"]))
    check("f6_is_64", sum(1 for e in pol["entries"] if e["frequency"]=="F6" and not e.get("legacy")) == 64)

def test_campaign_refuses_redundant_and_seed2():
    import lsu_campaign as LC
    pol = P.load_policy()
    # every redundant F6 refuses
    red = [e["run_id"] for e in pol["entries"] if e["run_policy"] == "STRESS_REDUNDANT" and not e["legacy"]]
    check("redundant_exist", len(red) == 25)
    import lsu_freq_policy as FP
    bad = [r for r in red if FP.query(pol, r, 1)["decision"] != "REFUSE_STRESS_REDUNDANT"]
    check("all_redundant_refused", not bad, str(bad[:5]))
    # representative seed2 is not-required, seed1 allowed
    check("rep_seed1_allow", FP.query(pol, "T04-F6-W4", 1)["decision"] == "ALLOW_STRESS_ONLY")
    check("rep_seed2_not_required", FP.query(pol, "T04-F6-W4", 2)["decision"] == "POLICY_NOT_REQUIRED")
    # the campaign must expose the gate
    check("campaign_has_gate", hasattr(LC, "policy_decision"))

def test_policy_decision_gate_semantics():
    """[R6-FREQPOLICY] the ruled gate semantics through the campaign's own
    policy_decision (not just the raw query): the loud opt-in, the
    never-permits, and the optional-overlay degradation."""
    import lsu_campaign as LC
    if not hasattr(LC, "policy_decision"):
        check("gate_present", False, "lsu_campaign.policy_decision 缺失")
        return
    check("gate_present", True)
    pol = P.load_policy()
    red = next(e["run_id"] for e in pol["entries"]
               if e["run_policy"] == "STRESS_REDUNDANT" and not e["legacy"])
    norm = next(e["run_id"] for e in pol["entries"] if e["run_policy"] == "NORMAL")

    def refused(fn):
        try:
            fn()
            return False
        except SystemExit as e:
            return str(e).startswith("[R6-FREQPOLICY]")

    check("normal_seed1_allow", LC.policy_decision(norm, 1) == "ALLOW")
    check("normal_seed4_refused", refused(lambda: LC.policy_decision(norm, 4)))
    # representative F6 seed1 needs the loud opt-in
    check("rep_seed1_refused_without_flag",
          refused(lambda: LC.policy_decision("T04-F6-W4", 1)))
    check("rep_seed1_allowed_with_flag",
          LC.policy_decision("T04-F6-W4", 1, allow_stress_only=True) == "ALLOW_STRESS_ONLY")
    # --allow-stress-only never permits seed>1, never unblocks STRESS_REDUNDANT
    check("rep_seed2_refused_even_with_flag",
          refused(lambda: LC.policy_decision("T04-F6-W4", 2, allow_stress_only=True)))
    check("redundant_refused_even_with_flag",
          refused(lambda: LC.policy_decision(red, 1, allow_stress_only=True)))
    # overlay optional: missing module / missing JSON never block a NORMAL run
    _orig = LC._FP
    try:
        LC._FP = None
        check("module_missing_allow", LC.policy_decision(norm, 1) == "ALLOW")
        class _NoJSON:
            @staticmethod
            def load_policy():
                raise FileNotFoundError("R6-FREQUENCY-POLICY.json")
        LC._FP = _NoJSON
        check("json_missing_allow", LC.policy_decision(norm, 1) == "ALLOW")
    finally:
        LC._FP = _orig
    # unknown runid: an F6 tier refuses (no ungoverned stress run); a
    # non-F6 synthetic id (test/toy fixtures) runs ungated.
    check("unknown_f6_refused", refused(lambda: LC.policy_decision("X09-F6-W1", 1)))
    check("unknown_nonf6_allow", LC.policy_decision("X01-F0-W1", 1) == "ALLOW")

def test_scheduler_all_excludes_redundant():
    """[R6-FREQPOLICY] lsu_r6_schedule.sh must drop schedule_enabled=false cells
    from --cells all AND from an explicit --cells list, with one visible drop
    line per RunID, while schedule_enabled=true cells stay selected.

    The live ready_contract.json (post R6-RECONCILE 110b96aa) has gate={} and 0
    READY rows, so --cells all against it dies at the binary check before any
    selection exists. The scheduler is therefore driven through a fixture
    contract built from REAL contract rows whose statuses mirror the
    pre-RECONCILE READY set (A04-F6-W3 — STRESS_REDUNDANT, schedule_enabled=
    false — was genuinely READY then and leaked into --cells all). Without a
    selectable disabled cell this test would be vacuous."""
    import subprocess, tempfile, os, shutil
    pol = P.load_policy()
    sched = {e["run_id"]: e for e in pol["entries"]}
    con = json.loads((REPO / "docs/gem5-fi/lsu/mdspec/ready_contract.json").read_text("utf-8"))
    rows = {e["run_id"]: e for e in con["entries"]}

    KEEP = ["A01-F0-W3", "T04-F6-W4"]   # NORMAL / STRESS_ONLY rep -> schedule_enabled=true
    DROP = ["A04-F6-W3", "A06-F6-W5"]   # STRESS_REDUNDANT -> schedule_enabled=false
    HELD = ["T01-F0-W4"]                # contract-BLOCKED control (policy would allow it)
    check("sched_fixture_policy_keeps",
          all(sched[r].get("schedule_enabled") is True for r in KEEP),
          str([(r, sched[r].get("schedule_enabled")) for r in KEEP]))
    check("sched_fixture_policy_drops",
          all(sched[r].get("schedule_enabled") is False for r in DROP),
          str([(r, sched[r].get("schedule_enabled")) for r in DROP]))

    binpath = REPO / "CHAOS" / "gem5" / "build" / "ARM" / "gem5.opt"
    if not (binpath.exists() and os.access(binpath, os.X_OK)):
        check("sched_fixture_binary", False, "missing executable %s" % binpath)
        return
    binsha = subprocess.run(["sha256sum", str(binpath)],
                            capture_output=True, text=True).stdout.split()[0]
    entries = []
    for rid in KEEP + DROP:
        e = dict(rows[rid]); e["status"] = "READY"; entries.append(e)
    for rid in HELD:                      # stays contract-BLOCKED
        entries.append(dict(rows[rid]))
    fixture = {
        "source": "tests/test_lsu_freq_policy.py::test_scheduler_all_excludes_redundant "
                  "(REAL contract rows; READY set mirrors pre-R6-RECONCILE state)",
        "total": len(entries),
        "status": {"READY": len(KEEP) + len(DROP), "BLOCKED": len(HELD)},
        "seeds_per_cell": 1, "max_parallel": 1,
        "formal_outdir": "runs/lsu/r6_freqpolicy_t3_fixture",
        "fs_checkpoint": con["fs_checkpoint"],
        "gate": {"binary": str(binpath), "binary_sha256": binsha},
        "verdict": {"formal_phase": "screening", "screening_target": 385,
                    "focus_target": 2401, "focus_runids": []},
        "entries": entries,
    }
    RUNROOT = "/home/sdc/gem5-fi-ding/runs/lsu/r6_freqpolicy_t3_fixture"  # script refuses runroot outside runs/lsu

    def sched_dry(cells):
        shutil.rmtree(RUNROOT, ignore_errors=True)   # no stale plan.tsv can mask a failure
        with tempfile.TemporaryDirectory() as td:
            cpath = os.path.join(td, "fixture_contract.json")
            with open(cpath, "w") as f:
                json.dump(fixture, f, ensure_ascii=False)
            r = subprocess.run(["bash", str(REPO / "tools" / "lsu_r6_schedule.sh"),
                                "--contract", cpath, "--runroot", RUNROOT,
                                "--cells", cells, "--dry-run"],
                               capture_output=True, text=True, cwd=str(REPO))
        plan = os.path.join(RUNROOT, "plan.tsv")
        plan_ids = ([l.split("\t")[0] for l in open(plan).read().splitlines() if l.strip()]
                    if os.path.isfile(plan) else None)
        return r, plan_ids

    r, plan_ids = sched_dry("all")
    check("scheduler_all_dryrun_ok", r.returncode == 0, (r.stderr or r.stdout)[-300:])
    if r.returncode != 0:
        return
    check("scheduler_all_excludes_disabled",
          plan_ids is not None and not (set(DROP) & set(plan_ids)),
          str(sorted(set(DROP) & set(plan_ids or []))))
    check("scheduler_all_drop_lines_visible",
          all(("[R6-FREQPOLICY] drop %s: schedule_enabled=false" % rid) in r.stdout
              for rid in DROP),
          r.stdout[-400:])
    check("scheduler_all_keeps_enabled",
          set(KEEP) <= set(plan_ids or []), str(plan_ids))
    check("scheduler_all_blocked_still_held",
          not (set(HELD) & set(plan_ids or [])), str(plan_ids))

    # ruling: a MANUALLY listed schedule_enabled=false cell is dropped, not silently run
    r2, plan_ids2 = sched_dry(",".join(["A01-F0-W3"] + DROP))
    check("scheduler_explicit_dryrun_ok", r2.returncode == 0, (r2.stderr or r2.stdout)[-300:])
    if r2.returncode != 0:
        return
    check("scheduler_explicit_drops_disabled", plan_ids2 == ["A01-F0-W3"], str(plan_ids2))
    check("scheduler_explicit_drop_line_visible",
          all(("[R6-FREQPOLICY] drop %s: schedule_enabled=false" % rid) in r2.stdout
              for rid in DROP),
          r2.stdout[-400:])

def test_runner_manifest_carries_policy():
    """[R6-FREQPOLICY] lsu_runner.build_manifest must carry the frequency
    policy (run_policy/required_seeds/include_in_statistics) read from the
    overlay — the runner never re-derives the rule. Real signature is
    build_manifest(item_id, phase, sample_index, ...): ITEM-054 -> T04-F6-W4
    (representative F6), ITEM-041 -> T01-F0-W4 (NORMAL)."""
    import lsu_runner as LR
    m = LR.build_manifest("ITEM-054", "pilot", 0)          # T04-F6-W4
    check("manifest_stress_run_id", m.get("run_id") == "T04-F6-W4", str(m.get("run_id")))
    check("manifest_run_policy", m.get("run_policy") == "STRESS_ONLY", str(m.get("run_policy")))
    check("manifest_required_seeds", m.get("required_seeds") == 1, str(m.get("required_seeds")))
    check("manifest_stress_not_in_stats", m.get("include_in_statistics") is False,
          str(m.get("include_in_statistics")))
    m2 = LR.build_manifest("ITEM-041", "pilot", 0)         # T01-F0-W4
    check("manifest_normal_run_id", m2.get("run_id") == "T01-F0-W4", str(m2.get("run_id")))
    check("manifest_normal_policy", m2.get("run_policy") == "NORMAL", str(m2.get("run_policy")))
    check("manifest_normal_seeds", m2.get("required_seeds") == 3, str(m2.get("required_seeds")))
    check("manifest_normal_in_stats", m2.get("include_in_statistics") is True,
          str(m2.get("include_in_statistics")))
    # UNKNOWN_RUNID: query() returns a SHORT dict with no run_policy key —
    # the manifest must degrade to "UNKNOWN" and still freeze, never crash.
    _orig_query = P.query
    try:
        P.query = lambda pol, rid, seed: {"run_id": rid, "seed": seed,
                                          "decision": "UNKNOWN_RUNID"}
        m3 = LR.build_manifest("ITEM-054", "pilot", 0)
        check("manifest_unknown_runid_degrades",
              m3.get("run_policy") == "UNKNOWN", str(m3.get("run_policy")))
    finally:
        P.query = _orig_query
    # overlay unavailable (policy JSON missing): the manifest must still be
    # produced (no run_policy key, or "UNKNOWN") — never an exception.
    _orig_load = P.load_policy
    try:
        def _no_json(*a, **k):
            raise FileNotFoundError("R6-FREQUENCY-POLICY.json")
        P.load_policy = _no_json
        m4 = LR.build_manifest("ITEM-054", "pilot", 0)
        check("manifest_overlay_optional",
              m4.get("run_id") == "T04-F6-W4"
              and ("run_policy" not in m4 or m4.get("run_policy") == "UNKNOWN"),
              str(m4.get("run_policy")))
    finally:
        P.load_policy = _orig_load

def main():
    test_policy_covers_all_runids()
    test_campaign_refuses_redundant_and_seed2()
    test_policy_decision_gate_semantics()
    test_scheduler_all_excludes_redundant()
    test_runner_manifest_carries_policy()
    print(f"\n{'ALL PASS' if not fails else 'FAILED (%d): %s' % (len(fails), fails)}")
    return 0 if not fails else 1

if __name__ == "__main__":
    sys.exit(main())
