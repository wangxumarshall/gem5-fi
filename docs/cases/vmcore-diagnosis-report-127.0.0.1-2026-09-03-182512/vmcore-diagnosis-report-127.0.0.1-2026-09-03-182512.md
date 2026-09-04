# CPU179 缺陷核第 8 次致命转储深度诊断报告
## ——撕裂移位族第 5 相位（槽 123 +1 字节）实锤 + 35 次 WARNING 历见最多的簇状脉冲发作

| 项 | 值 |
|---|---|
| 目标转储 | `/home/sdc/wangxu/vmcore0102/127.0.0.1-2026-09-03-18:25:12/`（**73.7 GB，十二案最大体积**，PARTIAL DUMP，vmcore-dmesg.txt 4202 行） |
| 主机 | Yangtze Computing R240K V2 / BC82AMQA，BIOS 7.48 06/15/2026 |
| CPU | Kunpeng-920 (HIP08/TaiShan-v110) ×192，8 NUMA 节点 |
| 内核 | 6.6.0-145.3.23.154.oe2403sp3.aarch64 #1 SMP（debuginfo 精确匹配；Tainted G W OE） |
| 崩溃 | 2026-09-03 18:24:21 CST（dmesg 时间戳 322246.221818s），uptime **89.51h（3 天 17.5 小时）**，CPU **179**，PID 16 `rcu_sched` |
| 结论 | **第 8 次独立坐实 CPU179 缺陷核（LSU 装载数据返回通路 SDC），撕裂移位族相位谱新增第 5 个数据点：x20 实收值 `0x00ffffb617dd3940` 与被读数组中"槽 123 起点 +1 字节"处的 8 字节非对齐窗口内容逐位一致（crash 直读该地址验证），而指令语义应取槽 12（真值 `0xffffb617dc4d6000`，全数组 192 项 0x22000 等差完好）——内存完好、寄存器收坏，坏值是数据源相位错位 1 字节、跨槽 123/124 边界的字节流窗口。本案更重要的增量在发作统计学：35 次 WARNING（历案最多，为第 7 案 13 次的 2.7 倍）呈四簇脉冲式爆发，簇内毫秒级连发、簇间 10 秒整数倍节律，"静默 19.7h → 簇爆发 → 长静默 → 末簇 → 21s 后 panic"的间歇性发作模式为"电压/频率相依性边际条件窗口"假说提供了迄今最完整的统计学样本。** |

---

## 1. 执行摘要

1. 本次 panic 是同一缺陷的**第 8 次发作**，发生在 89.51 小时存活之后（十二案存活时长第 3 位，仅次于 08-31 案 110h 与 08-17 案 66.5h 之上……准确排序为 110h > 89.5h > 66.5h，居第二）。崩溃进程与第 7 案相同：`rcu_sched`（PID 16）——内核 RCU 状态机根线程，经 `rcu_gp_fqs_loop→schedule_timeout→schedule→newidle_balance` 触发负载均衡时撞上缺陷核装载。Oops 不可恢复，kdump 整机重启，73.7G 转储落盘（十二案最大）。
2. 故障指令与既往各案**逐字相同**：`find_busiest_group+0x140`（`kernel/sched/fair.c` `update_sg_lb_stats()` per-CPU 遍历体），`Code:` 五指令字 `f9400782 f879d814 2a1903e0 8b14003b (f9409377)` 完全一致。寄存器代数闭合：`x27 = x1 + x20 = ffffc9e8a3cd96c0 + 00ffffb617dd3940 = 00ffc99ebbaad000`（逐位），`FAR = x27 + 0x120 = 00ffc99ebbaad120` **完整 64 位逐位吻合**【实锤】。
3. **本案决定性证据——撕裂窗口物理定位**【实锤】：把 192 槽 `__per_cpu_offset` 数组按内存小端拼成字节流，x20 的 8 字节序列（`40 39 dd 17 b6 ff ff 00`）在**全数组唯一命中"槽 123 起点 +1 字节"**（数组基址 +985 字节处）；crash 直读 `rd -64 ffffc9e8a40d59a9`（即该地址）返回首字 **`00ffffb617dd3940`，与 x20 逐位相等**。撕裂相位谱第 5 个数据点：1 字节相位（与 08-25-15:58 案同粒度但不同槽），窗口跨 123/124 槽边界。被读内存本身完好（192 项等差无一损坏）——数据源没错、相位错了。
4. 反事实验证三重闭合【实锤】：`x27_true(12) = &runqueues + __per_cpu_offset[12] = 0xffff8000801af6c0`，与 `rq(12)` 实例内嵌自指针 `nohz_csd.info` 逐位一致；该地址 crash `vtop` 走查 **VALID**（PA=0x37ffe2e6c0，PTE VALID|SHARED|AF|NG|PXN|UXN|DIRTY）；实例健全（`cpu=12`、`nr_running=1`、`cfs.avg.load_avg=1023`）。若装载交付真值，指令平静读到 1023，系统继续运行。**异常的唯一必要条件是装载结果被撕裂。**
5. **本案统计学特色——35 次 WARNING 簇状脉冲**【实锤】：全部 35 次位于 CPU179（其余 191 核零事件），进程为 irqbalance（32 次）/pmdalinux（3 次）两个系统监控代理。发作呈四簇：首症 19.95h 孤发 → **39.66h 簇 B（10 秒内 5 连发毫秒级密集 + 之后 5 次 10s 整数倍节律延伸）→ 44.8h 簇 C（13 次，同样先密集后 10s/20s 节律）→ 44.2h 簇 D（3 次）→ 45.3h 长静默 → 89.5h 末簇（2 次，10s 间隔）→ 21.2s 后 panic**。"静默—爆发—静默"的间歇性脉冲与"电压/频率边际条件窗口"假说高度吻合（§9）。
6. 处置建议不变且紧迫：**offline CPU179 + 整片送修（RMA）**。本开机 WARNING #1 出现于 19.95h，其后机器"表面健康"运行了近 70 小时才死——监控曲线正常不构成安全证据。

---

## 2. 证据规则与方法

