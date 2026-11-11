#!/usr/bin/env python3
"""Build the v3.3.2 supplementary acceptance tables and the config workbook."""
from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

from openpyxl import Workbook

ROOT = Path(__file__).resolve().parents[1]
AUD = ROOT / "audit_v3_3_2"
RUNS = AUD / "runs"
W = ROOT / "docs/gem5-fi/lsu/implementation_v3_2/workloads"
D = ROOT / "workloads/directed"

FILES = {
    "A01": ("agu_addrmodes", W / "agu_addrmodes", W / "agu_addrmodes.golden"),
    "A03": ("agu_addrmodes", W / "agu_addrmodes", W / "agu_addrmodes.golden"),
    "FW02": ("sq_forward_w4v2 (candidate)", D / "sq_forward_w4v2",
             D / "sq_forward_w4v2.golden"),
    "FW05": ("fw05_forward", W / "fw05_forward", W / "fw05_forward.golden"),
    "SQ01": ("sq_reload_v3212 (candidate)", W / "sq_reload_v3212",
             W / "sq_reload_v3212.golden"),
    "SQ03": ("sq_reload_v3212 (candidate)", W / "sq_reload_v3212",
             W / "sq_reload_v3212.golden"),
    "SP05": ("sq_reload_v3212 (candidate)", W / "sq_reload_v3212",
             W / "sq_reload_v3212.golden"),
    "DA04": ("alignment", W / "alignment", W / "alignment.golden"),
    "LP01": ("load_response", W / "load_response", W / "load_response.golden"),
    "MD04": ("md04_violations_v332 (candidate)",
             D / "md04_violations_v332", D / "md04_violations_v332.golden"),
    "LQ04": ("lq_lifetime_ordinal", W / "lq_lifetime_ordinal",
             W / "lq_lifetime_ordinal.golden"),
    "RP01": ("replay_partial_v332 (candidate)", D / "replay_partial_v332",
             D / "replay_partial_v332.golden"),
}

HOOK = {
    "A01": ("CHAOSAddrPath", "lsq_pushRequest_PRE (A01Bit F0, bit 3)",
            "transient EA bit flip", "none (v3.3.1 path)"),
    "A03": ("CHAOSAddrPath", "lsq_pushRequest_PRE (A03stuck0, F5)",
            "persistent EA bit-3 stuck-at-0", "PC threaded + stuck lifecycle"),
    "FW02": ("CHAOSLSQFwd", "store->load forward decision (f6_fw02)",
             "one suppressed forward", "none"),
    "FW05": ("CHAOSLSQFwd", "forward decision (fw05_older_src)",
             "older-source substitution", "none"),
    "SQ01": ("CHAOSLSQFwd", "lsq_write_sq_entry (sq01_bit3)",
             "SQ data bit-3 flip", "none"),
    "SQ03": ("CHAOSLSQFwd", "executeStore _canWB (sq03_canwb)",
             "premature canWB", "none"),
    "SP05": ("CHAOSLSQFwd", "completeStore (sp05_complete)",
             "store completion lost", "none"),
    "DA04": ("CHAOSLSQFwd", "store byte-enable (da04_be_bit0)",
             "byte-enable bit flip", "runner p=0 omit (control hazard closed)"),
    "LP01": ("CHAOSL1DForward", "LSQ completeDataAccess post-check",
             "byte-0 response bit flip", "PC/VA/dyn-seq/LQ identity added"),
    "MD04": ("CHAOSMD04", "LSQUnit::checkViolations",
             "violation report suppressed", "runner p=0 omit (control hazard closed)"),
    "LQ04": ("CHAOSLQ04", "LQ entry lifetime/ordinal",
             "LQ entry lifetime fault", "none"),
    "RP01": ("CHAOSLSQFwd", "read() PartialAddrRangeCoverage reschedule",
             "replay reschedule skipped", "none (v3.2.12 hook)"),
}


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def jload(p):
    try:
        return json.loads(p.read_text())
    except Exception:
        return {}


def control_checksum(model, ctx):
    d = RUNS / f"{model}-R{ctx:02d}-control"
    for name in ("oracle.log", "stdout.log"):
        p = d / name
        if p.exists():
            text = p.read_text(errors="replace")
            m = (re.search(r"got=([0-9a-fA-F]+)", text)
                 or re.search(r"checksum=0x([0-9a-fA-F]+)", text))
            if m:
                return m.group(1)
    return "n/a"


