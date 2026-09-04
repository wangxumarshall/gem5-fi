# CPU179 缺陷核第 7 次致命转储深度诊断报告
## ——撕裂移位族新相位（+2 字节跨槽非对齐窗口）实锤 + 110h 最长存活

| 项 | 值 |
|---|---|
| 目标转储 | `/home/sdc/wangxu/vmcore0102/127.0.0.1-2026-08-31-00:47:32/`（14.7 GB，PARTIAL DUMP，vmcore-dmesg.txt 3243 行） |
| 主机 | Yangtze Computing R240K V2 / BC82AMQA，BIOS 7.48 06/15/2026 |
| CPU | Kunpeng-920 (HIP08/TaiShan-v110) ×192，8 NUMA 节点 |
| 内核 | 6.6.0-145.3.23.154.oe2403sp3.aarch64 #1 SMP（debuginfo 精确匹配；Tainted G W OE，[last unloaded: l1d_disable]） |
| 崩溃 | 2026-08-31 00:46:42 CST（dmesg 时间戳 396122.719381s），uptime **110.03h（4 天 14 小时，十二案最长）**，CPU **179**，PID 16 `rcu_sched` |
| 结论 | **第 7 次独立坐实 CPU179 缺陷核（LSU 装载数据返回通路 SDC），并首次以"字节流非对齐窗口"实锤撕裂移位族的物理来源：x20 实收值 `0xa000ffffbe56fb25` 与被读数组中"槽 125 起点 +2 字节"处的 8 字节非对齐窗口内容逐位一致（crash 直读该地址验证），而指令语义应取槽 60（真值 `0xffffbe56fa9b6000`，全数组 192 项 0x22000 等差完好）——内存完好、寄存器收坏，且坏值不是任何槽的算术移位，而是数据源相位错位 2 字节、跨槽边界的字节流窗口。撕裂相位谱从既往的 1 字节（≫8）扩展到 2 字节，且首次确认窗口可跨槽。** |

---

## 1. 执行摘要

1. 本次 panic 是同一缺陷的**第 7 次发作**，发生在**十二案最长的 110.03 小时存活**之后（刷新 08-17 案 66.5h 纪录）。崩溃进程为 `rcu_sched`（PID 16）——内核 RCU 状态机的根线程，它死亡意味着 RCU 宽限期推进机制当场停摆，Oops 不可恢复直接进入 kdump 整机重启。
2. 故障指令与既往各案**逐字相同**：`find_busiest_group+0x140`（`kernel/sched/fair.c` `update_sg_lb_stats()` per-CPU 遍历体），`Code:` 字段五指令字 `f9400782 f879d814 2a1903e0 8b14003b (f9409377)` 完全一致。寄存器代数闭合：`x27 = x1 + x20 = ffffc1a985e596c0 + a000ffffbe56fb25 = a000c1a9443c91e5`（逐位），`FAR = x27 + 0x120` 低 48 位逐位吻合（48-bit VA 下 dmesg 只打印低 48 位）【实锤】。
3. **本案决定性新证据——撕裂窗口的物理定位**【实锤】：把 192 槽 `__per_cpu_offset` 数组按内存小端拼成字节流，x20 的 8 字节序列在**全数组唯一命中"槽 125 起点 +2 字节"**（数组基址 +1002 字节处）；crash 直读 `rd -64 ffffc1a9862559ba`（即该地址）返回首字 **`a000ffffbe56fb25`，与 x20 逐位相等**。即：CPU179 上这条装载指令交付的不是槽 60 的数据，也不是任何槽的旋转/移位，而是**从错误相位（+2 字节）读出的跨槽（125/126 边界）非对齐字节流窗口**。被读内存本身完好（全数组等差数列无一项损坏）——**数据源没错、相位错了**。
4. 反事实验证三重闭合【实锤】：`x27_true(60) = &runqueues + __per_cpu_offset[60] = 0xffff80008080f6c0`，与 `rq(60)` 实例内嵌自指针 `nohz_csd.info` 逐位一致；该地址 crash `vtop` 走查 **VALID**（PA=0x2037ffe306c0，PTE VALID|DIRTY）；实例健全（`cpu=60`、`nr_running=1`、`cfs.avg.load_avg=1024`）。若装载交付真值，指令平静读到 1024，系统继续运行。**异常的唯一必要条件是装载结果被撕裂。**
5. 本次开机 13 次 WARNING（spurious 翻译故障）**100% 位于 CPU179**，进程仅 pmdalinux（8 次）/irqbalance（5 次）两个系统监控代理；末次 WARNING 距 panic 仅 **3.098 秒**（396119.621 → 396122.719），且最后三连发在 0.027 秒内密集出现——发作末期加速的特征与"边际条件窗口"假说一致。
6. 处置建议不变且紧迫：**offline CPU179 + 整片送修（RMA）**。本案期间三次 l1d_disable 试验（44747s/82326s/83107s，各持续 2~900 秒后重新使能并卸载）再次证明无效——卸载后 198031 秒（55h）内故障照常发作至致命。

---

## 2. 证据规则与方法