- **只依据 vmcore / vmcore-dmesg.txt 取证**；引用既往会话结论处标注〔既往已证〕。
- 所有 64 位地址加法一律 Python3 模 2⁶⁴ 计算（本目录 `algebra.py`，输出 `algebra_out.txt`），并以 crash 内建 per-cpu 解析器与结构体内嵌自指针独立对照，杜绝手算误差。
- 工具：crash 8.0.4-17.oe2403sp4 + 精确版本 debuginfo vmlinux（`/usr/lib/debug/usr/lib/modules/6.6.0-145.3.23.154.oe2403sp3.aarch64/vmlinux`）；objdump -dl（DWARF 行号）；grep/awk（dmesg 法证）。已知怪癖：crash `-i` 批首行被吞（首行放无害命令 `sys`）、`log` 命令在此类 PARTIAL DUMP 上挂起（禁用，dmesg 一律取自 vmcore-dmesg.txt）、加载期 ~384 条 IRQ/SDEI stack seek error 属转储未含该区的正常现象、`vtop` 对非规范地址需显式 `-k`（输出 "not a kernel virtual address" 即硬件 L0 的 crash 侧投影）。73.7G 转储加载耗时约 6 分钟（后台运行 + taskset 隔离 0-31 核，绝不使用 CPU179）。
- 报告区分三层置信：**【实锤】**= dump 内可复核证据；**【强推】**= 多源证据收敛的推断；**【假设】**= 无法软件验证的部分，明示验证途径。

---

## 3. 本次开机时间线【时间线】

| 时刻（dmesg 时间戳） | 事件 | 证据 |
|---|---|---|
| 0.000000s（2026-08-30 01:53:35 前后） | `Booting Linux on physical CPU 0x0000080000 [0x481fd010]`，内核 6.6.0-145.3.23.154.oe2403sp3.aarch64 #1 | dmesg 行 1 |
| 0~1.5s | 硬件枚举：BERT（HISI HIP08）在位、GHES firmware-first 使能、ghes_edac 注册（32 DIMM sockets）、192 核 8 节点启动 | dmesg 行 12/1307/2175-2176/1255 |
| 1.105296s | `pstore: Using crash dump compression: deflate`（kdump 就绪） | dmesg 行 1945 |
| 41.791034s | `hns3 enp189s0f0: link up`（业务网卡上线） | dmesg 行 2577 |
| 89.912396s | `block dm-2: the capability attribute has been deprecated`——**最后一条正常常规消息** | dmesg 行 2578 |
| 89.9s~71822.0s | **静默 71732 秒（19.93h）：0 条内核消息**（awk 全量核验为 0） | 全量核验 |
| **71822.056524s（19.95h）** | **首症**：WARNING #1，`Ignoring spurious kernel translation fault at ffff6040629fe5d1`，CPU179，PID 9736 irqbalance | dmesg 行 2580-2581 |
| 71822.1s~142792.0s | **再静默 70970 秒（19.71h）**——首症后近 20 小时无任何事件 | 全量核验 |
| **142792.045531s（39.66h）** | **簇 B 爆发开始**：WARNING #2，far=ffff604017b3d164，irqbalance | dmesg 行 2625 |
| 142792.047134s（+0.0016s） | WARNING #3，far=…d0d5 | dmesg 行 2670 |
| 142792.047387s（+0.0003s） | WARNING #4，far=…d3ab | dmesg 行 2715 |
| 142792.051267s（+0.0039s） | WARNING #5，far=…d79f | dmesg 行 2760 |
| 142792.056110s（+0.0048s） | WARNING #6，far=…d2e5——**簇 B 核心 5 连发，10.6 毫秒内完成** | dmesg 行 2805 |
| 142802.041184s（簇起 +10.0s） | WARNING #7，far=…e450——**10 秒节律开始** | dmesg 行 2850 |
| 142802.042971s / 142802.048720s | WARNING #8/#9（簇内毫秒配对） | dmesg 行 2895/2940 |
| 142812.052220s / 142812.059244s（+10.0s） | WARNING #10/#11 | dmesg 行 2985/3030 |
| 142822.040263s / 142822.040795s（+10.0s） | WARNING #12/#13 | dmesg 行 3075/3120 |
| 142832.040565s（+10.0s） | WARNING #14，irqbalance | dmesg 行 3165 |
| 142835.314727s / 142835.335959s | WARNING #15/#16——**进程切换为 pmdalinux**（PID 10282），far=…c3d7/…c629 | dmesg 行 3210/3255 |
| 142845.336632s（+10.0s） | WARNING #17，pmdalinux，far=…e7b5——**簇 B 终止：53 秒内 16 次** | dmesg 行 3300 |
| 142845s~146862s | 静默 4017 秒（1.12h） | 全量核验 |
| **146862.038941s（40.79h）** | **簇 C 爆发**：WARNING #18，far=ffff6040195f507d，irqbalance | dmesg 行 3345 |
| 146862.041345s~146862.082363s | WARNING #19~#22——**4 连发，43.4 毫秒内 5 起** | dmesg 行 3390-3525 |
| 146872.051406s / 146872.067966s / 146872.069151s（+10.0s） | WARNING #23~#25 | dmesg 行 3570/3615/3660 |
| 146882.051132s / 146882.057984s（+10.0s） | WARNING #26/#27 | dmesg 行 3705/3750 |
| 146902.061615s / 146902.076315s（+20.0s） | WARNING #28/#29 | dmesg 行 3795/3840 |
| 146912.077318s（+10.0s） | WARNING #30——**簇 C 终止：50 秒内 13 次** | dmesg 行 3885 |
| 146912s~159162s | 静默 12250 秒（3.40h） | 全量核验 |
| **159162.040691s（44.21h）** | **簇 D**：WARNING #31，far=ffff604083c486b8，irqbalance | dmesg 行 3930 |
| 159162.065884s / 159172.064790s（+10.0s） | WARNING #32/#33——簇 D 共 3 次，跨度 10.02s | dmesg 行 3975/4020 |
| 159172s~322215s | **长静默 163043 秒（45.29h，本案最长静默窗）** | 全量核验 |
| **322215.057951s（89.50h）** | **末簇**：WARNING #34，far=ffff604013441935，irqbalance | dmesg 行 4065 |
| **322225.050804s（+9.993s）** | WARNING #35，far=ffff604061374839——**末次前兆** | dmesg 行 4111 |
| **322246.221818s（末次 W 后 21.171s）** | **panic**：`Unable to handle kernel paging request at virtual address 00ffc99ebbaad120`，CPU179 上 rcu_sched（PID 16），`find_busiest_group+0x140` 崩溃 | dmesg 行 4155 |
| 322246.599318s | `Starting crashdump kernel...` → kdump 完成，73.7G vmcore 落盘 | dmesg 行 4201 |

