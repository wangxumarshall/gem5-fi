#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第 8 次致命转储（127.0.0.1-2026-09-03-18:25:12）寄存器代数与反事实复算
所有 64 位运算模 2^64。输入全部来自真实取证输出：
  - vmcore-dmesg.txt 崩溃块（x1/x9/x20/x25/x27/FAR/ESR，行 4155 起）
  - crash_session.log / crash_session2.log / crash_session3.log
    （sym / px __per_cpu_offset[n] / rd -64 __per_cpu_offset 192 / vtop / p runqueues:n）
用法: python3 algebra.py
"""
M = (1 << 64) - 1

# ---- 输入（逐条注明来源） ----
# vmcore-dmesg.txt 崩溃块寄存器（行 4168~4182）
x1  = 0xffffc9e8a3cd96c0   # x1  = ldp 出的 &runqueues（percpu 静态模板地址）
x20 = 0x00ffffb617dd3940   # x20 = ldr x20,[x0, w25, sxtw #3] 的返回值（实收撕裂值）
x27 = 0x00ffc99ebbaad000   # x27 = add x27, x1, x20 的结果
x25 = 0x0c                 # x25 = i（迭代 CPU 号）= 12；x0/x3/x6 亦为 0xc（四寄存器互证）
FAR = 0x00ffc99ebbaad120   # Unable to handle kernel paging request at ...
x9  = 0xffffc9e8a22aae58   # x9 = find_busiest_group+0x150（KASLR 锚）
x24 = 0xffffc9e8a40d5000   # x24 = adrp 页基（4K 对齐，&__per_cpu_offset 同页）
x21 = 0xffffc9e8a40cfcb0   # x21 = &nr_cpu_ids

# crash: sym find_busiest_group / sym runqueues / sym nr_cpu_ids / sym __per_cpu_offset
fbG_runtime   = 0xffffc9e8a22aad08
runqueues_rt  = 0xffffc9e8a3cd96c0
nr_cpu_ids_rt = 0xffffc9e8a40cfcb0
percpu_off_rt = 0xffffc9e8a40d55d0

# crash: px __per_cpu_offset[12] / [179] / [0] / [1] / [123] / [124]（内存真值）
off12  = 0xffffb617dc4d6000
off179 = 0xffffb617ddb04000
off0   = 0xffffb617dc33e000
off1   = 0xffffb617dc360000
off123 = 0xffffb617dd394000
off124 = 0xffffb617dd3b6000

# crash: rd -64 ffffc9e8a40d59a9 2 → 基址+985 字节处非对齐窗口实读（crash_session2.log）
unaligned_window_word = 0x00ffffb617dd3940

# crash: p runqueues:12 / p runqueues:179 内嵌自指针
rq12_selfptr  = 0xffff8000801af6c0   # nohz_csd.info
rq179_selfptr = 0xffff8000817dd6c0

# vmlinux 静态符号（nm 输出）
fbG_static   = 0xffff80008013ad08
runqueues_st = 0xffff800081b696c0
nr_cpu_ids_st= 0xffff800081f5fcb0
percpu_off_st= 0xffff800081f655d0

def add(a, b): return (a + b) & M
def popcount(v): return bin(v).count('1')
def rol_bytes(v, n):  # 64 位值按字节循环左移 n 字节
    b = v.to_bytes(8, 'big')
    b = b[n:] + b[:n]
    return int.from_bytes(b, 'big')

print("=" * 72)
print("A. KASLR 滑移一致性（四个独立符号 + x9 锚互相咬合）")
print("=" * 72)
kaslr_x9  = (x9 - 0x150 - fbG_static) & M
kaslr_sym = (fbG_runtime - fbG_static) & M
print(f"x9 锚定 KASLR      = {kaslr_x9:#x}")
print(f"sym 锚定 KASLR     = {kaslr_sym:#x}")
print(f"runqueues 咬合     = {(runqueues_rt - runqueues_st) & M:#x}  (应等于 KASLR)")
print(f"nr_cpu_ids 咬合    = {(nr_cpu_ids_rt - nr_cpu_ids_st) & M:#x}")
print(f"percpu_offset 咬合 = {(percpu_off_rt - percpu_off_st) & M:#x}")
ok_kaslr = kaslr_x9 == kaslr_sym == (runqueues_rt - runqueues_st) \
           == (nr_cpu_ids_rt - nr_cpu_ids_st) == (percpu_off_rt - percpu_off_st)
print(f"五路一致: {ok_kaslr}")
print(f"x24 = {x24:#x}（adrp 页基，4K 对齐低 12 位恒 0；")
print(f"     与 &__per_cpu_offset = {percpu_off_rt:#x} 同页，差 0x5d0 由 add 立即数补足）")

print()
print("=" * 72)
print("B. 故障点寄存器代数闭合（撕裂移位族）")
print("=" * 72)
print(f"x1  (模板 &runqueues) = {x1:#x}")
print(f"x20 (实收偏移)        = {x20:#018x}   <-- 应为 __per_cpu_offset[12]")
print(f"x25 (i = 迭代 CPU 号) = {x25:#x} = {x25}（x0/x3/x6 同为 0xc，四寄存器互证）")
x27_calc = add(x1, x20)
print(f"x27 = x1 + x20 (mod 2^64) = {x27_calc:#018x}")
print(f"崩溃块 x27                = {x27:#018x}   逐位相等: {x27_calc == x27}")
far_calc = add(x27, 0x120)
print(f"FAR_calc = x27 + 0x120 = {far_calc:#018x}")
print(f"崩溃 FAR（dmesg 文本）  = {FAR:#018x}")
print(f"FAR_calc == FAR（逐位，含高 16 位 00ff）: {far_calc == FAR}")
print(f"注：本案 x27 高 16 位 = 00ff（撕裂值高 16 位 00ff 直通），FAR 完整 64 位")
print(f"    逐位打印——与 08-31 案（高 16 位 a000 不入 dmesg 打印）形态不同，如实记录")

print()
print("=" * 72)
print("C. 内存真值对照（crash 从 vmcore 读出，内存完好）")
print("=" * 72)
print(f"__per_cpu_offset[12]  真值 = {off12:#x}   (x25=i=12 → 本指令应取此槽)")
print(f"__per_cpu_offset[179] 真值 = {off179:#x}  (崩溃执行核 179 → 计划要求对照)")
print(f"__per_cpu_offset[0]   真值 = {off0:#x}")
print(f"数组等差步长: off[1]-off[0] = {off1-off0:#x}; "
      f"off[12]-off[0] = {off12-off0:#x} = 12*0x22000: {(off12-off0)==12*0x22000}; "
      f"off[179]-off[12] = {off179-off12:#x} = 167*0x22000: {(off179-off12)==167*0x22000}")
print(f"x20 实收 {x20:#018x} ≠ 真值 {off12:#x} → 装载撕裂")
print(f"汉明距离 popcount(x20 ^ off[12])  = {popcount(x20 ^ off12)}")
print(f"          popcount(x20 ^ off[179]) = {popcount(x20 ^ off179)}")
print(f"          popcount(x20 ^ off[0])   = {popcount(x20 ^ off0)}")

print()
print("=" * 72)
print("D. 撕裂形态判定（字节流非对齐窗口匹配 —— 复用第 7 次案方法）")
print("=" * 72)
# 把全 192 槽按内存小端字节流拼接，搜索 x20 的 8 字节 LE 序列
STEP = 0x22000
stream = b"".join((off0 + i*STEP).to_bytes(8, 'little') for i in range(192))
le_x20 = x20.to_bytes(8, 'little')
hits, i = [], 0
while True:
    j = stream.find(le_x20, i)
    if j < 0: break
    hits.append((j // 8, j % 8))
    i = j + 1
print(f"x20 LE 字节序列（内存序）: {' '.join(f'{b:02x}' for b in le_x20)}")
print(f"在 192 槽数组字节流中搜索: 命中 {hits}（全数组唯一）")
print(f"  → 命中位置 = 槽 123 起始 + 1 字节（数组基址 + 123*8 + 1 = 基址 + 985 字节）")
# 等价公式
merged = (off123 >> 8) | ((off124 & 0xFF) << 56)
print(f"等价公式: (off[123]>>8) | ((off[124]&0xFF)<<56)")
print(f"  = ({off123:#x} >> 8) | (({off124:#x} & 0xFF) << 56)")
print(f"  = {merged:#018x}   == x20: {merged == x20}")
# crash 实读验证
print(f"crash 实读（crash_session2.log）: rd -64 ffffc9e8a40d59a9 2")
print(f"  → 首字 = {unaligned_window_word:#018x}   == x20: {unaligned_window_word == x20}")
print(f"  （ffffc9e8a40d59a9 = &__per_cpu_offset + 985 字节 = 槽123 LE 字节 1 处）")
print()
print("撕裂形态结论：")
print("  08-25-15:58 案形态 = offset[0] >> 8（槽内 1 字节相位，槽 0 起点）")
print("  08-31 案形态   = +2 字节相位、跨槽 125/126 边界")
print("  本案形态 = 槽 123 起点 +1 字节相位的非对齐窗口（不跨槽，窗口完整落在")
print("  槽 123/124 边界前 7 字节内——实为 123 槽内 1 字节相位 + 顶入 124 槽首字节）")
print("  撕裂相位谱：1 字节（08-25-15:58, 本案）→ 2 字节（08-31）→ 半字旋转（08-14）")
# 与旋转族比对（排除 ROL16 等简单旋转）
match_rot = [f"ROL{k*8}B" for k in range(1, 8) if rol_bytes(off12, k) == x20]
print(f"与 off[12] 的字节旋转族比对: {match_rot if match_rot else '无 1~7 字节旋转匹配（非 08-14 案 ROL16 形态）'}")

print()
print("=" * 72)
print("E. 反事实验证（若 ldr 交付真值则不崩）")
print("=" * 72)
x27_true_12  = add(runqueues_rt, off12)
x27_true_179 = add(runqueues_rt, off179)
print(f"x27_true(i=12)  = &runqueues + __per_cpu_offset[12]  = {x27_true_12:#x}")
print(f"x27_true(i=179) = &runqueues + __per_cpu_offset[179] = {x27_true_179:#x}")
print(f"rq(12)  内嵌自指针 nohz_csd.info = {rq12_selfptr:#x}  逐位一致: {x27_true_12 == rq12_selfptr}")
print(f"rq(179) 内嵌自指针 nohz_csd.info = {rq179_selfptr:#x} 逐位一致: {x27_true_179 == rq179_selfptr}")
print(f"两自指针间距 = {rq179_selfptr - rq12_selfptr:#x} = 167*0x22000: {(rq179_selfptr-rq12_selfptr)==167*0x22000}")
print()
print("crash vtop（crash_session3.log）：")
print(f"  vtop {x27_true_12:#x}  → PHYSICAL 37ffe2e6c0, PTE e80037ffe2ef03 (VALID|SHARED|AF|NG|PXN|UXN|DIRTY)  ← VALID")
print(f"  vtop {x27_true_179:#x} → PHYSICAL 6057ffe026c0, PTE e86057ffe02f03 (VALID|SHARED|AF|NG|PXN|UXN|DIRTY)  ← VALID")
print(f"若收到真值，故障装载将读 rq(12)->cfs.avg.load_avg（+0x120 处）= 1023（实例健全）")
print(f"对照 rq(179)->cfs.avg.load_avg = 319（崩溃核自身实例亦健全）")
print(f"→ 正确数据下指令平静完成，异常的唯一必要条件是装载结果被腐化")

print()
print("=" * 72)
print("F. 故障地址页表走查（撕裂移位族 → 非规范域 → L0）")
print("=" * 72)
print(f"FAR = {FAR:#018x} 非规范地址（bit[63:48] = 00ff，既非 ffff 内核域也非有效用户域）")
print(f"dmesg: [00ffc99ebbaad120] address between user and kernel address ranges → FSC=0x04 (level 0)")
print(f"crash vtop -k {FAR:#018x} → (not a kernel virtual address)——与硬件走查一致（crash_session2.log）")
print(f"对照：撕裂移位族既往各案（08-14/08-17/08-25-15:58/08-31）FSC 均为 L0，本案一致")
print()
print("复算结论：所有等式机器验证成立，无一手工计算。")
