# ARM64 CPU 微架构 × SDC 敏感性对比研究
---

## 1. 基本信息

| | Kunpeng 920 | 920f | Neoverse N1 | Neoverse N2 | Neoverse N3 |
|---|---|---|---|---|---|
| 厂商/系列 | HiSilicon | HiSilicon | Arm Neoverse | Arm Neoverse | Arm Neoverse |
| 微架构名 | TaiShan v110 | part 0xd22（"72F5"） | Neoverse N1 | Neoverse N2 | Neoverse N3 |
| 架构版本 | ARMv8.2-A | ARMv8（SVE2/SME2） | ARMv8.2-A | Armv9.0-A（含v8.5特性） | Armv9.2-A（含v8.7特性） |
| MIDR part | 0xd01 (0x481fd010) | 0xd22 (0x480fd220) | — | — | — |
| 定位 | 数据中心 | HPC/超算核 | 高性能基础设施核 | 高性能/平衡核 | 平衡性能、低功耗、面积受限核 |
| 流水线 | 4-wide OoO，~8 级，PRF 后端 | 未知（SVE512 双 FMA 实测） | 超标量变长 OoO | 超标量 OoO（TRM 未公开宽度） | 超标量 OoO（TRM 未公开宽度） |
| 簇/共享单元 | 4 核 CCL 共享 L3 tag；SCCL=die | 38 核/NUMA 节点（节点即调度域） | DSU 簇（≤4 核 + L3 可选） | DSU-110 簇 | DSU-120（Direct connect 单核配置无 L3/SCU） |
| 内存/页 | DDR4-2933 8通道；4KB页大小；64KB 为 ARMv8.2 架构必备；16KB 未验证（MMFR0 相应字段固件不可读，见源文档可信度警告） | 565GB；**64KB**（TGran4=0xf） | 48-bit PA | 48-bit PA（4/16/64KB granule） | 48-bit VA/PA |
| ISA 边界要点 | 无 SVE/PAC/BTI/LRCPC/AArch32；有 LSE | SVE512+SME2+SHA3/SM3/SM4+LRCPC2/3；BTI=0,MTE=0 | AArch32 EL0；LDAPR(v8.3) | SVE/SVE2 128b；AArch32+AArch64 | 仅 A64；SVE/SVE2 128b|
| 主频（实测/典型） | 2.6 GHz 固定 | 2.0 GHz 定频 | ~2.6-3.1 GHz（公开资料） | ~2.4-3.0 GHz（公开资料） | ~2.4-3.0 GHz（公开资料） |

---

## 1.5 各芯片微架构功能图（★ = 独有/标志性设计）

以下五张图采用统一泳道格式（前端按序 / 后端乱序 / 内存层级+MMU，外加 RAS 横幅），
**金粗边框（★）标记该芯片在本组五款中独有或标志性的设计**，红色标记 SDC 高危部件/通路，
灰虚线框（920f）表示黑盒未公开。图内数字均与本文各节表格同源，可交叉验证。

> 嵌入格式说明：本文直接将五张 **SVG（矢量）** 内嵌到 markdown 中，中文字形由
> SVG 内 `font-family` 回退到系统/浏览器端渲染，字体内聚、无栅格化乱码；
> PNG 栅格件与对应 `.svg` 源文件仍保留在 `figures/` 下供离线下载（
> `sdc-fig-<chip>.png` / `.svg`）。

### Kunpeng 920

<div align="center">

<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1480 1400" width="1480" height="1400" font-family="system-ui,'PingFang SC','Noto Sans CJK SC','Microsoft YaHei',sans-serif">
  <defs><marker id="arr" markerWidth="11" markerHeight="9" refX="9.5" refY="4.5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L11,4.5 L0,9 Z" fill="#5a6b7c"/></marker><marker id="arrC" markerWidth="11" markerHeight="9" refX="9.5" refY="4.5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L11,4.5 L0,9 Z" fill="#7c3aed"/></marker></defs>
  <rect x="0" y="0" width="1480" height="1400" fill="#ffffff"/>
  <text x="30" y="34" font-size="20" font-weight="700" fill="#1f2937">Kunpeng 920 · TaiShan v110 微架构功能图（ARMv8.2-A · 4 宽乱序 · 2.6GHz 实测）</text>
  <text x="30" y="56" font-size="12" fill="#6b7280">布局 = 920 实测结构：前端 4 宽无 uop-cache → 三类统一调度器 → chiplet 三模式 SLC。红=SDC 高危（无架构 RAS）· 数据出处：kunpeng920_microarchitecture.md 本机实测 + 公开资料</text>
  <rect x="30" y="72" width="1420" height="36" rx="6" fill="#f7f9fb" stroke="#c6d2dd"/>
    <line x1="46" y1="90" x2="72" y2="90" stroke="#5a6b7c" stroke-width="2" marker-end="url(#arr)"/>
    <text x="78" y="94" font-size="11.5" fill="#1f2937">指令/数据流</text>
    <line x1="201" y1="90" x2="227" y2="90" stroke="#7c3aed" stroke-width="2" stroke-dasharray="5,3" marker-end="url(#arrC)"/>
    <text x="233" y="94" font-size="11.5" fill="#1f2937">控制流</text>
    <rect x="313" y="83" width="14" height="14" fill="#fffbeb" stroke="#b45309" stroke-width="2.6"/>
    <text x="333" y="94" font-size="11.5" fill="#1f2937">独有/标志性</text>
    <rect x="456" y="83" width="14" height="14" fill="#f9fafb" stroke="#9ca3af" stroke-width="1.3" stroke-dasharray="4,3"/>
    <text x="476" y="94" font-size="11.5" fill="#1f2937">未公开/黑盒</text>
    <line x1="599" y1="90" x2="621" y2="90" stroke="#b91c1c" stroke-width="3.5"/>
    <text x="627" y="94" font-size="11.5" fill="#1f2937">SDC 高危/无保护</text>
  <rect x="30" y="130" width="1420" height="240" rx="10" fill="#eaf2fb" stroke="#a9c9ec" stroke-width="1.5"/>
  <rect x="30" y="106" width="190" height="24" rx="5" fill="#4a5f78"/>
  <text x="41" y="123.5" font-size="14" fill="#ffffff" font-weight="600">前端 Fetch（按序 · 4 宽）</text>
  <text x="236" y="123" font-size="11.5" fill="#4a5f78" font-style="italic">无 uop-cache → 取指带宽悬崖：L1I 内 4 条/cyc → L2 ~1.75 → L3/内存 ~0.25</text>
  <rect x="50" y="166" width="260" height="178" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="62" y="188" font-size="13.5" fill="#1f2937" text-anchor="start" font-weight="700">BPU 分支预测</text>
  <text x="62" y="208" font-size="10.5" fill="#1f2937" text-anchor="start">· BTB 两级：L1 64 项（taken 1c）</text>
  <text x="62" y="225" font-size="10.5" fill="#1f2937" text-anchor="start">· L2 BTB ~2048 项</text>
  <text x="62" y="242" font-size="10.5" fill="#1f2937" text-anchor="start">· 方向：两级动态（≈A73 水平）</text>
  <text x="62" y="259" font-size="10.5" fill="#1f2937" text-anchor="start">· RAS 31–32 · 间接 ~256 目标</text>
  <text x="62" y="276" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">· 无任何 ECC/parity 披露（无 PAC）</text>
  <text x="62" y="293" font-size="10.5" fill="#6b7280" text-anchor="start">· mcf MPKI 16.64（N1 为 15.03）</text>
  <rect x="50" y="366" width="260" height="0" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="180.0" y="388" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700"></text>
  <rect x="340" y="166" width="200" height="96" rx="7" fill="#fffbeb" stroke="#b45309" stroke-width="3"/>
  <text x="440.0" y="188" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">L1-I-cache 64KB 4-way</text>
  <text x="440.0" y="208" font-size="10.5" fill="#b45309" text-anchor="middle" font-weight="600">64B 行 · AIVIVT（L1Ip=2 实测）</text>
  <text x="440.0" y="225" font-size="10.5" fill="#b91c1c" text-anchor="middle" font-weight="600">厂商称 ECC（无架构化证据）</text>
  <rect x="340" y="276" width="200" height="68" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="440.0" y="298" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">取指+译码</text>
  <text x="440.0" y="318" font-size="10.5" fill="#1f2937" text-anchor="middle">4 条/周期 · 定长 32-bit</text>
  <text x="440.0" y="335" font-size="10.5" fill="#1f2937" text-anchor="middle">仅 AArch64（无 AArch32）</text>
  <path d="M300,250 L334,250" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <path d="M440,262 L440,272" fill="none" stroke="#7c3aed" stroke-width="1.6" marker-end="url(#arrC)"/>
  <text x="452" y="258" font-size="10" fill="#7c3aed" text-anchor="start">下一 PC</text>
  <rect x="570" y="166" width="250" height="178" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="582" y="188" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">Rename / Dispatch</text>
  <text x="582" y="208" font-size="10.5" fill="#1f2937" text-anchor="start">· PRF 式：31 GPR → INT ~128 物理寄存器</text>
  <text x="582" y="225" font-size="10.5" fill="#1f2937" text-anchor="start">· Flag 重命名 ~31 · move elimination</text>
  <text x="582" y="242" font-size="10.5" fill="#1f2937" text-anchor="start">· FP/向量 PRF 偏小（易压满）</text>
  <text x="582" y="259" font-size="10.5" fill="#1f2937" text-anchor="start">· 按类分流 → 三类统一式调度器</text>
  <text x="582" y="276" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">· PRF 翻转=直接 SDC（无保护披露）</text>
  <text x="582" y="293" font-size="10.5" fill="#6b7280" text-anchor="start">· squash 回滚依赖历史缓冲正确性</text>
  <path d="M540,250 L564,250" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <rect x="850" y="166" width="290" height="178" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="862" y="188" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">ISA 精确边界（ID 寄存器 EL0 实测）</text>
  <text x="862" y="208" font-size="10.5" fill="#1f2937" text-anchor="start">有：LSE 完整 · AES+PMULL · SHA1/256（无 512）</text>
  <text x="862" y="225" font-size="10.5" fill="#1f2937" text-anchor="start">　　CRC32 · UDOT/SDOT · FHM · JSCVT · FCMA</text>
  <text x="862" y="242" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">无：SVE · PAC · BTI · LRCPC · MTE · AArch32</text>
  <text x="862" y="259" font-size="10.5" fill="#1f2937" text-anchor="start">CTR：DIC=IDC=0（无 I/D 自动一致）· ERG=64B</text>
  <text x="862" y="276" font-size="10.5" fill="#6b7280" text-anchor="start">CASAL 实测 43c · NOP 0.26c ≈ 3.9 IPC</text>
  <text x="862" y="293" font-size="10.5" fill="#6b7280" text-anchor="start">MMFR0/DFR0 部分字段固件实现不全（已判可信边界）</text>
  <path d="M820,250 L844,250" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <rect x="30" y="400" width="1420" height="300" rx="10" fill="#fdf2e5" stroke="#edcba0" stroke-width="1.5"/>
  <rect x="30" y="376" width="150" height="24" rx="5" fill="#a05a2c"/>
  <text x="41" y="393.5" font-size="14" fill="#ffffff" font-weight="600">后端 OoO Execute</text>
  <text x="196" y="393" font-size="11.5" fill="#a05a2c" font-style="italic">ROB ~128 uop（实测有效 108–110）· 三类统一式调度器各 ~33 项</text>
  <rect x="50" y="436" width="250" height="150" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="62" y="458" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">发射队列（3 类统一式）</text>
  <text x="62" y="478" font-size="10.5" fill="#1f2937" text-anchor="start">· ALU 类 ~33 · 访存类 ~33 · FP/向量类 ~33</text>
  <text x="62" y="495" font-size="10.5" fill="#1f2937" text-anchor="start">· 唤醒-选择环路 1–2c</text>
  <text x="62" y="512" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">· 控制触发器密集 = SDC 敏感区</text>
  <text x="62" y="529" font-size="10.5" fill="#6b7280" text-anchor="start">· 每源寄存器一条等待链</text>
  <text x="62" y="546" font-size="10.5" fill="#6b7280" text-anchor="start">· 对照：Neoverse V2 为 9 个分立 IQ</text>
  <rect x="330" y="436" width="250" height="150" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="342" y="458" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">PRF + 旁路网络</text>
  <text x="342" y="478" font-size="10.5" fill="#1f2937" text-anchor="start">· INT PRF ~128 · Flag ~31 · FP PRF 偏小</text>
  <text x="342" y="495" font-size="10.5" fill="#1f2937" text-anchor="start">· 记分牌：读 PRF 或等旁路</text>
  <text x="342" y="512" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">· 旁路=纯导线+传输门，无任何保护</text>
  <text x="342" y="529" font-size="10.5" fill="#6b7280" text-anchor="start">· 背靠背链不写 PRF（转发掩蔽）</text>
  <rect x="610" y="436" width="380" height="150" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="622" y="458" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">执行单元簇</text>
  <text x="622" y="478" font-size="10.5" fill="#1f2937" text-anchor="start">· ALU×3（加 1c）· MUL/DIV×1（乘 4c；除 19c/早退 6.2c）</text>
  <text x="622" y="495" font-size="10.5" fill="#1f2937" text-anchor="start">· FP0/FP1 双 128-bit FMA（FP32 5c · FP64 quarter-rate）</text>
  <text x="622" y="512" font-size="10.5" fill="#1f2937" text-anchor="start">· 分支两口 · 1 taken/cyc · CRC32X 1c · AESD 3c</text>
  <text x="622" y="529" font-size="10.5" fill="#1f2937" text-anchor="start">· NEON 128b 上限（无 SVE）</text>
  <text x="622" y="546" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">· 进位链/FMA 树=时序违例重灾区（纯 SDC 通路）</text>
  <rect x="1020" y="436" width="400" height="150" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="1032" y="458" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">ROB ~128 uop + Commit（4 宽）</text>
  <text x="1032" y="478" font-size="10.5" fill="#1f2937" text-anchor="start">· 按程序序飞行指令账本 · 头部完成且无异常才退休</text>
  <text x="1032" y="495" font-size="10.5" fill="#1f2937" text-anchor="start">· squash 从出错点回滚全部后继</text>
  <text x="1032" y="512" font-size="10.5" fill="#1f2937" text-anchor="start">· 结果退休进架构态 · store 放行写 L1D（C7）</text>
  <text x="1032" y="529" font-size="10.5" fill="#6b7280" text-anchor="start">· x86 ROB 320–512 vs ARM 640–768+（面积账对照）</text>
  <text x="1032" y="546" font-size="10.5" fill="#6b7280" text-anchor="start">· 反压：ROB/IQ/LSQ 满 → rename 停</text>
  <path d="M300,510 L324,510" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <path d="M580,510 L604,510" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <path d="M990,510 L1014,510" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <rect x="30" y="730" width="1420" height="200" rx="10" fill="#eaf6ee" stroke="#a9d9bc" stroke-width="1.5"/>
  <rect x="30" y="706" width="150" height="24" rx="5" fill="#3f7a58"/>
  <text x="41" y="723.5" font-size="14" fill="#ffffff" font-weight="600">访存 LSU + MMU</text>
  <text x="196" y="723" font-size="11.5" fill="#3f7a58" font-style="italic">AGU×2 · store 不投机 · TLB 无保护（RAS=0）</text>
  <rect x="50" y="766" width="300" height="140" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="62" y="788" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">LSU：AGU×2 + L1D</text>
  <text x="62" y="808" font-size="10.5" fill="#1f2937" text-anchor="start">· 2 load 或 1L+1S /cyc · 2×128b 读</text>
  <text x="62" y="825" font-size="10.5" fill="#1f2937" text-anchor="start">· L1D 64KB 4-way · load-to-use 4c</text>
  <text x="62" y="842" font-size="10.5" fill="#1f2937" text-anchor="start">· store 转发 6–7c（跨 16B +1~2c）</text>
  <text x="62" y="859" font-size="10.5" fill="#1f2937" text-anchor="start">· LSE 原子在 L1 争用下 43c（CASAL 实测）</text>
  <text x="62" y="876" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">· 厂商称 ECC（无架构化证据）</text>
  <rect x="380" y="766" width="320" height="140" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="392" y="788" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">LSQ（LQ + SQ）· STLF</text>
  <text x="392" y="808" font-size="10.5" fill="#1f2937" text-anchor="start">· store 不投机：退休后才写 L1D</text>
  <text x="392" y="825" font-size="10.5" fill="#1f2937" text-anchor="start">· load 乱序但先查 SQ（STLF）</text>
  <text x="392" y="842" font-size="10.5" fill="#1f2937" text-anchor="start">· STLF：CAM 匹配直转，不经 cache/PRF</text>
  <text x="392" y="859" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">· STLF 段 ECC 全失明</text>
  <text x="392" y="876" font-size="10.5" fill="#6b7280" text-anchor="start">· （五款共同的 SDC 盲区）</text>
  <rect x="730" y="766" width="330" height="140" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="742" y="788" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">MMU：TLB + PTW</text>
  <text x="742" y="808" font-size="10.5" fill="#1f2937" text-anchor="start">· iTLB 32 项全相联 · dTLB 32 项全相联</text>
  <text x="742" y="825" font-size="10.5" fill="#1f2937" text-anchor="start">· L2 TLB 1024 项 I/D 共用，命中 +11c</text>
  <text x="742" y="842" font-size="10.5" fill="#1f2937" text-anchor="start">· PTW 4KB/16KB/64KB 粒度</text>
  <text x="742" y="859" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">· TLB 无保护披露（RAS=0）</text>
  <text x="742" y="876" font-size="10.5" fill="#6b7280" text-anchor="start">· 4KB×4=16KB 恰处 VIPT 别名临界（实测无别名）</text>
  <path d="M680,830 L704,830" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <rect x="30" y="960" width="1420" height="240" rx="10" fill="#f1edfb" stroke="#cfc0ef" stroke-width="1.5"/>
  <rect x="30" y="936" width="200" height="24" rx="5" fill="#6d5aa0"/>
  <text x="41" y="953.5" font-size="14" fill="#ffffff" font-weight="600">内存层级 Memory（chiplet）</text>
  <text x="246" y="953" font-size="11.5" fill="#6d5aa0" font-style="italic">chiplet：2 计算 die(SCCL)+1 IO die，CoWoS · 每 die 8 CCL(4核簇) · Hydra 互联 · 距离 10/12/20/22</text>
  <rect x="50" y="996" width="240" height="120" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="170.0" y="1018" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">L1-Dcache 64KB 4-way</text>
  <text x="170.0" y="1038" font-size="10.5" fill="#1f2937" text-anchor="middle">load 54.6 / store 41.2 GB/s</text>
  <text x="170.0" y="1055" font-size="10.5" fill="#1f2937" text-anchor="middle">4c load-to-use（依赖链实测 2.87）</text>
  <text x="170.0" y="1072" font-size="10.5" fill="#b91c1c" text-anchor="middle" font-weight="600">ECC 强度不可验证</text>
  <text x="170.0" y="1089" font-size="10.5" fill="#1f2937" text-anchor="middle">L1←L2 ~32B/cyc（refill 可观测）</text>
  <rect x="320" y="996" width="250" height="120" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="445.0" y="1018" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">L2 私有 512KB/核 8-way</text>
  <text x="445.0" y="1038" font-size="10.5" fill="#1f2937" text-anchor="middle">10c · 64B · PoU</text>
  <text x="445.0" y="1055" font-size="10.5" fill="#1f2937" text-anchor="middle">实测 4.88ns（256KB 工作集）</text>
  <text x="445.0" y="1072" font-size="10.5" fill="#b91c1c" text-anchor="middle" font-weight="600">厂商称 ECC（无证据）</text>
  <text x="445.0" y="1089" font-size="10.5" fill="#1f2937" text-anchor="middle">load 42.8 GB/s（256KB）</text>
  <rect x="600" y="996" width="400" height="178" rx="7" fill="#fffbeb" stroke="#b45309" stroke-width="3"/>
  <text x="612" y="1018" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">L3 / SLC 每 die 32MB</text>
  <text x="612" y="1038" font-size="10.5" fill="#1f2937" text-anchor="start">· 8 bank×4MB · 15-way 伪随机</text>
  <text x="612" y="1055" font-size="10.5" fill="#1f2937" text-anchor="start">· 128B 行（L1/L2 是 64B！）</text>
  <text x="612" y="1072" font-size="10.5" fill="#1f2937" text-anchor="start">· tag 在簇侧 · 数据 bank 在 NoC 侧</text>
  <text x="612" y="1089" font-size="10.5" fill="#b45309" text-anchor="start" font-weight="600">· 三模式 Shared/Private/Partition(默认)</text>
  <text x="612" y="1106" font-size="10.5" fill="#1f2937" text-anchor="start">· partition 近端 4MB ~36c → 全容量 &gt;90c</text>
  <text x="612" y="1123" font-size="10.5" fill="#1f2937" text-anchor="start">· 双核共享退化为全容量高延迟</text>
  <rect x="1030" y="996" width="390" height="120" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="1225.0" y="1018" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">DDR4-2933 ×8ch</text>
  <text x="1225.0" y="1038" font-size="10.5" fill="#1f2937" text-anchor="middle">每 die 读 ~63 GB/s</text>
  <text x="1225.0" y="1055" font-size="10.5" fill="#1f2937" text-anchor="middle">空载 ~96ns · 实测 163.5ns（256MB）</text>
  <text x="1225.0" y="1072" font-size="10.5" fill="#047857" text-anchor="middle" font-weight="600">Registered-DDR4 SECDED（ghes_edac 实证）</text>
  <text x="1225.0" y="1089" font-size="10.5" fill="#1f2937" text-anchor="middle">ce/ue 计数实测为 0</text>
  <path d="M290,1056 L314,1056" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <path d="M570,1056 L594,1056" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <path d="M1000,1056 L1024,1056" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <rect x="30" y="1240" width="1420" height="140" rx="10" fill="#fef2f2" stroke="#b91c1c" stroke-width="2"/>
  <text x="46" y="1266" font-size="15" fill="#b91c1c" font-weight="700">RAS / 保护状态（SDC 视角）——RAS=0，五款中敏感性最高</text>
  <text x="46" y="1288" font-size="11.5" fill="#1f2937">架构化 RAS (ERR*/ESB/poison)</text>
  <text x="406" y="1288" font-size="11.5" fill="#b91c1c">无 —— ID_AA64PFR0_EL1.RAS = 0（EL0 实测）：无 ERR* 记录寄存器、无 ESB、无架构化 poison、无 FHI/ERI、无架构化错误注入</text>
  <text x="46" y="1307" font-size="11.5" fill="#1f2937">核内翻转归宿</text>
  <text x="406" y="1307" font-size="11.5" fill="#b91c1c">性能异常 / 崩溃 / 静默（SDC）——最后一类无任何架构级可见信号</text>
  <text x="46" y="1326" font-size="11.5" fill="#1f2937">厂商宣称冲突</text>
  <text x="406" y="1326" font-size="11.5" fill="#b91c1c">宣称 I$/D$ ECC、Memory Poisoning 与 RAS=0 冲突：即便有也是非架构化私有实现，SDC 实验不可依赖</text>
  <text x="46" y="1345" font-size="11.5" fill="#1f2937">平台级 RAS</text>
  <text x="406" y="1345" font-size="11.5" fill="#047857">ACPI HEST/EINJ/BERT/ERST 全在（EINJ 368B 固件注入可用）· ghes_edac DDR SECDED · MPAM · SDEI</text>
  <text x="46" y="1364" font-size="11.5" fill="#1f2937">uncore 观测</text>
  <text x="406" y="1364" font-size="11.5" fill="#6b7280">每 die L3C×8（back_invalid=一致性干扰）· HHA×2 · DDRC×4 · 需 perf_event_paranoid≤1 · 调频粒度=die 级</text>