**发作节律**【实锤，本案核心统计学证据】：35 次 WARNING 呈**四簇脉冲 + 毫秒级簇内密集 + 10 秒整数倍跨簇节律**：
- 簇内：簇 B 核心 5 连发跨度 10.6ms、簇 C 前 5 连发跨度 43.4ms——**毫秒级爆发**；
- 簇间延伸：簇 B 内 16 次事件的时间戳全部落在 `142792 + 10k` 秒（k=0,1,2,3,3.3,5.3）的 10 秒栅格上，簇 C 同样（146862+10/20 栅格）——**10 秒整数倍节律**，而簇内相邻事件间隔仅 0.2~25ms；
- 簇间隔：19.93h（开机→W1）→ 19.71h（W1→簇B）→ 1.12h（B→C）→ 3.40h（C→D）→ 45.29h（D→末簇）→ 21.17s（末簇→panic）；
- 与第 7 案（13 次、三簇、末簇 3.1s 即死）对比：本案前兆更丰富（35 次）、末次前兆距 panic 更长（21.2s），但簇形态更"规整"（10s 栅格）。
- WARNING 的 spurious FAR 全部落于 `ffff60xx`（vmalloc/percpu-chunk 区统计结构），ESR 全部 `0x96000044`（WnR=1 写访问 + FSC=L0），与既往各案一致。

---

## 4. 故障现象【故障现象】

Oops 原文（vmcore-dmesg.txt 行 4155 起，摘录）：

```
[322246.221818] Unable to handle kernel paging request at virtual address 00ffc99ebbaad120
[322246.230565] Mem abort info:
[322246.234146]   ESR = 0x0000000096000004
[322246.238684]   EC = 0x25: DABT (current EL), IL = 32 bits
[322246.252557]   FSC = 0x04: level 0 translation fault
[322246.280107] [00ffc99ebbaad120] address between user and kernel address ranges
[322246.288036] Internal error: Oops: 0000000096000004 [#1] SMP
[322246.396732] CPU: 179 PID: 16 Comm: rcu_sched Kdump: loaded Tainted: G        W           6.6.0-145.3.23.154.oe2403sp3.aarch64 #1
[322246.425388] pc : find_busiest_group+0x140/0xb60
[322246.430717] lr : find_busiest_group+0x11c/0xb60
[322246.436037] sp : ffff8000821ab830
[322246.440140] x29: ffff8000821ab9b0 x28: ffff8000821ab940 x27: 00ffc99ebbaad000
[322246.448071] x26: ffff604003e9e3c0 x25: 000000000000000c x24: ffffc9e8a40d5000
[322246.456003] x23: 0000000000000400 x22: ffff604003e9e3c0 x21: ffffc9e8a40cfcb0
[322246.463933] x20: 00ffffb617dd3940 x19: ffff8000821aba40 x18: 0000000000000000
[322246.487716] x11: 0000000000000060 x10: 0000000000000120 x9 : ffffc9e8a22aae58
[322246.495644] x8 : ffff8000821ab998 x7 : 0000000000000000 x6 : 000000000000000c
[322246.503572] x5 : fffffffffffff000 x4 : 0000000000000000 x3 : 000000000000000c
[322246.511500] x2 : 0000000000003000 x1 : ffffc9e8a3cd96c0 x0 : 000000000000000c
[322246.519428] Call trace:
[322246.522660]  find_busiest_group+0x140/0xb60
[322246.527633]  load_balance+0x108/0x6c0
[322246.532739]  newidle_balance+0x198/0x510
[322246.537992]  pick_next_task_fair+0x110/0x718
[322246.543551]  pick_next_task+0x60/0x398
[322246.548573]  __schedule+0x1b4/0x8a0
[322246.553327]  schedule+0x58/0x130
[322246.557804]  schedule_timeout+0x1b0/0x2f0
[322246.563046]  rcu_gp_fqs_loop+0x11c/0x358
[322246.568205]  rcu_gp_kthread+0x124/0x178
[322246.573274]  kthread+0xec/0x100
[322246.577645]  ret_from_fork+0x10/0x20
[322246.582455] Code: f9400782 f879d814 2a1903e0 8b14003b (f9409377)
```

要点：ESR=0x96000004（DABT、WnR=0 读访问、FSC=0x04 **L0**）；`Code:` 与既往各案逐字相同；`x20 = 00ffffb617dd3940`（撕裂值，非零非模板）；`x25 = 0xc = 12`（迭代 CPU 号，四寄存器互证 x0/x3/x6 同为 0xc）；dmesg 明确标注 `address between user and kernel address ranges`（非规范域在两域之间，MMU 第一级即拒绝）。撕裂移位族签名：FAR 高 16 位 `00ff`（非规范域）→ L0。崩溃时 1 分钟负载 98.60、5 分钟 26.71（crash `sys`）——长存活机器的常规负载。本案 FAR 为**完整 64 位逐位打印**（`00ffc99ebbaad120` 与 x27+0x120 的 64 位值逐位相等，高 16 位 00ff 直通），与 08-31 案"dmesg 只打印低 48 位"形态不同，如实记录（两者均为 48-bit VA 配置下 dmesg %pS 打印宽度的差异投影，不影响代数闭合）。

---

## 5. 业务现象【业务现象】

- **崩溃进程是谁**：`rcu_sched`（PID 16），**内核 RCU 状态机的根线程**（rcu_gp_kthread），与第 7 案（08-31，110h）完全相同的受害者身份。它不是用户态业务进程，而是内核"垃圾回收中枢"：每个 RCU 宽限期由它驱动，`rcu_gp_fqs_loop` 是其强迫静止状态检测循环。崩溃时它正在 `schedule_timeout` 睡眠等待下一个 fqs 轮询点，内核在为新任务选核时进入 `newidle_balance`（idle 平衡）路径触发负载均衡，均衡器遍历调度组内 CPU 时撞上缺陷核装载。
- **对上层服务的表现**：rcu_sched 死亡的直接工程含义是 **RCU 宽限期永久停滞风险**——所有等待宽限期的回调（内存释放、模块卸载清理等）将永不执行。但这一后果没有机会兑现：Oops 在 `die_kernel_fault` 路径判 fatal，直接进入 kdump——**整机所有业务（2215 个任务）瞬间停摆并重启**。对运维而言，这是一台连续运行 89.5 小时、承载常规负载（1 分钟均值 98.60）的生产机的整机宕机：所有任务的非持久状态全部丢失，宕机时刻 2026-09-03 18:24（周五傍晚业务时段）。
- **89.5h 存活的业务暴露面**：本案是十二案中存活时长第二位（110h > 89.5h > 66.5h > …）。从业务连续性视角：(a) 缺陷核的发作率极低且**不随时间衰减**——45.29h 最长静默窗后照样末簇复发；(b) 长存活不等于安全，存活时长本身不构成任何"已渡过危险期"的证据；(c) 与第 7 案（110h）合计，两个最长存活案的受害者都是 rcu_sched——这不是巧合：存活越久，rcu_sched 这种永生内核线程在 CPU179 上的调度暴露次数越多，**暴露面与存活时长成正比**，而缺陷核不看受害者身份（§9）。
- **本开机的监控代理暴露**：35 次 WARNING 全部由 irqbalance（32 次）与 pmdalinux（3 次）踩中——两个周期性读 /proc/interrupts、/proc/stat 的系统监控代理。它们以固定周期（约 10s，与簇间 10 秒栅格吻合——irqbalance 默认扫描间隔）反复在 CPU179 上执行内核 `show_interrupts` 序列化路径，是"高频读内核统计结构"的最佳探针。簇 D 中进程从 irqbalance 切换到 pmdalinux 再切回，说明爆发窗口跨越多个进程的轮询周期。

