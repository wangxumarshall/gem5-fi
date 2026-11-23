#!/usr/bin/env python3
"""Generate M01 diagnostic-granularity evidence deliverables.

Reads MMU_FINAL/_work/m01_evidence.json + hardcoded disasm/source maps, writes:
  5 context reports, instruction-level propagation CSV, gap matrix CSV,
  evidence index, raw trace extracts, and a manifest.
"""
import json, os, gzip, re, hashlib, shutil, subprocess, csv

ROOT = "/home/sdc/gem5-fi-mmu-impl-v2"
O = os.path.join(ROOT, "MMU_FINAL", "_work")
OUT = os.path.join(ROOT, "MMU_FINAL", "M01_Diagnostic_Granularity_Evidence")
os.makedirs(OUT, exist_ok=True)

E = json.load(open(os.path.join(O, "m01_evidence.json")))

# ---------------------------------------------------------------
# context metadata (from w9.c source + mmu_w9.dyn disassembly)
# ---------------------------------------------------------------
CTX = {
 "C01": dict(
   title="C01 — 直接 Load 消费路径 (R01)",
   src="run_context R01: v = *p; sink = v;",
   load_pc="0x400eb0", load_insn="ldrb w2, [x28]", load_desc="v = *p（x28=&p）",
   consumers=[
     ("0x400eb8", "and x0, x2, #0xff", "零扩展 v 到 64 位（消费者读 w2）"),
     ("0x400ec0", "str x0, [x26]", "sink = v（x26=&sink）")],
   oracle_field="observed（=scalar v）", vec=False, branch=False),
 "C02": dict(
   title="C02 — NEON/SIMD Lane 消费路径 (R05)",
   src="run_context R05: vec=vld1q_u8(p); vec=vaddq_u8(vec,1); vec0=vgetq_lane_u8(vec,0); sink=vec0; v=*p;",
   load_pc="0x4011d0 / 0x4011e4", load_insn="ldr q0, [x28] / ldrb w2, [x28]",
   load_desc="vec=vld1q_u8(p)（16 字节向量 load）/ v=*p（标量 oracle）",
   consumers=[
     ("0x4011cc", "movi v1.16b, #0x1", "vdupq_n_u8(1)"),
     ("0x4011d4", "add v0.16b, v0.16b, v1.16b", "vaddq_u8(vec,1)（消费者）"),
     ("0x4011d8", "umov w0, v0.b[0]", "vgetq_lane_u8(vec,0) 提取 lane 0"),
     ("0x4011dc", "str x0, [x26]", "sink = *vec0"),
     ("0x4011e8", "and w2, w2, #0xff", "标量 v（oracle）")],
   oracle_field="vec0 + observed", vec=True, branch=False),
 "C03": dict(
   title="C03 — 错误值被软件隔离 (C03 weak consumer)",
   src="run_context C03: volatile uint8_t dead = *p; (void)dead; v = 0;",
   load_pc="0x401138", load_insn="ldrb w0, [x28]", load_desc="dead = *p（结果被丢弃）",
   consumers=[
     ("0x40113c", "and w0, w0, #0xff", "dead 值零扩展"),
     ("0x401140", "strb w0, [sp, #247]", "dead 存入栈槽（volatile，随即被丢弃）")],
   oracle_field="observed（C03 不校验 observed）", vec=False, branch=False),
 "C04": dict(
   title="C04 — 错误数据改变后续访存地址 (R04)",
   src="run_context R04: v=*p; q=p+(v&0x0F); w=*q; sink=w;",
   load_pc="0x401108 / 0x401118", load_insn="ldrb w2,[x28] / ldrb w0,[x28,x0]",
   load_desc="第一条 v=*p / 第二条 w=*(p+(v&0x0F))",
   consumers=[
     ("0x401110", "and x0, x2, #0xf", "v & 0x0F → 第二条 load 的偏移"),
     ("0x40111c", "and x0, x0, #0xff", "第二条 load 结果零扩展")],
   oracle_field="observed（=第二条 load 值）", vec=False, branch=False),
 "C05": dict(
   title="C05 — 错误值影响控制流 (R03)",
   src="run_context R03: v=*p; if(v==expect){branch=1;sink=0x100}else{branch=2;sink=0x200};",
   load_pc="0x4010cc", load_insn="ldrb w0, [x28]", load_desc="v = *p（stale load）",
   consumers=[
     ("0x4010d0", "and w2, w0, #0xff", "v & 0xff"),
     ("0x4010d4", "cmp w21, w0, uxtb", "比较 v 与 expect（w21=expect）"),
     ("0x4010d8", "b.eq 0x4012a4", "v==expect → branch=1 路径"),
     ("0x4010dc", "mov x0, #0x200", "v!=expect → sink=0x200"),
     ("0x4010e0", "mov w8, #0x2", "*branch = 2")],
   oracle_field="branch + observed", vec=False, branch=True),
}

