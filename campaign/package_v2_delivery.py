#!/usr/bin/env python3
"""Package the MMU E2E V2 final delivery into 3 ZIPs + manifest.

ZIP64 + deflate.  Reads the already-generated derived artifacts + raw RETRY2
runs + modified gem5 source + analysis scripts.  No experiment changes.
"""
import csv
import hashlib
import os
import zipfile

ROOT = "/home/sdc/gem5-fi-mmu-impl-v2"
DELIVERY = os.path.join(ROOT, "exports", "MMU_E2E_V3_FINAL_DELIVERY")
ANALYSIS = os.path.join(ROOT, "analysis")
RETRY2 = os.path.join(ROOT, "runs", "W5X3_RETRY2")
GEM5 = os.path.join(ROOT, "CHAOS", "gem5")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def add_file(zf, src, arc):
    zf.write(src, arc, compress_type=zipfile.ZIP_DEFLATED)


def add_dir_tree(zf, base, prefix):
    n = 0
    for root, _, files in os.walk(base):
        for fn in sorted(files):
            p = os.path.join(root, fn)
            rel = os.path.relpath(p, base)
            arc = os.path.join(prefix, rel)
            zf.write(p, arc, compress_type=zipfile.ZIP_DEFLATED)
            n += 1
    return n


def build_zip(name, entries_fn):
    path = os.path.join(DELIVERY, name)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED,
                         allowZip64=True) as zf:
        entries_fn(zf)
    return path


def zip1(zf):
    for fn in ["REPORT.md", "final_acceptance.md", "acceptance.json",
               "experiment_status.csv", "per_condition.json",
               "partial23_repair_comparison.csv", "per_model_completeness.csv",
               "terminal_symptoms.csv", "completeness.csv",
               "propagation_chains.csv", "summary_by_model.csv",
               "fault_control_compare.csv", "timing_map.csv",
               "conditions.json", "control_map.json",
               "final_issue_closure.csv",
               "M07_C02_FINAL_CLOSURE.md", "M06_C05_PILOT_EVIDENCE.md"]:
        p = os.path.join(DELIVERY, fn)
        if os.path.isfile(p):
            add_file(zf, p, fn)
        elif os.path.isfile(os.path.join(ANALYSIS, fn)):
            add_file(zf, os.path.join(ANALYSIS, fn), fn)
        elif os.path.isfile(os.path.join(ROOT, fn)):
            add_file(zf, os.path.join(ROOT, fn), fn)


def zip2(zf):
    for fn in ["causal_nodes.csv", "causal_edges.csv", "causal_branches.csv",
               "per_condition.json", "propagation_chains.csv",
               "chain_edges.csv", "chain_branches.csv",
               "authoritative_trace_index.csv", "completeness.csv",
               "retry2_map.json", "retry2_evidence_index.json",
               "control_map.json"]:
        p = os.path.join(DELIVERY, fn)
        if os.path.isfile(p):
            add_file(zf, p, fn)
        else:
            add_file(zf, os.path.join(ANALYSIS, fn), fn)
    add_dir_tree(zf, os.path.join(DELIVERY, "PARTIAL23_REPAIR_EVIDENCE"),
                 "PARTIAL23_REPAIR_EVIDENCE")
    add_dir_tree(zf, os.path.join(DELIVERY, "per_sample_e2e_paths"),
                 "per_sample_e2e_paths")


