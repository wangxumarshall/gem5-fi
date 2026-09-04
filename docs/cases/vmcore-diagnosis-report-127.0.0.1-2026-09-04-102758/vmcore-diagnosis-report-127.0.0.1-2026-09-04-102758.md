# CPU179 缺陷核第 10 次致命转储深度诊断报告
## ——零塌缩族短存活案例 + 当日连续两开机 sftp-server 双杀的第一案（10:27）

| 项 | 值 |
|---|---|
| 目标转储 | `/home/sdc/wangxu/vmcore0102/127.0.0.1-2026-09-04-10:27:58/`（29.7 GB，PARTIAL DUMP，vmcore-dmesg.txt 2731 行） |
| 主机 | Yangtze Computing R240K V2 / BC82AMQA，BIOS 7.48 06/15/2026 |
| CPU | Kunpeng-920 (HIP08/TaiShan-v110) ×192，8 NUMA 节点 |
| 内核 | 6.6.0-145.3.23.154.oe2403sp3.aarch64 #1 SMP（debuginfo 精确匹配，Tainted: G W——因 2 次 spurious WARNING） |
| 崩溃 | 2026-09-04 10:27:14 CST（dmesg 时间戳 3951.160261s），uptime **01:05:51**，CPU **179**，PID 293168 `sftp-server` |
| 结论 | **第 10 次独立坐实 CPU179 缺陷核（LSU 装载数据返回通路 SDC）：装载 `__per_cpu_offset[149]` 的指令实收 0（真值 `0xffffa6616d8f8000`），零塌缩使 `x27` 落回 `.data..percpu` 模板地址，`ldr x23,[x27,#288]` 在 free_initmem 解映射域触发 L3 翻译故障。本案三个辨识点：(a) 短存活——开机 35 分钟首症（WARNING）、70 分钟死亡；(b) 迭代号 149 ≠ 执行核 179，继第 11 次案（i=97）后第二例"腐化绑定执行核、与被读槽位无关"；(c) 与 1.4h 后的下一开机（11:00 案，同为 sftp-server 崩溃）构成当日连续两开机 sftp-server 双杀——负载相依性最直接的样本对。** |

---

## 1. 执行摘要

1. 本次 panic 是同一缺陷的**第 10 次发作**：开机后 35 分钟（2099.55s）出现第一症（CPU179 spurious translation fault WARNING），70 分钟（3951.16s）致命。**短存活案例**：此前最短 418s（15:58 案）为"速死无前兆"，本案则是"前兆出现后 30 分钟内死亡"——前兆到死亡的间隔在十二案中属于短促的一类。
2. 故障指令与既往各案**逐字相同**：`find_busiest_group+0x140`（`kernel/sched/fair.c` `update_sg_lb_stats()` per-CPU 遍历体），`Code:` 字段五个指令字 `f9400782 f879d814 2a1903e0 8b14003b (f9409377)` 与既往完全一致。寄存器代数闭合：`x27 = x1 + x20 = ffffd99f13ae96c0 + 0`，`FAR = x27 + 0x120`，逐位成立【实锤】。
3. **零塌缩族完整实锤**：x20 实测为 0（dmesg 崩溃块），内存真值 `__per_cpu_offset[149] = 0xffffa6616d8f8000`（crash 会话 `px` + `rd` 双路一致），全数组 192 项保持 `0x22000` 等差数列——**内存完好，坏的是装入寄存器的那个值**【实锤】。FSC=L3/pte=0，走表输出（dmesg show_pte 与 crash vtop 双路）PGD/PUD/PMD 均在、PTE=0，与既往零塌缩案（08-26、15:42）页表几何一致。
4. **迭代号 149（x25=0x95）≠ 执行核 179**：崩溃执行核仍是 CPU179，被遍历的调度组成员是 CPU149。与第 11 次案（1.4h 后，i=97）一起构成两例连续的"迭代号 ≠ 执行核"证据——**腐化绑定"哪条装载指令在 CPU179 上执行"，与"被读哪个槽位"无关**【实锤】。
5. 反事实验证：若实收真值，`x27_true(149) = 0xffff8000813e16c0`，与 `p runqueues:149` 实例内嵌自指针 `nohz_csd.info` **逐位一致**；对照通路 `x27_true(179) = 0xffff8000817dd6c0` 与 `p runqueues:179` 的 `curr`（恰为崩溃任务自身 `0xffff00400845bf00`）及其内嵌自指针同样闭合，且该地址 vtop 验证 **VALID**（PTE=`e86057ffe02f03`）——若装载交付真值，指令将平静读到 `load_avg=0`（CPU149 空载）继续执行【实锤】。
6. **跨案联动（当日 sftp-server 双杀）**：本案（10:27，uptime 66 分钟）与 1.4h 后的 11:00 案（uptime 24 分钟）**连续两次开机均由 sftp-server 触发、同路径 pipe_write→schedule→newidle_balance、同指令、同零塌缩族**。两次开机的崩溃负载均高（本案 load 137/153/141，11:00 案 load 15.7）且都在传输业务承压时段——sftp 传输会话的高频调度（pipe_write 阻塞唤醒 + idle 平衡）是该缺陷最高效的"点火器"，§9 详述。
7. 处置紧迫性：**立即 offline CPU179 并整片送修（RMA）**。本机当日已发生 3 次致命转储（09:15/10:27/11:00），故障在持续发作。

---

## 2. 证据规则与方法

