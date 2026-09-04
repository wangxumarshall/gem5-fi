# CPU179 缺陷核第 12 次致命转储深度诊断报告
## ——同进程同路径二次命中（mi-scavenger × futex→newidle_balance）与 incomplete 转储的法证边界

| 项 | 值 |
|---|---|
| 目标转储 | `/home/sdc/wangxu/vmcore0102/127.0.0.1-2026-09-04-12:33:31/`（vmcore-incomplete 9.2 GB，kdump 未完成 + vmcore-dmesg.txt 190 KB） |
| 主机 | Yangtze Computing R240K V2 / BC82AMQA，BIOS 7.48 06/15/2026（localhost0102） |
| CPU | Kunpeng-920 (HIP08/TaiShan-v110) ×192，8 NUMA 节点 |
| 内核 | 6.6.0-145.3.23.154.oe2403sp3.aarch64 #1 SMP Mon Jul 27 19:00:34 CST 2026（与既往 11 案一致） |
| 崩溃 | 2026-09-04 12:33:31 CST 前后，uptime **5060.5 s ≈ 1.41 h**，CPU **179**，PID 55114 `mi-scavenger` |
| 前兆 | 仅 1 次 WARNING（5022.4 s，CPU 179，PID 61156 `HeapHelper`），距 panic **38.1 s** |
| 结论 | **第 12 次发作，与第 6 次（08-26）同进程（mi-scavenger）、同调用路径（futex_wait_queue→…→newidle_balance→find_busiest_group+0x140）、同子族形态（零塌缩）。x27==x1 且 FAR==x27+0x120 逐位闭合【实锤】；因 vmcore-incomplete 无法做内存真值对照，零塌缩族归类（x20 实收 0）为【强推】。** |

---

## 1. 执行摘要

1. 本案是 CPU179 缺陷核的**第 12 次致命发作**，也是 09-04 当日第 4 次崩溃（10:27 / 11:00 / 12:33 三次连发，前一次开机始于 09-03 18:44）。开机仅 **1.41 小时**即死亡，属短存活案例；距同日上一次崩溃（11:00 案，存活 24 分钟）仅约 2.5 小时。
2. 崩溃签名与第 6 次（08-26 案）**逐项同构**：同进程名 `mi-scavenger`、同用户态入口（futex 系统调用）、同调度路径（`futex_wait_queue→schedule→__schedule→pick_next_task→newidle_balance→load_balance→find_busiest_group`）、同致命指令 `find_busiest_group+0x140/0xb60`、同 Code 窗口五指令字 `f9400782 f879d814 2a1903e0 8b14003b (f9409377)`、同 ESR=0x96000007（FSC=L3，pte=0）、同页表走查输出（pgd/pud/pmd 描述符逐位一致）。
3. 寄存器代数**逐位闭合**【实锤】：x20=0、x27==x1==`ffffc8a996d396c0`（runqueues percpu 模板地址）、FAR=`ffffc8a996d397e0`==x27+0x120——零塌缩族的完整形态闭合。跨开机不变式（x21−x1=0x3f65f0、x24−x21=0x5350、x9−x1≡0xfffffffffe5d1798、x23=0x400）与 08-26 / 09-04-11:00 两案**三案一致**，构成确定性代码路径指纹。
4. **法证边界（诚实声明）**：本转储为 vmcore-incomplete（9.2 GB，kdump 未完成）。crash 8.0.4 加载实际尝试结果：384 个 seek error 后中止于 `page excluded: memory section root table`，**未到达命令提示符**——内存真值对照（`__per_cpu_offset[53]` 真值是否非零）、反事实地址 vtop 走查、`p runqueues:53` 实例验证**全部不可执行**。故 x20 实收 0 是"装载结果被腐化"的判定保持【强推】（升级途径见 §7.4）。
5. 38 秒前的前兆 WARNING 是**本案最有信息量的新证据**：spurious 翻译错（ESR=0x96000004，L0）落在 `ffff604003e63c98`，其寄存器 x26=`ffff604003e63c60` 与 38 秒后致命块的 x26 **逐位相同**——同一 CPU 上、同一调度路径上、**同一个 sched_group 对象**先后两次被扰（先 PTW 读出瞬态误报、后装载数据塌缩为零），两事件相距 38.1 秒。这是"发作窗口内多操作相继受扰"签名在本案的直接体现。
6. 处置建议不变且更为紧迫：**立即 offline CPU179 + 整片送修（RMA）**。本开机 command line 无 isolcpus/offline 参数、dmesg 零 offline 记录——第 12 次崩溃时 CPU179 仍在线，风险持续。

---

## 2. 证据规则与方法

