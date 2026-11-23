#!/usr/bin/env python3
"""M01 diagnostic evidence final reconciliation + v2 report generation."""
import os, gzip, re, json, csv, hashlib, shutil, subprocess, tarfile

ROOT = "/home/sdc/gem5-fi-mmu-impl-v2"
OUT = os.path.join(ROOT, "MMU_FINAL", "M01_Diagnostic_Granularity_Evidence_Final")
os.makedirs(OUT, exist_ok=True)
E = json.load(open(os.path.join(ROOT, "MMU_FINAL", "_work", "m01_evidence2.json")))

BUILD = "741cdc567f4894448ed9aea08bcf9f9db2d65f42e089becac587890bfe9047b3"
FNV = {"af64274c86026bfd": "0xAA", "af64084c86023750": "0x55",
       "217454b2f3049aa5": "16x0xAA", "d7e54fa625bb2055": "16x0x55"}

# annotation vocabulary
DIRECT = "DIRECT_TRACE"
SRC    = "SOURCE_CONFIRMED"
DERIV  = "DERIVED_FROM_DATA"
ORACLE = "ORACLE_CONFIRMED"
NOBS   = "NOT_OBSERVED"

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""): h.update(c)
    return h.hexdigest()

def load_line(run, kind, keyvals):
    """first trace line matching kind + keyvals, return (line_no, dict)."""
    p = os.path.join(ROOT, "runs", "W5X3", run, "Trace", "prop_evt.txt.gz")
    with gzip.open(p, "rt", errors="replace") as f:
        for ln, line in enumerate(f, 1):
            if "kind=%s " % kind not in line: continue
            d = dict(re.findall(r"([a-zA-Z_0-9]+)=([^ ]*)", line))
            if all(d.get(k) == v for k, v in keyvals):
                return ln, d
    return None, {}

# ------------------------------------------------------------------
# evidence annotation helpers per context
# ------------------------------------------------------------------
CTX = {
 "C01": dict(name="DIRECT_LOAD", title="C01 — 直接 Load 消费路径 (R01)",
   src="v = *p; sink = v;",
   loads=[("400eb0","ldrb w2, [x28]","w2/x2","v = *p（x28=&p）")],
   chain=[("TLBI Suppression (mmu_fault_arm→tlbi_suppressed)", DIRECT),
          ("stale L2 TLB Hit（旧 PA 保留）", DERIV),
          ("旧 PA", DIRECT),
          ("`ldrb w2,[x28]` @0x400eb0（目标 Load）", SRC),
          ("Memory Response = 旧 marker（data_fnv 指纹=0xAA/0x55）", DIRECT),
          ("RF Writeback（物理寄存器 int:NNN）", DIRECT),
          ("消费者 `and x0,x2,#0xff` @0x400eb8 读 w2", DIRECT),
          ("`str x0,[x26]` sink=v @0x400ec0", SRC),
          ("Oracle: observed=Fault≠Control", ORACLE)]),
 "C02": dict(name="SIMD_LANE", title="C02 — NEON/SIMD Lane 消费路径 (R05)",
   src="vec=vld1q_u8(p); vec=vaddq_u8(vec,1); vec0=vgetq_lane_u8(vec,0); sink=vec0; v=*p;",
   loads=[("4011d0","ldr q0, [x28]","v0(q0)","vec=vld1q_u8(p)（16 字节向量）"),
          ("4011e4","ldrb w2, [x28]","w2","v=*p（标量 oracle）")],
   chain=[("TLBI Suppression", DIRECT),
          ("stale L2 TLB Hit", DERIV),
          ("`ldr q0,[x28]` @0x4011d0（NEON 向量 Load）", SRC),
          ("Memory Response 16×marker（data_fnv 指纹，Fault=16×0xAA）", DIRECT),
          ("RF Writeback vec:NNN（128 位向量寄存器）", DIRECT),
          ("`add v0.16b,v0.16b,v1.16b` @0x4011d4（消费者，+1）", DIRECT),
          ("`umov w0,v0.b[0]` @0x4011d8（提取 lane 0 到 w0）", SRC),
          ("Oracle: vec0=Fault≠Control（0xAB vs 0x56）", ORACLE)]),
 "C03": dict(name="MASKING", title="C03 — 错误值被软件隔离 (C03 weak consumer)",
   src="volatile uint8_t dead = *p; (void)dead; v = 0;",
   loads=[("401138","ldrb w0, [x28]","w0","dead = *p")],
   chain=[("TLBI Suppression", DIRECT),
          ("stale L2 TLB Hit", DERIV),
          ("`ldrb w0,[x28]` @0x401138（dead Load, data_fnv 指纹）", DIRECT),
          ("`and w0,w0,#0xff` @0x40113c", SRC),
          ("`strb w0,[sp,#247]` @0x401140（存临时栈槽）", SRC),
          ("`ldrb w0,[sp,#247]` @0x401144（重新读回栈槽值）", SRC),
          ("重新读回的值被丢弃，变量 v 重定义为 0", SRC),
          ("Oracle: observed=0x00，Fault==Control（均 PASS）", ORACLE)]),
 "C04": dict(name="POINTER_DEPENDENCY", title="C04 — 错误数据改变后续访存地址 (R04)",
   src="v=*p; q=p+(v&0x0F); w=*q; sink=w;",
   loads=[("401108","ldrb w2, [x28]","w2","第一条 v=*p"),
          ("401118","ldrb w0, [x28, x0]","w0","第二条 w=*(p+(v&0x0F))")],
   chain=[("TLBI Suppression", DIRECT),
          ("stale L2 TLB Hit", DERIV),
          ("第一条 `ldrb w2,[x28]` @0x401108", SRC),
          ("第一条 Memory Response 旧 marker（data_fnv）", DIRECT),
          ("`and x0,x2,#0xf` @0x401110（v&0x0F=0x0A/0x05）", SRC),
          ("第二条 `ldrb w0,[x28,x0]` @0x401118，VA=0x400000000A/05", DIRECT),
          ("第二条 Memory Response（旧页 0xAA vs 新页 0x55）", DIRECT),
          ("Oracle: observed 不同（第二条 load 值）", ORACLE)]),
 "C05": dict(name="CONTROL_FLOW", title="C05 — 错误值影响控制流 (R03)",
   src="v=*p; if(v==expect){branch=1}else{branch=2};",
   loads=[("4010cc","ldrb w0, [x28]","w0","v = *p")],
   chain=[("TLBI Suppression", DIRECT),
          ("stale L2 TLB Hit", DERIV),
          ("`ldrb w0,[x28]` @0x4010cc（目标 Load）", SRC),
          ("Memory Response 旧 marker（data_fnv）", DIRECT),
          ("`cmp w21,w0,uxtb` @0x4010d4（v vs expect）", SRC),
          ("`b.eq` @0x4010d8（条件分支）", SRC),
          ("Oracle: branch=Fault≠Control（2 vs 1）", ORACLE),
          ("NZCV/redirect 未直接记录", NOBS)]),
}