- **只依据 vmcore / vmcore-dmesg.txt 取证**；第 11 次案引用处仅使用其已发布的报告事实作对照（其 vmcore 未在本会话重新加载——两案页表几何对照使用第 11 次案报告内已归档的 crash 会话输出，并如实标注）。
- 所有 64 位地址加法一律 Python3 模 2⁶⁴ 计算（本目录 `algebra.py`，输出 `algebra_out.txt`），并以 crash 内建 per-cpu 解析器与结构体内嵌自指针独立对照，杜绝手算误差。
- 工具：crash 8.0.4-17.oe2403sp4 + 精确版本 debuginfo vmlinux（`/usr/lib/debug/usr/lib/modules/6.6.0-145.3.23.154.oe2403sp3.aarch64/vmlinux`）；objdump -d（反汇编）；grep/awk（dmesg 法证）。已知怪癖：crash `-i` 批首行被吞（首行放无害命令 `# probe-warmup`）、`log` 命令在此类 PARTIAL DUMP 上挂起（禁用，dmesg 一律取自 vmcore-dmesg.txt）、加载期 ~384 条 IRQ/SDEI stack seek error 属转储未含该区的正常现象（本会话实测 384 条）。
- 所有重负载命令（crash 加载 29.7G 转储）以 `taskset -c 0-31` 隔离执行，**绝不使用 CPU179**。
- 报告区分三层置信：**【实锤】**= dump 内可复核证据；**【强推】**= 多源证据收敛的推断；**【假设】**= 无法软件验证的部分，明示验证途径。

---

## 3. 本次开机时间线【时间线】

| 时刻（dmesg 时间戳） | 事件 | 证据 |
|---|---|---|
| 0.000000s（2026-09-04 约 09:22:04，由 panic 墙钟倒推） | `Booting Linux on physical CPU 0x0000080000 [0x481fd010]`，内核 6.6.0-145.3.23.154.oe2403sp3.aarch64 #1 | dmesg 行 1 |
| 0~1.5s | 硬件枚举：BERT（HISI HIP08）在位、GHES firmware-first 使能、ghes_edac 注册（EDAC MC0）、192 核启动 | dmesg 行 12/1307/1857/2176 |
| 1.110460s | `pstore: Using crash dump compression: deflate`（kdump 就绪） | dmesg 行 1945 |
| 29.6~29.8s | RPC tcp/rdma transport 注册，网络栈就绪 | dmesg 后段 |
| 30.0~30.1s | EXT4-fs（sda2、dm-2）以 ordered data mode 挂载 | dmesg |
| 42.049318s | `hns3 enp189s0f0: link up`（业务网卡上线） | dmesg |
| 94.493539s | `block dm-2: the capability attribute has been deprecated`——**开机后最后一条正常内核消息** | dmesg |
| 94.5s ~ 2099.5s | **静默 2005 秒**：0 条内核消息（awk 全量核验为 0 行） | 全量核验 |
| 2099.552081s | **首症**：`Ignoring spurious kernel translation fault at virtual address ffff604003e54458`，CPU179，PID 16 `rcu_sched`（`arch/arm64/mm/fault.c:494 __do_kernel_fault`） | dmesg 行 2594 |
| 2117.796132s | 第二症（同形态）：spurious fault @ `ffff604003e61280`，CPU179，PID 16 `rcu_sched` | dmesg 行 2636 |
| 2117.8s ~ 3951.2s | **再静默 1833 秒**：0 条内核消息（awk 全量核验为 0 行） | 全量核验 |
| 3951.160261s | `Unable to handle kernel paging request at virtual address ffffd99f13ae97e0`——CPU179 上 sftp-server（PID 293168）经 pipe_write→schedule→newidle_balance 触发负载均衡，`find_busiest_group+0x140` 崩溃（**开机 65 分 51 秒**） | dmesg 行 2677 |
| 3951.583179s | `Starting crashdump kernel...` → kdump 完成，29.7G vmcore 落盘（目录时间戳 10:27:58） | dmesg 行 2730 |

**短存活画像**：开机 35 分钟首症、70 分钟死亡。两次 WARNING 间隔 18.2 秒成对出现后，机器又"表面健康"地运行了 30.6 分钟才被杀死——首症与死亡之间没有渐进恶化的中间态（无第三次 WARNING、无任何 RAS 事件），符合"间歇性、低概率、单次即致命"的既往发作特征。与当日相邻两案对照：前案 09:15（uptime 14.5h）、后案 11:00（uptime 24 分钟）——当日三开机存活时间 14.5h / 1.1h / 0.4h 递减，§9 讨论。

---

## 4. 故障现象【故障现象】

Oops 原文（vmcore-dmesg.txt 行 2677 起，摘录；完整块见本目录 `dmesg_forensics.txt` ③）：

