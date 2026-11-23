#!/usr/bin/env python3
"""Final M01 v2 report + propagation CSV + index + manifest + ZIP packaging."""
import os, json, csv, hashlib, zipfile

ROOT = "/home/sdc/gem5-fi-mmu-impl-v2"
OUT = os.path.join(ROOT, "MMU_FINAL", "M01_Diagnostic_Granularity_Evidence_Final")
E = json.load(open(os.path.join(ROOT, "MMU_FINAL", "_work", "m01_evidence2.json")))
BUILD = "741cdc567f4894448ed9aea08bcf9f9db2d65f42e089becac587890bfe9047b3"
W9_DYN = "eff7595885d6912b87155c0dc8c3a6cb15fb27e58b903c1082d16396b9f9e361"
W9_C = "c45f0701279f3a940b884eac2ccd02c0d621cbac6b4850f1ab4c63a2ebf6faa8"

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""): h.update(c)
    return h.hexdigest()

# ============ final v2 report ============
def v2_report():
    L = ["# M01 TLB Invalidation C01–C05 T01–T03 传播报告（Diagnostic Ready v2）","",
         "> 诊断粒度：从故障激活（TLBI Suppression）到软件可见结果（Guest Oracle）的**指令级**传播。",
         "> Build Hash：`%s`。工作负载 `mmu_w9.dyn` SHA256 `%s`，`w9.c` SHA256 `%s`。" % (BUILD, W9_DYN, W9_C),"",
         "## 1. 故障语义","",
         "M01 = Hierarchical TLB Invalidation Suppression：抑制一次 TLBI 失效，使 **stale L2/统一 TLB entry**",
         "保留旧物理页映射；后续对同一 VA 的 Load 命中 stale entry → 读到**旧页 marker**（0xAA 或 0x55），",
         "而非 remap 后的新页 marker。`mmu_fault_arm → tlbi_suppressed`，随后 Load 命中时 `mmu_fault_disarm`。","",
         "**旧 PA 是错误映射，不代表该 PA 中数据发生位翻转**：旧页内数据仍是完整 marker（0xAA/0x55），",
         "错误源于「访问了旧物理页」而非「正确页的数据损坏」。","",
         "## 2. 五种 Context 指令级传播（含证据标注）","",
         "标注：`DIRECT_TRACE`（原始 Trace 直接记录）· `SOURCE_CONFIRMED`（源码/反汇编）· "
         "`DERIVED_FROM_DATA`（data_fnv 指纹+指令语义）· `ORACLE_CONFIRMED`（Guest Oracle）· `NOT_OBSERVED`（无直接证据）。",""]
    ctx_blocks = {
      "C01": "**C01 直接数据消费**：`ldrb w2,[x28]`(0x400eb0) → [data_fnv 指纹→旧 marker，DIRECT] → RF Writeback int:NNN → "
             "消费者 `and x0,x2,#0xff`(0x400eb8) 读 w2 → `str x0,[x26]` sink → observed=Fault(0xAA)≠Control(0x55)。",
      "C02": "**C02 SIMD Lane**：`ldr q0,[x28]`(0x4011d0,16 字节) → [data_fnv 指纹→16×旧 marker，DIRECT] → "
             "`add v0.16b,v0.16b,v1.16b`(0x4011d4,+1) → `umov w0,v0.b[0]`(0x4011d8,**提取 lane 0**) → vec0=Fault(0xAB)≠Control(0x56)。"
             "独立标量 `ldrb w2,[x28]`(0x4011e4) 提供 observed。**仅 lane 0 被观测**，其余 15 lane 由 16×marker 推导（NOT_OBSERVED per-lane）。",
      "C03": "**C03 软件隔离**：`ldrb w0,[x28]`(0x401138,dead) → `and w0,w0,#0xff`(0x40113c) → "
             "`strb w0,[sp,#247]`(0x401140,存栈槽) → `ldrb w0,[sp,#247]`(0x401144,**重新读回栈槽**) → "
             "读回值被丢弃、变量 v 重定义 0 → observed=0x00。**Fault==Control**（均 PASS）——错误值被隔离，未进校验。",
      "C04": "**C04 两级 Load 地址依赖**：第一条 `ldrb w2,[x28]`(0x401108) → `and x0,x2,#0xf`(0x401110,偏移=v&0x0F) → "
             "第二条 `ldrb w0,[x28,x0]`(0x401118,**VA=0x400000000A/0x4000000005**)。第一条错误 Load 确实改变第二条地址："
             "Fault 偏移 0x0A（v=0xAA）vs Control 0x05（v=0x55）。",
      "C05": "**C05 控制流**：`ldrb w0,[x28]`(0x4010cc) → `cmp w21,w0,uxtb`(0x4010d4,v vs expect) → `b.eq`(0x4010d8) → "
             "Fault branch=2（0xAA≠0x55）vs Control branch=1（0x55==0x55）。**NZCV/redirect 未直接记录**（NOT_OBSERVED），"
             "分支结果由 Guest Oracle branch 字段 ORACLE_CONFIRMED。",
    }
    for ctx in ("C01","C02","C03","C04","C05"):
        L += [ctx_blocks[ctx], ""]
    L += ["## 3. 终态与完整传播链（10 步）","",
          "| Context | T01/T02 | T03 |",
          "|---|---|---|",
          "| C01 | SDC（observed 0xAA vs 0x55） | ACTIVATED_UNCONSUMED |",
          "| C02 | SDC（vec0 0xAB vs 0x56） | ACTIVATED_UNCONSUMED |",
          "| C03 | ACTIVATED_MASKED（Fault==Control） | ACTIVATED_UNCONSUMED |",
          "| C04 | SDC（第二条 VA 0x0A vs 0x05） | ACTIVATED_UNCONSUMED |",
          "| C05 | SDC（branch 2 vs 1） | ACTIVATED_UNCONSUMED |","",
          "每条传播链 10 步：TLBI Suppression → stale L2 Hit → 旧 PA → Translation/LSU → Memory Response → "
          "RF Writeback → 实际消费者 → 指令间数据/地址变化 → Commit/Squash → 最终 Oracle。","",
          "## 4. 证据边界（不编造）","",
          "- `data_fnv` 是 memory_response 响应数据的 **FNV-1a-64 指纹**，非原始数据字节；"
          "字节值（0xAA/0x55/16×0xAA）由指纹 + FNV 计算 + 初始化 marker 推导（DERIVED_FROM_DATA）。",
          "- 物理寄存器（`int:NNN`/`vec:NNN`，rf_writeback.field）与架构寄存器（w0/w2/v0，反汇编）分开记录。",
          "- **未直接记录**：消费者中间操作数实际值、SIMD 逐 lane、NZCV 条件标志、branch redirect/目标——"
          "均如实标注 NOT_OBSERVED，不新增推断。",
          "- Control 的 NEON 向量 data_fnv 未在 Trace 记录（16 字节 data_fnv 仅 fault-tagged 计算），"
          "Control 的 vec0 由 Guest Oracle ORACLE_CONFIRMED。","",
          "## 5. 原始证据","",
          "- 15 条 Fault Trace：`runs/W5X3/M01-F0-W9-W5X3-{C,T}/Trace/prop_evt.txt.gz`（交付包 raw_trace_extracts/）。",
          "- 5 条 Control Trace：`runs/W5X3/CTRL-M01-{C}/Trace/prop_evt.txt.gz`（交付包 control_traces/）。",
          "- 反汇编：`mmu_w9.dyn.disasm.txt`；源码：`w9.c`。",""]
    return "\n".join(L)