</svg>

</div>

独有/标志性：L3/SLC 三模式（Shared/Private/**Partition 默认**）+ **128B 行**（L1/L2 是 64B）+ tag 在簇侧；
无 µop cache（取指带宽悬崖）；**RAS=0**（无架构化 RAS，全图唯一的"裸奔"平台）；AIVIVT L1I；NEON 128b 上限。

### 920f（part 0xd22）

<div align="center">

<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1480 1400" width="1480" height="1400" font-family="system-ui,'PingFang SC','Noto Sans CJK SC','Microsoft YaHei',sans-serif">
  <defs><marker id="arr" markerWidth="11" markerHeight="9" refX="9.5" refY="4.5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L11,4.5 L0,9 Z" fill="#5a6b7c"/></marker><marker id="arrC" markerWidth="11" markerHeight="9" refX="9.5" refY="4.5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L11,4.5 L0,9 Z" fill="#7c3aed"/></marker></defs>
  <rect x="0" y="0" width="1480" height="1400" fill="#ffffff"/>
  <text x="30" y="34" font-size="20" font-weight="700" fill="#1f2937">920f · HiSilicon part 0xd22 微架构功能图（ARMv9 · SVE512+SME2 · 黑盒实测）</text>
  <text x="30" y="56" font-size="12" fill="#6b7280">布局 = 黑盒结构：大量未公开（灰虚线）+ SVE512/SME2 宽向量金卡 + 无 LLC 扁平层级 + 64KB 强制页。出处：920f.md NSCC cn23154 实测</text>
  <rect x="30" y="72" width="1420" height="36" rx="6" fill="#f7f9fb" stroke="#c6d2dd"/>
    <line x1="46" y1="90" x2="72" y2="90" stroke="#5a6b7c" stroke-width="2" marker-end="url(#arr)"/>
    <text x="78" y="94" font-size="11.5" fill="#1f2937">指令/数据流</text>
    <line x1="201" y1="90" x2="227" y2="90" stroke="#7c3aed" stroke-width="2" stroke-dasharray="5,3" marker-end="url(#arrC)"/>
    <text x="233" y="94" font-size="11.5" fill="#1f2937">控制流</text>
    <rect x="313" y="83" width="14" height="14" fill="#fffbeb" stroke="#b45309" stroke-width="2.6"/>
    <text x="333" y="94" font-size="11.5" fill="#1f2937">独有/标志性</text>
    <rect x="456" y="83" width="14" height="14" fill="#f9fafb" stroke="#9ca3af" stroke-width="1.3" stroke-dasharray="4,3"/>
    <text x="476" y="94" font-size="11.5" fill="#1f2937">未公开/黑盒</text>
    <line x1="599" y1="90" x2="621" y2="90" stroke="#b91c1c" stroke-width="3.5"/>
    <text x="627" y="94" font-size="11.5" fill="#1f2937">SDC 高危/无保护</text>
  <rect x="30" y="130" width="1420" height="240" rx="10" fill="#eaf2fb" stroke="#a9c9ec" stroke-width="1.5"/>
  <rect x="30" y="106" width="210" height="24" rx="5" fill="#4a5f78"/>
  <text x="41" y="123.5" font-size="14" fill="#ffffff" font-weight="600">前端 Fetch（规格未公开）</text>
  <text x="256" y="123" font-size="11.5" fill="#4a5f78" font-style="italic">分支预测器容量待测（bpbench 未完成）· 仅 AArch64 · CTR_EL0=0x9444c004（ERG=64B）</text>
  <rect x="50" y="166" width="250" height="130" rx="7" fill="#f9fafb" stroke="#9ca3af" stroke-width="1.5" stroke-dasharray="6,4"/>
  <text x="175.0" y="188" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">BPU（未公开）</text>
  <text x="175.0" y="208" font-size="10.5" fill="#1f2937" text-anchor="middle">BTB/RAS/间接预测容量</text>
  <text x="175.0" y="225" font-size="10.5" fill="#1f2937" text-anchor="middle">均未测得（待 bpbench）</text>
  <text x="175.0" y="242" font-size="10.5" fill="#1f2937" text-anchor="middle">CSV2/3=1（推测攻击缓解在）</text>
  <rect x="340" y="166" width="210" height="130" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="445.0" y="188" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">L1-I-cache 32KB 4-way</text>
  <text x="445.0" y="208" font-size="10.5" fill="#1f2937" text-anchor="middle">64B 行（CTR 实测）</text>
  <text x="445.0" y="225" font-size="10.5" fill="#b91c1c" text-anchor="middle" font-weight="600">ECC/parity 未披露</text>
  <text x="445.0" y="242" font-size="10.5" fill="#1f2937" text-anchor="middle">（RAS=1 但无 TRM）</text>
  <rect x="580" y="166" width="210" height="130" rx="7" fill="#f9fafb" stroke="#9ca3af" stroke-width="1.5" stroke-dasharray="6,4"/>
  <text x="685.0" y="188" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">译码 / 重命名 / 派遣</text>
  <text x="685.0" y="208" font-size="10.5" fill="#1f2937" text-anchor="middle">宽度未公开</text>
  <text x="685.0" y="225" font-size="10.5" fill="#1f2937" text-anchor="middle">仅 A64 指令集</text>
  <text x="685.0" y="242" font-size="10.5" fill="#1f2937" text-anchor="middle">（无 AArch32）</text>
  <rect x="820" y="166" width="330" height="178" rx="7" fill="#fffbeb" stroke="#b45309" stroke-width="3"/>
  <text x="832" y="188" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">SVE 512-bit + SME/SME2（五款唯一宽向量）</text>
  <text x="832" y="208" font-size="10.5" fill="#1f2937" text-anchor="start">· SVEver=1 · f32mm/f64mm/BF16=1 · 实测 VL=64B</text>
  <text x="832" y="225" font-size="10.5" fill="#1f2937" text-anchor="start">· SME2：f64f64/b16f32/f32f32/i8i32（fa64=0）</text>
  <text x="832" y="242" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">· Z0–Z31 × 512b + 矩阵 tile = 新增大面积无保护数据面</text>
  <text x="832" y="259" font-size="10.5" fill="#1f2937" text-anchor="start">· SVE512 FMA 实测 ≥13.6 flop/cyc（理论 16）</text>
  <text x="832" y="276" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">· 单向量翻转影响 64B 连续数据</text>
  <rect x="1180" y="166" width="240" height="130" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="1192" y="188" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">ISA 扩展（实测）</text>
  <text x="1192" y="208" font-size="10.5" fill="#1f2937" text-anchor="start">SHA1/2/512 · SHA3 · SM3/SM4</text>
  <text x="1192" y="225" font-size="10.5" fill="#1f2937" text-anchor="start">LRCPC2/3 · i8mm · bf16 · RPRES</text>
  <text x="1192" y="242" font-size="10.5" fill="#1f2937" text-anchor="start">WFXT · SVE2 全集 · AES · LSE</text>
  <text x="1192" y="259" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">BTI=0 · MTE=0 · RNDR=0</text>
  <path d="M300,230 L334,230" fill="none" stroke="#7c3aed" stroke-width="1.6" marker-end="url(#arrC)"/>
  <path d="M550,230 L574,230" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <path d="M790,230 L814,230" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <path d="M1150,230 L1174,230" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <rect x="30" y="400" width="1420" height="300" rx="10" fill="#fdf2e5" stroke="#edcba0" stroke-width="1.5"/>
  <rect x="30" y="376" width="210" height="24" rx="5" fill="#a05a2c"/>
  <text x="41" y="393.5" font-size="14" fill="#ffffff" font-weight="600">后端 OoO Execute（吞吐实测）</text>
  <text x="256" y="393" font-size="11.5" fill="#a05a2c" font-style="italic">标量 FMA 2/cyc · NEON128 FMA 2/cyc · SVE512 FMA ≥2/cyc——三级向量吞吐阶梯全部双发</text>
  <rect x="50" y="436" width="300" height="150" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="62" y="458" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">标量 / NEON 通路</text>
  <text x="62" y="478" font-size="10.5" fill="#1f2937" text-anchor="start">· 标量 FMADD 8 链：8.0 Gflop/s = 4 flop/cyc</text>
  <text x="62" y="495" font-size="10.5" fill="#1f2937" text-anchor="start">· NEON128 8×2lane：13.5 Gflop/s ≈ 6.75</text>
  <text x="62" y="512" font-size="10.5" fill="#b45309" text-anchor="start" font-weight="600">· 标量 FMA 双端口实证（920 为 FP 单口怪点）</text>
  <text x="62" y="529" font-size="10.5" fill="#1f2937" text-anchor="start">· 单核理论 128 Gflop/s（SVE512 FP64）</text>
  <rect x="380" y="436" width="330" height="178" rx="7" fill="#fffbeb" stroke="#b45309" stroke-width="3"/>
  <text x="392" y="458" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">SVE512 数据通路</text>
  <text x="392" y="478" font-size="10.5" fill="#1f2937" text-anchor="start">· SVE512 8×8lane：27.2 Gflop/s 下限（~13.6）</text>
  <text x="392" y="495" font-size="10.5" fill="#1f2937" text-anchor="start">· 608 核节点理论 ~77.8 Tflop/s（FP64）</text>
  <text x="392" y="512" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">· 单向量翻转影响 64B 连续数据</text>
  <text x="392" y="529" font-size="10.5" fill="#6b7280" text-anchor="start">· flopbench 修正版待复测（初版被编译器削链）</text>
  <text x="392" y="546" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">· 全部数据面无保护披露</text>
  <rect x="740" y="436" width="300" height="150" rx="7" fill="#f9fafb" stroke="#9ca3af" stroke-width="1.5" stroke-dasharray="6,4"/>
  <text x="890.0" y="458" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">PRF / ROB / 调度器（未公开）</text>
  <text x="890.0" y="478" font-size="10.5" fill="#1f2937" text-anchor="middle">容量/结构黑盒</text>
  <text x="890.0" y="495" font-size="10.5" fill="#1f2937" text-anchor="middle">与五款一致：无任何保护披露</text>
  <text x="890.0" y="512" font-size="10.5" fill="#1f2937" text-anchor="middle">FI 实验按 gem5 O3 通用模型注入</text>
  <rect x="1070" y="436" width="350" height="150" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="1082" y="458" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">LSU / 访存</text>
  <text x="1082" y="478" font-size="10.5" fill="#1f2937" text-anchor="start">· LSE 原子 · LRCPC2/3（LDAPR 系增强）</text>
  <text x="1082" y="495" font-size="10.5" fill="#1f2937" text-anchor="start">· DC ZVA 64B</text>
  <text x="1082" y="512" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">· LSQ/store buffer 保护未披露（五款共同盲区）</text>
  <text x="1082" y="529" font-size="10.5" fill="#6b7280" text-anchor="start">· 定频 2.0GHz（userspace 锁 MAX）→ 测量无变频噪声</text>
  <path d="M350,510 L374,510" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <path d="M710,510 L734,510" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <path d="M1040,510 L1064,510" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <rect x="30" y="730" width="1420" height="240" rx="10" fill="#f1edfb" stroke="#cfc0ef" stroke-width="1.5"/>
  <rect x="30" y="706" width="210" height="24" rx="5" fill="#6d5aa0"/>
  <text x="41" y="723.5" font-size="14" fill="#ffffff" font-weight="600">内存层级 + MMU（无 LLC）</text>
  <text x="256" y="723" font-size="11.5" fill="#6d5aa0" font-style="italic">16 计算 NUMA + 16 无 CPU 内存节点（疑似 CXL/近存）· 跨 socket 距离 61–91 · 8×200GbE RoCE 聚合 1.6Tb/s</text>
  <rect x="50" y="766" width="250" height="150" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="175.0" y="788" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">L1-Dcache 32KB 8-way</text>
  <text x="175.0" y="808" font-size="10.5" fill="#1f2937" text-anchor="middle">64B 行 · 实测 ~5.0ns（≈10c）</text>
  <text x="175.0" y="825" font-size="10.5" fill="#b45309" text-anchor="middle" font-weight="600">8-way（同代 Neoverse 为 4-way）</text>
  <text x="175.0" y="842" font-size="10.5" fill="#b91c1c" text-anchor="middle" font-weight="600">ECC 未披露</text>
  <text x="175.0" y="859" font-size="10.5" fill="#1f2937" text-anchor="middle">容量 32KB &lt; 920 的 64KB</text>
  <rect x="330" y="766" width="290" height="150" rx="7" fill="#fffbeb" stroke="#b45309" stroke-width="3"/>
  <text x="475.0" y="788" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">L2 私有 768KB 12-way</text>
  <text x="475.0" y="808" font-size="10.5" fill="#1f2937" text-anchor="middle">统一 I+D · 实测 ~8.7ns（≈17c）</text>
  <text x="475.0" y="825" font-size="10.5" fill="#b45309" text-anchor="middle" font-weight="600">五款中最大私有 L2（N3 可配 2MB 追平）</text>
  <text x="475.0" y="842" font-size="10.5" fill="#b45309" text-anchor="middle" font-weight="600">12-way 非常规（920:8 / N 系:8）</text>
  <text x="475.0" y="859" font-size="10.5" fill="#b91c1c" text-anchor="middle" font-weight="600">ECC 未披露</text>
  <rect x="650" y="766" width="300" height="150" rx="7" fill="#fffbeb" stroke="#b45309" stroke-width="3"/>
  <text x="800.0" y="788" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">无 L3 / LLC</text>
  <text x="800.0" y="808" font-size="10.5" fill="#b45309" text-anchor="middle" font-weight="600">sysfs 无 index3 · CLIDR 陷阱实证</text>
  <text x="800.0" y="825" font-size="10.5" fill="#1f2937" text-anchor="middle">SCN 网状远端 8–16MB → 45–90ns</text>
  <text x="800.0" y="842" font-size="10.5" fill="#1f2937" text-anchor="middle">（网络侧缓存，非核侧 LLC）</text>
  <text x="800.0" y="859" font-size="10.5" fill="#1f2937" text-anchor="middle">少一级缓存 = 少一级 SDC 暴露面</text>
  <rect x="980" y="766" width="440" height="150" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="992" y="788" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">DRAM / NUMA</text>
  <text x="992" y="808" font-size="10.5" fill="#1f2937" text-anchor="start">565GB · 16×31–33GB 计算节点</text>
  <text x="992" y="825" font-size="10.5" fill="#1f2937" text-anchor="start">远程 NUMA 实测 ~130ns</text>
  <text x="992" y="842" font-size="10.5" fill="#1f2937" text-anchor="start">node16–31 无 CPU 各 4GB（性质待确认：CXL? HBM?）</text>
  <text x="992" y="859" font-size="10.5" fill="#1f2937" text-anchor="start">PMUv3 6 计数器 + SPE + AMU=1 · DIT=1</text>
  <path d="M300,840 L324,840" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <path d="M620,840 L644,840" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <path d="M950,840 L974,840" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <rect x="30" y="1010" width="1420" height="170" rx="10" fill="#eaf6ee" stroke="#a9d9bc" stroke-width="1.5"/>
  <rect x="30" y="986" width="160" height="24" rx="5" fill="#3f7a58"/>
  <text x="41" y="1003.5" font-size="14" fill="#ffffff" font-weight="600">MMU：TLB + PTW</text>
  <text x="206" y="1003" font-size="11.5" fill="#3f7a58" font-style="italic">TLB 容量未测（缺口，待补）</text>
  <rect x="50" y="1046" width="620" height="110" rx="7" fill="#fffbeb" stroke="#b45309" stroke-width="3"/>
  <text x="62" y="1068" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">64KB 强制页（TGran4=0xf）</text>
  <text x="62" y="1088" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">· 单 TLB entry 翻转波及面 ×16（vs 4KB 页）——SDC 放大器</text>
  <text x="62" y="1105" font-size="10.5" fill="#1f2937" text-anchor="start">· PAGESIZE=4096 是内核兼容层假象</text>
  <text x="62" y="1122" font-size="10.5" fill="#b45309" text-anchor="start" font-weight="600">· 未被文献覆盖的放大器实验设计点</text>
  <rect x="700" y="1046" width="720" height="110" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="712" y="1068" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">uncore 观测</text>
  <text x="712" y="1088" font-size="10.5" fill="#1f2937" text-anchor="start">171 perf 设备 = 8 SCCL×(4 DDRC+4 HHA+16 UC) + 14 SICL L3（hisi_sicl3_pa/h60pa）+ SPE + PCIe PTT</text>
  <text x="712" y="1105" font-size="10.5" fill="#1f2937" text-anchor="start">隔离：isolcpus + nohz_full 覆盖 608 核，每 NUMA 留末核处理中断（FI 实验绑核须避开）</text>
  <text x="712" y="1122" font-size="10.5" fill="#6b7280" text-anchor="start">复现入口：dnode -l cn23154 / dattach -c '/home/share/suke/archprobe/...'（详见 920f.md §6）</text>
  <rect x="30" y="1215" width="1420" height="140" rx="10" fill="#fef2f2" stroke="#b91c1c" stroke-width="2"/>
  <text x="46" y="1241" font-size="15" fill="#b91c1c" font-weight="700">RAS / 保护状态（SDC 视角）——RAS=1 但防御矩阵黑盒</text>
  <text x="46" y="1263" font-size="11.5" fill="#1f2937">架构化 RAS</text>
  <text x="406" y="1263" font-size="11.5" fill="#047857">ID_AA64PFR0_EL1.RAS = 1（实测）—— 有 ARMv8.2+ RAS 架构扩展，但防御矩阵黑盒</text>
  <text x="46" y="1282" font-size="11.5" fill="#1f2937">与 920 的关键代差</text>
  <text x="406" y="1282" font-size="11.5" fill="#1f2937">ERR* 寄存器 / ESB / 架构化 poison 理论上存在 · 具体注入寄存器布局未知（无厂商 TRM）</text>
  <text x="46" y="1301" font-size="11.5" fill="#1f2937">其他</text>
  <text x="406" y="1301" font-size="11.5" fill="#1f2937">DIT=1（数据无关时间）· CSV2/3=1 · AMU=1 · 无 MTE（内存标签纠错不可用）</text>
  <text x="46" y="1320" font-size="11.5" fill="#1f2937">SDC 实验定位</text>
  <text x="406" y="1320" font-size="11.5" fill="#b91c1c">RAS=1 但无文档 → 有防御潜力但强度未知；64KB 页 × TLB 注入是未被文献覆盖的放大器实验</text>
  <text x="46" y="1339" font-size="11.5" fill="#1f2937">未决项（920f.md §7 原文）</text>
  <text x="406" y="1339" font-size="11.5" fill="#6b7280">SVE512 峰值复测 · 分支预测器容量（bpbench 中断过）· node16–31 内存节点性质（需 ddrc PMU 或 dmesg root）</text>
</svg>

</div>

独有/标志性：**SVE 512-bit + SME/SME2**（五款唯一宽向量）；**768KB/12-way L2**（非常规配置）；
**无 L3/LLC**（少一级缓存暴露面）；**64KB 强制页**（TLB 翻转波及面 ×16 放大器）；RAS=1 但防御矩阵黑盒。

### Neoverse N1

<div align="center">

<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1480 1450" width="1480" height="1450" font-family="system-ui,'PingFang SC','Noto Sans CJK SC','Microsoft YaHei',sans-serif">
  <defs><marker id="arr" markerWidth="11" markerHeight="9" refX="9.5" refY="4.5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L11,4.5 L0,9 Z" fill="#5a6b7c"/></marker><marker id="arrC" markerWidth="11" markerHeight="9" refX="9.5" refY="4.5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L11,4.5 L0,9 Z" fill="#7c3aed"/></marker></defs>
  <rect x="0" y="0" width="1480" height="1450" fill="#ffffff"/>
  <text x="30" y="34" font-size="20" font-weight="700" fill="#1f2937">Arm Neoverse N1 微架构功能图（ARMv8.2-A · 超标量乱序 · DSU）</text>
  <text x="30" y="56" font-size="12" fill="#6b7280">布局 = N1 TRM 组件结构（章节号随文标注）：三指令集译码 + ETM + 三级原子 + 两级 TLB（L1 flops）。出处：Neoverse N1 TRM 100616_0401_02</text>
  <rect x="30" y="72" width="1420" height="36" rx="6" fill="#f7f9fb" stroke="#c6d2dd"/>
    <line x1="46" y1="90" x2="72" y2="90" stroke="#5a6b7c" stroke-width="2" marker-end="url(#arr)"/>
    <text x="78" y="94" font-size="11.5" fill="#1f2937">指令/数据流</text>
    <line x1="201" y1="90" x2="227" y2="90" stroke="#7c3aed" stroke-width="2" stroke-dasharray="5,3" marker-end="url(#arrC)"/>
    <text x="233" y="94" font-size="11.5" fill="#1f2937">控制流</text>
    <rect x="313" y="83" width="14" height="14" fill="#fffbeb" stroke="#b45309" stroke-width="2.6"/>
    <text x="333" y="94" font-size="11.5" fill="#1f2937">独有/标志性</text>
    <rect x="456" y="83" width="14" height="14" fill="#f9fafb" stroke="#9ca3af" stroke-width="1.3" stroke-dasharray="4,3"/>
    <text x="476" y="94" font-size="11.5" fill="#1f2937">未公开/黑盒</text>
    <line x1="599" y1="90" x2="621" y2="90" stroke="#b91c1c" stroke-width="3.5"/>
    <text x="627" y="94" font-size="11.5" fill="#1f2937">SDC 高危/无保护</text>
  <rect x="30" y="130" width="1420" height="240" rx="10" fill="#eaf2fb" stroke="#a9c9ec" stroke-width="1.5"/>
  <rect x="30" y="106" width="220" height="24" rx="5" fill="#4a5f78"/>
  <text x="41" y="123.5" font-size="14" fill="#ffffff" font-weight="600">前端 Fetch（按序 · TRM §3.1）</text>
  <text x="266" y="123" font-size="11.5" fill="#4a5f78" font-style="italic">取指→译码→重命名→派遣 · A32/T32/A64 三指令集译码 · I$ 硬件一致性可配（COHERENT_ICACHE，推荐 L2=1MB）</text>
  <rect x="50" y="166" width="260" height="130" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="62" y="188" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">程序流预测（TRM §7.3）</text>
  <text x="62" y="208" font-size="10.5" fill="#1f2937" text-anchor="start">动态分支预测器 + BTB + 间接预测</text>
  <text x="62" y="225" font-size="10.5" fill="#1f2937" text-anchor="start">容量 TRM 未披露</text>
  <text x="62" y="242" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">Table 9-1 明示：BTB / GHB / BPIQ</text>
  <text x="62" y="259" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">全部 None（无保护）</text>
  <rect x="340" y="166" width="220" height="130" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="450.0" y="188" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">L1-I-cache 64KB 4-way</text>
  <text x="450.0" y="208" font-size="10.5" fill="#1f2937" text-anchor="middle">64B 行 · 硬件一致性可配（§3.1.1）</text>
  <text x="450.0" y="225" font-size="10.5" fill="#047857" text-anchor="middle" font-weight="600">tag: 1 parity/39b · data: SED/72b</text>
  <text x="450.0" y="242" font-size="10.5" fill="#1f2937" text-anchor="middle">错误→行失效重取（无数据丢失）</text>
  <rect x="590" y="166" width="200" height="130" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="690.0" y="188" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">译码（§3.1.2）</text>
  <text x="690.0" y="208" font-size="10.5" fill="#1f2937" text-anchor="middle">A32 / T32 / A64</text>
  <text x="690.0" y="225" font-size="10.5" fill="#1f2937" text-anchor="middle">NEON+FP 各态支持</text>
  <text x="690.0" y="242" font-size="10.5" fill="#b45309" text-anchor="middle" font-weight="600">AArch32 EL0（五款唯一）</text>
  <rect x="820" y="166" width="200" height="130" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="920.0" y="188" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">重命名（§3.1.3）</text>
  <text x="920.0" y="208" font-size="10.5" fill="#1f2937" text-anchor="middle">寄存器重命名促乱序</text>
  <text x="920.0" y="225" font-size="10.5" fill="#1f2937" text-anchor="middle">分发至各发射队列</text>
  <text x="920.0" y="242" font-size="10.5" fill="#b91c1c" text-anchor="middle" font-weight="600">PRF 保护无披露</text>
  <rect x="1050" y="166" width="180" height="130" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="1140.0" y="188" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">发射（§3.1.4）</text>
  <text x="1140.0" y="208" font-size="10.5" fill="#1f2937" text-anchor="middle">issue queues 暂存</text>
  <text x="1140.0" y="225" font-size="10.5" fill="#1f2937" text-anchor="middle">待派发指令</text>
  <text x="1140.0" y="242" font-size="10.5" fill="#1f2937" text-anchor="middle">（容量未披露）</text>
  <rect x="1270" y="166" width="160" height="130" rx="7" fill="#fffbeb" stroke="#b45309" stroke-width="3"/>
  <text x="1350.0" y="188" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">ETM（§2.2）</text>
  <text x="1350.0" y="208" font-size="10.5" fill="#1f2937" text-anchor="middle">Embedded Trace</text>
  <text x="1350.0" y="225" font-size="10.5" fill="#1f2937" text-anchor="middle">Macrocell</text>
  <text x="1350.0" y="242" font-size="10.5" fill="#1f2937" text-anchor="middle">指令 trace only</text>
  <text x="1350.0" y="259" font-size="10.5" fill="#b45309" text-anchor="middle" font-weight="600">N2/N3 为 ETE+TRBE 型</text>
  <path d="M310,230 L334,230" fill="none" stroke="#7c3aed" stroke-width="1.6" marker-end="url(#arrC)"/>
  <path d="M560,230 L584,230" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <path d="M790,230 L814,230" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <path d="M1020,230 L1044,230" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <rect x="30" y="400" width="1420" height="300" rx="10" fill="#fdf2e5" stroke="#edcba0" stroke-width="1.5"/>
  <rect x="30" y="376" width="150" height="24" rx="5" fill="#a05a2c"/>
  <text x="41" y="393.5" font-size="14" fill="#ffffff" font-weight="600">后端 OoO Execute</text>
  <text x="196" y="393" font-size="11.5" fill="#a05a2c" font-style="italic">INT 单元 + 向量单元（NEON+FP，可选 Crypto）· 写回经记分牌仲裁 · 推测错路径经 squash 回滚</text>
  <rect x="50" y="436" width="300" height="150" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="62" y="458" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">整数执行（§3.1.5）</text>
  <text x="62" y="478" font-size="10.5" fill="#1f2937" text-anchor="start">· 算术/逻辑数据处理 · ROB 128（公开规格）</text>
  <text x="62" y="495" font-size="10.5" fill="#1f2937" text-anchor="start">· LDAPR 系（RCpc v8.3，ISAR1 实证）</text>
  <text x="62" y="512" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">· ALU 位翻转=纯 SDC 通路（无任何校验）</text>
  <text x="62" y="529" font-size="10.5" fill="#6b7280" text-anchor="start">· LOR：4 个 Limited Ordering Region 描述符</text>
  <rect x="380" y="436" width="300" height="150" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="392" y="458" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">向量执行（§3.1.5）</text>
  <text x="392" y="478" font-size="10.5" fill="#1f2937" text-anchor="start">· NEON 128b SIMD + FP32/FP64</text>
  <text x="392" y="495" font-size="10.5" fill="#1f2937" text-anchor="start">· Crypto 可选（AES/SHA）· 无 SVE</text>
  <text x="392" y="512" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">· FMA 树=时序违例重灾区</text>
  <rect x="710" y="436" width="330" height="150" rx="7" fill="#fffbeb" stroke="#b45309" stroke-width="3"/>
  <text x="722" y="458" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">三级原子执行（§7.4.1）</text>
  <text x="722" y="478" font-size="10.5" fill="#1f2937" text-anchor="start">· near atomic：L1 命中且 unique 态，核内完成</text>
  <text x="722" y="495" font-size="10.5" fill="#1f2937" text-anchor="start">· far atomic：miss/共享 → CHI 接口送互联</text>
  <text x="722" y="512" font-size="10.5" fill="#1f2937" text-anchor="start">· 全簇 miss → DSU L3 分配执行（可配 L3 时）</text>
  <text x="722" y="529" font-size="10.5" fill="#6b7280" text-anchor="start">· CPUECTLR 可配各类原子倾向 near · PLDW/PRFM 提示</text>
  <rect x="1080" y="436" width="340" height="150" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="1250.0" y="458" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">观测单元（§2.2）</text>
  <text x="1250.0" y="478" font-size="10.5" fill="#1f2937" text-anchor="middle">PMU + SPE + AMU</text>
  <text x="1250.0" y="495" font-size="10.5" fill="#1f2937" text-anchor="middle">TrustZone · PBHA</text>
  <text x="1250.0" y="512" font-size="10.5" fill="#1f2937" text-anchor="middle">Crypto 可选扩展</text>
  <path d="M350,510 L374,510" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <path d="M680,510 L704,510" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <rect x="30" y="730" width="1420" height="240" rx="10" fill="#eaf6ee" stroke="#a9d9bc" stroke-width="1.5"/>
  <rect x="30" y="706" width="150" height="24" rx="5" fill="#3f7a58"/>
  <text x="41" y="723.5" font-size="14" fill="#ffffff" font-weight="600">访存 LSU + MMU</text>
  <text x="196" y="723" font-size="11.5" fill="#3f7a58" font-style="italic">L1D 64KB 4-way VIPT · ECC per 32 bits · 两级 TLB</text>
  <rect x="50" y="766" width="330" height="178" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="62" y="788" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">LSU + L1D（§3.1.6/§7.4）</text>
  <text x="62" y="808" font-size="10.5" fill="#1f2937" text-anchor="start">· L1D 64KB 4-way VIPT 64B · ECC per 32 bits</text>
  <text x="62" y="825" font-size="10.5" fill="#1f2937" text-anchor="start">· 内部独占监视器（LL/SC）</text>
  <text x="62" y="842" font-size="10.5" fill="#1f2937" text-anchor="start">· transient/non-temporal 特化</text>
  <text x="62" y="859" font-size="10.5" fill="#1f2937" text-anchor="start">· write streaming 模式（§7.2.7）</text>
  <text x="62" y="876" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">· L1 PHT 无保护（Table 9-1）</text>
  <rect x="410" y="766" width="280" height="130" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="550.0" y="788" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">预取（§7.5）</text>
  <text x="550.0" y="808" font-size="10.5" fill="#1f2937" text-anchor="middle">数据预取器 + L1 PHT</text>
  <text x="550.0" y="825" font-size="10.5" fill="#b91c1c" text-anchor="middle" font-weight="600">PHT：Table 9-1 明示 None</text>
  <text x="550.0" y="842" font-size="10.5" fill="#1f2937" text-anchor="middle">（预取错地址多被掩盖，低危）</text>
  <rect x="720" y="766" width="700" height="178" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="732" y="788" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">MMU：两级 TLB（§6.2）</text>
  <text x="732" y="808" font-size="10.5" fill="#1f2937" text-anchor="start">· iTLB 48 项全相联（4K–32M）· dTLB 48 项全相联（4K–512M）· L1 命中 1c</text>
  <text x="732" y="825" font-size="10.5" fill="#1f2937" text-anchor="start">· L2 TLB 1280 项 5-way 共享（§6.2.3）· 4 并行 walk / 2 lookup · 连续 6 miss 停顿</text>
  <text x="732" y="842" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">· L1 TLB 用触发器实现 → 无 cache 保护（TRM 原文注释）</text>
  <text x="732" y="859" font-size="10.5" fill="#1f2937" text-anchor="start">· MMUTC 2-bit 交错 parity/71b</text>
  <rect x="30" y="1010" width="1420" height="240" rx="10" fill="#f1edfb" stroke="#cfc0ef" stroke-width="1.5"/>
  <rect x="30" y="986" width="230" height="24" rx="5" fill="#6d5aa0"/>
  <text x="41" y="1003.5" font-size="14" fill="#ffffff" font-weight="600">内存层级（L1 → L2 → DSU）</text>
  <text x="276" y="1003" font-size="11.5" fill="#6d5aa0" font-style="italic">异步 CPU bridge 连 DSU · 组件常在 · 与 DSU 间仅一致性接口可配同步</text>
  <rect x="50" y="1046" width="280" height="178" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="190.0" y="1068" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">L1-Dcache 64KB 4-way VIPT</text>
  <text x="190.0" y="1088" font-size="10.5" fill="#1f2937" text-anchor="middle">64B 行 · ECC per 32 bits（§3.1.6）</text>
  <text x="190.0" y="1105" font-size="10.5" fill="#047857" text-anchor="middle" font-weight="600">Table 9-1: tag SECDED 42+7b</text>
  <text x="190.0" y="1122" font-size="10.5" fill="#047857" text-anchor="middle" font-weight="600">data SECDED 32+1 poison+7b</text>
  <text x="190.0" y="1139" font-size="10.5" fill="#1f2937" text-anchor="middle">poison 粒度 64b（L1D 特例 32b）</text>
  <text x="190.0" y="1156" font-size="10.5" fill="#1f2937" text-anchor="middle">UC→evict 纠正回填（§9.2）</text>
  <rect x="360" y="1046" width="330" height="178" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="525.0" y="1068" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">L2 私有 256/512/1024KB 8-way</text>
  <text x="525.0" y="1088" font-size="10.5" fill="#1f2937" text-anchor="middle">私有统一（§3.1.7）· 2 bank</text>
  <text x="525.0" y="1105" font-size="10.5" fill="#047857" text-anchor="middle" font-weight="600">tag SECDED（50–57 tag+7 ECC）</text>
  <text x="525.0" y="1122" font-size="10.5" fill="#047857" text-anchor="middle" font-weight="600">data SECDED 8 ECC/64b</text>
  <text x="525.0" y="1139" font-size="10.5" fill="#b45309" text-anchor="middle" font-weight="600">TQ 24/36/48 项可配（2bank×12/18/24）</text>
  <text x="525.0" y="1156" font-size="10.5" fill="#b91c1c" text-anchor="middle" font-weight="600">L2 victim 阵列：None（Table 9-1）</text>
  <rect x="720" y="1046" width="330" height="178" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="885.0" y="1068" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">DSU（簇共享单元）</text>
  <text x="885.0" y="1088" font-size="10.5" fill="#1f2937" text-anchor="middle">≤4 核 + 可选 L3 / snoop filter</text>
  <text x="885.0" y="1105" font-size="10.5" fill="#1f2937" text-anchor="middle">单核直连配置可无 L3/SCU</text>
  <text x="885.0" y="1122" font-size="10.5" fill="#1f2937" text-anchor="middle">L3 保护 = DSU TRM 范围</text>
  <text x="885.0" y="1139" font-size="10.5" fill="#1f2937" text-anchor="middle">（core TRM 不披露）</text>
  <rect x="1080" y="1046" width="340" height="150" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="1250.0" y="1068" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">SoC 侧</text>
  <text x="1250.0" y="1088" font-size="10.5" fill="#1f2937" text-anchor="middle">48-bit PA · GICv4.1 CPU 接口</text>
  <text x="1250.0" y="1105" font-size="10.5" fill="#1f2937" text-anchor="middle">PMU + SPE + AMU（§2.2）</text>
  <text x="1250.0" y="1122" font-size="10.5" fill="#1f2937" text-anchor="middle">TrustZone · PBHA</text>
  <text x="1250.0" y="1139" font-size="10.5" fill="#1f2937" text-anchor="middle">Crypto 可选扩展</text>
  <path d="M330,1120 L354,1120" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <path d="M690,1120 L714,1120" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <path d="M1050,1120 L1074,1120" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <rect x="30" y="1290" width="1420" height="160" rx="10" fill="#f0fdf4" stroke="#047857" stroke-width="2"/>
  <text x="46" y="1316" font-size="15" fill="#047857" font-weight="700">RAS 扩展（TRM §9 全披露）——五款中的透明度参照系</text>
  <text x="46" y="1338" font-size="11.5" fill="#1f2937">架构化机制</text>
  <text x="406" y="1338" font-size="11.5" fill="#047857">ERR&lt;n&gt;FR/CTLR/MISC0-1+PFGF · SEA/AEA/ERI · FHI/ERI 中断 · ESB 指令 · poison 传播（64b 粒度，L1D 32b）</text>
  <text x="46" y="1357" font-size="11.5" fill="#1f2937">错误注入（§9.7）</text>
  <text x="406" y="1357" font-size="11.5" fill="#047857">CE/DE/UC/RE 四类全可注入（ERRSELR_EL1 选 record 0 + ERR0CTLR），注入不破坏真实 RAM 数据/校验逻辑</text>
  <text x="46" y="1376" font-size="11.5" fill="#1f2937">tag UC 处置</text>
  <text x="406" y="1376" font-size="11.5" fill="#1f2937">失效整行 + ERI 通知（地址/一致性态未知，无法 poison，软件被告知数据可能丢失——显式非静默）</text>
  <text x="46" y="1395" font-size="11.5" fill="#1f2937">SDC 判定基准</text>
  <text x="406" y="1395" font-size="11.5" fill="#b45309">TRM §9.1 直接给出 SDC 定义（silent data corruptions）——本仓库 SDC 判定基准的引用源</text>
  <text x="46" y="1414" font-size="11.5" fill="#1f2937">明示无保护清单</text>
  <text x="406" y="1414" font-size="11.5" fill="#b91c1c">L1 BTB · GHB · BPIQ · L1 PHT · MMU replacement/biased-repl · L2 victim · L1 TLB（flops）</text>
  <text x="46" y="1433" font-size="11.5" fill="#1f2937">SED 弱点</text>
  <text x="406" y="1433" font-size="11.5" fill="#b91c1c">I$ tag parity+data SED（弱于 L1D SECDED）→ TRM 承认 SED 双位错 might cause data corruption</text>
</svg>

</div>

独有/标志性：**ETM**（指令 trace，N2/N3 改 ETE+TRBE）——五款唯一仍在用 ETM 型 trace 单元；
AArch32 EL0（A32/T32/A64，与 N2 相同；920/920f/N3 无）；
三级原子执行（near L1 → far CHI → DSU L3，N2/N3 亦有同类机制）；L2 TQ 24/36/48 项可配（五款唯一把 TQ 深度列为构建选项）；
TRM 明示无保护清单最完整（BTB/GHB/BPIQ/PHT/L2 victim/L1 TLB flops）——本组"披露透明度参照系"。

### Neoverse N2

<div align="center">

<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1480 1450" width="1480" height="1450" font-family="system-ui,'PingFang SC','Noto Sans CJK SC','Microsoft YaHei',sans-serif">
  <defs><marker id="arr" markerWidth="11" markerHeight="9" refX="9.5" refY="4.5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L11,4.5 L0,9 Z" fill="#5a6b7c"/></marker><marker id="arrC" markerWidth="11" markerHeight="9" refX="9.5" refY="4.5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L11,4.5 L0,9 Z" fill="#7c3aed"/></marker></defs>
  <rect x="0" y="0" width="1480" height="1450" fill="#ffffff"/>
  <text x="30" y="34" font-size="20" font-weight="700" fill="#1f2937">Arm Neoverse N2 微架构功能图（Armv9.0-A · 超标量乱序 · DSU-110）</text>
  <text x="30" y="56" font-size="12" fill="#6b7280">布局 = N2 增量结构：L0 MOP cache 前端金卡（五款唯一）+ SVE2 首世代 + MMUTC SED 升级。出处：Neoverse N2 TRM 102099_0003_06</text>
  <rect x="30" y="72" width="1420" height="36" rx="6" fill="#f7f9fb" stroke="#c6d2dd"/>
    <line x1="46" y1="90" x2="72" y2="90" stroke="#5a6b7c" stroke-width="2" marker-end="url(#arr)"/>
    <text x="78" y="94" font-size="11.5" fill="#1f2937">指令/数据流</text>
    <line x1="201" y1="90" x2="227" y2="90" stroke="#7c3aed" stroke-width="2" stroke-dasharray="5,3" marker-end="url(#arrC)"/>
    <text x="233" y="94" font-size="11.5" fill="#1f2937">控制流</text>
    <rect x="313" y="83" width="14" height="14" fill="#fffbeb" stroke="#b45309" stroke-width="2.6"/>
    <text x="333" y="94" font-size="11.5" fill="#1f2937">独有/标志性</text>
    <rect x="456" y="83" width="14" height="14" fill="#f9fafb" stroke="#9ca3af" stroke-width="1.3" stroke-dasharray="4,3"/>
    <text x="476" y="94" font-size="11.5" fill="#1f2937">未公开/黑盒</text>
    <line x1="599" y1="90" x2="621" y2="90" stroke="#b91c1c" stroke-width="3.5"/>
    <text x="627" y="94" font-size="11.5" fill="#1f2937">SDC 高危/无保护</text>
  <rect x="30" y="130" width="1420" height="240" rx="10" fill="#eaf2fb" stroke="#a9c9ec" stroke-width="1.5"/>
  <rect x="30" y="106" width="250" height="24" rx="5" fill="#4a5f78"/>
  <text x="41" y="123.5" font-size="14" fill="#ffffff" font-weight="600">前端 Fetch（按序 · TRM §3.1 p40）</text>
  <text x="296" y="123" font-size="11.5" fill="#4a5f78" font-style="italic">L1I 64KB 4-way 64B · iTLB 全相联（4K/16K/64K/2M 原生页）· A32/T32/A64 全译码（AArch32 全保留）</text>
  <rect x="50" y="166" width="250" height="130" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="62" y="188" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">程序流预测（§7.3 p66）</text>
  <text x="62" y="208" font-size="10.5" fill="#1f2937" text-anchor="start">BTB（taken 目标）+ 方向预测器（历史）</text>
  <text x="62" y="225" font-size="10.5" fill="#1f2937" text-anchor="start">返回栈 + 静态预测器 + 间接预测器</text>
  <text x="62" y="242" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">BTB/GHB/BIM 保护未列（Table 11-1）</text>
  <text x="62" y="259" font-size="10.5" fill="#1f2937" text-anchor="start">A32↔T32 状态切换分支也预测</text>
  <rect x="330" y="166" width="200" height="130" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="430.0" y="188" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">L1-I-cache 64KB 4-way</text>
  <text x="430.0" y="208" font-size="10.5" fill="#1f2937" text-anchor="middle">64B 行 · I$ 硬件一致性（§7.4）</text>
  <text x="430.0" y="225" font-size="10.5" fill="#047857" text-anchor="middle" font-weight="600">tag/data: SED parity（Table 11-1）</text>
  <text x="430.0" y="242" font-size="10.5" fill="#1f2937" text-anchor="middle">投机取指行为 §7.2 约束</text>
  <rect x="560" y="166" width="310" height="178" rx="7" fill="#fffbeb" stroke="#b45309" stroke-width="3"/>
  <text x="572" y="188" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">L0 MOP 缓存（§3.1 p40）</text>
  <text x="572" y="208" font-size="10.5" fill="#b45309" text-anchor="start" font-weight="600">1536 项 · 4-way 倾斜相联（skewed）</text>
  <text x="572" y="225" font-size="10.5" fill="#1f2937" text-anchor="start">存已译码+已优化指令</text>
  <text x="572" y="242" font-size="10.5" fill="#047857" text-anchor="start" font-weight="600">data: SED（Table 11-1）</text>
  <text x="572" y="259" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">弱保护 × 高命中 × 指令面</text>
  <text x="572" y="276" font-size="10.5" fill="#b45309" text-anchor="start" font-weight="600">（五款唯一 MOP 结构）</text>
  <rect x="900" y="166" width="250" height="130" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="1025.0" y="188" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">重命名 / 发射（§3.1）</text>
  <text x="1025.0" y="208" font-size="10.5" fill="#1f2937" text-anchor="middle">重命名促乱序</text>
  <text x="1025.0" y="225" font-size="10.5" fill="#1f2937" text-anchor="middle">分发至各发射队列</text>
  <text x="1025.0" y="242" font-size="10.5" fill="#b91c1c" text-anchor="middle" font-weight="600">PRF 保护未披露</text>
  <rect x="1190" y="166" width="230" height="130" rx="7" fill="#fffbeb" stroke="#b45309" stroke-width="3"/>
  <text x="1305.0" y="188" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">ETE + TRBE</text>
  <text x="1305.0" y="208" font-size="10.5" fill="#1f2937" text-anchor="middle">Embedded Trace Ext</text>
  <text x="1305.0" y="225" font-size="10.5" fill="#1f2937" text-anchor="middle">+ Trace Buffer</text>
  <text x="1305.0" y="242" font-size="10.5" fill="#1f2937" text-anchor="middle">（替代 N1 ETM 型式）</text>
  <path d="M300,230 L324,230" fill="none" stroke="#7c3aed" stroke-width="1.6" marker-end="url(#arrC)"/>
  <path d="M530,230 L554,230" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <path d="M870,230 L894,230" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <path d="M1150,230 L1174,230" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <rect x="30" y="400" width="1420" height="300" rx="10" fill="#fdf2e5" stroke="#edcba0" stroke-width="1.5"/>
  <rect x="30" y="376" width="260" height="24" rx="5" fill="#a05a2c"/>
  <text x="41" y="393.5" font-size="14" fill="#ffffff" font-weight="600">后端 OoO Execute（TRM §3.1 p41-42）</text>
  <text x="306" y="393" font-size="11.5" fill="#a05a2c" font-style="italic">整数执行 + 向量执行（FPU · NEON · SVE/SVE2 128b 向量长度 · Crypto 可选含 SM3/SM4）</text>
  <rect x="50" y="436" width="290" height="150" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="62" y="458" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">整数执行单元</text>
  <text x="62" y="478" font-size="10.5" fill="#1f2937" text-anchor="start">· 算术/逻辑数据处理（§3.1）</text>
  <text x="62" y="495" font-size="10.5" fill="#1f2937" text-anchor="start">· RNG 支持（§16，RNDR/RNDRRS）</text>
  <text x="62" y="512" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">· ALU 数据通路无保护披露</text>
  <rect x="370" y="436" width="350" height="178" rx="7" fill="#fffbeb" stroke="#b45309" stroke-width="3"/>
  <text x="382" y="458" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">向量执行：SVE / SVE2（§14）</text>
  <text x="382" y="478" font-size="10.5" fill="#1f2937" text-anchor="start">· 向量长度 128-bit（与 NEON 等宽，非宽向量）</text>
  <text x="382" y="495" font-size="10.5" fill="#1f2937" text-anchor="start">· SVE2 全集：predication/gather/permute</text>
  <text x="382" y="512" font-size="10.5" fill="#b45309" text-anchor="start" font-weight="600">· 五款 Neoverse 侧第一个 SVE 世代（920f 为 512b）</text>
  <rect x="750" y="436" width="330" height="178" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="762" y="458" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">Crypto 扩展（可选 · §3.1）</text>
  <text x="762" y="478" font-size="10.5" fill="#1f2937" text-anchor="start">· AES · SHA-1/224/256/384/512</text>
  <text x="762" y="495" font-size="10.5" fill="#1f2937" text-anchor="start">· SM3/SM4（v8.2-SM）· 有限域（GCM/ECC）</text>
  <text x="762" y="512" font-size="10.5" fill="#6b7280" text-anchor="start">· 独立授权许可（实现时可含/不含）</text>
  <rect x="1120" y="436" width="300" height="150" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="1132" y="458" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">LSU + L1D（§8 p69-72）</text>
  <text x="1132" y="478" font-size="10.5" fill="#047857" text-anchor="start">· L1D 64KB 4-way 64B · tag/data SECDED</text>
  <text x="1132" y="495" font-size="10.5" fill="#1f2937" text-anchor="start">· 独占监视器（§8.3）· DC ZVA 64B</text>
  <text x="1132" y="512" font-size="10.5" fill="#b45309" text-anchor="start" font-weight="600">· write streaming（read allocate）L1+L2 双级（§8.5）</text>
  <path d="M340,510 L364,510" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <path d="M720,510 L744,510" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <rect x="30" y="730" width="1420" height="240" rx="10" fill="#eaf6ee" stroke="#a9d9bc" stroke-width="1.5"/>
  <rect x="30" y="706" width="150" height="24" rx="5" fill="#3f7a58"/>
  <text x="41" y="723.5" font-size="14" fill="#ffffff" font-weight="600">预取 + MMU</text>
  <text x="196" y="723" font-size="11.5" fill="#3f7a58" font-style="italic">两级 TLB + MMUTC SED（Table 6-1 p57-58）</text>
  <rect x="50" y="766" width="360" height="130" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="62" y="788" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">预取器（§8.4）</text>
  <text x="62" y="808" font-size="10.5" fill="#1f2937" text-anchor="start">load 侧 VA → L1+L2 · store 侧 PA → 仅 L2（分裂式）</text>
  <text x="62" y="825" font-size="10.5" fill="#1f2937" text-anchor="start">+ TLB 预取器 · region 预取器（CPUECTLR 可控）</text>
  <rect x="440" y="766" width="480" height="178" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="452" y="788" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">MMU：两级 TLB + MMUTC（§6.1）</text>
  <text x="452" y="808" font-size="10.5" fill="#1f2937" text-anchor="start">· iTLB 48 项全相联 · dTLB 44 项全相联 · L2 TLB 1280 项 5-way I/D 共享</text>
  <text x="452" y="825" font-size="10.5" fill="#1f2937" text-anchor="start">· TRBE TLB 2 项 · 翻译表预取器（ECtlR 可关）· L2 命中 +3c 罚</text>
  <text x="452" y="842" font-size="10.5" fill="#b45309" text-anchor="start" font-weight="600">· MMUTC：SED（Table 11-1）——N1 仅 2-bit 交错 parity，N2 升级</text>
  <rect x="950" y="766" width="470" height="150" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="962" y="788" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">观测单元</text>
  <text x="962" y="808" font-size="10.5" fill="#1f2937" text-anchor="start">48-bit PA · PMU 6 计数器（§3.1 p42）</text>
  <text x="962" y="825" font-size="10.5" fill="#1f2937" text-anchor="start">SPE（v8.4 可选实现）· AMU</text>
  <text x="962" y="842" font-size="10.5" fill="#1f2937" text-anchor="start">GIC CPU 接口 · RNG</text>
  <text x="962" y="859" font-size="10.5" fill="#6b7280" text-anchor="start">Debug/ELA 可选（§2.5）</text>
  <rect x="30" y="1010" width="1420" height="240" rx="10" fill="#f1edfb" stroke="#cfc0ef" stroke-width="1.5"/>
  <rect x="30" y="986" width="250" height="24" rx="5" fill="#6d5aa0"/>
  <text x="41" y="1003.5" font-size="14" fill="#ffffff" font-weight="600">内存层级（L1 → L2 → DSU-110）</text>
  <text x="296" y="1003" font-size="11.5" fill="#6d5aa0" font-style="italic">异步 CPU bridge 连 DSU-110（缓冲+同步核与簇）· 组件常在（All components always present §3）</text>
  <rect x="50" y="1046" width="330" height="178" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="215.0" y="1068" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">L1-Dcache 64KB 4-way</text>
  <text x="215.0" y="1088" font-size="10.5" fill="#1f2937" text-anchor="middle">64B 行（§3.1 p42）</text>
  <text x="215.0" y="1105" font-size="10.5" fill="#047857" text-anchor="middle" font-weight="600">tag/data: SECDED（Table 11-1）</text>
  <text x="215.0" y="1122" font-size="10.5" fill="#1f2937" text-anchor="middle">双位错=检出/上报/延迟</text>
  <text x="215.0" y="1139" font-size="10.5" fill="#1f2937" text-anchor="middle">dirty 行双位错→数据可能丢失（显式）</text>
  <rect x="410" y="1046" width="330" height="178" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="575.0" y="1068" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">L2 私有 512KB/1024KB 8-way</text>
  <text x="575.0" y="1088" font-size="10.5" fill="#1f2937" text-anchor="middle">统一 I+D（§3.1 p42 · §9）</text>
  <text x="575.0" y="1105" font-size="10.5" fill="#047857" text-anchor="middle" font-weight="600">tag/data: SECDED</text>
  <text x="575.0" y="1122" font-size="10.5" fill="#047857" text-anchor="middle" font-weight="600">L2 TQ：SECDED（表 11-1 唯一队列类保护）</text>
  <text x="575.0" y="1139" font-size="10.5" fill="#1f2937" text-anchor="middle">victim 表未列（N1 明示 None，N2 未披露）</text>
  <rect x="770" y="1046" width="330" height="178" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="935.0" y="1068" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">DSU-110 簇</text>
  <text x="935.0" y="1088" font-size="10.5" fill="#1f2937" text-anchor="middle">L3/SCU/snoop filter = DSU TRM 范围</text>
  <text x="935.0" y="1105" font-size="10.5" fill="#1f2937" text-anchor="middle">CPU bridge 异步（频/电/面积解耦）</text>
  <text x="935.0" y="1122" font-size="10.5" fill="#1f2937" text-anchor="middle">DSU 依赖特性见 TRM §2.3</text>
  <rect x="1130" y="1046" width="290" height="130" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="1275.0" y="1068" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">SoC 侧</text>
  <text x="1275.0" y="1088" font-size="10.5" fill="#1f2937" text-anchor="middle">48-bit PA</text>
  <text x="1275.0" y="1105" font-size="10.5" fill="#1f2937" text-anchor="middle">GIC CPU 接口</text>
  <text x="1275.0" y="1122" font-size="10.5" fill="#1f2937" text-anchor="middle">RNG · Debug/ELA</text>
  <rect x="30" y="1290" width="1420" height="160" rx="10" fill="#f0fdf4" stroke="#047857" stroke-width="2"/>
  <text x="46" y="1316" font-size="15" fill="#047857" font-weight="700">RAS 扩展（TRM §11 p96-100）——含至 Armv9.0-A 全量</text>
  <text x="46" y="1338" font-size="11.5" fill="#1f2937">保护矩阵（Table 11-1）</text>
  <text x="406" y="1338" font-size="11.5" fill="#047857">SECDED = L1D tag/data · L2 tag/data · L2 TQ；SED = L1I tag/data · L0 MOP · MMUTC</text>
  <text x="46" y="1357" font-size="11.5" fill="#1f2937">TRM 原文承认</text>
  <text x="406" y="1357" font-size="11.5" fill="#b91c1c">SED RAM 双位错 core does not detect … might cause data corruption——I$/MOP/MMUTC 是承认的 SDC 通道</text>
  <text x="46" y="1376" font-size="11.5" fill="#1f2937">错误遏制（§11.2）</text>
  <text x="406" y="1376" font-size="11.5" fill="#1f2937">数据错误经 poison 传播不静默扩散 · evict 双错可 poison · L1D/L2 tag 不可遏制错误（UC 声明）</text>
  <text x="46" y="1395" font-size="11.5" fill="#1f2937">错误注入（§11.5）</text>
  <text x="406" y="1395" font-size="11.5" fill="#047857">CE（L1D 单 ECC）· DE（L1→L2 evict 双 ECC / snoop）· UC（L1 tag evict 后双 ECC）· ERR0PFGCDN 倒计数</text>
  <text x="46" y="1414" font-size="11.5" fill="#1f2937">报告机制</text>
  <text x="406" y="1414" font-size="11.5" fill="#047857">FHI=nCOREFAULTIRQ · ERI=nCOREERRIRQ · 消费时 SEA/AEA/ERI · MEMORY_ERROR PMU 事件联动 · ESB · Node 0=L1+L2</text>
  <text x="46" y="1433" font-size="11.5" fill="#1f2937">SDC 视角</text>
  <text x="406" y="1433" font-size="11.5" fill="#b45309">N2 相对 N1 的增量 = MMUTC SED + MOP SED；新增 MOP 是弱保护×高命中率×指令面三重叠加的独立注入靶点</text>
</svg>

</div>

独有/标志性：**L0 MOP 缓存 1536 项 4-way skewed**（存已译码优化指令，SED 弱保护×高命中×指令面，五款唯一 MOP）；
**MMUTC 拉进 SED**（N1 仅 2-bit 交错 parity）；AArch32 EL0（A32/T32/A64，与 N1 相同）；write streaming L1+L2 双级；
load VA / store PA 分裂预取器（N3 改为 VA+PC 双源引擎）。

### Neoverse N3

<div align="center">

<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1480 1450" width="1480" height="1450" font-family="system-ui,'PingFang SC','Noto Sans CJK SC','Microsoft YaHei',sans-serif">
  <defs><marker id="arr" markerWidth="11" markerHeight="9" refX="9.5" refY="4.5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L11,4.5 L0,9 Z" fill="#5a6b7c"/></marker><marker id="arrC" markerWidth="11" markerHeight="9" refX="9.5" refY="4.5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L11,4.5 L0,9 Z" fill="#7c3aed"/></marker></defs>
  <rect x="0" y="0" width="1480" height="1450" fill="#ffffff"/>
  <text x="30" y="34" font-size="20" font-weight="700" fill="#1f2937">Arm Neoverse N3 微架构功能图（Armv9.2-A · 平衡性能核 · DSU-120 Direct connect）</text>
  <text x="30" y="56" font-size="12" fill="#6b7280">布局 = N3 防御结构：分裂式 L2 TLB（small 1536 + medium 256）+ aux tag + ECC granule 可配 + MPAM。出处：Neoverse N3 TRM 107997_0001_03</text>
  <rect x="30" y="72" width="1420" height="36" rx="6" fill="#f7f9fb" stroke="#c6d2dd"/>
    <line x1="46" y1="90" x2="72" y2="90" stroke="#5a6b7c" stroke-width="2" marker-end="url(#arr)"/>
    <text x="78" y="94" font-size="11.5" fill="#1f2937">指令/数据流</text>
    <line x1="201" y1="90" x2="227" y2="90" stroke="#7c3aed" stroke-width="2" stroke-dasharray="5,3" marker-end="url(#arrC)"/>
    <text x="233" y="94" font-size="11.5" fill="#1f2937">控制流</text>
    <rect x="313" y="83" width="14" height="14" fill="#fffbeb" stroke="#b45309" stroke-width="2.6"/>
    <text x="333" y="94" font-size="11.5" fill="#1f2937">独有/标志性</text>
    <rect x="456" y="83" width="14" height="14" fill="#f9fafb" stroke="#9ca3af" stroke-width="1.3" stroke-dasharray="4,3"/>
    <text x="476" y="94" font-size="11.5" fill="#1f2937">未公开/黑盒</text>
    <line x1="599" y1="90" x2="621" y2="90" stroke="#b91c1c" stroke-width="3.5"/>
    <text x="627" y="94" font-size="11.5" fill="#1f2937">SDC 高危/无保护</text>
  <rect x="30" y="130" width="1420" height="240" rx="10" fill="#eaf2fb" stroke="#a9c9ec" stroke-width="1.5"/>
  <rect x="30" y="106" width="240" height="24" rx="5" fill="#4a5f78"/>
  <text x="41" y="123.5" font-size="14" fill="#ffffff" font-weight="600">前端 Fetch（按序 · TRM §2.1 p31）</text>
  <text x="286" y="123" font-size="11.5" fill="#4a5f78" font-style="italic">L1I 32KB 或 64KB（可配）4-way 64B · iTLB 全相联 32 项 · 仅 A64 译码（无 AArch32）· 动态分支预测器单列组件</text>
  <rect x="50" y="166" width="260" height="130" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="62" y="188" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">程序流预测（§6.3 p59）</text>
  <text x="62" y="208" font-size="10.5" fill="#1f2937" text-anchor="start">BTB + BP 方向预测器（历史）</text>
  <text x="62" y="225" font-size="10.5" fill="#1f2937" text-anchor="start">返回栈（BL/BLR* push · RET* pop）</text>
  <text x="62" y="242" font-size="10.5" fill="#1f2937" text-anchor="start">静态 + 间接预测器</text>
  <text x="62" y="259" font-size="10.5" fill="#1f2937" text-anchor="start">不预测：ERET/SVC/HVC/SMC</text>
  <rect x="340" y="166" width="230" height="130" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="455.0" y="188" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">L1-I-cache 32/64KB 4-way</text>
  <text x="455.0" y="208" font-size="10.5" fill="#1f2937" text-anchor="middle">64B 行（§2.1 · §1.2 可配）</text>
  <text x="455.0" y="225" font-size="10.5" fill="#047857" text-anchor="middle" font-weight="600">tag/data: SED（Table 10-1）</text>
  <text x="455.0" y="242" font-size="10.5" fill="#1f2937" text-anchor="middle">硬件一致性 §6.4（与 L2 弱包含）</text>
  <rect x="600" y="166" width="220" height="130" rx="7" fill="#fffbeb" stroke="#b45309" stroke-width="3"/>
  <text x="710.0" y="188" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">译码（§2.1）</text>
  <text x="710.0" y="208" font-size="10.5" fill="#b45309" text-anchor="middle" font-weight="600">仅 A64（无 A32/T32）</text>
  <text x="710.0" y="225" font-size="10.5" fill="#1f2937" text-anchor="middle">AArch64 内部格式</text>
  <text x="710.0" y="242" font-size="10.5" fill="#1f2937" text-anchor="middle">无 MOP 结构（N2 删减）</text>
  <rect x="850" y="166" width="220" height="130" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="960.0" y="188" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">重命名 / 发射</text>
  <text x="960.0" y="208" font-size="10.5" fill="#1f2937" text-anchor="middle">重命名 + issue queues</text>
  <text x="960.0" y="225" font-size="10.5" fill="#1f2937" text-anchor="middle">（§2.1 组件图）</text>
  <text x="960.0" y="242" font-size="10.5" fill="#b91c1c" text-anchor="middle" font-weight="600">PRF 保护未披露</text>
  <rect x="1100" y="166" width="320" height="130" rx="7" fill="#fffbeb" stroke="#b45309" stroke-width="3"/>
  <text x="1112" y="188" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">MPAM（§1.1 Cache features）</text>
  <text x="1112" y="208" font-size="10.5" fill="#1f2937" text-anchor="start">Memory System Resource</text>
  <text x="1112" y="225" font-size="10.5" fill="#1f2937" text-anchor="start">Partitioning &amp; Monitoring</text>
  <text x="1112" y="242" font-size="10.5" fill="#1f2937" text-anchor="start">缓存/带宽 QoS 硬件分区</text>
  <text x="1112" y="259" font-size="10.5" fill="#6b7280" text-anchor="start">（920 平台级 MPAM 有 ACPI 表；N3 为核内特性）</text>
  <path d="M310,230 L334,230" fill="none" stroke="#7c3aed" stroke-width="1.6" marker-end="url(#arrC)"/>
  <path d="M570,230 L594,230" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <path d="M820,230 L844,230" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <rect x="30" y="400" width="1420" height="300" rx="10" fill="#fdf2e5" stroke="#edcba0" stroke-width="1.5"/>
  <rect x="30" y="376" width="260" height="24" rx="5" fill="#a05a2c"/>
  <text x="41" y="393.5" font-size="14" fill="#ffffff" font-weight="600">后端 OoO Execute（§2.1 p31-32）</text>
  <text x="306" y="393" font-size="11.5" fill="#a05a2c" font-style="italic">整数执行 + 向量执行（NEON+FP · SVE/SVE2 128b · Crypto 可选含 SHA-3/SM3/SM4）· 平衡性能/低功耗/面积受限定位</text>
  <rect x="50" y="436" width="290" height="150" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="62" y="458" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">整数执行单元</text>
  <text x="62" y="478" font-size="10.5" fill="#1f2937" text-anchor="start">· 算术/逻辑数据处理（§2.1）</text>
  <text x="62" y="495" font-size="10.5" fill="#1f2937" text-anchor="start">· RNG（§16）· Utility bus（§11）</text>
  <text x="62" y="512" font-size="10.5" fill="#b91c1c" text-anchor="start" font-weight="600">· ALU 数据通路无保护披露</text>
  <rect x="370" y="436" width="350" height="178" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="382" y="458" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">向量执行：SVE / SVE2（§14）</text>
  <text x="382" y="478" font-size="10.5" fill="#1f2937" text-anchor="start">· 向量长度 128-bit · NEON+FP32/FP64</text>
  <text x="382" y="495" font-size="10.5" fill="#1f2937" text-anchor="start">· Crypto：AES · SHA-1/2 · SHA-3 · SM3/SM4</text>
  <text x="382" y="512" font-size="10.5" fill="#1f2937" text-anchor="start">· EOR3/XAR/BCAX 随 SVE2 免费（免 Crypto 授权）</text>
  <rect x="750" y="436" width="350" height="178" rx="7" fill="#fffbeb" stroke="#b45309" stroke-width="3"/>
  <text x="762" y="458" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">L2 预取引擎（VA + PC 双源）</text>
  <text x="762" y="478" font-size="10.5" fill="#1f2937" text-anchor="start">· §8 L2 内存系统：虚拟地址 + 程序计数器</text>
  <text x="762" y="495" font-size="10.5" fill="#1f2937" text-anchor="start">· 各引擎分别向 L2 预取（next-line/stride 类）</text>
  <text x="762" y="512" font-size="10.5" fill="#b45309" text-anchor="start" font-weight="600">· N2 为 load VA / store PA 分裂预取，N3 改双源引擎</text>
  <rect x="1130" y="436" width="290" height="150" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="1275.0" y="458" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">观测单元</text>
  <text x="1275.0" y="478" font-size="10.5" fill="#b45309" text-anchor="middle" font-weight="600">PMU 6 或 20 计数器（可配）</text>
  <text x="1275.0" y="495" font-size="10.5" fill="#1f2937" text-anchor="middle">SPE（§22 v8.7）· ETE+TRBE</text>
  <text x="1275.0" y="512" font-size="10.5" fill="#1f2937" text-anchor="middle">AMU（§21）· ELA 组件化</text>
  <path d="M340,510 L364,510" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <path d="M720,510 L744,510" fill="none" stroke="#5a6b7c" stroke-width="1.6" marker-end="url(#arr)"/>
  <rect x="30" y="730" width="1420" height="240" rx="10" fill="#eaf6ee" stroke="#a9d9bc" stroke-width="1.5"/>
  <rect x="30" y="706" width="250" height="24" rx="5" fill="#3f7a58"/>
  <text x="41" y="723.5" font-size="14" fill="#ffffff" font-weight="600">访存 + MMU（分裂式 L2 TLB）</text>
  <text x="296" y="723" font-size="11.5" fill="#3f7a58" font-style="italic">L1D 32/64KB 可配 4-way 64B · tag/data/aux tag 全 SECDED · LSE 原子在 L1 内存系统实现（§7.3）</text>
  <rect x="50" y="766" width="360" height="178" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="62" y="788" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">LSU + L1D（§7 p62-65）</text>
  <text x="62" y="808" font-size="10.5" fill="#1f2937" text-anchor="start">· L1D 32/64KB（可配）4-way 64B</text>
  <text x="62" y="825" font-size="10.5" fill="#047857" text-anchor="start" font-weight="600">· tag/data/aux tag 全 SECDED</text>
  <text x="62" y="842" font-size="10.5" fill="#1f2937" text-anchor="start">· LSE 原子在 L1 内存系统实现（§7.3）</text>
  <text x="62" y="859" font-size="10.5" fill="#1f2937" text-anchor="start">· 独占监视器（§7.4）· write streaming（§7.2）</text>
  <text x="62" y="876" font-size="10.5" fill="#6b7280" text-anchor="start">· 预取（§7.5）</text>
  <rect x="440" y="766" width="480" height="178" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="452" y="788" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">MMU：分裂式 L2 TLB + walk cache（§5.1 p50 Table 5-1）</text>
  <text x="452" y="808" font-size="10.5" fill="#1f2937" text-anchor="start">· iTLB 32 项 · dTLB 48 项（全相联）· SPE TLB 1 项 · TRBE TLB 1 项</text>
  <text x="452" y="825" font-size="10.5" fill="#b45309" text-anchor="start" font-weight="600">· small-page TLB（4K/16K/64K）：6-way 1536 项（reduced-area 4-way 1024）</text>
  <text x="452" y="842" font-size="10.5" fill="#b45309" text-anchor="start" font-weight="600">· medium-page TLB（2M/32M/512M）：4-way 256 项 + walk cache</text>
  <text x="452" y="859" font-size="10.5" fill="#047857" text-anchor="start" font-weight="600">· TLB：SED（Table 10-1，措辞从 N2 的 MMUTC 升级为 TLB）</text>
  <rect x="950" y="766" width="470" height="150" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="962" y="788" font-size="13" fill="#1f2937" text-anchor="start" font-weight="700">内存层级补充</text>
  <text x="962" y="808" font-size="10.5" fill="#1f2937" text-anchor="start">单核 Direct connect 配置无 L3/SCU/snoop filter（§1 图 1-1）</text>
  <text x="962" y="825" font-size="10.5" fill="#1f2937" text-anchor="start">CPU bridge 连 DSU-120</text>
  <text x="962" y="842" font-size="10.5" fill="#1f2937" text-anchor="start">48-bit VA/PA（§1.1）</text>
  <rect x="30" y="1010" width="1420" height="240" rx="10" fill="#f1edfb" stroke="#cfc0ef" stroke-width="1.5"/>
  <rect x="30" y="986" width="320" height="24" rx="5" fill="#6d5aa0"/>
  <text x="41" y="1003.5" font-size="14" fill="#ffffff" font-weight="600">内存层级（L1 → L2 → DSU-120 Direct connect）</text>
  <text x="366" y="1003" font-size="11.5" fill="#6d5aa0" font-style="italic">单核 Direct connect 配置无 L3/SCU/snoop filter · CPU bridge 连 DSU-120</text>
  <rect x="50" y="1046" width="350" height="178" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="225.0" y="1068" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">L1-Dcache 32/64KB 4-way</text>
  <text x="225.0" y="1088" font-size="10.5" fill="#1f2937" text-anchor="middle">64B 行（§2.1 · §9.1 编码验证 4-way）</text>
  <text x="225.0" y="1105" font-size="10.5" fill="#047857" text-anchor="middle" font-weight="600">tag/data: SECDED</text>
  <text x="225.0" y="1122" font-size="10.5" fill="#b45309" text-anchor="middle" font-weight="600">aux tag: SECDED（Table 10-1 新增行）</text>
  <text x="225.0" y="1139" font-size="10.5" fill="#1f2937" text-anchor="middle">UC 双位错=检出并上报/延迟（显式非静默）</text>
  <rect x="430" y="1046" width="380" height="178" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="620.0" y="1068" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">L2 私有 128KB–2MB 8-way 2-bank</text>
  <text x="620.0" y="1088" font-size="10.5" fill="#1f2937" text-anchor="middle">PIPT · 动态偏置替换策略（Table 8-1）</text>
  <text x="620.0" y="1105" font-size="10.5" fill="#047857" text-anchor="middle" font-weight="600">tag/data: SECDED · TQ 亦 SECDED</text>
  <text x="620.0" y="1122" font-size="10.5" fill="#b45309" text-anchor="middle" font-weight="600">ECC granule 可配 128/256 bit（§1.2）</text>
  <text x="620.0" y="1139" font-size="10.5" fill="#b45309" text-anchor="middle" font-weight="600">五款唯一可配纠错粒度</text>
  <rect x="840" y="1046" width="300" height="178" rx="7" fill="#fffbeb" stroke="#b45309" stroke-width="3"/>
  <text x="990.0" y="1068" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">DSU-120（Direct connect）</text>
  <text x="990.0" y="1088" font-size="10.5" fill="#b45309" text-anchor="middle" font-weight="600">CHI Issue E 接口</text>
  <text x="990.0" y="1105" font-size="10.5" fill="#b45309" text-anchor="middle" font-weight="600">256-bit 读/写通道宽</text>
  <text x="990.0" y="1122" font-size="10.5" fill="#1f2937" text-anchor="middle">单核配置：无 L3 / 无 SCU</text>
  <text x="990.0" y="1139" font-size="10.5" fill="#1f2937" text-anchor="middle">（L3 保护 = DSU TRM 范围）</text>
  <rect x="1170" y="1046" width="250" height="130" rx="7" fill="#ffffff" stroke="#7c93a8" stroke-width="1.5"/>
  <text x="1295.0" y="1068" font-size="13" fill="#1f2937" text-anchor="middle" font-weight="700">SoC 侧</text>
  <text x="1295.0" y="1088" font-size="10.5" fill="#1f2937" text-anchor="middle">48-bit VA/PA（§1.1）</text>
  <text x="1295.0" y="1105" font-size="10.5" fill="#1f2937" text-anchor="middle">GIC CPU 接口 · RNG</text>
  <text x="1295.0" y="1122" font-size="10.5" fill="#1f2937" text-anchor="middle">ELA-600 可选（§1.2）</text>
  <rect x="30" y="1290" width="1420" height="160" rx="10" fill="#f0fdf4" stroke="#047857" stroke-width="2"/>
  <text x="46" y="1316" font-size="15" fill="#047857" font-weight="700">RAS 扩展（TRM §10 p76-80）——含至 Armv9.2-A · 五款中防御矩阵最厚</text>
  <text x="46" y="1338" font-size="11.5" fill="#1f2937">保护矩阵（Table 10-1）</text>
  <text x="406" y="1338" font-size="11.5" fill="#047857">SECDED = L1D tag / aux tag / data · L2 tag/data · L2 TQ；SED = L1I tag/data · TLB（措辞从 N2 的 MMUTC 升级为 TLB）</text>
  <text x="46" y="1357" font-size="11.5" fill="#1f2937">错误遏制（§10.2）</text>
  <text x="406" y="1357" font-size="11.5" fill="#1f2937">poison 传播 + evict 双错 poison + ESB 隔离不精确异常 · L1D/L2 tag UC 不可遏制声明与 N2 一致</text>
  <text x="46" y="1376" font-size="11.5" fill="#1f2937">错误注入（§10.5）</text>
  <text x="406" y="1376" font-size="11.5" fill="#047857">CE（L1D 单 ECC）· DE（L1→L2 evict/snoop 双 ECC）· UC（L1 和 L2 tag evict 后双 ECC——比 N2 的仅 L1 tag 扩展）</text>
  <text x="46" y="1395" font-size="11.5" fill="#1f2937">寄存器风格</text>
  <text x="406" y="1395" font-size="11.5" fill="#b45309">带 _EL1 后缀（ER1PFGCDN_EL1，RASv1.1 风格）· FHI/ERI · SEA/AEA/ERI · MEMORY_ERROR PMU 事件</text>
  <text x="46" y="1414" font-size="11.5" fill="#1f2937">Node 0 覆盖</text>
  <text x="406" y="1414" font-size="11.5" fill="#b45309">明确覆盖 L1 + L2 + MMU/TLB（N2 为 L1+L2；N3 把地址翻译部件纳入 RAS 节点）</text>
  <text x="46" y="1433" font-size="11.5" fill="#1f2937">SDC 视角</text>
  <text x="406" y="1433" font-size="11.5" fill="#047857">披露范围内相对敏感性最低——TLB/翻译路径在 N3 获 SED；残余弱点：SED 类双位错仍是 corruption 通道；执行单元/PRF/LSQ 依旧无披露</text>
</svg>

</div>

独有/标志性：**分裂式 L2 TLB**（small-page 1536 项 6-way + medium-page 256 项 4-way + walk cache）；
**TLB 整体 SED**（N2 仅 MMUTC）；**L1D aux tag SECDED**（新增披露行）；L2 ECC granule 128/256b 可配（注意：比 N1/N2 的 64b 码字更粗，UC poison 波及面更大，但为五款唯一可配）；
MPAM（N2 亦有 FEAT_MPAM）；CHI Issue E 256-bit 接口（N2 同款）；PMU 6/20 计数器可配（五款唯一 PMU 深度构建选项）；RAS Node 0 明确覆盖 MMU/TLB；
无 MOP 结构（相对 N2 删减）——披露范围内 SDC 防御最厚。

---

## 2. 纵轴分类体系（体系结构公认分层）

```
A. 指令供给前端 (Instruction Frontend)
   A1 指令缓存 L1I$        A2 分支预测 (BTB/方向预测器/RAS/间接预测)
   A3 译码与 µop 缓存      A4 指令 TLB (ITLB)
B. 乱序执行引擎 (OoO Core)
   B1 寄存器重命名 ( Rename / PRF )   B2 调度器 (Issue Queue)
   B3 ROB / 提交           B4 执行单元 (INT/FP/向量)
C. 访存与数据通路 (Memory Pipeline)
   C1 AGU / LSU / Store Buffer   C2 原子与同步单元
   C3 数据预取器
D. 缓存层次 (Cache Hierarchy)
   D1 L1D$      D2 L2$ (私有)     D3 L3/SLC (共享)    D4 一致性协议/目录
E. 地址转换 (Address Translation)
   E1 DTLB / L2 TLB    E2 MMU 翻译缓存/页表遍历
F. 可靠性/ RAS 与错误处理 (Reliability)
   F1 RAM 保护 (ECC/parity 矩阵)   F2 架构化 RAS (寄存器/异常/ESB/poison)
   F3 错误注入    F4 平台 RAS 栈 (ACPI/EDAC)
```

以下各节即按此纵轴逐层展开，每层一张「部件 × 5 芯片」表。

---

## 2.5 全单元微架构大对比总表（五款 × 全部件速查）

> 本表是 §1.5 五张功能图（`figures/sdc-fig-*.svg`）与 §3–§8 各分表的**全景汇总**：
> 纵轴为微架构逻辑单元，分组与功能图完全一致（取指与前段 Fetch → OoO 译码/重命名/分发 → IEX → LSU → FSU → MMU → L2/一致性，末行 RAS 总线跨组）；
> 横轴为五款处理器。**单元格事实与出处均见对应章节（§3 前端 / §4 乱序引擎 / §5 访存 / §6 缓存 / §7 地址转换 / §8 RAS），本表不引入新数据**；★ = 该行中独有/标志性设计（与 §1.5 定义一致）。

| 分组 | 单元 | Kunpeng 920 (TSV110) | 920f (0xd22) | Neoverse N1 | Neoverse N2 | Neoverse N3 |
|---|---|---|---|---|---|---|
| **Fetch 取指与前段** | IFU 取指宽度 | 4 条/周期 | 未公开 | 超标量（宽度未披露） | 超标量（宽度未披露） | 超标量（宽度未披露） |
| | BRE 分支方向预测 | 两级动态（≈A73 水平） | 未测（bpbench 未完成） | 动态预测器 | 分支方向预测器（历史） | 方向预测器（历史） |
| | BP / BTB | L1 64 项；L2 ~2048 项 | 未测 | BTB 容量未披露 | BTB 容量未披露 | BTB 容量未披露 |
| | 返回栈 RAS | 31–32 项 | 未测 | 有 | 有 | 有（BL/BLR* push；RET* pop） |
| | µop / MOP cache | 无（代码溢出 L1i 后带宽 4→0.25 条/cyc） | 未披露 | 无此结构 | ★ L0 MOP 1536 项 4-way skewed（data SED） | 无（相对 N2 删减） |
| | L1-I-TLB | 32 项全相联 | 未测 | 48 项全相联 | 48 项全相联 | 32 项全相联 |
| | L1-I-cache | 64KB 4-way AIVIVT | 32KB 4-way | 64KB 4-way | 64KB 4-way | 32/64KB（可配）4-way |
| | I$ RAM 保护 | 声称 ECC（无架构化证据） | 未披露 | tag parity + data SED | tag+data SED | tag+data SED |
| **OoO 译码·重命名·分发** | Int Decode | 4 宽 | 未公开 | A32/T32/A64 | A32/T32/A64 | 仅 A64 |
| | Int Rename | PRF ~128 项 | 未公开 | 未披露 | 未披露 | 未披露 |
| | Int Dispatch（ROB 提交） | ROB ~128（实测有效 108–110） | 未测 | 128（公开规格） | 未披露 | 未披露 |
| | FP/SIMD decode·rename·dispatch | 2×FP 管线 | SVE512 译码 | NEON 128b | SVE2 128b | SVE2 128b |
| | 调度器 Issue Queue | ALU/LS/FP 三类统一式，各 ~33 项 | 未测 | issue queues（容量未给） | issue queues | issue queues |
| | 乱序引擎保护 | 无（RAS=0） | 未披露 | 无披露 | 无披露 | 无披露 |
| **IEX 整数执行** | ALU Issue Queue ×3 | 各 ~33 项 | 未公开 | 未披露 | 未披露 | 未披露 |
| | Int PRF | ~128 项；Flag rename ~31 | 未公开 | 未披露 | 未披露 | 未披露 |
| | ALU ×3 | 分支可占 2 ALU，1 taken/cyc | 未公开 | INT 执行单元 | INT 执行单元 | INT 执行单元 |
| | MDU 乘除 | 乘 4 / 除 19（udiv 小商早退 6.2） | 未公开 | 未披露 | 未披露 | 未披露 |
| | MSR/CP15 系统寄存器 | 有 | 有 | 系统寄存器 | 系统寄存器 | 系统寄存器 |
| | 执行单元保护 | 无公开信息 | 未披露 | 无披露 | 无披露 | 无披露 |
| **LSU 访存** | LSU MDU/SYS Issue Queue | ~33 项 | 未公开 | 未披露 | 未披露 | 未披露 |
| | LS×2 / STD×2（AGU/store） | 2×AGU：2 load 或 1L+1S /cyc；store→load 转发 6–7 cyc | 未测 | load/store 单元 | LSU | LSU |
| | L1-DTLB | 32 项全相联 | 未测（64KB 强制页 → 波及面 ×16） | 48 项全相联 | 44 项全相联 | 48 项全相联 |
| | L1-Dcache | 64KB 4-way，load-to-use 4 cyc | 32KB 8-way（~10 cyc） | 64KB 4-way | 64KB 4-way | 32/64KB 4-way |
| | L1D / L1 TLB 保护 | ECC 声称无证据 | 未披露 | D$ SECDED（42b+7；32b+1 poison）；L1 TLB = flops 无保护 | D$ SECDED；MMUTC SED | D$ SECDED + ★ aux tag SECDED；TLB SED |
| **FSU 浮点/向量** | FSU Issue Queue | ~33 项 | 未公开 | 未披露 | 未披露 | 未披露 |
| | FP/SIMD PRF | 偏小 | ★ Z0–Z31 ×512b | 128b NEON | SVE 128b | SVE 128b |
| | FSU Pipe ×2 | FP32 FMA 2/cyc；FP64 1/4 rate | SVE512 FMA ≥2/cyc（13.6 flop/cyc 下限） | NEON 128b | SVE2 128b | SVE2 128b（+SHA-3） |
| | 向量数据面保护 | 无披露 | SVE512 巨型寄存器 = 新增无保护数据面 | 无披露 | 无披露 | 无披露 |
| **MMU 地址转换** | L2 TLB | 1024 项共用（命中 +11 cyc） | 未测 | 1280 项 5-way | 1280 项 5-way | ★ 分裂：small 1536 项 6-way + medium 256 项 4-way + walk cache |
| | MMU/TLB 保护 | 无披露（RAS=0） | 未披露 | MMUTC 2-bit 交错 parity | MMUTC SED | TLB 整体 SED；RAS Node 0 覆盖 MMU/TLB |
| **L2 / 核缓存一致性** | L2 私有缓存 | 512KB 8-way 10 cyc | ★ 768KB 12-way 17 cyc | 256/512/1024KB 8-way（★ TQ 24/36/48 可配） | 512/1024KB 8-way | 128KB–2MB 8-way 2-bank PIPT |
| | L2 RAM 保护 | 声称 ECC（无证据） | 未披露 | tag+data SECDED | tag+data+TQ SECDED | SECDED（granule 128/256b 可配） |
| | L3 / LLC | 每 die 32MB SLC 15-way 128B 行，tag 在簇侧，S/P/P(默认) 三模式 | ★ 无 L3/LLC（少一级暴露面） | DSU 内可选 L3 | DSU-110 L3 | Direct connect 无 L3/SCU |
| | 互连 / 一致性 | Hydra/HHA 目录 + 跨 die 环形 NoC | HCCS（跨 socket NUMA 61–91） | DSU SCU + snoop filter | DSU-110 | DSU-120；CHI-E 256-bit |
| | 内存接口 | DDR4-2933 ×8ch | 565GB；16+16 NUMA | 48-bit PA；GICv4.1 | CHI-E 256-bit | 48-bit VA/PA；MPAM |
| **RAS 总线（跨组）** | 架构化 RAS | ✗ RAS=0（无 ERR*/ESB/poison） | ✓ RAS=1（黑盒） | 完整 RAS 扩展 | v9.0 全量 | v9.2 全量 |
| | SDC 敏感性画像（§9.2） | 最高（核内翻转无架构级可见信号） | 高（黑盒 + SVE512 新数据面） | 披露透明度参照系 | ≈N1（MOP 为独立靶点） | 披露范围内最低 |