```
[ 3951.160261] Unable to handle kernel paging request at virtual address ffffd99f13ae97e0
[ 3951.169008] Mem abort info:
[ 3951.172588]   ESR = 0x0000000096000007
[ 3951.177126]   EC = 0x25: DABT (current EL), IL = 32 bits
[ 3951.183228]   SET = 0, FnV = 0
[ 3951.187067]   EA = 0, S1PTW = 0
[ 3951.190993]   FSC = 0x07: level 3 translation fault         <-- L3，与 08-26 案同类
[ 3951.196659] Data abort info:
[ 3951.200325]   ISV = 0, ISS = 0x00000007, ISS2 = 0x00000000
[ 3951.206601]   CM = 0, WnR = 0, TnD = 0, TagAccess = 0       <-- WnR=0：读访问
[ 3951.218544] swapper pgtable: 4k pages, 48-bit VAs, pgdp=000040448bb14000
[ 3951.226036] [ffffd99f13ae97e0] pgd=10006057fffff403, p4d=10006057fffff403, pud=10006057ffffe403, pmd=10006057ffffa403, pte=0000000000000000
                                                                                        ^^^^ pmd 在、pte=0，走表止步 L3
[ 3951.239362] Internal error: Oops: 0000000096000007 [#1] SMP
[ 3951.348040] CPU: 179 PID: 293168 Comm: sftp-server Kdump: loaded Tainted: G        W           6.6.0-145.3.23.154.oe2403sp3.aarch64 #1
[ 3951.377213] pc : find_busiest_group+0x140/0xb60
[ 3951.382539] lr : find_busiest_group+0x11c/0xb60
[ 3951.387857] sp : ffff8001e54ab740
[ 3951.391956] x29: ffff8001e54ab8c0 x28: ffff8001e54ab770 x27: ffffd99f13ae96c0
[ 3951.399884] x26: ffff604003e611e0 x25: 0000000000000095 x24: ffffd99f13ee5000
[ 3951.407810] x23: 0000000000000401 x22: ffff604003e618a0 x21: ffffd99f13edfcb0
[ 3951.415738] x20: 0000000000000000 x19: ffff8001e54ab950 x18: 0000000000000000
[ 3951.447449] x9 : ffffd99f120bae58 x8 : ffff8001e54ab7c8 x7 : 0000000000000000 x6 : 0000000000000095
[ 3951.463303] x2 : 00000000000019850 x1 : ffffd99f13ae96c0 x0 : 0000000000000095
[ 3951.471231] Call trace:
[ 3951.475113]  find_busiest_group+0x140/0xb60
[ 3951.480648]  load_balance+0x108/0x6c0
[ 3951.485624]  newidle_balance+0x198/0x510
[ 3951.490847]  pick_next_task_fair+0x110/0x718
[ 3951.496413]  pick_next_task+0x60/0x398
[ 3951.501443]  __schedule+0x1b4/0x8a0
[ 3951.506203]  schedule+0x58/0x130
[ 3951.510706]  pipe_write+0x1ec/0x558
[ 3951.515477]  new_sync_write+0x140/0x158
[ 3951.520598]  vfs_write+0x21c/0x2b0
[ 3951.525269]  ksys_write+0xf4/0x118
[ 3951.529937]  __arm64_sys_write+0x24/0x38
[ 3951.535121]  invoke_syscall+0x50/0x128
[ 3951.540127]  el0_svc_common.constprop.0+0xc8/0xf0
[ 3951.546087]  do_el0_svc+0x48/0x78
[ 3951.550657]  el0_slow_syscall+0x44/0x1b8
[ 3951.555834]  el0t_64_sync_handler+0x100/0x130
[ 3951.561433]  el0t_64_sync+0x188/0x190
[ 3951.566320] Code: f9400782 f879d814 2a1903e0 8b14003b (f9409377)
```

要点：ESR=0x96000007（DABT、WnR=0 读访问、FSC=0x07 L3）；`Code:` 与既往各案逐字相同；崩溃时 1 分钟负载 **137.39**（crash `sys`：LOAD AVERAGE: 137.39, 153.39, 141.58）——192 核机器上传输业务满负荷承压；任务总数 2008。

两次前兆 WARNING 形态（与既往各案一致，`__do_kernel_fault` 打头的 spurious translation fault，均 CPU179、均 PID 16 rcu_sched、ESR=0x96000004 形态的读访问翻译异常被 `is_spurious_el1_translation_fault` 判定为虚假后限速告警）：

```
[ 2099.552081] Ignoring spurious kernel translation fault at virtual address ffff604003e54458
[ 2099.552090] WARNING: CPU: 179 PID: 16 at arch/arm64/mm/fault.c:494 __do_kernel_fault+0x130/0x1b8
[ 2117.796132] Ignoring spurious kernel translation fault at virtual address ffff604003e61280
[ 2117.796143] WARNING: CPU: 179 PID: 16 at arch/arm64/mm/fault.c:494 __do_kernel_fault+0x130/0x1b8
```

（两次 WARNING 的完整寄存器块与 call trace 存 `dmesg_forensics.txt`——均为 `rcu_gp_kthread → schedule_timeout → __schedule → pick_next_task_fair` 的调度路径，与既往 D3 探针形态一致。）

---

## 5. 业务现象【业务现象】

- **崩溃进程是谁**：`sftp-server`（PID 293168），用户态文件传输服务进程（OpenSSH 的 SFTP 子系统服务端）。崩溃时它正在执行 `write()` 系统调用写管道（`ksys_write → pipe_write`），`pipe_write` 在管道容量不足时调用 `schedule()` 让出 CPU，内核为新任务选核时进入 `newidle_balance`（idle 平衡），负载均衡器遍历调度组内 CPU 时在 CPU179 上撞上缺陷核装载。
- **对上层服务的表现**：该 sftp 会话的文件传输**当场中断**（用户可见传输停滞/连接复位），且因 Oops 不可恢复直接进入 kdump——**整机 2008 个任务瞬间停摆并重启**。对运维而言，这是一台开机 66 分钟、正处于传输高峰承压（load 137/153/141，1/5/15 分钟全部 >137）的生产机的**无预告宕机**：panic 前最后一根监控采样完全正常（最后一次异常信号是 30 分钟前的两条 WARNING，若未配置对应告警规则则完全无感知）。
- **业务连续性含义**：与 08-26 案（mi-scavenger 后台扫描）、08-31/09-03 案（rcu_sched 内核线程）等内部任务视角不同，本案与第 11 次案（1.4h 后）同为**直接面向用户的传输业务进程**视角——缺陷核杀死的不是"内部维护任务"，而是用户正在使用的服务本身。
- **当日连续两开机 sftp-server 双杀**：本案（10:27，第 10 次）与 1.4h 后的 11:00 案（第 11 次，PID 56263）**连续两次开机、两个不同会话的 sftp-server 进程、同一触发路径（pipe_write→schedule→newidle_balance）、同一指令、同零塌缩族**。两次崩溃时刻机器都在传输业务承压状态（本案 load 137、11:00 案 load 15.7 且爬升中）。这不是巧合级的重复：§9 从负载相依性角度讨论——sftp 传输是"管道写阻塞 + 高频调度 + idle 平衡"的组合负载，恰好高频执行 `find_busiest_group` 的 per-CPU 遍历体，把 CPU179 的间歇缺陷的"点火概率"放大到连续两开机必炸的程度。