CONSUMER_DISASM = {
    "400eb8": "and x0, x2, #0xff",
    "400ebc": "and w2, w2, #0xff",
    "4010d0": "and w2, w0, #0xff",
    "4010d4": "cmp w21, w0, uxtb",
    "401110": "and x0, x2, #0xf",
    "40111c": "and x0, x0, #0xff",
    "40113c": "and w0, w0, #0xff",
    "4011d4": "add v0.16b, v0.16b, v1.16b",
    "4011d8": "umov w0, v0.b[0]",
    "4011e8": "and w2, w2, #0xff",
}

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()

def sample_ctx(sid):
    return "C" + sid.split("-C")[1][:2]

def fmt_load(l):
    return (f"PC={l['pc']} `{l['disasm']}` dseq={l['dseq']} "
            f"data={l['data'][0]} va={l['va']} pa={l['pa']} reg={l['reg']}")

# ================================================================
# 1. five context reports
# ================================================================
def gen_context_report(ctx):
    m = CTX[ctx]
    lines = [f"# {m['title']} — 指令级传播证据", "",
             f"> 来源 workload `w9.c`：`{m['src']}`", "",
             "本报告以原始 `prop_evt` Trace + `mmu_w9.dyn` 反汇编 + Guest Oracle 重建",
             "故障动态指令 → 软件可见结果的传播链。`data_fnv` 为 memory_response 返回数据的",
             "FNV-1a-64 哈希（`0xAA`=af64274c86026bfd，`0x55`=af64084c86023750，16×0xAA=",
             "217454b2f3049aa5，16×0x55=d7e54fa625bb2055），用于恢复 Load 返回的实际字节。", ""]
    lines.append("## Fault-Control 对照（Guest Oracle）")
    lines.append("")
    lines.append("| Timing | 注入 iter | Fault observed / vec0 / branch / result | Control observed / vec0 / branch / result |")
    lines.append("|---|---|---|---|")
    for t in ("T01", "T02", "T03"):
        sid = f"M01-F0-W9-W5X3-{ctx}-{t}"
        cid = f"CTRL-M01-{ctx}"
        fs = E["samples"][sid]["oracle"]
        cs = E["controls"][cid]["oracle"]
        for i in range(3):
            f = fs[i]; c = cs[i]
            if f["result"] == "FAIL":
                lines.append(f"| {t} | iter={i} | obs={f['observed']} vec0={f['vec0']} branch={f['branch']} **{f['result']}** | obs={c['observed']} vec0={c['vec0']} branch={c['branch']} {c['result']} |")
    lines.append("")
    # target load + consumers for T01/T02
    for t in ("T01", "T02"):
        sid = f"M01-F0-W9-W5X3-{ctx}-{t}"
        v = E["samples"][sid]
        lines.append(f"## {t} 目标动态 Load → 消费者（{sid}）")
        lines.append("")
        # find the stale load (the one with data matching the fault marker)
        loads = [l for l in v["loads"] if l["data"][0] in ("0xAA", "0x55", "16x0xAA", "16x0x55")]
        # dedupe by dseq
        seen = set(); uniq = []
        for l in loads:
            if l["dseq"] in seen: continue
            seen.add(l["dseq"]); uniq.append(l)
        for l in uniq:
            lines.append(f"- **Load** {fmt_load(l)}")
        for c in v["consumers"]:
            dis = CONSUMER_DISASM.get(c["pc"], "?")
            lines.append(f"  - **消费者** PC={c['pc']} `{dis}` dseq={c['dseq']} (consumer_of={c['producer']}, commit={c['cs']})")
        lines.append(f"- **fault_arm** eid={v['arm_eid']}，tlbi_suppressed eid={v['suppress_eids']}，disarm eid={v['disarm_eids']}")
        lines.append("")
    # propagation diagram
    lines.append("## 传播链（实际指令 + 寄存器 + 值）")
    lines.append("")
    lines.append("```text")
    lines.append("TLBI Suppression (fault_arm -> tlbi_suppressed)")
    lines.append("      |")
    lines.append("      v")
    lines.append("Stale L2 TLB Hit (旧 PA 保留)")
    lines.append("      |")
    lines.append("      v")
    lines.append(f"{m['load_insn']}   <-- 目标 Load（{m['load_pc']}）")
    lines.append("      |  Memory Response = 旧 marker (data_fnv)")
    lines.append("      v")
    lines.append("RF Writeback (物理寄存器)")
    for pc, insn, d in m["consumers"]:
        lines.append(f"      |")
        lines.append(f"      v")
        lines.append(f"{insn}   <-- {pc}  {d}")
    lines.append("      |")
    lines.append("      v")
    lines.append(f"Guest Oracle: {m['oracle_field']}（Fault ≠ Control）")
    lines.append("```")
    lines.append("")
    # unresolved
    lines.append("## 当前无法证明的细节（证据缺口）")
    lines.append("")
    lines.append("- 消费者中间计算结果的**实际寄存器数值**（如 `and`/`cmp`/`add` 的输入输出值）不在 prop_evt Trace 中；"
                 "本报告由 `data_fnv`（memory response 返回字节）+ 反汇编指令语义恢复，属于静态可推导、动态值部分恢复。")
    if m["vec"]:
        lines.append("- SIMD **每 lane 数值**未逐 lane 记录：`umov w0, v0.b[0]` 仅提取 lane 0，其余 15 lane 不在 Trace；"
                     "但 16 字节全为同一 marker（16×0xAA/0x55），vaddq+1 后全 0xAB/0x56，可推导。")
    if m["branch"]:
        lines.append("- **NZCV 条件标志与 branch redirect** 未在 prop_evt 中记录（仅有 Guest Oracle 的 branch=1/2 结果）；"
                     "`cmp w21,w0,uxtb` 的比较结果由 Load 值（0xAA vs 0x55）与 expect 推导。")
    lines.append("")
    return "\n".join(lines)