- **只依据 vmcore / vmcore-dmesg.txt 取证**；引用既往会话结论处标注〔既往已证〕。
- 所有 64 位地址加法一律 Python3 模 2⁶⁴ 计算（本目录 `algebra.py`，输出 `algebra_out.txt`），并以 crash 内建 per-cpu 解析器与结构体内嵌自指针独立对照，杜绝手算误差。
- 工具：crash 8.0.4-17.oe2403sp4 + 精确版本 debuginfo vmlinux（`/usr/lib/debug/usr/lib/modules/6.6.0-145.3.23.154.oe2403sp3.aarch64/vmlinux`）；objdump -dl（DWARF 行号）；grep/awk（dmesg 法证）。已知怪癖：crash `-i` 批首行被吞（首行放无害命令 `sys`）、`log` 命令在此类 PARTIAL DUMP 上挂起（禁用，dmesg 一律取自 vmcore-dmesg.txt）、加载期 ~384 条 IRQ/SDEI stack seek error 属转储未含该区的正常现象。
- 报告区分三层置信：**【实锤】**= dump 内可复核证据；**【强推】**= 多源证据收敛的推断；**【假设】**= 无法软件验证的部分，明示验证途径。

---

## 3. 本次开机时间线【时间线】

| 时刻（dmesg 时间戳） | 事件 | 证据 |
|---|---|---|
| 0.000000s（2026-08-26 10:44:40 前后） | `Booting Linux on physical CPU 0x0000080000 [0x481fd010]`，内核 6.6.0-145.3.23.154.oe2403sp3.aarch64 #1 | dmesg 行 1 |
| 0~1.5s | 硬件枚举：BERT（HISI HIP08）在位、GHES firmware-first 使能、ghes_edac 注册、192 核启动 | dmesg 行 12/1307/1857/2176 |
| 1.102469s | `pstore: Using crash dump compression: deflate`（kdump 就绪） | dmesg 行 1945 |
| 38.8s | `hns3 enp189s0f0: link up`（业务网卡上线） | dmesg 行 2586 |
| 80.6s | `block dm-2: the capability attribute has been deprecated`——**最后一条正常常规消息** | dmesg 行 2587 |
| 80.7s~10520.6s | **静默 10440 秒（2.9h）：0 条内核消息**（awk 全量核验为 0） | 全量核验 |
| **10520.595s（2.92h）** | **首症**：WARNING #1，`Ignoring spurious kernel translation fault at ffff60400826514e`，CPU179，PID 14074 pmdalinux | dmesg 行 2589-2590 |
| 11620.5s / 11775.0s / 12975.1s / 13390.5s | WARNING #2~#5（pmdalinux ×2、irqbalance ×2），间隔 155~1200s——**首簇：2.9h~3.7h 内 5 连发** | dmesg 行 2635/2680/2725/2770 |
| 18148~80946s | silifuzz_orches 5 次运行记录（memfd 提示，间接证明机上有主动测试负载在跑） | dmesg |
| 44747.2s | **l1d_disable 试验 #1**：CPU179 L1D 禁用，2.1s 后重新使能卸载 | dmesg 行 2822-2823 |
| 82326.1s / 83108.0s | **l1d_disable 试验 #2/#3**：分别禁用 300s/899s 后重新使能卸载 | dmesg 行 2828-2833 |
| 13390.5s~282138.5s | **静默 268748 秒（74.7h，本案最长静默窗）**——期间穿插 l1d 试验与 silifuzz 运行，但零硬件异常事件 | 全量核验 |
| **282138.528s（78.4h）** | WARNING #6（pmdalinux，far=ffff60415e428327）——l1d_disable 卸载 55h 后首次复发 | dmesg 行 2837 |
| 345159.0s / 362639.0s | WARNING #7/#8（irqbalance ×2，间隔 17.5h/4.9h） | dmesg 行 2882/2927 |
| 363149.1s / 363388.5s | WARNING #9/#10（pmdalinux、irqbalance，间隔 510s/239s）——**次簇形成** | dmesg 行 2972/3017 |
| 363389s~396119s | 静默 32731 秒（9.1h） | 全量核验 |
| **396119.594s** | WARNING #11（pmdalinux，far=ffff604349d163ab） | dmesg 行 3062 |
| **396119.598s（+0.0041s）** | WARNING #12（pmdalinux，far=ffff604349d16466） | dmesg 行 3107 |
| **396119.621s（+0.0231s）** | WARNING #13（pmdalinux，far=ffff604349d1649d）——**末簇三连发 0.027s** | dmesg 行 3152 |
| **396122.719s（+3.098s）** | **panic**：`Unable to handle kernel paging request at virtual address 0000c1a9443c9305`，CPU179 上 rcu_sched（PID 16）经 rcu_gp_fqs_loop→schedule_timeout→schedule→newidle_balance 触发负载均衡，`find_busiest_group+0x140` 崩溃 | dmesg 行 3195 |
| 396123.110s | `Starting crashdump kernel...` → kdump 完成，14.7G vmcore 落盘 | dmesg 行 3242 |

**发作节律**【实锤，对预测模型的直接输入】：13 次 WARNING 呈**三簇脉冲**——首簇 2.9~3.7h（5 次，分钟~小时级间隔）、中段孤发（78.4h）、末簇 110.0h（3 次密集三连发后 3.1s 即 panic）。最长静默窗 74.7h（W5→W6）。**WARNING 间隔无单调趋势**（1099s→155s→1200s→415s→74.7h→17.5h→4.9h→510s→239s→9.1h→0.004s→0.023s），但**末次发作呈明显加速**：panic 前 3.1 秒内三连发，簇内间隔毫秒级。

