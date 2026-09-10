#!/usr/bin/env python3
"""案19（第19次致命转储 127.0.0.1-2026-09-07-15:16:31）代数复算
vmcore 文件缺失（kdump 未保存），所有寄存器值取自 vmcore-dmesg.txt 崩溃块原文；
内存真值对照不可执行，x20 撕裂窗口形态判定为【强推】。
"""
M = 1 << 64

# ── 崩溃块实测（dmesg L2590 起）──
x1  = 0xffffa3e0121e96c0   # ldr x1,[x19,#56] → &runqueues（模板，语义由 KASLR 不变式锁定）
x20 = 0xffdc206dfa4000ff   # ldr x20,[x0,w25,sxtw#3] 实收（撕裂形态）
x27 = 0xffdbc44e0c5e97bf   # add x27,x1,x20
FAR = 0xffdbc44e0c5e98df   # ldr x23,[x27,#0x120] 的故障地址
x25 = 0xa1                 # 迭代号 i = 161
x9  = 0xffffa3e0107bae58
x21 = 0xffffa3e0125dfcb0
x24 = 0xffffa3e0125e5000
x23 = 0x400
x22 = x26 = 0xffff604003ed3ea0

def chk(name, ok):
    print(("PASS " if ok else "FAIL ") + name)

print("== 案19 寄存器代数闭合 ==")
chk("x27 == x1 + x20 (mod 2^64)", x27 == (x1 + x20) % M)
chk("FAR == x27 + 0x120", FAR == (x27 + 0x120) % M)
chk("x25 == 161（迭代 CPU 161 ≠ 执行核 179）", x25 == 161)
chk("FAR 非规范（0xffdb… 高位不在内核地址形态）", not (0xffff000000000000 <= FAR < 0x10000000000000000))

print("\n== KASLR 不变式（跨开机指纹，对齐 12 案 census §2.8）==")
chk("x9 - x1 == 0xfffffffffe5d1798", (x9 - x1) % M == 0xfffffffffe5d1798)
chk("x21 - x1 == 0x3f65f0", (x21 - x1) % M == 0x3f65f0)
chk("x24 - x21 == 0x5350", (x24 - x21) % M == 0x5350)
chk("x9 低 16 位 == ae58（fbG+0x150 页内偏移）", (x9 & 0xffff) == 0xae58)
chk("x23 == 0x400（前次迭代 load_avg 残留）", x23 == 0x400)
chk("x22 == x26（sd/sched_group 相关指针一致）", x22 == x26)

print("\n== x20 撕裂形态分析（无 vmcore，形态学【强推】）==")
print(f"x20 = 0x{x20:016x}")
for shift in range(1, 8):
    rol = ((x20 << (8 * shift)) | (x20 >> (64 - 8 * shift))) % M
    print(f"ROL{shift}B(x20) = 0x{rol:016x}")
print()
# 既往已证撕裂族形态：x20 = __per_cpu_offset 字节流在 +1/+2/+5 字节相位的非对齐窗口。
# 数组槽形如 ffffAABBCCCDe000（小端字节序 ...e0 00 cd cc bb aa ff ff）。
# x20 小端字节流 = ff 00 40 fa 6d 20 dc ff：
#   相邻窗口特征 —— 低字节 ff 是上一槽最高字节，随后 00 40 fa 6d 20 dc 是本槽低 6 字节，
#   高两字节 ff dc?? —— 注意案19 数组真值不可测，无法做窗口直读比对（区别于第 7/8/9 案【实锤】）。
# 与既往形态对照：
#   第 2/5 案 ≫8 形态高 3 字节 = 00 ff ff；本案高 3 字节（大端）= ff dc 20，是第 9 案
#   （2cd7ddf3a9089790）之后第二个"非规范大值"形态——更接近跨槽窗口的原样字节流。
print("形态判定：x20 为 __per_cpu_offset 字节流跨槽非对齐窗口（【强推】，无法窗口直读验证）")
print("对照：第 2/5 案 ≫8 形态（高3字节 00ffff）vs 本案 ff dc 20 跨槽原样窗口（近第 9 案非规范大值形态）")

print("\n== 反事实（不可验证声明）==")
print("vmcore 文件缺失：x27_true = &runqueues + off[161] 与 off[161] 真值均无法读出，")
print("反事实 vtop 不可执行（区别于案 18 的三重闭合）。撕裂窗口直读比对不可执行（区别于第 7/8/9 案）。")
print("子族归类依据：x20 非零非全零 + 非规范 FAR + x27=x1+x20 闭合 + L0 FSC —— 与撕裂移位族")
print("第 1/2/5/7/8/9 案全部几何特征吻合，唯缺内存真值比对，故降级【强推】。")
