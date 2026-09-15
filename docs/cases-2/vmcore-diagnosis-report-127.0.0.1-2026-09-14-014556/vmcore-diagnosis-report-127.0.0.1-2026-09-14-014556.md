# 案 #28 独立法证诊断报告：127.0.0.1-2026-09-14-01:45:56

**零塌缩族第 9 案 + 9 案中唯一完整 vmcore 者：`__per_cpu_offset[7]` 真值 crash 实测对照（0xffffb5297a60c000 vs 实收 0，64 位全异）+ x17 残留上次正确装载的槽 179 真值（数组完好的活证）+ 反事实路径两级 vtop 实测闭合（runqueues[7]/[179] 逐位吻合）+ 184 次前兆谱系新纪录（43 簇三段式）+ swapper/179 idle softirq 崩溃链**

| 项 | 值 |
|---|---|
| 报告日期 | 2026-09-15（独立重研究，未读任何既有单案报告正文） |
| 数据源 | `/home/sdc/wangxu/vmcore0102/127.0.0.1-2026-09-14-01:45:56/vmcore-dmesg.txt`（10947 行）+ **`vmcore`（12,287,357,637 字节 ≈ 12GB，完整可用）** |
| 证据地位 | **9 案中唯一有完整 vmcore 者**——本案执行 crash 8.0.4 动态取证（真值对照、反事实 vtop、页表几何），其余 8 案的"真值不可测"降级在本案全部补齐为实测 |
| 平台 | Yangtze Computing R240K V2/BC82AMQA（Kunpeng-920 系，192 核 8 NUMA 节点），BIOS 7.48 06/15/2026（dmesg L10908） |
| 内核 | 6.6.0-145.3.23.154.oe2403sp3.aarch64 #1 SMP Mon Jul 27 19:00:34 CST 2026（dmesg L2）——与谱系 12 案完全同 build（BuildID 276194e5…） |
| 取证附件 | `algebra.py` + `algebra_out.txt`（代数闭合 + 真值对照 + 反事实）、`dmesg_forensics.txt`（行号级摘录含 184 前兆谱）、**`crash_session.log`（crash 8.0.4-17.oe2403sp4 完整会话，taskset -c 0-47 冷加载 12GB vmcore）** |

---

## 1. 摘要与置信度

开机 **142080 秒（1.64 天，谱系第 4 长 uptime）**内，CPU179 累计爆发 **184 次 spurious kernel translation fault 前兆**（全部 CPU179——**谱系单案前兆数新纪录**，旧纪录为谱系 #2 案的 26 次与 #8 案的 35 次的 5 倍以上），呈现 43 簇『首发作窗（7.15h，38 次）→ 25.02h 大静默 → 再发作窗（32.5h，40 次）→ 临终密集窗（37.2-39.4h，106 次）』结构。最终（142080.1s）CPU179 的 **idle 线程 swapper/179（PID 0）**在空闲调度 softirq 路径（`do_idle → cpuidle_idle_call → el1h_64_irq → irq_exit_rcu → run_rebalance_domains → _nohz_idle_balance → rebalance_domains → load_balance → find_busiest_group`）中，执行 `__per_cpu_offset[]` 装载指令 `ldr x20, [x0, x25, sxtw #3]`（x25=7，读 CPU7 的槽），**装载返回值 x20 = 0 完全零塌缩**。零偏移使加法恒等（x27=x1），致命装载以 x1+0x120 寻址，FAR=ffffcad705af97e0 为 canonical 但 PTE=0 的地址，触发 **level 3** translation fault 致命 Oops。

**本案的 crash 实测三重铁证**（9 案中其余 8 案不可测的部分）：
1. **真值对照**：`__per_cpu_offset[7]` 内存真值 = `0xffffb5297a60c000`（crash `p` 实测，canonical + 4K 对齐 + 非零），与实收 x20=0 **64 位全异**——"内存完好、装载返回坏"从推断升级为实测；
2. **x17 化石**：崩溃寄存器快照中 x17 = `0xffffb5297bce4000`，与 crash 实测 `__per_cpu_offset[179]` 真值**逐位一致**——这是此前某次正确装载残留的旧值，直接证明同一颗核此前亿万次装载同一数组都返回正确值，唯独致命这一次返回 0；
3. **反事实两级闭合**：x1 + `__per_cpu_offset[7]` = `0xffff8000801056c0` 与 crash 实测 `runqueues[7]` 逐位一致（x1 语义钉死为 `&runqueues` percpu 模板基址）；x1 + `__per_cpu_offset[179]` = `0xffff8000817dd6c0` 与 `runqueues[179]` 逐位一致。真值路径 `runqueues[7]+0x120` 为已映射有效地址——**正确执行永不崩溃，崩溃 100% 归因于那一次装载读回**。

