#!/usr/bin/env python3
"""lsu_freq_policy.py — R6 frequency/statistics policy overlay (single source of truth).

Rule (2026-10-25 ruling):
  F0-F5          -> NORMAL,           required_seeds=3, schedule_enabled=True,  in_stats=True
  representative F6 -> STRESS_ONLY,   required_seeds=1, schedule_enabled=True,  in_stats=False
  other F6       -> STRESS_REDUNDANT, required_seeds=0, schedule_enabled=False, in_stats=False
Representatives: one per distinct F6 model_id (injector/hook identity is per-model);
T04-F6-W4 pinned; tie-break prefers certified existing evidence, else lexicographically smallest.

Emits R6-FREQUENCY-POLICY.json (machine) and R6-FREQUENCY-POLICY.md (audit) from the SAME dict.
`--check` re-emits in memory and byte-compares against disk (drift = failure).
"""
import argparse, csv, hashlib, json, sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MDS = REPO / "docs/gem5-fi/lsu/mdspec"
POLICY_JSON = MDS / "R6-FREQUENCY-POLICY.json"
POLICY_MD = MDS / "R6-FREQUENCY-POLICY.md"
RUNID_MAP = MDS / "runid_map.json"
MATRIX = REPO / "artifacts/lsu-trial/07-expanded-matrix-backfilled.csv"

SCHEMA_VERSION = "r6-frequency-policy/1"
DECISION_DATE = "2026-10-25"
DECISION_SOURCE = "user-ruling-2026-10-25:R6-frequency-policy-overlay"

REPRESENTATIVE_PIN = {"T04": "T04-F6-W4"}          # mandatory ARM TLB representative
EXISTING_EVIDENCE = {                              # runid -> certified evidence locator
    "T04-F6-W4": "runs/lsu/r6_c9_T04-F6-W4_s1 (seed1: eligible=1 injected=1 certified=true graceful=true terminal=full provable_to=L5)",
}

def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def _f6_rows_from_matrix():
    rows = list(csv.reader(open(MATRIX, encoding="utf-8")))
    return [r[1] for r in rows[1:] if len(r) > 1 and r[1].strip().split("-")[1:2] == ["F6"]]

def build_policy(runid_map_path=RUNID_MAP, matrix_path=MATRIX):
    rm = json.loads(Path(runid_map_path).read_text("utf-8"))
    entries = []
    f6 = [e for e in rm["entries"] if e["freq"] == "F6"]
    groups = {}
    for e in f6:
        groups.setdefault(e["model_id"], []).append(e["run_id"])

    def pick_rep(model, runids):
        if model in REPRESENTATIVE_PIN:
            return REPRESENTATIVE_PIN[model]
        with_ev = [r for r in runids if r in EXISTING_EVIDENCE]
        return (sorted(with_ev) or sorted(runids))[0]

    reps = {pick_rep(m, rs) for m, rs in groups.items()}
    rep_of = {r: pick_rep(m, rs) for m, rs in groups.items() for r in rs}

    for e in rm["entries"]:                       # authoritative 325
        rid, f = e["run_id"], e["freq"]
        if f == "F6":
            if rid in reps:
                entries.append(dict(run_id=rid, frequency=f, run_policy="STRESS_ONLY",
                    required_seeds=1, schedule_enabled=True, include_in_statistics=False,
                    representative_for=rid, exclusion_reason=None,
                    existing_evidence=EXISTING_EVIDENCE.get(rid), legacy=False))
            else:
                entries.append(dict(run_id=rid, frequency=f, run_policy="STRESS_REDUNDANT",
                    required_seeds=0, schedule_enabled=False, include_in_statistics=False,
                    representative_for=rep_of[rid], exclusion_reason="covered_by_representative_F6",
                    existing_evidence=None, legacy=False))
        else:
            entries.append(dict(run_id=rid, frequency=f, run_policy="NORMAL",
                required_seeds=3, schedule_enabled=True, include_in_statistics=True,
                representative_for=None, exclusion_reason=None, existing_evidence=None, legacy=False))

    known = {e["run_id"] for e in entries}
    for rid in sorted(set(_f6_rows_from_matrix()) - known):   # 4 legacy V2.0-deleted F6 rows
        entries.append(dict(run_id=rid, frequency="F6", run_policy="STRESS_REDUNDANT",
            required_seeds=0, schedule_enabled=False, include_in_statistics=False,
            representative_for=None, exclusion_reason="covered_by_representative_F6",
            existing_evidence=None, legacy=True))

    return {
        "schema_version": SCHEMA_VERSION, "decision_date": DECISION_DATE,
        "decision_source": DECISION_SOURCE,
        "immutable_inputs": {"xlsx_sha256": sha256(REPO/"docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案.xlsx"),
                             "generated_md_sha256": {p.name: sha256(p) for p in sorted(
                                 (REPO/"docs/gem5-fi/lsu").glob("gem5-fi-LSU单元故障注入方案*.md"))},
                             "matrix_sha256": sha256(MATRIX), "runid_map_sha256": sha256(RUNID_MAP)},
        "representative_groups": {m: {"representative": pick_rep(m, rs), "runids": sorted(rs)}
                                  for m, rs in sorted(groups.items())},
        "counts": {"total": len(entries),
                   "normal": sum(1 for e in entries if e["run_policy"] == "NORMAL"),
                   "stress_only": sum(1 for e in entries if e["run_policy"] == "STRESS_ONLY"),
                   "stress_redundant": sum(1 for e in entries if e["run_policy"] == "STRESS_REDUNDANT")},
        "entries": entries,
    }