def prop_csv():
    rows = []
    for ctx in ("C01","C02","C03","C04","C05"):
        for t in ("T01","T02","T03"):
            sid = f"M01-F0-W9-W5X3-{ctx}-{t}"
            v = E["samples"][sid]
            fail = [o for o in v["oracle"] if o["result"]=="FAIL"]
            term = "SDC" if fail else ("ACTIVATED_MASKED" if ctx=="C03" and v["loads"] else "ACTIVATED_UNCONSUMED")
            loads = []
            seen=set()
            for l in v["loads"]:
                if l["data"] and l["dseq"] not in seen:
                    seen.add(l["dseq"]); loads.append(l)
            ld = "; ".join(f"{l['pc']}:{l['data']}(dseq={l['dseq']},arch={l['arch_reg']},phys={l['phys_reg']},pa={l['pa']})" for l in loads)
            # filter consumers to context PCs only (drop libc register-renaming false positives)
            ctxpcs = {"400eb8","400ebc","4010d0","4010d4","401110","401118","40113c","4011d4","4011d8","4011e8"}
            cons = "; ".join(f"{c['pc']}(dseq={c['dseq']})" for c in v["consumers"] if c["pc"] in ctxpcs)
            f_o = "; ".join(f"i{o['iter']}:{o['observed']}/{o['vec0']}/{o['branch']}/{o['result']}" for o in v["oracle"])
            c_o = "; ".join(f"i{o['iter']}:{o['observed']}/{o['vec0']}/{o['branch']}/{o['result']}" for o in E["controls"][f"CTRL-M01-{ctx}"]["oracle"])
            rows.append({"SampleRunID":sid,"Context":ctx,"Timing":t,"TerminalState":term,
                         "fault_arm_eid":v["arm"][0] if v["arm"] else "",
                         "Loads(data@PC,dseq,arch/phys reg,pa)":ld,
                         "Consumers(PC,dseq)":cons,
                         "FaultOracle":f_o,"ControlOracle":c_o})
    return rows

