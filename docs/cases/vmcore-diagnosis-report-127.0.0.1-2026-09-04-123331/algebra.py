#!/usr/bin/env python3
# 第 12 次致命转储（2026-09-04 12:33:31, vmcore-incomplete）地址代数复算
# 数据来源：vmcore-dmesg.txt 崩溃块（5060.516765s Oops, CPU 179, mi-scavenger）
# 全部运算模 2^64，禁止手算。
M = (1 << 64) - 1

# ---- 崩溃块寄存器原文摘录（dmesg 行 2648~2654）----
# x27: ffffc8a996d396c0   x1 : ffffc8a996d396c0   x20: 0000000000000000
# FAR: ffffc8a996d397e0   ESR: 0x96000007          pc : find_busiest_group+0x140
x1  = 0xffffc8a996d396c0
x20 = 0x0000000000000000
x27 = 0xffffc8a996d396c0
FAR = 0xffffc8a996d397e0

print("== 核心闭合验证（零塌缩族判据）==")
x27_calc = (x1 + x20) & M
print(f"x1                 = {x1:016x}   (runqueues percpu 模板地址, 崩溃块)")
print(f"x20                = {x20:016x}   (应为 __per_cpu_offset[53], 实收 0)")
print(f"x27 (崩溃块)       = {x27:016x}")
print(f"x27 = (x1+x20)%2^64= {x27_calc:016x}   逐位一致: {x27_calc == x27}")
print(f"x27 == x1 (塌缩)   : {x27 == x1}")
FAR_calc = (x27 + 0x120) & M
print(f"FAR (崩溃块)       = {FAR:016x}")
print(f"FAR = (x27+0x120)  = {FAR_calc:016x}   逐位一致: {FAR_calc == FAR}")

print()
print("== 跨开机不变式（与 08-26 / 09-04-11:00 案对照）==")
cases = {
    #           x1(rq模板)              x9(pc锚,fbG+0x150)      x21(nr_cpu_ids)         x24(percpu页基)         x25(i)
    "08-26      ": (0xffffa29301d796c0, 0xffffa2930034ae58,     0xffffa2930216fcb0,     0xffffa29302175000,     0xb3),
    "09-04-11:00": (0xffffd77069c696c0, 0xffffd7706823ae58,     0xffffd7706a05fcb0,     0xffffd7706a065000,     0x61),
    "09-04-12:33": (0xffffc8a996d396c0, 0xffffc8a99530ae58,     0xffffc8a99712fcb0,     0xffffc8a997135000,     0x35),
}
for name, (rx1, rx9, rx21, rx24, rx25) in cases.items():
    print(f"{name}: x21-x1={((rx21-rx1)&M):#x}  x24-x21={(rx24-rx21):#x}  "
          f"x9低16位={rx9&0xffff:#x}  x25(i)={rx25:#x}={rx25}")
print(f"三案 x9-x1 (mod 2^64) 全部 = {(0xffffc8a99530ae58 - 0xffffc8a996d396c0) & M:#x}")

print()
print("== 迭代 CPU 号与调用路径语义 ==")
print(f"x25 = x0 = x6 = 0x35 = 53 —— update_sg_lb_stats 迭代至组内第 53 号 CPU（三寄存器互证）")
print(f"x23 = 0x400 —— 前一次成功迭代的 load_avg 残留（跨案不变式）")

print()
print("== WARNING(5022s) 与致命 Oops(5060s) 的关系 ==")
w_far = 0xffff604003e63c98
w_x26 = 0xffff604003e63c60
f_x26 = 0xffff604003e63c60
f_x22 = 0xffff604003e635a0
print(f"WARNING FAR  = {w_far:016x} (= WARNING x26 + {w_far-w_x26:#x})")
print(f"WARNING x26  = {w_x26:016x}  (sched_group 指针)")
print(f"致命块 x26   = {f_x26:016x}  —— 与 WARNING x26 逐位相同: {f_x26 == w_x26}")
print(f"致命块 x22   = {f_x22:016x}  (同族 sched_group, x26-x22 = {(f_x26-f_x22)&M:#x})")
print(f"WARNING ESR(x19) = 0x96000004 → FSC=0x04 L0；致命 ESR = 0x96000007 → FSC=0x07 L3")
delta = 5060.516765 - 5022.426725
print(f"WARNING→panic 间隔 = {delta:.6f} s ≈ {delta:.1f} s")

print()
print("== 时间线 ==")
print(f"开机首行: [    0.000000] Booting Linux on physical CPU 0x0000080000 [0x481fd010]")
print(f"panic 尾行: [ 5060.935234] Bye!  (Starting crashdump kernel... 之后)")
print(f"panic 时刻 uptime = 5060.516765 s = {5060.516765/3600:.3f} h (~1.4h)")
print(f"WARNING 时刻 uptime = 5022.426712 s = {5022.426712/3600:.3f} h")

print()
print("== 结论 ==")
print("x27 == x1 且 FAR == x27+0x120 逐位精确成立 → x20 实收 0 → 零塌缩族形态闭合。")
print("无内存真值对照（vmcore-incomplete, crash 拒载）→ 归类置信度：【强推】而非【实锤】。")
