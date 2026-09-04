#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
algebra.py — 第 10 次致命转储（127.0.0.1-2026-09-04-10:27:58）寄存器代数闭合与反事实验算
全部运算模 2^64，无手算。输入值来源：
  - 崩溃块寄存器（vmcore-dmesg.txt 行 2677 起，Oops 原文）
  - vmlinux 静态符号（nm 输出）
  - crash 会话真值（crash_session.log：sym / px __per_cpu_offset[149] / [179] / p runqueues:NNN）
运行：python3 algebra.py > algebra_out.txt
"""
M = (1 << 64) - 1

def h(x):
    return f"0x{x:016x}"

print("== A. KASLR 滑移五路咬合 ==")
# 崩溃块寄存器（dmesg 原文）
x9  = 0xffffd99f120bae58   # 崩溃块 x9（bl cpu_util_cfs 的返回地址槽 = find_busiest_group+0x150）
x21 = 0xffffd99f13edfcb0   # 崩溃块 x21（adrp+add 构造的 &nr_cpu_ids）
x24 = 0xffffd99f13ee5000   # 崩溃块 x24（adrp 页基 = &__per_cpu_offset - 0x5d0）
x1  = 0xffffd99f13ae96c0   # 崩溃块 x1（ldp x0,x1,[sp,#8] 装入的 &runqueues 模板）

# vmlinux 静态符号（nm）
ST_fbg       = 0xffff80008013ad08  # find_busiest_group
ST_nr_cpu    = 0xffff800081f5fcb0  # nr_cpu_ids
ST_pcpu_page = 0xffff800081f65000  # __per_cpu_offset - 0x5d0 的 adrp 页基（objdump: adrp x24, ffff800081f65000）
ST_runqueues = 0xffff800081b696c0  # runqueues（.data..percpu 模板）

# crash sym 运行期符号（crash_session.log）
RT_fbg       = 0xffffd99f120bad08
RT_nr_cpu    = 0xffffd99f13edfcb0
RT_pcpu      = 0xffffd99f13ee55d0
RT_runqueues = 0xffffd99f13ae96c0

slide_x9  = (x9  - (ST_fbg + 0x150)) & M
slide_x21 = (x21 - ST_nr_cpu) & M
slide_x24 = (x24 - ST_pcpu_page) & M
slide_x1  = (x1  - ST_runqueues) & M
slide_sym_fbg  = (RT_fbg       - ST_fbg) & M
slide_sym_nr   = (RT_nr_cpu    - ST_nr_cpu) & M
slide_sym_pcpu = (RT_pcpu      - (ST_pcpu_page + 0x5d0)) & M
slide_sym_rq   = (RT_runqueues - ST_runqueues) & M
for name, v in [("x9-(fbg+0x150)", slide_x9), ("x21-nr_cpu_ids", slide_x21),
                ("x24-adrp页基", slide_x24), ("x1-runqueues", slide_x1),
                ("sym fbg", slide_sym_fbg), ("sym nr_cpu_ids", slide_sym_nr),
                ("sym __per_cpu_offset", slide_sym_pcpu), ("sym runqueues", slide_sym_rq)]:
    print(f"  {name:24s} = {h(v)}")
assert len({slide_x9, slide_x21, slide_x24, slide_x1, slide_sym_fbg,
            slide_sym_nr, slide_sym_pcpu, slide_sym_rq}) == 1
print(f"  → 八路全部一致，KASLR 滑移 = {h(slide_x9)}  【实锤】")

print()
print("== B. 故障点代数闭合（零塌缩族）==")
x20 = 0x0000000000000000   # 崩溃块 x20（ldr x20,[x0,w25,sxtw#3] 实收值）
x25 = 0x95                  # 崩溃块 x25（mov x25,x0 ← _find_next_and_bit 返回的迭代 CPU 号）
x6  = 0x95                  # 崩溃块 x6
x0  = 0x95                  # 崩溃块 x0
FAR = 0xffffd99f13ae97e0   # 崩溃块 FAR（Unable to handle ... at virtual address）
x27 = (x1 + x20) & M
print(f"  x1  (模板 &runqueues) = {h(x1)}   == crash sym runqueues {h(RT_runqueues)} 逐位一致")
print(f"  x20 (实收)            = {h(x20)}   ← 零塌缩：应为 __per_cpu_offset[149] 真值")
print(f"  x27 = x1 + x20        = {h(x27)}   == 崩溃块 x27 = 0xffffd99f13ae96c0 逐位一致 ✓")
print(f"  FAR = x27 + 0x120     = {h((x27 + 0x120) & M)}   == 崩溃 FAR {h(FAR)} 逐位一致 ✓")
assert x27 == 0xffffd99f13ae96c0
assert (x27 + 0x120) & M == FAR
assert x25 == x6 == x0 == 149
print(f"  x25 = x6 = x0 = 0x95 = {149}（迭代 CPU 号三寄存器互证）")
print("  指令字 f9409377 解码: ldr x23,[x27,#288]; 288 = 36×8 = 0x120 → FAR-x27=0x120 吻合 ✓")

print()
print("== C. 内存真值对照（crash 会话）==")
true_149 = 0xffffa6616d8f8000   # crash> px __per_cpu_offset[149]
true_179 = 0xffffa6616dcf4000   # crash> px __per_cpu_offset[179]
arr0     = 0xffffa6616c52e000   # crash> rd -64 __per_cpu_offset 192 首槽
print(f"  __per_cpu_offset[149] 真值 = {h(true_149)}   x20 实收 = {h(x20)}   ← 真值非零、实收为零")
print(f"  __per_cpu_offset[179] 真值 = {h(true_179)}")
print(f"  数组基址（槽 0）          = {h(arr0)}")
# rd 输出 192 槽逐项等差校验（离线解析 crash_session.log）
import re
lines = open("crash_session.log").read().splitlines()
vals = []
grab = False
for l in lines:
    if l.startswith("crash> rd -64 __per_cpu_offset"):
        grab = True; continue
    if grab:
        if "crash>" in l: break
        m = re.match(r"^([0-9a-f]+):\s+([0-9a-f]+)\s+([0-9a-f]+)", l)
        if m:
            vals += [int(m.group(2), 16), int(m.group(3), 16)]
print(f"  rd 解析槽数 = {len(vals)}（预期 192）")
assert len(vals) == 192
diffs = {(vals[i+1] - vals[i]) for i in range(191)}
print(f"  相邻槽差集合 = {[h(d) for d in sorted(diffs)]}（预期唯一 0x22000）")
assert diffs == {0x22000}
assert all(vals[k] == vals[0] + k * 0x22000 for k in range(192))
print(f"  全数组 = 槽0 + k×0x22000 (k=0..191) 逐项成立 ✓")
print(f"  off[149] - off[0] = {h(vals[149]-vals[0])} = 149×0x22000 = {h(149*0x22000)} ✓")
print(f"  off[179] - off[0] = {h(vals[179]-vals[0])} = 179×0x22000 = {h(179*0x22000)} ✓")
assert vals[149] == true_149 and vals[179] == true_179
print("  → 内存完好（等差数列不可能在单槽被写 0 后仍保持），坏的是装入寄存器的值 【实锤】")

print()
print("== D. 反事实验证（若 ldr 交付真值则不崩）==")
x27_true_149 = (x1 + true_149) & M
x27_true_179 = (x1 + true_179) & M
print(f"  x27_true(149) = &runqueues + off[149] = {h(x27_true_149)}")
print(f"                == crash p runqueues:149 的 nohz_csd.info / cfs.rq 内嵌自指针 0xffff8000813e16c0 逐位一致 ✓")
print(f"               == 该实例 rd 直读 cfs.avg.load_avg = 0（CPU149 空载，健全数据）")
print(f"  x27_true(179) = &runqueues + off[179] = {h(x27_true_179)}")
print(f"               == crash p runqueues:179 的 nohz_csd.info / cfs.rq 内嵌自指针 0xffff8000817dd6c0 逐位一致 ✓")
print(f"               == vtop {h(x27_true_179)} → PTE e86057ffe02f03 (VALID|SHARED|AF|NG|PXN|UXN|DIRTY) 【VALID】")
assert x27_true_149 == 0xffff8000813e16c0
assert x27_true_179 == 0xffff8000817dd6c0
print(f"  故障指令将读 rq(149)->cfs.avg.load_avg = 0 并继续执行——异常的唯一必要条件是 x20 被腐化")

print()
print("== E. 页表走查几何（L3/pte=0 与第 11 次案 L2/pmd=0 的对照）==")
print("  本案 vtop x27(模板塌缩地址) 与 vtop FAR：PGD=10006057fffff403, PUD=10006057ffffe403,")
print("  PMD=10006057ffffa403（非零），PTE=0000000000000000 → 走表止步 L3，与 dmesg show_pte（pte=0）逐位一致")
print("  第 11 次案（1.4h 后下一开机）：同 PGD/PUD 值，PMD=0 → 止步 L2")
print("  → 同一 free_initmem 解映射域在不同 KASLR 相位下的拆除进度投影，非新故障通路（详见报告 §6 P4）")

print()
print("== F. 迭代号 149 的意义 ==")
print("  执行核 = 179（bt: CPU: 179），迭代对象 = CPU149（x25=0x95）")
print("  → 继第 11 次案（i=97）之后第二例『迭代号 ≠ 执行核』，再次否证槽位特异性假说")