---

## 6. 诊断定位过程【诊断定位过程】

### P1 勘察（dmesg 全量法证）

命令与输出见本目录 `dmesg_forensics.txt`。关键结果：
- `grep -c "WARNING: CPU:"` → **2**；`grep -oE "WARNING: CPU: [0-9]+" | sort | uniq -c` → `2 WARNING: CPU: 179`（**非 179 核计数为 0**）。
- 两次 WARNING 时间戳：2099.552090s / 2117.796143s（间隔 18.2s，成对出现于 rcu_sched 的调度路径）。
- 静默窗核验：94.5s~2099.5s 之间内核消息 **0** 条；2117.8s~3951.2s 之间 **0** 条。
- RAS 负证据：BERT（HISI HIP08）在位内容空、GHES firmware-first 使能、ghes_edac 注册（EDAC MC0），全程零 CE/UE 记录、零 Hardware error 行。
- 崩溃块寄存器全量提取（x0~x30 + pstate + Code），见 §4。

### P2 静态反汇编与符号语义重建（vmlinux + DWARF）

`objdump -d` 于 `find_busiest_group` 静态基址 `0xffff80008013ad08`（nm 输出），故障窗口（与既往各案同窗口，本内核再验证一次）：

```asm
; kernel/sched/fair.c — update_sg_lb_stats(): for_each_cpu_and(i, group_span, env->cpus)
ffff…ae20  bl   _find_next_and_bit        ; x0 = 下一个置位 CPU 编号 i
ffff…ae24  mov  x25, x0                   ; x25 = i（本案 = 0x95 = 149）
ffff…ae34  ldp  x0, x1, [sp, #8]          ; x0 = &__per_cpu_offset[0]; x1 = &runqueues（模板）
ffff…ae3c  ldr  x20, [x0, w25, sxtw #3]   ; x20 = __per_cpu_offset[i]   ← 数据来源（实收 0）
ffff…ae44  add  x27, x1, x20              ; x27 = &per_cpu(runqueues,i) (mod 2^64)
ffff…ae48  ldr  x23, [x27, #288]          ; rq->cfs.avg.load_avg        ← 致命点(+0x140)
```

故障指令字 `f9409377` 解码：`ldr x23, [x27, #288]`（imm12=36, 36×8=0x120）——与 FAR−x27=0x120 精确吻合。
KASLR 锚定【实锤】：崩溃块 `x9 = ffffd99f120bae58 = find_busiest_group+0x150`（`bl cpu_util_cfs` 的返回地址），反推滑移 `0x599e91f80000`；寄存器锚（x9/x21/x24/x1）与 crash `sym` 四符号（find_busiest_group/runqueues/nr_cpu_ids/__per_cpu_offset）的运行期−静态差**八路全部等于同一滑移值**（`algebra_out.txt` A 节）。`x21 = ffffd99f13edfcb0 = &nr_cpu_ids`、`x24 = ffffd99f13ee5000 = __per_cpu_offset − 0x5d0` 的 adrp 页基（objdump：`adrp x24, ffff800081f65000` + `add x0, x24, #0x5d0` + `str x0,[sp,#8]` 构造序列），与 `ldp x0,x1,[sp,#8]` 装载序列吻合——寄存器现场与指令语义完全自洽。

### P3 crash 动态取证（29.7G 完整转储，决定性实验）

命令批 `forensics_cmds.txt`，完整输出 `crash_session.log`。执行方式：`taskset -c 0-31 timeout 3600 crash <vmlinux> <vmcore> -i forensics_cmds.txt`（隔离 0-31 核，绝不使用 CPU179）。crash `sys` 摘要：`DUMPFILE: …10:27:58/vmcore [PARTIAL DUMP]`、`CPUS: 192`、`DATE: Fri Sep 4 10:27:14 CST 2026`、`UPTIME: 01:05:51`、`LOAD AVERAGE: 137.39, 153.39, 141.58`、`TASKS: 2008`；`bt`：`PID: 293168 TASK: ffff00400845bf00 CPU: 179 COMMAND: "sftp-server"`，栈回溯与 dmesg call trace 逐帧一致（find_busiest_group at ffffd99f120bae44 ← el1h_64_sync ← … ← pipe_write ← … ← el0t_64_sync）。

