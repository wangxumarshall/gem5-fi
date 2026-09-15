#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
案 #21 (127.0.0.1-2026-09-08-17:21:33) mod 2^64 代数闭合 + 坏值形态位级分析
数据源: vmcore-dmesg.txt 行号级摘录(见 dmesg_forensics.txt)
运行: python3 algebra.py | tee algebra_out.txt
"""
M = 1 << 64

# ---- 寄存器现场(dmesg 行 2741/2743/2744/2750) ----
x1  = 0xffffac1530ea96c0   # 行2750: sg 或 percpu 变量基址(内核规范地址)
x20 = 0xd3eb5026e000ffff   # 行2744: __per_cpu_offset[54] 装载返回坏值
x27 = 0xd3eafc3c10eb96bf   # 行2741: add x27,x1,x20 结果
FAR = 0xd3eafc3c10eb97df   # 行2720: ldr x23,[x27,#288] 缺页地址
x25 = 0x36                 # 行2742: w25=54 (CPU54 的 percpu 槽位)
x0  = 0x36                 # 行2750
x3_precursor = 0xffffd3eb50934000  # 行2603/2649/2694: 三次前兆块中 x3 恒定值

print('=' * 72)
print('一、加法代数闭合 (mod 2^64)')
print('=' * 72)

s = (x1 + x20) % M
print(f'x1          = {x1:016x}   (dmesg 行2750)')
print(f'x20         = {x20:016x}   (dmesg 行2744)')
print(f'x1 + x20    = {s:016x}   (mod 2^64)')
print(f'x27 (寄存器)= {x27:016x}   (dmesg 行2741)')
print(f'判定: x27 == x1 + x20  ->  {s == x27}')
print()

t = (x27 + 0x120) % M
print(f'x27 + 0x120 = {t:016x}   (mod 2^64; 0x120 = 288 = cfs.avg 载荷偏移十进制)')
print(f'FAR (缺页)  = {FAR:016x}   (dmesg 行2720)')
print(f'判定: FAR == x27 + 0x120 ->  {t == FAR}')
print()
print('结论: 两级加法逐位闭合。x27 与 FAR 均由 x20 坏值纯算术派生,')
print('      加法器/有效地址生成无错;唯一异常源 = x20 装载返回值。')

print()
print('=' * 72)
print('二、指令级复核 (Code: f9400782 f879d814 2a1903e0 8b14003b (f9409377))')
print('=' * 72)
print('pc-0x10  f9400782 : ldr  x2, [x28]           — 前序指令(上下文)')
print('pc-0x0c  f879d814 : ldr  x20, [x0, w25, sxtw #3]  — 装载 __per_cpu_offset[54]')
print('pc-0x08  2a1903e0 : mov  w0, w25             — w0 = 54')
print('pc-0x04  8b14003b : add  x27, x1, x20        — 基址+percpu 偏移')
print('pc       f9409377 : ldr  x23, [x27, #288]    — 读 rq->cfs.avg 相关,触发 L0 fault')
print()

print('=' * 72)
print('三、x20 坏值形态位级分析')
print('=' * 72)
print(f'x20 = {x20:016x}')
print(f'16bit 段分解: [63:48]=d3eb  [47:32]=5026  [31:16]=e000  [15:0]=ffff')
print(f'字节分解   : d3 eb 50 26 e0 00 ff ff  (byte7..byte0)')
print()

print('--- 3.1 与真值形态(percpu 偏移 = 0xffff....xxx000,页对齐)对照 ---')
truth_form_examples = {
    '谱系#4 真值(08-25-15:42)': 0xffffda55e61ce000,
    '谱系#6 真值(08-26-10:37)': 0xffffdd6d7fa64000,
    '谱系#10 真值(09-04-10:27)': 0xffffa6616d8f8000,
    '谱系#11 真值(09-04-11:00)': 0xffffa89017090000,
}
for name, tv in truth_form_examples.items():
    print(f'  {name}: {tv:016x}  汉明距离(x20)={bin(x20 ^ tv).count("1")}')
print()
print('  真值形态约束(形态学,本案无 vmcore 不可直接对照——降级声明):')
print('    a) 高 16 位 = 0xffff (内核线性映射/pcpu 区域形态)')
print('    b) 低 13~16 位 = 0 (单位 pcpu chunk 页对齐)')
print('  x20 违反 a):高 16 位 = d3eb (非全 1,高位塌缩)')
print('  x20 违反 b):低 16 位 = ffff (非页对齐,0xff 全 1 沾染标签)')
print()

print('--- 3.2 高位段与 FAR/前兆 x3 的形态关联 ---')
print(f'x20 高16位 d3eb vs FAR 高16位 d3ea: 汉明距离 = {bin(0xd3eb ^ 0xd3ea).count("1")} (d3eb^d3ea=0x0001)')
print(f'x3(三次前兆块恒定) = {x3_precursor:016x}')
print(f'  x3 段分解: [63:48]=ffff  [47:32]=d3eb  [31:16]=5093  [15:0]=4000')
print(f'  x3 恰为 CPU179 本地 percpu 区形态: ffff 开头 + 50934000 页对齐尾')
print(f'  注意: x3 的 [47:32] 段 = d3eb,与 x20 高16位完全一致!')
print()

print('--- 3.3 rol16(前兆 x3) 假设检验 ---')
rol16_x3 = ((x3_precursor << 16) % M) | (x3_precursor >> 48)
print(f'x3  rol16  = {rol16_x3:016x}')
print(f'x20       = {x20:016x}')
print(f'XOR       = {x20 ^ rol16_x3:016x}')
hd = bin(x20 ^ rol16_x3).count('1')
print(f'汉明距离  = {hd} / 64 位 (仅 {hd} 位差异!)')
print('  段级差异:')
for i in range(4):
    a = (rol16_x3 >> (16 * i)) & 0xffff
    b = (x20 >> (16 * i)) & 0xffff
    print(f'    段[15+{16*i}:{16*i}]  rol16(x3)={a:04x}  x20={b:04x}  xor={a^b:04x}  hd={bin(a^b).count("1")}')
print()
print('  判读:x20 ≈ rol16(x3) + 7bit 低位差异 —— 若 x20 是某次真实装载,')
print('  则其形态 = "16bit lane 循环左移 1 段 + 段内少量翻转" 的结构化重组,')
print('  与 SYNTHESIS 谱系 #1(16bit lane 循环错位) / #7(ror16+0xa000 顶标签)')
print('  同属 lane 错位族,而非随机位翻转。')

print()
print('=' * 72)
print('四、末次前兆 → 致命间隔精确计算')
print('=' * 72)
t_fatal = 76274.523293   # 行2720 Unable to handle ...
t_p3    = 75523.625474   # 行2676 第3次 spurious
t_p2    = 74796.054873   # 行2631 第2次
t_p1    = 74323.653548   # 行2585 第1次
d3 = t_fatal - t_p3
print(f'致命时刻   = {t_fatal:.6f} s (行2720)')
print(f'前兆#3     = {t_p3:.6f} s (行2676)')
print(f'前兆#3 → 致命间隔 = {d3:.6f} s = {d3/60:.4f} min = {d3/3600:.6f} h')
print(f'前兆#1 → #2 间隔 = {t_p2-t_p1:.6f} s = {(t_p2-t_p1)/60:.2f} min')
print(f'前兆#2 → #3 间隔 = {t_p3-t_p2:.6f} s = {(t_p3-t_p2)/60:.2f} min')
print(f'前兆#1 → 致命  = {t_fatal-t_p1:.6f} s = {(t_fatal-t_p1)/3600:.2f} h')

print()
print('=' * 72)
print('五、前兆地址形态')
print('=' * 72)
precs = [0xffff604004d01102, 0xffff604005ce047c, 0xffff604005ce6450]
for i, p in enumerate(precs, 1):
    print(f'  前兆#{i}: {p:016x}')
print('  高 32 位全部 = ffff6040 (Node7 vmalloc/pcpu 段聚集);')
print('  低 32 位: 04d01102 / 05ce047c / 05ce6450 —— 相互分散(非同一地址反复);')
print('  #2 与 #3 低段前缀 05ce 相同(同一 64KB 邻域,相隔 0x5fd4)。')

print()
print('=' * 72)
print('六、总结(代数与形态)')
print('=' * 72)
print('1.【实锤】x27 = x1 + x20 (mod 2^64) 逐位闭合 → add 指令与操作数传递无错。')
print('2.【实锤】FAR = x27 + 0x120 (mod 2^64) 逐位闭合 → 缺页地址为 x20 坏值的')
print('   纯算术结果;致命链条唯一注入点 = ldr x20,[x0,w25,sxtw#3] 装载返回。')
print('3.【实锤】x20 形态 = 高段塌缩(ffff→d3eb) + 低16位 0xffff 全1标签;')
print('   非 percpu 偏移合法形态(高16应 ffff、低13~16应页对齐 0)。')
print('4.【强推】x20 与三次前兆块恒定 x3(ffffd3eb50934000,CPU179 本地 percpu 区)')
print('   呈 rol16 关系(仅 7/64 位差异)——16bit lane 错位族形态学指纹,')
print('   归并谱系 lane 错位族(#1/#5/#7),其中 #7(ror16+0xa000 顶标签)最相似。')
print('5. 本案无 vmcore 文件,__per_cpu_offset[54] 内存真值不可对照(降级声明):')
print('   真值完好性结论由谱系 10/12 案先例 + 加法闭合间接支撑,非本案直接实证。')