def write_context_report(ctx):
    m = CTX[ctx]
    L = [f"# {m['title']} — 指令级传播证据（v2）","",
         f"> 工作负载 `w9.c`：`{m['src']}`","",
         "**证据标注**：`DIRECT_TRACE`=原始 Trace 直接记录；`SOURCE_CONFIRMED`=源码/反汇编确认；",
         "`DERIVED_FROM_DATA`=数据指纹/初始化内容+指令语义推导；`ORACLE_CONFIRMED`=Guest Oracle；",
         "`NOT_OBSERVED`=无直接证据。`data_fnv` 是 memory_response **响应数据的 FNV-1a-64 指纹**",
         "（非原始字节）；物理寄存器（`int:NNN`/`vec:NNN`）与架构寄存器（w2/v0）分开记录。",""]
    # fault-control oracle table
    L += ["","## Fault-Control 对照（Guest Oracle，全部 3 迭代）","",
          "| Timing | iter | Fault observed/vec0/branch/result | Control observed/vec0/branch/result | 一致？ |",
          "|---|---|---|---|---|"]
    cid = f"CTRL-M01-{ctx}"
    for t in ("T01","T02","T03"):
        fs = E["samples"][f"M01-F0-W9-W5X3-{ctx}-{t}"]["oracle"]
        cs = E["controls"][cid]["oracle"]
        for i in range(3):
            f, c = fs[i], cs[i]
            same = "相同" if (f["observed"],f["vec0"],f["branch"],f["result"])==(c["observed"],c["vec0"],c["branch"],c["result"]) else "不同"
            fname = "FAIL" if f["result"]=="FAIL" else f["result"]
            L.append(f"| {t} | {i} | {f['observed']}/{f['vec0']}/{f['branch']}/{fname} | "
                     f"{c['observed']}/{c['vec0']}/{c['branch']}/{c['result']} | {same} |")
    L += ["", "## 传播链（10 步，含证据标注）","", "```text"]
    for step, anno in m["chain"]:
        L.append(f"{step}   [{anno}]")
    L += ["```",""]
    # per-timing T01/T02 detailed
    for t in ("T01","T02"):
        sid = f"M01-F0-W9-W5X3-{ctx}-{t}"
        v = E["samples"][sid]
        L += [f"## {t} 目标 Load → 消费者（{sid}）",""]
        seen=set(); uniq=[]
        for l in v["loads"]:
            if l["data"] and l["dseq"] not in seen:
                seen.add(l["dseq"]); uniq.append(l)
        for l in uniq:
            L.append(f"- **Load** PC={l['pc']} `{l['disasm']}` 架构寄存器={l['arch_reg']} 物理寄存器={l['phys_reg']} "
                     f"dseq={l['dseq']} data_fnv 指纹→`{l['data']}` va={l['va']} pa={l['pa']} [{DIRECT}/{DERIV}]")
        for c in v["consumers"]:
            L.append(f"  - **消费者** PC={c['pc']} dseq={c['dseq']} (consumer_of={c['producer']}, 物理寄存器依赖, commit={c['cscomm']}) [{DIRECT}]")
        L.append(f"- fault_arm eid={v['arm']}，tlbi_suppressed eid={v['supp']}，disarm eid={v['disarm']}")
        L.append("")
    # T03 unconsumed
    L += ["## T03 — 故障建立但无后续消费（ACTIVATED_UNCONSUMED）","",
          "T03 的 fault_arm 与 tlbi_suppressed 均在 Trace 中出现（故障已建立），但 ITER 命中",
          "唯一一次注入位于最后一个维护 epoch，其后无 Load 消费保留的 stale Entry——无 committed",
          "fault-tagged Load / consumer。Oracle 3 迭代均 PASS。",""]
    return "\n".join(L)