速查要点（详见 §9）：
1. **结构覆盖面**：920f（无 LLC + SVE512）与 920（片上 SLC 三模式）是两个极端的缓存/向量组织；N2 是五款唯一带 MOP cache 的核（多一个指令面暴露点），N3 是唯一分裂式 L2 TLB。
2. **保护覆盖面**：从 920 的「RAS=0 + ECC 声称无证据」到 N3 的「TLB/aux tag/granule 全披露」，架构化防御纵深单调递增（920 < 920f(未知) < N1 ≤ N2 < N3）；但**五款的执行单元、PRF、调度器、LSQ 均无任何保护披露**——这是所有乱序核共同的 SDC 盲区（§4）。
3. **速查表用法**：行 = 注入靶点候选，列 = 平台差异；「未披露/未测」单元格即黑盒区域，FI 建模时按未知处理而非假设有保护。

---

## 3. A. 指令供给前端

### A1. L1 指令缓存

| | 920 (v110) | 920f | N1 | N2 | N3 |
|---|---|---|---|---|---|
| 容量/相联 | 64KB / 4-way / 64B | 32KB / 4-way / 64B (CTR 实测) | 64KB / 4-way / 64B | 64KB / 4-way / 64B | **32KB 或 64KB**（可配）/ 4-way / 64B |
| 索引方式 | AIVIVT（CTR_EL0.L1Ip=2，实测） | 未测 | — | — | 编码表用 VA bits[13:6]（VIPT 型） |
| 硬件一致性 | 无（DIC=0 实测） | 未测 | 可配（COHERENT_ICACHE，推荐 L2=1MB） | §7.4 支持 | BROADCASTICINVAL=1 时与 L2 弱包含 |
| ECC/保护 | 厂商宣称 ECC（无架构化证据，RAS=0） | 未披露 | tag: 1 parity bit/39b；data: SED/72b；错误→行失效重取 | tag+data: SED parity | tag+data: SED parity |