- **证据源**：仅 `vmcore-dmesg.txt`（2681 行，开机至 panic 完整）。vmcore-incomplete 经实际加载尝试确认不可用（见 §6 P3），内存侧证据缺失处一律显式标注"不可验证"。
- **诚实铁律**：本报告每一处引用均为真实命令输出（命令与输出全文存同目录 `dmesg_forensics.txt`，行号可直接复核）；所有 64 位地址运算用 Python3 模 2⁶⁴ 脚本计算（`algebra.py`，输出 `algebra_out.txt`），禁止手算。
- **三级置信**：【实锤】= dmesg 内可直接复核（寄存器值、闭合等式、时间戳、行号）；【强推】= 多源证据收敛但缺内存真值对照（零塌缩族归类、x20 腐化判定）；【假设】= 无法软件验证、明示验证途径（微架构物理机理）。
- **工具**：grep/awk（dmesg 法证）、Python3（代数）、crash 8.0.4-17.oe2403sp4 + debuginfo vmlinux `/usr/lib/debug/usr/lib/modules/6.6.0-145.3.23.154.oe2403sp3.aarch64/vmlinux`（加载尝试，失败如实记录）。
- **跨案参照**：08-26 案报告（第 6 次，同为 mi-scavenger）；09-04-11:00 案（第 11 次，同为零塌缩形态）；core179-microarch-rootcause-synthesis/paper_zh.md §6（三启示）。

---

## 3. 本次开机时间线【时间线】

| 时刻（uptime） | 墙钟（约） | 事件 | dmesg 行号 | 置信 |
|---|---|---|---|---|
| 0.000000 s | 11:09:10 | `Booting Linux on physical CPU 0x0000080000 [0x481fd010]`，KASLR enabled | 1, 3 | 【实锤】 |
| 0.000000 s | — | 内核 6.6.0-145.3.23.154.oe2403sp3.aarch64 #1；Memory: 791048808K/805102592K available | 2, 408 | 【实锤】 |
| 0.000000 s | — | crashkernel=1024M,high 预留（kdump 已武装）；command line 无 isolcpus/offline | 121–122, 387 | 【实锤】 |
| 0.352334 s | — | `smp: Brought up 8 nodes, 192 CPUs`（CPU179 在线） | 1255 | 【实锤】 |
| 21.8 s | — | `Hostname set to <localhost0102>`（即故障机 0102） | 2488 | 【实锤】 |
| 37.9–85.8 s | — | 常规启动消息（firewalld memfd、hns3 link up、dm-2 deprecation）——**此后 dmesg 进入静默** | 2577–2580 | 【实锤】 |
| **5022.426712 s** | ~12:32:03 | **首症暨唯一前兆**：`Ignoring spurious kernel translation fault at ffff604003e63c98`，WARNING: CPU 179, PID 61156 `HeapHelper`，`__do_kernel_fault`（fault.c:494）；ESR=0x96000004（L0）；调用路径含 `_find_next_and_bit+0x18`（与致命崩溃同一 `newidle_balance` 调度路径） | 2581–2583 | 【实锤】 |
| **5060.516765 s** | ~12:32:41 | **致命 Oops**：`Unable to handle kernel paging request at ffffc8a996d397e0`，ESR=0x96000007（FSC=L3, pte=0） | 2628–2629 | 【实锤】 |
| 5060.703166 s | — | CPU: 179 PID: 55114 Comm: **mi-scavenger**（Kdump: loaded, Tainted: G W——W 即 38 秒前那条 WARNING） | 2644 | 【实锤】 |
| 5060.920551 s | — | `SMP: stopping secondary CPUs` → `Starting crashdump kernel...` → `Bye!` | 2678–2680 | 【实锤】 |
| 12:33:31 | — | 转储目录时间戳（kdump 会话建立但**未完成**，产物为 vmcore-incomplete 9.2 GB） | 目录名 | 【实锤】 |

**WARNING→panic 间隔 = 5060.516765 − 5022.426725 = 38.090 s**（脚本计算）。开机 83.7 分钟无事件 → 1 起 spurious 前兆 → 38 秒后致命。

**当日崩溃级联（跨开机上下文，墙钟由 dump 目录时间 − uptime 反推，±分钟级精度）**：09-03 18:44 开机 → 09-04 09:15 崩（第 9 次，存活 14.5 h）→ 09:22 重启 → 10:27 崩（第 10 次，1.1 h）→ 10:35 重启 → 11:00 崩（第 11 次，24 min）→ 11:09 重启 → 12:33 崩（**本案**，1.41 h）。同日四崩，重启不隔断故障——与"核私有缺陷"判定自洽。

---

## 4. 故障现象【故障现象】

### 4.1 Oops 原文（dmesg 行 2628–2656，完整块见 forensics 附件）