def zip3(zf):
    # raw RETRY2 runs (full traces + logs + manifests)
    add_dir_tree(zf, RETRY2, "runs/W5X3_RETRY2")
    # modified gem5 source (5 files) under gem5_source/
    for rel in ["src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc",
                "src/cpu/o3/CHAOSPropagation/CHAOSPropagation.hh",
                "src/cpu/o3/fetch.cc", "src/cpu/o3/fetch.hh",
                "src/arch/arm/tlb.cc"]:
        add_file(zf, os.path.join(GEM5, rel),
                 "gem5_source/" + rel.replace("/", "_"))
    # source diff + instrumentation spec + call-site index
    for fn in ["0202c_source_diff.md", "0202c_instrumentation_spec.md",
               "0202c_source_call_sites.md"]:
        p = os.path.join(ROOT, "work", fn)
        if os.path.isfile(p):
            add_file(zf, p, "docs/" + fn)
    # analysis / tools scripts
    for fn in ["campaign/propagation.py", "campaign/finalize.py",
               "campaign/acceptance.py", "campaign/validate.py",
               "campaign/export_evidence.py", "campaign/gen_v2_delivery.py",
               "campaign/gen_causal_dag.py", "campaign/gen_repair_evidence.py",
               "campaign/control_map.py", "campaign/oracle.py",
               "campaign/gen_report.py", "campaign/gen_issue_closure.py",
               "campaign/run_fb1b_controls.py",
               "campaign/when5x3_retry2.py", "campaign/make_retry2_index.py",
               "tools/prop_trace_dump.py"]:
        p = os.path.join(ROOT, fn)
        if os.path.isfile(p):
            add_file(zf, p, fn)
    # reproduction
    repro = os.path.join(DELIVERY, "REPRODUCTION.md")
    if not os.path.isfile(repro) and os.path.isfile(
            os.path.join(ROOT, "work", "REPRODUCTION_V3.md")):
        import shutil as _sh
        _sh.copy2(os.path.join(ROOT, "work", "REPRODUCTION_V3.md"), repro)
    if os.path.isfile(repro):
        add_file(zf, repro, "REPRODUCTION.md")
    # golden eligible-event streams (control pre-scan eligible census)
    add_dir_tree(zf, os.path.join(ANALYSIS, "eligible_events"),
                 "analysis/eligible_events")
    # workloads: source + binaries + rcS (W11-W14)
    add_dir_tree(zf, os.path.join(ROOT, "workloads", "mmu_w5x3"),
                 "workloads/mmu_w5x3")
    add_dir_tree(zf, os.path.join(ROOT, "campaign", "rcs"), "campaign/rcs")
    # M06-C05 pilot (speculative wrong-path feasibility boundary) evidence
    add_dir_tree(zf, os.path.join(ROOT, "runs", "pilot", "M06-C05"),
                 "runs/pilot/M06-C05")
    # disassembly material
    add_dir_tree(zf, os.path.join(ROOT, "work", "disasm"), "disasm")
    add_file(zf, os.path.join(ROOT, "work", "REPRODUCTION_V3.md"),
             "docs/REPRODUCTION_V3.md")


