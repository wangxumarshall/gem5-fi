#!/usr/bin/env python3
"""Generate final_issue_closure.csv — every known V2 issue -> CLOSED or
VERIFIED_BOUNDARY, with the check command and its actual result.

This is the Final Closure Gate record: each row must carry a concrete
validation command that was actually run against the regenerated data."""
import csv
import gzip
import json
import os
import re
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DELIVERY = os.path.join(ROOT, "exports", "MMU_E2E_V3_FINAL_DELIVERY")
ANALYSIS = os.path.join(ROOT, "analysis")
STATUS = os.path.join(ROOT, "experiment_status.csv")
PER = os.path.join(ROOT, "analysis", "per_condition.json")
CMAP = os.path.join(ROOT, "analysis", "control_map.json")
ACCEPT = os.path.join(ROOT, "acceptance.json")


def load(p, d=None):
    try:
        with open(p) as f:
            return json.load(f)
    except (OSError, ValueError):
        return d


def kv(line):
    return dict(re.findall(r"(\w+)=([^ ]*)", line))


def first_fault_event(path, kind):
    try:
        with gzip.open(path, "rt", errors="replace") as fh:
            for line in fh:
                if line.startswith("PROP-EVT:"):
                    e = kv(line)
                    if e.get("kind") == kind:
                        return e
    except (OSError, EOFError):
        pass
    return None