```
[ 5060.516765] Unable to handle kernel paging request at virtual address ffffc8a996d397e0
[ 5060.528919]   ESR = 0x0000000096000007
[ 5060.533368]   EC = 0x25: DABT (current EL), IL = 32 bits
[ 5060.546980]   FSC = 0x07: level 3 translation fault
[ 5060.574087] swapper pgtable: 4k pages, 48-bit VAs, pgdp=00002054b0164000
[ 5060.581491] [ffffc8a996d397e0] pgd=10006057fffff403, p4d=10006057fffff403, pud=10006057ffffe403, pmd=10006057ffffa403, pte=0000000000000000
[ 5060.703166] CPU: 179 PID: 55114 Comm: mi-scavenger Kdump: loaded Tainted: G        W
[ 5060.732081] pc : find_busiest_group+0x140/0xb60
[ 5060.737321] lr : find_busiest_group+0x11c/0xb60
```

### 4.2 全量寄存器（x0–x30，dmesg 行 2648–2656）

```
x29: ffff8001e4bcb8c0 x28: ffff8001e4bcb770 x27: ffffc8a996d396c0
x26: ffff604003e63c60 x25: 0000000000000035 x24: ffffc8a997135000
x23: 0000000000000400 x22: ffff604003e635a0 x21: ffffc8a99712fcb0
x20: 0000000000000000 x19: ffff8001e4bcb950 x18: 0000000000000000
x17: 0000000000000000 x16: 0000000000000000 x15: 0000ffff98317e20
x14: 0000000000000000 x13: 0000000000000000 x12: 0000000000000000
x11: 0000000000000000 x10: 0000000000000000 x9 : ffffc8a99530ae58
x8 : ffff8001e4bcb7c8 x7 : 0000000000000000 x6 : 0000000000000035
x5 : ffe0000000000000 x4 : 0000000000000000 x3 : 0000000000000035
x2 : 0000000000007445 x1 : ffffc8a996d396c0 x0 : 0000000000000035
```

### 4.3 Call trace（完整，dmesg 行 2657–2676）

```
find_busiest_group+0x140/0xb60      ← 致命点
load_balance+0x108/0x6c0
newidle_balance+0x198/0x510
pick_next_task_fair+0x110/0x718
pick_next_task+0x60/0x398
__schedule+0x1b4/0x8a0
schedule+0x58/0x130
futex_wait_queue+0x78/0xb0          ← 用户态 futex 睡眠
futex_wait+0xe8/0x1d0
do_futex+0xec/0x1a0
__arm64_sys_futex+0x80/0x198
invoke_syscall+0x50/0x128
el0_svc_common.constprop.0+0xc8/0xf0
do_el0_svc+0x48/0x78
el0_slow_syscall+0x44/0x1b8
el0t_64_sync_handler+0x100/0x130
el0t_64_sync+0x188/0x190
Code: f9400782 f879d814 2a1903e0 8b14003b (f9409377)
```

**与 08-26 案 Call trace 逐帧对照**：两案从 `find_busiest_group` 到 `el0t_64_sync` 的 17 帧完全一致（含各帧偏移 `+0x140/+0x108/+0x198/+0x110/+0x60/+0x1b4/+0x58/+0x78/+0xe8/+0xec/+0x80/+0x50/+0xc8/+0x48/+0x44/+0x100/+0x188`），Code 窗口五指令字逐字相同。

### 4.4 前兆 WARNING 原文（dmesg 行 2581–2583）

```
[ 5022.426712] ------------[ cut here ]------------
[ 5022.426725] Ignoring spurious kernel translation fault at virtual address ffff604003e63c98
[ 5022.426734] WARNING: CPU: 179 PID: 61156 at arch/arm64/mm/fault.c:494 __do_kernel_fault+0x130/0x1b8
[ 5022.426885] CPU: 179 PID: 61156 Comm: HeapHelper Kdump: loaded Not tainted
```

其调用路径（行 2603–2621）同样经 `newidle_balance+0x198 → pick_next_task_fair → … → schedule → futex_wait_queue → … → el0t_64_sync`，异常点在 `_find_next_and_bit+0x18`——即与致命崩溃**同一负载均衡遍历的位扫描环节**。

### 4.5 RAS 负证据（dmesg grep）

- `ACPI: BERT 0x000000002F61FF98 000030 (v01 HISI HIP08 …)` 在位（行 12）；
- `GHES: APEI firmware first mode is enabled`（行 1308）；`EDAC MC0: Giving out device to module ghes_edac.c`（行 2177）；
- **全程零 CE/UE 记录、零 ERRIDR/ERX/mce 事件**。注意：本案开机仅存活 1.4 h 且 dmesg 未见 `rasnode` 扫描记录（08-26 案 8026s 才扫描，本案 5060s 即死，未到扫描时刻）——rasnode 维度本案**无数据**而非"扫描过且干净"，如实区分。