---

## 4. 故障现象【故障现象】

Oops 原文（vmcore-dmesg.txt 行 3195 起，摘录）：

```
[396122.719381] Unable to handle kernel paging request at virtual address 0000c1a9443c9305
[396122.731717]   ESR = 0x0000000096000004
[396122.736255]   EC = 0x25: DABT (current EL), IL = 32 bits
[396122.750128]   FSC = 0x04: level 0 translation fault
[396122.777675] user pgtable: 4k pages, 48-bit VAs, pgdp=0000204003e1c000
[396122.784907] [0000c1a9443c9305] pgd=0000000000000000, p4d=0000000000000000
[396122.792491] Internal error: Oops: 0000000096000004 [#1] SMP
[396122.905717] CPU: 179 PID: 16 Comm: rcu_sched Kdump: loaded Tainted: G        W  OE
[396122.934368] pc : find_busiest_group+0x140/0xb60
[396122.939698] lr : find_busiest_group+0x11c/0xb60
[396122.945017] sp : ffff8000821ab830
[396122.949119] x29: ffff8000821ab9b0 x28: ffff8000821ab860 x27: a000c1a9443c91e5
[396122.957048] x26: ffff604003e270c0 x25: 000000000000003c x24: ffffc1a986255000
[396122.964975] x23: 0000000000000400 x22: ffff604003e27120 x21: ffffc1a98624fcb0
[396122.972903] x20: a000ffffbe56fb25 x19: ffff8000821aba40 x18: 0000000000000000
[396123.004620] x8 : ffff8000821ab8b8 x7 : 0000000000000000 x6 : 000000000000003c
[396123.012549] x5 : f000000000000000 x4 : 0000000000000000 x3 : 000000000000003c
[396123.020475] x2 : 0000000000009063 x1 : ffffc1a985e596c0 x0 : 000000000000003c
[396123.028404] Call trace:
[396123.032417]  find_busiest_group+0x140/0xb60
[396123.037974]  load_balance+0x108/0x6c0
[396123.042968]  newidle_balance+0x198/0x510
[396123.048214]  pick_next_task_fair+0x110/0x718
[396123.053801]  pick_next_task+0x60/0x398
[396123.058856]  __schedule+0x1b4/0x8a0
[396123.063637]  schedule+0x58/0x130
[396123.068154]  schedule_timeout+0x1b0/0x2f0
[396123.073447]  rcu_gp_fqs_loop+0x11c/0x358
[396123.078653]  rcu_gp_kthread+0x124/0x178
[396123.083770]  kthread+0xec/0x100
[396123.088196]  ret_from_fork+0x10/0x20
[396123.093055] Code: f9400782 f879d814 2a1903e0 8b14003b (f9409377)
```

要点：ESR=0x96000004（DABT、WnR=0 读访问、FSC=0x04 **L0**）；`Code:` 与既往各案逐字相同；`x20 = a000ffffbe56fb25`（撕裂值，非零非模板）；`x25 = 0x3c = 60`（迭代 CPU 号，四寄存器互证 x0/x3/x6 同为 0x3c）；崩溃时 1 分钟负载 176.87（crash `sys`）——110h 长存活的满负荷机器。撕裂移位族签名：FAR 高位 `0000`（非规范域）→ L0，pgd=0 在用户页表第一级即断。

---

## 5. 业务现象【业务现象】

- **崩溃进程是谁**：`rcu_sched`（PID 16），**内核 RCU 状态机的根线程**（rcu_gp_kthread）。它不是用户态业务进程，而是内核"垃圾回收中枢"：每个 RCU 宽限期（grace period）由它驱动，`rcu_gp_fqs_loop` 是其强迫静止状态（quiescent state）检测循环。崩溃时它正在 `schedule_timeout` 睡眠等待下一个 fqs 轮询点被唤醒，内核在为新任务选核时进入 `newidle_balance`（idle 平衡）路径触发负载均衡，均衡器遍历调度组内 CPU 时撞上缺陷核装载。
- **对上层服务的表现**：rcu_sched 死亡的直接工程含义是**RCU 宽限期永久停滞风险**——所有等待宽限期的回调（内存释放、模块卸载清理等）将永不执行，内存泄漏式堆积最终拖垮全机。但本案中这一后果**没有机会兑现**：Oops 本身不可恢复（内核在 `die_kernel_fault` 路径判 fatal），直接进入 kdump——**整机所有业务（2205 个任务，load 176.87 的满负荷机器）瞬间停摆并重启**。对运维而言，这是一台连续运行 110 小时、承载重负载（历史峰值 183.57）的生产机的**整机宕机**：所有 2205 个任务（含传输、扫描、系统服务）的非持久状态全部丢失。
- **110h 长存活的业务暴露面**：本案刷新十二案最长存活纪录（110.03h，约为最短案 0.4h 的 273 倍）。从业务连续性视角，这意味着：(a) 缺陷核的发作率极低但**不随时间衰减**——74.7h 静默后照样复发；(b) 长存活不等于安全，**存活时长本身不构成任何"已渡过危险期"的证据**；(c) 本机上有 silifuzz_orches 主动测试负载在跑（18148s 起有 5 次记录），说明机器同时承担测试业务——测试负载并未"测出"这个缺陷（与论文 §6.1 "主动 SBST 语料未覆盖此通路"的判定一致）。

---

