#!/usr/bin/env python3
"""案18（第18次致命转储 127.0.0.1-2026-09-07-13:51:42）代数复算
所有寄存器值取自 vmcore-dmesg.txt 崩溃块原文；内存真值取自 crash session5/6
（/tmp/crash-0907/session5.log、session6.log）与 session3（/tmp/crash-0907/session3.log）。
"""
M = 1 << 64

# ── 崩溃块实测（dmesg L4295 起）──
x1  = 0xffffdf9b728096c0   # ldr x1,[x19,#56] → &runqueues（session5: sym 逐位命中）
x20 = 0x0000000000000000   # ldr x20,[x0,w25,sxtw#3] 实收（零塌缩）
x27 = 0xffffdf9b728096c0   # add x27,x1,x20
FAR = 0xffffdf9b728097e0   # ldr x23,[x27,#0x120] 的故障地址
x25 = 8                    # 迭代号 i（CPU 8）
x9  = 0xffffdf9b70ddae58
x21 = 0xffffdf9b72bffcb0
x24 = 0xffffdf9b72c05000
x23 = 0x400

# ── crash 内存真值 ──
RUNQUEUES_SYM   = 0xffffdf9b728096c0  # session5: sym ffffdf9b728096c0 → runqueues
PCPU_OFF_0      = 0xffffa0650d80e000  # session3: __per_cpu_offset[0]
PCPU_OFF_8      = 0xffffa0650d91e000  # session3: __per_cpu_offset[8]
PCPU_OFF_179    = 0xffffa0650efd4000  # session3: __per_cpu_offset[179]
RQ8_INSTANCE    = 0xffff8000801276c0  # session5: p runqueues → [8]

def chk(name, ok):
    print(("PASS " if ok else "FAIL ") + name)

print("== 案18 寄存器代数闭合 ==")
chk("x1 == &runqueues（crash sym 实锤）", x1 == RUNQUEUES_SYM)
chk("x27 == x1 + x20 (mod 2^64)", x27 == (x1 + x20) % M)
chk("FAR == x27 + 0x120", FAR == (x27 + 0x120) % M)
chk("x25 == 8（迭代 CPU 8 ≠ 执行核 179）", x25 == 8)

print("\n== KASLR 不变式（跨开机指纹，对齐 12 案 census §2.8）==")
chk("x9 - x1 == 0xfffffffffe5d1798", (x9 - x1) % M == 0xfffffffffe5d1798)
chk("x21 - x1 == 0x3f65f0", (x21 - x1) % M == 0x3f65f0)
chk("x24 - x21 == 0x5350", (x24 - x21) % M == 0x5350)
chk("x9 低 16 位 == ae58（fbG+0x150 页内偏移）", (x9 & 0xffff) == 0xae58)
chk("x23 == 0x400（前次迭代 load_avg 残留）", x23 == 0x400)

print("\n== __per_cpu_offset[] 数组完整性（三点等差）==")
chk("off[8] - off[0] == 8*0x22000", PCPU_OFF_8 - PCPU_OFF_0 == 8 * 0x22000)
chk("off[179] - off[0] == 179*0x22000", PCPU_OFF_179 - PCPU_OFF_0 == 179 * 0x22000)

print("\n== 反事实：若 x20 收到真值 off[8] ==")
x27_true = (x1 + PCPU_OFF_8) % M
chk("x27_true == crash p runqueues [8] 实例（逐位）", x27_true == RQ8_INSTANCE)
print(f"   x27_true      = 0x{x27_true:016x}")
print(f"   反事实访问地址 = 0x{(x27_true + 0x120) % M:016x}（cpu8 rq + 0x120, cfs_rq.load_avg 域）")
print(f"   实测 FAR      = 0x{FAR:016x}（= runqueues 模板 + 0x120, init 解映射域）")
print(f"   汉明距离(x27_true, x27) = {bin(x27_true ^ x27).count('1')} 位（真值高位 ffff800080… vs 塌缩 ffffdf9b72…）")