# ================================================================
# 2. instruction-level propagation CSV (15 samples)
# ================================================================
def gen_prop_csv():
    rows = []
    for ctx in ("C01", "C02", "C03", "C04", "C05"):
        for t in ("T01", "T02", "T03"):
            sid = f"M01-F0-W9-W5X3-{ctx}-{t}"
            v = E["samples"][sid]
            fail = [o for o in v["oracle"] if o["result"] == "FAIL"]
            term = "SDC" if fail else ("ACTIVATED_MASKED" if ctx == "C03" and v["loads"] else "ACTIVATED_UNCONSUMED")
            loads = [l for l in v["loads"] if l["data"][0]]
            load_str = "; ".join(f"{l['pc']}:{l['data'][0]}(dseq={l['dseq']},reg={l['reg']})" for l in loads)
            cons_str = "; ".join(f"{c['pc']}(dseq={c['dseq']},of={c['producer']})" for c in v["consumers"])
            rows.append({
                "SampleRunID": sid, "Context": ctx, "Timing": t,
                "TerminalState": term,
                "fault_arm_eid": v["arm_eid"] or "",
                "Loads(data@PC)": load_str,
                "Consumers(PC)": cons_str,
                "FaultOracle": "; ".join(f"iter{o['iter']}:{o['observed']}/{o['branch']}/{o['vec0']}/{o['result']}" for o in v["oracle"]),
                "ControlOracle": "; ".join(f"iter{o['iter']}:{o['observed']}/{o['branch']}/{o['vec0']}/{o['result']}" for o in E["controls"][f"CTRL-M01-{ctx}"]["oracle"]),
            })
    return rows