## 6. 诊断定位过程【诊断定位过程】

### P1 勘察（dmesg 全量法证）

命令与输出见本目录 `dmesg_forensics.txt`。关键结果：
- `grep -c "WARNING: CPU:"` → **13**；per-CPU 分布 `13 WARNING: CPU: 179`——**全部 13 次位于 CPU179，其余 191 核零事件**；
- WARNING 进程分布：pmdalinux（PID 14074）×8、irqbalance（PID 9678）×5——两个系统监控代理，与既往各案"监控代理最常踩中"的规律一致（它们频繁读 /proc、/sys 触发内核指针解引用）；
- 全部 13 次 spurious FAR 均落于 `ffff60xx/ffff20xx`（vmalloc/percpu-chunk 区统计结构），ESR 均 `0x96000044`（WnR=1 写访问 + FSC=L0，x19 残留值可证）；
- RAS 负证据：BERT 在位内容空、GHES firmware-first 使能、ghes_edac 注册，全程零 CE/UE；
- l1d_disable 三次试验（44747s/82326s/83108s）后卸载，末次试验后 198031s（55h）WARNING #6 复发、312014s（86.7h）后致命 panic——**L1D 禁用期间与卸载后故障行为无任何改变**；
- 崩溃块寄存器全量提取（x0~x30 + pstate + Code），见 §4。

### P2 静态反汇编与符号语义重建（vmlinux + DWARF）

`objdump -dl` 于 `find_busiest_group` 静态基址 `0xffff80008013ad08`（nm 输出），故障窗口（与既往各案同窗口，本内核再验证一次）：

```asm
; kernel/sched/fair.c — update_sg_lb_stats(): for_each_cpu_and(i, group_span, env->cpus)
ffff…ae10  bl   _find_next_and_bit        ; x0 = 下一个置位 CPU 编号 i
ffff…ae24  mov  x25, x0                   ; x25 = i（本案 = 0x3c = 60）
ffff…ae34  ldp  x0, x1, [sp, #8]          ; x0 = &__per_cpu_offset[0]; x1 = &runqueues（模板）
ffff…ae3c  ldr  x20, [x0, w25, sxtw #3]   ; x20 = __per_cpu_offset[i]   ← 数据来源（实收撕裂值）
ffff…ae44  add  x27, x1, x20              ; x27 = &per_cpu(runqueues,i) (mod 2^64)
ffff…ae48  ldr  x23, [x27, #288]          ; rq->cfs.avg.load_avg        ← 致命点(+0x140)
```

故障指令字 `f9409377` 解码：`ldr x23, [x27, #288]`（imm12=36, 36×8=0x120）——`&((struct rq *)0)->cfs.avg.load_avg` 偏移 0x120 经 crash 实测验证（`p &((struct rq *)0)->cfs.avg.load_avg` → `0x120`，crash_session5.log）。KASLR 锚定【实锤】：崩溃块 `x9 = ffffc1a98442ae58 = find_busiest_group+0x150`，反推滑移 `0x41a9042f0000`；crash `sym` 四符号（find_busiest_group/runqueues/nr_cpu_ids/__per_cpu_offset）运行期地址与静态地址之差**五路全部等于同一滑移值**（`algebra_out.txt` A 节）。`x21 = ffffc1a98624fcb0 = &nr_cpu_ids`（值 0xc0=192）、`x24 = ffffc1a986255000 = &__per_cpu_offset − 0x5d0`（adrp 页基），与 `str x0,[sp,#8]` 构造序列吻合——寄存器现场与指令语义完全自洽。

### P3 crash 动态取证（14.7G 完整转储，决定性实验）

命令批 `forensics_cmds.txt`，完整输出 `crash_session.log`；补充会话 `crash_session_supplements.log`（vtop 走查 + 非对齐窗口直读 + 结构体偏移验证）。执行方式：`taskset -c 0-31 timeout 3600 crash <vmlinux> <vmcore> -i <cmds>`（隔离 0-31 核，绝不使用 CPU179）。

**(a) 内存真值对照**【实锤】：
```
crash> px __per_cpu_offset[60]
$4 = 0xffffbe56fa9b6000        <-- 真值：i=60 应取此槽（x25=0x3c=60）
crash> px __per_cpu_offset[179]
$5 = 0xffffbe56fb984000        <-- 崩溃执行核 179 的槽位（亦非零，供交叉对照）
crash> rd -64 __per_cpu_offset 192
ffffc1a9862555d0:  ffffbe56fa1be000 ffffbe56fa1e0000   ← 槽 0/1
（全数组 192 项完美等差：基址 ffffbe56fa1be000，步长 0x22000；
 off[60]−off[0]=0x7f8000=60×0x22000 ✓；off[179]−off[60]=0xfce000=119×0x22000 ✓）
```
被读内存完好无损；坏的是**装入寄存器的那个值**（x20=0xa000ffffbe56fb25）。软件写坏内存的可能被排除（等差数列不可能在单槽被写成撕裂值后还保持全局等差）。

