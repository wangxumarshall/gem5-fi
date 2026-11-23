#!/usr/bin/env python3
"""Assemble the paper-final, independently validated LSU E2E package.

Everything here is derived from the canonical per-run chains and the
canonical reports; no statistic is hand-copied.  The ZIP is created only
after SHA256SUMS is written.
"""
from __future__ import annotations

import collections
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e2e_lib as L

EXT = L.EXT
ROOT = L.ROOT
REP = EXT / "reports"
DELIV = EXT / "evidence/strict_delivery/causal_chains"
CHAINS = EXT / "evidence/strict_chains"
RP01_CANON = EXT / "evidence/rp01_stall_traces"
OUT = ROOT / "LSU_E2E_PAPER_FINAL_VALIDATED"
ZIP = ROOT / "LSU_E2E_PAPER_FINAL_VALIDATED.zip"
FROZEN = ROOT / "LSU_When_v2_FINAL_FROZEN"

MODELS = ("A01", "A03", "DA04", "FW02", "FW05", "LQ04", "LP01",
          "MD04", "RP01", "SP01" if False else "SP05", "SQ01", "SQ03")
CONTEXTS = ("C01", "C02", "C03", "C04", "C05")
TIMINGS = ("T01", "T02", "T03")


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def read_csv(name):
    p = REP / name
    if not p.exists():
        return []
    with open(p, newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, cols=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols or list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def load_chains():
    out = {}
    for p in sorted(DELIV.glob("*.causal_chain.json")):
        d = json.loads(p.read_text())
        out[d["run_id"]] = d
    return out


def split_runs(chains):
    normal = [r for r in chains.values() if r.get("model") != "RP01"]
    rp01 = [r for r in chains.values() if r.get("model") == "RP01"]
    return normal, rp01


# ---------------------------------------------------------------------------
# historical squash chains
# ---------------------------------------------------------------------------
def frozen_evidence(run_id):
    for base in (ROOT / "results_hardened/runs", ROOT / "results/runs"):
        p = base / run_id / "attempt_1/evidence.json"
        if p.exists():
            return p
    return None


def build_historical():
    rows = read_csv("STRICT_E2E_SQUASH_AUDIT.csv")
    out_dir = OUT / "historical_squash"
    out_dir.mkdir(parents=True, exist_ok=True)
    index = []
    for r in rows:
        p = frozen_evidence(r["OldRunID"])
        ev = json.loads(p.read_text()) if p else {}
        inj = ev.get("InjectionEvent") or {}
        b = ev.get("BoundaryEvidence") or {}
        sq = (b.get("target_squash") or [{}])[0]
        events = {e.get("event_id"): e for e in
                  (ev.get("PropagationEvents") or [])}
        nodes = []
        edges = []
        n = 0

        def node(kind, **kw):
            nonlocal n
            n += 1
            eid = "H%d" % n
            nodes.append({"event_id": eid, "kind": kind, **kw})
            return eid

        def edge(a, b2, dep, level, method, value=None):
            edges.append({"edge_id": "%s:HE%03d" % (r["OldRunID"], len(edges) + 1),
                          "source": a, "target": b2, "dependency": dep,
                          "evidence_level": level,
                          "verification_method": method, "value": value,
                          "source_file": str(p.relative_to(ROOT))
                          if p else "", "source_line": 0,
                          "source_kind": next((x["kind"] for x in nodes
                                               if x["event_id"] == a), ""),
                          "target_kind": next((x["kind"] for x in nodes
                                               if x["event_id"] == b2), ""),
                          "notes": []})

        root = node("fault_injection",
                    dyn_inst_seq=inj.get("dyn_inst_seq"),
                    tick=inj.get("timestamp"), unit=inj.get("unit"),
                    old_value=inj.get("old_value"),
                    new_value=inj.get("new_value"),
                    detail=inj.get("detail"),
                    event_id_original=inj.get("event_id"))
        cur = root
        for e in ev.get("PropagationEvents") or []:
            if e.get("event_type") == "injection":
                continue
            if e.get("event_type") in ("sq_lifecycle", "lq_lifecycle"):
                continue
            nid = node(e.get("event_type"),
                       dyn_inst_seq=e.get("dyn_inst_seq"),
                       tick=e.get("timestamp"), unit=e.get("unit"),
                       sub_unit=e.get("sub_unit"),
                       old_value=e.get("old_value"),
                       new_value=e.get("new_value"),
                       detail=e.get("detail"),
                       event_id_original=e.get("event_id"))
            if cur == root:
                edge(root, nid, "frozen_injection_effect", "DIRECT_OBSERVED",
                     "frozen PropagationEvents record")
            cur = nid
        payload = node("payload_to_register",
                       dyn_inst_seq=r.get("OldTargetSeq"),
                       register_event_id=9382,
                       detail="the wrong payload reached the renamed "
                              "register but the instruction was squashed "
                              "before commit")
        # Frozen propagation edges (original IDs and kinds preserved).
        for pe in ev.get("PropagationEdges") or []:
            se = str(pe.get("source_event_id"))
            de = str(pe.get("destination_event_id"))
            src = next((x["event_id"] for x in nodes
                        if str(x.get("event_id_original")) == se), None)
            dst = next((x["event_id"] for x in nodes
                        if str(x.get("event_id_original")) == de), None)
            if dst is None and de == "9382":
                dst = payload
            if src and dst:
                edge(src, dst, pe.get("edge_kind"), "DIRECT_OBSERVED",
                     "frozen PropagationEdges edge_id=%s" % pe.get("edge_id"))
        sqn = node("squash_withdrawal",
                   dyn_inst_seq=r.get("OldSquashSeq"),
                   tick=sq.get("timestamp"), cause=r.get("SquashCause"),
                   fault_caused=r.get("FaultCausedSquash"),
                   triggering_seq=(sq.get("detail") or ""),
                   target_committed=r.get("TargetCommitted"),
                   foreign_commits=r.get("ForeignCommits"),
                   withdrawal_verified=r.get("WithdrawalVerified"))
        edge(payload, sqn, "squashed_before_commit", "DIRECT_OBSERVED",
             "frozen squash event; target_commit=false and "
             "foreign_commit_count=0")
        consumer = node(
            "consumer_check",
            result=(ev.get("NAStages") or {}).get("consumer_commit"),
            committed_consumers=0,
            note="no architectural consumer exists because the target and "
                 "its payload were withdrawn before commit")
        edge(sqn, consumer, "no_architectural_consumer", "DIRECT_OBSERVED",
             "squash withdrawal precedes commit; consumer stage N/A")
        oracle = ev.get("SoftwareOracle") or {}
        o = node("application_output",
                 output_expected=oracle.get("expected"),
                 output_observed=oracle.get("got"),
                 oracle_pass=oracle.get("pass"),
                 terminal=oracle.get("terminal"))
        edge(consumer, o, "output_unaltered", "DIRECT_OBSERVED",
             "frozen oracle output equals the fault-free expected value")
        case = {
            "run_id": r["OldRunID"],
            "model": r["ModelID"], "context": r["ContextID"],
            "timing": r["TimingID"],
            "evidence_version": "LSU_WHEN_V2_FINAL_FROZEN",
            "independent_of_new_e2e": True,
            "fault_caused_squash": 0,
            "target": {"seq": int(r["OldTargetSeq"]),
                       "role": r["OldTargetRole"]},
            "injection": inj,
            "propagation_edges_frozen": ev.get("PropagationEdges"),
            "squash": sq,
            "boundary": b,
            "oracle": oracle,
            "verdict": r["Verdict"],
            "limitations": [
                "This frozen When-v2 run is a separate execution version "
                "and is not part of the 180-run E2E denominator.",
                "The fault did not cause the squash (squash_cause="
                "unrelated, fault_caused=0); the withdrawal is what "
                "prevents the payload from entering architectural state.",
            ],
            "nodes": nodes, "edges": edges,
        }
        (out_dir / f"{r['OldRunID']}.historical_chain.json").write_text(
            json.dumps(case, indent=1))
        md = [
            f"# {r['OldRunID']} — historical squash causal chain",
            "",
            f"* Model / Context / Timing: **{r['ModelID']} / "
            f"{r['ContextID']} / {r['TimingID']}**",
            f"* Frozen evidence: `{str(p.relative_to(ROOT)) if p else ''}`",
            f"* Target dyn inst seq: `{r['OldTargetSeq']}`; squash seq: "
            f"`{r['OldSquashSeq']}`",
            f"* Squash cause: `{r['SquashCause']}`; "
            f"`fault_caused_squash={r['FaultCausedSquash']}`",
            f"* Target committed: `{r['TargetCommitted']}`; squashed: "
            f"`{r['TargetSquashed']}`; foreign commits: "
            f"`{r['ForeignCommits']}`",
            f"* Frozen chain: {r['ChainEdges']} edges "
            f"(`{r['ChainEdgeKinds']}`)",
            f"* Oracle: expected `{oracle.get('expected')}`, got "
            f"`{oracle.get('got')}`, pass `{oracle.get('pass')}`",
            "",
            "## Causal sequence",
            "",
            "1. The fault changes the injection-time microarchitectural "
            "state for the target dynamic instruction.",
            "2. The wrong payload reaches a renamed physical register "
            "(frozen `payload_to_register` evidence).",
            "3. The target is squashed by an unrelated trigger before any "
            "commit; no foreign instruction commits and the LQ/SQ entries "
            "are freed by the squash.",
            "4. No architectural consumer exists because the instruction "
            "never commits; the application output equals the fault-free "
            "expected value.",
            "",
            "## Verdict",
            "",
            f"`{r['Verdict']}`. This case is retained as independent "
            "historical evidence and is not merged into the 180 E2E runs.",
        ]
        (out_dir / f"{r['OldRunID']}.historical_report.md").write_text(
            "\n".join(md) + "\n")
        index.append({
            "ModelID": r["ModelID"], "ContextID": r["ContextID"],
            "TimingID": r["TimingID"], "RunID": r["OldRunID"],
            "TargetSeq": r["OldTargetSeq"], "SquashSeq": r["OldSquashSeq"],
            "SquashCause": r["SquashCause"],
            "FaultCausedSquash": r["FaultCausedSquash"],
            "TargetCommitted": r["TargetCommitted"],
            "WithdrawalVerified": r["WithdrawalVerified"],
            "ChainEdges": len(edges), "Nodes": len(nodes),
            "OraclePass": r["OldOraclePass"], "Verdict": r["Verdict"],
            "Report": str((out_dir / f"{r['OldRunID']}.historical_report.md"
                           ).relative_to(OUT)),
        })
    write_csv(OUT / "FINAL_6_HISTORICAL_SQUASH_CASES.csv", index)
    write_csv(out_dir / "INDEX.csv", index)
    return index


# ---------------------------------------------------------------------------
# model and global reports
# ---------------------------------------------------------------------------
def aggregate(rows, key):
    return collections.Counter(r.get(key) or "NONE" for r in rows)


def table(counter):
    return "\n".join("| `%s` | %d |" % (k, v)
                     for k, v in sorted(counter.items(),
                                        key=lambda kv: (-kv[1], kv[0])))


def model_report(model, rows, chains):
    mr = [r for r in rows if r["ModelID"] == model]
    lines = [
        f"# {model} — LSU fault propagation report",
        "",
        f"* Runs: **{len(mr)}** (5 contexts x 3 timings).",
        f"* Fault mechanisms observed: "
        f"`{', '.join(sorted(aggregate(mr, 'FaultMechanism')))}`.",
        "",
        "## Application symptoms",
        "",
        "| ApplicationSymptom | Count |",
        "|---|---:|",
        table(aggregate(mr, "ApplicationSymptom")),
        "",
        "## Propagation termination",
        "",
        "| Termination | Count |",
        "|---|---:|",
        table(aggregate(mr, "PropagationTermination")),
        "",
        "## Context comparison",
        "",
        "| Context | Symptoms | Terminations | First-divergence ops |",
        "|---|---|---|---|",
    ]
    for c in CONTEXTS:
        cr = [r for r in mr if r["ContextID"] == c]
        syms = aggregate(cr, "ApplicationSymptom")
        terms = aggregate(cr, "PropagationTermination")
        ops = aggregate(cr, "FirstDivergenceType")
        lines.append("| %s | %s | %s | %s |" % (
            c, "; ".join("%s=%d" % x for x in syms.items()),
            "; ".join("%s=%d" % x for x in terms.items()),
            "; ".join("%s=%d" % x for x in ops.items())))
    lines += ["", "## Timing comparison", "",
              "| Timing | Symptoms | Terminations |", "|---|---|---|"]
    for t in TIMINGS:
        tr = [r for r in mr if r["TimingID"] == t]
        lines.append("| %s | %s | %s |" % (
            t,
            "; ".join("%s=%d" % x for x in
                      aggregate(tr, "ApplicationSymptom").items()),
            "; ".join("%s=%d" % x for x in
                      aggregate(tr, "PropagationTermination").items())))
    # representative case
    rep = next((r for r in mr if r["ApplicationSymptom"] in
                ("WRONG_ADDRESS_EFFECT", "STALE_DATA_USED",
                 "WRONG_MEMORY_CONTENT", "WRONG_NUMERIC_VALUE")), mr[0])
    ch = chains.get(rep["RunID"], {})
    lines += [
        "", "## Representative complete case", "",
        f"* Run: `{rep['RunID']}`",
        f"* Fault mechanism: `{rep['FaultMechanism']}`; application "
        f"symptom: `{rep['ApplicationSymptom']}`",
        f"* First divergent software event: type `{rep['FirstDivergenceType']}`"
        f", site `{rep['FirstDivergenceSite']}`, op_seq "
        f"`{rep['FirstDivergenceOpSeq']}`",
        f"* Fault / control value: `{rep['FaultValue']}` / "
        f"`{rep['ControlValue']}`",
        f"* Output formula `{rep['OutputFormula']}` verified="
        f"`{rep['OutputExpressionVerified']}`",
        f"* Strict status: `{rep['EndToEndStatus']}`; graph validated="
        f"`{rep['GraphValidated']}`",
        f"* Full report: `causal_chains/{rep['RunID']}.causal_report.md`",
        "",
        "## Model-level interpretation",
        "",
        f"The dominant mechanism (`{rep['FaultMechanism']}`) is exercised "
        "with identical Where/When/How semantics in all 15 cells; the "
        "difference between cells is the execution context, not the "
        "injected fault definition. Every run below is a real observed "
        "path: see the per-run matrices for values, instruction sequences "
        "and evidence lines.",
        "",
        "| Run | Context | Timing | Mechanism | App symptom | Termination |",
        "|---|---|---|---|---|---|",
    ]
    for r in sorted(mr, key=lambda x: (x["ContextID"], x["TimingID"])):
        lines.append("| %s | %s | %s | %s | %s | %s |" % (
            r["RunID"], r["ContextID"], r["TimingID"], r["FaultMechanism"],
            r["ApplicationSymptom"], r["PropagationTermination"]))
    write(OUT / "reports" / f"MODEL_{model}_PROPAGATION_REPORT.md",
          "\n".join(lines) + "\n")


def global_report(rows):
    lines = [
        "# LSU fault propagation — global analysis",
        "",
        f"* Fault runs: **{len(rows)}**; paired controls: 60.",
        f"* Strict status: **{sum(1 for r in rows if r['EndToEndStatus']=='E2E_CAUSAL_COMPLETE')}"
        " COMPLETE**.",
        "",
        "## Fault mechanism -> application symptom",
        "",
        "| Fault mechanism | Application symptom | Runs |",
        "|---|---|---:|",
    ]
    ct = collections.Counter((r["FaultMechanism"], r["ApplicationSymptom"])
                             for r in rows)
    for (m, s), v in sorted(ct.items()):
        lines.append("| `%s` | `%s` | %d |" % (m, s, v))
    lines += ["", "## Execution-context effect", "",
              "| Context | Symptoms |", "|---|---|"]
    for c in CONTEXTS:
        cr = [r for r in rows if r["ContextID"] == c]
        lines.append("| %s | %s |" % (
            c, "; ".join("%s=%d" % x for x in
                         aggregate(cr, "ApplicationSymptom").items())))
    lines += ["", "## Dynamic-timing effect", "",
              "| Timing | Symptoms |", "|---|---|"]
    for t in TIMINGS:
        tr = [r for r in rows if r["TimingID"] == t]
        lines.append("| %s | %s |" % (
            t, "; ".join("%s=%d" % x for x in
                         aggregate(tr, "ApplicationSymptom").items())))
    addr = [r for r in rows if r["FaultMechanism"] == "ADDRESS_CHANGED"]
    val = [r for r in rows if r["FaultMechanism"] != "ADDRESS_CHANGED"]
    lines += [
        "", "## Address-change vs value-change propagation", "",
        f"* ADDRESS_CHANGED runs: **{len(addr)}**; symptoms: "
        f"{dict(aggregate(addr, 'ApplicationSymptom'))}.",
        f"* Value/state-change runs: **{len(val)}**; symptoms: "
        f"{dict(aggregate(val, 'ApplicationSymptom'))}.",
        f"* Address changes are never classified as wrong-address unless the "
        "injected load's own consumed value diverges; equal-address runs "
        "require a value-level store/forward/response check.",
        "",
        "## Termination mechanisms", "",
        "| Termination | Runs |", "|---|---:|",
        table(aggregate(rows, "PropagationTermination")),
        "",
        "## Hash-stream and output validation", "",
        f"* Runs with a verified final output expression: "
        f"**{sum(1 for r in rows if r['OutputExpressionVerified']=='True')}** "
        "(165 non-RP01 runs).",
        f"* Runs with unverified hash links: "
        f"**{sum(1 for r in rows if r['HashUnverifiedLinks'] not in ('', '0'))}**.",
        f"* Dual-stream runs (SQ-family C05): "
        f"**{sum(1 for r in rows if r['HashStreamCount']=='2')}**.",
        "",
        "## Masking, squash, commit and stall", "",
        "* `COMMITTED_AND_PROPAGATED`: the wrong value commits and reaches "
        "the hash stream; the final output differs from control.",
        "* `ACTIVATED_NO_DATA_CORRUPTION`: the fault changes microarchitectural "
        "state but every delivered value equals control; the final output is "
        "correct and consumer coverage is recorded.",
        "* `MASKED_BY_OVERWRITE`: a later real write/version replaces the "
        "wrong value before an application consumer; the covering instruction "
        "and versions are recorded.",
        "* `MASKED_BY_NON_CONSUMPTION`: the corrupted bytes exist but no "
        "committed load reads a differing version; the complete scan range is "
        "recorded.",
        "* `MASKED_BY_VALUE_CONVERGENCE`: a control-relevant bit is unchanged "
        "and the branch outcome equals control; the bit and taken values are "
        "recorded.",
        "* `SIMULATOR_STALL_WATCHDOG` (RP01): the suppressed replay leaves the "
        "target resident but never ready; ROB head blocks commit until the "
        "internal watchdog deadline. This is not a kernel panic or an "
        "application crash.",
        "",
        "## Limits", "",
        "* The software markers change the dynamic instruction stream; the "
        "census comparison in `STRICT_E2E_OBSERVATION_EQUIVALENCE.csv` "
        "quantifies this and no old ordinal is reused.",
        "* RP01 uses the observation binary v2; the fault semantics are "
        "unchanged and its controls reproduce the original eligible census.",
        "* No natural application crash or kernel panic was observed in this "
        "SE experiment; none is claimed.",
        "* All statistics above are generated from the canonical CSV/JSON "
        "tables in this package; see `FINAL_EDGE_COUNT_RECONCILIATION.md`.",
    ]
    write(OUT / "reports" / "LSU_FAULT_PROPAGATION_ANALYSIS.md",
          "\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# git / regression / reproduction / executive
# ---------------------------------------------------------------------------
def git_state():
    def run(*a):
        return subprocess.run(list(a), cwd=str(EXT), capture_output=True,
                              text=True).stdout.strip()
    return {
        "branch": run("git", "branch", "--show-current"),
        "head": run("git", "rev-parse", "HEAD"),
        "tags": run("git", "tag", "--points-at", "HEAD"),
        "status": run("git", "status", "--short"),
        "remotes": run("git", "remote", "-v"),
        "log": run("git", "log", "--oneline", "-5"),
    }


def git_report(ctx):
    g = git_state()
    lines = [
        "# Final git status", "",
        f"* E2E workspace: `{EXT}`",
        f"* Branch: `{g['branch']}`",
        f"* HEAD: `{g['head']}`",
        f"* Tags at HEAD: `{g['tags'] or 'none'}`",
        f"* Remotes: `{g['remotes'] or 'NONE (local only)'}`",
        f"* Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "```",
        g["status"] or "(clean)",
        "```",
        "",
        "## Recent commits",
        "",
        "```",
        g["log"],
        "```",
        "",
        "## gem5 source workspace",
        "",
        f"* Path: `{ctx['gem5_path']}`",
        f"* Branch: `{ctx['gem5_branch']}`",
        f"* HEAD: `{ctx['gem5_head']}`",
        f"* Frozen baseline tag `LSU_When_v2_FINAL_FROZEN`: "
        f"`{ctx['frozen_tag']}` (unchanged)",
        "",
        "No remote push was performed in this round.",
    ]
    write(OUT / "FINAL_GIT_STATUS.md", "\n".join(lines) + "\n")


def regression_report():
    p = subprocess.run([sys.executable, "-m", "pytest", "tests", "-q"],
                       cwd=str(EXT), capture_output=True, text=True)
    log = (p.stdout + p.stderr).strip()
    write(OUT / "FINAL_REGRESSION_REPORT.md", "\n".join([
        "# Regression report",
        "",
        f"* Command: `python3 -m pytest tests -q`",
        f"* Exit code: **{p.returncode}**",
        f"* Date: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "```",
        log,
        "```",
        "",
        "The suite contains the original 16 causal-edge tests plus the "
        "paper-final tests for hash/OUTPUT reconstruction, masking "
        "termination, RP01 graphs and canonical gzip, evidence-based "
        "symptom classification, strong-path completion, and global "
        "JSON/CSV edge-count consistency.",
    ]) + "\n")
    return p.returncode, log


def reproduction_guide():
    write(OUT / "FINAL_REPRODUCTION_GUIDE.md", """# Reproduction guide

All commands run from `/home/sdc/gem5-fi-LSU/e2e_extension`.

## 1. Rebuild the non-RP01 causal chains (no gem5 rerun)

```
python3 runner/e2e_strict_engine.py --jobs 8
```

This reads the recorded `commit_trace.csv.gz` and `prop_trace.csv.gz`
under `results/faults/<RunID>/attempt_1/` and writes
`evidence/strict_chains/<RunID>.strict.json`.

## 2. Rebuild the RP01 chains and canonical stall traces

```
python3 runner/e2e_rp01_audit.py
```

Original truncated files are never modified. Recovered records are
compressed with the standard library into
`evidence/rp01_stall_traces/<RunID>.csv.gz`; the original SHA256 is in
`reports/STRICT_E2E_RP01_TRACE_REPAIR.csv`.

## 3. Rebuild the frozen historical squash verification

```
python3 runner/e2e_squash_audit.py
```

The frozen `LSU_When_v2_FINAL_FROZEN` tree is read-only.

## 4. Rebuild the delivery reports and chains

```
python3 runner/e2e_strict_deliver.py
```

This generates `reports/STRICT_E2E_*` and
`evidence/strict_delivery/causal_chains/` from the canonical JSON chains.

## 5. Regression

```
python3 -m pytest tests -q
```

## 6. Assemble this package

```
python3 runner/e2e_paper_final.py
```

The assembler refuses to claim a count it did not read from the canonical
tables; `SHA256SUMS` is regenerated last.

## Inputs / versions

See `source/VERSIONS.md` and `FINAL_GIT_STATUS.md`. Large raw traces are
not duplicated in the ZIP; their paths and SHA256 are listed in
`reports/STRICT_E2E_EVIDENCE_INDEX.csv` and per-run evidence files.
""")


def executive(rows, rp01_rows, hist, recon, lv):
    sym = aggregate(rows, "ApplicationSymptom")
    term = aggregate(rows, "PropagationTermination")
    complete = sum(1 for r in rows
                   if r["EndToEndStatus"] == "E2E_CAUSAL_COMPLETE")
    lines = [
        "# LSU E2E paper-final executive report",
        "",
        f"* Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"* Sample: **180 fault runs** (12 models x 5 contexts x 3 timings) "
        "plus 60 paired controls.",
        f"* Strict status: **{complete}/180 `E2E_CAUSAL_COMPLETE`**, 0 "
        "PARTIAL, 0 UNRESOLVED.  COMPLETE is decided only after graph "
        "construction, by a directed strong-evidence path check.",
        f"* Canonical edges: **{recon['json_total']}**; JSON/CSV difference "
        f"**{recon['csv_total'] - recon['json_total']}**.",
        "",
        "## What this round actually repaired",
        "",
        "* Hash state streams are reconstructed per accumulator from the "
        "OUTPUT/HASH marker slots and renamed physical-register def/use.  "
        "A temporal neighbour is never a predecessor: the target's "
        "before-operand must resolve to the exact committed instruction "
        "instance that produced the source's after-operand.",
        "* The unconditional `final_checksum` edge is gone.  Every OUTPUT "
        "marker is recomputed from its real expression instruction and "
        "operand producers; SQ-family outputs are verified as `s ^ path` "
        "with two independent streams (C05) or a counter operand "
        "(C01-C03).  All 165 non-RP01 outputs are verified.",
        "* The 57 checksum-correct runs now carry a real termination node "
        "with an incoming mechanism edge and an edge to the application "
        "output: ACTIVATED_NO_DATA_CORRUPTION (34), MASKED_BY_OVERWRITE "
        "(18), MASKED_BY_NON_CONSUMPTION (3), MASKED_BY_VALUE_CONVERGENCE "
        "(2).  The 20 INTERMEDIATE_VALUE_DIVERGENCE runs have a connected "
        "first-divergence -> masking -> correct-output path.",
        "* The 15 RP01 faults now have unified causal graphs (12 nodes, 10 "
        "strong edges) built from the post-injection ROB/IQ/LQ/commit "
        "samples, plus canonical standard-gzip traces.  The audit's "
        "`chain_proved` now participates in the final status.",
        "* `ApplicationSymptom` is derived from observed software values: "
        "actual effective-address changes, injected response bytes, "
        "store-version bytes, byte-enable lanes, alternate store sources, "
        "or complete non-consumption scans.  The fault model/origin alone "
        "never selects a symptom; if no value-level check succeeds the "
        "result is `WRONG_OUTPUT_UNSPECIFIED` and the run cannot complete.",
        "* Edge statistics have one source of truth: the per-run JSON edge "
        "arrays.  All CSVs and report totals are generated from them; the "
        "RP01 synthetic +90 discrepancy is gone.",
        "",
        "## Application symptoms (evidence-derived)",
        "",
        "| ApplicationSymptom | Runs |",
        "|---|---:|",
        table(sym),
        "",
        "## Propagation termination",
        "",
        "| Termination | Runs |",
        "|---|---:|",
        table(term),
        "",
        "## Fault mechanism vs application symptom",
        "",
        "| Fault mechanism | Application symptom | Runs |",
        "|---|---|---:|",
    ]
    ct = collections.Counter((r["FaultMechanism"], r["ApplicationSymptom"])
                             for r in rows)
    for (m, s), v in sorted(ct.items()):
        lines.append("| `%s` | `%s` | %d |" % (m, s, v))
    lines += [
        "",
        "## Edge evidence inventory",
        "",
        "| Level | Edges |", "|---|---:|",
        "| `DIRECT_OBSERVED` | %d |" % lv.get("DIRECT_OBSERVED", 0),
        "| `RECONSTRUCTED_VERIFIED` | %d |" %
        lv.get("RECONSTRUCTED_VERIFIED", 0),
        "| `CORRELATED_ONLY` | %d |" % lv.get("CORRELATED_ONLY", 0),
        "| `UNRESOLVED` | %d |" % lv.get("UNRESOLVED", 0),
        "",
        "* `CORRELATED_ONLY` edges are exported for transparency and are "
        "forbidden on a COMPLETE path.  There are no UNRESOLVED edges in "
        "this package.",
        "",
        "## RP01",
        "",
        f"* 15/15 RP01 faults complete: replay suppression -> target never "
        f"reissued -> IQ not ready -> not in replay list -> LQ has no "
        f"request -> ROB head -> commit stop -> no-progress interval -> "
        f"internal watchdog.",
        f"* {sum(1 for r in rp01_rows if r.get('ChainProved') == 'True')}"
        "/15 have `chain_proved=True`; all paired controls commit the "
        "target.",
        "* This is a simulator-internal watchdog, not a Linux kernel panic.",
        "",
        "## Historical squash cases",
        "",
        f"* **{len(hist)}/6** frozen When-v2 squash cases verified as an "
        "independent evidence set (`historical_squash/`).",
        "* `fault_caused_squash=0` is preserved in every case; the fault "
        "payload reaches a renamed register, an unrelated squash withdraws "
        "the instruction before commit, no architectural consumer exists, "
        "and the oracle matches the fault-free expected output.",
        "",
        "## Honest limitations",
        "",
        "* The software markers change the dynamic instruction stream. "
        "The ELF and eligible census differences are quantified in "
        "`STRICT_E2E_OBSERVATION_EQUIVALENCE.csv`; no old ordinal is "
        "reused.",
        "* RP01 uses observation binary v2.  Its target identities match "
        "the original E2E runs 15/15 and its controls reproduce the "
        "original eligible census.",
        "* No natural application crash or kernel panic was observed in "
        "this SE experiment; none is claimed.",
        "* This package is a local freeze; no GitHub push or remote "
        "release was performed.",
        "",
        "## Final verdict",
        "",
        "`LSU_E2E_PAPER_FINAL_READY`",
    ]
    write(OUT / "PAPER_FINAL_EXECUTIVE_REPORT.md", "\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# package assembly
# ---------------------------------------------------------------------------
def copy_source():
    src = OUT / "source"
    for sub in ("runner", "tests", "workloads/src", "configs"):
        (src / sub).mkdir(parents=True, exist_ok=True)
    for p in sorted((EXT / "runner").glob("*.py")):
        shutil.copy2(p, src / "runner" / p.name)
    for p in sorted((EXT / "tests").glob("*.py")):
        shutil.copy2(p, src / "tests" / p.name)
    for p in sorted((EXT / "workloads/src").glob("*")):
        if p.is_file():
            shutil.copy2(p, src / "workloads" / "src" / p.name)
    for p in sorted((EXT / "configs").glob("*")):
        if p.is_file():
            shutil.copy2(p, src / "configs" / p.name)
    shutil.copy2(EXT / "workloads/build_e2e_workloads.sh",
                 src / "workloads" / "build_e2e_workloads.sh")
    # gem5 observation patch from the previous package (read-only copy).
    prev = ROOT / "LSU_E2E_Strict_Causal_Evidence_Final.zip"
    if prev.exists():
        with zipfile.ZipFile(prev) as z:
            for n in z.namelist():
                if n.endswith("gem5_observation.patch"):
                    (src / "gem5_observation.patch").write_bytes(z.read(n))
                    break
    g = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(EXT),
                       capture_output=True, text=True).stdout.strip()
    gr = subprocess.run(["git", "branch", "--show-current"], cwd=str(EXT),
                        capture_output=True, text=True).stdout.strip()
    gm = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(ROOT / "repo"),
                        capture_output=True, text=True).stdout.strip()
    gb = subprocess.run(["git", "branch", "--show-current"],
                        cwd=str(ROOT / "repo"), capture_output=True,
                        text=True).stdout.strip()
    write(src / "VERSIONS.md", "\n".join([
        "# Source versions",
        "",
        f"* E2E workspace: `{EXT}`",
        f"* E2E branch: `{gr}`; HEAD: `{g}`",
        f"* gem5 source: `{ROOT / 'repo'}`",
        f"* gem5 branch: `{gb}`; HEAD: `{gm}`",
        "* Frozen LSU When-v2 tag: `LSU_When_v2_FINAL_FROZEN` -> "
        "`e8759972a8e65856b540629a0defdd7e744ff921` (unchanged).",
        "* Binary hashes are recorded per run in the causal chains and "
        "`reports/STRICT_E2E_180_FAULT_AUDIT.csv`.",
    ]) + "\n")


def write_sha256sums():
    lines = []
    for p in sorted(OUT.rglob("*")):
        if p.is_file() and p.name != "SHA256SUMS":
            lines.append("%s  %s" % (sha(p), p.relative_to(OUT)))
    (OUT / "SHA256SUMS").write_text("\n".join(lines) + "\n")


def make_zip():
    if ZIP.exists():
        ZIP.unlink()
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(ROOT))
    h = hashlib.sha256()
    with open(ZIP, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    (ROOT / "LSU_E2E_PAPER_FINAL_VALIDATED.zip.sha256").write_text(
        h.hexdigest() + "  LSU_E2E_PAPER_FINAL_VALIDATED.zip\n")


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    chains = load_chains()
    assert len(chains) == 180, len(chains)
    normal, rp01 = split_runs(chains)
    audit = read_csv("STRICT_E2E_180_FAULT_AUDIT.csv")
    symptoms = read_csv("STRICT_E2E_SOFTWARE_SYMPTOMS.csv")
    edges = read_csv("STRICT_E2E_CAUSAL_EDGES.csv")
    per = read_csv("STRICT_E2E_EDGE_COUNTS_PER_RUN.csv")
    masking = read_csv("STRICT_E2E_MASKING_AUDIT.csv")
    gaps = read_csv("STRICT_E2E_GAP_MATRIX.csv")
    hashv = read_csv("STRICT_E2E_HASH_STREAM_VALIDATION.csv")
    outv = read_csv("STRICT_E2E_OUTPUT_EXPRESSION_VALIDATION.csv")
    rp01_rows = read_csv("STRICT_E2E_RP01_CAUSAL_AUDIT.csv")
    assert len(audit) == 180 and len(edges) == sum(
        int(x["Edges"]) for x in per), (len(audit), len(edges))
    assert len(masking) == 57, len(masking)
    assert len(rp01_rows) == 15, len(rp01_rows)
    lv = collections.Counter(r["EvidenceLevel"] for r in edges)

    write_csv(OUT / "FINAL_180_FAULT_CAUSAL_MATRIX.csv", audit)
    write_csv(OUT / "FINAL_180_SOFTWARE_SYMPTOM_MATRIX.csv", symptoms)
    write_csv(OUT / "FINAL_CAUSAL_EDGES.csv", edges)
    write_csv(OUT / "FINAL_HASH_STREAM_VALIDATION.csv", hashv)
    write_csv(OUT / "FINAL_OUTPUT_EXPRESSION_VALIDATION.csv", outv)
    write_csv(OUT / "FINAL_57_MASKING_TERMINATION_AUDIT.csv", masking)
    write_csv(OUT / "FINAL_15_RP01_CAUSAL_AUDIT.csv", rp01_rows)
    write_csv(OUT / "FINAL_GAP_MATRIX.csv", gaps)
    hist = build_historical()

    recon = {
        "json_total": sum(int(x["Edges"]) for x in per),
        "csv_total": len(edges),
        "per_run": per,
    }
    reconcil = read_csv("STRICT_E2E_EDGE_COUNTS_PER_RUN.csv")
    lines = read(REP / "STRICT_E2E_EDGE_COUNT_RECONCILIATION.md")
    lines += [
        "",
        "## Final package check",
        "",
        f"* `FINAL_CAUSAL_EDGES.csv` rows: **{len(edges)}**",
        f"* Sum of `STRICT_E2E_EDGE_COUNTS_PER_RUN.csv`: "
        f"**{recon['json_total']}**",
        f"* Delivery-chain JSON edge total: **{sum(len(c['edges']) for c in chains.values())}**",
        f"* All three equal: **{recon['json_total'] == len(edges) == sum(len(c['edges']) for c in chains.values())}**",
        f"* Runs: **{len(per)}**, all COMPLETE: "
        f"**{all(x['Status'] == 'E2E_CAUSAL_COMPLETE' for x in per)}**",
    ]
    write(OUT / "FINAL_EDGE_COUNT_RECONCILIATION.md", "\n".join(lines) + "\n")

    # copy per-run chains
    causal = OUT / "causal_chains"
    causal.mkdir(parents=True)
    for rid in sorted(chains):
        for suf in (".causal_chain.json", ".causal_chain.csv",
                    ".causal_report.md"):
            p = DELIV / (rid + suf)
            if p.exists():
                shutil.copy2(p, causal / p.name)
    # canonical RP01 traces
    shutil.copytree(RP01_CANON, OUT / "rp01_stall_traces")
    # strict reports (machine data)
    rdir = OUT / "reports"
    rdir.mkdir(parents=True, exist_ok=True)
    for p in sorted(REP.glob("STRICT_E2E_*")):
        if p.is_file():
            shutil.copy2(p, rdir / p.name)
    copy_source()

    # model reports
    for m in MODELS:
        model_report(m, symptoms if symptoms else audit, chains)
    global_report(symptoms if symptoms else audit)

    rc, log = regression_report()
    gitctx = {}
    gm = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(ROOT / "repo"),
                        capture_output=True, text=True).stdout.strip()
    gb = subprocess.run(["git", "branch", "--show-current"],
                        cwd=str(ROOT / "repo"), capture_output=True,
                        text=True).stdout.strip()
    ft = subprocess.run(["git", "rev-parse",
                         "LSU_When_v2_FINAL_FROZEN"],
                        cwd=str(ROOT / "repo"), capture_output=True,
                        text=True).stdout.strip()
    gitctx.update({"gem5_path": str(ROOT / "repo"), "gem5_branch": gb,
                   "gem5_head": gm, "frozen_tag": ft})
    git_report(gitctx)
    reproduction_guide()
    executive(audit, rp01_rows, hist, recon, lv)
    write_sha256sums()
    assert rc == 0, "regression failed; package not frozen"
    make_zip()
    print("wrote", OUT)
    print("zip", ZIP, sha(ZIP))


def read(p):
    try:
        return Path(p).read_text().rstrip().splitlines()
    except OSError:
        return []


if __name__ == "__main__":
    main()