# ================================================================
# 3. gap matrix CSV
# ================================================================
def gen_gap_csv():
    rows = []
    G = [
      ("C01","T01","22825682","0x400eb0","目标 Load 返回数据","A","prop_evt memory_response.data_fnv","","已恢复 0xAA","高"),
      ("C01","T01","22825682","0x400eb0","Load 物理目的寄存器","A","prop_evt rf_writeback.field","","int:135","高"),
      ("C01","T01","22825684","0x400eb8","消费者指令 PC+反汇编","A+B","consumer 事件 + mmu_w9.dyn 反汇编","","and x0,x2,#0xff","高"),
      ("C01","T01","-","-","消费者中间寄存器实际数值","C","需新增观测埋点（DynInst operand value）","and 的输入/输出实际值未记录","需纯观测埋点","中"),
      ("C02","T01","22826295","0x4011d0","NEON 16 字节向量数据","A","memory_response.data_fnv=16×0xAA","","217454b2f3049aa5","高"),
      ("C02","T01","-","-","SIMD 各 lane 数值","C","需新增埋点（SIMD lane value）","仅 lane 0 被 umov 提取","需纯观测埋点","中"),
      ("C02","T01","22826295","0x4011d4","向量加法（消费者）","A+B","consumer 事件 + 反汇编","","add v0.16b,+,v1.16b","高"),
      ("C03","T01","22825712","0x401138","dead Load 返回数据","A","memory_response.data_fnv","","0xAA（被丢弃）","高"),
      ("C03","T01","-","-","错误值被隔离的具体位置","B","反汇编：strb 到栈槽后无后续读取","dead 值存栈后不再读","静态+动态值可恢复","高"),
      ("C04","T01","22826118","0x401118","第二条 Load VA/PA","A","memory_response.va/pa","","va=0x400000000a pa=0x8348600a","高"),
      ("C04","T01","22826114","0x401110","偏移计算 (v&0x0F)","B","反汇编 and x0,x2,#0xf + data=0xAA","","0x0A","高"),
      ("C05","T01","22826003","0x4010cc","目标 Load 返回数据","A","memory_response.data_fnv","","0xAA","高"),
      ("C05","T01","-","0x4010d4","cmp 两操作数/NZCV","B+C","反汇编 cmp w21,w0,uxtb + data","NZCV 实际位未记录","需纯观测埋点","高"),
      ("C05","T01","-","0x4010d8","条件分支跳转目标/redirect","C","需新增埋点（branch redirect）","prop_evt 无 branch/redirect 事件","需纯观测埋点","高"),
      ("C05","T01","-","-","分支结果","A","Guest Oracle branch=2 vs 1","","已恢复","高"),
    ]
    for r in G:
        rows.append(dict(zip(["Context","Timing","DynInstSeq","PC","Evidence_Item",
                              "Current_Availability","Evidence_Source","Missing_Detail",
                              "Required_Action","Diagnostic_Importance"], r)))
    return rows

# ================================================================
# 4. evidence index
# ================================================================
def gen_index():
    lines = ["# M01 诊断证据来源索引", "",
             "每条结论对应的原始文件 / 行号 / EventID。", ""]
    lines.append("| 结论 | 证据来源 | 定位 |")
    lines.append("|---|---|---|")
    lines.append("| 目标 Load PC / DynInstSeq | `runs/W5X3/<run>/Trace/prop_evt.txt.gz` | kind=commit/translation_result 的 pc= 与 dyn_inst_seq= |")
    lines.append("| Load 返回数据 | 同上 | kind=memory_response 的 data_fnv=（0xAA=af64274c86026bfd, 0x55=af64084c86023750） |")
    lines.append("| Load 物理寄存器 | 同上 | kind=rf_writeback 的 field=int:NNN |")
    lines.append("| 消费者指令 | 同上 + `workloads/mmu_w5x3/mmu_w9.dyn` 反汇编 | kind=consumer 的 pc= / consumer_of=；objdump -d 对应 PC |")
    lines.append("| Guest Oracle | `runs/W5X3/<run>/Run_Log/board.terminal` | W9_RESULT 行 observed/vec0/branch/result |")
    lines.append("| 工作负载语义 | `workloads/mmu_w5x3/w9.c` | run_context() 各 ctx 分支 |")
    lines.append("| 故障模型语义 | `analysis/per_model_propagation.md` / `per_sample_e2e_paths/` | M01 TLBI suppression |")
    lines.append("| 终态分类 | `experiment_status.csv` | M01 行 TerminalState/Completeness |")
    lines.append("| Control 对照 | `runs/W5X3/CTRL-M01-<ctx>/` | board.terminal + prop_evt |")
    lines.append("")
    return "\n".join(lines)