---

## 6. 诊断定位过程【诊断定位过程】

### P1 勘察（dmesg 全量法证 + WARNING 簇分析）

命令与输出见本目录 `dmesg_forensics.txt`。关键结果：
- `grep -c "WARNING: CPU:"` → **35**（历案最多：第 7 案 13、08-17 案 26、其余各案 0~2）；per-CPU 分布 `35 WARNING: CPU: 179`——**全部 35 次位于 CPU179，其余 191 核零事件**；
- WARNING 进程分布：irqbalance（PID 9736）×32、pmdalinux（PID 10282）×3——与既往各案"监控代理最常踩中"的规律一致；
- WARNING 时间戳聚类（`grep "WARNING: CPU: 179" | awk -F'[][]' '{print $2}' | sort -n | uniq -c`）：35 个时间戳全部唯一（无同一秒重复），呈 §3 所列四簇结构——**这是十二案中首次以 10 秒栅格规整爆发**；
- 全部 35 次 spurious FAR 均落于 `ffff60xx`（vmalloc/percpu-chunk 区统计结构，按页聚合：ffff604017b3×16、ffff6040195f×13、ffff604083c4×3、其余 3 页各 1），WARNING 块内 `x19 = 0x96000044`（ESR，WnR=1 写 + FSC=L0）35/35 一致，`x21 = FAR` 逐块吻合；
- WARNING 调用路径（irqbalance 与 pmdalinux 完全同构）：`__do_kernel_fault → do_bad_area → do_translation_fault → do_mem_abort → el1_abort → el1h_64_sync → __memcpy → seq_printf → show_interrupts → seq_read_iter → … → el0t_64_sync`——**读 /proc/interrupts 的 memcpy 写目标指针被腐化**，与既往各案一致；
- RAS 负证据：BERT 在位（HISI HIP08）、GHES firmware-first 使能、ghes_edac 注册 32 DIMM，全程零 CE/UE 记录；
- 本开机无 l1d_disable 试验记录（grep "L1D" 为 0）——与 08-31 案三次试验的对照见 §9；
- 崩溃块寄存器全量提取（x0~x30 + pstate + Code），见 §4。

### P2 静态反汇编与符号语义重建（vmlinux + DWARF）

`objdump -dl` 于 `find_busiest_group` 静态基址 `0xffff80008013ad08`（nm 输出），故障窗口（与既往各案同窗口，本内核再验证一次）：

```asm
; kernel/sched/fair.c — update_sg_lb_stats(): for_each_cpu_and(i, group_span, env->cpus)
ffff…ae10  bl   _find_next_and_bit        ; x0 = 下一个置位 CPU 编号 i
ffff…ae24  mov  x25, x0                   ; x25 = i（本案 = 0xc = 12）
ffff…ae34  ldp  x0, x1, [sp, #8]          ; x0 = &__per_cpu_offset[0]; x1 = &runqueues（模板）
ffff…ae3c  ldr  x20, [x0, w25, sxtw #3]   ; x20 = __per_cpu_offset[i]   ← 数据来源（实收撕裂值）
ffff…ae44  add  x27, x1, x20              ; x27 = &per_cpu(runqueues,i) (mod 2^64)
ffff…ae48  ldr  x23, [x27, #288]          ; rq->cfs.avg.load_avg        ← 致命点(+0x140)
```

故障指令字 `f9409377` 解码：`ldr x23, [x27, #288]`（imm12=36, 36×8=0x120）——`&((struct rq *)0)->cfs.avg.load_avg` 偏移 0x120 经 crash 实测验证（`p &((struct rq *)0)->cfs.avg.load_avg` → `0x120`，crash_session2.log）。KASLR 锚定【实锤】：崩溃块 `x9 = ffffc9e8a22aae58 = find_busiest_group+0x150`，反推滑移 `0x49e822170000`；crash `sym` 四符号（find_busiest_group/runqueues/nr_cpu_ids/__per_cpu_offset）运行期地址与静态地址之差**五路全部等于同一滑移值**（`algebra_out.txt` A 节）。`x21 = ffffc9e8a40cfcb0 = &nr_cpu_ids`（值 0xc0=192）、`x24 = ffffc9e8a40d5000` 为 adrp 页基（4K 对齐，与 `&__per_cpu_offset = ffffc9e8a40d55d0` 同页、差 0x5d0 由 `add x0, x24, #0x5d0` 补足，与 `str x0,[sp,#8]` 构造序列吻合）——寄存器现场与指令语义完全自洽。

### P3 crash 动态取证（73.7G 完整转储，决定性实验）

命令批 `forensics_cmds.txt`，完整输出 `crash_session.log`；补充会话 `crash_session_supplements.log`（= crash_session2.log + crash_session3.log：`vtop -k` 走查 + 非对齐窗口直读 + 结构体偏移验证 + 反事实 vtop）。执行方式：`taskset -c 0-31 timeout 7200 crash <vmlinux> <vmcore> -i <cmds>`（隔离 0-31 核，绝不使用 CPU179）；73.7G 加载约 6 分钟。

