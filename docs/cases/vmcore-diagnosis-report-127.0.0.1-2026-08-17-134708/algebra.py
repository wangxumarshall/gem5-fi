#!/usr/bin/env python3
# 第 2 次转储（2026-08-17-13:47:08）寄存器代数复算
# 数据来源：vmcore-dmesg.txt 崩溃块（dmesg 行 3749 起），逐位与 dmesg 原文核对
# 所有运算模 2^64，禁止手算 —— 本脚本是唯一计算来源

M = (1 << 64) - 1

def h(x):
    return f"0x{x:016x}"

# ---- 崩溃块寄存器（dmesg 原文摘录） ----
x25 = 0xaf              # 迭代 CPU 号 = 175
x20 = 0x00ffffa827b20fe0  # 应为 __per_cpu_offset[175]，实收值
x1  = 0xffffd7d8cdf196c0  # &runqueues percpu 模板地址
x27 = 0x00ffd780f5a3a6a0  # 实收寄存器值
FAR = 0x00ffd780f5a3a7c0  # 硬件上报故障地址
x23 = 0x400
x21 = 0xffffd7d8ce30fcb0  # nr_cpu_ids 指针
x24 = 0xffffd7d8ce315000  # __per_cpu_offset 数组页基址锚
x22 = 0xffff604003e9ec00
x26 = 0xffff604003e9ec00

print("== 寄存器代数闭合（第 2 次转储 2026-08-17-13:47:08）==\n")

# ---- 闭合等式 1：x27 = x1 + x20 (mod 2^64) ----
s = (x1 + x20) & M
print(f"[1] x27 = x1 + x20 (mod 2^64)")
print(f"    x1  = {h(x1)}   (&runqueues 模板)")
print(f"    x20 = {h(x20)}   (实收，应为 __per_cpu_offset[175])")
print(f"    x1 + x20 = {h(s)}")
print(f"    寄存器 x27 = {h(x27)}")
print(f"    逐位相等: {s == x27}")
print()

# ---- 闭合等式 2：FAR = x27 + 0x120 (mod 2^64) ----
f = (x27 + 0x120) & M
print(f"[2] FAR = x27 + 0x120 (mod 2^64)")
print(f"    x27 + 0x120 = {h(f)}")
print(f"    硬件 FAR    = {h(FAR)}")
print(f"    逐位相等: {f == FAR}")
print()

# ---- 撕裂移位族形态分析：x20 相对 08-26 案真值的形态 ----
# 08-26 案（第 6 次转储）实测 __per_cpu_offset 数组为等差数列：
#   base = 0xffffdd6d7e29e000, 步长 0x22000, 即 entry[i] = base + i*0x22000
# 本开机 KASLR/内存布局不同，数值不可直接套用；但同一内核同一启动风格。
# 撕裂移位族判定核心是【形态】而非真值：x20 = 00ffffa827b20fe0
# 高 2 字节为 0x00ff —— 恰是"整体右移 8 位"(≫8) 的特征：任何
# 0xffff.... 真值右移 8 位后高字节变 0x00、次高字节变 0xff。
v = x20
print(f"[3] x20 撕裂形态分析")
print(f"    x20 = {h(v)}")
print(f"    高 4 位字节: {v >> 32:08x}  （真值应为 ffffxxxx 形态）")
print(f"    x20 >> 8  = {h((v >> 8))}")
print(f"    (x20 << 8) & M = {h((v << 8) & M)}   ← 若真值 = x20 左移 8 位（即 x20 = 真值 ≫ 8）")
print(f"    注：candidate_true = 0x{((v << 8) & M):x} 形态为 ffffa8a27b20fe00")
print(f"    非规范检查：x20 高 16 位 = 0x{v >> 48:04x} ≠ 0xffff → 非规范内核指针")
print()

# ---- FAR 高位异常：FAR 与 x27 高字节对照 ----
print(f"[4] FAR 高位形态")
print(f"    FAR = {h(FAR)}  高 16 位 = 0x{FAR >> 48:04x}（非规范：'between user and kernel address ranges'）")
print(f"    x27 = {h(x27)}  高 16 位 = 0x{x27 >> 48:04x}")
print(f"    FAR 与 x27 仅低 63 位内差 0x120，高 16 位同源（同为撕裂结果）")
print()

# ---- 不变式核对（与既往 5 案跨开机指纹） ----
print(f"[5] 跨开机不变式")
print(f"    x23 = {h(x23)} （≡0x400，前次成功迭代 load_avg 残留，既往 5 案一致）")
print(f"    x22 == x26: {x22 == x26} （{h(x22)}，sched_group slab 指针成对，既往一致）")
print(f"    x21 = {h(x21)} （nr_cpu_ids）")
print(f"    x24 = {h(x24)}")
print(f"    x21 - x24 = {h((x21 - x24) & M)} （既往恒为 -0x5350）")
print()

# ---- 反事实推演 ----
# 真值 offset[175] 本案不可知（vmcore incomplete），但 08-26 案实测数组
# 是等差数列、真值 ≈ 0xffffdddd.... 形态。反事实仅做形态推演：
# 若 x20 收到真值 T（0xffff.... 规范指针），则 x27_true = x1 + T
# 高 16 位 = ffff（x1 高16=ffff + T 高16=ffff，进位后仍 ffff8000 型），
# 是规范内核地址，vtop 应 VALID —— 与 08-26 案反事实实验同构。
print(f"[6] 反事实形态推演（不可数值验证，标注边界）")
print(f"    x1 高 16 位 = 0x{x1 >> 48:04x}")
print(f"    若 T 为规范 0xffff.... 值，x1+T 高位进位 → ffff8000 型规范地址（同 08-26 案）")
print(f"    本案 vmcore-incomplete，无法 vtop 验证 —— 反事实止于形态层【边界声明】")

# ---- 补充：x20 字节级撕裂形态分析（与 15:58 案同构对照） ----
print("\n== 补充：x20 字节级撕裂形态 ==")
b = x20.to_bytes(8, 'big')
print(f"    x20 字节序列（大端 B0..B7）: {' '.join(f'{x:02x}' for x in b)}")
print(f"    高 2 字节 = {b[0]:02x} {b[1]:02x} （规范内核指针应为 ff ff）")
x20_1558 = 0x00ffffcc879da2e0   # 15:58 案 x20（既往已证 offset[0]≫8 形态）
b2 = x20_1558.to_bytes(8, 'big')
print(f"    15:58 案 x20 字节序列:      {' '.join(f'{x:02x}' for x in b2)}")
print(f"    两案高 2 字节完全一致（00 ff）: {b[:2] == b2[:2]}")
T = (x20 << 8) & M
print(f"    反推 T = x20 << 8 = {h(T)}，高 16 位 = 0x{T >> 48:04x} → 规范 ffff 形态")
print(f"    被撕裂移出的低 8 位不可恢复（信息丢失）→ 只能形态归类，无法数值对照真值")