**(b) 撕裂窗口物理定位（本案核心新证据）**【实锤】：
把 192 槽按内存小端序拼成 1536 字节的字节流，搜索 x20 的 8 字节 LE 序列（`25 fb 56 be ff ff 00 a0`）：
```
全流唯一命中: [(125, 2)]   ← 槽 125 起始 + 2 字节（数组基址 + 125*8 + 2 = 基址 + 1002 字节）
等价公式: (off[125]>>16) | ((off[126]&0xFFFF)<<48)
  = (0xffffbe56fb258000 >> 16) | ((0xffffbe56fb27a000 & 0xFFFF) << 48)
  = 0xa000ffffbe56fb25   == x20: True
```
crash 直读验证（`crash_session_supplements.log`，crash_session4 部分）：
```
crash> rd -64 ffffc1a9862559ba 2     ← ffffc1a9862559ba = &__per_cpu_offset + 1002 字节
ffffc1a9862559ba:  a000ffffbe56fb25 c000ffffbe56fb27
                   ^^^^^^^^^^^^^^^^ 与 x20 逐位相等
```
**这条非对齐窗口直读是"撕裂移位族"假说提出以来最直接的物理证据**：撕裂值不是凭空噪声、不是任何槽的算术移位（1~7 字节旋转族比对全部不匹配），而是**内存中真实存在的一段字节流**——只是它从错误的位置（+2 字节相位）开始。相邻的槽 123 窗口（基址+986）读出 `6000ffffbe56fb21`、槽 125 窗口读出 `a000ffffbe56fb25`、下一窗口 `c000ffffbe56fb27`——非对齐相位上每相邻 8 字节就是一个同构形态 `xxxx ffffbe56 fbxx` 的值，撕裂机制在其中**任选了一个相位交付**。
形态归类：与既有撕裂移位族**同构**（数据源相位错位、fill-buffer/字节通道错配），但**相位谱扩展**——既往 08-25-15:58 案为"槽内 1 字节相位（offset[0]≫8）"，本案为 **"2 字节相位 + 跨槽（125/126）边界"**；08-14 案 ROL16 形态（半字旋转）与本案亦不同（旋转族比对不匹配）。汉明距离：`popcount(x20 ^ off[60]) = 35`、`popcount(x20 ^ off[179]) = 37`、`popcount(x20 ^ off[0]) = 33`——与既往撕裂案（35/36 位级）同量级，均匀散布无列聚类，再次排除结构化数字故障。

**(c) 迭代号 60 的意义**【实锤】：`x25 = x0 = x3 = x6 = 0x3c`（四寄存器互证），即本次迭代对象是 CPU60 的 rq。与第 11 次案（i=97）相同，迭代号 ≠ 执行核号（179）——**腐化绑定执行核（哪条装载指令在 CPU179 上跑），不绑定被读数据的位置**（槽 60 与槽 179 都在同一数组同一页，真值都完好）。

**(d) 反事实验证**【实锤】：
```
Python: x27_true(60) = &runqueues + __per_cpu_offset[60] = 0xffffc1a985e596c0 + 0xffffbe56fa9b6000
      = 0xffff80008080f6c0  (mod 2^64)
crash> p runqueues:60 → 实例内嵌自指针 nohz_csd.info = 0xffff80008080f6c0  ← 逐位一致
        （cfs.rq / rt.rq / active_balance_work.arg 同值，见 crash_session.log）
crash> vtop ffff80008080f6c0
        PHYSICAL: 2037ffe306c0; PTE: e82037ffe30f03 (VALID|DIRTY)   ← VALID
实例健全: cpu = 60, nr_running = 1, cfs.avg.load_avg = 1024, nr_switches = 7643528
```
若那条 `ldr x20,[x0,w25,sxtw#3]` 交付真值，故障指令将平静地读到 1024，程序继续。**异常的唯一必要条件是装载结果被撕裂。**

**(e) 崩溃执行核 179 的 rq 状态交叉**【实锤】：
```
crash> bt → PID 16 TASK: ffff00202514bf00 CPU: 179 COMMAND: "rcu_sched"
crash> p runqueues:179 → cpu = 179, nr_running = 0, curr = 0xffff00202514bf00  ← 恰为崩溃任务自身
                            cfs.avg.load_avg = 4, nr_switches = 9986310
```
rq(179) `curr` 指针与 bt 报告的 panic task 结构体地址逐位相等；`nr_running=0` 与 newidle_balance 的 idle 平衡场景吻合；rq(179) 内嵌自指针 `nohz_csd.info = 0xffff8000817dd6c0` 与 `x27_true(179) = &runqueues + __per_cpu_offset[179]` 逐位一致（Python 复算，`algebra_out.txt` E 节），该地址经 vtop 走查 VALID（PA=0x6057ffe046c0）——两条独立通路（i=60 语义通路与 i=179 对照通路）均闭合。

### P4 软件根因排除

| 假设 | 判定 | 关键反证 |
|---|---|---|
| 内核软件 bug（UAF/越界/竞态） | 排除【实锤】 | 代数闭合 + 反事实验证；内存真值恒完好；同一指令跨 8 个开机的不同 KASLR/不同迭代号（176/175/146/179/97/60…）均崩溃而软件路径完全自洽 |
| DIMM/DDR 颗粒故障 | 排除【实锤】 | EDAC 零记录；被读数组等差完好；撕裂值是数组字节流的真实子串（不是随机位翻转）；损坏随执行核（179）不随地址 |
| L3/互连故障 | 排除【强推】 | 槽 60/125/179 数据均完好（同 NUMA 节点内共享路径无恙）；故障 100% 绑定 CPU179 私有通路 |
| 页表/MMU 硬件走表损坏 | 排除【实锤】 | FAR 非规范域 L0 是坏地址的必然投影（pgd=0 用户表第一级即断）；vtop 对真值地址走查 VALID 证明走表诚实 |
| KASLR/装载地址错位 | 排除【实锤】 | 五路符号咬合 + x24 adrp 页基吻合（algebra_out.txt A 节） |
| "槽位特异性"假说 | 排除【实锤】 | 本案 i=60、第 11 案 i=97：迭代对象都非 179，真值槽均完好，仍崩——腐化绑定执行核 |
| l1d_disable 可缓解 | 排除【实锤】 | 本开机三次试验（2.1s/300s/899s）后卸载，55h 后 WARNING 复发、86.7h 后致命 |