def main():
    zips = {
        "MMU_E2E_V3_FINAL_REPORT.zip": zip1,
        "MMU_E2E_V3_CAUSAL_EVIDENCE.zip": zip2,
        "MMU_E2E_V3_RAW_AND_SOURCE.zip": zip3,
    }
    results = []
    for name, fn in zips.items():
        path = build_zip(name, fn)
        size = os.path.getsize(path)
        results.append((name, path, size, sha256(path)))
        print("%s  %d bytes" % (name, size))

    # --- manifest ---
    status = {r["NewSampleRunID"]: r for r in
              csv.DictReader(open(os.path.join(ROOT, "experiment_status.csv")))}
    from collections import Counter
    comp = Counter(r.get("Completeness") for r in status.values())

    rows = []
    rows.append("# MMU_E2E_V3 交付清单 (delivery manifest)\n")
    rows.append("## 1. ZIP 文件\n")
    for name, path, size, h in results:
        rows.append("- **%s**\n  - 路径：`%s`\n  - 大小：%d bytes (%.1f MiB)\n  - SHA256：`%s`\n" %
                   (name, path, size, size / 1048576.0, h))

    rows.append("## 2. 最终统计\n")
    rows.append("- FULL: %d\n" % comp.get("FULL", 0))
    partial = sum(v for k, v in comp.items() if k.startswith("PARTIAL"))
    rows.append("- PARTIAL: %d\n" % partial)
    rows.append("- N/A: %d\n" % comp.get("FILE_MISSING", 0))
    rows.append("- 原 23 条 PARTIAL：21 条补全为 FULL（12 取指 + 9 M05 数据消费者）；M07-C02-T01/T02 正确重分类为 "
                "REQUEST_PENDING_AT_ROI_END（PARTIAL，请求在 ROI 结束前未完成）。\n")

    rows.append("## 3. 本轮新增运行\n")
    r2 = [d for d in os.listdir(RETRY2) if os.path.isdir(
        os.path.join(RETRY2, d))]
    faults = [d for d in r2 if "RETRY2-" in d]
    controls = [d for d in r2 if d.startswith("CTRL2")]
    rows.append("- 新增 Fault 运行：%d\n" % len(faults))
    rows.append("- 新增 Control 运行：%d\n" % len(controls))

    rows.append("## 4. gem5 观测埋点主要新增\n")
    rows.append("- IFU propagation：`ifu_response` / `ifu_decode` + fault-tagged "
                "commit（真实 Request 对象身份桥 translation_id → dyn_inst_seq）\n")
    rows.append("- M05 提交消费者：poisoned-DTB 暖命中消费事务（MMU_CONSUMER_REUSE_CAP=16）\n")
    rows.append("- 掩盖机制：`mmu_fault_summary.masked_reason`\n")
    rows.append("- **源码调用位置清单**：`docs/0202c_source_call_sites.md`（ZIP3），给出"
                " `cache_request`(Cache::access)、`lsu_request`/`translation_result`"
                "(translateMmuOn)、LSQ 翻译完成/派发/squash(SingleDataRequest::finish/"
                "LSQUnit::read/LSQUnit::squash)、Commit 异常投递/提交(commitHead)、"
                "ARM Data Abort(faults.cc) 的实际调用位置与逐文件 SHA256。\n")

    rows.append("## 5. 本轮元数据修正（不重跑实验）\n")
    rows.append("- `control_map.json`：120 条 `ControlID` 已从权威 `conditions.json` "
                "按 SampleRunID 恢复（此前被误写为 CTRL-M08-C05）；保留真实解析的 "
                "ControlRunID / ControlBuildHash / ControlTraceSHA256。\n")
    rows.append("- **ControlRunID 实际路径修正**：以 `ControlTraceSHA256` 逐样本匹配真实"
                " control run 目录（`sha256sum` 校验），重写 `ControlRunID` 为实际运行"
                "目录名（`ControlID` 逻辑名不变）：M02→`CTRL-M02-C0X-PFN`(15)、"
                "M04-C01/03/04/05→`CTRL-M04-C0X-DECOY`(12)、M03-C02/M04-C02/M05-C02→"
                "`CTRL2-*`(9)、M05-C03/04/05→`CTRL2B-*`(9)、M07-C02-T01/T02→"
                "`CTRL2-M07-C02` 与 T03→`CTRL-M07-C02`(3)、M07-C05→`CTRL2-M07-C05`(3)、"
                "M06-C05→空(3)，共 53 条修正；`control_map.json`/`authoritative_trace_index.csv`/"
                "`fault_control_compare.csv` 三处同步。非后缀 `CTRL-M02-C0X`/"
                "`CTRL-M04-C0X` 目录是过期 stub（manifest 指向 -PFN/-DECOY 的 trace 但"
                "自身盘上 trace 不同、注入目标参数不匹配），已从权威映射排除（`control_map.py`"
                " 跳过 manifest trace 指向其它 run 目录的 stub）。A20 因此改为与正确"
                "标定 Control 比对，`mmu_m02_old_pfn`/`mmu_m04_decoy_pfn` 全部匹配"
                "（declared injection-target diff 由 27 归 0），0 build mismatch / "
                "0 config mismatch / 0 missing control。\n")
    rows.append("- A20 强化：build hash 之外逐样本核对 disk_sha256 / rcs_sha256 / "
                "config-kernel-bootloader-checkpoint / 共享运行参数；故障注入目标参数"
                "（mmu_m02_old_pfn、mmu_m04_decoy_pfn）为逐样本标定值，与正确标定 "
                "Control 比对后全部匹配（0 declared injection-target diff）。\n")
    rows.append("- M06-C05 Pilot 证据：`M06_C05_PILOT_EVIDENCE.md` + "
                "`runs/pilot/M06-C05/`（pilot_result.json / rcS / command / "
                "board.terminal / trace / SHA256），未重跑 Pilot。\n")
    rows.append("- 构建版本：`741cdc…`（原构建）、`eb327197…`（IFU+masked_reason，"
                "12 取指 + 2 M07-C02 + CTRL2 controls）、`fb1b6f01…`（+MMU_CONSUMER_"
                "REUSE_CAP=16，9 M05 数据 + CTRL2B controls）；逐样本 BuildHash 见 "
                "`control_map.json`。复现入口见 `REPRODUCTION.md`（ZIP3）与 "
                "`campaign/rcs/*.rcS`。\n")

    rows.append("## 6. 仍缺失的传播事件及技术原因\n")
    rows.append("- M07-C02-T01/T02：请求在 ROI 结束时仍未完成（无 memory "
                "response / consumer / commit / 异常投递），保留 PARTIAL。详见 "
                "`M07_C02_FINAL_CLOSURE.md`：故障指令在 `lsu_request` 处终止、无 "
                "`cache_request`（请求未发往 Cache）；根因是负载在页表游走期间已被 "
                "squash（`squash_status=squashed`，Control 与非目标 load `seq=30014904`"
                " 同结构复现），其 NoFault 翻译被 `squashTranslation` 丢弃；Control 同 "
                "load 为 Data Abort（证故障改变了微架构路径但未形成 SDC）。\n")
    rows.append("- 埋点完整性按唯一请求计数：9 条 load 完整走通、2 条 load 发出 "
                "`lsu_request` 但无 `cache_request`（故障指令 + 非目标 `seq=30014904`），"
                "并非 10 条完整。\n")
    rows.append("- PID/Episode 关联：ep1/2/3 = pid 318/320/322 = asid 236/242/248 = "
                "observed ldrb `seq=24118302`/`27030544`/`29694101`；T01 故障落 ep1、"
                "T02 落 ep2（one-shot + Timing 决定）。\n")
    rows.append("- M06-C05（3 条）：冻结配置可行性边界（speculative "
                "wrong-path），N/A（见 `M06_C05_PILOT_EVIDENCE.md`）。\n")

    rows.append("## 7. 已知问题 / 未通过验收\n")
    rows.append("- 见 final_issue_closure.csv（逐项 CLOSED / VERIFIED_BOUNDARY）；"
                "validate.py ALL CHECKS PASSED。\n")

    rows.append("## 8. 无法从交付材料独立验证的结论\n")
    rows.append("- M07-C02 故障 Episode 的 SIGSEGV 精确动态指令：可证**非**故障指令"
                "（它得 `fault_status=NoFault`，无异常投递）；ep2/ep3 的 SIGSEGV 来自"
                "未故障架构拒绝路径（`translation_result(Data)`+`squash`，直接可证）；"
                "ep1（T01）/ep2（T02）的 SIGSEGV 来自故障指令之外、one-shot 消耗后的"
                "架构拒绝（re-execution），其 Data Abort 未以独立 `translation_result`/"
                "`exception_delivery` 事件在当前构建 Trace 中直接观测到（数据侧本就"
                "不发射 `exception_delivery`，Control 亦为 0 条），故保留 PARTIAL（见 "
                "`M07_C02_FINAL_CLOSURE.md`）。\n")

    with open(os.path.join(DELIVERY, "MMU_E2E_V3_DELIVERY_MANIFEST.md"),
              "w") as f:
        f.write("\n".join(rows))
    print("manifest written")


if __name__ == "__main__":
    main()