---

## 5. 业务现象【业务现象】

**mi-scavenger 是什么**：与第 6 次（08-26 案）完全相同的业务进程——机上 SDC 压测/清道夫类后台程序（"mi-"前缀家族，同机另见 `HeapHelper` 等 mi 系进程，本案 WARNING 宿主 HeapHelper 即同一业务栈的堆管理辅助线程）。它在 futex 上睡眠等待任务（扫描间隔/工作分配），被唤醒路径进入内核调度器。按既往八案横向统计的定性：**触发者与业务负载无关，唯一公共变量是"崩溃那一刻恰好被调度到 CPU179 上执行"**——mi-scavenger 与 HeapHelper 都不是故障的制造者，只是雷区上的过路者。

**崩溃瞬间它在做什么**：PID 55114 mi-scavenger 发起 `futex` 系统调用进入 `futex_wait_queue` 睡眠；内核在让它睡下的路径上（`schedule → __schedule → pick_next_task_fair`）发现本 CPU 即将空闲，触发 `newidle_balance` 顺手做一次负载均衡；`find_busiest_group` 遍历调度组内各 CPU 的运行队列统计时，一条 `ldr x23, [x27, #288]`（读 `cpu_rq(i)->cfs.avg.load_avg`）因基址寄存器 x27 被 x20=0 塌缩到 percpu 模板地址（init 区，已被 `free_initmem` 解映射）而触发 L3 翻译错误 → Oops → kdump。

**对上层服务的表现**：
1. **整机致命重启**：Oops 不可恢复，`SMP: stopping secondary CPUs` → crashdump kernel → 重启。机器上全部业务（含 mi 系压测栈自身、以及任何共享此机的服务）一次中断。这是 09-04 当日**第四次**同样结局——10:27、11:00、12:33 三小时内三崩，每次重启后 8~9 分钟完成开机、随后数十分钟内再度崩溃。对依赖此机的上层服务而言，表现为**反复的、间隔缩短的服务不可用**。
2. **mi-scavenger 自身任务未完成即死**：其扫描/清理工作在本轮开机只推进了约 1.4 小时就被打断；其业务语义（持续性后台清理）在当日实际上已无法维持。
3. **转储本身不完整**（运维层影响）：kdump 未完成导致 vmcore-incomplete，事后深度取证（内存真值）不可行——故障复发时证据链自动降级，这是缺陷核对运维的次生损耗。

---

## 6. 诊断定位过程【诊断定位过程】

### P1 · dmesg 全量勘察（命令+输出见 `dmesg_forensics.txt`）

开机指纹：`Linux version 6.6.0-145.3.23.154.oe2403sp3.aarch64 … #1 SMP Mon Jul 27 19:00:34 CST 2026`（行 2），与既往 11 案同版本同构建；`Memory: 791048808K/805102592K`（行 408）；command line（行 387）`crashkernel=1024M,high`，**无 isolcpus/offline** → CPU179 带缺陷在线。WARNING 统计：总数 1，per-CPU 分布仅 `CPU: 179`（其余 191 核零事件）。全部异常事件宿主 CPU 唯一：`grep -oE "CPU: [0-9]+" | sort -u` 只返回 179。

### P2 · 崩溃块与 WARNING 块提取

完整 Oops 块（行 2628–2680，awk 提取 90+ 行）与 WARNING 块（行 2581–2641）全部摘录存证。关键读数：
- 致命块：x20=0，x27==x1==`ffffc8a996d396c0`，x25=x0=x6=0x35（=53，迭代 CPU 号三寄存器互证），x23=0x400，x9=`ffffc8a99530ae58`（KASLR 锚，低 16 位 `ae58`=`find_busiest_group+0x150` 页内偏移，与 08-26/11:00 案同构）。
- WARNING 块：x19=0x96000004（ESR 作为 `__do_kernel_fault` 入参），x21=`ffff604003e63c98`（故障地址入参），x26=`ffff604003e63c60`。

### P3 · crash 加载尝试（法证边界实证）

```
cmd: taskset -c 0-31 timeout 1800 crash /usr/lib/debug/usr/lib/modules/6.6.0-145.3.23.154.oe2403sp3.aarch64/vmlinux \
     /home/sdc/wangxu/vmcore0102/127.0.0.1-2026-09-04-12:33:31/vmcore-incomplete -i /dev/stdin   (批命令: sys / quit)
退出码 1；输出 417 行，其中 "crash: seek error" 384 行（IRQ/SDEI stack pointer 等内核虚拟地址定位失败）；
末行: crash: page excluded: kernel virtual address: ffff6057fffaeb00  type: "memory section root table"
未出现 crash> 提示符 → 会话未建立。
```