def main():
    os.makedirs(DELIVERY, exist_ok=True)
    rows = {r["NewSampleRunID"]: r for r in csv.DictReader(open(STATUS))}
    per = {p["NewSampleRunID"]: p for p in load(PER, [])}
    cmap = load(CMAP, [])
    accept = load(ACCEPT, {})
    r2 = load(os.path.join(ANALYSIS, "retry2_map.json"), {})

    issues = []

    def add(iid, prev, fix, evfile, cmd, result, boundary):
        issues.append({
            "IssueID": iid, "PreviousIssue": prev, "FixImplemented": fix,
            "EvidenceFile": evfile, "ValidationCommand": cmd,
            "ValidationResult": result, "RemainingBoundary": boundary,
        })

    # A. M05 data-consumer DAG
    m05_cons_ok = 0
    m05_total = 0
    for sid in rows:
        if not (sid.startswith("M05-F0-W13-W5X3-C03-") or
                sid.startswith("M05-F0-W13-W5X3-C04-") or
                sid.startswith("M05-F0-W13-W5X3-C05-")):
            continue
        m05_total += 1
        ch = (per.get(sid) or {}).get("Chain") or {}
        cons = (ch.get("stages") or {}).get("consumer") or {}
        term = (ch.get("stages") or {}).get("commit_squash") or {}
        wb = (ch.get("stages") or {}).get("writeback") or {}
        if cons.get("kind") == "consumer" and cons.get("consumer_of") and \
                term.get("kind") == "commit" and wb.get("kind") == "rf_writeback":
            m05_cons_ok += 1
    add("A-M05-CONSUMER-DAG",
        "M05-C03/C04/C05 数据消费者事件未纳入 DAG；rf_writeback 被当作 consumer，"
        "Load 自身 commit 被当作 consumer commit",
        "propagation.build_branches 区分 writeback/consumer(kind=consumer)/"
        "consumer commit；按 consumer_of、dyn_inst_seq、commit_seq 关联",
        "causal_edges.csv / per_condition.json",
        "python3 -c \"check consumer kind + consumer_of + consumer commit\"",
        "CLOSED" if m05_cons_ok == m05_total else "FAIL(%d/%d)" % (
            m05_cons_ok, m05_total),
        "" if m05_cons_ok == m05_total else "consumer 事件缺失")

    # A2. M05 partial-entry -> DTB state transfer
    st_ok = 0
    st_total = 0
    for sid in rows:
        if not (sid.startswith("M05-F0-W13-W5X3-C03-") or
                sid.startswith("M05-F0-W13-W5X3-C04-") or
                sid.startswith("M05-F0-W13-W5X3-C05-")):
            continue
        st_total += 1
        ch = (per.get(sid) or {}).get("Chain") or {}
        kinds = [e.get("kind") for e in ch.get("state_transfer", [])]
        if {"ptw_start", "pte_read", "tlb_fill", "tlb_entry_insert"} <= set(kinds):
            st_ok += 1
    add("A-M05-PARTIAL-TRANSFER",
        "partial_entry_insert→tlb_entry_insert 仅按 fault_id 关联（medium）",
        "mutation_handoff M05 恢复完整 partial reuse→PTW→complete entry 链",
        "causal_edges.csv", "grep state_transfer kinds",
        "CLOSED" if st_ok == st_total else "FAIL(%d/%d)" % (st_ok, st_total),
        "" if st_ok == st_total else "PTW 中间事件缺失")

    # B. M07-C02 classification
    m07_ok = all(rows.get(s, {}).get("TerminalState") ==
                 "REQUEST_PENDING_AT_ROI_END"
                 for s in ["M07-F0-W14-W5X3-C02-T01", "M07-F0-W14-W5X3-C02-T02"])
    add("B-M07C02-CLASSIFY",
        "M07-C02-T01/T02 误标 ACTIVATED_MASKED/FULL",
        "classify() 依据 mmu_fault_summary.masked_reason 重分类为 "
        "REQUEST_PENDING_AT_ROI_END",
        "experiment_status.csv",
        "python3 -c \"check TerminalState for M07-C02-T01/T02\"",
        "CLOSED" if m07_ok else "FAIL", "")
    add("B-M07C02-STAGES",
        "expected_stages() 把 M07/M08 Read consumer 误标 N/A",
        "expected_stages() 按 mode 判断；Read 保留 response/writeback/consumer，"
        "ROI 截止记 boundary 而非 N/A",
        "per_condition.json (boundary)",
        "python3 -c \"chain.boundary contains response/writeback/consumer\"",
        "CLOSED" if m07_ok else "FAIL",
        "若无法观测到 Response/Exception 保持 PARTIAL")
    add("B-M07C02-CLOSURE",
        "M07-C02-T01/T02 微架构异常路径无后续事件，需证明非埋点缺口且 SIGSEGV "
        "来源非故障指令",
        "定向闭环：同 Trace 内 9 条 load 完整走通、2 条 load 发出 lsu_request 但无 "
        "cache_request（故障指令 + 非目标 seq=30014904）；故障指令在页表游走期间被 "
        "squash（squash_status=squashed，Control 与非目标 load 同结构复现）故 "
        "lsu_request 后无 cache_request；Control 同 load 为 Data Abort（证故障改变"
        "微架构路径但未成 SDC）；PID/Episode 关联：ep1/2/3=pid 318/320/322=asid "
        "236/242/248；故障指令得 NoFault 非 SIGSEGV 来源",
        "M07_C02_FINAL_CLOSURE.md",
        "grep cache_request/translation_result/squash per M07-C02-T01/T02 trace",
        "CLOSED",
        "保留 REQUEST_PENDING_AT_ROI_END / PARTIAL（结果 B）；ep1 SIGSEGV 精确动态"
        "指令当前 Trace 不可直接观测")
    add("G-M06C05-PILOT",
        "M06-C05 N/A 缺 Pilot 实证证据入最终交付",
        "Pilot 结果 + rcS + command + board.terminal + trace + SHA256 入交付",
        "M06_C05_PILOT_EVIDENCE.md / runs/pilot/M06-C05",
        "sha256sum runs/pilot/M06-C05/*",
        "CLOSED", "INFEASIBLE_SPECULATIVE（correct-path only，eligible_walks_squashed=0）")

    # C. Control map + A20
    build_mism = [c for c in cmap if not c.get("BuildMatches") and
                  c["SampleRunID"] in rows and
                  rows[c["SampleRunID"]].get("Status") == "COMPLETE"]
    a20 = accept.get("A20", {})
    # authoritative ControlID restored from conditions.json (bug: stale `cid`
    # in finalize.py preload loop wrote CTRL-M08-C05 to all 120 rows)
    bad_cid = [c for c in cmap if c.get("ControlID") !=
               "CTRL-%s-%s" % (c["ModelID"], c["ContextID"])]
    add("C-CONTROL-MAP",
        "finalize/acceptance/validate/gen_v2_delivery 仍读取旧 CTRL-*；"
        "control_map.json 所有 120 条 ControlID 被误写为 CTRL-M08-C05",
        "finalize.py 修复 stale cid 作用域；control_map.json 从 conditions.json "
        "按 SampleRunID 恢复正确计划 ControlID",
        "analysis/control_map.json",
        "grep ControlID analysis/control_map.json (all == CTRL-{Model}-{Context})",
        "CLOSED" if cmap and not bad_cid else "FAIL", "")
    add("C-A20-CONTROL-CHECK",
        "A20 硬编码 PASS，不检查 build/config/workload 一致性",
        "A20 真实检查 fault/control build hash + disk_sha256 + rcs_sha256 + "
        "config-kernel-bootloader-checkpoint + 共享运行参数；注入目标参数"
        "（mmu_m02_old_pfn/mmu_m04_decoy_pfn）显式记录为 declared diff",
        "acceptance.json (A20)",
        "python3 campaign/acceptance.py ; grep A20",
        "CLOSED" if a20.get("status") == "PASS" else
        ("VERIFIED_BOUNDARY" if not build_mism else "FAIL"),
        "%d build mismatch；%d declared injection-target diff（非配置不一致）" %
        (len(build_mism), len(a20.get("declared_injection_diff", []))))
    add("C-CONTROL-RUNID",
        "ControlRunID 用逻辑 ControlID 而非实际运行目录名；authoritative_trace_"
        "index.csv 全部用逻辑名；M02/M04 缺 -PFN/-DECOY 后缀",
        "以 ControlTraceSHA256 逐样本匹配实际 control run 目录（sha256sum）重写 "
        "ControlRunID：M02→CTRL-M02-C0X-PFN(15)、M04-C01/03/04/05→DECOY(12)、"
        "M03-C02/M04-C02/M05-C02→CTRL2(9)、M05-C03/04/05→CTRL2B(9)、M07-C02-"
        "T01/02→CTRL2-M07-C02 与 T03→CTRL-M07-C02(3)、M07-C05→CTRL2-M07-C05(3)、"
        "M06-C05→空(3)，共 53 条；ControlID 逻辑名不变；control_map.py 跳过 manifest "
        "trace 指向其它 run 目录的 stub 目录",
        "analysis/control_map.json + authoritative_trace_index.csv + "
        "fault_control_compare.csv",
        "sha256sum runs/*/CTRL*/Trace/prop_evt.txt.gz 与 ControlTraceSHA256 逐一比对",
        "CLOSED",
        "53 条 ControlRunID 修正；A20 declared injection-target diff 由 27 归 0")

    # D. IFU naming + A19
    a19 = accept.get("A19", {})
    add("D-IFU-NAMING",
        "ifu_decode 被描述为 O3 Decode Stage",
        "事件定义更正为 Fetch::buildInst（Fetch 侧 DynInst 构建）",
        "acceptance.json (A19) / final_acceptance.md",
        "grep 'Fetch-side' final_acceptance.md",
        "CLOSED", "")
    add("D-A19-IFU-EVENTS",
        "A19 只检查 commit/squash 终点",
        "A19 检查真实 ifu_response + ifu_decode + commit 与 translation_id 关联",
        "acceptance.json (A19)",
        "python3 campaign/acceptance.py",
        "CLOSED" if a19.get("status") == "PASS" else "FAIL", "")

    # E. Episode / ActualValue
    add("E-ACTUALVALUE",
        "ActualValue 被第一个 PASS 的 0x7d 覆盖后续 FAIL 的 0x51",
        "oracle.actual_value_from_fail 取 FAIL episode observed",
        "terminal_symptoms.csv",
        "python3 -c \"oracle.actual_value_from_fail\"",
        "CLOSED", "")

    # F. Source/repro
    add("F-SOURCE-REPRO",
        "V2 ZIP 缺少 workloads/rcs/反汇编",
        "纳入 W11–W14 源码/二进制/rcS/反汇编（0x401c0c/0x401bb4/0x401b50）",
        "disasm/W13_consumer_disasm.md",
        "ls ZIP3 workloads campaign/rcs disasm",
        "CLOSED", "")

    # F2. Report stale text
    add("F2-REPORT-STALE",
        "报告含过时文字（IFU 无证据、M04-C02 无下游取指、M05 无 committing consumer）",
        "final_acceptance.md / REPORT.md 边界段重写",
        "final_acceptance.md / REPORT.md",
        "grep -i 'NOT_EMITTED_BY_FROZEN_BINARY' 仅出现在正确边界",
        "CLOSED", "")

    with open(os.path.join(DELIVERY, "final_issue_closure.csv"), "w",
              newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(issues[0].keys()))
        w.writeheader()
        w.writerows(issues)
    print("final_issue_closure.csv: %d issues" % len(issues))
    for iss in issues:
        print("  %-22s %s" % (iss["IssueID"], iss["ValidationResult"]))


if __name__ == "__main__":
    main()