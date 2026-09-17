#!/usr/bin/env python3
"""Emit plans/sdc-process-reclassification.md from reclass3_metrics.json."""
import json, os
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
rows = json.load(open(os.path.join(REPO, "artifacts/meta/reclass3_metrics.json")))

# ---- Category 2 protection audit (three-state labels) ----
# Protected units (protectionModel implemented in code): CHAOSCache(l1d/l1i/l2), CHAOSMem(memory),
# CHAOSArmTLB(l1_tlb), CHAOSPTW(ptw).
PROTECTED = {"l1d", "l1i", "l2", "memory", "l1_tlb", "ptw", "l3"}  # l3 via CHAOSCache pairedSector
# N/A (industry-consensus unprotected in commercial non-safety CPUs): comb logic / control FSMs
NA_UNITS = {"exec", "fsu", "decode", "bpu", "exmon", "ras"}
# NOT-IMPLEMENTED (industry standard says HW protects; we scope-cut): NoC/CHI/HCCS
NOTIMPL_UNITS = {"noc"}
# UNKNOWN (V110 protection status unverifiable; N1 proxy assumption "not listed = none")
UNKNOWN_UNITS = {"physreg", "rat", "freelist", "rob", "iq", "lsq_fwd", "l1d_fwd", "sysreg"}
# l3 tag/coh directory also unknown — handled inline

# verification round (this session, /tmp/verify replays):
VERIFIED = {
    "physreg": "✓(2/2 guest-real page-fault)",
    "rat": "✓(2/2 guest-real page-fault)",
    "freelist": "✓(1/1 guest-real page-fault)",
    "decode": "✓(1/1 guest-real page-fault)",
    "exmon": "✓(1/1 gem5-assertion-mediated)",
    "iq": "✗ artifact found: 778 'Crash' rows = exit1/2+faults0 config errors (madd_chain binary-name), reclassified SimulatorError in this table; true IQ wake_omit DUE (58-63%) separately confirmed in v1.2",
    "exec": "未抽查(exit=-6 全体,同 fwdsrc 签名)",
    "lsq_fwd": "未抽查(exit=-6 全体)",
    "ptw": "H7 formal 49% 致死(exit=134=gem5 panic-abort 报 guest 内核态故障;含 8 kernel panic + 6 abort,单发核实过)",
}

def c2_label(unit, prot, c2, nv):
    if unit in PROTECTED:
        if prot in ("none", "?") and unit != "ptw":
            return "0(本cell=none臂)"
        return c2 if nv else "—"
    if unit in NA_UNITS: return "N/A(共识不保护)"
    if unit in NOTIMPL_UNITS: return "未实现(行业有)"
    if unit in UNKNOWN_UNITS: return "未知/待证实"
    if unit == "l3": return "未知/待证实(tag/目录)"
    return "?"

# group rows by unit then campaign
by_unit = defaultdict(list)
for r in rows: by_unit[r["unit"]].append(r)

UNIT_CN = {"physreg":"PRF 物理寄存器堆","rat":"RAT 重命名表","freelist":"FreeList",
    "rob":"ROB","iq":"发射队列","exec":"整数执行","fsu":"FPU/向量执行",
    "lsq_fwd":"LSQ 转发","l1d":"L1D 数据","l1d_fwd":"L1D post-check 通路",
    "l1i":"L1I 指令","l2":"L2","l3":"L3/互连代理","memory":"DRAM 后备",
    "decode":"译码","bpu":"分支预测","ras":"RAS(异常抑制)","exmon":"独占监视器",
    "l1_tlb":"数据 TLB","sysreg":"系统寄存器","ptw":"页表遍历"}