结论：kdump 未完成使关键内核数据页缺失，crash 无法初始化。**凡依赖 vmcore 内存读数的取证（`__per_cpu_offset[]` 真值、vtop 走查、`p runqueues:53`、rd 数组导出）全部不可执行**，本案证据链止步于 dmesg。

### P4 · 软件成因排除（基于 dmesg 可得证据）

1. **内核/软件 bug 排除**【强推】：同一二进制（同版本同构建日期）在 12 次开机中 11 次崩溃于同一指令，且其余 191 核累计数百小时零事件；寄存器代数（§7）与既证两案（08-26 完整闭环、09-04-11:00 同形态）严格同构；WARNING 与 Oops 都发生在 CPU179 的调度路径而宿主进程各异（HeapHelper/mi-scavenger）——若是软件 bug，不应随核选择发作。
2. **DIMM/DDR 故障排除**【强推】：EDAC/GHES 在位零记录；FAR 是内核虚拟地址且形态与既往"零塌缩"逐位吻合，非物理地址乱码形态。
3. **RAS 可见故障排除**【实锤】：ESR EC=0x25 普通 DABT，非 0x2f SError——硬件从未将其识别为可上报错误（既往已证的"检测盲区"判定）。

### P5 · 定位收敛

寄存器闭合（§7）+ 三案不变式互证 + 38 秒双事件同对象 → 零塌缩族【强推】、CPU179 LSU 装载数据返回通路 SDC 判定维持（§8）。

---

## 7. 逻辑链条（寄存器代数闭合与反事实）【逻辑链条】

### 7.1 指令语义（既往已证，本案签名复核一致）

故障窗口五指令字与 08-26 案逐字相同：

```asm
; kernel/sched/fair.c — update_sg_lb_stats(): for_each_cpu_and(i, group_span, env->cpus)
  …    ldp  x0, x1, [sp, #8]          ; x0 = &__per_cpu_offset[0], x1 = &runqueues（percpu 静态模板）
  …    ldr  x20, [x0, w25, sxtw #3]   ; x20 = __per_cpu_offset[i]        ← 数据来源（i = x25 = 53）
  …    add  x27, x1, x20              ; x27 = &per_cpu(runqueues, i)     (mod 2^64)   ← 8b14003b
  …    ldr  x23, [x27, #288]          ; rq->cfs.avg.load_avg             ← 致命点(+0x140)   ← (f9409377)
```

语义即 C 表达式 `cpu_rq(53)->cfs.avg.load_avg`。

### 7.2 核心闭合等式（Python3 模 2⁶⁴，输出逐位见 `algebra_out.txt`）【实锤】

```
x27 = (x1 + x20) mod 2^64 = ffffc8a996d396c0 + 0 = ffffc8a996d396c0   ← 与崩溃块 x27 逐位一致
x27 == x1（塌缩到模板地址）                                            ← True
FAR = (x27 + 0x120) mod 2^64 = ffffc8a996d396c0 + 0x120 = ffffc8a996d397e0 ← 与上报 FAR 逐位一致
```

即：**x20 实收 0 → x27 塌缩为 percpu 模板地址 → +0x120 的 `ldr` 命中 init 区解映射页 → L3/pte=0**。寄存器侧的零塌缩形态链条完整闭合。

### 7.3 跨开机不变式（三案对照，KASLR 随机化下的确定性指纹）【实锤】

| 不变式 | 08-26（第 6 次） | 09-04-11:00（第 11 次） | 本案（第 12 次） |
|---|---|---|---|
| x21 − x1（nr_cpu_ids↔runqueues 模板） | 0x3f65f0 | 0x3f65f0 | **0x3f65f0** |
| x24 − x21（percpu 数组基址页内偏移） | 0x5350 | 0x5350 | **0x5350** |
| x9 − x1 mod 2⁶⁴（.text 锚↔模板） | 0xfffffffffe5d1798 | 0xfffffffffe5d1798 | **0xfffffffffe5d1798** |
| x9 低 16 位（fbG+0x150 页内偏移） | 0xae58 | 0xae58 | **0xae58** |
| x23（上次迭代 load_avg 残留） | 0x400 | 0x564 | **0x400** |
| Code 窗口五指令字 | 相同 | 相同 | **相同** |
| ESR / FSC | 0x96000007 / L3 | 0x96000006 / L2 | **0x96000007 / L3** |
| x20 | 0 | 0 | **0** |
| x27==x1 且 FAR==x27+0x120 | 是 | 是 | **是** |
| 页表走查 pgd/pud/pmd 描述符 | …f403/…e403/…a403 | — | **…f403/…e403/…a403（与 08-26 逐位相同）** |