def write_gap():
    base = {
      "(": "(",
    }
    rows = []
    for ctx, m in CTX.items():
        for t in ("T01","T02","T03"):
            kind = "SDC" if t in ("T01","T02") and ctx!="C03" else ("MASKED" if ctx=="C03" else "UNCONSUMED")
            items = [
              ("目标 Load 返回数据（data_fnv 指纹）", DIRECT, "prop_evt memory_response.data_fnv" if t in("T01","T02") else "N/A（无消费）", "高"),
              ("Load 物理/架构寄存器", DIRECT if t in("T01","T02") else "N/A", "rf_writeback.field + 反汇编", "高"),
              ("消费者指令 PC+反汇编", DIRECT, "consumer 事件 + mmu_w9.dyn 反汇编", "高"),
              ("消费者中间操作数实际值", NOBS, "需新增埋点（DynInst operand value）", "中"),
            ]
            if ctx=="C02":
                items.append(("SIMD 每 lane 数值", NOBS, "仅 lane0 被 umov，其余 15 lane 未记录", "中"))
            if ctx=="C05":
                items.append(("NZCV 条件标志/branch redirect", NOBS, "prop_evt 无 branch/redirect 事件", "高"))
            if ctx=="C04":
                items.append(("第二条 Load VA/PA（偏移 0x0A/0x05）", DIRECT, "memory_response.va/pa", "高"))
            for item,avail,src,imp in items:
                rows.append({"Context":ctx,"Timing":t,"Evidence_Item":item,
                             "Current_Availability":avail,"Evidence_Source":src,
                             "Diagnostic_Importance":imp,
                             "Note":"跨 Timing 共用的缺口（非逐样单独缺失）" if avail==NOBS else ""})
    return rows

def extract_control_traces():
    d = os.path.join(OUT, "control_traces")
    os.makedirs(d, exist_ok=True)
    tgz = os.path.join(ROOT, "MMU_When_Golden_Evidence.tar.gz")
    with tarfile.open(tgz, "r:gz") as tf:
        for c in ("CTRL-M01-C01","CTRL-M01-C02","CTRL-M01-C03","CTRL-M01-C04","CTRL-M01-C05"):
            for suffix in ("/Trace/prop_evt.txt.gz","/Run_Log/board.terminal","/manifest.json"):
                name = f"runs/W5X3/{c}{suffix}"
                try:
                    m = tf.getmember(name)
                    m.name = f"{c}{suffix.replace('/','_')}"
                    tf.extract(m, d)
                except KeyError:
                    pass
    return d

def main():
    for ctx in CTX:
        p = os.path.join(OUT, f"M01_{ctx}_{CTX[ctx]['name']}_DIAGNOSTIC_EVIDENCE.md")
        open(p, "w").write(write_context_report(ctx))
    # gap matrix
    gaps = write_gap()
    p = os.path.join(OUT, "M01_DIAGNOSTIC_EVIDENCE_GAP_MATRIX.csv")
    with open(p, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(gaps[0].keys())); w.writeheader(); w.writerows(gaps)
    # control traces
    extract_control_traces()
    # copy fault extracts + source
    d = os.path.join(OUT, "raw_trace_extracts"); os.makedirs(d, exist_ok=True)
    for s, v in E["samples"].items():
        src = os.path.join(ROOT, "runs", "W5X3", s, "Trace", "prop_evt.txt.gz")
        shutil.copy2(src, os.path.join(d, f"{s}_prop_evt.txt.gz"))
    d = os.path.join(OUT, "workload_source_and_disassembly"); os.makedirs(d, exist_ok=True)
    shutil.copy2(os.path.join(ROOT,"workloads","mmu_w5x3","w9.c"), os.path.join(d,"mmu_w9.c"))
    subprocess.run(["objdump","-d",os.path.join(ROOT,"workloads","mmu_w5x3","mmu_w9.dyn")],
                   stdout=open(os.path.join(d,"mmu_w9.dyn.disasm.txt"),"w"), stderr=subprocess.DEVNULL)
    print("context reports + gap + control traces + fault extracts + source written")

if __name__ == "__main__":
    main()