#!/usr/bin/env python3
"""sdc_diagnose.py — seven-step SDC diagnosis + P/N rules + confidence
engine for openEuler/Kunpeng920 (plan §7.4–§7.6, Task 4.3).

Input: aggregated evidence (from logparse.py aggregates + optional
RAS/EDAC/reboot facts). Engine:
  Step 1 Top-N candidate ranking      (anomaly volume per host)
  Step 2 reboot anomaly                (>=6 unplanned/30d generic, >=3 AI)
  Step 3 RAS silence                   (no CPU RAS records + zero CE/UE
                                        deviation => SDC candidate; SError
                                        WITH valid record => loud, N3)
  Step 4 core concentration            (single core >60% + sibling merge
                                        + >=2 apps, P1/P2)
  Step 5 exception-type weighting      (§7.3 star matrix, via esr_decode)
  Step 6 service-history cross-check   (repeated misdiagnoses, P6)
  Step 7 independent FA confirmation   (>=70% repro, P7)

Rules (§7.5): P1–P11 positive, N1–N10 negative (any N hit => excluded).
Confidence (§7.6):
  HIGH   P1+P2+P3+P5 + (P4 any type / P8 / P9)  -> isolate + FA
  MEDIUM P1+P2+P5 (no P4)                       -> extend testing
  LOW    only P3 or P6                           -> monitor
  EXCLUDED any N rule hit

Verification anchors (plan §7.8 core179 six-case replay):
  - core179 evidence -> HIGH confidence (P1+P2+P5 hit, P4-type hit via
    0x960000xx DABT, N3 NOT hit) and recommendation offline+FA+RMA
  - a fabricated uniform-distribution log -> N1 excludes

Usage:
  python3 sdc_diagnose.py --evidence evidence.json
  python3 sdc_diagnose.py --logparse-dir /path/to/vmcore-dumps
"""
import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from logparse import parse, aggregate, load_text  # noqa: E402
from esr_decode import decode as decode_esr  # noqa: E402


def evaluate(ev: dict) -> dict:
    """Run the seven steps + P/N rules over an evidence dict.

    Expected evidence fields (all optional; logparse aggregate keys map in):
      n_anomalies, per_core, top_core, top_core_count, concentration,
      per_core_comms (or P2 facts), esr_histogram, reboot_unplanned_30d,
      ras_cpu_records, edac_ce_count, edac_ue_count, serror_with_valid_record,
      service_misdiagnose_30d, fa_repro_rate, uniform_distribution(bool)
    """
    rules_hit, rules_miss = [], []

    def hit(rule, desc):
        rules_hit.append({"rule": rule, "desc": desc})

    # --- Step 4 / P1: core concentration > 60% (homogeneous Kunpeng920)
    conc = ev.get("concentration", 0.0)
    p1 = conc > 0.60
    if p1:
        hit("P1", f"single-core concentration {conc*100:.1f}% > 60% "
                  f"(top core {ev.get('top_core')})")
    # P2: >=2 distinct apps failing on the top core
    p2 = bool(ev.get("P2_multi_app_on_top_core") or
              (ev.get("top_core_comms") and len(ev["top_core_comms"]) >= 2))
    if p2:
        hit("P2", ">=2 distinct applications failed on the same core")
    # --- Step 2 / P3: unplanned reboots
    reboots = ev.get("reboot_unplanned_30d", 0)
    ai_load = bool(ev.get("ai_workload"))
    p3 = reboots >= (3 if ai_load else 6)
    if p3:
        hit("P3", f"{reboots} unplanned reboots/30d "
                  f">= {'3 (AI)' if ai_load else '6 (generic)'}")
    # --- Step 5 / P4: high-relevance exception types on the same core
    esr_hist = ev.get("esr_histogram", {})
    p4_types = set()
    for esr_hex, cnt in esr_hist.items():
        d = decode_esr(int(esr_hex, 16))
        if d.get("sdc_weight_stars", 0) >= 3:
            p4_types.add(f"{esr_hex} ({d['ec_name']}, {d['sdc_relevance']})")
    p4 = len(p4_types) > 0 and p1
    if p4:
        hit("P4", f"high-relevance exception types on the top core: "
                  f"{', '.join(sorted(p4_types))}")
    # --- Step 3 / P5: RAS silence
    ras_cpu = ev.get("ras_cpu_records", 0)
    ce, ue = ev.get("edac_ce_count", 0), ev.get("edac_ue_count", 0)
    serr_valid = bool(ev.get("serror_with_valid_record"))
    p5 = (ras_cpu == 0 and ce == 0 and ue == 0 and not serr_valid)
    if p5:
        hit("P5", f"RAS silent: no CPU RAS records, EDAC CE={ce} UE={ue}, "
                  f"no SError-with-valid-record")
    # P6: service history (repeated misdiagnosis)
    if ev.get("service_misdiagnose_30d", 0) >= 1:
        hit("P6", "repeated misdiagnosis/no-fault-found in 30d history")
    # P7: independent FA
    if ev.get("fa_repro_rate", 0) >= 0.70:
        hit("P7", f"independent FA reproduction {ev['fa_repro_rate']*100:.0f}% >= 70%")
    # P10: persistence across quarters
    if ev.get("persistent_failures_quarters", 0) >= 2:
        hit("P10", "failures persisted >=2 quarters (PinDrop-style)")
    # P11: sibling cores co-failing
    if ev.get("sibling_cores_failed"):
        hit("P11", "SMT sibling cores co-failing")

    # --- negative rules (any hit => excluded)
    n_hits = []
    if ev.get("uniform_distribution") or (conc <= 0.25 and ev.get("n_anomalies", 0) >= 20):
        n_hits.append(("N1", "anomalies uniformly distributed across cores -> software"))
    if ev.get("single_app_same_backtrace"):
        n_hits.append(("N2", "single app + identical backtrace -> software defect"))
    if ras_cpu > 0:
        n_hits.append(("N3", f"RAS has explicit CPU hardware fault records "
                             f"({ras_cpu}) -> loud fault, not silent"))
    if ev.get("fuzzer_tool_origin"):
        n_hits.append(("N4", "anomalies traced to fuzzer/test tool -> excluded"))
    if ev.get("hw_diagnostic_in_dump"):
        n_hits.append(("N5", "crash dump contains hardware diagnostics -> not silent"))
    if ev.get("known_bug_or_cve"):
        n_hits.append(("N6", "matches known bug/CVE pattern -> software root cause"))
    if ev.get("mass_synchronized_anomalies"):
        n_hits.append(("N7", "large-scale synchronized anomalies -> config/software"))
    if ev.get("missing_memory_barrier"):
        n_hits.append(("N8", "missing memory barrier (porting artifact) -> software"))
    if ev.get("environment_transient"):
        n_hits.append(("N9", "environment transient (power/thermal event) -> environmental"))
    if ev.get("single_negative_test"):
        n_hits.append(("N10", "single negative test is unreliable — continuous "
                              "re-testing required (<=30d revisit)"))

    # --- confidence (§7.6)
    if n_hits:
        level, action = "EXCLUDED", "not SDC: " + "; ".join(
            f"{r} {d}" for r, d in n_hits)
    elif p1 and p2 and p3 and p5 and (p4 or ev.get("p8_vector_signal")
                                      or ev.get("p9_nzcv_anomaly")):
        level = "HIGH"
        action = "立即隔离（offline 该核）+ FA 硅片分析 + RMA"
    elif p1 and p2 and p5:
        level = "MEDIUM"
        action = "增加测试覆盖 / 延长观察（补 P4 证据或 FA）"
    elif p3 or ev.get("service_misdiagnose_30d"):
        level = "LOW"
        action = "标记观察：监控 CE/PMU 偏差，<=30 天重访"
    else:
        level, action = "LOW", "证据不足：继续采集（Top-N/重启/RAS）"

    return {
        "confidence": level,
        "action": action,
        "rules_hit": rules_hit,
        "rules_negative": [{"rule": r, "desc": d} for r, d in n_hits],
        "seven_steps": {
            "step1_topN": ev.get("n_anomalies", 0),
            "step2_reboots": reboots,
            "step3_ras_silent": p5,
            "step4_concentration": conc,
            "step5_weighted_types": sorted(p4_types),
            "step6_service_history": ev.get("service_misdiagnose_30d", 0),
            "step7_fa_repro": ev.get("fa_repro_rate", 0),
        },
    }


