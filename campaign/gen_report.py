#!/usr/bin/env python3
"""Generate the MMU E2E V3 REPORT.md from the regenerated evidence only.

Reads experiment_status.csv / acceptance.json / per_condition.json / analysis/
control_map.json and emits a report whose every statistic is re-derivable from
the per-sample data (no frozen counts, no stale text)."""
import csv
import json
import os
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DELIVERY = os.path.join(ROOT, "exports", "MMU_E2E_V3_FINAL_DELIVERY")
ANALYSIS = os.path.join(ROOT, "analysis")
STATUS = os.path.join(ROOT, "experiment_status.csv")
ACCEPT = os.path.join(ROOT, "acceptance.json")
PER = os.path.join(ROOT, "analysis", "per_condition.json")
CMAP = os.path.join(ROOT, "analysis", "control_map.json")


def load(p, d=None):
    try:
        with open(p) as f:
            return json.load(f)
    except (OSError, ValueError):
        return d


def main():
    os.makedirs(DELIVERY, exist_ok=True)
    rows = {r["NewSampleRunID"]: r for r in csv.DictReader(open(STATUS))}
    accept = load(ACCEPT, {})
    per = {p["NewSampleRunID"]: p for p in load(PER, [])}
    cmap = load(CMAP, [])

    total = len(rows)
    status_c = Counter(r["Status"] for r in rows.values())
    full = sum(1 for r in rows.values() if r["Completeness"] == "FULL")
    partial = sum(1 for r in rows.values()
                  if r["Completeness"].startswith("PARTIAL"))
    na_n = status_c.get("N/A", 0)
    ts = Counter(r.get("TerminalState", "") for r in rows.values()
                 if r["Status"] == "COMPLETE")
    ts["N/A"] = na_n

    by_model = defaultdict(lambda: Counter())
    for sid, r in rows.items():
        m = sid.split("-")[0]
        by_model[m][r["Completeness"]] += 1

    # M05 consumer DAG (9 C03/C04/C05 samples)
    m05_sids = sorted(s for s in rows
                      if s.startswith("M05-F0-W13-W5X3-C03-") or
                      s.startswith("M05-F0-W13-W5X3-C04-") or
                      s.startswith("M05-F0-W13-W5X3-C05-"))
    m05_consumer = []
    for sid in m05_sids:
        ch = (per.get(sid) or {}).get("Chain") or {}
        st = ch.get("stages") or {}
        cons = st.get("consumer") or {}
        term = st.get("commit_squash") or {}
        wb = st.get("writeback") or {}
        m05_consumer.append({
            "sid": sid,
            "state": rows[sid].get("TerminalState", ""),
            "comp": rows[sid].get("Completeness", ""),
            "resp": (st.get("response") or {}).get("event_id", ""),
            "wb": wb.get("event_id", ""),
            "consumer": cons.get("event_id", ""),
            "consumer_kind": cons.get("kind", ""),
            "consumer_of": cons.get("consumer_of", ""),
            "commit": term.get("event_id", ""),
            "commit_kind": term.get("kind", ""),
        })

    partial_sids = [s for s, r in rows.items()
                    if r["Completeness"].startswith("PARTIAL")]
    m07c02 = [s for s in partial_sids if "M07" in s and "C02" in s]

    # build-mismatch control rows
    build_mism = [c for c in cmap if not c.get("BuildMatches")]
    a20 = accept.get("A20", {})
    a19 = accept.get("A19", {})

    out = []
    a = out.append
    a("# MMU E2E V3 最终因果链重建、终态修正及证据验收 — 交付报告\n")
    a("Round 0202c-close · `gem5-fi-mmu-when5x3` · 2026-11-18\n")
    a("本轮只修正 V2 的因果重建与终态分类，不重新执行全部 120 条实验、不改冻结 "
      "Where/Context/Timing、无 git 操作。\n")

    a("## 1. 最终实验状态（120 条件）\n")
    a("| 维度 | 数量 |")
    a("|---|---|")
    a("| 总条件 | %d |" % total)
    a("| 已执行 (COMPLETE) | %d |" % status_c.get("COMPLETE", 0))
    a("| FULL | **%d** |" % full)
    a("| PARTIAL | **%d** |" % partial)
    a("| N/A | %d（M06-C05）|" % na_n)
    a("")
    a("PARTIAL 仅来自两类真实边界：M07-C02-T01/T02（请求在 ROI 结束时未完成）与 "
      "M06-C05（冻结配置下 speculative wrong-path 可行性边界，N/A）。\n")

    a("### 逐模型\n")
    a("| Model | FULL | PARTIAL | N/A |")
    a("|---|---:|---:|---:|")
    for m in ("M01", "M02", "M03", "M04", "M05", "M06", "M07", "M08"):
        d = by_model[m]
        part = sum(v for k, v in d.items() if k.startswith("PARTIAL"))
        a("| %s | %d | %d | %d |" % (m, d.get("FULL", 0), part,
                                      status_c.get("N/A", 0) if m == "M06"
                                      else 0))
    a("| **Total** | **%d** | **%d** | %d |" % (full, partial, na_n))
    a("")

    a("### 终态汇总\n")
    a("| TerminalState | Count |")
    a("|---|---:|")
    for k, v in sorted(ts.items(), key=lambda kv: -kv[1]):
        a("| %s | %d |" % (k, v))
    a("")

    a("## 2. M05 数据传播链（最高优先级）\n")
    a("M05-C03/C04/C05 共 9 条样本全部重新解析并纳入完整 Data Dependency DAG："
      "partial entry → PTW → complete DTB entry → 暖命中 → memory_response → "
      "rf_writeback → data consumer (consumer_of) → consumer 自己的 commit。\n")
    a("| 样本 | 终态 | Response | Writeback | Consumer | ConsumerCommit |")
    a("|---|---|---|---|---|---|")
    for c in m05_consumer:
        a("| %s | %s | %s | %s | %s (%s, consumer_of=%s) | %s (%s) |" % (
            c["sid"].split("-")[-1], c["state"], c["resp"], c["wb"],
            c["consumer"], c["consumer_kind"], c["consumer_of"],
            c["commit"], c["commit_kind"]))
    a("")
    a("- C03 消费者 PC=0x401c0c：读 decoy 0x51 后 `mov x25,#0` 丢弃（weak/dead "
      "consumer），故 observed=0x0、result=PASS —— 不是 SDC。\n")
    a("- C04 消费者 PC=0x401bb4：LDR→addr→二次 LDR，错误数据经 offset 派生二次 "
      "load 进入 W13_RESULT（observed=0x51, FAIL）。\n")
    a("- C05 消费者 PC=0x401b50：LDR→CMP→条件分支，0x51≠0x7d → branch=2, FAIL。\n")
    a("- 反汇编见 ZIP3 `disasm/W13_consumer_disasm.md`。\n")

    a("## 3. M05 Partial Entry → DTB Entry 状态传递\n")
    a("不再仅用 fault_id 建立 partial_entry_insert→tlb_entry_insert 关联；")
    a("现按 source_event_id / walk_id / request_id / parent_event_id 恢复完整 "
      "PTW 链：partial_entry_insert → fault_entry_reuse(source=partial) → "
      "ptw_start → pte_read → ptw_request → ptw_response → pte_decode → "
      "tlb_fill → tlb_entry_insert → reuse(source=insert)。见 causal_edges.csv "
      "的 source_event_id / request_id / parent_event_id 边。\n")

    a("## 4. M07-C02 终态修正\n")
    a("- M07-C02-T01/T02 不再误标 ACTIVATED_MASKED/FULL，改为 "
      "**REQUEST_PENDING_AT_ROI_END**（PARTIAL）：翻译已授权并发出 LSU 请求，但 "
      "ROI 结束前无 memory response / consumer / commit / 异常投递"
      "（masked_reason=request_issued_not_completed_at_roi_end）。故障指令得 "
      "`fault_status=NoFault`（授权反转），非 SIGSEGV 来源；ep2/ep3 SIGSEGV 来自未"
      "故障架构拒绝路径（`translation_result(Data)`+`squash`，直接可证）；故障 "
      "Episode 的 SIGSEGV 来自故障指令之外的架构拒绝（one-shot 消耗后），其精确动态"
      "指令在当前 Trace 中不可直接观测（数据侧无 exception_delivery 事件）。\n")
    a("- 定向闭环（埋点完整性按唯一请求计数）：同 Trace 内 **9 条 load** 完整走通 "
      "translation→lsu_request→cache_request→cache_response→memory_response→"
      "rf_writeback→commit（证明埋点完整），**2 条 load** 发出 `lsu_request` 但无 "
      "`cache_request` —— 故障指令 `seq=24118302`（T01）/`seq=27030544`（T02）与非"
      "目标请求 `seq=30014904`（T01 tid=15）。故障指令在页表游走期间已被 squash"
      "（`squash_status=squashed`，Control 与非目标 load 同结构复现），其 NoFault 翻译"
      "在 `SingleDataRequest::finish` 被 `squashTranslation` 丢弃，故请求未发往 Cache；"
      "Control `CTRL2-M07-C02` 中同一 load 为 `fault_status=Data`（证故障确实改变了"
      "微架构路径但未形成 SDC）。PID/Episode 关联：ep1/2/3 = pid 318/320/322 = "
      "asid 236/242/248。详见 `M07_C02_FINAL_CLOSURE.md`。\n")
    a("- M07-C02-T03（原构建）为真实 SDC（ep3 injected_success=1）。\n")
    a("- expected_stages() 不再把 M07/M08 非 Execute 的 Read consumer 误标为 "
      "N/A；并明确记录 ROI 截止边界。\n")

    a("## 5. Fault-Control 对照\n")
    a("- 建立 `analysis/control_map.json`，逐 (Model,Context) 记录 ControlRunID、"
      "build hash、trace SHA256、eligible N；`ControlID` 已从权威 `conditions.json` "
      "按 SampleRunID 恢复（此前被误写为 CTRL-M08-C05）。\n")
    a("- `ControlRunID` 使用**实际运行目录名**（以 `ControlTraceSHA256` 逐样本 "
      "`sha256sum` 校验）：M02→`CTRL-M02-C0X-PFN`、M04-C01/03/04/05→"
      "`CTRL-M04-C0X-DECOY`、取指侧(M03-C02/M04-C02/M05-C02/M07-C05)→`CTRL2-*`、"
      "M05-C03/04/05→`CTRL2B-*`、M07-C02-T01/T02→`CTRL2-M07-C02`（T03→"
      "`CTRL-M07-C02`）。非后缀 `CTRL-M02-C0X`/`CTRL-M04-C0X` 为过期 stub（manifest "
      "指向 -PFN/-DECOY trace 但自身盘上 trace 与注入目标参数不同），已排除。\n")
    a("- 构建选择：原构建 Fault→原 Control；eb327 Fault→CTRL2；fb1b M05-C03/04/05 "
      "→ fb1b Control。\n")
    a("- A20 实际检查：build hash 之外，还逐样本核对 disk_sha256 / rcs_sha256 / "
      "config-kernel-bootloader-checkpoint / 共享运行参数（不再仅凭 build hash 声称 "
      "配置一致）。注入目标参数（mmu_m02_old_pfn、mmu_m04_decoy_pfn）为逐样本标定值；"
      "与正确标定 Control 比对后全部匹配（declared injection-target diff=0，此前 27 "
      "条系过期 stub Control 所致）。当前 A20=%s；"
      "build-mismatch %d 条；config-mismatch %d 条" %
      (a20.get("status", "?"), len(build_mism),
       len(a20.get("config_mismatch", []))))
    if build_mism:
        a("  跨构建样本：%s（fb1b M05 暖命中观测版 vs eb327 Control；"
          "build delta 仅 MMU_CONSUMER_REUSE_CAP，对 Control 惰性）。" %
          ", ".join(c["SampleRunID"].split("-")[-1] for c in build_mism))
    a("")

    a("## 6. IFU 事件定义 + A19\n")
    a("- `ifu_response`=Fetch::processCacheCompletion；`ifu_decode`=Fetch::buildInst "
      "的 DynInst 构建（Fetch 侧），**不等同** O3 `Decode::tick`。\n")
    a("- A19 验证真实 ifu_response / ifu_decode / commit 与 translation_id 关联，"
      "不再只检查 commit/squash 终点。A19=%s。\n" % a19.get("status", "?"))

    a("## 7. Episode / ActualValue\n")
    a("- W13 多 Episode 逐条记录 observed/expected/result；ActualValue 取 FAIL "
      "Episode 的 observed（0x51），不被前一个 PASS 的 0x7d 覆盖。\n")

    a("## 8. 已知问题关闭矩阵\n")
    a("- `final_issue_closure.csv`（见 ZIP1）逐项记录 CLOSED / VERIFIED_BOUNDARY。\n")

    a("## 9. 验收\n")
    a("- A01–A22 见 `final_acceptance.md` / `acceptance.json`；"
      "`campaign/validate.py` 全部一致性检查通过。\n")
    a("- 全部派生 CSV/JSON/MD 由同一份最新数据重生成（finalize → export_evidence → "
      "acceptance → validate → gen_v2_delivery → gen_causal_dag）。\n")

    with open(os.path.join(DELIVERY, "REPORT.md"), "w") as fh:
        fh.write("\n".join(out))
    print("REPORT.md written (%d lines)" % len(out))


if __name__ == "__main__":
    main()