def render_md(pol):
    L = [f"# R6 Frequency Policy (generated — do not hand-edit)",
         "", f"- schema_version: `{pol['schema_version']}`",
         f"- decision_date: {pol['decision_date']}",
         f"- decision_source: {pol['decision_source']}",
         f"- counts: {json.dumps(pol['counts'], ensure_ascii=False)}", "",
         "## Representative F6 groups", "",
         "| model | representative | runids |", "|---|---|---|"]
    for m, g in pol["representative_groups"].items():
        L.append(f"| {m} | {g['representative']} | {', '.join(g['runids'])} |")
    L += ["", "## F6 per-RunID policy table", "",
          "| RunID | policy | req_seeds | sched | in_stats | representative | reason |",
          "|---|---|---|---|---|---|---|"]
    for e in pol["entries"]:
        if e["frequency"] == "F6":
            L.append(f"| {e['run_id']} | {e['run_policy']} | {e['required_seeds']} | "
                     f"{e['schedule_enabled']} | {e['include_in_statistics']} | "
                     f"{e['representative_for'] or ''} | {e['exclusion_reason'] or ''} |")
    return "\n".join(L) + "\n"

def load_policy(path=POLICY_JSON):
    return json.loads(Path(path).read_text("utf-8"))

def query(pol, run_id, seed):
    e = next((x for x in pol["entries"] if x["run_id"] == run_id), None)
    if e is None:
        return {"run_id": run_id, "seed": seed, "decision": "UNKNOWN_RUNID"}
    if e["run_policy"] == "STRESS_REDUNDANT":
        dec = "REFUSE_STRESS_REDUNDANT"
    elif seed <= e["required_seeds"]:
        dec = "ALLOW_STRESS_ONLY" if e["run_policy"] == "STRESS_ONLY" else "ALLOW"
    else:
        dec = "POLICY_NOT_REQUIRED"
    return {**{k: e[k] for k in ("run_policy","required_seeds","schedule_enabled",
             "include_in_statistics","representative_for","exclusion_reason","existing_evidence")},
            "run_id": run_id, "seed": seed, "decision": dec}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="verify JSON+MD on disk match a fresh render")
    ap.add_argument("--query", nargs=2, metavar=("RUNID", "SEED"))
    a = ap.parse_args()
    pol = build_policy()
    if a.query:
        print(json.dumps(query(pol, a.query[0], int(a.query[1])), ensure_ascii=False))
        return 0
    if a.check:
        ok = (POLICY_JSON.read_text("utf-8") == json.dumps(pol, ensure_ascii=False, indent=1) + "\n"
              and POLICY_MD.read_text("utf-8") == render_md(pol))
        print("POLICY_CHECK: " + ("OK" if ok else "DRIFT"))
        return 0 if ok else 1
    POLICY_JSON.write_text(json.dumps(pol, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    POLICY_MD.write_text(render_md(pol), encoding="utf-8")
    print(json.dumps(pol["counts"], ensure_ascii=False))
    return 0

if __name__ == "__main__":
    sys.exit(main())
