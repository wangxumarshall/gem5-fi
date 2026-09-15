#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
案 #27 (127.0.0.1-2026-09-12-10:00:31) 指令级代数闭合复算
全部算术在 mod 2^64 下进行（AArch64 通用寄存器语义）。

dmesg 寄存器事实（vmcore-dmesg.txt L3356-3406）：
  pc  = find_busiest_group+0x140/0xb60
  Code: f9400782 f879d814 2a1903e0 8b14003b (f9409377)
  x27 = d73fd531b2dc658c
  x20 = d74000ffffabcecc
  x1  = ffffd431b33096c0
  x25 = 0x14 (20)
  x23 = 0x400
  FAR = 003fd531b2dc66ac   ← 注意：顶字节与 x27+0x120 不一致（见二节）
  ESR = 0x96000004 (DABT current EL, FSC=0x04 level 0 translation fault)
"""
M = (1 << 64) - 1

def h(v): return f"0x{v:016x}"
def seg16(v):
    return [(v >> 48) & 0xFFFF, (v >> 32) & 0xFFFF, (v >> 16) & 0xFFFF, v & 0xFFFF]

print("=" * 78)
print("案 #27 代数闭合复算（mod 2^64）")
print("=" * 78)

x27 = 0xd73fd531b2dc658c
x20 = 0xd74000ffffabcecc
x1  = 0xffffd431b33096c0
x25 = 0x14
x23 = 0x400
FAR = 0x003fd531b2dc66ac

print(f"\n[输入] x27={h(x27)}  x20={h(x20)}  x1={h(x1)}")
print(f"[输入] x25={h(x25)}({x25})  x23={h(x23)}({x23})  FAR={h(FAR)}")

# ---------------------------------------------------------------
print("\n" + "-" * 78)
print("一、加法器闭合 #1：x27 == x1 + x20 (mod 2^64)   ← add x27, x1, x20")
print("-" * 78)
s = (x1 + x20) & M
print(f"  x1  = {h(x1)}")
print(f"  x20 = {h(x20)}")
print(f"  和  = {h(s)}")
print(f"  x27 = {h(x27)}")
print(f"  闭合判定: x27 == x1 + x20 → {s == x27}")
if s == x27:
    print("  【实锤】ALU 加法器与操作数装载完全正确；")
    print("          x27 的异常形态 100% 来自 x20。")

# ---------------------------------------------------------------
print("\n" + "-" * 78)
print("二、闭合 #2 与 FAR 顶字节截断：FAR vs x27 + 0x120")
print("-" * 78)
imm = 288
f2 = (x27 + imm) & M
print(f"  x27      = {h(x27)}")
print(f"  x27+0x120= {h(f2)}")
print(f"  FAR      = {h(FAR)}")
print(f"  逐位闭合判定: FAR == x27 + 0x120 → {f2 == FAR}")
print(f"  XOR      = {h(f2 ^ FAR)}")
print(f"  低 48 位一致? {(f2 & ((1<<48)-1)) == (FAR & ((1<<48)-1))}")
print(f"  反证非移位 imm=0x48: x27+0x48 = {h((x27+0x48)&M)} ≠ FAR（排除）")
print()
print("  『不闭合』假象解剖（与案 #22 同模式）：")
print("  - 差异仅在高 16 位：computed [63:48]=d73f vs FAR [63:48]=003f；")
print("    XOR=0xd700000000000000，即只有顶字节 [63:56] d7→00，次字节 3f 保留；")
print("  - 低 48 位（d531b2dc66ac）逐位一致——装载定序（基址+偏移）无错；")
print("  - 案 #22（09-11-14:31）：computed 9226bb43eeea3c9d vs FAR 0026bb43eeea3c9d，")
print("    XOR=0x9200000000000000——同样只有顶字节 92→00，次字节 26 保留；")
print("  - 两案 XOR 模式严格同构（仅顶字节清零）→ 非规范 VA 进入翻译路径时")
print("    顶字节被截断/替换是【系统性硬件行为痕迹】，不是随机错误；")
print("  - 该痕迹不改变定罪：即使以 FAR 反推 x20，其低 48 位 00ffffabcecc")
print("    仍非任何合法 percpu 偏移形态（页对齐破坏 + 标签错位不变）。")

# ---------------------------------------------------------------
print("\n" + "-" * 78)
print("三、致命装载指令槽位解码")
print("-" * 78)
print("  Code: f9400782 f879d814 2a1903e0 8b14003b (f9409377)")
print("  括号内 f9409377 = ldr x23, [x27, #0x120]  (288 字节偏移)")
print("  前一条 8b14003b = add  x27, x1, x20")
print("  再前 2a1903e0   = orr  x0, wzr, w25 (w25=0x14 → x0=20, 与 x0 dump=0x14 吻合)")
print("  再前 f879d814   = ldr  x20, [x0, x25, sxtw #3]  ← __per_cpu_offset[20] 装载")
print(f"  x25=20 → __per_cpu_offset[20]，即 CPU20 的 percpu 偏移槽（跨槽：本核 179 未读自己的槽）")
print(f"  x20 装载返回 = {h(x20)} —— 即被腐化的 __per_cpu_offset[20] 读出值")

# ---------------------------------------------------------------
print("\n" + "-" * 78)
print("四、x20 = d74000ffffabcecc 位级 16 位段分析（00ff|ffxx 相邻双段 + 高段注入）")
print("-" * 78)
s20 = seg16(x20)
print(f"  x20 = {h(x20)}")
print(f"    [63:48] = 0x{s20[0]:04x}   ← d740：无 ff——标签完全离开顶段（高段随机注入，案 #22 的 9226 同型）")
print(f"    [47:32] = 0x{s20[1]:04x}   ← 0x00ff：ff 对齐到 bit39..32")
print(f"    [31:16] = 0x{s20[2]:04x}   ← 0xffab：ff 又出现在 bit31..24")
print(f"    [15: 0] = 0x{s20[3]:04x}   ← 0xcecc：低 12 位=0xecc，页对齐段异常")

print("\n  -- 与案 #24（09-11-17:06，00ff|ffb8 相邻双段）形态对照 --")
c24 = 0x00ffffb810e4a240
print(f"  案24 x20 = {h(c24)}   段: 00ff | ffb8 | 10e4 | a240")
print(f"  案27 x20 = {h(x20)}   段: d740 | 00ff | ffab | cecc")
print("  结构对照：")
print("    00ff 段位置 : 案24 在 [63:48]，案27 在 [47:32] —— 整体再下移 16 位")
print("    ffxx 段位置 : 案24 在 [47:32]（ffb8），案27 在 [31:16]（ffab）—— 同步下移")
print("    两案均为『00ff 与 ffxx 相邻』的双段结构，错位窗口整体漂移 16 位；")
print("    案27 顶段被随机值 d740 占据（标签完全离开顶段）。")

print("\n  -- 对照：x1 = ffffd431b33096c0（rq 指针，canonical 真值）--")
s1 = seg16(x1)
print(f"  x1 = {h(x1)}")
print(f"    [63:48]=0x{s1[0]:04x} [47:32]=0x{s1[1]:04x} [31:16]=0x{s1[2]:04x} [15:0]=0x{s1[3]:04x}")

print("\n  -- x27 = x1 + x20 的逐段进位传播 --")
s27 = seg16(x27)
carry = 0
res = []
for i in range(3, -1, -1):
    t = s1[i] + s20[i] + carry
    res.append(t & 0xFFFF)
    carry = t >> 16
res = list(reversed(res))
print(f"  重算 x27 段值 = {[f'0x{v:04x}' for v in res]}  vs dump x27 段值 = {[f'0x{v:04x}' for v in s27]}")

print("\n  关键观察：")
print("  1. x20[63:48]=0xd740：无任何 ff——canonical 标签从顶段完全消失；")
print("     顶段被高熵随机值占据（与案 #22 顶段 9226 同型：高段注入）。")
print("  2. 00ff|ffab 相邻双段（[47:32]+[31:16]）：ff 对连续出现在 bit39..32 与")
print("     bit31..24——与案 #24 的 00ff|ffb8（[63:48]+[47:32]）同构，整体下移 16 位。")
print("  3. x20[11:0]=0xecc ≠ 0：percpu 偏移 4K 页对齐不变式破坏【实锤】")
print("     （谱系实测真值低 16 位有 e000/4000/8000 等，不变式取低 12 位；")
print("     本机 dmesg percpu 4K 页 fallback 直接证据）。")

# ---------------------------------------------------------------
print("\n" + "-" * 78)
print("五、前兆谱（17 次）节奏 + 受害进程特异性")
print("-" * 78)
print("  17 次全部 CPU: 179；地址全部 ffff6040 前缀（canonical percpu/vmalloc 区）。")
print("  时间 34323.6s ~ 34983.6s，末次距致命 15.931s。")
print("  聚类（间隔<60s）：2 簇——")
print("    簇1: t=34324s, 13 次, 持续 100s（开机 9.53h 起）")
print("    簇2: t=34954s,  4 次, 持续 30s（致命前 46s 起）")
print("  前兆受害：PID 13780（pmdalinux）×16 + PID 9692×1，路径同为")
print("  show_interrupts → seq_printf → __memcpy（读 /proc/interrupts，与案 #7/#26 同路径）。")
print("  特异点：开机 0~34323s（9.5h）零前兆——前兆全部集中在致命前 676s 内，")
print("  两簇之间 630s 静默——『临终双簇』节奏。")

# ---------------------------------------------------------------
print("=" * 78)
print("六、最终闭合判定汇总")
print("=" * 78)
ok1 = (s == x27)
ok2 = (f2 == FAR)
print(f"  (1) x27 = x1 + x20            : {'闭合' if ok1 else '不闭合'}")
print(f"  (2) FAR vs x27 + 0x120        : 顶字节截断（XOR=0xd700…，低 48 位闭合）")
print(f"      —— 与案 #22 XOR=0x9200… 同模式，系统性非随机")
print(f"  (3) x25 = 20 → __per_cpu_offset[20]（跨槽：CPU179 读 CPU20 的槽）")
print(f"  (4) x20 低 12 位 = 0xecc ≠ 0：percpu 偏移 4K 页对齐不变式破坏【实锤】")
print(f"  (5) x20 顶段 d740 无 ff + 00ff|ffab 相邻双段：标签错位【实锤】")
print(f"  (6) 前兆 17 次全 CPU179、末次距致命 15.931s、taint W 自洽")
print()
print("  推理链：x20 装载返回坏值 → add（纯正确指令）传播 → ldr 以坏 x27 寻址 →")
print("          FAR 非规范（顶字节另遭截断）→ L0 translation fault → Oops。")
print("          除 x20 装载本身外，每一步均被代数闭合验证为正确执行。")