SDC 视角：L1I 属**指令面**——翻转直接改变被执行的指令流，是 SDC 的**最高危入口之一**；但 N1/N2/N3 的 SED 仅检单比特，TRM 原文（N2 §11.1）：SED RAM 双位错误「core does not detect … might cause data corruption」——**架构层面承认 I$ 双位翻转可致 SDC**。SED 检出后的恢复策略是失效重取（无数据丢失），这比 L1D 的 poison 更干净。920 的 RAS=0 意味着其 ECC 声称无法用标准 ERR 寄存器验证，I$ 保护强度**未知**。

### A2. 分支预测

| | 920 | 920f | N1 | N2 | N3 |
|---|---|---|---|---|---|
| BTB | L1 64 项；L2 ~2048 项 | 未测 | BTB（容量未披露） | BTB（容量未披露） | BTB（容量未披露） |
| 方向预测器 | 两级动态（≈A73 水平） | 待测（bpbench 未完成） | 动态预测器 | 分支方向预测器（历史） | BP 预测器（历史） |
| 返回栈 RAS | 31–32 项 | 未测 | 有 | 有 | 有（BL/BLR* push；RET* pop） |
| 间接预测 | ~256 目标 | 未测 | 有 | 间接分支预测器 | 间接分支预测器 |
| **保护** | 无 ECC（公开资料无任何提及） | 未披露 | **BTB/GHB/BPIQ 全部无保护**（TRM Table 9-1 明示 None） | TRM Table 11-1 **未列** BTB/GHB → 未披露 | TRM Table 10-1 **未列** → 未披露 |