L = []
L.append("# SDC 过程三分类重统计(2026-09-11)")
L.append("")
L.append("> **框架**:SDC 的本质是过程——错误架构结果 + RAS 链路零告警 + 穿透保护路径——不取决于最终表现形式。")
L.append("> 对每个 (单元, 故障模型, workload) cell:")
L.append("> - **C1 无影响** = Masked/N_valid")
L.append("> - **C2 过程中被检出** = (Corrected+DetectedContained)/N_valid —— 仅真建模了保护的单元非零")
L.append("> - **C3 未检出但有问题** = (SDC+Crash+Hang)/N_valid,子项 **3a** 静默错 = SDC、**3b** 崩溃暴露 = Crash、**3c** 挂起暴露 = Hang")
L.append("> - N_valid = N_total − Inactive − SimulatorError(工具伪影在分母外);**有效率** = N_valid/(N_total−Inactive),**伪影率** = 1−有效率")
L.append("> - 数据源:每个数字可溯源到 runs/<campaign>/c*/results.jsonl;H7 formal 来自 artifacts/p20_h7_formal/results.txt(shell 跑批,标注)。")
L.append("> - **重分类修正**:原 iq_f5f6_pilot/iq_f5_formal_madd/iq_f6_phase_curve 的 778 条 \"Crash\"(exit∈{1,2}+faults=0)实为 gem5 配置错误(madd_chain 二进制名错),本表按 SimulatorError 处理(详见 findings)。")
L.append("")
L.append("## 类别2 保护机制审计(三态)")
L.append("")
L.append("| 状态 | 单元 | 依据 |")
L.append("|---|---|---|")
L.append("| **有保护建模**(C2 按实际 rep 统计) | L1D/L1I/L2(CHAOSCache protectionModel)、DRAM(CHAOSMem)、DTLB(CHAOSArmTLB)、PTW(ptwEcc) | 代码 grep 全仓库核实,仅这 4 注入器实现 protectionModel |")
L.append("| **N/A**(真机大概率也不保护) | Exec、FPU、Decode、AGU、BPU、ExMon、RAS | 组合逻辑/控制状态机,商用非安全关键芯片普遍不加 ECC(行业共识) |")
L.append("| **未实现**(行业标准有,我们没做) | NoC/CHI/HCCS | 链路级 CRC+重传是行业标准;主动 scope-cut |")
L.append("| **未知/待证实** | PRF、RAT、FreeList、ROB、IQ、LSQFwd、L1DForward、SysReg、L3 tag/一致性目录 | 鲲鹏 V110 是否保护无法确定;N1 代理假设\"未列=无保护\"仅因 ARM 公开手册没提,**不代表真没有**,未经实机验证 |")
L.append("")
L.append("## 逐单元三分类表")
L.append("")
for unit in sorted(by_unit, key=lambda u: -len(by_unit[u])):
    rs = by_unit[unit]
    L.append(f"### {UNIT_CN.get(unit, unit)}(`{unit}`)— {len(rs)} cells,{sum(r['n_total'] for r in rs)} reps")
    L.append("")
    L.append("| campaign / cell | 故障模型/模式 | workload | 平台 | 保护 | N | Nv | C1 无影响% | C2 检出% | C3 未检出% | 3a SDC% | 3b Crash% | 3c Hang% | 有效率% | 二次核实 |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in sorted(rs, key=lambda r: (r["campaign"], r["cell"])):
        wl = (r["workload"] or "?").replace("-golden-v1","")
        mode = r["model"] + (("/" + r["axes"]) if r["axes"] else "")
        prot = r["prot"] if r["prot"] != "none" else "none"
        ver = VERIFIED.get(unit, "—") if r["C3b"] != "0.0" and r["needs_verify"] else ("—" if not r["needs_verify"] else VERIFIED.get(unit, "未抽查"))
        L.append(f"| {r['campaign']}/{r['cell']} | {mode} | {wl} | {r['plat']} | {prot} | {r['n_total']} | {r['N_valid']} | {r['C1']} | {c2_label(unit, r['prot'], r['C2'], r['N_valid'])} | {r['C3']} | {r['C3a']} | {r['C3b']} | {r['C3c']} | {r['validity']} | {ver} |")
    L.append("")
L.append("## 工具伪影二次核实记录(2026-09-11,/tmp/verify 重放,stderr 全保留)")
L.append("")
L.append("| 单元 | 重放 reps | 退出信号 | 裁定 |")
L.append("|---|---|---|---|")
L.append("| physreg(fwdsrc cell) | 2 | rc=134,gem5 panic 报 `Page table fault @ 0x0/0x7fbffefc10` | **guest 真实故障**(stuck_at_zero→坏指针→页表错),SIGABRT 是 gem5-SE 报告无 handler 的 guest fault 的方式——Crash 分类**正确** |")
L.append("| rat(spec_leak) | 2 | 同上,`Page table fault @ 0x21130` | **guest 真实故障**,Crash 正确 |")
L.append("| freelist(mark_free) | 1 | `Page table fault @ 0x47ffff6afa0` | **guest 真实故障**,Crash 正确 |")
L.append("| decode | 1 | `Page table fault @ 0x8001ff2c20` | **guest 真实故障**,Crash 正确 |")
L.append("| exmon(stxr_force_fail) | 1 | rc=134,gem5 `Assertion extraDataValid() failed`(request.hh:912) | **gem5 断言中介**:注入破坏 STXR 协议→gem5 内部断言暴露;真机对应锁协议破坏(livelock/abort)。按 DUE 计,标注\"gem5-assertion-mediated\" |")
L.append("| iq(F5/F6 旧 3 campaign) | 1 + 全量扫描 | 原 778 条 Crash = exit1/2+faults=0 | **工具伪影**(madd_chain 二进制名错→gem5 配置错误;2026-09-04 版分类器误标 Crash)。本表已改计 SimulatorError;真 IQ 结局以 v1.2 修复后数据为准 |")
L.append("")
L.append("## 诚实边界")
L.append("")
L.append("1. **iq_f5f6_pilot/iq_f5_formal_madd/iq_f6_phase_curve 作废**:778 reps 的 \"Crash\" 全是 exit∈{1,2}+faults=0 的 gem5 配置错误(二进制名 madd_chain 应为 madd_chain_kernel)。本表重计为 SimulatorError(伪影率因此上升)。**IQ 单元的可信数字 = v1.2 修复后的 pwf_v12_iq_*(wake_omit 63.5% DUE formal)**。")
L.append("2. **SIGABRT 疑点已核实但非全量**:核实了 6 单元 8 reps(physreg/rat/freelist/decode/exmon + iq-artifact)。exec/lsq_fwd 的 exit=-6 全体与 fwdsrc 同签名(Page table fault 家族),未逐一重放——标注\"未抽查\"。")
L.append("3. **fs_mode cells**(tlbf5/sysreg/ptw boot)的 Masked = 内核存活 oracle,3a 静默面未知(FS 无法区分安静算错)。")
L.append("4. **H7 formal 为 360s 截断观察窗**(censored):survivor = 窗口内无 panic,非全程存活。")
L.append("5. **类别2 的\"未知/待证实\"**(9 单元)是 N1 代理假设,未经实机验证——引用时必须带上这个限定。")
L.append("6. **runner.py 待办**:results.jsonl 未保存 stderr 原文与退出原因文本,本次回溯靠重放。建议加 `exit_reason` 字段(取 stderr 首个 panic/assert 行,~50 字符)——已列 task_plan 待办,未顺手改。")
os.makedirs(os.path.join(REPO, "plans"), exist_ok=True)
open(os.path.join(REPO, "plans/sdc-process-reclassification.md"), "w").write("\n".join(L) + "\n")
print("wrote plans/sdc-process-reclassification.md,", len(L), "lines")
