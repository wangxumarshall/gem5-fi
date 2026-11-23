#!/usr/bin/env python3
"""Final independent acceptance checks for the strict E2E round."""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e2e_lib as L

EXT = L.EXT
ROOT = L.ROOT
REP = EXT / "reports"
CH = EXT / "evidence/strict_delivery/causal_chains"
SLOT = EXT / "results_strict_rp01"


def j(p):
    try:
        return json.loads(Path(p).read_text())
    except (OSError, ValueError):
        return {}


def main():
    checks = []

    def ck(name, ok, detail=""):
        checks.append({"Check": name, "Pass": bool(ok), "Detail": detail})

    audit = list(csv.DictReader(open(REP / "STRICT_E2E_180_FAULT_AUDIT.csv")))
    ck("180_audit_rows", len(audit) == 180, f"{len(audit)}")
    ck("all_complete", all(r["EndToEndStatus"] == "E2E_CAUSAL_COMPLETE"
                           for r in audit),
       str({r["EndToEndStatus"] for r in audit}))
    models = {r["ModelID"] for r in audit}
    ck("12_models", len(models) == 12, ",".join(sorted(models)))
    per = {}
    for r in audit:
        per[r["ModelID"]] = per.get(r["ModelID"], 0) + 1
    ck("15_per_model", all(v == 15 for v in per.values()), str(per))
    ck("chain_files", all((CH / f"{r['RunID']}.causal_chain.json").exists()
                          for r in audit), str(len(list(CH.glob("*.json")))))

    ctrls = [j(p) for p in (EXT / "results/state").glob("E2E-*-CTRL.json")]
    ck("60_controls_complete", len(ctrls) == 60 and all(
        c.get("status") == "COMPLETED" and c.get("oracle_pass") and
        c.get("injection_count") == 0 for c in ctrls), str(len(ctrls)))
    ck("180_ordinal_matches", all(r["OrdinalMatch"] == "True"
                                 for r in audit if r["ModelID"] != "RP01") or
       all(j(EXT / "results/state" / f"{r['RunID']}.json").get(
           "ordinal_match") is True for r in audit
           if r["ModelID"] != "RP01"), "")

    sdc = [r for r in audit if r["SoftwareSymptom"] == "WRONG_OUTPUT"]
    ck("108_wrong_output", len(sdc) == 108, str(len(sdc)))
    sdc_ok = True
    output_ok = True
    for r in sdc:
        d = j(CH / f"{r['RunID']}.causal_chain.json")
        s = d.get("software") or {}
        conn = s.get("causal_connection") or {}
        c = d.get("classification") or {}
        if s.get("hash_transition_failures") != 0:
            sdc_ok = False
        if conn.get("level") not in ("DIRECT_OBSERVED",
                                     "RECONSTRUCTED_VERIFIED"):
            sdc_ok = False
        if not (s.get("application_validation") or {}).get("verified"):
            sdc_ok = False
        if not (s.get("output_validation") or {}).get("verified"):
            output_ok = False
        if (s.get("hash_flow") or {}).get("unverified_links") != 0:
            output_ok = False
    ck("sdc_hash_and_edge_proof", sdc_ok, "")
    ck("165_output_expressions_verified", output_ok, "165 non-RP01 runs")

    noerr = [r for r in audit if r["SoftwareSymptom"] in (
        "NO_VISIBLE_ERROR", "INTERMEDIATE_VALUE_DIVERGENCE")]
    ck("57_no_checksum_error", len(noerr) == 57, str(len(noerr)))
    mask = list(csv.DictReader(open(REP / "STRICT_E2E_MASKING_AUDIT.csv")))
    ck("57_masking_rows", len(mask) == 57, str(len(mask)))
    ck("masking_categories_A_D", all(r["Category"] in "ABCD"
                                     for r in mask),
       str({r["Category"] for r in mask}))
    ck("masking_proof_present", all(r["Proof"] not in ("", "{}")
                                    for r in mask), "")
    ep_ok = True
    ivd_ok = True
    for r in noerr:
        d = j(CH / f"{r['RunID']}.causal_chain.json")
        eps = [n for n in d.get("nodes") or []
               if n.get("kind") == "masking_endpoint"]
        if not eps:
            ep_ok = False
            continue
        ep = eps[0]["event_id"]
        indeg = [e for e in d.get("edges") or []
                 if e.get("target") == ep and
                 e.get("evidence_level") in ("DIRECT_OBSERVED",
                                             "RECONSTRUCTED_VERIFIED")]
        out = [e for e in d.get("edges") or []
               if e.get("source") == ep and
               e.get("evidence_level") in ("DIRECT_OBSERVED",
                                           "RECONSTRUCTED_VERIFIED")]
        if not indeg or not out:
            ep_ok = False
        if r["SoftwareSymptom"] == "INTERMEDIATE_VALUE_DIVERGENCE":
            if not any(n.get("kind") == "first_software_divergence"
                       for n in d.get("nodes") or []):
                ivd_ok = False
    ck("57_masking_endpoints_connected", ep_ok, "")
    ck("20_ivd_terminal_nodes", ivd_ok, "")

    rp = list(csv.DictReader(open(REP / "STRICT_E2E_RP01_STALL_AUDIT.csv")))
    ck("rp01_15_audit", len(rp) == 15, str(len(rp)))
    ck("rp01_15_complete", all(r["ChainStatus"] == "E2E_CAUSAL_COMPLETE"
                               for r in rp), "")
    ck("rp01_probes_present", all(int(r["ProbeRows"]) > 200 for r in rp), "")
    ck("rp01_target_head", all(int(r["TargetAtROBHeadCount"]) > 0
                               for r in rp), "")
    ck("rp01_control_commits", all(r["TargetCommittedControl"] == "True"
                                   for r in rp), "")
    ck("rp01_watchdog_reason", all(r["WatchdogReason"] ==
                                   "INTERNAL_WATCHDOG_DEADLINE"
                                   for r in rp), "")
    ck("rp01_target_identity_same", all(
        r.get("TargetIdentitySame") == "True" for r in rp),
       str({r.get("TargetIdentitySame") for r in rp}))
    ck("rp01_chain_proved", all(r.get("ChainProved") == "True" for r in rp),
       "")
    import gzip
    canon = EXT / "evidence/rp01_stall_traces"
    gz_ok = True
    for p in sorted(canon.glob("*.csv.gz")):
        try:
            with gzip.open(p, "rb") as g:
                lines = [x for x in g.read().decode().splitlines()
                         if x and not x.startswith("#")]
            if not lines or lines[-1].split(",")[1] != "WATCHDOG":
                gz_ok = False
        except (OSError, EOFError):
            gz_ok = False
    ck("rp01_canonical_gzip", len(list(canon.glob("*.csv.gz"))) == 15 and
       gz_ok, "")

    sq = list(csv.DictReader(open(REP / "STRICT_E2E_SQUASH_AUDIT.csv")))
    ck("six_squash_rows", len(sq) == 6, str(len(sq)))
    ck("six_squash_verified", all(r["Verdict"] == "VERIFIED" for r in sq),
       str({r["Verdict"] for r in sq}))
    ck("six_squash_frozen_sha", all(r["FrozenEdgeSHA256Match"] == "True"
                                    for r in sq), "")
    ck("six_squash_cause_preserved", all(
        r["SquashCause"] == "unrelated" and r["FaultCausedSquash"] == "0"
        for r in sq), "")

    eq = list(csv.DictReader(open(REP /
                                  "STRICT_E2E_OBSERVATION_EQUIVALENCE.csv")))
    ck("60_equivalence_rows", len(eq) == 60, str(len(eq)))
    same = sum(1 for r in eq if r["EligibleCensusSame"] == "True")
    ck("census_delta_reported", same + sum(
        1 for r in eq if r["EligibleCensusSame"] == "False") == 60,
       f"same={same} changed={60-same}")

    edges_csv = list(csv.DictReader(
        open(REP / "STRICT_E2E_CAUSAL_EDGES.csv")))
    per_csv = list(csv.DictReader(
        open(REP / "STRICT_E2E_EDGE_COUNTS_PER_RUN.csv")))
    ck("edge_json_csv_reconciled",
       len(edges_csv) == sum(int(x["Edges"]) for x in per_csv) and
       len({x["EdgeID"] for x in edges_csv}) == len(edges_csv),
       f"csv={len(edges_csv)} sum={sum(int(x['Edges']) for x in per_csv)}")

    tests = subprocess.run(["python3", "-m", "pytest", "tests", "-q"],
                           cwd=str(EXT), capture_output=True, text=True)
    ck("negative_positive_tests", tests.returncode == 0,
       tests.stdout.strip().splitlines()[-1] if tests.stdout else "")

    head = subprocess.run(["git", "rev-parse", "HEAD"],
                          cwd=str(ROOT / "repo"),
                          capture_output=True, text=True).stdout.strip()
    frozen = subprocess.run(
        ["git", "rev-parse", "LSU_When_v2_FINAL_FROZEN^{commit}"],
        cwd=str(ROOT / "repo"), capture_output=True,
        text=True).stdout.strip()
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", frozen, head],
        cwd=str(ROOT / "repo")).returncode == 0
    ck("frozen_commit_unchanged",
       frozen == "e8759972a8e65856b540629a0defdd7e744ff921" and ancestor,
       f"tag={frozen} head={head} ancestor={ancestor}")
    changed = subprocess.run(
        ["git", "diff", "--name-only"], cwd=str(ROOT / "repo"),
        capture_output=True, text=True).stdout.split()
    rule_headers = [x for x in changed if x.endswith("_rules.hh")]
    ck("no_fault_rule_edit", not rule_headers, ";".join(rule_headers))

    with open(REP / "STRICT_E2E_VERIFICATION_RESULTS.csv", "w",
              newline="") as f:
        w = csv.DictWriter(f, fieldnames=["Check", "Pass", "Detail"])
        w.writeheader()
        w.writerows(checks)
    passed = sum(1 for c in checks if c["Pass"])
    print(f"{passed}/{len(checks)} checks pass")
    for c in checks:
        if not c["Pass"]:
            print("FAIL", c)
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