---

## 7. 逻辑链条（寄存器代数闭合与反事实）【逻辑链条】

全部等式由 `algebra.py` 机器验证（模 2⁶⁴），输出存 `algebra_out.txt`：

**第一环 · KASLR 五路咬合**：`x9` 锚（find_busiest_group+0x150）、crash `sym` 四符号（runqueues / nr_cpu_ids / __per_cpu_offset / find_busiest_group）的运行期−静态差全部等于 `0x41a9042f0000`。寄存器现场与符号表互证，不存在地址错读空间。

**第二环 · 故障点代数闭合（撕裂移位）**：
```
x1  = ffffc1a985e596c0   (&runqueues 模板，== sym runqueues 逐位)
x20 = a000ffffbe56fb25   (实收；应为 __per_cpu_offset[60] = ffffbe56fa9b6000)
x27 = x1 + x20 = a000c1a9443c91e5   ← 与崩溃块 x27 逐位相等
FAR = x27 + 0x120 = a000c1a9443c9305 ← 低 48 位与崩溃 FAR (c1a9443c9305) 逐位相等
                                       （48-bit VA 下 dmesg 只打印低 48 位；MMU 报
                                        FAR_EL1 亦取低 48 位，高 16 位 a000 不入报告）
x25 = x0 = x3 = x6 = 0x3c = 60（迭代 CPU 号，四寄存器互证）
```

**第三环 · 内存真值对照 + 撕裂窗口定位**：`__per_cpu_offset[60]=0xffffbe56fa9b6000`（非零）、数组 192 项 `0x22000` 等差完好 → 内存好、寄存器坏。x20 的 8 字节 LE 序列在全数组字节流**唯一**命中"槽 125 +2 字节"处，crash 直读该地址（`ffffc1a9862559ba`）返回值与 x20 **逐位相等**——撕裂值 = 数组字节流在 +2 字节相位上的非对齐 8 字节窗口，**数据源相位错位实锤**。等价公式 `(off[125]>>16) | ((off[126]&0xFFFF)<<48)` 机器复验成立。

**第四环 · 反事实验证**：
```
x27_true(60)  = &runqueues + __per_cpu_offset[60]  = 0xffff80008080f6c0
                == p runqueues:60 的 nohz_csd.info 内嵌自指针（逐位）
                → vtop VALID（PA=0x2037ffe306c0，PTE VALID|DIRTY）
                → 故障装载将读 rq(60)->cfs.avg.load_avg = 1024（+0x120 偏移经 struct 验证），不崩
x27_true(179) = &runqueues + __per_cpu_offset[179] = 0xffff8000817dd6c0
                == p runqueues:179 的 nohz_csd.info（逐位）→ vtop VALID（PA=0x6057ffe046c0）
```
两条独立通路（语义应然 i=60 与对照核 i=179）双双闭合。

**第五环 · FSC 几何归一**：撕裂值使 x27 落入非规范域（bit[63:48]=a000≠ffff/0000），MMU 在 PGD 级即失败 → FSC=L0、pgd=0。与既往撕裂移位三案（08-14/08-17/08-25-15:58）的 L0 签名完全一致；零塌缩族才落 init 域报 L2/L3——**FSC 谱系完全由坏地址落点决定，非两种病**。

**结论**：五环全部机器闭合，无一手工计算。逻辑链的唯一自由变量是 `ldr x20,[x0,w25,sxtw#3]` 的返回值——它在 CPU179 上执行时交付了从错误相位（+2 字节、跨槽边界）读出的数组字节流窗口。

---

## 8. 故障根因【故障根因】

- **子族归类：撕裂移位族（tear-and-shift）【实锤】**——x20 实收值是被读数组字节流在 +2 字节相位上的非对齐 8 字节窗口（crash 直读验证逐位一致），x27 = x1 + 撕裂值落入非规范域，FAR=x27+0x120 触发 L0。与 08-14（ROL16 半字旋转）、08-17/08-25-15:58（≫8 跨字节 1 字节相位）同族。**本案为该族新增第 4 个相位数据点：2 字节相位 + 跨槽边界。**
- **微架构判定：LSU 装载数据返回通路 SDC【强推，十二案收敛】**——"从已验证完好的内存装载 → 寄存器获得错误相位的数据 → 坏值作为地址偏移污染后续访存"。本案把"撕裂"的含义精确化了一步：**撕裂值不是损坏的数据，而是错位的数据**——它是内存中真实存在的字节流，只是 fill-buffer/字节通道在数据返回合并时选错了起始相位（+2 字节）。这比"随机位翻转"或"整字清零"更指向**选路/合并控制逻辑**（如 fill-buffer 合并窗口的字节使能相位、lane skew），而非存储单元阵列本身。与 gem5 故障注入实验 `--lsq-structural byte_lane_skew` 复现的 PTR_CORRUPT 形态同族〔既往已证，core179-microarch-rootcause-synthesis/paper_zh.md §5 H5〕。
- **本案增量证据**：(a) 非对齐窗口直读成功——首次把撕裂值与内存中一段真实字节流逐位对上，"撕裂移位"从数值形态推断升级为物理来源实证；(b) 相位谱 1 字节→2 字节→跨槽边界，说明相位错配不是固定偏移而是**可变相位**，与"多字节通道各自边际时序"的模型一致；(c) i=60（又一个非 179 迭代号）再次确认腐化绑定执行核。
- **物理机理层【假设，与既往一致】**：sense-amp/位线均衡在特定调度相位×电压裕量下的边际时序失效；精确到晶体管级需芯片 ATE/DFT/BIST（MBIST/LBIST、shmoo），超出 vmcore 方法论可观测极限——此为证据边界声明，非调查缺失。