三次开机 KASLR 各不相同（x1 高位 ffffa293 / ffffd770 / ffffc8a9），而上述相对距离全部恒定——**这只能来自同一确定性代码路径的同一执行点**，三案互证寄存器语义解释无误。x23=0x400 与 08-26 案同值（第 11 次为 0x564，属正常数据变化）。

### 7.4 反事实推演与法证边界（诚实声明）

**反事实（推演，非本案可实证）**：若该 `ldr x20,[x0,w25,sxtw #3]` 交付真值 `__per_cpu_offset[53]`（真值形态可由 08-26 案的等差数列数组外推：某非零 `ffff…000` 型值），则 x27 将落在正常的 `per_cpu(runqueues,53)` 实例地址，`+0x120` 的 load_avg 装载平静完成，系统继续运行——**异常的唯一必要条件是 x20 被腐化为 0**。此推演的实证前提（真值非零、反事实地址 VALID）在 08-26 案已用 crash 三重验证坐实；本案因 vmcore-incomplete **不可复核**。

**零塌缩族归类的证据结构**：
- 【实锤】部分：x27==x1、FAR==x27+0x120、x20=0、FSC=L3/pte=0、页表走查与 08-26 逐位同——**形态学闭合**。
- 【强推】部分：据此判定"x20 是装载返回通路腐化所致（而非内存中真存 0）"。依据：08-26 案（完整转储）已证同一形态下 `__per_cpu_offset[179]` 内存真值非零且全数组完好等差；本案同形态同路径，最优解释是同一机制。**缺**：本案自身无法排除"内存真值恰好为 0"的（极不可能但逻辑上存在的）对立假设。
- **升级途径**：若未来获得同签名完整转储（如本案后续复发的完整 dump），执行 `px __per_cpu_offset[53]` + `rd -64 __per_cpu_offset 192` + `vtop`（x1 模板+真值偏移）三件套即可将【强推】升【实锤】。

### 7.5 38 秒双事件（本案特有证据）

WARNING（5022.4s）与致命 Oops（5060.5s）的寄存器对照（Python 复算见 `algebra_out.txt`）：

- WARNING 故障地址 `ffff604003e63c98` = WARNING 块 x26 + 0x38；
- WARNING 块 x26 = `ffff604003e63c60` = **致命块 x26（逐位相同）**——同一 sched_group 对象；
- 两事件同在 CPU179、同在 `newidle_balance` 调用路径（WARNING 经 `_find_next_and_bit+0x18` 位扫描，Oops 经 `find_busiest_group+0x140` 队列统计读取，二者是同一次负载均衡遍历的相邻环节）；
- 间隔 38.090 s。

解释【强推】：第一个事件是 PTW/装载读出瞬态误报（内核自判 spurious：重走成功→页表完好→瞬时错），第二个事件是装载数据塌缩（不可恢复）。同一对象、同一路径、同一 CPU 上 38 秒内两类瞬态先后出现——与既往"发作窗口内多操作相继受扰"签名一致，且把 D3（虚假翻译错误）→ D1（数据腐化）的谱系在同一时间窗内直接串联。

---

## 8. 故障根因【故障根因】

**判定：CPU179 核内 LSU 装载数据返回通路间歇性 SDC（静默数据损坏），本案为零塌缩子族第 4 例（08-25 15:42、08-26、09-04-11:00 之后）。**

- **子族归类：零塌缩族【强推】**。形态学证据链【实锤】（§7.2/§7.3）；内存真值对照缺失（vmcore-incomplete），降一级为强推，升级途径已明示（§7.4）。
- **机制**（既往已证，本案签名一致，属【假设】层——软件侧不可再下钻）：`ldr x20,[x0,w25,sxtw #3]`（缩放变址装载）从完好内存读取 `__per_cpu_offset[53]` 时，装载数据返回通路（fill-buffer 合并/load 返回选路，约 L1D 读出段）交付全零；x27=x1+0 塌缩到 `.data..percpu` 模板地址；该区间在 `free_initmem()` 后设计性解映射，MMU 诚实走完四级页表得 pte=0 → L3 翻译错误。**pte=0 无需页表硬件故障假设**。
- **为什么是这张"彩票"**：newidle_balance 是本机最频繁的内核路径之一（每次 CPU 空闲转换都会进入），`find_busiest_group` 内的 per-CPU 遍历是其中缩放变址装载最密集的点——12 案 11 案命中同一指令不是巧合，是**高频指令 × 单核私有故障**的必然交集（观察性关联，如实标注：并非该指令本身有任何特殊）。
- **单核私有性**：本案 2 起事件（1 WARNING + 1 Oops）100% CPU179；其余 191 核本次开机 1.4 h 零事件（历史累计约 600+ 核·小时零事件）。共享资源（L3/DRAM/互连）病因与"仅单核发病"矛盾，排除。
- **物理层边界**：sense-amp/位线/填充缓冲具体失效位置超出 vmcore 方法论可达极限（本案连 vmcore 都不完整，边界更收紧一档），需 ATE/DFT/BIST——明示为证据极限而非调查缺失。

