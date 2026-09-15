#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
案 #24 (127.0.0.1-2026-09-11-17:06:07) 指令级代数闭合复算
全部算术在 mod 2^64 下进行（AArch64 通用寄存器语义）。

已勘察寄存器事实（dmesg L2600-2624）：
  pc  = find_busiest_group+0x140/0xb60
  Code: f9400782 f879d814 2a1903e0 8b14003b (f9409377)
  x27 = 00ffc7a7ac4a3900
  x20 = 00ffffb810e4a240
  x1  = ffffc7ef9b6596c0
  x25 = 0x32 (50)
  x23 = 0x400
  FAR = 00ffc7a7ac4a3a20
  ESR = 0x96000004 (DABT current EL, FSC=0x04 level 0 translation fault)
"""
M = (1 << 64) - 1

def h(v): return f"0x{v:016x}"
def seg16(v):
    """按 16 位段切片：[63:48] [47:32] [31:16] [15:0]"""
    return [(v >> 48) & 0xFFFF, (v >> 32) & 0xFFFF, (v >> 16) & 0xFFFF, v & 0xFFFF]

print("=" * 78)
print("案 #24 代数闭合复算（mod 2^64）")
print("=" * 78)

x27 = 0x00ffc7a7ac4a3900
x20 = 0x00ffffb810e4a240
x1  = 0xffffc7ef9b6596c0
x25 = 0x32
x23 = 0x400
FAR = 0x00ffc7a7ac4a3a20

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
    print("          x27 的异常形态 100% 来自 x20（percpu 偏移装载返回值），")
    print("          而非加法指令本身。")

# ---------------------------------------------------------------
print("\n" + "-" * 78)
print("二、加法器闭合 #2：FAR == x27 + 0x120 (mod 2^64)  ← ldr x23, [x27, #288]")
print("-" * 78)
# Code dump 中 (f9409377): ldr x23, [x27, #288] —— 288 = 0x120 = 0x48 << 3
imm = 288
f2 = (x27 + imm) & M
print(f"  x27      = {h(x27)}")
print(f"  imm      = 0x{imm:x} (=288, LDR unsigned offset 0x48<<3)")
print(f"  x27+0x120= {h(f2)}")
print(f"  FAR      = {h(FAR)}")
print(f"  闭合判定: FAR == x27 + 0x120 → {f2 == FAR}")
# 反证 0x48 原始 imm 解码（非左移 3 位）：0x2a1903e0 是 orr w0,wzr,w25(uxtw?)
print(f"  反证非移位 imm=0x48: x27+0x48 = {h((x27+0x48)&M)} ≠ FAR（排除）")

# ---------------------------------------------------------------
print("\n" + "-" * 78)
print("三、致命装载指令槽位解码")
print("-" * 78)
print("  Code: f9400782 f879d814 2a1903e0 8b14003b (f9409377)")
print("  括号内 f9409377 = ldr x23, [x27, #0x120]  (288 字节偏移)")
print("  前一条 8b14003b = add  x27, x1, x20")
print("  再前 2a1903e0   = orr  x0, wzr, w25 (w25=0x32 → x0=50, 与 x0 dump=0x32 吻合)")
print("  再前 f879d814   = ldr  x20, [x0, x25, sxtw #3]  ← __per_cpu_offset[50] 装载")
print(f"  x25=50 → __per_cpu_offset[50]，即 CPU50 的 percpu 偏移槽（跨槽：本核 179 未读自己的槽）")
print(f"  x20 装载返回 = {h(x20)} —— 即被腐化的 __per_cpu_offset[50] 读出值")

# ---------------------------------------------------------------
print("\n" + "-" * 78)
print("四、x20 = 00ffffb810e4a240 位级 16 位段分析（标签错位形态）")
print("-" * 78)
s20 = seg16(x20)
print(f"  x20 = {h(x20)}")
print(f"    [63:48] = 0x{s20[0]:04x}   ← 非 canonical 内核标签（真值此段应 0xffff）")
print(f"    [47:32] = 0x{s20[1]:04x}   ← 0xffb8：含 ff 沾染段")
print(f"    [31:16] = 0x{s20[2]:04x}   ← 0x10e4")
print(f"    [15: 0] = 0x{s20[3]:04x}   ← 0xa240，页对齐段异常（真值低 16 位应为 0x0000）")

print("\n  -- 对照：x1 = ffffc7ef9b6596c0（rq->cfs 指针，canonical 真值）--")
s1 = seg16(x1)
print(f"  x1 = {h(x1)}")
print(f"    [63:48]=0x{s1[0]:04x} [47:32]=0x{s1[1]:04x} [31:16]=0x{s1[2]:04x} [15:0]=0x{s1[3]:04x}")

print("\n  -- x27 = x1 + x20 的逐段进位传播 --")
s27 = seg16(x27)
print(f"  x27 = {h(x27)}")
print(f"    [63:48]=0x{s27[0]:04x} [47:32]=0x{s27[1]:04x} [31:16]=0x{s27[2]:04x} [15:0]=0x{s27[3]:04x}")

# 逐段加法表（含进位）
print("\n  逐段加法（低段→高段，含进位）：")
carry = 0
rows = []
for i in range(3, -1, -1):
    t = s1[i] + s20[i] + carry
    r = t & 0xFFFF
    carry = t >> 16
    name = ["[63:48]", "[47:32]", "[31:16]", "[15: 0]"][i]
    rows.append((name, s1[i], s20[i], r, carry))
    print(f"    {name}: 0x{s1[i]:04x} + 0x{s20[i]:04x} + c{carry if carry==0 else ''}"
          f" = 0x{r:04x} (进位输出 {carry})")
    carry = carry  # 下一轮的输入进位
# 重算正确（上面打印进位有竞争，严格重算）:
carry = 0
res = []
for i in range(3, -1, -1):
    t = s1[i] + s20[i] + carry
    res.append(t & 0xFFFF)
    carry = t >> 16
res = list(reversed(res))
print(f"  重算 x27 段值 = {[f'0x{v:04x}' for v in res]}  vs dump x27 段值 = {[f'0x{v:04x}' for v in s27]}")

print("\n  关键观察：")
print("  1. x20[63:48]=0x00ff —— canonical 内核指针此段必为 0xffff；")
print("     这里是 00ff：ff 标签出现在 bit47..40，位置比真值低 8 位，")
print("     即『ff 标签右移一个字节段』（错位沾染），与案22/23 的 ff 迁移谱同族。")
print("  2. x20[47:32]=0xffb8 —— ff 出现在次高 16 位段，进一步证明 ff 沾染")
print("     跨越段边界（bit47..32 区间内 ff 前缀 + 尾随 b8）。")
print("  3. x20[11:0]=0x240 ≠ 0 —— percpu 偏移真值低 12 位恒为 0（4K 页对齐；")
print("     谱系实测真值低 16 位有 e000/4000/8000 等，故不变式取低 12 位），")
print("     该 0x240 是注入位，且经加法污染 x27[15:0]=0x900+0x240+进位路径。")

# ---------------------------------------------------------------
print("\n" + "-" * 78)
print("五、ff 标签位置迁移谱（同日四连崩 + 谱系前案对照）")
print("-" * 78)
print("  坏值(x20 或等价)          [63:48] [47:32] [31:16] [15: 0]  ff/ffff 沾染段")
fam = [
    ("案22 09-11-14:31 x20=9226e000ffffa4bd", 0x9226e000ffffa4bd),
    ("案23 09-11-16:30 x20=ffa9342267e000ff", 0xffa9342267e000ff),
    ("案24 09-11-17:06 x20=00ffffb810e4a240", x20),
    ("案25 09-11-17:58 x20=0000000000000000", 0x0000000000000000),
]
for name, v in fam:
    sg = seg16(v)
    marks = []
    for j in range(4):
        if sg[j] == 0xFFFF: marks.append(f"FFFF@{j}")
        elif sg[j] == 0xFF00: marks.append(f"FF00@{j}")
        elif sg[j] == 0x00FF: marks.append(f"00FF@{j}")
        elif (sg[j] & 0xFF00) == 0xFF00: marks.append(f"FFxx@{j}")
        elif (sg[j] & 0x00FF) == 0x00FF: marks.append(f"xxFF@{j}")
    print(f"  {name}")
    print(f"    {h(v)}  0x{sg[0]:04x}   0x{sg[1]:04x}   0x{sg[2]:04x}   0x{sg[3]:04x}   "
          + (", ".join(marks) if marks else "(无 ff 沾染——零塌缩)"))

print("""
  谱系结论：
  - 案22 (9226e000 ffff a4bd)：0xffff 完整标签出现在 [31:16] 段；
  - 案23 (ffa9..e000ff)：0xff 前缀钉在 [63:56]，0xff 尾缀落在 [15:8]；
  - 案24 (00ffff b8..)：0xffff 标签迁移到 [47:32]，且 [63:48] 残留 00ff 半标签；
  - 案25：全零塌缩（对照项，无标签保留）。
  同日 3.45h 内 4 崩（14:31→17:58），同一 0xff/0xffff 沾染模式在不同
  16 位段之间迁移，唯一自然解释是装载返回通路（L1D 出口→bypass/移位
  网络→RF 写口）的 lane 选通错位：数据未变，『哪个字节进哪个槽』错了
  ——固定坏位无法产生这种段间迁移。
  案24 的 00ff|ffff 双段形态是迄今最直接的『标签跨段错位』活体样本：
  真值高 16 位 0xffff 的一半(00ff)留在顶段，另一半(ff)已溢出到次高段。""")

# ---------------------------------------------------------------
print("=" * 78)
print("六、最终闭合判定汇总")
print("=" * 78)
ok1 = (s == x27)
ok2 = (f2 == FAR)
print(f"  (1) x27 = x1 + x20            : {'闭合' if ok1 else '不闭合'}")
print(f"  (2) FAR = x27 + 0x120         : {'闭合' if ok2 else '不闭合'}")
print(f"  (3) x25 = 50 → __per_cpu_offset[50]（跨槽：CPU179 读 CPU50 的槽，调度域遍历正常行为）")
print(f"  (4) x23 = 0x400 未见使用异常（致命装载目标寄存器，值未落地）")
print(f"  (5) x20 低 12 位 = 0x240 ≠ 0：percpu 偏移 4K 页对齐不变式被破坏【实锤】")
print(f"  (6) x20[63:48] = 0x00ff ≠ 0xffff：canonical 标签错位【实锤】")
print()
print("  推理链：x20 装载返回坏值 → add（纯正确指令）传播 → ldr 以坏 x27 寻址 →")
print("          FAR 非法 → L0 translation fault → Oops。除 x20 装载本身外，")
print("          每一步均被代数闭合验证为正确执行。")