def evidence_from_logparse(path: str, extra: dict = None) -> dict:
    """Build the evidence dict from a vmcore-dumps dir (or one log file)."""
    if os.path.isdir(path):
        files = sorted(glob.glob(os.path.join(path, "*", "vmcore-dmesg.txt"))
                       or glob.glob(os.path.join(path, "vmcore-dmesg.txt")))
    else:
        files = [path]
    events = []
    for fp in files:
        events.extend(parse(load_text(fp), source=fp))
    # signature subset: spurious + Oops (the SDC-relevant family)
    sig = [e for e in events if e["kind"] in
           ("spurious_translation_fault", "Oops")]
    agg = aggregate(sig)
    ev = dict(agg)
    # per-core comm sets for P2
    per_core_comms = {}
    for e in sig:
        c = e.get("cpu")
        if c is not None:
            per_core_comms.setdefault(c, set()).add(e.get("comm", "?"))
    top = agg.get("top_core")
    ev["top_core_comms"] = sorted(per_core_comms.get(top, set())) if top is not None else []
    ev["P2_multi_app_on_top_core"] = len(ev["top_core_comms"]) >= 2
    if extra:
        ev.update(extra)
    return ev


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--evidence", help="evidence JSON file")
    ap.add_argument("--logparse-dir",
                    help="vmcore dumps dir — build evidence via logparse")
    ap.add_argument("--extra", help="extra evidence JSON (reboots/RAS/FA)",
                    default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.evidence:
        with open(args.evidence) as f:
            ev = json.load(f)
    elif args.logparse_dir:
        extra = {}
        if args.extra:
            with open(args.extra) as f:
                extra = json.load(f)
        ev = evidence_from_logparse(args.logparse_dir, extra)
    else:
        ap.error("need --evidence or --logparse-dir")

    verdict = evaluate(ev)
    if args.json:
        print(json.dumps({"evidence": ev, "verdict": verdict},
                         indent=2, ensure_ascii=False, default=str))
        return
    v = verdict
    print(f"置信度: {v['confidence']}")
    print(f"处置: {v['action']}")
    print("七步法:")
    s = v["seven_steps"]
    print(f"  Step1 Top-N anomalies = {s['step1_topN']}")
    print(f"  Step2 unplanned reboots/30d = {s['step2_reboots']}")
    print(f"  Step3 RAS silent = {s['step3_ras_silent']}")
    print(f"  Step4 concentration = {s['step4_concentration']*100:.1f}%")
    print(f"  Step5 weighted types = {s['step5_weighted_types'] or '-'}")
    print(f"  Step6 misdiagnoses/30d = {s['step6_service_history']}")
    print(f"  Step7 FA repro = {s['step7_fa_repro']}")
    print("正向规则命中:")
    for r in v["rules_hit"]:
        print(f"  {r['rule']}: {r['desc']}")
    if v["rules_negative"]:
        print("负向规则命中（排除）:")
        for r in v["rules_negative"]:
            print(f"  {r['rule']}: {r['desc']}")


if __name__ == "__main__":
    main()