**(a) 内存真值对照**【实锤】：
```
crash> px __per_cpu_offset[149]
$1 = 0xffffa6616d8f8000        <-- 真值非零；x25=i=149，本指令应取此槽
crash> px __per_cpu_offset[179]
$2 = 0xffffa6616dcf4000        <-- 崩溃执行核 179 的槽位（亦非零，供交叉对照）
crash> rd -64 __per_cpu_offset 192
ffffd99f13ee55d0:  ffffa6616c52e000 ffffa6616c550000   ← 槽 0/1，与 px 逐位一致
ffffd99f13ee5a70:  ffffa6616d8d6000 ffffa6616d8f8000   ← 槽 148/149（rd 行内槽位对齐核算）
ffffd99f13ee5b60:  ffffa6616dcd2000 ffffa6616dcf4000   ← 槽 178/179
（全数组 192 项完美等差：基址 ffffa6616c52e000，步长 0x22000；
  off[149]−off[0]=0x13ca000=149×0x22000 ✓；off[179]−off[0]=0x17c6000=179×0x22000 ✓）
```
被读内存完好无损；坏的是**装入寄存器的那个值**（x20=0）。软件写坏内存的可能被排除（等差数列不可能在单槽被写成 0 后还保持——`algebra.py` C 节离线解析 rd 全部 96 行、192 槽逐项校验通过）。

**(b) 迭代号 149 的意义**【实锤】：`x25 = x6 = x0 = 0x95`（三寄存器互证），即本次迭代对象是 CPU149 的 rq。这是继第 11 次案（i=97）之后**第二例迭代号 ≠ 执行核号**（08-26 案 i=179、15:42 案 i=176、08-14 案 i=176）。两例连续的"i ≠ 179 而崩在 179"直接否证任何"槽位 179/97/149 特异性"假说：腐化跟随**执行核**（CPU179），不跟随**被读数据的位置**（槽 149 与槽 179 物理上都在同一数组的同一缓存行域内，真值都完好）。

**(c) 反事实验证**【实锤】：
```
Python: x27_true(149) = &runqueues + __per_cpu_offset[149] = 0xffffd99f13ae96c0 + 0xffffa6616d8f8000
      = 0xffff8000813e16c0  (mod 2^64)
crash> p runqueues:149 → 实例内嵌自指针 nohz_csd.info = 0xffff8000813e16c0  ← 逐位一致
        （cfs.rq 内嵌自指针同值 0xffff8000813e16c0，见 crash_session.log 行 772/1178/1350/1426）
```
该实例健全：`cpu = 149`、`online = 1`、`nr_running = 0`（CPU149 空载）、`cfs.avg.load_avg = 0`、`nr_switches = 32790`。若那条 `ldr x20,[x0,w25,sxtw#3]` 交付真值，故障指令将平静地读到 `load_avg = 0`，程序继续。**异常的唯一必要条件是装载结果被腐化。**

**(d) 崩溃任务与 rq(179) 状态交叉**【实锤】：
```
crash> bt → PID 293168 TASK: ffff00400845bf00 CPU: 179 COMMAND: "sftp-server"
crash> p runqueues:179 → cpu = 179, nr_running = 0, curr = 0xffff00400845bf00  ← 恰为崩溃任务自身
                            cfs.avg.load_avg = 640, util_avg = 83, nr_switches = 80370
```
rq(179) `curr` 指针与 bt 报告的 panic task 结构体地址逐位相等；`nr_running=0` 与 newidle_balance 的 idle 平衡场景吻合；rq(179) 内嵌自指针 `nohz_csd.info = cfs.rq = 0xffff8000817dd6c0` 与 `x27_true(179) = &runqueues + __per_cpu_offset[179]` 逐位一致（Python 复算，`algebra_out.txt` D 节）——两条独立通路（i=149 语义通路与 i=179 计划对照通路）均闭合。且 `vtop 0xffff8000817dd6c0` 返回 **VALID**（PTE=`e86057ffe02f03`，VALID|SHARED|AF|NG|PXN|UXN|DIRTY，PA=`0x6057ffe026c0`）——反事实地址在真实页表中有效。

**(e) 页表走查（L3/pte=0）**【实锤】：
```
crash> vtop ffffd99f13ae96c0                        （模板塌缩地址 == x27）
   PGD: ffffd99f13914d98 => 10006057fffff403
   PUD: ffff6057fffff3e0 => 10006057ffffe403
   PMD: ffff6057ffffe4e8 => 10006057ffffa403        ← PMD 表项仍在
   PTE: ffff6057ffffa748 => 0                       ← PTE 表项为 0，走表止步 L3

crash> vtop ffffd99f13ae97e0                        （FAR = x27+0x120）
   PGD/PUD/PMD 同上（同一 4KB 页）                  ← PTE: => 0，止步 L3
```
与 dmesg show_pte 输出（`pgd=10006057fffff403, p4d=…f403, pud=…e403, pmd=…a403, pte=0000000000000000`）**逐位一致**——硬件走表、内核打印、crash 复核三方一致，证明走表本身诚实，坏的是输入地址。FSC=L3 与 08-26 案（pte=0）同类；与第 11 次案（pmd=0/FSC=L2）的差异是页表几何差异（见 P4）。

### P4 与第 11 次案的 L3/L2 页表几何对照（跨案归一）

本案与 1.4h 后的第 11 次案（11:00 开机）同为零塌缩族，但 FSC 不同：