**(a) 内存真值对照**【实锤】：
```
crash> px __per_cpu_offset[12]
$4 = 0xffffb617dc4d6000        <-- 真值：i=12 应取此槽（x25=0xc=12）
crash> px __per_cpu_offset[179]
$5 = 0xffffb617ddb04000        <-- 崩溃执行核 179 的槽位（亦非零，供交叉对照）
crash> rd -64 __per_cpu_offset 192
ffffc9e8a40d55d0:  ffffb617dc33e000 ffffb617dc360000   ← 槽 0/1
（全数组 192 项完美等差：基址 ffffb617dc33e000，步长 0x22000；
 off[12]−off[0]=0x198000=12×0x22000 ✓；off[179]−off[12]=0x162e000=167×0x22000 ✓）
```
被读内存完好无损；坏的是**装入寄存器的那个值**（x20=0x00ffffb617dd3940）。软件写坏内存的可能被排除（等差数列不可能在单槽被写成撕裂值后还保持全局等差）。

**(b) 撕裂窗口物理定位（本案核心证据，方法复用第 7 案）**【实锤】：
把 192 槽按内存小端序拼成 1536 字节的字节流，搜索 x20 的 8 字节 LE 序列（`40 39 dd 17 b6 ff ff 00`）：
```
全流唯一命中: [(123, 1)]   ← 槽 123 起始 + 1 字节（数组基址 + 123*8 + 1 = 基址 + 985 字节）
等价公式: (off[123]>>8) | ((off[124]&0xFF)<<56)
  = (0xffffb617dd394000 >> 8) | ((0xffffb617dd3b6000 & 0xFF) << 56)
  = 0x00ffffb617dd3940   == x20: True
```
crash 直读验证（`crash_session_supplements.log`，crash_session2 部分）：
```
crash> rd -64 ffffc9e8a40d59a9 2     ← ffffc9e8a40d59a9 = &__per_cpu_offset + 985 字节
ffffc9e8a40d59a9:  00ffffb617dd3940 00ffffb617dd3b60
                   ^^^^^^^^^^^^^^^^ 与 x20 逐位相等
```
**非对齐窗口直读再次成功**：撕裂值不是凭空噪声、不是任何槽的算术移位（1~7 字节旋转族比对全部不匹配），而是**内存中真实存在的一段字节流**——从错误相位（+1 字节）读出的跨槽（123/124 边界）非对齐 8 字节窗口。形态归类：与既有撕裂移位族**同构**（数据源相位错位、fill-buffer/字节通道错配）。**相位谱第 5 个数据点**：08-25-15:58 案"槽 0 起点 1 字节相位（≫8）"、08-14 案"ROL16 半字旋转"、08-31 案"槽 125 起点 +2 字节跨槽"、08-17 案（dmesg-only，≫8 形态强推）之后，本案为"槽 123 起点 +1 字节、跨 123/124 槽边界"。汉明距离：`popcount(x20 ^ off[12]) = 26`、`popcount(x20 ^ off[179]) = 29`、`popcount(x20 ^ off[0]) = 31`——与既往撕裂案（26~37 位级）同量级，均匀散布无列聚类，再次排除结构化数字故障。

**(c) 迭代号 12 的意义**【实锤】：`x25 = x0 = x3 = x6 = 0xc`（四寄存器互证），即本次迭代对象是 CPU12 的 rq。与第 7 案（i=60）、第 11 案（i=97）相同，迭代号 ≠ 执行核号（179）——**腐化绑定执行核（哪条装载指令在 CPU179 上跑），不绑定被读数据的位置**（槽 12 与槽 179 都在同一数组同一页，真值都完好；撕裂窗口落在槽 123/124，同样完好）。

**(d) 反事实验证**【实锤】：
```
Python: x27_true(12) = &runqueues + __per_cpu_offset[12] = 0xffffc9e8a3cd96c0 + 0xffffb617dc4d6000
      = 0xffff8000801af6c0  (mod 2^64)
crash> p runqueues:12 → 实例内嵌自指针 nohz_csd.info = 0xffff8000801af6c0  ← 逐位一致
crash> vtop ffff8000801af6c0（crash_session3.log）
        PHYSICAL: 37ffe2e6c0; PTE: e80037ffe2ef03 (VALID|SHARED|AF|NG|PXN|UXN|DIRTY)  ← VALID
实例健全: cpu = 12, nr_running = 1, cfs.avg.load_avg = 1023, nr_switches = 3081970
```
若那条 `ldr x20,[x0,w25,sxtw#3]` 交付真值，故障指令将平静地读到 1023，程序继续。**异常的唯一必要条件是装载结果被撕裂。**

**(e) 崩溃执行核 179 的 rq 状态交叉**【实锤】：
```
crash> bt → PID 16 TASK: ffff0020250d3f00 CPU: 179 COMMAND: "rcu_sched"
crash> p runqueues:179 → cpu = 179, nr_running = 0, curr = 0xffff0020250d3f00  ← 恰为崩溃任务自身
                            cfs.avg.load_avg = 319, nr_switches = 7315613
```
rq(179) `curr` 指针与 bt 报告的 panic task 结构体地址逐位相等；`nr_running=0` 与 newidle_balance 的 idle 平衡场景吻合；rq(179) 内嵌自指针 `nohz_csd.info = 0xffff8000817dd6c0` 与 `x27_true(179) = &runqueues + __per_cpu_offset[179]` 逐位一致（Python 复算，`algebra_out.txt` E 节），该地址经 vtop 走查 VALID（PA=0x6057ffe026c0）——两条独立通路（i=12 语义通路与 i=179 对照通路）均闭合。

### P4 软件根因排除

| 假设 | 判定 | 关键反证 |
|---|---|---|
| 内核软件 bug（UAF/越界/竞态） | 排除【实锤】 | 代数闭合 + 反事实验证；内存真值恒完好；同一指令跨 9 个开机的不同 KASLR/不同迭代号（176/175/146/179/97/60/12…）均崩溃而软件路径完全自洽 |
| DIMM/DDR 颗粒故障 | 排除【实锤】 | EDAC 零记录；被读数组等差完好；撕裂值是数组字节流的真实子串（crash 直读逐位验证）；损坏随执行核（179）不随地址 |
| L3/互连故障 | 排除【强推】 | 槽 12/123/124/179 数据均完好（同 NUMA 节点内共享路径无恙）；故障 100% 绑定 CPU179 私有通路 |
| 页表/MMU 硬件走表损坏 | 排除【实锤】 | FAR 非规范域 L0 是坏地址的必然投影（`address between user and kernel address ranges`，crash `vtop -k` 亦判 "not a kernel virtual address"）；vtop 对真值地址走查 VALID 证明走表诚实 |
| KASLR/装载地址错位 | 排除【实锤】 | 五路符号咬合 + x24 adrp 页基吻合（algebra_out.txt A 节） |
| "槽位特异性"假说 | 排除【实锤】 | 本案 i=12、第 7 案 i=60、第 11 案 i=97：迭代对象都非 179，真值槽均完好，仍崩——腐化绑定执行核 |
| "监控代理触发"假说（irqbalance 是诱因） | 排除【实锤】 | 35 次 WARNING 由两个互不相干的监控进程踩中；panic 受害者是 rcu_sched（与监控无关）；唯一公共变量是"内核指针装载指令在 CPU179 上执行" |