---

## 9. 启示【启示】

### 9.1 同进程同路径二次命中：统计规律进一步收紧

mi-scavenger × `futex_wait_queue→…→newidle_balance→find_busiest_group+0x140` 这一完整组合在 12 案中**精确重现两次**（08-26 第 6 次、本案第 12 次），且两次都是零塌缩子族、都是 pte=0/L3。12 案的宿主进程横跨 swapper、kworker、rcu_sched、claude、sftp-server、mi-scavenger——六种身份无关的进程，唯一公共变量是"那一刻在 CPU179 上"。mi-scavenger 的二次命中进一步佐证：**它不是病因，是这条高频调度路径的常客**（futex 睡眠-唤醒循环使它比一般进程更频繁地把 newidle_balance 推上 CPU179）。对预测模型的意义：宿主进程不可预测，但**路径可预测**——监控应锚定路径签名（`find_busiest_group` + spurious fault 组合）而非进程名。

### 9.2 前兆信号的有效窗口：38 秒

本案 WARNING→panic 仅 38.1 秒，是 12 案中最短的前兆-死亡间隔之一（08-26 案为 65 分钟起）。结合第 11 次的**零前兆直接死亡**，可以量化"spurious WARNING 做预警"策略的真实边界：前兆**有则必中**（12 案中 WARNING 宿主核无一例外是 179），但**窗口可能短到分钟级甚至为零**。fail-fast 逻辑必须自动化（内核/sysfs 层直接下线高危核），人工响应窗口不可依赖——这正是 paper_zh.md §6.1"将 SDC 转化为快速失败信号"的直接论据：被动遥测（`is_spurious_el1_translation_fault` → WARN）成本近零、特异性极高，但只能作为自动触发的引信而非人工告警工单。

### 9.3 incomplete 转储的取证边界：证据链自动降级的教训

本案与第 2 次（08-17）同为 vmcore-incomplete：kdump 自身被同一故障机的重启时序截断。两点教训：
1. **形态学闭合的独立价值**：寄存器代数（x27==x1、FAR==x27+0x120）+ 跨案不变式（KASLR 无关的相对距离）不依赖内存真值即可完成子族归类至【强推】——dmesg-only 法证不是残缺版 crash 法证，而是**分层证据体系的独立一层**。把"实锤/强推"边界写死在报告里（如本案 §7.4），比一个含糊的"已验证"更接近真相。
2. **处置紧迫性的证据学后果**：每多一次崩溃，就有概率再产出一个 incomplete 转储（本案 9.2 GB 无效取证 + 一次整机中断的代价）。**offline CPU179 的成本（1/192 算力）与再崩一次的代价（服务中断 + 证据损失）完全不成比例**——12 次发作后该核仍在线，是本案最刺眼的运维事实。

### 9.4 对应 paper_zh.md §6 三启示

- **启示 1（逃逸分级/§6.3）**：零塌缩（全零交付）是 load 返回路径（fill-buffer 合并/load 返回 mux）缺陷的又一形态学样本——它应与字节旋转、陈旧重放同列为"高 SDC 风险逃逸"故障模型，纳入制造测试逃逸分级指标；本案提供了该形态的第 4 个架构级观测点。
- **启示 2（PEPR 对齐/§6.3）**：全零交付不是任何位翻转模型的自然产物（48 位翻转到全零的概率可忽略），与"结构化而非位级"论断再次吻合——ATPG 故障模型对此类缺陷仍是偶然检测，PEPR 式区域穷尽与状态相关向量（fill-buffer 队列状态）才是靶区。
- **启示 3（SBST 强化/§6.3）**：`__per_cpu_offset[i] → cpu_rq(i)` 的"加载→解引用"链第 12 次把数据通路损坏转化为页错误快速失败——ptrskew 式指针解引用级探针语料的架构针对性再次得到确认；本案同时显示该转化的**前兆形态**（D3 spurious）与**致命形态**（D1 塌缩）可在 38 秒内相继出现，支持把两类信号合并为单一健康评分。

### 9.5 跨案谱系增量（本报告新增数据点）

- 零塌缩族第 4 例（08-25 15:42 / 08-26 / 09-04-11:00 / 本案），pte=0/L3 回归（第 11 次曾现 pmd=0/L2 变体）；
- WARNING→panic 间隔谱新增 38.1 s 极短样本；
- 同一 sched_group 对象 38 秒内先后承受 D3 与 D1 两类瞬态（§7.5，新观测）；
- 12 案中第 2 个 vmcore-incomplete（09-04-12:33 与 08-17 同为 kdump 未完成）。