SDC 视角：分支预测结构是**控制面**——翻转通常导致 mispredict（性能损失）或错误路径取指（被推测执行后丢弃），**理论上不易直接产生体系结构可见的 SDC**；但例外路径存在：BTB 目标翻转 + 推测窗口内的副作用（如非瞬时内存操作）或与 PAC 缺失叠加（920 无 PAC）时可能放大攻击面。注意 N1 TRM 明确把 BTB/GHB/BPIQ 列为 **None（无保护）**——这是 Arm 官方文档中少见的"承认无保护"的部件，对 SDC 故障注入实验是**最容易命中且必然漏检的靶点**。

### A3. 译码与 µop 缓存

| | 920 | 920f | N1 | N2 | N3 |
|---|---|---|---|---|---|
| 译码宽度 | 4/cyc | 未知 | A32/T32/A64 | A32/T32/A64 | 仅 A64 |
| µop/MOP cache | **无**（代码溢出 L1i 后带宽 4→0.25 条/cyc 骤降） | 未披露 | 无 MOP（N1 无此结构） | **L0 MOP 1536 项，4-way skewed**，存已译码优化指令 | TRM 组件图与编码章均无 MOP → **无（相对 N2 删减）** |
| 保护 | — | — | — | MOP data: SED parity | — |