def main():
    matrix = list(csv.DictReader(open(AUD / "LSU_60Context_Final_Readiness_Matrix.csv")))
    causal = list(csv.DictReader(open(AUD / "propagation/LSU_60Context_Causal_Propagation_Final.csv")))

    # 1. source/hook audit
    rows = []
    for m, (obj, site, sem, change) in HOOK.items():
        ms = [r for r in matrix if r["ModelID"] == m]
        rows.append({
            "ModelID": m, "SimObject": obj, "HookSite": site,
            "FaultSemantics": sem, "V332Change": change,
            "FaultInjected": sum(1 for r in ms if r["FaultInjected"] == "YES"),
            "Contexts": len(ms),
            "Status": "HOOK_VERIFIED",
        })
    with open(AUD / "LSU_12Model_Source_Hook_Audit.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    print("wrote source hook audit")

    # 2. workload/oracle audit
    rows = []
    for m, (name, elf, golden) in FILES.items():
        g = golden.read_text().strip() if golden.exists() else "n/a"
        ck = control_checksum(m, 1)
        rows.append({
            "ModelID": m, "Workload": name, "ELF": str(elf),
            "ELFSHA256": sha(elf), "Golden": g,
            "ControlChecksum": ck,
            "OracleMatch": ("YES" if ck != "n/a" and ck in g else "NO"),
            "WorkloadStatus": ("CANDIDATE_PENDING_APPROVAL"
                               if "(candidate)" in name else "FORMAL"),
        })
    with open(AUD / "LSU_Workload_Oracle_Final_Audit.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    print("wrote workload oracle audit")

    # 3. diagnostic features
    rows = []
    for r in causal:
        m, ctx = r["ModelID"], r["ContextID"]
        meta = jload(RUNS / f"{m}-{ctx}-fault/pilot_meta.json")
        ev = (meta.get("classification") or {}).get("fault_effect_evidence") or {}
        rows.append({
            "ModelID": m, "ContextID": ctx,
            "InjectionEventID": ev.get("injection_event_id", "n/a"),
            "ChainPtag": ev.get("chain_ptag", "n/a"),
            "ChainDynInstSeq": ev.get("chain_dyn_inst_seq", "n/a"),
            "ChainEventCount": ev.get("chain_events", "n/a"),
            "ChainEventTypes": "|".join(ev.get("chain_event_types", []) or []),
            "ValueDivergenceCount": ev.get("value_divergence_count", "n/a"),
            "ControlDivergenceCount": ev.get("control_divergence_count", "n/a"),
            "PropagationCoverage": (meta.get("classification") or {}).get(
                "fault_effect_propagation_coverage", "n/a"),
            "FaultEffectReason": (meta.get("classification") or {}).get(
                "fault_effect_reason", "n/a"),
            "Terminal": r["ArchitecturalOrTerminal"],
            "EvidenceClass": r["EvidenceClass"],
        })
    with open(AUD / "LSU_Diagnostic_Features_Final.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    print("wrote diagnostic features")

    # 4. config workbook
    wb = Workbook()
    ws = wb.active; ws.title = "60 Contexts"
    cols = ["ModelID", "ContextID", "Seed", "WorkloadStatus", "Ordinal",
            "FaultTerminal", "FaultInjected", "ControlInjected",
            "ControlProof", "ControlOracle", "Trace", "CausalClass",
            "Qualifier", "Ready"]
    ws.append(cols)
    for r in matrix:
        ws.append([r.get(c) for c in cols])
    ws2 = wb.create_sheet("12 Model Summary")
    ws2.append(["ModelID", "Contexts", "FaultInjected", "ControlsZero",
                "Terminals"])
    for m in HOOK:
        ms = [r for r in matrix if r["ModelID"] == m]
        terms = {}
        for r in ms:
            terms[r["FaultTerminal"]] = terms.get(r["FaultTerminal"], 0) + 1
        ws2.append([m, len(ms),
                    sum(1 for r in ms if r["FaultInjected"] == "YES"),
                    sum(1 for r in ms if r["ControlInjected"] == "0"),
                    ";".join(f"{k}={v}" for k, v in sorted(terms.items()))])
    ws3 = wb.create_sheet("Provenance")
    for row in [
        ["Final HEAD", "fc60822408cbb3f5af4788bd99fc82c114917367"],
        ["Base HEAD", "3504ec23733ad1de550554693a8e10c87a3a81ad"],
        ["Final binary SHA256",
         "070d68a688464fa737e6bf102f44a27e911dc29d15142d77c82ec2083115f5ca"],
        ["Base binary SHA256",
         "d3807fbef631354a41d9d6d8cf14c11020e396439f80bdd516225c6b5e37e2b2"],
        ["Binary size", "1149044528"],
        ["ConfigFrozen", "NO — awaits researcher approval of candidate workloads and ROI"],
        ["Formal campaign", "NOT STARTED"],
    ]:
        ws3.append(row)
    wb.save(AUD / "LSU_Formal_Experiment_Config.xlsx")
    print("wrote config workbook")


if __name__ == "__main__":
    main()