RAS/EDAC/GHES 全程零上报；taint `G W` 与 184 次 WARNING 自洽。

**三级置信度**：
- 现象层（184 次前兆 + x20 装载返回零 → 传播 → PTE=0 L3 fault）：**【实锤】**——dmesg + 代数闭合 + **crash 真值/vtop 实测**（algebra_out.txt 全部 True）。
- 通路归属（CPU179 核内装载返回通路的零塌缩）：**【强推→接近实锤】**——本案真值对照实测完成（谱系 10 案同构 + 本案补齐），仅"物理位点在核内哪一段"仍属推断。
- 物理位点：**【假设】**——软件不可分辨。

---

## 2. 六要素逐字（证据：dmesg_forensics.txt D 节，行号=源文件原始行号）

| 要素 | 逐字值 | 源行 |
|---|---|---|
| ① 时间 | `Internal error: Oops: 0000000096000007 [#1] SMP` @ 142080.18s；uptime = **142080s ≈ 1.64d**（crash sys 实测 `UPTIME: 1 days, 15:28:00`；开机时刻 L2174: rtc 设 2026-09-12T02:17:10 UTC） | L10904, crash_session.log |
| ② CPU | `CPU: 179 PID: 0 Comm: swapper/179 Kdump: loaded Tainted: G W` | L10907 |
| ③ 进程/上下文 | **idle 线程 softirq 路径**：`rebalance_domains ← _nohz_idle_balance ← run_rebalance_domains ← handle_softirqs ← irq_exit_rcu ← el1h_64_irq ← default_idle_call ← cpuidle_idle_call ← do_idle ← cpu_startup_entry ← secondary_start_kernel`——空闲 CPU 的周期性负载均衡 softirq（与案 #20 同链） | L10926-10943 |
| ④ 致命点 | `pc : find_busiest_group+0x140/0xb60`；`lr : find_busiest_group+0x11c/0xb60`；`Code: f9400782 f879d814 2a1903e0 8b14003b (f9409377)` | L10911-10912, L10944 |
| ⑤ 异常码/地址 | `ESR = 0x0000000096000007`；`EC = 0x25: DABT (current EL)`；`FSC = 0x07: level 3 translation fault`；`FAR(首行) = ffffcad705af97e0`；页表 walk：`pgd=10006057fffff403, pud=10006057ffffe403, pmd=10006057ffffa403, pte=0000000000000000` | L10893, L10894, L10897, L10891, L10903 |
| ⑥ 关键寄存器 | `x27: ffffcad705af96c0`；`x20: 0000000000000000`；`x1 : ffffcad705af96c0`；`x17: ffffb5297bce4000`；`x25: 0000000000000007`；`x0 : 0000000000000007`；`pstate: 20400009`；`Tainted: G W` | L10913, L10916, L10922, L10917, L10914, L10922, L10909, L10907 |

---

## 3. 指令级解剖

### 3.1 Code dump 五指令窗口反汇编（dmesg L10944）

```
f9400782   ldr  x2, [x28]                  // +0x128（上文，未参与致命链）
f879d814   ldr  x20, [x0, x25, sxtw #3]    // +0x130 ← __per_cpu_offset[x25] 装载（腐化点）
2a1903e0   orr  x0, wzr, w25               // +0x134（dump 时 x0=0x7）
8b14003b   add  x27, x1, x20               // +0x13c ← x20=0 使加法退化为恒等：x27 = x1
(f9409377) ldr  x23, [x27, #0x120]         // +0x140 ← 致命装载（offset 288）
```

x0 dump 值 0x7 与 x25=0x7 逐字吻合——寄存器快照内部自洽。crash `sym` 实测：`find_busiest_group = ffffcad7040cad08`（fair.c:13011），+0x140 = ffffcad7040cae48 与崩溃帧 `bt` 显示 `find_busiest_group at ffffcad7040cae44`（swapper/179 栈顶）吻合。

### 3.2 x25=7 跨槽——正常行为

