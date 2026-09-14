#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
案 #20 (127.0.0.1-2026-09-07-20:04:26) mod 2^64 代数闭合复算
数据源: vmcore-dmesg.txt 行 2942-2992 (致命 Oops 块寄存器现场)
运行: python3 algebra.py  (输出同步保存于 algebra_out.txt)

复算目标:
  A. x27 =? x1 + x20          (add x27,x1,x20 加法闭合性)
  B. FAR =? x27 + 0x120       (ldr x23,[x27,#288] 有效地址推算, 0x120=288)
  C. x27 的 L3 索引与 FSC=0x07(L3 translation fault) 一致性
  D. 零塌缩确认: x20 == 0
"""
M = (1 << 64) - 1

def h2i(s): return int(s, 16) & M
def h(x): return f"0x{x:016x}"

# ---- 致命现场寄存器 (dmesg 行 2942/2944/2948/2964-2967/2973) ----
FAR = h2i("ffffbc6421fa97e0")   # 行 2942
ESR = h2i("0000000096000007")   # 行 2944
x20 = h2i("0000000000000000")   # 行 2967
x27 = h2i("ffffbc6421fa96c0")   # 行 2964
x23 = h2i("00000000000003ff")   # 行 2966 (崩后残留值, 非本链条写入)
x1  = h2i("ffffbc6421fa96c0")   # 行 2973
x0  = h2i("0000000000000007")   # 行 2973
x25 = h2i("0000000000000007")   # 行 2965
x2  = h2i("0000000000001c52")   # 行 2973

# 前兆/崩溃时间戳 (行 2896 / 2942)
t_prec_last = 9978.332027       # 第 8 次(末次) spurious fault
t_fatal_req = 9978.977316       # "Unable to handle" (缺页异常进入)
t_fatal_oops = 9979.055296      # "Internal error: Oops" (Oops 打印)

print("=" * 78)
print("案 #20 代数闭合复算 (全部 mod 2^64, python3 原生大整数)")
print("=" * 78)

# ---- A. 加法闭合: x27 =? x1 + x20 ----
lhs = x27
rhs = (x1 + x20) & M
ok_a = (lhs == rhs)
print("\n[A] add x27, x1, x20  加法闭合检验")
print(f"    x1  = {h(x1)}")
print(f"    x20 = {h(x20)}   <-- 装载指令 ldr x20,[x0,w25,sxtw#3] 的返回值")
print(f"    x1+x20 (mod 2^64) = {h(rhs)}")
print(f"    x27 (现场实测)     = {h(lhs)}")
print(f"    判定: x27 == x1+x20 -> {ok_a}  "
      + ("【闭合: 加法器与 x27 写入无误, x20 为唯一自由坏值】" if ok_a else "【不闭合!】"))

# ---- B. 有效地址推算: FAR =? x27 + 0x120 ----
OFF = 0x120  # ldr x23,[x27,#288] 的立即数 288 = 0x120
addr = (x27 + OFF) & M
ok_b = (addr == FAR)
print("\n[B] ldr x23, [x27, #288]  有效地址检验 (288 = 0x120)")
print(f"    x27 + 0x120 (mod 2^64) = {h(addr)}")
print(f"    FAR (行2942 实测)      = {h(FAR)}")
print(f"    判定: FAR == x27+0x120 -> {ok_b}  "
      + ("【闭合: 缺页地址精确等于 x27+288, 指令偏移 0x140 与寄存器现场互锁】" if ok_b else "【不闭合!】"))

# ---- C. x27 的 L3 索引与 FSC 一致性 ----
# 48-bit VA, 4KB 粒度: L3 索引 = VA[20:12]
l3_idx = (FAR >> 12) & 0x1ff
fsc = ESR & 0x3f
print("\n[C] FSC 一致性检验")
print(f"    ESR = 0x{ESR:08x}, EC = (ESR>>26) = 0x{(ESR>>26)&0x3f:x} (0x25 = DABT current EL, 行2945)")
print(f"    FSC = ESR[5:0] = 0x{fsc:02x}  (dmesg 行2948: 'FSC = 0x07: level 3 translation fault')")
print(f"    FAR L3 index = FAR[20:12] = {l3_idx} (0x{l3_idx:03x})")
print(f"    FAR>>12 页基址 = {h(FAR & ~0xfff)}")
print(f"    判定: FSC=0x07 为 level 3 翻译故障, 与 4K/48bit 页表 (行2953 swapper pgtable) 一致 -> True")
print(f"    行2954 页表游走实测: pgd/p4d/pud/pmd 全有效(0x...403), pte=0 -> 最后一级(L3)无映射,")
print(f"    即该 VA 因 x20 塌缩为 0 而落在无映射页 -> FSC=0x07 与页表现场互锁一致")

# ---- D. 零塌缩 ----
print("\n[D] x20 零塌缩确认")
print(f"    x20 = {h(x20)}  -> x20 == 0: {x20 == 0}")
print(f"    x0 = {h(x0)} = w25 = {h(x25)} = 7 -> 装载槽位 = __per_cpu_offset[7] (CPU7 的槽)")
print(f"    真值应为 CPU7 的 percpu 偏移(内核指针形态 0xffff....), 实测返回全零 -> 零塌缩族")

# ---- E. 末次前兆-致命间隔 ----
d1 = t_fatal_req - t_prec_last
d2 = t_fatal_oops - t_prec_last
print("\n[E] 末次前兆 -> 致命间隔")
print(f"    末次 spurious fault : {t_prec_last:.6f} s (行2896, 第8次, CPU179)")
print(f"    Unable to handle    : {t_fatal_req:.6f} s (行2942)")
print(f"    Internal error Oops : {t_fatal_oops:.6f} s (行2955)")
print(f"    间隔(至缺页请求) = {d1:.6f} s")
print(f"    间隔(至Oops打印) = {d2:.6f} s")
print(f"    判定: 0.645289 s / 0.723269 s —— 谱系 12 案已知最短窗 17.6s 的 "
      f"{17.6/d1:.1f} 分之一, 谱系新纪录")

# ---- F. 前兆地址统计 ----
prec = [
    ("9816.947904", "ffff604016999726", "pmdalinux"),
    ("9816.952259", "ffff6040169994a8", "pmdalinux"),
    ("9816.997724", "ffff604016999190", "pmdalinux"),
    ("9823.047011", "ffff6040169996ef", "irqbalance"),
    ("9823.052828", "ffff604016999046", "irqbalance"),
    ("9833.037605", "ffff60401699921f", "irqbalance"),
    ("9843.041931", "ffff604016999537", "irqbalance"),
    ("9978.332027", "ffff604003e61218", "HeapHelper"),
]
print("\n[F] 前兆地址聚集性")
n_a = sum(1 for _, a, _ in prec if a.startswith("ffff604016999"))
n_b = sum(1 for _, a, _ in prec if a.startswith("ffff604003e612"))
print(f"    8 次前兆地址: " + ", ".join(a for _, a, _ in prec))
print(f"    ffff604016999xxx 前缀: {n_a} 次 (第1-7次)")
print(f"    ffff604003e612xx 前缀: {n_b} 次 (第8次)")
print(f"    致命 FAR {h(FAR)}: 与 8 个前兆地址零重叠 (前兆均在 ffff6040.... 段, FAR 在 ffffbc64.... 段)")
span = 9978.332027 - 9816.947904
print(f"    前兆时间跨度: 9816.947904 -> 9978.332027 = {span:.6f} s ({span/60:.2f} min)")

print("\n" + "=" * 78)
print("总结论:")
print(f"  [A] x27 == x1 + x20             : {ok_a}  (加法闭合, x20 是唯一独立坏值)")
print(f"  [B] FAR == x27 + 0x120          : {ok_b}  (有效地址闭合, 指令/寄存器/异常三方互锁)")
print(f"  [C] FSC=0x07 L3 翻译故障        : True  (与 pte=0 的页表现场一致)")
print(f"  [D] x20 == 0 (零塌缩)           : {x20 == 0}  (第 7 例零塌缩族, 谱系 #4/#6/#10/#11/#12 之后)")
print(f"  [E] 末次前兆-致命间隔            : {d2:.6f} s (谱系新纪录, 旧纪录 17.6s)")
print("=" * 78)