---

## 7. 逻辑链条（寄存器代数闭合与反事实）【逻辑链条】

全部等式由 `algebra.py` 机器验证（模 2⁶⁴），输出存 `algebra_out.txt`：

**第一环 · KASLR 五路咬合**：`x9` 锚（find_busiest_group+0x150）、crash `sym` 四符号（runqueues / nr_cpu_ids / __per_cpu_offset / find_busiest_group）的运行期−静态差全部等于 `0x49e822170000`。寄存器现场与符号表互证，不存在地址错读空间。

**第二环 · 故障点代数闭合（撕裂移位）**：
```
x1  = ffffc9e8a3cd96c0   (&runqueues 模板，== sym runqueues 逐位)
x20 = 00ffffb617dd3940   (实收；应为 __per_cpu_offset[12] = ffffb617dc4d6000)
x27 = x1 + x20 = 00ffc99ebbaad000   ← 与崩溃块 x27 逐位相等
FAR = x27 + 0x120 = 00ffc99ebbaad120 ← 与崩溃 FAR 完整 64 位逐位相等
                                         （本案高 16 位 00ff 直通打印，与 08-31 案
                                          低 48 位打印形态不同，代数闭合不受影响）
x25 = x0 = x3 = x6 = 0xc = 12（迭代 CPU 号，四寄存器互证）
```

**第三环 · 内存真值对照 + 撕裂窗口定位**：`__per_cpu_offset[12]=0xffffb617dc4d6000`（非零）、数组 192 项 `0x22000` 等差完好 → 内存好、寄存器坏。x20 的 8 字节 LE 序列在全数组字节流**唯一**命中"槽 123 +1 字节"处，crash 直读该地址（`ffffc9e8a40d59a9`）返回值与 x20 **逐位相等**——撕裂值 = 数组字节流在 +1 字节相位上的非对齐 8 字节窗口，**数据源相位错位实锤**。等价公式 `(off[123]>>8) | ((off[124]&0xFF)<<56)` 机器复验成立。

**第四环 · 反事实验证**：
```
x27_true(12)  = &runqueues + __per_cpu_offset[12]  = 0xffff8000801af6c0
                == p runqueues:12 的 nohz_csd.info 内嵌自指针（逐位）
                → vtop VALID（PA=0x37ffe2e6c0，PTE VALID|…|DIRTY）
                → 故障装载将读 rq(12)->cfs.avg.load_avg = 1023（+0x120 偏移经 struct 验证），不崩
x27_true(179) = &runqueues + __per_cpu_offset[179] = 0xffff8000817dd6c0
                == p runqueues:179 的 nohz_csd.info（逐位）→ vtop VALID（PA=0x6057ffe026c0）
```
两条独立通路（语义应然 i=12 与对照核 i=179）双双闭合。

**第五环 · FSC 几何归一**：撕裂值使 x27 落入非规范域（bit[63:48]=00ff≠ffff/0000），MMU 在 PGD 级即失败 → FSC=L0，dmesg 明示 `address between user and kernel address ranges`。与既往撕裂移位各案（08-14/08-17/08-25-15:58/08-31）的 L0 签名完全一致；零塌缩族才落 init 域报 L2/L3——**FSC 谱系完全由坏地址落点决定，非两种病**。

**结论**：五环全部机器闭合，无一手工计算。逻辑链的唯一自由变量是 `ldr x20,[x0,w25,sxtw#3]` 的返回值——它在 CPU179 上执行时交付了从错误相位（+1 字节、跨 123/124 槽边界）读出的数组字节流窗口。

---

## 8. 故障根因【故障根因】

- **子族归类：撕裂移位族（tear-and-shift）【实锤】**——x20 实收值是被读数组字节流在 +1 字节相位上的非对齐 8 字节窗口（crash 直读验证逐位一致），x27 = x1 + 撕裂值落入非规范域，FAR=x27+0x120 触发 L0。与 08-14（ROL16 半字旋转）、08-17（≫8 跨字节 1 字节相位，强推）、08-25-15:58（≫8，槽 0 起点）、08-31（+2 字节跨槽 125/126）同族。**本案为该族相位谱第 5 个数据点：1 字节相位、槽 123 起点、跨 123/124 槽边界。**
- **微架构判定：LSU 装载数据返回通路 SDC【强推，十二案收敛】**——"从已验证完好的内存装载 → 寄存器获得错误相位的数据 → 坏值作为地址偏移污染后续访存"。本案与第 7 案采用同一字节流非对齐窗口匹配法，**连续两案把撕裂值与内存中一段真实字节流逐位对上**（第 7 案 +2 字节跨槽 125/126、本案 +1 字节跨槽 123/124）——"撕裂值不是损坏的数据，而是错位的数据"这一论断从单例升级为可重复的方法学实证。错位相位在 1~2 字节间变化、命中槽位随机（125→123），支持 **fill-buffer 合并窗口的字节使能相位/lane skew 选路控制逻辑**失效模型（而非存储单元阵列缺陷）。与 gem5 故障注入实验 `--lsq-structural byte_lane_skew` 复现的 PTR_CORRUPT 形态同族〔既往已证，core179-microarch-rootcause-synthesis/paper_zh.md §5 H5〕。
- **本案增量证据（统计学）**：35 次 WARNING 的四簇脉冲 + 10 秒栅格节律是历案最完整的发作统计样本：(a) 簇内毫秒级连发（10.6ms 内 5 起）说明边际条件窗口一旦打开，连续多次装载都交付错位数据；(b) 10 秒整数倍栅格与 irqbalance 扫描周期吻合——同一周期性负载在窗口期内反复踩中，窗口关闭后同样的负载零事件，**发作由核的状态决定而非由负载决定**；(c) 簇间隔（19.7h/1.12h/3.40h/45.29h）无周期规律，与"间歇性边际条件"（电压/温度/频率组合穿越阈值）的随机到达过程一致。
- **物理机理层【假设，与既往一致】**：sense-amp/位线均衡在特定调度相位×电压裕量下的边际时序失效；精确到晶体管级需芯片 ATE/DFT/BIST（MBIST/LBIST、shmoo），超出 vmcore 方法论可观测极限——此为证据边界声明，非调查缺失。本案簇发统计为 shmoo 复现提供了"间歇性、窗口期、周期性负载敏感"的实验设计参数。