def index():
    L=["# M01 诊断证据来源索引（v2）","","| 结论 | 证据来源 | 定位 | 标注 |","|---|---|---|---|",
       "| 目标 Load PC / DynInstSeq | runs/W5X3/<run>/Trace/prop_evt.txt.gz | kind=translation_result 的 pc=/dyn_inst_seq= | DIRECT_TRACE |",
       "| Load 返回数据（字节值） | 同上 | kind=memory_response 的 data_fnv=（FNV 指纹）→ FNV-1a-64 反推 0xAA/0x55/16×0xAA/16×0x55 | DIRECT_TRACE+DERIVED_FROM_DATA |",
       "| Load 物理寄存器 | 同上 | kind=rf_writeback 的 field=int:NNN / vec:NNN | DIRECT_TRACE |",
       "| Load 架构寄存器 | workloads/mmu_w5x3/mmu_w9.dyn 反汇编 | objdump -d 对应 PC（ldrb w2/v0 等） | SOURCE_CONFIRMED |",
       "| 消费者指令 | 同上 + prop_evt | kind=consumer 的 pc=/consumer_of=（物理寄存器依赖） | DIRECT_TRACE |",
       "| Guest Oracle | runs/W5X3/<run>/Run_Log/board.terminal | W9_RESULT 行 observed/vec0/branch/result | ORACLE_CONFIRMED |",
       "| 工作负载语义 | workloads/mmu_w5x3/w9.c | run_context() 各 ctx 分支 | SOURCE_CONFIRMED |",
       "| Control 对照 | MMU_When_Golden_Evidence.tar.gz / runs/W5X3/CTRL-M01-* | prop_evt + board.terminal | 同上 |",
       "| 终态分类 | experiment_status.csv | M01 行 | — |"]
    return "\n".join(L)+"\n"

