#!/usr/bin/env python3
"""Generate MMU_E2E_V2_FINAL delivery derived artifacts (no experiment changes).

Reads ONLY authoritative existing artifacts (per_condition.json,
experiment_status.csv, run manifests, retry2 indices, oracle terminal lines)
and emits the derived CSVs / per-sample paths / per-model stats required by the
V2 independent-acceptance packaging.

Nothing here re-runs an experiment, edits a conclusion, or changes frozen
fault semantics.
"""
import csv
import gzip
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "campaign"))
import control_map  # noqa: E402
import oracle  # noqa: E402
DELIVERY = os.path.join(ROOT, "exports", "MMU_E2E_V3_FINAL_DELIVERY")
RUNS = os.path.join(ROOT, "runs", "W5X3")
RETRY = os.path.join(ROOT, "runs", "W5X3_RETRY")
RETRY2 = os.path.join(ROOT, "runs", "W5X3_RETRY2")
ANALYSIS = os.path.join(ROOT, "analysis")
COND = os.path.join(ROOT, "campaign", "conditions.json")


def load(p, d=None):
    try:
        with open(p) as f:
            return json.load(f)
    except (OSError, ValueError):
        return d


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def read_csv(p):
    with open(p, newline="") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------------------
# authoritative sources
# ---------------------------------------------------------------------------
conds = load(COND, [])
status = {r["NewSampleRunID"]: r for r in read_csv(os.path.join(ROOT, "experiment_status.csv"))}
per = {p["NewSampleRunID"]: p for p in load(os.path.join(ANALYSIS, "per_condition.json"), [])}
r2 = load(os.path.join(ANALYSIS, "retry2_map.json"), {})
r2ev = load(os.path.join(ANALYSIS, "retry2_evidence_index.json"), {})
r1 = load(os.path.join(ANALYSIS, "retry_map.json"), {})
runman = load(os.path.join(ROOT, "run_manifest.json"), {})
accept = load(os.path.join(ROOT, "acceptance.json"), {})
cmap = {c["NewSampleRunID"]: c for c in conds}
# Authoritative ControlRunID (actual run dir) per sample, from the build-matched
# control map — NOT the plan's logical ControlID.  The plan `conditions.json` only
# names CTRL-{Model}-{Context}; the real dir may carry -PFN / -DECOY / CTRL2 /
# CTRL2B suffixes.  Using the plan ID here previously reported wrong ControlRunIDs.
ctrl_runid = {c["SampleRunID"]: c.get("ControlRunID", "")
              for c in load(os.path.join(ANALYSIS, "control_map.json"), [])}


def resolve_manifest(sid):
    """-> (manifest, run_id, run_kind) honouring retry2 > retry > original."""
    if sid in r2:
        rid = r2[sid]
        return load(os.path.join(RETRY2, rid, "manifest.json"), {}), rid, "retry2"
    if sid in r1:
        rid = r1[sid]
        return load(os.path.join(RETRY, rid, "manifest.json"), {}), rid, "retry"
    return load(os.path.join(RUNS, sid, "manifest.json"), {}), sid, "original"


def trace_info(sid):
    man, rid, kind = resolve_manifest(sid)
    if not man:
        return None
    return {
        "run_id": rid,
        "kind": kind,
        "trace": man.get("trace", ""),
        "trace_sha256": man.get("trace_sha256", ""),
        "build_hash": man.get("gem5_sha256", ""),
        "terminal": man.get("terminal", ""),
        "terminal_sha256": man.get("terminal_sha256", ""),
        "control_id": ctrl_runid.get(sid, ""),
        "returncode": man.get("returncode", ""),
        "activation_count": man.get("activation_count", ""),
        "ordinal": man.get("ordinal", ""),
    }


def oracle_lines(man):
    return oracle.oracle_lines(man.get("terminal_lines") or [])


def fault_lines(sid):
    man, _, _ = resolve_manifest(sid)
    return man, oracle_lines(man)


_ctrl_reg = control_map.registry()