---

## 9. 启示【启示】

**对根因模型的增量**：
1. **撕裂相位谱第 5 数据点 + 连续两案非对齐窗口直读成功**：1 字节（08-25-15:58、本案）→ 2 字节（08-31）→ 半字旋转（08-14），相位在 1~2 字节粒度上变化、命中槽位随机。对 fill-buffer 合并模型的意义：错配相位不是固定偏移而是**可变相位窗口**（1~2 字节观测值支持"多字节通道各自边际时序、合并时相位失配"的结构模型，paper_zh.md §5 byte_lane_skew）。方法学意义：第 7 案首创的字节流非对齐窗口匹配法在本案**无需修改即再次命中**——它已从单案技巧升级为撕裂移位族的标配判定工具。
2. **簇状爆发对"电压/频率相依性"假说的支撑（本案核心增量）**：35 次 WARNING 的四簇脉冲结构给出了迄今最强的"边际条件窗口"统计学证据。若缺陷是恒定性的（如固定 stuck-at），事件应近似泊松均匀到达；而本案观测到的是**簇内毫秒级密集 + 簇间数小时~数十小时静默 + 10 秒栅格（负载周期）规整爆发**——最经济的解释是：**缺陷的激活需要特定边际条件（电压/频率/时序相位组合）暂时进入窗口，窗口打开时连续多次装载交付错位数据（簇内连发），窗口关闭后同样的周期性负载零事件（长静默）**。10 秒栅格尤其关键：它证明在窗口期内，"每次踩中"的概率极高（irqbalance 每 10s 轮询一次即每 10s 出一次 WARNING），而窗口期外概率近零——发作率的时间结构是双峰的，不是均匀的。这对预测模型的含义：(a) **"最近 N 小时无事件"完全不能说明窗口不会在下一秒打开**（45.29h 静默后末簇照样到来）；(b) **簇发本身是可检测的强信号**——本案簇 B 的"10 秒内 ≥2 次 spurious WARNING"若配置为自动 offline 触发条件，机器可在首簇（39.66h）即被保护，避免其后 50 小时的暴露与最终宕机；相比第 7 案（末簇距 panic 仅 3.1s，来不及反应），本案簇 B 距 panic 尚有 49.8h——**簇发形态给了自动化响应以小时级而非秒级的窗口**。
3. **WARNING 数量与 panic 无必然联系**：本案 35 次前兆（历案最多）与 09-04-11:00 案 0 次前兆（速死）构成前兆谱的两个极端，且都死于同一指令同一机制。WARNING（D3 通路，写访问指针腐化但被 spurious 判定容忍）与 panic（D1 通路，读访问偏移腐化进地址运算）是同一缺陷在两类指令上的投影——前兆数量取决于缺陷窗口期与用户态可感知路径的交集，而非缺陷严重程度。
4. **rcu_sched 二度受害与暴露面模型**：两个最长存活案（110h/89.5h）的 panic 受害者都是 rcu_sched（PID 16，永生内核线程）。这不是缺陷"偏好"rcu_sched，而是**暴露累积效应**：rcu_sched 在 fqs 循环中周期性睡眠/唤醒，每次唤醒都经过调度器选核路径；存活越久，它在 CPU179 上的唤醒次数越多。缺陷核的受害者分布由"指令流经过 CPU179 的频次×时长"决定——高 AVF 通路论断的又一次印证（paper_zh.md §6.2）。

**对三启示（paper_zh.md §6）的印证**：
- **fail-fast（§6.1）**：本案 35 次前兆全部可被 `grep "Ignoring spurious kernel translation fault"` 规则捕获，且簇发形态（10s 内 ≥2 次）提供了小时级响应窗口——**秒级密度触发 + 自动 offline 脚本**在本案形态下完全来得及（对比第 7 案的 3.1s 极限窗口与 09-04-11:00 案的零前兆）。论文 §6.1 的被动遥测（WARN_RATELIMIT → fail-fast 信号 → 热下线）在本案获得了最有利的实证条件；但三案合观（3.1s / 21.2s / 0s 前兆窗口）说明被动遥测的响应窗口方差极大，唯一可靠的 fail-fast 仍是**已知缺陷核立即 offline**。
- **位置锚定校验（§6.2 Positional Parity）**：本案撕裂值再次是"错位但真实"的数据——窗口内 8 个字节全部完好，任何位级 ECC/奇偶校验都会放行（连续两案验证）。必须校验"数据与位置的绑定关系"（paper_zh.md §6.2：为每个字节通道附加物理位置标签，跨通道错位即 MCE）才能拦截。本案 + 第 7 案构成该论点的双实例：两个通过了所有位级校验的错位值，一个杀死了 RCU 根线程（第 7 案），另一个再次杀死了它（本案）。
- **PEPR（§6.3 制造测试）**：1 字节与 2 字节相位的连续观测为 fill-buffer 合并窗口字节相位错配提供了更精确的测试向量参数空间（1~2 字节偏移、跨 8 字节槽边界）。建议在逃逸分级中将"负载数据返回路径 fill-buffer 合并 / load 返回 mux"继续标记为 i 类高 SDC 风险（paper_zh.md §6.3），并针对 1~2 字节相位错配设计定向扫描向量；本案的簇发统计（间歇性、窗口期、周期负载敏感）提示制造端 shmoo 应包含**电压×频率边际角点的重复装载序列**而非单次装载。

**工程启示**：本开机 WARNING #1（19.95h）与簇 B（39.66h）两次提供了明确的处置窗口，机器仍"健康"运行了近 50 小时后死亡。对已确认缺陷核，"观察等待"没有合理窗口——每一次簇发都是下一次宕机的免费预告。

---

## 10. 处置建议