| | 本案（第 10 次） | 第 11 次案（11:00） |
|---|---|---|
| KASLR 滑移 | 0x599e91f80000 | 0x576fe8100000 |
| x27 模板塌缩地址 | ffffd99f13ae96c0 | ffffd77069c696c0 |
| PGD 表项值 | 10006057fffff403 | 10006057fffff403（**逐位相同**） |
| PUD 表项值 | 10006057ffffe403 | 10006057ffffe403（**逐位相同**） |
| PMD 表项值 | 10006057ffffa403（在） | 0（已清） |
| PTE 表项值 | 0（已清） | ——（走表止步于 PMD） |
| FSC | 0x07 (L3) | 0x06 (L2) |

（第 11 次案走查数据引自其已发布报告归档的 crash 会话输出 `crash_session.log`/`crash_session_0826_vtop_ref.log`——两案的 PGD/PUD 表项值逐位相同，说明两者都是 init 映射域的同一套上层页表、x27 都落在 `.data..percpu` 模板节内距 `__per_cpu_start` 相同偏移处，仅 KASLR 滑移不同。）

机理（与第 11 次案报告 P4 结论互证）：arm64 `free_initmem()` 在开机末尾对 init 区（含 `.data..percpu` 模板域）做**设计内的永久解映射**，页表拆除以层级从细到粗回收。本案该 4KB 页的状态是"PMD 尚存而 PTE 已清"（止步 L3）；第 11 次案同一模板域的 2MB 块状态是"PMD 已清"（止步 L2）——KASLR 滑移使 percpu 模板落在 2MB 块内的不同相位，拆除投影的断点层级随之不同。**FSC=L2 与 L3 是同一零塌缩机制在页表几何上的不同投影，不是新故障通路。** 本案的 L3 形态与 08-26 案（pte=0）完全一致，是零塌缩族的"经典"页表形态。

### P5 软件根因排除

| 假设 | 判定 | 关键反证 |
|---|---|---|
| 内核软件 bug（UAF/越界/竞态） | 排除【实锤】 | 代数闭合 + 反事实验证；内存真值恒完好；同一指令十案跨多个开机的不同 KASLR/不同迭代号（149/97/179/176）均崩溃而软件路径完全自洽 |
| DIMM/DDR 颗粒故障 | 排除【实锤】 | EDAC 零记录；被读数组等差完好；损坏随执行核（179）不随地址（本案槽 149） |
| L3/互连故障 | 排除【强推】 | 槽 149 与 179 数据均完好；故障 100% 绑定 CPU179 私有通路（十二开机 100% 事件位于 CPU179，其余 191 核零事件） |
| 页表/MMU 硬件走表损坏 | 排除【实锤】 | 本案 vtop 与 dmesg show_pte 三方一致；pte=0 有 free_initmem 设计性解释 |
| KASLR/装载地址错位 | 排除【实锤】 | 八路符号咬合（algebra_out.txt A 节） |
| "槽位特异性"假说 | 排除【实锤】 | 本案 i=149：迭代对象不是 179，真值槽 149 完好，仍崩——与第 11 次案（i=97）连续两例互证 |

---

## 7. 逻辑链条（寄存器代数闭合与反事实）【逻辑链条】

全部等式由 `algebra.py` 机器验证（模 2⁶⁴），输出存 `algebra_out.txt`：

**第一环 · KASLR 八路咬合**：`x9` 锚（find_busiest_group+0x150）、寄存器锚 x21/x24/x1、crash `sym` 四符号（find_busiest_group / runqueues / nr_cpu_ids / __per_cpu_offset）的运行期−静态差全部等于 `0x599e91f80000`。寄存器现场与符号表互证，不存在地址错读空间。

**第二环 · 故障点代数闭合（零塌缩）**：
```
x1  = ffffd99f13ae96c0   (&runqueues 模板，== sym runqueues 逐位)
x20 = 0000000000000000   (实收；应为 __per_cpu_offset[149] = ffffa6616d8f8000)
x27 = x1 + x20 = ffffd99f13ae96c0   ← 与崩溃块 x27 逐位相等，且 == 模板地址（塌缩）
FAR = x27 + 0x120 = ffffd99f13ae97e0 ← 与崩溃 FAR 逐位相等（指令字解码 imm12×8=0x120 交叉验证）
x25 = x6 = x0 = 0x95 = 149（迭代 CPU 号，三寄存器互证）
```

**第三环 · 内存真值对照**：`__per_cpu_offset[149]=0xffffa6616d8f8000`（非零）、`[179]=0xffffa6616dcf4000`（非零）、数组 192 项 `0x22000` 等差完好 → 内存好、寄存器坏。

**第四环 · 反事实验证**：
```
x27_true(149)  = &runqueues + __per_cpu_offset[149]  = 0xffff8000813e16c0
                == p runqueues:149 的 nohz_csd.info / cfs.rq 内嵌自指针（逐位）
                → 故障装载将读 rq(149)->cfs.avg.load_avg = 0（CPU149 空载），不崩
x27_true(179)  = &runqueues + __per_cpu_offset[179]  = 0xffff8000817dd6c0
                == p runqueues:179 的 nohz_csd.info / cfs.rq（逐位）
                == vtop 验证 VALID（PTE e86057ffe02f03，PA 0x6057ffe026c0）
                → 计划要求的 179 通路同样闭合且页表有效
```

**第五环 · 页表几何闭合**：本案 vtop 两走查（x27 与 FAR 同一 4KB 页）PGD/PUD/PMD 均非零、PTE=0，与 dmesg show_pte 逐位一致；与第 11 次案并排：PGD/PUD 表项值两案逐位相同，仅 PMD 之后断点层级不同（本案 L3、彼案 L2）→ 同一解映射域在不同 KASLR 相位下的拆除投影。

