#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
案 #26 (127.0.0.1-2026-09-12-00:09:19) 指令级代数闭合复算
全部算术在 mod 2^64 下进行（AArch64 通用寄存器语义）。

dmesg 寄存器事实（vmcore-dmesg.txt L5431-5483）：
  pc  = find_busiest_group+0x140/0xb60
  Code: f9400782 f879d814 2a1903e0 8b14003b (f9409377)
  x27 = ffdf57e3756297bf
  x20 = ffdfb79a8ee000ff
  x1  = ffffa048e68296c0
  x25 = 0xac (172)
  x23 = 0x3ff
  FAR = ffdf57e3756298df
  ESR = 0x96000004 (DABT current EL, FSC=0x04 level 0 translation fault)
"""
M = (1 << 64) - 1

def h(v): return f"0x{v:016x}"
def seg16(v):
    return [(v >> 48) & 0xFFFF, (v >> 32) & 0xFFFF, (v >> 16) & 0xFFFF, v & 0xFFFF]

print("=" * 78)
print("案 #26 代数闭合复算（mod 2^64）")
print("=" * 78)

x27 = 0xffdf57e3756297bf
x20 = 0xffdfb79a8ee000ff
x1  = 0xffffa048e68296c0
x25 = 0xac
x23 = 0x3ff
FAR = 0xffdf57e3756298df

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
    print("          x27 的异常形态 100% 来自 x20（percpu 偏移装载返回值）。")

# ---------------------------------------------------------------
print("\n" + "-" * 78)
print("二、加法器闭合 #2：FAR == x27 + 0x120 (mod 2^64)  ← ldr x23, [x27, #288]")
print("-" * 78)
imm = 288
f2 = (x27 + imm) & M
print(f"  x27      = {h(x27)}")
print(f"  imm      = 0x{imm:x} (=288, LDR unsigned offset 0x48<<3)")
print(f"  x27+0x120= {h(f2)}")
print(f"  FAR      = {h(FAR)}")
print(f"  闭合判定: FAR == x27 + 0x120 → {f2 == FAR}")
print(f"  反证非移位 imm=0x48: x27+0x48 = {h((x27+0x48)&M)} ≠ FAR（排除）")

# ---------------------------------------------------------------
print("\n" + "-" * 78)
print("三、致命装载指令槽位解码")
print("-" * 78)
print("  Code: f9400782 f879d814 2a1903e0 8b14003b (f9409377)")
print("  括号内 f9409377 = ldr x23, [x27, #0x120]  (288 字节偏移)")
print("  前一条 8b14003b = add  x27, x1, x20")
print("  再前 2a1903e0   = orr  x0, wzr, w25 (w25=0xac → x0=172, 与 x0 dump=0xac 吻合)")
print("  再前 f879d814   = ldr  x20, [x0, x25, sxtw #3]  ← __per_cpu_offset[172] 装载")
print(f"  x25=172 → __per_cpu_offset[172]，即 CPU172 的 percpu 偏移槽（跨槽：本核 179 未读自己的槽）")
print(f"  x20 装载返回 = {h(x20)} —— 即被腐化的 __per_cpu_offset[172] 读出值")

# ---------------------------------------------------------------
print("\n" + "-" * 78)
print("四、x20 = ffdfb79a8ee000ff 位级 16 位段分析（双端 ff 沾染形态，跨 boot 复现）")
print("-" * 78)
s20 = seg16(x20)
print(f"  x20 = {h(x20)}")
print(f"    [63:48] = 0x{s20[0]:04x}   ← 非 canonical 内核标签（真值此段应 0xffff）；顶字节 [63:56]=ff 存活")
print(f"    [47:32] = 0x{s20[1]:04x}   ← 0xb79a：随机数据段")
print(f"    [31:16] = 0x{s20[2]:04x}   ← 0x8ee0：随机数据段")
print(f"    [15: 0] = 0x{s20[3]:04x}   ← 0x00ff，低 12 位=0x0ff，页对齐段异常 + ff 落底字节 [7:0]")

print("\n  -- 与案 #23（09-11-16:30，前一 boot）形态对照 --")
c23 = 0xffa9342267e000ff
print(f"  案23 x20 = {h(c23)}   [ff][a9][34][22][67][e0][00][ff]")
print(f"  案26 x20 = {h(x20)}   [ff][df][b7][9a][8e][e0][00][ff]")
print("  结构签名逐字节对照：")
print("    字节7（顶）  : ff  ==  ff   ← 半标签钉顶，两案一致")
print("    字节6        : a9  !=  df   ← 随机")
print("    字节5..1     : 随机 != 随机  ← 高熵注入")
print("    字节1        : e0  ==  e0   ← 巧合（1/256，不具判别力）")
print("    字节0（底）  : 00 ff == 00 ff ← 尾缀 00ff，两案一致")
print("  → 同一『双端 ff 沾染』形态签名跨 boot 复现（不同次开机、不同槽位、")
print("    不同中段数据，但顶字节 ff + 尾段 00ff 的结构骨架相同）。")

print("\n  -- 对照：x1 = ffffa048e68296c0（rq 指针，canonical 真值）--")
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
print("  1. x20[63:48]=0xffdf ≠ 0xffff：顶字节 ff 存活、次字节 df 随机——")
print("     与案 23 的 0xffa9 同构（半标签钉顶 + 随机次字节）。")
print("  2. x20[15:0]=0x00ff：ff 又出现在底字节——双端 ff 沾染，与案 23 一致。")
print("  3. x20[11:0]=0x0ff ≠ 0：percpu 偏移 4K 页对齐不变式被破坏【实锤】")
print("     （谱系实测真值低 16 位有 e000/4000/8000 等，不变式取低 12 位；")
print("     本机 dmesg L321-322 percpu 4K 页 fallback 直接证据）。")

# ---------------------------------------------------------------
print("\n" + "-" * 78)
print("五、前兆谱（63 次 spurious fault）节奏分析")
print("-" * 78)
print("  63 次全部 CPU: 179；时间 2141.3s ~ 21771.3s；末次距致命 1.752s。")
print("  按间隔<60s 聚成 16 簇：")
clusters = [
    (1, 2141, 4, 10), (2, 2311, 3, 0), (3, 2521, 8, 81), (4, 2671, 10, 110),
    (5, 2981, 11, 70), (6, 3231, 2, 10), (7, 3451, 12, 60), (8, 3631, 1, 0),
    (9, 3711, 1, 0), (10, 7811, 1, 0), (11, 7892, 1, 0), (12, 8501, 1, 0),
    (13, 9131, 2, 50), (14, 20991, 2, 58), (15, 21201, 3, 70), (16, 21771, 1, 0),
]
for i, t0, n, dur in clusters:
    print(f"    簇{i:2d}: t={t0:5d}s, {n:2d} 次, 持续 {dur:3d}s")
print("""
  节奏特征：
  - 前兆集中在前 1600s（簇 1-9，57 次）+ 中段零星（簇 10-13，5 次）+
    尾段再起（簇 14-16，6 次）——『发作期-静默期-再发作』三段式；
  - 发作期内单簇最密 12 次/60s（簇 7）；
  - 末次前兆距致命 1.752s——谱系第 3 短（#20 案 0.72s、#8 案 21.17s 之后）；
  - 前兆地址前缀：ffff6040×54 + ffff0040×9，均 canonical percpu/vmalloc 区。""")

# ---------------------------------------------------------------
print("=" * 78)
print("六、最终闭合判定汇总")
print("=" * 78)
ok1 = (s == x27)
ok2 = (f2 == FAR)
print(f"  (1) x27 = x1 + x20            : {'闭合' if ok1 else '不闭合'}")
print(f"  (2) FAR = x27 + 0x120         : {'闭合' if ok2 else '不闭合'}")
print(f"  (3) x25 = 172 → __per_cpu_offset[172]（跨槽：CPU179 读 CPU172 的槽）")
print(f"  (4) x20 低 12 位 = 0x0ff ≠ 0：percpu 偏移 4K 页对齐不变式破坏【实锤】")
print(f"  (5) x20[63:48] = 0xffdf ≠ 0xffff：canonical 标签错位【实锤】")
print(f"  (6) 前兆 63 次全 CPU179、末次距致命 1.752s、taint W 自洽")
print()
print("  推理链：x20 装载返回坏值 → add（纯正确指令）传播 → ldr 以坏 x27 寻址 →")
print("          FAR 非法（between）→ L0 translation fault → Oops。")
print("          除 x20 装载本身外，每一步均被代数闭合验证为正确执行。")