---

## 9. 启示【启示】

**对根因模型的增量**：
1. **撕裂相位谱扩展（1 字节 → 2 字节 → 跨槽）**：既往三案撕裂形态（ROL16、≫8）都可用"1 字节粒度的相位错位"描述；本案首次观测到 2 字节相位且窗口跨过 8 字节槽边界。这对 fill-buffer 合并模型是强约束：错配相位不是死的 1 字节偏移，而是**可变相位窗口**——支持"多字节通道（byte lane）各自独立边际时序、合并时相位失配"的结构模型（论文 §5 的 byte_lane_skew 故障模型）。预测：后续案件可能观测到 3~7 字节相位的撕裂值。
2. **110h 存活 + 74.7h 最长静默窗的发作频率统计**：13 次 WARNING 分布于 2.9h/78.4h/110h 三个簇，间隔无单调趋势（最长 74.7h，最短 0.004s）。对预测模型的三点含义：(a) **不能用"最近 N 小时无事件"做安全声明**——74.7h 静默后照样复发；(b) **末段加速是强前兆**——panic 前 3.1s 内三连发（间隔 0.004s/0.023s），如果监控以"1 秒内 ≥2 次 spurious WARNING"为触发条件，理论上能在死前 ~3 秒捕获——对人工处置无意义，但对**自动 offline 脚本**（秒级响应）有边际价值；(c) 发作率与运行时长无关、与 l1d_disable 无关、与负载类型无关（pmdalinux/irqbalance/rcu_sched 三个毫不相干的进程都踩中）——**唯一相关变量是"这条装载指令是否在 CPU179 上执行"**。
3. **rcu_sched 视角的新含义**：崩溃进程首次是内核核心基础设施线程（PID 16，开机即存在）。前 6 案的崩溃者是用户业务进程或 idle 线程，本案是 RCU 根线程——**缺陷核不看对象身份，任何路过 find_busiest_group 的指令流都是候选受害者**。这坐实了"高 AVF 通路"论断：负载均衡是所有 CPU 所有进程共享的内核热路径，110h 满负载机器上它的执行次数以亿计，只要缺陷核在线，命中只是时间问题。

**对三启示（论文 §6）的印证**：
- **fail-fast（§6.1）**：本案末簇三连发（3.1s 内）+ 09-04-11:00 案零前兆构成前兆谱的两个极端——发作可以"零前兆"（24 分钟速死案）也可以"密集前兆但窗口仅 3 秒"（本案）。论文 §6.1 的被动遥测（WARN_RATELIMIT → fail-fast 信号 → 热下线）在本案的边界条件下**需要秒级自动响应回路**才可能生效；人工流程完全来不及。唯一可靠的 fail-fast 是**已知缺陷核立即 offline**。
- **位置锚定校验（§6.2 Positional Parity）**：本案撕裂值是"错位但真实"的数据——ECC/奇偶校验若只校验"数据位完整性"将**漏检**（窗口内字节无损坏），必须校验"数据与位置的绑定关系"（论文 §6.2 的核心论点）才能拦截。本案是该论点迄今最干净的实例：一个通过了所有位级校验的错位值，直接杀死了 RCU 根线程。
- **PEPR（§6.3 制造测试）**：2 字节相位 + 跨槽窗口的撕裂形态为 PEPR（物理感知区域伪穷尽测试）提供了新的目标故障模型参数——fill-buffer 合并窗口的**字节相位错配**应在逃逸分级（启示 1）中标记为高 SDC 风险（i 类：负载数据返回路径 fill-buffer 合并 / load 返回 mux）。

**工程启示**：110h 长存活证明"机器还能跑"与"机器安全"是两回事。对已确认缺陷核的处置不存在"观察等待"的合理窗口——本案机器在 WARNING #1（2.9h）时就已满足论文 §6.1 的遥测标记条件，其后又"健康"运行了 107 小时才死，期间所有监控曲线正常。

---

## 10. 处置建议