---

## 10. 处置建议

1. **立即（再次强调，第 12 次）**：`echo 0 > /sys/devices/system/cpu/cpu179/online` 下线 CPU179。本开机（command line 无 isolcpus，dmesg 零 offline 记录）证明该核仍带病在线。下线应按物理核粒度执行并持久化（grub `isolcpus=179` 或 systemd 拉起即下线），防止维护重启后复活。
2. **根本**：整 socket/整机 RMA，引用十二案总表 + 08-26 案 §3.5 反事实实验 + 本案三案不变式作为返修凭证；请厂家执行核内 MBIST/LBIST 与 shmoo 复现（−30 mV 欠压可控复现同签名〔既往 gem5-fi 活体报告〕可作 ATE 起点）。
3. **不要**部署 `l1d_disable` 类缓解——既往实证无效（15:42 案卸载后 3.7 h 仍 panic）。
4. **监控**：自动化 grep `Ignoring spurious kernel translation fault`，命中即自动下线宿主核（本案前兆窗口仅 38 秒，人工流程来不及）；同时监控 kdump 完整性（incomplete 转储意味着证据链降级，应触发"尽快下线取证窗口关闭"的升级逻辑）。
5. **证据保全**：本转储目录（vmcore-incomplete + dmesg）与 08-26 完整转储同签名的组合是"形态学闭合→内存真值"分层的教科书样本，建议原样归档。

---

## 附录：命令索引（全部取证命令，可复核）

```bash
D=/home/sdc/wangxu/vmcore0102/127.0.0.1-2026-09-04-12:33:31/vmcore-dmesg.txt
# ① 开机指纹与 WARNING 统计
wc -l $D                                                        # 2681
grep -nE "Linux version|Command line|Memory:" $D | head -5      # 行 2/387/408
grep -c "WARNING: CPU:" $D                                      # 1
grep -oE "WARNING: CPU: [0-9]+" $D | sort | uniq -c             # 仅 CPU:179
grep -oE "CPU: [0-9]+" $D | sort | uniq -c                      # 全部异常宿主 = 179
# ② 崩溃块与 WARNING 块
awk '/Unable to handle/{f=1} f{print; c++} c>90{exit}' $D       # 完整 Oops（x0~x30）
sed -n '2581,2641p' $D                                          # WARNING 完整块
grep -n "Ignoring spurious" $D                                  # 行 2582
# ③ RAS 负证据与时间线端点
grep -nE "ERRIDR|ERX|EDAC|BERT|GHES|mce|ras" $D | head
grep -E "^\[" $D | head -1; tail -3 $D                          # 开机零点 / panic 终点
grep "pgd=" $D                                                  # 页表走查行
# ④ crash 加载尝试（incomplete，实际失败记录）
taskset -c 0-31 timeout 1800 crash /usr/lib/debug/usr/lib/modules/6.6.0-145.3.23.154.oe2403sp3.aarch64/vmlinux \
  /home/sdc/wangxu/vmcore0102/127.0.0.1-2026-09-04-12:33:31/vmcore-incomplete -i /dev/stdin   # exit 1, 384 seek errors
# ⑤ 代数复算（禁止手算）
python3 algebra.py > algebra_out.txt                            # x27=x1+x20, FAR=x27+0x120, 三案不变式
# ⑥ 跨案对照（08-26 同签名案）
grep "pgd=" /home/sdc/wangxu/vmcore0102/127.0.0.1-2026-08-26-10:37:27/vmcore-dmesg.txt
awk '/Unable to handle/{f=1} f{print; c++} c>60{exit}' /home/sdc/wangxu/vmcore0102/127.0.0.1-2026-08-26-10:37:27/vmcore-dmesg.txt
```

全部命令的真实输出存于同目录 `dmesg_forensics.txt`（244 行）；代数脚本与输出存 `algebra.py` / `algebra_out.txt`。

**方法学备注（诚实记录）**：08-26 案曾发生两次手工 64 位加法错误，均被脚本复算捕获——本案全部地址运算由 `algebra.py` 机器完成，报告数值与 `algebra_out.txt` 逐位一致。本案所有【强推】项的升级途径已在 §7.4 显式写明；incomplete 转储不可执行的取证清单在 §6 P3 逐项列出，未以任何方式伪装为已验证。

---
*报告生成：2026-09-04 · 第 12 次致命转储深度诊断会话 · 证据全部源自 vmcore-dmesg.txt（2681 行）+ crash 加载尝试实录 · 证据极限：dmesg-only（vmcore-incomplete）*
