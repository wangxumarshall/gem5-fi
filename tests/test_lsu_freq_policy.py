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

def main():
    test_policy_covers_all_runids()
    test_campaign_refuses_redundant_and_seed2()
    test_policy_decision_gate_semantics()
    print(f"\n{'ALL PASS' if not fails else 'FAILED (%d): %s' % (len(fails), fails)}")
    return 0 if not fails else 1

if __name__ == "__main__":
    sys.exit(main())