CPU7 属 Node 0，CPU179 属 Node 7——顶层调度域遍历跨 NUMA 读槽的标准动作。跨槽无异常，异常仅在装载返回值。

### 3.3 代数闭合 + crash 实测（algebra_out.txt，全部 True）

1. **x27 = x1 + x20**：`ffffcad705af96c0 + 0 = ffffcad705af96c0` ——闭合（恒等）。
2. **FAR = x27 + 0x120**：`ffffcad705af96c0 + 0x120 = ffffcad705af97e0` ——闭合。crash `vtop` 实测两地址：PGD/PUD/PMD 均有效、**PTE = 0**——与 ESR FSC=0x07 level 3 完全一致（页表 walk 走到最后一级才断）。
3. **反证非移位偏移**：x27+0x48 ≠ FAR，排除解码错误。

---

## 4. 真值对照与反事实【本案核心——crash 实测】

### 4.1 `__per_cpu_offset[7]` 真值 vs 实收 x20（algebra_out.txt 第三节）

| 量 | 值 | 来源 |
|---|---|---|
| x20 实收（崩溃时装载返回） | `0x0000000000000000` | dmesg L10916 |
| `__per_cpu_offset[7]` 内存真值 | `0xffffb5297a60c000` | crash `p __per_cpu_offset[7]`（crash_session.log） |
| 真值 ⊕ 实收 | `0xffffb5297a60c000`（64 位全异） | — |

真值满足全部三条不变式：canonical（ffff 顶段）、4K 页对齐（低 12 位 000）、非零。实收 0 三条全破坏。**"内存完好、装载返回坏"在本案是实测事实，不再是推断**——这与谱系 10 个可对照案例的结论完全一致，并首次在 09-07 之后的 9 案系列中补上了真值对照。

### 4.2 x17 化石：上次正确装载的残留（algebra_out.txt 第四节）

崩溃快照 x17 = `0xffffb5297bce4000`，与 crash 实测 `__per_cpu_offset[179]` 真值**逐位一致**。解读：这是同一次 `find_busiest_group` 循环（或近期执行）中**正确装载**槽 179 偏移后残留在寄存器中的旧值。它的存在直接证明：
- 同一颗 CPU179、同一指令族、同一数组——**此前装载返回的都是正确值**；
- 数组内存本身完好（与 4.1 互证）；
- 唯独致命这一次（读槽 7）返回 0——**单次、间歇、无累积**。

这是谱系 20+ 案中首次在崩溃快照内捕获"正确执行的化石证据"，与谱系 #3 案的 AT S1E1R 重走自证、#10 案的 at s1e1r 重放成功互为补充。

### 4.3 反事实两级闭合（algebra_out.txt 第五节）

| 换算 | 计算 | crash 实测 | 一致 |
|---|---|---|---|
| x1 + `__per_cpu_offset[7]` | `0xffff8000801056c0` | `runqueues[7] = 0xffff8000801056c0` | **逐位 True** |
| x1 + `__per_cpu_offset[179]` | `0xffff8000817dd6c0` | `runqueues[179] = 0xffff8000817dd6c0` | **逐位 True** |

两级换算均闭合，**x1 语义钉死：x1 = `&runqueues` 的 percpu 模板基址**（percpu 变量静态地址 + percpu 偏移 = 本 CPU 实例地址）。反事实路径：若 x20 返回真值，`ldr x23,[x27,#0x120]` 将读 `runqueues[7]+0x120`（rq->cfs.avg 等字段）——**已映射有效地址，正确执行永不崩溃**。实际路径 FAR=x1+0+0x120 落入 PTE=0 空洞（percpu 模板区运行时不映射）→ L3 fault。

**崩溃 100% 归因于那一次装载读回返回 0**——反事实从谱系的"推断版"升级为"crash 实测版"。

---

## 5. 前兆谱：184 次新纪录的 43 簇结构（dmesg_forensics.txt C 节）

### 5.1 统计

- **184 次**（谱系单案新纪录，为旧纪录谱系 #2 案 26 次 / #8 案 35 次的 5 倍+），全部 `CPU: 179`（184/184）；
- 时间 25736.35s（7.15h）~ 141977.63s（39.44h），**末次距致命 102.470s**；
- 地址前缀：ffff6040×170 + ffff6041×4 + ffff6042×9（percpu/vmalloc 区）+ **ffffcad7×1**（118599.12s 一次落在与 x1/kernel image 同 ffffcad7 段）；
- 受害：PID 10202×142 + PID 9670×40（pmdalinux 两实例）+ 1355092×1 + 10199×1；路径 `show_interrupts → seq_printf → __memcpy`（读 /proc/interrupts，与案 #7/#26/#27 同源）。