SDC 视角：MOP cache 命中率高（N2 主打结构），翻转 = 译码后指令被静默篡改，且**不经取指级校验**——N2 用 SED 覆盖单比特；双位翻转同 TRM 承认可致 corruption。920 无 µop cache，反而少一个 SDC 暴露面。

### A4. 指令 TLB（详见 E 节统一表）

---

## 4. B. 乱序执行引擎

### B1-B3. 重命名/调度/ROB

| | 920 | 920f | N1 | N2 | N3 |
|---|---|---|---|---|---|
| ROB | ~128 µop（实测有效 108–110） | 未测 | 128（公开规格，TRM 未披露） | 未披露 | 未披露 |
| 调度器 | ALU/LS/FP 三类统一式，各 ~33 项 | 未测 | issue queues（TRM 未给容量） | issue queues | issue queues |
| INT PRF | ~128 项；Flag rename ~31 | 未测 | 未披露 | 未披露 | 未披露 |
| move elimination | 有 | 未测 | 未披露 | 未披露 | 未披露 |
| **保护** | 无（架构上无 RAS，实现未知） | 未披露 | TRM 未列任何保护 → 无披露 | 未披露 | 未披露 |

SDC 视角：PRF/ROB/调度器属于**数据面寄存器堆**——物理寄存器堆翻转 = 立刻改变在飞指令的操作数 → **直接 SDC**，且五款芯片均**未公开任何保护**（Arm TRM 的 RAS 章只覆盖 RAM 型缓存/TLB 结构，PRF 之类的触发器阵列不在列）。这是所有乱序核共同的 SDC 盲区，也解释了为何学术 FI 研究（gem5 FI/O3 寄存器注入）大量集中在 PRF。

