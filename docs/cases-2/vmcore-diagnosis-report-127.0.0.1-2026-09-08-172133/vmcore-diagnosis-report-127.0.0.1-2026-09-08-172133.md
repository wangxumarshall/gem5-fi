# 案 #21 深度诊断报告:127.0.0.1-2026-09-08-17:21:33

| 项 | 值 |
|---|---|
| 编号 | **#21**(vmcore0102 时间序第 21 个致命转储,2026-09-08 17:21:33) |
| 数据源 | 仅 `vmcore-dmesg.txt`(2772 行),**无 vmcore 内存映像** |
| 平台 | Yangtze Computing R240K V2/BC82AMQA(BIOS 7.48 06/15/2026),Kunpeng 架构 192 核 8 NUMA 节点 |
| 内核 | openEuler 6.6.0-145.3.23.154.oe2403sp3.aarch64 #1 SMP(2026-07-27 build) |
| 取证方法 | dmesg 行号级摘录 + Python3 mod 2^64 代数复算 + Code 指令手工 A64 解码 |
| 附件 | `algebra.py` / `algebra_out.txt`(代数与形态)、`dmesg_forensics.txt`(原文摘录+grep 统计) |

> **降级声明【实锤】**:本目录只有 dmesg,没有 vmcore 文件。一切需要读内存真值的验证(`__per_cpu_offset[54]` 数组内容、rq 实例 PTE 有效性、x20 与真值的直接汉明对照)在本案中**不可执行**。本报告所有真值相关结论均为形态学推断或谱系先例迁移,并逐条标注。这与谱系 12 案中 2 个 incomplete dump 案(#12 等)的降级情形同构。

---

## 1. 案情摘要 + 置信度

uptime ≈ 76275 s(约 21.19 h)时,进程 `mi-scavenger`(PID 2795884)在 CPU 179 上经 `newidle_balance → load_balance → find_busiest_group+0x140` 路径,执行 `ldr x23,[x27,#0x120]` 触发 L0 translation fault(ESR=0x96000004,FAR=d3eafc3c10eb97df 非规范地址),Oops 致命,kdump 转储。致命链唯一注入点是其前两条指令 `ldr x20,[x0,w25,sxtw#3]`(装载 `__per_cpu_offset[54]`)返回坏值 `x20=d3eb5026e000ffff`——高 16 位塌缩(应为 ffff)+低 16 位 0xffff 全 1 标签沾染的混合形态。

**本核心结论三级置信**:

- 现象层(x20 装载返回坏值 → 传播为致命缺页):【实锤】——两级加法 mod 2^64 逐位闭合(dmesg 寄存器现场,见 §3/§6);
- 通路归属(CPU179 核内读数据通路 SDC,非内存/软件/一致性):【强推】——同核唯一性 + 前兆同核 + RAS 零上报 + 加法器排除,但**本案无内存真值对照**;
- 物理位点(RF 端口/bypass/lane 选通网络)与物理成因:【假设】——软件不可分辨。

与前 20 案的关系:本案是 SYNTHESIS 12 案谱系的**第 21 次独立复现**,且坏值形态为谱系四族中罕见的**混合形态**(高位塌缩 + lane 错位标签并存),具独立形态学价值。

## 2. 崩溃现场六要素(逐字摘录,行号 = vmcore-dmesg.txt 真实行号)

来源:`/home/sdc/wangxu/vmcore0102/127.0.0.1-2026-09-08-17:21:33/vmcore-dmesg.txt`

```
行2720: [76274.523293] Unable to handle kernel paging request at virtual address d3eafc3c10eb97df
行2722: [76274.535798]   ESR = 0x0000000096000004
行2723: [76274.540420]   EC = 0x25: DABT (current EL), IL = 32 bits
行2726: [76274.554552]   FSC = 0x04: level 0 translation fault
行2731: [76274.582532] [d3eafc3c10eb97df] address between user and kernel address ranges
行2732: [76274.590546] Internal error: Oops: 0000000096000004 [#1] SMP
行2735: [76274.699507] CPU: 179 PID: 2795884 Comm: mi-scavenger Kdump: loaded Tainted: G        W           6.6.0-145.3.23.154.oe2403sp3.aarch64 #1
行2737: [76274.721280] pstate: 204000c9 (nzCv daIF +PAN -UAO -TCO -DIT -SSBS BTYPE=--)
行2738: [76274.729122] pc : find_busiest_group+0x140/0xb60
行2739: [76274.734536] lr : find_busiest_group+0x11c/0xb60
行2741: [76274.744128] x29: ffff8001f84338c0 x28: ffff8001f8433850 x27: d3eafc3c10eb96bf
行2742: [76274.752144] x26: ffff604004f86240 x25: 0000000000000036 x24: ffffac15312a5000
行2743: [76274.760158] x23: 0000000000000400 x22: ffff604004f86240 x21: ffffac153129fcb0
行2744: [76274.768174] x20: d3eb5026e000ffff x19: ffff8001f8433950 x18: 0000000000000000
行2750: [76274.816263] x2 : 00000000000077fc x1 : ffffac1530ea96c0 x0 : 0000000000000036
行2769: [76274.915246] Code: f9400782 f879d814 2a1903e0 8b14003b (f9409377)
行2771: [76274.932390] Starting crashdump kernel...
```

六要素:时刻 76274.523293 s;CPU 179;进程 mi-scavenger(PID 2795884,futex 等待中被调度);pc=find_busiest_group+0x140/0xb60;ESR=0x96000004(EC=0x25 DABT current EL,FSC=0x04 L0 translation fault);FAR=d3eafc3c10eb97df(行2731 明示"between user and kernel address ranges"——非规范地址,TTBR0/TTBR1 均不可能命中,L0 直接 fault)。

## 3. 指令级解剖:Code 5 指令手工 A64 解码 + 传播链

Code 窗口 5 指令逐条解码(编码域人工切分,复核见 `algebra_out.txt` 第二节):

| 位置 | 编码 | 解码结果 | 语义 |
|---|---|---|---|
| pc-0x10 | `f9400782` | `ldr x2, [x28, #0x8]` | 前序上下文(读 x28 所指结构 +8) |
| **pc-0x0c** | **`f879d814`** | **`ldr x20, [x0, w25, w25 符号扩展左移3]`(即 `ldr x20,[x0,w25,sxtw #3]`)** | **从 `__per_cpu_offset[w25=54]` 装载 CPU54 的 percpu 偏移到 x20 ← 唯一注入点** |
| pc-0x08 | `2a1903e0` | `mov w0, w25`(orr w0, wzr, w25) | w0=54,参数传递 |
| pc-0x04 | `8b14003b` | `add x27, x1, x20` | percpu 基址合成:x1(变量静态基址)+x20(动态偏移) |
| **pc** | **`f9409377`** | **`ldr x23, [x27, #0x120]`**(imm12=0x24,0x24×8=0x120=288) | 读 `rq->cfs.avg` 载荷(load_avg 族字段)→ 对非规范 x27+0x120 取数,L0 fault 致命 |

编码域证据(以 `f879d814` 为例):size=11(64 位)、V=0、opc=01(LDR)、Rm=w25、option=6(SXTW)、S=1、Rn=x0、Rt=x20——与反汇编形态完全一致;`f9409377`:size=11、opc=01、imm12=0x24、Rn=x27、Rt=x23,unsigned offset = 0x24<<3 = 0x120。

**传播链(代数闭合,python3 mod 2^64 实算,输出见 algebra_out.txt 第一节)**:

```
x1  = ffffac1530ea96c0   (行2750)
x20 = d3eb5026e000ffff   (行2744)  ← 坏值
x1 + x20 (mod 2^64) = d3eafc3c10eb96bf
x27 (行2741)        = d3eafc3c10eb96bf   → 逐位相等【实锤】
x27 + 0x120         = d3eafc3c10eb97df
FAR (行2720)        = d3eafc3c10eb97df   → 逐位相等【实锤】
```

即:x27 与 FAR 都是 x20 坏值经**纯正确算术**派生的结果。add 指令、操作数传递、有效地址生成全部无错;x23=0x400(行2743)是 ldr 语义反应(致命 fault 未完成装载,x23 保留先前值,与谱系各案一致)。

## 4. 坏值形态分析:x20 = d3eb5026e000ffff

### 4.1 位级分解(实锤,来源 algebra_out.txt 第三节)

- 16 位段:[63:48]=`d3eb`、[47:32]=`5026`、[31:16]=`e000`、[15:0]=`ffff`
- 字节序(byte7→byte0):`d3 eb 50 26 e0 00 ff ff`

真值形态约束(形态学;本案无 vmcore,不可直接对照——降级声明):percpu 偏移在谱系 10 个可对照案中恒为 `ffff....xxx000` 形态(高 16 位全 1,低位页对齐),如 #4 案真值 `ffffda55e61ce000`、#6 案 `ffffdd6d7fa64000`、#10 案 `ffffa6616d8f8000`、#11 案 `ffffa89017090000`。x20 与这些**真值形态样本**的汉明距离为 31~40 位(纯参考值,非本案真值)。

x20 对两条形态约束**双双违反**:

- **高段塌缩**:高 16 位 = `d3eb`,不是 `ffff`——真值最高 16 位"消失",被中段样式的值顶替;
- **低 16 位 0xffff 全 1标签**:真值此段应为页对齐零,却呈现全 1——这是"标签/沾染"形态,与随机翻转(约 8 位期望置位数)明显不同,0xffff 无法用小位数随机翻转从 0x0000 得到(需 16 位全部翻转)。

### 4.2 与前兆块 x3 的 rol16 关系(本案最锋利的形态学发现)

三次前兆 WARNING 块中寄存器 x3 **恒定**为 `ffffd3eb50934000`(行2603/2649/2694,三次完全相同)——这是 CPU179 本地 percpu 区的规范形态(ffff 开头、50934000 页对齐尾)。它与 x20 坏值存在惊人关系:

```
x3       = ffff d3eb 5093 4000
x3 rol16 = d3eb 5093 4000 ffff     (16bit lane 循环左移一段)
x20      = d3eb 5026 e000 ffff
XOR      = 0000 00b5 a000 0000     → 汉明距离仅 7 / 64 位!
段级: [63:48] d3eb=d3eb(全同)  [47:32] 5093 vs 5026(5位差)
       [31:16] 4000 vs e000(2位差)  [15:0] ffff=ffff(全同)
```

即 **x20 ≈ rol16(x3) + 7 位段内差异**:x20 的高 16 位 `d3eb` 恰是 x3 的 [47:32] 段;x20 的低 16 位 `ffff` 恰是 x3 的高 16 位(循环绕回)。这不是巧合级别的相似——若 x20 为随机 64 位值,与 rol16(x3) 汉明距离的期望约 32 位,≤7 位的概率约为 C(64,≤7)/2^64 ≈ 2^-46 量级。合理解释是:x20 的装载返回通路发生了 **16bit lane 循环错位**(数据通道按 16 位 lane 复用时错选了一段),叠加段内少量位翻转。

**须诚实标注】:这是跨寄存器(x3 是前兆时刻另一上下文的值)的形态学对照,不是同一数据的直接因果——x3 只证明"d3eb 段在 CPU179 相关数据中真实存在",rol16 闭合是【强推】而非【实锤】。其价值在于给出"lane 错位"这一机理指纹,与 x20 自身"低 16 位 0xffff 标签"的独立观察互相印证。

### 4.3 与 SYNTHESIS 谱系四族对照归并

SYNTHESIS-12case-cross-analysis.md 谱系表四族:零塌缩族(#4/#6/#10/#11/#12)、lane 错位族(#1 16bit lane 循环移位、#5 +1 字节窗口、#7 ror16+0xa000 顶标签)、部分位保留族(#8/#9)、读写双向族(#2/#3 前兆)。

本案 x20 归并判定:**主归 lane 错位族,兼零塌缩族特征(高位塌缩)**——

- 与 **#7 案(ror16+0xa000 顶标签)** 最相似:#7 是真值 ror16 后顶上 0xa000 标签;本案是真值形态 rol16 后低位顶上 0xffff 标签(全 1 版)。两案共同点:移位量都是 16 位(一个 lane 宽度)、标签都出现在 lane 边界、都不是随机翻转;
- 与 **#1 案(16bit lane 循环错位重组)** 同机理:本案 §4.2 的 rol16(x3) 7 位闭合直接复现了"lane 循环错位"形态;
- 高位 `ffff→d3eb` 的塌缩同时呈现零塌缩族的"高段失效"特征——本案是谱系中罕见的**两族特征并存**的混合形态,进一步支持 SYNTHESIS §2.3 的论断:四族不是四种独立故障,而是同一通路(lane 复用/选通网络)不同故障相位的表现。

FAR=d3eafc3c10eb97df 的非规范性:高 16 位 d3ea(比 x20 的 d3eb 恰差 1 位——加法进位所致),落入 TTBR0/TTBR1 均不覆盖的非规范区间,MMU 直接 L0 fault,无需查页表——这解释了为何 ESR FSC=L0 且无后续页表遍历痕迹。

## 5. 前兆谱:3 次 spurious fault 全谱

三次前兆全部 CPU:179,全部为 `/proc/interrupts` 读路径(`show_interrupts → seq_printf → __memcpy` 中对**有效内核地址**的假 translation fault,内核 AT 重走后判 spurious 放行),与谱系 #7 案前兆路径完全一致:

| # | 时刻(s) | 行号 | 假 fault 地址 | 进程 | 距下次/致命 |
|---|---|---|---|---|---|
| 1 | 74323.653548 | 行2585 | ffff604004d01102 | pmdalinux (PID 10320) | +472.40 s → #2 |
| 2 | 74796.054873 | 行2631 | ffff604005ce047c | irqbalance (PID 9774) | +727.57 s → #3 |
| 3 | 75523.625474 | 行2676 | ffff604005ce6450 | pmdalinux (PID 10320) | **+750.897819 s → 致命** |

**末次前兆 → 致命间隔 = 76274.523293 − 75523.625474 = 750.897819 s = 12.515 min(12 min 30.9 s)**【实锤,python3 实算】。三次间隔节奏(472 s / 728 s / 751 s)呈近似等周期(约 8~12.5 min),暗示间歇性故障的激发条件周期性出现(如 irqbalance/pmdalinux 周期性读 /proc/interrupts 触发同通路)。

前兆地址形态:高 32 位全部 `ffff6040`(Node7 vmalloc/pcpu 段聚集);#2 与 #3 低段前缀 `05ce` 相同(同一 64KB 邻域,相距 0x5fd4),#1 相互分散——**ffff6040 段聚集但具体地址分散**,即"同一地址空间区域、非同一地址反复",符合"通路瞬时腐化,非存储单元驻留坏"的谱系定式(§2.4)。另注:致命块 x26/x22 = ffff604004f86240 亦落在同段(sched 域对象),证明 CPU179 当时正在操作 Node7 本地调度器数据。

补充事实:CPU179 曾在 1308.495461 s 被 offline(行2580 `psci: CPU179 killed`),61118.978549 s 重新 onlined(行2583),**全部 3 次前兆与致命都发生在 re-online 之后的 13156~15156 s 窗口内**(61118→74323→76274)。

## 6. 反事实与软件排除

**(a) RAS 零上报【实锤】**(grep 统计,全部命令与输出见 dmesg_forensics.txt 第 I 节):`hardware error`=0、`machine check`=0、`corrected/uncorrected error`=0、EDAC 错误事件=0;ghes 全部 2 行均为初始化(行2175-2176 `ghes_edac: This system has 32 DIMM sockets` / `EDAC MC0: Giving out device`),无任何 GHES 事件上报。固件侧 RAS 链路(HEST 行1305、GHES APEI firmware-first 行"GHES: APEI firmware first mode is enabled"、EDAC MC Ver 3.0.0 行1857)健全在位——负证据有效:若有 DIMM 级 CE/UE,该链路应上报而未上报。33 处 `Firmware Bug` 全部为 IORT SMMU 映射告警(行1460 等),与本案无关联。

**(b) taint 自洽【实锤】**:致命块 `Tainted: G W`(行2735)——W 正是三次前兆 WARNING 所置;三次前兆块自身"Not tainted"(行2589)→ 第 1 次前兆时内核干净。G 为模块加载。无 prior bug 污染,时间线自洽。

**(c) 加法闭合独立验证 x20 为唯一坏值【实锤,本案降级条件下的最强证据】**:§3 两级加法逐位闭合证明 x27、FAR 均为 x20 的确定性算术结果。反事实:若 x20 装载返回任何合法 percpu 偏移(ffff....xxx000 形态),x27+0x120 必落在规范内核地址,不会 L0 fault。因此崩溃 100% 归因于该次装载的返回值——尽管本案无 vmcore 不能直接读 `__per_cpu_offset[54]` 内存真值,但谱系 10/12 案中该数组真值全部实测完好(SYNTHESIS §2.5),且本案若数组真坏(驻留),不可能呈现"三次前兆间隔 8~12 min、单发致命"的间歇模式。

**(d) 软件排除【强推】**:(i) 同一 `find_busiest_group+0x140` 装载指令在 192 核上每天执行亿万次,若为软件 bug 应遍地开花,而非 21/21 案独聚 CPU179;(ii) 前兆三块与致命块的进程/路径(pmdalinux、irqbalance、mi-scavenger)互不相同,唯一公共因子是 CPU179;(iii) 内核为 2026-07-27 同一 build,谱系 12 案已确认该 build 在 191 颗核上零异常;(iv) 前兆为对有效映射地址的假 fault(AT 重走放行),软件页表错误不会"重走即好"。

## 7. 根因三级置信 + 跨案对照

**根因判定**:CPU179(MPIDR 0x7a0300,Node 7)核内读数据通路(load 返回段/L1D→fill buffer→RF 写口/lane 选通网络)间歇性、无检错覆盖的结构化数据腐化(SDC),本次表现为"16bit lane 循环错位 + 高位塌缩 + 低位全 1 标签沾染"混合形态,经 `__per_cpu_offset[54]` 装载注入调度器热路径致致命缺页。

| 层级 | 判定 | 置信度 | 本案证据(降级后) |
|---|---|---|---|
| 现象层 | x20 装载返回坏值,两级加法传播为 L0 fault | 【实锤】 | dmesg 行2720/2741/2744/2750 + algebra_out.txt 逐位闭合 |
| 通路归属 | CPU179 核内读通路 SDC(非内存/软件/一致性) | 【强推】 | 3+1 事件全聚 CPU179、RAS 零上报、加法器排除、taint 自洽;**缺真值对照** |
| 物理位点 | lane 复用/选通网络(rol16 指纹)vs RF 写口 vs PTW | 【假设】 | rol16(x3) 7 位闭合是形态学线索,不可软件分辨 |

**跨案对照(编号 #21)**:本案为 vmcore0102 时间序第 21 次致命转储,SYNTHESIS 12 案谱系(2026-08-14 至 09-04)之后的第 9 次(谱系外 #13~#20 为 09-04 至 09-07 各案)。与谱系不变式的符合度:

- 受害核唯一性(CPU179):符合【实锤】;
- 受害指令族(`__per_cpu_offset[]` 装载,find_busiest_group+0x140):符合,且 pc/lr/Code 窗口与谱系 11 案完全同位【实锤】;
- 坏值形态:lane 错位族为主 + 零塌缩高位特征混合——谱系内首见两族并存于单值,归 #7(ror16+标签)最近亲【强推】;
- 前兆统一(spurious fault 同核):符合,且前兆路径(show_interrupts 读)与 #7 案完全一致【实锤】;
- 末次前兆-致命窗 750.90 s:落入谱系分布(17.6 s~10.7 h)中部,不刷新极值【实锤】。

**处置建议**(与 SYNTHESIS §6 一致,本案加重):立即 offline CPU179——特别是本案显示 CPU179 曾于 1308 s 被 offline 又于 61118 s re-online,**全部故障发生在 re-online 之后**,这本身构成"该核只要在线即累积风险"的又一佐证;给 spurious fault 加 per-CPU 计数与阈值隔离(本案前兆已有约 12.5 min 预警窗,足够自动化响应);RMA 工单证据链引用本案 #21 与 rol16 形态指纹。

---

*本报告为独立诊断,未参考 docs/cases 与 docs/cases-2 任何既有报告正文(唯一例外:SYNTHESIS-12case-cross-analysis.md 谱系表用于 §4.3/§7 对照)。全部原始摘录见 dmesg_forensics.txt,全部计算可由 `python3 algebra.py` 复现。*