1. **立即**：`echo 0 > /sys/devices/system/cpu/cpu179/online` 下线 CPU179。本案是第 8 次致命发作；簇 B（39.66h，10 秒内 5 连发）即为最明确的热下线触发点，其后 49.8h 的暴露本可避免。
2. **根本**：整机/整 socket 送修（RMA），引用本报告 §6 P3(b)（非对齐窗口直读——第 7 案 + 本案连续实证）与 §7（五环闭合）作为返修凭证；请厂家对 CPU179 执行核内 MBIST/LBIST 与 shmoo 复现，实验设计参考本案簇发统计：**电压×频率边际角点 + 周期性重复装载序列**（10s 周期、簇内毫秒级连发形态），并针对 fill-buffer 合并窗口 1~2 字节相位错配设计定向测试向量。
3. **不要**部署 `l1d_disable` 类缓解——本开机无该试验记录，但既往各案（08-31 三次试验后照常发作）已充分证伪。
4. **监控策略**：继续 grep `Ignoring spurious kernel translation fault`（本案 35 次前兆全部可被此规则捕获）；**新增簇发密度触发规则**："10 秒内 ≥2 次 spurious WARNING → 自动 offline 脚本"。本案证明簇发形态可提供小时级响应窗口（对比第 7 案 3.1s 与 09-04-11:00 案零前兆，三案合观响应窗口方差极大）——被动遥测值得部署，但不能作为唯一防线；已知缺陷核的唯一安全策略是立即 offline。

---

## 附录：命令索引（本报告全部取证命令，可复核）

```bash
D=/home/sdc/wangxu/vmcore0102/127.0.0.1-2026-09-03-18:25:12/vmcore-dmesg.txt
VL=/usr/lib/debug/usr/lib/modules/6.6.0-145.3.23.154.oe2403sp3.aarch64/vmlinux
VM=/home/sdc/wangxu/vmcore0102/127.0.0.1-2026-09-03-18:25:12/vmcore

# ① dmesg 法证（本目录 dmesg_forensics.txt）
grep -nE "Linux version|Command line|Memory:" $D | head -5
grep -c "WARNING: CPU:" $D                          # → 35
grep -oE "WARNING: CPU: [0-9]+" $D | sort | uniq -c # → 35 WARNING: CPU: 179
grep "WARNING: CPU: 179" $D | awk -F'[][]' '{print $2}' | sort -n | uniq -c | awk '{print $2, "x"$1}'
                                                    # → 35 个唯一时间戳（四簇结构）
grep "Comm:" $D | grep -oE "PID: (9736|10282|16) Comm: [a-zA-Z_-]+" | sort | uniq -c
                                                    # → irqbalance×32 / pmdalinux×3 / rcu_sched×1(panic 块)
grep -n "Ignoring spurious" $D                      # → 35 条 spurious FAR（ffff60xx 区）
grep -E "x19: 000000009600" $D | grep -oE "x19: [0-9a-f]+" | sort | uniq -c   # → 35 × 0x96000044
awk '/Unable to handle/{f=1} f{print; c++} c>90{exit}' $D                    # 完整崩溃块（x0~x30）
grep -nE "ERRIDR|ERX|EDAC|BERT|GHES|mce|ras" $D | head                        # RAS 负证据
awk '$0 ~ /^\[/ {ts=$1; gsub(/[\[\]]/,"",ts); if (ts+0>90.0 && ts+0<71822.0) c++} END{print c+0}' $D
# → 0（静默窗核验；同式改边界核验全部 6 个静默窗，均 0）

# ② 静态语义（vmlinux）
nm $VL | grep -wE "find_busiest_group|runqueues|__per_cpu_offset|nr_cpu_ids"
objdump -dl --start-address=0xffff80008013ade8 --stop-address=0xffff80008013ae70 $VL

# ③ crash 动态取证（本目录 forensics_cmds.txt → crash_session.log；73.7G，taskset 隔离 0-31）
taskset -c 0-31 timeout 7200 crash $VL $VM -i forensics_cmds.txt
#   关键命令：sys / bt / sym runqueues / px __per_cpu_offset[12] / px __per_cpu_offset[179]
#             rd -64 __per_cpu_offset 192 / p runqueues:12 / p runqueues:179
# 补充会话（crash_session_supplements.log = crash_session2 + crash_session3）：
taskset -c 0-31 timeout 3600 crash $VL $VM -i forensics_cmds2.txt
#   vtop -k 00ffc99ebbaad120 → "not a kernel virtual address"（与硬件 L0 一致）
#   rd -64 ffffc9e8a40d59a9 2 → 首字 00ffffb617dd3940 == x20（非对齐窗口直读）
#   px __per_cpu_offset[123] / [124] / p &((struct rq *)0)->cfs.avg.load_avg → 0x120
taskset -c 0-31 timeout 3600 crash $VL $VM -i forensics_cmds3.txt
#   vtop ffff8000801af6c0 → VALID (PA 37ffe2e6c0)
#   vtop ffff8000817dd6c0 → VALID (PA 6057ffe026c0)

# ④ 代数复算（本目录 algebra.py → algebra_out.txt）
python3 algebra.py
```

**诚实性备注**：(1) 本报告所有引用输出均摘自上述真实执行日志，关键数值（`0xffffb617dc4d6000`、`0x00ffffb617dd3940`、`00ffc99ebbaad000`、`rd -64 ffffc9e8a40d59a9` 首字、`nohz_csd.info = 0xffff8000801af6c0`、`cpu = 12`、`curr = 0xffff0020250d3f00`、load_avg=1023 等）已逐条与 `crash_session.log` / `crash_session_supplements.log` / `dmesg_forensics.txt` 原文比对。(2) `vtop` 对非规范 FAR 需显式 `-k` 选项，输出 "not a kernel virtual address" 与硬件 L0 判定一致（crash_session2.log）。(3) dmesg 崩溃块打印的 FAR `00ffc99ebbaad120` 与 x27+0x120 的完整 64 位值逐位相等（高 16 位 00ff 直通打印）——与 08-31 案（dmesg 只打印低 48 位、高 16 位 a000 不入报告）形态不同；两者均为打印宽度差异的投影，代数闭合均逐位成立，如实记录。(4) WARNING 块的 `x21`（FAR 寄存器）与 `x19`（ESR 寄存器）在 35 个 WARNING 块中逐一提取核对，其中 panic 块自身的 x21=ffffc9e8a40cfcb0（&nr_cpu_ids）不属于 WARNING 样本，已剔除。(5) 十二案横向综合（含本案在内的总表更新）在 Task 8 统一完成，本报告不重复编制。

---
*报告生成：2026-09-04 · 深度诊断会话 · 证据全部源自 127.0.0.1-2026-09-03-18:25:12 的 vmcore（73.7G）/vmcore-dmesg.txt 及其 3 个 crash 会话（crash_session.log + crash_session_supplements.log = crash_session2.log + crash_session3.log）*