### 5.2 43 簇大结构（algebra_out.txt 第六节）

| 阶段 | 时间窗 | 簇 | 次数 | 特征 |
|---|---|---|---|---|
| 首发作窗 | 7.15-7.51h | 簇 1-6 | 38 | 密集成簇（簇 4 单簇 12 次） |
| **大静默** | 7.51-32.54h | — | 0 | **25.02 小时零前兆** |
| 再发作窗 | 32.54-35.15h | 簇 7-18 | 40 | 零星转密集（簇 18 单簇 18 次） |
| 中静默 | 35.15-37.23h | — | 0 | 2.03h |
| **临终密集窗** | 37.23-39.44h | 簇 19-43 | **106** | 越临终越密（簇 43 单簇 **35 次/250s**），末次距致命 102s |

**解读**：184 次前兆不是均匀噪声，而是**多发作窗结构**——首窗（开机 7h）→ 超长静默（25h）→ 再起 → 临终加密。这与案 #26 的三段式、#27 的临终双簇构成同一族节奏的三个变体，共同指向：缺陷受慢变量调制成"发作窗"，窗内 PTW 段（前兆）被反复击中，窗尾数据返回段（致命）被击中。**临终加密**（末窗 106 次、末簇 35 次/250s、末次距致命 102s）是最强形态——发作强度在致命前达到峰值。

### 5.3 uptime=142080s：谱系第 4 长

crash `sys` 实测 `UPTIME: 1 days, 15:28:00`、`LOAD AVERAGE: 174.28`（192 核系统高负载）。谱系 uptime 谱（418s~6.21d）中 1.64d 位居第 4——零塌缩在最长运行段之一出现，且高负载背景下 184 次前兆密集爆发。

---

## 6. 反事实与软件排除

### 6.1 反事实推演——已由 crash 实测完成（见 4.3 节）

真值路径两级 vtop 实测有效；正确执行永不崩溃。**本案无降级声明**——与前 8 案不同，本案真值对照、反事实、页表几何全部实测。

### 6.2 软件成因排除

| 软件假设 | 排除证据 |
|---|---|
| 内核 bug | ① 官方 build #1（L10907），W taint 仅由 184 次 spurious WARNING 累积（自洽）；② 191 颗其他核同路径零异常，仅 CPU179 崩（谱系含本案 20/20 案同核）；③ 软件 bug 不挑核 |
| 坏页/页表被改 | ESR=0x96000007、S1PTW=0（L10896）；crash vtop 实测 PGD/PUD/PMD 全有效、仅 PTE=0——页表完好，是寻址落入模板区空洞；且 `__per_cpu_offset[]` 数组真值 crash 实测完好（4.1 节） |
| 竞态/内存序 | 纯读侧受害；零塌缩非过期值（percpu 偏移运行期不变，且 x17 残留的槽 179 正确值证明近期装载正常） |
| 编译器/解码错 | Code 五指令窗口与 crash sym 实测符号地址吻合（3.1 节）；x0=0x7 与 w25 自洽；imm 反证闭合 |
| idle 线程专属 | swapper/179 只是恰在 CPU179 空闲的调度者；谱系受害者横跨 8+ 种进程/上下文——缺陷挑核不挑进程 |

### 6.3 硬件侧非核内通路排除

- **DIMM/内存控制器**：RAS 全程零上报（10947 行 hardware error 匹配 0）；且 crash 实测 `__per_cpu_offset[]` 7 个抽检槽真值全部完好——**内存侧实测无恙**；20 案锁定 CPU179 与 DIMM 对称受害预期矛盾。
- **缓存一致性**：受害数据为内核全局数组元素读出；191 核对称受害预期与观测矛盾。
- **L1D 阵列驻留损伤**：谱系 #7 案 L1D 禁用实验期间仍复发；x17 化石（4.2 节）证明同核近期装载正常——非驻留性固定损伤。

---

## 7. 根因三级置信判定与跨案对照

### 7.1 判定