# ================================================================
# 5. raw trace extracts
# ================================================================
def gen_extracts():
    d = os.path.join(OUT, "raw_trace_extracts")
    os.makedirs(d, exist_ok=True)
    # extract fault chain window for each sample (fault_id=1 events, key kinds)
    key = ("mmu_fault_arm","tlbi_suppressed","tlbi_match","mmu_fault_disarm",
           "fault_entry_reuse","fault_entry_consume","permission_eval","translation_result",
           "lsu_request","memory_response","rf_writeback","consumer","commit","squash")
    for ctx in ("C01","C02","C03","C04","C05"):
        for t in ("T01","T02","T03"):
            sid = f"M01-F0-W9-W5X3-{ctx}-{t}"
            src = os.path.join(ROOT,"runs","W5X3",sid,"Trace","prop_evt.txt.gz")
            dst = os.path.join(d, f"{sid}_fault_chain.txt")
            with gzip.open(src,"rt",errors="replace") as f, open(dst,"w") as out:
                out.write(f"# {sid} fault-tagged chain (fault_id=1, key kinds)\n")
                for line in f:
                    if "fault_id=1" not in line: continue
                    dd = dict(re.findall(r"([a-z_]+)=([^ ]*)", line))
                    if dd.get("kind") in key:
                        out.write(f"eid={dd.get('event_id')} kind={dd.get('kind')} "
                                  f"dseq={dd.get('dyn_inst_seq','')} pc={dd.get('pc','')} "
                                  f"field={dd.get('field','')} fn={dd.get('data_fnv','')} "
                                  f"va={dd.get('va','')} pa={dd.get('pa','')} "
                                  f"tick={dd.get('tick','')} cs={dd.get('commit_status','')}\n")
    return d

# ================================================================
# write everything
# ================================================================
def main():
    # context reports
    for ctx in CTX:
        p = os.path.join(OUT, f"M01_{ctx}_DIAGNOSTIC_EVIDENCE.md")
        name = {"C01":"DIRECT_LOAD","C02":"SIMD_LANE","C03":"MASKING",
                "C04":"POINTER_DEPENDENCY","C05":"CONTROL_FLOW"}[ctx]
        p = os.path.join(OUT, f"M01_{ctx}_{name}_DIAGNOSTIC_EVIDENCE.md")
        open(p,"w").write(gen_context_report(ctx))
        print("wrote", os.path.basename(p))
    # propagation CSV
    rows = gen_prop_csv()
    p = os.path.join(OUT, "M01_INSTRUCTION_LEVEL_PROPAGATION.csv")
    with open(p,"w",newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print("wrote", os.path.basename(p))
    # gap matrix
    rows = gen_gap_csv()
    p = os.path.join(OUT, "M01_DIAGNOSTIC_EVIDENCE_GAP_MATRIX.csv")
    with open(p,"w",newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print("wrote", os.path.basename(p))
    # index
    p = os.path.join(OUT, "M01_DIAGNOSTIC_EVIDENCE_INDEX.md")
    open(p,"w").write(gen_index())
    print("wrote", os.path.basename(p))
    # extracts
    d = gen_extracts()
    print("extracts ->", os.path.relpath(d, ROOT))
    # copy workload source + disasm
    d = os.path.join(OUT, "workload_source_and_disassembly")
    os.makedirs(d, exist_ok=True)
    shutil.copy2(os.path.join(ROOT,"workloads","mmu_w5x3","w9.c"), os.path.join(d,"mmu_w9.c"))
    subprocess.run(["objdump","-d",os.path.join(ROOT,"workloads","mmu_w5x3","mmu_w9.dyn")],
                   stdout=open(os.path.join(d,"mmu_w9.dyn.disasm.txt"),"w"),
                   stderr=subprocess.DEVNULL)
    print("copied workload source + disasm")

if __name__ == "__main__":
    main()