**结论**：五环全部机器闭合，无一手工计算。逻辑链的唯一自由变量是 `ldr x20,[x0,w25,sxtw#3]` 的返回值——它在 CPU179 上执行时交付了 0。

---

## 8. 故障根因【故障根因】

- **子族归类：零塌缩族（zero-collapse）【实锤】**——x20 实收 0（真值非零），x27 塌缩回 percpu 模板地址，FAR=x27+0x120 落入 init 解映射域、pte=0/FSC=L3（零塌缩族的经典页表形态，与 08-26 案、15:42 案同族同形）。
- **微架构判定：LSU 装载数据返回通路 SDC【强推，十案收敛】**——"从已验证完好的内存装载 → 寄存器获得腐化值（本例全零）→ 坏值作为地址偏移污染后续访存"。零塌缩（全零交付）与撕裂移位（ROL16/≫8 字节相位错位）同源于**数据返回选路/合并环节交付了错误源或错误相位的数据**，而非存储单元位翻转。
- **本案增量证据**：迭代号 149 ≠ 执行核 179——与第 11 次案（i=97）构成连续两例"i ≠ 179 而崩在 179"，"腐化绑定执行核、与被读槽位无关"的判定从单案证据升级为相邻双案证据。
- **前兆形态【实锤】**：2 次 spurious WARNING（D3 探针，PTW 读出受扰）先于致命装载腐化（D1）31.2 分钟出现，且两症间隔仅 18.2s、集中于 rcu_sched 调度路径——D3 在本案是 D1 的前奏（与第 11 次案的零前兆形成对照，两案互为补充：D3 可有可无，D1 独立致命）。
- **物理机理层【假设，与既往一致】**：sense-amp/位线均衡在特定调度相位×电压裕量下的边际时序失效；精确到晶体管级需芯片 ATE/DFT/BIST（MBIST/LBIST、shmoo），超出 vmcore 方法论可观测极限——此为证据边界声明，非调查缺失。

---

## 9. 启示【启示】

**对根因模型的增量**：
1. **负载相依性获得最直接的样本对**：本案与第 11 次案相隔 1.4h（连续两次开机），崩溃进程同为 sftp-server、路径同为 pipe_write→schedule→newidle_balance、指令与子族均相同。当日三开机存活 14.5h → 1.1h → 0.4h，恰与传输负载的时段起伏（本案崩溃时 load 137 为当日峰值区）同向。合理解释是：sftp 传输会话=「管道写阻塞 → schedule → idle 平衡 → `find_busiest_group` per-CPU 遍历」的高频循环，把 CPU179 缺陷的每次发作概率乘上了一个巨大的执行次数基数——**负载越重，点火越快**。这与既往"故障率极低、间隔发作"的画像不矛盾：缺陷的物理触发是低概率事件，但触发窗口的打开频率由负载决定。
2. **迭代号 ≠ 执行核的连续第二例**：i=149（本案）与 i=97（第 11 次案）连续两例，加上既往 i=179/176 各案，"槽位特异性"假说已无任何存活空间。
3. **D3→D3→D1 的时间结构**：本案两症 WARNING（18.2s 内成对）→ 31.2 分钟静默 → 致命 D1。D3 与 D1 的时间间隔可长达几十分钟，"看到 D3 后立即 offline"的窗口在本案是充足的（31 分钟）——若被动遥测生效，本案本可在死亡前被拦截。这为 paper_zh.md §6.1 的 fail-fast 路线提供了正向样本（与第 11 次案的零前兆边界案例互补成对：一个证明"有窗口"，一个证明"窗口不总有"）。

**对监控与容错策略的含义（paper_zh.md §6 三启示在本案的体现）**：
- **§6.1 fail-fast / 被动遥测**：本案的 2 次 spurious WARNING 正是该节所述"最早期、最敏感的探针"。核心间对比遥测（192 核中唯一 CPU179 产生此类事件）在本案有 31 分钟的反应窗口——按该节建议"检测到即标记可疑并热下线"，本案的致命崩溃可被完全避免。**建议落地为自动规则**：`Ignoring spurious kernel translation fault` 单核计数 ≥2 即触发告警/自动 offline（本案恰好 2 次；跨案统计 11/12 开机有此前兆）。
- **§6.2 位置锚定校验（Positional Parity）**：零塌缩=load-return 通路的输出（全零）直接成为地址偏移（`__per_cpu_offset[i] → cpu_rq(i)`）——高 AVF 结构的教科书案例。若该通路具备位置锚定 parity，全零交付会在进入架构寄存器前被拦截为 MCE 而非静默传播为 panic。
- **§6.3 启示 3（SBST 升级至指针解引用级）**：本案再次演示"加载 → 解引用"链是 SDC 的最高风险转化点。当日连续两开机 sftp-server 双杀说明：真实业务负载（而非合成压测）就能高频踩中该链——SBST 语料应包含 `__per_cpu_offset[i] → cpu_rq(i)` 式指针解引用链，在空闲核上周期执行即可在致命发作前检出（fleetscanner/SiliFuzz 路线）。

**工程启示**：对运维的直接可操作结论是——**已知缺陷核的处置不能等**。本案前兆出现（2099s）到死亡（3951s）有 31 分钟，但第 11 次案只有 0 分钟；依赖"前兆驱动"的人工处置流程在这两案之间随机失效。唯一安全的策略是首次确认缺陷签名后立即 offline（当日 09:15 案之后若已 offline，本案与 11:00 案都不会发生）。

---

## 10. 处置建议