1. **立即**：`echo 0 > /sys/devices/system/cpu/cpu179/online` 下线 CPU179。本案是第 7 次致命发作；本开机 WARNING #1 出现于 2.9h，其后的 107h"表面健康期"不应再被解读为安全期。
2. **根本**：整机/整 socket 送修（RMA），引用本报告 §6 P3(b)（非对齐窗口直读——撕裂值物理来源实证）与 §7（五环闭合）作为返修凭证；请厂家对 CPU179 执行核内 MBIST/LBIST 与 shmoo 复现（−30mV 欠压曾可控复现同签名〔既往 gem5-fi 活体报告〕），并针对 **fill-buffer 合并窗口字节相位错配**（2 字节相位、跨 8 字节边界）设计定向测试向量。
3. **不要**再部署 `l1d_disable` 类缓解——本开机三次试验（2.1s/300s/899s 禁用）后故障照常发作，与既往各案结论一致。
4. **监控策略**：继续 grep `Ignoring spurious kernel translation fault`（本案 13 次前兆全部可被此规则捕获）；新增**秒级密度触发**规则（1 秒内 ≥2 次 → 自动 offline 脚本）以覆盖"末簇三连发"形态；但需认识到 09-04-11:00 案（零前兆）证明任何被动监控都有覆盖边界——已知缺陷核的唯一安全策略是立即 offline。

---

## 附录：命令索引（本报告全部取证命令，可复核）

```bash
D=/home/sdc/wangxu/vmcore0102/127.0.0.1-2026-08-31-00:47:32/vmcore-dmesg.txt
VL=/usr/lib/debug/usr/lib/modules/6.6.0-145.3.23.154.oe2403sp3.aarch64/vmlinux
VM=/home/sdc/wangxu/vmcore0102/127.0.0.1-2026-08-31-00:47:32/vmcore

# ① dmesg 法证（本目录 dmesg_forensics.txt）
grep -nE "Linux version|Command line|Memory:" $D | head -5
grep -c "WARNING: CPU:" $D                          # → 13
grep -oE "WARNING: CPU: [0-9]+" $D | sort | uniq -c # → 13 WARNING: CPU: 179
grep -n "Ignoring spurious" $D                      # → 13 条 spurious FAR
awk 'NR>=3195 && NR<=3243' $D                       # 完整崩溃块（x0~x30）
grep -nE "L1D DISABLED|L1D RE-ENABLED" $D           # → 三次 l1d_disable 试验
awk '$0 ~ /^\[/ {ts=$1; gsub(/[\[\]]/,"",ts); if (ts+0>80.7 && ts+0<10520) c++} END{print c+0}' $D  # → 0（静默窗）

# ② 静态语义（vmlinux）
nm $VL | grep -wE "find_busiest_group|runqueues|__per_cpu_offset|nr_cpu_ids|__init_begin|__init_end|__per_cpu_start|__per_cpu_end"
objdump -dl --start-address=0xffff80008013ade8 --stop-address=0xffff80008013ae70 $VL

# ③ crash 动态取证（本目录 forensics_cmds.txt → crash_session.log；14.7G，taskset 隔离 0-31）
taskset -c 0-31 timeout 3600 crash $VL $VM -i forensics_cmds.txt
#   关键命令：sys / bt / sym runqueues / px __per_cpu_offset[60] / px __per_cpu_offset[179]
#             rd -64 __per_cpu_offset 192 / vtop 0000c1a9443c9305 / vtop a000c1a9443c91e5
#             p runqueues:60 / p runqueues:179
# 补充会话（crash_session_supplements.log = session2+3+4+5 合并）：
taskset -c 0-31 timeout 3600 crash $VL $VM -i /dev/stdin <<'EOF'
sys
vtop ffff80008080f6c0
vtop ffff8000817dd6c0
rd -64 ffffc1a9862559ba 2
px __per_cpu_offset[125]
px __per_cpu_offset[126]
p &((struct rq *)0)->cfs.avg.load_avg
quit
EOF

# ④ 代数复算（本目录 algebra.py → algebra_out.txt）
python3 algebra.py
```

**诚实性备注**：(1) 本报告所有引用输出均摘自上述真实执行日志，关键数值（`0xffffbe56fa9b6000`、`0xa000ffffbe56fb25`、`a000c1a9443c91e5`、`rd -64 ffffc1a9862559ba` 首字、`nohz_csd.info = 0xffff80008080f6c0`、`cpu = 60`、`curr = 0xffff00202514bf00`、load_avg=1024 等）已逐条与 `crash_session.log` / `crash_session_supplements.log` / `dmesg_forensics.txt` 原文比对。(2) 模板地址处的直接结构体读 `p ((struct rq *)&runqueues)->cpu` 返回 `page excluded`（init 解映射域物理页不在 PARTIAL DUMP 内），属正常现象；该域内容本就不需要（真值证据来自 `__per_cpu_offset` 数组与 rq 实例）。(3) dmesg 崩溃块打印的 FAR `0000c1a9443c9305` 是 HW 上报 FAR_EL1 的低 48 位（48-bit VA 配置）；x27+0x120 的完整 64 位值 `a000c1a9443c9305` 高 16 位 a000 与 x27 高 16 位一致（源于撕裂值高 16 位），低 48 位与 FAR 逐位吻合——此为 08-14 案"HW 上报高位 vs 寄存器高位差异"签名的反面形态（本案一致而非相异），如实记录。(4) 十二案横向综合（含本案在内的总表更新）在 Task 8 统一完成，本报告不重复编制。

---
*报告生成：2026-09-04 · 深度诊断会话 · 证据全部源自 127.0.0.1-2026-08-31-00:47:32 的 vmcore/vmcore-dmesg.txt 及其 5 个 crash 会话（crash_session.log + crash_session_supplements.log）*