### B4. 执行单元

| | 920 | 920f | N1 | N2 | N3 |
|---|---|---|---|---|---|
| 整数 | 3×ALU + 1×MUL/DIV(4cyc)；分支可占 2 ALU，1 taken/cyc | 未测 | INT 执行单元 | INT 执行单元 | INT 执行单元 |
| FP/向量 | 2×FP；FP32 FMA 2/cyc（128b），FP64 1/4 rate；FADD 4/FMUL 5/FMA 5–7 cyc | 标量 FMA 2/cyc；NEON128 2/cyc；**SVE512 FMA ≥2/cyc（实测 13.6 flop/cyc 下限）** | NEON 128b | NEON + **SVE/SVE2 128b 向量长度** | NEON + SVE/SVE2 128b 向量长度 |
| Crypto | AES+PMULL/SHA1/SHA256/CRC32 | AES/SHA1/2/512/SHA3/SM3/SM4 | 可选扩展 | 可选扩展（含 SM3/SM4） | 可选扩展（含 SHA-3；EOR3/XAR/BCAX 随 SVE2 免费给） |
| 关键延迟（实测） | int-mul 3.42、udiv 早退 6.2、CASAL 43、LDR 依赖链 2.87 | — | — | — | — |
| **保护** | 无公开信息 | 未披露 | 无披露 | 无披露 | 无披露 |

SDC 视角：ALU/FMA 内部位翻转直接进结果寄存器 → **纯 SDC 通路**，无任何校验（除非上层做算法级冗余）。文献中锁步/双核冗余针对的正是这里。五款均无披露，视作同等高危。

---

## 5. C. 访存与数据通路

### C1. LSU / Store Buffer

| | 920 | 920f | N1 | N2 | N3 |
|---|---|---|---|---|---|
| AGU/LSU | 2×AGU（2 load 或 1L+1S）/cyc | 未测 | load/store 单元 | LSU | LSU |
| L1D 访问 | 2×128b/cyc | — | — | — | — |
| store→load 转发 | 6–7 cyc（跨 16B 边界 +1–2） | 未测 | — | — | — |
| 原子 | LSE 完整；CASAL 实测 43 cyc（L1 争用） | LSE | near/far atomic：L1 unique 命中走 near，miss/共享走 CHI far atomic；LOR 4 region | LSE 原子（TRM §8.2） | LSE 原子（§7.3 在 L1 内存系统中实现） |
| 独占监视器 | 内部 exclusive monitor | 未测 | 内部 exclusive monitor（§7.4.2） | §8.3 | §7.4 |
| **保护** | 无披露 | 未披露 | 无披露（store buffer 不在 RAS 表中） | L2 TQ 在 RAS 表（SECDED）；L1 侧队列未列 | L2 TQ SECDED |

SDC 视角：load/store 队列与 store buffer 中翻转直接改变待写数据/地址 → **高概率 SDC**。N1/N2/N3 唯一披露的保护点是 **L2 Transaction Queue（SECDED）**；L1 侧 LSQ 未披露。

### C3. 数据预取器

| | 920 | 920f | N1 | N2 | N3 |
|---|---|---|---|---|---|
| 结构 | 标量/向量优化（厂商描述） | 未测 | L1 PHT（prefetch history table） | load 侧 VA 预取 L1+L2；store 侧 PA 仅预取 L2；另有 TLB prefetcher、region prefetcher（IMP_CPUECTLR_EL1 可控） | L2 预取引擎（VA+PC） |
| **保护** | 无披露 | 未披露 | **PHT 无保护（TRM Table 9-1 明示 None）** | 未列 | 未列 |

SDC 视角：预取器翻转多产生"多余/错误地址的取数"，错误数据进缓存但未被消费 → 一般被掩盖；**但预取错地址会污染一致性状态/功耗，属低危控制面**。N1 明示 PHT 无 ECC。

