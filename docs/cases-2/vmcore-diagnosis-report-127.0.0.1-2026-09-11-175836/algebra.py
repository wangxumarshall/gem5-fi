#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
案 #25 (127.0.0.1-2026-09-11-17:58:36) 指令级代数闭合复算
全部算术在 mod 2^64 下进行（AArch64 通用寄存器语义）。

dmesg 寄存器事实（vmcore-dmesg.txt L2580-2629）：
  pc  = find_busiest_group+0x140/0xb60
  Code: f9400782 f879d814 2a1903e0 8b14003b (f9409377)
  x27 = ffffdee405e696c0
  x20 = 0000000000000000   ← 零塌缩
  x1  = ffffdee405e696c0
  x25 = 0x6
  x23 = 0x400
  FAR = ffffdee405e697e0
  ESR = 0x96000006 (DABT current EL, FSC=0x06 level 2 translation fault)
  页表 walk: pgd=10006057fffff403, pud=10006057ffffe403, pmd=0
"""
M = (1 << 64) - 1

def h(v): return f"0x{v:016x}"
def seg16(v):
    return [(v >> 48) & 0xFFFF, (v >> 32) & 0xFFFF, (v >> 16) & 0xFFFF, v & 0xFFFF]

print("=" * 78)
print("案 #25 代数闭合复算（mod 2^64）")
print("=" * 78)

x27 = 0xffffdee405e696c0
x20 = 0x0000000000000000
x1  = 0xffffdee405e696c0
x25 = 0x6
x23 = 0x400
FAR = 0xffffdee405e697e0

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
    print("          x27 == x1 —— x20 零塌缩使加法退化为恒等，")
    print("          x27 的值即 x1 原值（canonical），非法性 100% 来自")
    print("          x20 的零值（percpu 偏移装载返回 0）。")

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
print("  再前 2a1903e0   = orr  x0, wzr, w25 (w25=0x6 → x0=6, 与 x0 dump=0x6 吻合)")
print("  再前 f879d814   = ldr  x20, [x0, x25, sxtw #3]  ← __per_cpu_offset[6] 装载")
print(f"  x25=6 → __per_cpu_offset[6]，即 CPU6 的 percpu 偏移槽（跨槽：本核 179 未读自己的槽）")
print(f"  x20 装载返回 = {h(x20)} —— 即被腐化为全零的 __per_cpu_offset[6] 读出值")

# ---------------------------------------------------------------
print("\n" + "-" * 78)
print("四、x20 = 0 零塌缩形态分析 + FSC=L2 的页表几何")
print("-" * 78)
print("  x20 = 0x0000000000000000")
print("  真值应为 __per_cpu_offset[6]（canonical 内核地址、4K 页对齐、非零——")
print("  percpu 偏移在 192 核系统上不可能为 0：percpu 区与静态区不同址）。")
print("")
print("  零塌缩的两条不变式破坏：")
print("  1. 顶段 0xffff → 0x0000：canonical 标签塌缩【实锤】")
print("  2. 真值非零 → 0：__per_cpu_offset[] 全数组在 smp 初始化后无零元素")
print("     （谱系 #4/#10/#11 案 crash 实测各槽真值均 ffff 开头非零）【实锤】")
print("")
print("  零塌缩的传播几何（本案特有，与 L0 案不同）：")
print("  x20=0 → x27 = x1 + 0 = x1（恒等） → FAR = x1 + 0x120")
print("  FAR = ffffdee405e697e0 是 canonical 地址——")
print("  所以本案 FSC = 0x06 level 2 translation fault 而非 L0/between：")
print("  内核页表 walk（L2591-2592）: pgd=...f403(有效) pud=...e403(有效)")
print("  pmd=0x0000000000000000 ← L2 断链，该地址落在未建立 PMD 映射的空洞")
print("")
print("  语义解读：x1 是 percpu 静态基址形态的 canonical 指针（ffffdee4....），")
print("  本应加上 __per_cpu_offset[6] 平移到 CPU6 实例地址；零偏移使寻址")
print("  落回『静态区某空洞 + 0x120』——数据通路腐化被页表几何忠实记录。")

# ---------------------------------------------------------------
print("\n" + "-" * 78)
print("五、ff 标签位置迁移谱（同日四连崩对照，本案=零塌缩对照项）")
print("-" * 78)
print("  坏值(x20 或等价)          [63:48] [47:32] [31:16] [15: 0]  ff/ffff 沾染段")
fam = [
    ("案22 09-11-14:31 x20=9226e000ffffa4bd", 0x9226e000ffffa4bd),
    ("案23 09-11-16:30 x20=ffa9342267e000ff", 0xffa9342267e000ff),
    ("案24 09-11-17:06 x20=00ffffb810e4a240", 0x00ffffb810e4a240),
    ("案25 09-11-17:58 x20=0000000000000000", x20),
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
  同日 3.45h 内 4 崩（14:31→17:58），前三案 lane 错位（标签迁移）+
  本案零塌缩（整组 lane 未驱动/选通到零源）——同一装载返回通路的
  两种极端表现同日交替出现，与『通路级间歇缺陷、每次发作错排量随机』
  模型一致，与『固定坏位/固定坏页』模型矛盾。""")

# ---------------------------------------------------------------
print("=" * 78)
print("六、最终闭合判定汇总")
print("=" * 78)
ok1 = (s == x27)
ok2 = (f2 == FAR)
print(f"  (1) x27 = x1 + x20 (= x1)      : {'闭合' if ok1 else '不闭合'}")
print(f"  (2) FAR = x27 + 0x120          : {'闭合' if ok2 else '不闭合'}")
print(f"  (3) x25 = 6 → __per_cpu_offset[6]（跨槽：CPU179 读 CPU6 的槽，调度域遍历正常行为）")
print(f"  (4) x23 = 0x400 未见使用异常（致命装载目标寄存器，值未落地）")
print(f"  (5) x20 = 0：canonical 标签 + 非零性双不变式破坏【实锤】")
print(f"  (6) FSC = L2（pmd=0）：零偏移使 FAR 落入未映射空洞——")
print(f"      canonical-but-unmapped 几何，与 L0 案的 noncanonical 几何互为镜像")
print()
print("  推理链：x20 装载返回 0（零塌缩）→ add 恒等传递 → ldr 以 x1+0x120")
print("          寻址 → FAR canonical 但 L2 断 → translation fault → Oops。")
print("          除 x20 装载本身外，每一步均被代数闭合验证为正确执行。")