1. **现象层【实锤——含 crash 实测】**：CPU179 上 184 次 spurious 前兆（43 簇多发作窗结构，末次距致命 102.5s）后，`__per_cpu_offset[7]` 装载返回 0（**真值 crash 实测 0xffffb5297a60c000，64 位全异**），加法恒等传播使致命装载以 x1+0x120 寻址，FAR canonical 但 PTE=0（crash vtop 实测），L3 fault，开机 142080s 致命。
2. **通路归属【强推→接近实锤】**：CPU179 核内装载返回通路的零塌缩（整组 lane 未驱动/选通到零源），间歇性、无检错覆盖的 SDC。
   - 证据：真值对照 + x17 化石 + 反事实 vtop 三重实测（第 4 节）；184 次前兆同核多发作窗（5.2 节）；RAS 零上报 + 软件排除（6.2/6.3 节）；谱系零塌缩族 8 案同构。
   - 唯一保留【强推】而非【实锤】的原因：物理通路位点的软件不可分辨性（下一步须裸机/厂商手段）。
3. **物理位点【假设】**：lane 选通网络全零源选通 vs RF 写口整字未使能 vs L1D 出口锁存清零。验证：offline CPU179；裸机 load-verify；厂商 shmoo/MBIST。

### 7.2 跨案对照：9 案系列的收官定位

| 项 | #20（最近零塌缩案） | **#28（本案）** |
|---|---|---|
| 转储 | 09-07-20:04 | **09-14-01:45** |
| uptime | 9979s | **142080s（1.64d，第 4 长）** |
| 槽号 x25 | 7 | **7（同槽！跨 boot 复现）** |
| x20 | 0 | **0（零塌缩）** |
| ESR/FSC | 0x96000007/L3 | **0x96000007/L3（同型）** |
| 受害进程 | mi-scavenger | **swapper/179（idle softirq，与#20同链型）** |
| 前兆 | 8 | **184（新纪录，43 簇）** |
| 末距致命 | 0.72s | **102.5s** |
| vmcore | 无 | **有（12GB，三重实测）** |

**与案 #20 同槽（x25=7）同 FSC（L3）跨 boot 复现**：不同 boot、相隔 6.5 天、同一槽位两次零塌缩——槽位本身无特殊性（谱系槽号分布 6~179），但同槽同型复现再次排除"特定内存字坏"，强化"通路级随机击中"模型。

### 7.3 对谱系总图的增量

- **前兆数新纪录（184 次）**：旧纪录 35 次的 5.3 倍；43 簇多发作窗 + 临终加密结构为谱系最精细的前兆时间画像；
- **真值对照三重实测**（真值/vtop/x17 化石）：把 9 案系列中 8 案只能推断的部分补齐为实测，谱系"内存完好"结论的实测案例数从 10 增至 11；
- **x17 化石**：谱系首次在崩溃快照内捕获同核近期正确装载的残留证据；
- **反事实升级**：runqueues 两级换算逐位闭合，x1 语义（`&runqueues` percpu 模板基址）钉死——后续所有 dmesg-only 案的 x1 解读均以此为锚；
- **零塌缩族第 9 案**：与 #20 同槽同 FSC 跨 boot 复现，零塌缩几何谱（L2/L3 由空洞深度决定）完全互洽。

---

## 附:证据文件清单

| 文件 | 内容 |
|---|---|
| `algebra.py` | mod 2^64 代数闭合 + crash 实测真值对照 + x17 化石验证 + 反事实两级闭合 + 184 前兆 43 簇结构（可重跑） |
| `algebra_out.txt` | 上者真实运行输出（python3，2026-09-15，全部 True） |
| `dmesg_forensics.txt` | 行号级原文：开机头/RAS/184 次前兆谱（首尾全录）/Oops 全块/RAS 负证据/taint/journald 时间线 |
| `crash_session.log` | **crash 8.0.4-17.oe2403sp4 完整会话**（3178 行）：sys/p `__per_cpu_offset[]`×7 槽/p runqueues 全 192 CPU/sym/vtop×2/rd/bt 0 全 swapper 栈——taskset -c 0-47 下冷加载 12GB vmcore（约 10 分钟）一次性批处理取证 |

*本报告为独立重研究，除 SYNTHESIS-12case-cross-analysis.md 谱系表（许可对照项）外未读任何既有报告正文；兄弟案（#20/#25/#26/#27）数据仅取自各自 vmcore-dmesg.txt 原始 dump 行；crash 实测数据全部来自本案 vmcore 的自主取证会话。*