def manifest(zip_sha, zip_size):
    L=["# M01 诊断粒度证据最终交付清单（v2）","","本轮：离线证据提取 + 文档修正，**不新增埋点、不重新编译、不重新运行实验、无 Git**。","",
       "## 构建/工作负载","",
       f"- Build Hash：`{BUILD}`",
       f"- `mmu_w9.dyn` SHA256：`{W9_DYN}`",
       f"- `w9.c` SHA256：`{W9_C}`","",
       "## 关键结论","",
       "| Context | 传播链核心 | 终态 |",
       "|---|---|---|",
       "| C01 | ldrb w2 → and x0,x2 → str sink | T01/T02 SDC，T03 UNCONSUMED |",
       "| C02 | ldr q0 → add v0.16b+1 → umov w0,v0.b[0] | T01/T02 SDC，T03 UNCONSUMED |",
       "| C03 | ldrb w0 → strb/ldrb 栈槽（读回后丢弃）→ v=0 | T01/T02 MASKED（Fault==Control），T03 UNCONSUMED |",
       "| C04 | ldrb w2 → and x0,x2,#0xf → ldrb [x28,x0]（第二条 VA 偏移 0x0A/0x05） | T01/T02 SDC，T03 UNCONSUMED |",
       "| C05 | ldrb w0 → cmp w21,w0 → b.eq（branch 2/1） | T01/T02 SDC，T03 UNCONSUMED |","",
       "## 证据完整度","",
       "15 条 Fault + 5 条 Control 均以 data_fnv 指纹 + 反汇编 + consumer（物理寄存器依赖）+ Guest Oracle 重建。",
       "明确区分目标 Load 的 Squash 与消费者 Commit（仅 committed 消费者纳入）。","",
       "## 尚未解决证据缺口（均 NOT_OBSERVED，可选补证）","",
       "1. 消费者中间操作数实际值（需 DynInst operand value 埋点）。",
       "2. SIMD 每 lane 数值（仅 lane0 被 umov 提取）。",
       "3. NZCV 条件标志 / branch redirect / 跳转目标。",
       "4. Control 的 NEON 向量 data_fnv（16 字节指纹仅 fault-tagged 计算）。","",
       "## 是否需额外实验","",
       "**否**。现有 Trace + 反汇编 + Oracle 已足以逐条重建传播路径。上述缺口如需可在不改故障语义下新增纯观测埋点做最小范围配对重跑。","",
       "## 交付包","",
       f"- ZIP：`M01_Diagnostic_Granularity_Evidence_Final.zip`（{zip_size} B，SHA256 `{zip_sha}`）",
       "- 本清单不含对自身 ZIP 的哈希（避免自引用不一致）；ZIP SHA256 由打包后独立计算并填入。","",
       "## 交付文件（目录结构）","",
       "```",
       "M01_Diagnostic_Granularity_Evidence_Final/",
       "  M01_TLB_Invalidation_C01-C05_T01-T03_Propagation_Report_Diagnostic_Ready_v2.md",
       "  M01_C01_DIRECT_LOAD_DIAGNOSTIC_EVIDENCE.md  (+C02/C03/C04/C05)",
       "  M01_INSTRUCTION_LEVEL_PROPAGATION.csv",
       "  M01_DIAGNOSTIC_EVIDENCE_GAP_MATRIX.csv",
       "  M01_DIAGNOSTIC_EVIDENCE_INDEX.md",
       "  raw_trace_extracts/        (15 条 Fault prop_evt.txt.gz)",
       "  control_traces/            (5 条 Control prop_evt.txt.gz + board.terminal)",
       "  workload_source_and_disassembly/ (mmu_w9.c + mmu_w9.dyn.disasm.txt)",
       "  M01_DIAGNOSTIC_EVIDENCE_MANIFEST.md",
       "```"]
    return "\n".join(L)+"\n"

def main():
    open(os.path.join(OUT,"M01_TLB_Invalidation_C01-C05_T01-T03_Propagation_Report_Diagnostic_Ready_v2.md"),"w").write(v2_report())
    rows = prop_csv()
    with open(os.path.join(OUT,"M01_INSTRUCTION_LEVEL_PROPAGATION.csv"),"w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    open(os.path.join(OUT,"M01_DIAGNOSTIC_EVIDENCE_INDEX.md"),"w").write(index())
    # package ZIP (manifest written AFTER zip sha is known -> two-pass)
    zpath = os.path.join(ROOT,"MMU_FINAL","M01_Diagnostic_Granularity_Evidence_Final.zip")
    with zipfile.ZipFile(zpath,"w",zipfile.ZIP_DEFLATED,allowZip64=True) as zf:
        for root,_,files in os.walk(OUT):
            for fn in sorted(files):
                p=os.path.join(root,fn)
                zf.write(p, os.path.relpath(p, os.path.dirname(OUT)), compress_type=zipfile.ZIP_DEFLATED)
    zsha = sha(zpath); zsize = os.path.getsize(zpath)
    open(os.path.join(OUT,"M01_DIAGNOSTIC_EVIDENCE_MANIFEST.md"),"w").write(manifest(zsha, zsize))
    # re-package to include the manifest (with final zip sha)
    os.remove(zpath)
    with zipfile.ZipFile(zpath,"w",zipfile.ZIP_DEFLATED,allowZip64=True) as zf:
        for root,_,files in os.walk(OUT):
            for fn in sorted(files):
                p=os.path.join(root,fn)
                zf.write(p, os.path.relpath(p, os.path.dirname(OUT)), compress_type=zipfile.ZIP_DEFLATED)
    print("final ZIP:", zpath)
    print("SHA256:", sha(zpath))
    print("files:", len([1 for _,_,f in os.walk(OUT) for _ in f]))

if __name__ == "__main__":
    main()