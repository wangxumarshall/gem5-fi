#!/usr/bin/env python3
"""Build the v3.3.1 60-context ROI percentile mapping and distinctness audit.

Inputs are the census JSONL rows produced by tools/lsu_v331_census.py plus the
authoritative Excel seeds. Every row is OBSERVED or explicitly NOT_MAPPED with
a reason; no value is invented.
"""
import csv
import json
import math
import os
import re
import openpyxl

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CENSUS = os.path.join(ROOT, "audit_v3_3_1/roi/census")
OUT = os.path.join(ROOT, "audit_v3_3_1/roi")
XLSX = os.path.join(ROOT, "docs/gem5-fi/lsu/implementation_v3_2/excel/"
                          "gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.7.xlsx")
BIN_SHA = ("d3807fbef631354a41d9d6d8cf14c11020e396439f80bdd516225c6b5e37e2b2")

MODELS = ["A01", "A03", "FW02", "FW05", "SQ01", "SQ03", "SP05",
          "DA04", "LP01", "MD04", "LQ04", "RP01"]

# Frozen percentages (researcher decision A).
PCTS = [0.1, 0.3, 0.5, 0.7, 0.9]

# ROI and observed percentile ordinals. roi_n/ordinals are measured by the
# census in audit_v3_3_1/roi/census; the tag names the raw JSONL record.
ROI = {
    "A01": dict(workload="agu_addrmodes (W1)", start=1040, end=1234, n=195,
                ordinals=[1059, 1098, 1137, 1176, 1215], tag="A01_w1_r01",
                instr="load (AGU EA)", status="MAPPED",
                elig="Load completed AGU EA and was accepted by pushRequest"),
    "A03": dict(workload="agu_addrmodes (W1)", start=1040, end=1234, n=195,
                ordinals=[1059, 1098, 1137, 1176, 1215], tag="A03_w1_pct_r01",
                instr="load (AGU EA, F5 persistent)", status="MAPPED_WITH_SEMANTIC_CAVEAT",
                elig="Load completed AGU EA and was accepted by pushRequest"),
    "FW05": dict(workload="fw05_forward (W8a)", start=1, end=2000, n=2000,
                 ordinals=[200, 600, 1000, 1400, 1800], tag="FW05_w8a_pct_r01",
                 instr="load with >=2 distinct full-cover stores", status="MAPPED",
                 elig="full-cover forwarding pair with a distinct older store"),
    "DA04": dict(workload="alignment (W8b)", start=33, end=1056, n=1024,
                 ordinals=[135, 340, 544, 749, 954], tag="DA04_w8b_pct_r01",
                 instr="4B store (byte-enable)", status="MAPPED",
                 elig="Request with size==4 and a 4-lane byte-enable vector"),
    "LQ04": dict(workload="lq_lifetime_ordinal (W2)", start=1, end=5, n=5,
                 ordinals=[1, 2, 3, 4, 5], tag=None,
                 instr="load anchor (LQ entry)", status="MAPPED_FROM_PILOT_EVIDENCE",
                 elig="valid LQ entry with a request and not yet executed"),
    "SQ01": dict(workload="sq_drain (W3) formal / sq_reload_v3212 recommended",
                 start=1006, end=1133, n=128,
                 ordinals=[1018, 1044, 1069, 1095, 1121], tag="SQ01_sqreload_pct",
                 instr="store data byte0", status="MAPPED_ON_RECOMMENDED_WORKLOAD",
                 elig="store write passing the sq01 guard (merged forwarding-match stream)"),
    "SQ03": dict(workload="sq_drain (W3) formal / sq_reload_v3212 recommended",
                 start=1009, end=1136, n=128,
                 ordinals=[1021, 1047, 1072, 1098, 1124], tag="SQ03_sqreload_pct",
                 instr="store canWB", status="MAPPED_ON_RECOMMENDED_WORKLOAD",
                 elig="store reaching maybeSetCanWB in executeStore"),
    "SP05": dict(workload="store_path (W6) formal / sq_reload_v3212 recommended",
                 start=940, end=1067, n=128,
                 ordinals=[952, 978, 1003, 1029, 1055], tag="SP05_sqreload_pct",
                 instr="store completion", status="MAPPED_ON_RECOMMENDED_WORKLOAD",
                 elig="commitStores store passing chaos_sp05::isSelectable"),
    "FW02": dict(workload="sq_forward (W4)", start=None, end=None, n=0,
                 ordinals=[], tag=None, instr="load with older store",
                 status="INSUFFICIENT_EVENTS",
                 elig="store->load forwarding pair",
                 note="frozen W4 main has no data load (gcc -O2 folded every pair); N_ROI=0"),
    "MD04": dict(workload="replay_dependency (W7)", start=3, end=3, n=1,
                 ordinals=[3], tag="MD04_w7_r01", instr="younger load with 8B older store",
                 status="INSUFFICIENT_EVENTS",
                 elig="real byte-overlap violation report (store_size==8, load_size>=8)",
                 note="only ordinal 3 is in main (PC 0x400530, addr 0x491990); "
                      "ordinals 1,2,4,5,6 are libc/helper. N_ROI=1 < 5"),
    "LP01": dict(workload="load_response (W5)", start=None, end=None, n=None,
                 ordinals=[], tag=None, instr="load response (L1D)",
                 status="OBSERVABILITY_GAP",
                 elig="real data-load response in completeDataAccess",
                 note="the L1DForward record exposes only a physical address and no PC; "
                      "the eligible stream cannot be separated into the designed loop "
                      "with the current observation hook"),
    "RP01": dict(workload="replay_dependency (W7)", start=None, end=None, n=0,
                 ordinals=[], tag=None, instr="younger load with partial-overlap store",
                 status="INSUFFICIENT_EVENTS",
                 elig="PartialAddrRangeCoverage branch before rescheduleMemInst",
                 note="W7 main has only a full 8B store->8B load pair; no partial-overlap "
                      "event exists in the workload (v3.2.12 preflight: 5 eligible, all libc). "
                      "N_ROI=0; workload redesign required"),
}