def control_manifest(sid):
    """Build-matched control for a sample (never a cross-build substitute)."""
    c = cmap.get(sid, {})
    man, _, _ = resolve_manifest(sid)
    crec, _ = control_map.resolve_control(
        c.get("ModelID", ""), c.get("NewContext", ""),
        man.get("gem5_sha256", ""), _ctrl_reg)
    return (crec or {}).get("manifest") or {}, c.get("ControlID", "")


# ---------------------------------------------------------------------------
# round-0202b -> 0202c previous state of the 23 PARTIAL samples
# ---------------------------------------------------------------------------
PREV_STATE = {
    "M03-C02": ("PARTIAL_ARCHITECTURE",
                "IFU response / IFU decode / per-instruction commit "
                "(Execute fetch boundary, NOT_EMITTED_BY_FROZEN_BINARY)"),
    "M04-C02": ("PARTIAL_ARCHITECTURE",
                "IFU response / IFU decode / per-instruction commit "
                "(Execute fetch boundary, NOT_EMITTED_BY_FROZEN_BINARY)"),
    "M05-C02": ("PARTIAL_ARCHITECTURE",
                "IFU response / IFU decode / per-instruction commit "
                "(Execute fetch boundary, NOT_EMITTED_BY_FROZEN_BINARY)"),
    "M07-C05": ("PARTIAL_ARCHITECTURE",
                "IFU response / IFU decode / per-instruction commit "
                "(Execute fetch boundary, NOT_EMITTED_BY_FROZEN_BINARY)"),
    "M05-C03": ("PARTIAL_ARCHITECTURE",
                "LSU response / rf_writeback / commit (masking mechanism not "
                "event-evidenced)"),
    "M05-C04": ("PARTIAL_ARCHITECTURE",
                "LSU response / rf_writeback / commit (committing consumer "
                "NOT_OBSERVED)"),
    "M05-C05": ("PARTIAL_ARCHITECTURE",
                "LSU response / rf_writeback / commit (committing consumer "
                "NOT_OBSERVED)"),
    "M07-C02": ("PARTIAL_ARCHITECTURE",
                "response / writeback / consumer / commit (ROI ended before the "
                "granted request completed; masked_reason="
                "request_issued_not_completed_at_roi_end)"),
}

NEW_STAGES = {
    "M03-C02": "ifu_response + ifu_decode + fault-tagged commit (real IFU pipeline)",
    "M04-C02": "ifu_response + ifu_decode + fault-tagged commit (real IFU pipeline)",
    "M05-C02": "ifu_response + ifu_decode + fault-tagged commit (real IFU pipeline)",
    "M07-C05": "ifu_response + ifu_decode + fault-tagged commit (real IFU pipeline)",
    "M05-C03": "memory_response + rf_writeback + consumer(consumer_of) + "
               "consumer commit (weak/dead consumer, value discarded)",
    "M05-C04": "memory_response + rf_writeback + consumer(consumer_of) + "
               "consumer commit (committing data consumer at 0x401bb4)",
    "M05-C05": "memory_response + rf_writeback + consumer(consumer_of) + "
               "consumer commit (committing data consumer at 0x401b50)",
    "M07-C02": "translation_result + lsu_request issued, then ROI ended "
               "(request_issued_not_completed_at_roi_end) -> "
               "REQUEST_PENDING_AT_ROI_END (PARTIAL, not FULL)",
}

INSTRUMENT = {
    "M03-C02": "CHAOSPropagation mmuTakeFetchTxn/mmuNoteIfuResponse/mmuRegisterFetchSeq "
               "+ fetch.cc fetchBufferTxnId; ifu_response/ifu_decode events",
    "M04-C02": "CHAOSPropagation mmuTakeFetchTxn/mmuNoteIfuResponse/mmuRegisterFetchSeq "
               "+ fetch.cc fetchBufferTxnId; ifu_response/ifu_decode events",
    "M05-C02": "CHAOSPropagation mmuTakeFetchTxn/mmuNoteIfuResponse/mmuRegisterFetchSeq "
               "+ fetch.cc fetchBufferTxnId; ifu_response/ifu_decode events",
    "M07-C05": "CHAOSPropagation mmuTakeFetchTxn/mmuNoteIfuResponse/mmuRegisterFetchSeq "
               "+ fetch.cc fetchBufferTxnId; ifu_response/ifu_decode events",
    "M05-C03": "mmuNoteEntryInsert poisoned-DTB registration + tlb.cc M05 warm-hit "
               "adoption (MMU_CONSUMER_REUSE_CAP=16)",
    "M05-C04": "mmuNoteEntryInsert poisoned-DTB registration + tlb.cc M05 warm-hit "
               "adoption (MMU_CONSUMER_REUSE_CAP=16)",
    "M05-C05": "mmuNoteEntryInsert poisoned-DTB registration + tlb.cc M05 warm-hit "
               "adoption (MMU_CONSUMER_REUSE_CAP=16)",
    "M07-C02": "mmu_fault_summary masked_reason field",
}