1. **立即**：`echo 0 > /sys/devices/system/cpu/cpu179/online` 下线 CPU179。本机当日已发生 3 次致命转储（09:15 第 9 次、本案 10:27 第 10 次、11:00 第 11 次），且第 12 次（12:33）随后仍将发生——**故障在持续发作，每一次重启都在掷骰子**。
2. **根本**：整机/整 socket 送修（RMA），引用本报告 §6/§7（八路 KASLR 咬合 + 五环代数闭合 + 双通路自指针对照）与十二案主证据表作为返修凭证；请厂家对 CPU179 执行核内 MBIST/LBIST 与 shmoo 复现（−30mV 欠压曾可控复现同签名〔既往 gem5-fi 活体报告〕）。
3. **不要**再部署 `l1d_disable` 类缓解（既往实证无效）。
4. **监控策略**：把 `Ignoring spurious kernel translation fault` 的单核计数纳入告警（阈值 ≥2 或出现即告警）；同时认识到其覆盖边界（第 11 次案零前兆）——被动遥测与主动 SBST（paper_zh.md §6.1/§6.3）需组合部署。本案证明前兆窗口可以足够长（31 分钟），自动化的"检测即下线"有真实拦截价值。

---

## 附录：命令索引（本报告全部取证命令，可复核）

```bash
D=/home/sdc/wangxu/vmcore0102/127.0.0.1-2026-09-04-10:27:58/vmcore-dmesg.txt
VL=/usr/lib/debug/usr/lib/modules/6.6.0-145.3.23.154.oe2403sp3.aarch64/vmlinux

# ① dmesg 法证（本目录 dmesg_forensics.txt）
grep -nE "Linux version|Command line|Memory:" $D | head -5
grep -c "WARNING: CPU:" $D                          # → 2
grep -oE "WARNING: CPU: [0-9]+" $D | sort | uniq -c # → 2 WARNING: CPU: 179
grep "WARNING: CPU: 179" $D | awk -F'[][]' '{print $2}' | sort -n | uniq -c   # → 2099.55/2117.79 各 1
grep "Ignoring spurious" $D                         # → 2 行（ffff…4458 / ffff…1280）
awk '/Unable to handle/{f=1} f{print; c++} c>110{exit}' $D   # 完整崩溃块（行 2677 起）
awk '$0 ~ /^\[/ {ts=$1; gsub(/[\[\]]/,"",ts); if (ts+0>94.50 && ts+0<2099.5) c++} END{print c+0}' $D  # → 0（静默窗1）
awk '$0 ~ /^\[/ {ts=$1; gsub(/[\[\]]/,"",ts); if (ts+0>2117.9 && ts+0<3951.1) c++} END{print c+0}' $D  # → 0（静默窗2）
grep -nE "ERRIDR|ERX|EDAC|BERT|GHES|mce|ras|Hardware error|ECC" $D | head -12  # RAS 负证据

# ② 静态语义（vmlinux）
nm $VL | grep -wE "find_busiest_group|runqueues|__per_cpu_offset|nr_cpu_ids|__init_begin|__init_end|__per_cpu_start|__per_cpu_end"
objdump -d --start-address=0xffff80008013ade8 --stop-address=0xffff80008013ae60 $VL

# ③ crash 动态取证（本目录 forensics_cmds.txt → crash_session.log；29.7G，taskset 隔离 0-31）
taskset -c 0-31 timeout 3600 crash $VL \
  /home/sdc/wangxu/vmcore0102/127.0.0.1-2026-09-04-10:27:58/vmcore -i forensics_cmds.txt
#   关键命令：sys / bt / sym find_busiest_group / sym runqueues / sym __per_cpu_offset / sym nr_cpu_ids
#             px __per_cpu_offset[149] / px __per_cpu_offset[179] / rd -64 __per_cpu_offset 192
#             vtop ffffd99f13ae96c0 / vtop ffffd99f13ae97e0 / vtop ffff8000817dd6c0
#             p runqueues:149 / p runqueues:179 / rd -8 ffff8000817dd780

# ④ 代数复算（本目录 algebra.py → algebra_out.txt）
python3 algebra.py
```

**诚实性备注**：(1) 本报告所有引用输出均摘自上述真实执行日志，关键数值（`0xffffa6616d8f8000`、`0xffff8000813e16c0`、`0xffff8000817dd6c0`、pte=0、`cpu = 149`、`cpu = 179`、`curr = 0xffff00400845bf00`、load_avg=0/640 等）已逐条与 `crash_session.log` / `dmesg_forensics.txt` 原文比对。(2) 第 11 次案的页表走查数据（P4 对照表右列）引自其已发布报告归档的 crash 会话输出，本会话未重新加载该 vmcore——引用处已如实标注；两案 PGD/PUD 表项值逐位相同这一对照结论不受影响（其输出在其案件目录可复核）。(3) 模板塌缩地址处的直接内存读属 init 解映射域（pte=0），本就无需读取——真值证据来自 `__per_cpu_offset` 数组与 rq 实例，均已闭环。(4) 十二案横向综合（含本案在内的总表更新）在终案统一完成，本报告不重复编制。(5) 开机墙钟（约 09:22:04）由 panic 墙钟（kdump 落盘目录时间戳 10:27:58 前推至 dmesg 3951.58s 的 `Starting crashdump kernel`）减去 uptime 得出，为推算值非 dmesg 直读，标注于此。

---
*报告生成：2026-09-04 · 深度诊断会话 · 证据全部源自 127.0.0.1-2026-09-04-10:27:58 的 vmcore/vmcore-dmesg.txt 及其 crash 会话*