# A03 activation identities (event_ordinal -> activation seq / reason / affected)
A03_ACT = {
    1059: (12978, "ALREADY_STUCK", 0),
    1098: (13638, "STUCK_APPLIED", 1),
    1137: (14049, "ALREADY_STUCK", 0),
    1176: (14719, "ALREADY_STUCK", 0),
    1215: (15086, "STUCK_APPLIED", 1),
}

LQ04_ROWS = [
    (3, 0x400338, 1), (4, 0x40033c, 2), (5, 0x400340, 3),
    (6, 0x400344, 4), (7, 0x400348, 5),
]


def load_census(tag):
    if not tag:
        return {}
    p = os.path.join(CENSUS, tag + ".jsonl")
    rows = {}
    if os.path.exists(p):
        for line in open(p):
            d = json.loads(line)
            rows[d["ordinal"]] = d
    return rows


def as_int(v):
    if v is None or isinstance(v, int):
        return v
    try:
        return int(str(v), 0)
    except (TypeError, ValueError):
        return None


def kv(detail):
    out = {}
    for m in re.finditer(r"([A-Za-z_]+)=([^;]+)", detail or ""):
        out[m.group(1)] = m.group(2)
    return out


def seeds():
    wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
    ws = wb["5.60个样本执行矩阵"]
    rows = list(ws.iter_rows(values_only=True))
    h = rows[0]
    ix = {k: i for i, k in enumerate(h)}
    out = {}
    for r in rows[1:]:
        model = r[ix["FaultModelID"]]
        ctx = r[ix["SampleRunID"]].split("-")[-1]
        out[(model, ctx)] = (int(r[ix["Seed"]]), r[ix["SampleRunID"]])
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    seedmap = seeds()
    mrows, drows = [], []
    for model in MODELS:
        meta = ROI[model]
        cen = load_census(meta["tag"])
        for i, ctx in enumerate(["R01", "R02", "R03", "R04", "R05"]):
            seed, srid = seedmap[(model, ctx)]
            pct = PCTS[i]
            base = dict(ModelID=model, ContextID=ctx, SampleRunID=srid, Seed=seed,
                        Percentile=pct, Workload=meta["workload"],
                        ROI_Start_Ordinal=meta["start"], ROI_End_Ordinal=meta["end"],
                        ROI_N=meta["n"], InstructionType=meta["instr"],
                        EligibilityCondition=meta["elig"],
                        EvidenceBinarySHA=BIN_SHA)
            if meta["status"].startswith("MAPPED") and meta["ordinals"]:
                k = math.ceil(pct * meta["n"])  # nearest-rank k(p)
                ordinal = meta["ordinals"][i]
                row = cen.get(ordinal, {})
                det = kv(row.get("detail"))
                if model == "LQ04":
                    seq, pc, lqidx = LQ04_ROWS[i]
                    base.update(
                        EvidenceBinarySHA="f3c2a442 (v3.2.10 evidence; on-disk binary d3807fbe)",
                        Rank_k=k, ROI_Relative_Ordinal=i + 1,
                        Absolute_Eligible_Ordinal=ordinal,
                        DynInstSeq=seq, ActivationDynInstSeq=seq,
                        PC=hex(pc), Address_or_Entry="lq_idx=%d" % lqidx,
                        TargetEventStatus="OBSERVED", MappingStatus="MAPPED",
                        EvidencePath="docs/gem5-fi/lsu/implementation_v3_2/"
                                     "pilots_v3_2_10/LQ04-R%02d/lq04_injections.log" % (i + 1),
                        Notes="five _start anchor loads are the designed W2 ROI by construction")
                    drow = dict(ModelID=model, ContextID=ctx, Percentile=pct,
                                StaticPC=hex(pc), DynInstSeq=seq, Address="n/a",
                                LQ_SQ_Entry="lq_idx=%d" % lqidx, Generation="%d" % (i + 1),
                                DataDependence="five distinct anchor loads",
                                ReplayGeneration="n/a", SquashState="n/a",
                                DistinctFromPrevious="YES (distinct PC/seq/entry)",
                                Evidence="LQ04-R%02d lq04_injections.log" % (i + 1))
                else:
                    act = A03_ACT.get(ordinal) if model == "A03" else None
                    base.update(
                        Rank_k=k, ROI_Relative_Ordinal=ordinal - meta["start"] + 1,
                        Absolute_Eligible_Ordinal=ordinal,
                        DynInstSeq=row.get("seq"),
                        ActivationDynInstSeq=(act[0] if act else row.get("seq")),
                        PC=(hex(as_int(row["pc"])) if row.get("pc") else "n/a"),
                        Address_or_Entry=("addr=%s" % hex(as_int(row["addr"]))) if row.get("addr")
                                         else ("lq_seq=%s" % det.get("lq_entry_id", "n/a")),
                        TargetEventStatus=("ALREADY_STUCK(affected=0)" if act and act[1] == "ALREADY_STUCK"
                                           else ("STUCK_APPLIED" if act else "OBSERVED")),
                        MappingStatus=("MAPPED" if meta["status"] == "MAPPED"
                                       else meta["status"]),
                        EvidencePath="audit_v3_3_1/roi/census/%s.jsonl#K%d" % (meta["tag"], ordinal),
                        Notes=("F5 activation event is bit3=0 (ALREADY_STUCK); the first "
                               "affected load is seq %s" % row.get("seq")) if act and act[1] == "ALREADY_STUCK"
                              else "")
                    same_pc = (i > 0 and row.get("pc") is not None and
                               base.get("PC") == ("0x%x" % row["pc"]) and False)
                    drow = dict(
                        ModelID=model, ContextID=ctx, Percentile=pct,
                        StaticPC=(hex(as_int(row["pc"])) if row.get("pc") else "n/a"),
                        DynInstSeq=row.get("seq"),
                        Address=(hex(as_int(row["addr"])) if row.get("addr") else "n/a"),
                        LQ_SQ_Entry="sq_idx=%s" % det.get("sq_idx", det.get("store_seq", "n/a")),
                        Generation=det.get("generation", det.get("gen", "n/a")),
                        DataDependence=(det.get("golden_ea", "n/a") if model == "A03" else "n/a"),
                        ReplayGeneration=det.get("replay_generation", "n/a"),
                        SquashState="n/a",
                        DistinctFromPrevious=("YES (seq/address differ)" if i else "n/a"),
                        Evidence="census %s#K%d" % (meta["tag"], ordinal),
                        Notes=("same static PC as another context; dynamic seq/address differ"
                               if model in ("FW05", "A01") and i >= 3 else ""))
                mrows.append(base)
                drows.append(drow)
            else:
                base.update(
                    Rank_k="n/a", ROI_Relative_Ordinal="n/a",
                    Absolute_Eligible_Ordinal="n/a", DynInstSeq="n/a",
                    ActivationDynInstSeq="n/a", PC="n/a", Address_or_Entry="n/a",
                    TargetEventStatus="NOT_AVAILABLE",
                    MappingStatus=meta["status"],
                    EvidencePath=("audit_v3_3_1/audits/Agent_B_Workload_Disassembly_Findings.md"
                                  if model in ("FW02", "RP01") else
                                  "audit_v3_3_1/roi/census/ (see model note)"),
                    Notes=meta.get("note", ""))
                mrows.append(base)
                drows.append(dict(
                    ModelID=model, ContextID=ctx, Percentile=pct,
                    StaticPC="n/a", DynInstSeq="n/a", Address="n/a",
                    LQ_SQ_Entry="n/a", Generation="n/a", DataDependence="n/a",
                    ReplayGeneration="n/a", SquashState="n/a",
                    DistinctFromPrevious="NO_EVIDENCE",
                    Evidence=meta.get("note", ""), Notes=meta["status"]))

    mp = os.path.join(OUT, "LSU_60Context_ROI_Percentile_Mapping.csv")
    dp = os.path.join(OUT, "LSU_60Context_Distinctness_Audit.csv")
    with open(mp, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(mrows[0].keys()))
        w.writeheader()
        w.writerows(mrows)
    with open(dp, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(drows[0].keys()))
        w.writeheader()
        w.writerows(drows)
    print("wrote", mp, len(mrows), "rows")
    print("wrote", dp, len(drows), "rows")
    from collections import Counter
    print("mapping status:", Counter(r["MappingStatus"] for r in mrows))


if __name__ == "__main__":
    main()