CONCLUSION = {
    "M03-C02": "新增原始事件后补全",
    "M04-C02": "新增原始事件后补全",
    "M05-C02": "新增原始事件后补全",
    "M07-C05": "新增原始事件后补全",
    "M05-C03": "新增原始事件后补全",
    "M05-C04": "新增原始事件后补全",
    "M05-C05": "新增原始事件后补全",
    "M07-C02": "请求在 ROI 结束前未完成，正确重分类为 "
               "REQUEST_PENDING_AT_ROI_END（PARTIAL），不再误标为 FULL/MASKED",
}

PREV_BUILD = ""  # filled from the original manifest


def group_key(model, ctx):
    return "%s-%s" % (model, ctx)


def main():
    os.makedirs(DELIVERY, exist_ok=True)
    os.makedirs(os.path.join(DELIVERY, "per_sample_e2e_paths"), exist_ok=True)

    # ------------------------------------------------------------------
    # partial23_repair_comparison.csv
    # ------------------------------------------------------------------
    partial23 = [sid for sid in sorted(r2) if r2[sid]]
    cols = ["SampleRunID", "ModelID", "ContextID", "TimingID",
            "PreviousCompleteness", "FinalCompleteness",
            "PreviousMissingStages", "NewlyObservedStages",
            "InstrumentationAdded", "RerunPerformed", "OriginalRunID",
            "NewRunID", "OriginalBuildHash", "NewBuildHash", "NewTracePath",
            "NewTraceSHA256", "NewlyEstablishedCausalEdges",
            "FinalTerminalEvent", "FinalSoftwareSymptom", "OracleEvidence",
            "RemainingMissingStages", "RepairConclusion"]
    rows = []
    for sid in partial23:
        c = cmap[sid]
        model, ctx, tidx = c["ModelID"], c["NewContext"], c["TimingID"]
        key = group_key(model, ctx)
        prev_comp, prev_missing = PREV_STATE[key]
        st = status[sid]
        ch = (per.get(sid) or {}).get("Chain") or {}
        edges = ch.get("edges", [])
        term = ch.get("terminal") or {}
        term_ev = "%s(%s)" % (term.get("event_id", ""), term.get("kind", ""))
        # original build hash from the original run manifest
        orig_man = load(os.path.join(RUNS, sid, "manifest.json"), {})
        orig_build = orig_man.get("gem5_sha256", "")
        # new build hash / trace from retry2 index
        n = r2ev.get(sid, {})
        new_build = n.get("gem5_sha256", "")
        new_trace = n.get("trace", "")
        new_sha = n.get("trace_sha256", "")
        # newly established edges = non-UNKNOWN edge bases, and the NEW kinds
        bases = [e.get("basis") for e in edges if e.get("basis") != "UNKNOWN"]
        new_edge_desc = "; ".join(
            sorted(set("%s" % b for b in bases))) or "none"
        unobs = ch.get("unobserved", []) or []
        # software symptom from oracle
        man, fl = fault_lines(sid)
        symptom = symptom_for(model, ctx, st.get("TerminalState", ""), fl)
        oracle_ev = " | ".join(fl[:2]) if fl else "n/a"
        rows.append({
            "SampleRunID": sid,
            "ModelID": model,
            "ContextID": ctx,
            "TimingID": tidx,
            "PreviousCompleteness": prev_comp,
            "FinalCompleteness": st.get("Completeness", ""),
            "PreviousMissingStages": prev_missing,
            "NewlyObservedStages": NEW_STAGES[key],
            "InstrumentationAdded": INSTRUMENT[key],
            "RerunPerformed": "True",
            "OriginalRunID": sid,
            "NewRunID": n.get("retry_run_id", ""),
            "OriginalBuildHash": orig_build,
            "NewBuildHash": new_build,
            "NewTracePath": new_trace,
            "NewTraceSHA256": new_sha,
            "NewlyEstablishedCausalEdges": new_edge_desc,
            "FinalTerminalEvent": term_ev,
            "FinalSoftwareSymptom": symptom,
            "OracleEvidence": oracle_ev,
            "RemainingMissingStages": ";".join(unobs) if unobs else "none",
            "RepairConclusion": CONCLUSION[key],
        })
    with open(os.path.join(DELIVERY, "partial23_repair_comparison.csv"),
              "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print("partial23_repair_comparison.csv:", len(rows), "rows")

    # ------------------------------------------------------------------
    # terminal_symptoms.csv (all 117 executed + 3 N/A)
    # ------------------------------------------------------------------
    tcols = ["SampleRunID", "ModelID", "ContextID", "TimingID",
             "MicroarchTerminal", "ArchStateImpact", "SoftwareSymptom",
             "FaultOracle", "GoldenOracle", "ExitCodeOrSignal", "ActualValue",
             "TerminalEventID", "TerminalEventKind", "EvidenceSufficiency"]
    trows = []
    for sid in sorted(status):
        st = status[sid]
        c = cmap[sid]
        model, ctx = c["ModelID"], c["NewContext"]
        term_state = st.get("TerminalState", "") or "N/A"
        man, fl = fault_lines(sid)
        cman, cid = control_manifest(sid)
        cl = oracle_lines(cman)
        ch = (per.get(sid) or {}).get("Chain") or {}
        term = ch.get("terminal") or {}
        symptom = symptom_for(model, ctx, term_state, fl)
        exit_sig = exit_signal_for(fl)
        actual = actual_value_for(man, fl)
        arch_impact = arch_impact_for(term_state, model)
        sufficiency = "FULL" if st.get("Completeness") == "FULL" else \
            ("N/A" if term_state == "N/A" else "PARTIAL")
        trows.append({
            "SampleRunID": sid,
            "ModelID": model,
            "ContextID": ctx,
            "TimingID": c["TimingID"],
            "MicroarchTerminal": term_state,
            "ArchStateImpact": arch_impact,
            "SoftwareSymptom": symptom,
            "FaultOracle": " | ".join(fl) if fl else "n/a",
            "GoldenOracle": " | ".join(cl) if cl else "n/a",
            "ExitCodeOrSignal": exit_sig,
            "ActualValue": actual,
            "TerminalEventID": term.get("event_id", ""),
            "TerminalEventKind": term.get("kind", ""),
            "EvidenceSufficiency": sufficiency,
        })
    with open(os.path.join(DELIVERY, "terminal_symptoms.csv"), "w",
              newline="") as f:
        w = csv.DictWriter(f, fieldnames=tcols)
        w.writeheader()
        w.writerows(trows)
    print("terminal_symptoms.csv:", len(trows), "rows")

    # ------------------------------------------------------------------
    # authoritative_trace_index.csv (all 120)
    # ------------------------------------------------------------------
    icols = ["SampleRunID", "ActualRunID", "RunKind", "TracePath",
             "TraceSHA256", "BuildHash", "ControlRunID", "ActivationEventID",
             "ReturnCode", "ActivationCount", "TargetOrdinal",
             "AnalyzedFileVersion"]
    irows = []
    for sid in sorted(status):
        info = trace_info(sid)
        c = cmap[sid]
        ch = (per.get(sid) or {}).get("Chain") or {}
        act = ch.get("root") or {}
        st = status[sid]
        if info is None:
            irows.append({"SampleRunID": sid, "ActualRunID": "",
                          "RunKind": "missing", "TracePath": "",
                          "TraceSHA256": "", "BuildHash": "",
                          "ControlRunID": ctrl_runid.get(sid, ""),
                          "ActivationEventID": "", "ReturnCode": "",
                          "ActivationCount": "", "TargetOrdinal": "",
                          "AnalyzedFileVersion": "n/a"})
            continue
        irows.append({
            "SampleRunID": sid,
            "ActualRunID": info["run_id"],
            "RunKind": info["kind"],
            "TracePath": info["trace"],
            "TraceSHA256": info["trace_sha256"],
            "BuildHash": info["build_hash"],
            "ControlRunID": info["control_id"],
            "ActivationEventID": act.get("event_id", ""),
            "ReturnCode": info["returncode"],
            "ActivationCount": info["activation_count"],
            "TargetOrdinal": st.get("TargetOrdinal", ""),
            "AnalyzedFileVersion": info["trace"],
        })
    with open(os.path.join(DELIVERY, "authoritative_trace_index.csv"),
              "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=icols)
        w.writeheader()
        w.writerows(irows)
    print("authoritative_trace_index.csv:", len(irows), "rows")

    # ------------------------------------------------------------------
    # per-model completeness
    # ------------------------------------------------------------------
    from collections import Counter, defaultdict
    by_model = defaultdict(lambda: Counter())
    for sid, st in status.items():
        by_model[cmap[sid]["ModelID"]][st.get("Completeness", "MISSING")] += 1
    mcols = ["ModelID", "Total", "FULL", "PARTIAL", "N/A",
             "DominantTerminal"]
    mrows = []
    term_by_model = defaultdict(Counter)
    for sid, st in status.items():
        term_by_model[cmap[sid]["ModelID"]][st.get("TerminalState", "")] += 1
    for m in sorted(by_model):
        d = by_model[m]
        tc = term_by_model[m]
        dom = max(tc, key=tc.get) if tc else ""
        part = sum(v for k, v in d.items() if k.startswith("PARTIAL"))
        mrows.append({"ModelID": m, "Total": sum(d.values()),
                      "FULL": d.get("FULL", 0), "PARTIAL": part,
                      "N/A": d.get("FILE_MISSING", 0) + d.get("N/A", 0),
                      "DominantTerminal": dom})
    with open(os.path.join(DELIVERY, "per_model_completeness.csv"), "w",
              newline="") as f:
        w = csv.DictWriter(f, fieldnames=mcols)
        w.writeheader()
        w.writerows(mrows)
    print("per_model_completeness.csv:", len(mrows), "rows")

    # ------------------------------------------------------------------
    # per_sample_e2e_paths/*.md (117 executed samples)
    # ------------------------------------------------------------------
    generated = 0
    for sid in sorted(status):
        if sid not in per:
            continue
        write_sample_md(sid)
        generated += 1
    print("per_sample_e2e_paths:", generated, "files")

    # ------------------------------------------------------------------
    # copy authoritative CSVs/JSONs into delivery
    # ------------------------------------------------------------------
    for name in ["experiment_status.csv", "per_condition.json",
                 "propagation_chains.csv", "chain_edges.csv",
                 "chain_branches.csv", "completeness.csv",
                 "fault_control_compare.csv", "summary_by_model.csv",
                 "timing_map.csv", "retry2_map.json",
                 "retry2_evidence_index.json"]:
        src = os.path.join(ANALYSIS, name)
        if os.path.isfile(src):
            import shutil
            shutil.copy2(src, os.path.join(DELIVERY, name))
    # acceptance + final report
    for name in ["acceptance.json", "final_acceptance.md"]:
        import shutil
        src = os.path.join(ROOT, name)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(DELIVERY, name))
    # conditions.json + context_map
    import shutil
    shutil.copy2(COND, os.path.join(DELIVERY, "conditions.json"))
    print("copied authoritative artifacts")


# ---------------------------------------------------------------------------
# symptom / signal helpers
# ---------------------------------------------------------------------------
def _first(fl, key):
    for l in fl:
        m = re.search(key + r"=(\S+)", l)
        if m:
            return m.group(1)
    return ""


def symptom_for(model, ctx, term_state, fl):
    if term_state == "N/A" or term_state == "":
        return "N/A (not executed: M06-C05 speculative wrong-path feasibility boundary)"
    if term_state == "SDC":
        if model == "M03":
            return ("错误计算结果：读取到跨 ASID 标记 0xa5（预期 0x5a）——"
                    "错误取指/翻译导致错误值")
        if model == "M04":
            return ("错误数据：读取到 decoy sentinel 0x51（预期 0x7d）——"
                    "ITLB PFN 替换导致错误取指")
        if model == "M05":
            return ("错误数据：读取到 decoy sentinel 0x51（预期 0x7d）——"
                    "partial 表基替换导致错误数据")
        if model == "M07":
            if ctx == "C05":
                return ("权限绕过/非法执行：间接分支跳转到 XN 页并成功执行"
                        "（预期 SIGSEGV 被拦截），result=FAIL")
            return "错误结果：grant 反转使本应被拒的访问成功"
        if model == "M08":
            return "错误数据/地址：请求 PA bit-12 翻转后读取到错误数据"
        if model == "M01":
            return "错误数据：保留的 stale-PA entry 被复用，读到陈旧数据"
        if model == "M02":
            return "错误数据：PFN bit-0 翻转，读到相邻页数据"
        return "错误结果（SDC）"
    if term_state == "ACTIVATED_MASKED":
        if model == "M05":
            return "被掩盖且输出正确：decoy 值被消费/提交但未影响最终输出（weak consumer）"
        if model == "M07":
            return "被掩盖：read-exec-only 仍被拒绝（grant 反转未消费，masked_reason 显式）"
        if model == "M01" or model == "M02" or model == "M04":
            return "被掩盖且输出正确"
        return "被掩盖且输出正确"
    if term_state == "ACTIVATED_UNCONSUMED":
        return "未消费：故障 armed 后无后续访问消费（自然终止）"
    if term_state == "REQUEST_PENDING_AT_ROI_END":
        return ("请求在 ROI 结束时仍未完成：翻译已授权并发出 LSU 请求，但无 "
                "memory response / consumer / commit / 异常投递"
                "（masked_reason=request_issued_not_completed_at_roi_end）")
    if term_state == "PROPAGATED_BUT_SQUASHED":
        return "推测执行被 Squash：错误路径指令在提交前被冲刷"
    if term_state == "DETECTED_LOCALLY":
        return "MMU 检测并本地阻断：非法描述符被识别，未投递异常"
    if term_state == "DETECTED_DELIVERED":
        return "MMU 检测并投递异常（权限/预取异常，SIGSEGV）"
    return term_state


def exit_signal_for(fl):
    return oracle.exit_signal_from(
        [l for l in fl if oracle.ORACLE_RE.match(l)])


def actual_value_for(man, fl):
    # multi-episode W13 interleaves PASS (0x7d) and FAIL (0x51) episodes; the
    # fault's ActualValue is the observed of a FAIL episode, never the first
    # PASS episode's 0x7d.
    term = man.get("terminal_lines") or []
    return oracle.actual_value_from_fail(term)


def arch_impact_for(term_state, model):
    if term_state == "SDC":
        return "错误微架构状态被提交为错误架构状态（错误寄存器/内存值）"
    if term_state == "ACTIVATED_MASKED":
        return "错误状态被消费但架构状态最终正确（无可见影响）"
    if term_state == "ACTIVATED_UNCONSUMED":
        return "故障状态未被任何后续访问消费"
    if term_state == "REQUEST_PENDING_AT_ROI_END":
        return "请求已发出但 ROI 结束前未完成（无 response/consumer/commit/异常投递）"
    if term_state == "PROPAGATED_BUT_SQUASHED":
        return "错误状态到达执行/缓存但指令被冲刷，架构状态未改变"
    if term_state == "DETECTED_LOCALLY":
        return "MMU 本地检测，无异常投递，架构状态未改变"
    if term_state == "DETECTED_DELIVERED":
        return "异常投递到软件（SIGSEGV），架构状态回退"
    return "N/A"


# ---------------------------------------------------------------------------
# per-sample markdown
# ---------------------------------------------------------------------------
def write_sample_md(sid):
    st = status[sid]
    c = cmap[sid]
    ch = (per.get(sid) or {}).get("Chain") or {}
    info = trace_info(sid)
    man, fl = fault_lines(sid)
    cman, cid = control_manifest(sid)
    cl = oracle_lines(cman)

    model, ctx = c["ModelID"], c["NewContext"]
    term_state = st.get("TerminalState", "")
    term = ch.get("terminal") or {}
    root = ch.get("root") or {}
    mut = ch.get("mutation") or {}
    stages = ch.get("stages") or {}
    edges = ch.get("edges", [])
    branches = ch.get("branches", [])
    summary = ch.get("summary") or {}

    lines = []
    lines.append("# %s propagation path\n" % sid)
    lines.append("- Model: %s  Context: %s  Timing: %s" %
                 (model, ctx, c["TimingID"]))
    lines.append("- TerminalState: %s  Completeness: %s" %
                 (term_state, st.get("Completeness", "")))
    lines.append("")

    # Fault location
    lines.append("## Fault Location")
    where = c.get("FrozenWhereSource", "") or "n/a"
    inv = c.get("MutationInvariant", "") or "n/a"
    lines.append("- Where (frozen): %s" % where)
    lines.append("- Mutation: %s" % inv)
    lines.append("- Target field/op: %s" % (mut.get("kind", "") or "n/a"))
    lines.append("")

    # Activation
    lines.append("## Activation")
    lines.append("- EventID=%s Tick=%s Kind=%s" %
                 (root.get("event_id", ""), root.get("tick", ""),
                  root.get("kind", "")))
    lines.append("- fault_id=%s translation_id=%s dyn_inst_seq=%s" %
                 (root.get("fault_id", ""), root.get("translation_id", ""),
                  root.get("dyn_inst_seq", "")))
    lines.append("- before/after: %s -> %s" %
                 (root.get("before", "") or root.get("old_pfn", "") or
                  root.get("permission_before", ""),
                  root.get("after", "") or root.get("new_pfn", "") or
                  root.get("permission_after", "")))
    lines.append("")

    # Propagation (ordered stages)
    lines.append("## Propagation")
    order = ["activation", "mutation", "translation", "request", "response",
             "writeback", "consumer", "commit_squash"]
    for name in order:
        ev = stages.get(name)
        if not ev:
            continue
        lines.append("- %s: %s(%s) @%s tid=%s seq=%s" %
                     (name, ev.get("event_id", ""), ev.get("kind", ""),
                      ev.get("tick", ""), ev.get("translation_id", ""),
                      ev.get("dyn_inst_seq", "")))
    lines.append("- causal edges: %s" %
                 ("; ".join("%s->%s(%s)" % (e.get("source", ""),
                                            e.get("target", ""),
                                            e.get("basis", ""))
                            for e in edges) or "none"))
    if branches:
        lines.append("- branches: %s" % "; ".join(
            "tid=%s term=%s commit=%s squash=%s" %
            (b.get("translation_id", ""), b.get("terminal_kind", ""),
             b.get("commits", ""), b.get("squashed", ""))
            for b in branches))
    lines.append("")

    # Terminal
    lines.append("## Terminal")
    lines.append("- terminal: %s(%s) @%s" %
                 (term.get("event_id", ""), term.get("kind", ""),
                  term.get("tick", "")))
    lines.append("- terminal state: %s" % term_state)
    if summary:
        lines.append("- summary: outcome=%s masked_reason=%s state_consumed=%s" %
                     (summary.get("outcome", ""), summary.get("masked_reason", ""),
                      summary.get("state_consumed", "")))
    lines.append("")

    # Software symptom
    lines.append("## Software Symptom")
    lines.append("- symptom: %s" % symptom_for(model, ctx, term_state, fl))
    lines.append("- fault oracle: %s" % (" | ".join(fl) if fl else "n/a"))
    lines.append("- golden oracle: %s" % (" | ".join(cl) if cl else "n/a"))
    lines.append("")

    # Evidence
    lines.append("## Evidence")
    if info:
        lines.append("- trace: %s" % info["trace"])
        lines.append("- trace SHA256: %s" % info["trace_sha256"])
        lines.append("- build SHA256: %s" % info["build_hash"])
        lines.append("- control: %s" % cid)
    lines.append("")

    # Missing evidence
    lines.append("## Missing Evidence")
    unobs = ch.get("unobserved", []) or []
    lines.append("- %s" % ("; ".join(unobs) if unobs else "none"))
    lines.append("")

    with open(os.path.join(DELIVERY, "per_sample_e2e_paths",
                           sid + ".md"), "w") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