---

## 6. D. 缓存层次

### D1-D3. 容量/组织总表

| | 920 | 920f | N1 | N2 | N3 |
|---|---|---|---|---|---|
| L1D$ | 64KB/4-way/64B，VIPT，load-to-use 4 cyc | 32KB/**8-way**/64B（实测 ~10 cyc） | 64KB/4-way/64B，VIPT，ECC/32b | 64KB/4-way/64B | **32KB 或 64KB**/4-way/64B |
| L1I$ | 64KB/4-way | 32KB/4-way | 64KB/4-way | 64KB/4-way | 32KB 或 64KB/4-way |
| L2$ | 512KB/8-way/10 cyc 私有 | **768KB/12-way**/~17 cyc 私有统一 | 256/512/1024KB/8-way 私有（2 bank；TQ 24/36/48 项） | 512KB 或 1024KB/8-way 私有 | 128/256/512/1024/**2048KB**/8-way/2-bank/PIPT 私有 |
| L3/LLC | 每 die 32MB SLC（8 bank×4MB），**15-way 伪随机，128B 行**，tag 在簇侧；shared/private/**partition(默认)** 三模式 | **不存在**（sysfs 无 index3；SCN 远端 8–16MB 是网络侧缓存） | DSU 内可选 L3（TRM 范围外，DSU TRM 管） | DSU-110 L3（DSU TRM 范围） | Direct connect 单核配置无 L3/SCU |
| 行大小陷阱 | **L3=128B 而 L1/L2=64B** | 64B | 64B | 64B | 64B |
| 一致性 | Hydra/HHA 目录（edir-* PMU 可观测）；跨 die 环形 NoC | HCCS 类；NUMA 距离 61–91 跨 socket | DSU SCU+可选 snoop filter | DSU-110 SCU/snoop filter | DSU-120；CHI Issue E 接口 256-bit |

来源：920 sysfs 实测（sets=256/1024/2048）；920f 实测；N1 TRM §2.3/§3.1；N2 TRM p40/42；N3 TRM p31-33/67（Table 8-1）。

SDC 视角（缓存是 FI 实验主战场，本仓库 CHAOSCache 注入结论可直接映射）：
- **tag RAM 是最危险的缓存子结构**：tag 翻转 → 错误行命中 → 读出他人数据（伪共享式 SDC）或丢失写回。N2 TRM §11.2 原文："**Uncorrectable L1 data cache and L2 cache tag errors are not containable**"——架构承认 tag UC **不可遏制**；N1 的处置是失效整行 + ERI 通知（丢数据但**不静默**）。本仓库注入实证：tag→SDC `bd34ebf3da704050`，valid/dirty/repl/coh→Masked，与 TRM 叙述定性一致。
- **L3/SLC 的保护全部不在这三份 core TRM 范围内**（DSU/HHA 侧文档），Neoverse 三款 core TRM 只披露私有 L1/L2；920 的 L3 ECC 强度无公开证据。

### D4. 缓存 RAM 保护矩阵（SDC 敏感性的核心表）

| RAM | 920 | 920f | N1 | N2 | N3 |
|---|---|---|---|---|---|
| L1I tag | 声称 ECC（无证据） | 未披露 | 1 parity/39b | SED | SED |
| L1I data | 声称 ECC（无证据） | 未披露 | SED/72b | SED | SED |
| L0 MOP | （无此结构） | 未披露 | （无） | SED | （无此结构） |
| L1D tag | 声称 ECC | 未披露 | **SECDED**（42b+7 ECC；UC→evict-correct-refill） | **SECDED** | **SECDED** |
| L1D data | 声称 ECC | 未披露 | **SECDED**（32b+1 poison+7 ECC） | **SECDED** | **SECDED** |
| L1D aux tag | — | — | — | — | **SECDED**（N3 新增披露） |
| L2 tag | 声称 ECC | 未披露 | SECDED（50–57 tag bits+7 ECC） | SECDED | SECDED |
| L2 data | 声称 ECC | 未披露 | SECDED（8 ECC/64b） | SECDED | SECDED（ECC granule 可配 128/256b） |
| L2 TQ | — | — | SECDED（8 ECC/64b） | SECDED | SECDED |
| L2 victim | — | — | **None** | （表中未列） | （表中未列） |
| L2 uncore/DSU L3 | SLC 无公开数据 | 无 L3 | DSU TRM 范围 | DSU TRM 范围 | DSU TRM 范围 |

关键共性（N1/N2/N3 TRM 措辞一致）：SECDED RAM 的双位错被"检出并上报或延迟"，若发生在 **dirty 行**上则**数据可能丢失（显式通知，不是 SDC）**；SED RAM 的双位错**不检测，TRM 原文明言可能数据损坏（真 SDC）**；≥3 位错"可能检可能不检"（依 RAM 与位置）。

---

## 7. E. 地址转换

### TLB 组织与保护

| | 920 | 920f | N1 | N2 | N3 |
|---|---|---|---|---|---|
| iTLB | 32 项全相联 | 未测 | 48 项全相联（4K–32M） | **48 项全相联**（TRM Table 6-1） | 32 项全相联（4K–2M） |
| dTLB | 32 项全相联 | 未测 | 48 项全相联（4K–512M） | 44 项全相联 | 48 项全相联（4K–2M） |
| L2 TLB | 1024 项共用（命中 +11 cyc） | 未测 | 1280 项 5-way（4 并行 walk） | 1280 项 5-way | **分裂**：small-page 1536 项 6-way（或 1024 项 4-way reduced-area）+ medium-page 256 项 4-way + walk cache |
| 周边结构 | — | — | — | TRBE TLB 2 项；MMUTC；translation prefetcher | SPE TLB 1 项；TRBE TLB 1 项；translation prefetcher |
| **保护** | 无披露（RAS=0 → 架构上无 TLB RAS 机制） | 未披露（RAS=1 但无 TRM） | **L1 TLB = flops 无保护**（TRM 原文注释）；MMU translation cache 2-bit 交错 parity/71b；MMU replacement/biased-repl None | MMUTC: SED（Table 11-1） | **TLB: SED**（Table 10-1，措辞从 N2 的"MMUTC"改为"TLB"） |

SDC 视角：TLB 翻转 = 错误 VA→PA 映射 → **load/store 落错物理页**。若目标页恰好有写权限，是教科书级 SDC（写坏别人的页且无异常）；若权限位翻转则多为 abort（非 SDC）。N1 明示 L1 TLB 用触发器实现**无保护**；N2/N3 把 MMU 缓存拉进 SED。TLB 的 SDC 敏感性还与页大小相关：920f 强制 64KB 页 → 同样 1 项 TLB entry 覆盖 16 倍地址空间，**单次 entry 翻转的波及面 ×16**（对 SDC 是放大器）。

---

## 8. F. RAS 与错误处理（SDC 敏感性的"防御纵深"）

### F1. 架构化 RAS 支持

| | 920 | 920f | N1 | N2 | N3 |
|---|---|---|---|---|---|
| ID_AA64PFR0.RAS | **0（实测，无 ARMv8.2 RAS）** | **1（实测）** | 实现完整 RAS 扩展 | v9.0 RAS 全量 | v9.2 RAS 全量 |
| 错误记录寄存器 ERR* | 无 | 有（无 TRM 细节） | ERR<n>FR/CTLR/MISC0-1 + PFGF（TRM §13.47-13.51） | 同 N1 + MISC2-3 | 同 + 寄存器带 _EL1 后缀（RASv1.1 风格：ER1PFGCDN_EL1） |
| 中断 | — | — | FHI/ERI | FHI(nCOREFAULTIRQ)/ERI(nCOREERRIRQ) | 同 |
| 消费时报错 | — | — | SEA/AEA/ERI | SEA/AEA/ERI | SEA/AEA/ERI |
| ESB 指令 | 无 | 有 | 有 | 有 | 有 |
| Poison 传播 | 无架构机制（厂商私有） | 有（架构） | 64b 粒度（L1D 32b）；tag UC→失效+ERI | 总线 poison 属性；evict 双错 poison | 同 N2 |
| 错误注入 | 无架构接口 | 未知 | CE/DE/UC/RE 四类全可注入（§9.7） | CE(L1D 单 ECC)/DE(L1→L2 evict 双 ECC 或 snoop)/UC(L1 tag evict 后双 ECC) | CE/DE/UC（UC 定义为 L1 **和** L2 tag） |
| PMU 联动 | ghes_edac 平台计数 | SPE/PMUv3 | MEMORY_ERROR 事件（0x1A，§13 PMU 事件表） | MEMORY_ERROR 事件 | MEMORY_ERROR 事件 |
| 节点划分 | — | — | Node0=L1+L2 | Node0=L1+L2 私有存储系统 | Node0=L1+L2+**MMU/TLB**（N3 明确纳入） |

### F2. 平台级 RAS 栈

| | 920（本机实测） | 920f | N1/N2/N3 |
|---|---|---|---|
| ACPI | HEST/EINJ/BERT/ERST 全在（EINJ 368B → **固件级错误注入可用**）；MPAM；SDEI | 未探（root 不可及） | SoC 集成方决定 |
| EDAC | ghes_edac，DDR4 RDIMM **SECDED**（mc0，ce/ue 计数实测为 0） | 未知 | — |
| PCIe | AER（厂商宣称） | Gen4 RC | — |
| uncore PMU | L3C/HHA/DDRC 每 die 全套（back_invalid=核间一致性干扰计数器） | 171 perf 设备（8 SCCL×(4 DDRC+4 HHA+16 UC)+14 SICL L3） | DSU 侧 |

### F3. 诚实性标注（重要）

- kunpeng920.md 声称"指令/数据缓存 ECC、Memory Poisoning、MCA、99.999% 可用性"——**与同机实测 ID_AA64PFR0_EL1.RAS=0 直接冲突**。结论：920 有**非架构化**（non-architectural）的 ECC 实现（无 ERR* 编程模型、无 ESB、无架构 poison），平台 RAS 依赖 ACPI/GHES；其宣传口径不能等同于 Neoverse 级别的架构化 RAS。SDC 实验中**不能假设 920 有 poison 传播/ERI 等机制**。
- 920f RAS=1 仅说明架构授权存在，错误注入寄存器布局/保护矩阵**无厂商 TRM**，黑盒。

---

## 9. SDC 敏感性横向分析

### 9.1 敏感性排序（部件级，五款共性 + 差异）

按「无保护/弱保护 × 数据面 × 长驻留」三因子，微架构部件 SDC 敏感性从高到低：

| 排名 | 部件 | 保护现状（最优者） | SDC 机理 | 五款中最危险 |
|---|---|---|---|---|
| 1 | **执行单元/ALU/FMA 数据通路** | 全部无保护（无披露） | 运算中翻转直接进结果 | 全部等同高危 |
| 2 | **PRF/ROB/调度器触发器阵列** | 全部无保护（不在 RAS 表） | 在飞指令操作数/目的寄存器静默改写 | 全部等同高危 |
| 3 | **L1/L2 cache tag RAM** | SECDED（N1/N2/N3）；双位错仍不可遏制 | 错误命中→读错行/丢写回；UC 不可遏制 | 920（无架构 RAS，tag 保护未知）；N1/N2/N3 双位错场景 |
| 4 | **TLB/页表缓存** | N3 TLB SED / N2 MMUTC SED / N1 L1 TLB **flops 无保护** | 错误 VA→PA→写错物理页 | N1（L1 TLB）；920f（64KB 页放大波及面 ×16） |
| 5 | **L1I$/MOP（SED）** | SED 只检 1 位 | 双位翻转=静默改指令流（TRM 承认） | N2（多一个 1536 项 MOP 暴露面） |
| 6 | **LSQ/store buffer** | 无披露（仅 L2 TQ SECDED） | 待写数据/地址翻转 | 全部 |
| 7 | **BTB/GHB/预测器** | N1 明示 None；N2/N3 未披露 | 多为控制面→mispredict；间接 SDC 需特定推测路径 | 920（且无 PAC） |
| 8 | **预取器 PHT** | N1 明示 None | 错误预取多被掩盖（数据未被消费） | 低危 |
| 9 | **L1D/L2 data（SECDED）** | SECDED+poison | 单位纠、双位检出并通知（丢数据但不静默） | 相对最安全 |
| 10 | **DDR（平台层）** | 920: RDIMM SECDED+ghes_edac | 双位错不可纠但可检 | 平台层，非微架构 |

### 9.2 芯片级 SDC 敏感性画像

- **Kunpeng 920**（功能图见 [图 920-1](#kunpeng-920taishan-v110)）：**敏感性最高**。RAS=0 → 无架构化错误记录/ESB/poison，任何核内翻转只有"性能异常/崩溃/静默"三种归宿，其中"静默"无任何架构级可见信号；cache ECC 为厂商私有实现，强度不可验证；L3 128B 行 + tag 在簇侧的设计让 tag 翻转的波及面更大（一行 128B）。对 SDC 实验而言它是"最坏情况"平台，也是本仓库 gem5 FI 建模的主要对象。
- **920f**（功能图见 [图 920f-1](#920fhisilicon-part-0xd22未发布)）：架构上 RAS=1（有防御潜力），但无 TRM → 防御矩阵黑盒；**无 LLC** → 缓存暴露面反而小于 920（只有 L1D 32KB+L2 768KB），但 **64KB 强制页**放大 TLB 类翻转的波及面。SME/SVE512 的巨型向量寄存器（Z0–Z31 × 512b + 矩阵 tile）是新增的**无保护数据面**——单次向量寄存器翻转影响 64B 连续数据。
- **Neoverse N1**（功能图见 [图 N1-1](#neoverse-n1)）：RAS 矩阵披露最完整（连 None 都写明）；薄弱点：L1 TLB（flops 无保护）、BTB/GHB/BPIQ/PHT/L2 victim 无保护、I$ 仅 SED。作为"披露透明度最高"的参照系。
- **Neoverse N2**（功能图见 [图 N2-1](#neoverse-n2)）：在 N1 基础上把 MMUTC 拉进 SED、MOP cache 有 SED、其余同 N1；无新增明显弱点；数据面 SDC 防御 ≈ N1。
- **Neoverse N3**（功能图见 [图 N3-1](#neoverse-n3)）：保护矩阵最厚——TLB 明确 SED、L1D aux tag 新增 SECDED、L2 ECC granule 128/256b 可配（注意：比 N1/N2 的 64b 码字**更粗**，不可纠错误 poison 的数据跨度反而更大；其价值在构建期可配而非更细）、RAS 节点明确覆盖 MMU/TLB。**相对 SDC 敏感性最低**（在披露范围内，依据 TLB SED/aux tag/Node 0 覆盖，而非 granule）。

### 9.3 对本仓库 FI/SDC 研究的可操作结论

1. **注入靶点优先级**（依 §9.1 排序）：O3 PRF/执行单元 > cache tag > TLB > I$/MOP > 预测器。现有 CHAOSCache tag→SDC 实证（`bd34ebf3da704050`）落在第 3 位靶点，结论可推广到五款芯片（tag 语义跨架构同构）。
2. **920 是 SDC 上界样本**：无架构 RAS → 所有"检出/延迟/poison"防御为 0，FI 结果直接给出裸敏感性基线；N1/N2/N3 的同点注入可量化"RAS 防御削减了多少 SDC"。
3. **920f 的 64KB 页 × TLB 注入**是一个未被文献覆盖的放大器实验设计点。
4. **MOP cache（N2）** 是 SED 弱保护 × 高命中率 × 指令面的三重叠加，值得单独建注入模型（920/N3 无此结构，天然对照组）。
5. **双比特注入**是区分 SED 与 SECDED 防御强度的关键实验变量：SED RAM（I$/MMUTC/TLB）双位错是 TRM 承认的 SDC 通道，SECDED RAM 双位错则转为"显式丢数据"（非 SDC）。

---

## 附：五款芯片文档索引

| 芯片 | 文件 | 备注 |
|---|---|---|
| Kunpeng 920 | `kungpeng/kunpeng920_microarchitecture.md` | 实测主文档（sysfs/ID 寄存器/微基准/ACPI） |
| Kunpeng 920 | `kungpeng/kunpeng920.md` | 公开资料汇总（含与实测冲突的 RAS 宣称，见 §8.F3） |
| Kunpeng 920 | `kungpeng/kunpeng920_pmu_events.md` | PMU 事件全表（含 uncore） |
| 920f | `kungpeng/920f.md` | NSCC cn23154 实测 |
| Neoverse N1 | `neoverse-n1-trm/neoverse_n1_trm.md` (+PDF) | TRM 100616_0401_02 |
| Neoverse N2 | `neoverse-n2-trm/arm_neoverse_n2_core_trm_102099_0003_06_en.pdf` | 1668 页；RAS=ch11 p96 |
| Neoverse N3 | `neoverse-n3-trm/arm_neoverse_n3_core_technical_reference_manual_107997_0001_03_en.pdf` | 902 页；RAS=ch10 p76 |

本文所有 TRM 页码引用均可在对应 PDF 中直接验证；所有「实测」字样数据可在对应 md 文档中找到原始命令与输出。
