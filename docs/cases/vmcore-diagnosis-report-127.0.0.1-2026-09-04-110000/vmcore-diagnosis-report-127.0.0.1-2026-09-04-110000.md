# CPU179 缺陷核第 11 次致命转储深度诊断报告
## ——零前兆 24 分钟速死 + 零塌缩族 L2 页表变体（pmd=0）实锤

| 项 | 值 |
|---|---|
| 目标转储 | `/home/sdc/wangxu/vmcore0102/127.0.0.1-2026-09-04-11:00:00/`（46.9 GB，PARTIAL DUMP，vmcore-dmesg.txt 2634 行） |
| 主机 | Yangtze Computing R240K V2 / BC82AMQA，BIOS 7.48 06/15/2026 |
| CPU | Kunpeng-920 (HIP08/TaiShan-v110) ×192，8 NUMA 节点 |
| 内核 | 6.6.0-145.3.23.154.oe2403sp3.aarch64 #1 SMP（debuginfo 精确匹配，Not tainted——十二案唯一） |
| 崩溃 | 2026-09-04 10:59:16 CST（dmesg 时间戳 1456.227941s），uptime **00:24:16**（十二案最短），CPU **179**，PID 56263 `sftp-server` |
| 结论 | **第 11 次独立坐实 CPU179 缺陷核（LSU 装载数据返回通路 SDC）：装载 `__per_cpu_offset[97]` 的指令实收 0（真值 `0xffffa89017090000`），零塌缩使 `x27` 落回 `.data..percpu` 模板地址，`ldr x23,[x27,#288]` 在 free_initmem 解映射域触发翻译故障。本次新在：(a) 全程 0 次 WARNING——十二案唯一无前兆直接死亡；(b) FSC=L2/pmd=0——零塌缩族既往均为 L3/pte=0，本报告以双转储并排 vtop 实锤其为页表几何差异而非新故障通路。** |

---

## 1. 执行摘要

1. 本次 panic 是同一缺陷的**第 11 次发作**，也是**最短存活案例**：开机后 24 分 16 秒即致命，且全程 **0 次 WARNING**（`grep -c "WARNING: CPU:"` = 0）——在十二次开机中唯一一次"零前兆直接死亡"。dmesg 从 91.3s 到 1456.2s 之间**一条内核消息都没有**（awk 全量核验为 0 行），静默 1365 秒后一击毙命。
2. 故障指令与既往四案**逐字相同**：`find_busiest_group+0x140`（`kernel/sched/fair.c` `update_sg_lb_stats()` per-CPU 遍历体），`Code:` 字段五个指令字 `f9400782 f879d814 2a1903e0 8b14003b (f9409377)` 与既往完全一致。寄存器代数闭合：`x27 = x1 + x20 = ffffd77069c696c0 + 0`，`FAR = x27 + 0x120`，逐位成立【实锤】。
3. **迭代号首次为 97（x25=0x61）而非 179**：崩溃执行核仍是 CPU179，但本次被遍历的调度组成员是 CPU97。内存真值对照证明 `__per_cpu_offset[97] = 0xffffa89017090000`（非零），全数组 192 项保持 `0x22000` 等差数列——**内存完好，坏的是装入寄存器的那个值**【实锤】。反事实验证：若实收真值，`x27_true = ffff800080cf96c0`，与 `rq(97)` 实例内嵌自指针 `nohz_csd.info` **逐位一致**，该地址经 vtop 验证 VALID，指令将平静读到 `load_avg=1044`。
4. **L2 变体实锤**：本案 show_pte 报 `pmd=0`（FSC=0x06, level 2），而既往零塌缩案（08-26、15:42）均为 `pte=0`（FSC=0x07, level 3）。本报告对两案 vmcore 分别执行 crash `vtop` 并排走查：**两案的 PGD/PUD 表项值逐位相同（`10006057fffff403`/`10006057ffffe403`），走表路径完全一致，唯一差别是本案该 2MB 块的 PMD 表项已清零、08-26 案该 PMD 表项仍在而其下 PTE 清零**——即同一"init 区解映射"设计在不同开机 KASLR 滑移下的页表拆除进度/粒度投影不同，**不是新故障通路**【实锤】。
5. 微架构根因判定不变且进一步收敛：零塌缩（实收 0）+ 迭代号 97（非 179）说明**腐化与"被读哪个槽位"无关，只与"哪条装载指令在 CPU179 上执行"有关**——再次指向 LSU 装载数据返回通路（fill-buffer/读出选路）交付错误（本例为全零）数据，而非存储阵列位翻转。RAS/EDAC/GHES 全程静默与"故障位于核私有、不在任何 RAS 覆盖内"自洽。
6. 处置紧迫性升级：**本机已 11 次致命发作，且本案证明故障可完全无前兆地杀死一台刚开机 24 分钟的机器**——"用 WARNING 做预警监控"的策略存在覆盖边界。立即 offline CPU179 并整片送修（RMA）。

---

## 2. 证据规则与方法

- **只依据 vmcore / vmcore-dmesg.txt 取证**；08-26 案引用处仅使用其 vmcore-dmesg.txt 与本次对其 vmcore 重新执行的 crash 会话（非转述旧报告）。
- 所有 64 位地址加法一律 Python3 模 2⁶⁴ 计算（本目录 `algebra.py`，输出 `algebra_out.txt`），并以 crash 内建 per-cpu 解析器与结构体内嵌自指针独立对照，杜绝手算误差。
- 工具：crash 8.0.4-17.oe2403sp4 + 精确版本 debuginfo vmlinux（`/usr/lib/debug/usr/lib/modules/6.6.0-145.3.23.154.oe2403sp3.aarch64/vmlinux`）；objdump -dl（DWARF 行号）；grep/awk（dmesg 法证）。已知怪癖：crash `-i` 批首行被吞（首行放无害命令）、`log` 命令在此类 PARTIAL DUMP 上挂起（禁用，dmesg 一律取自 vmcore-dmesg.txt）、加载期 ~384 条 IRQ/SDEI stack seek error 属转储未含该区的正常现象。
- 报告区分三层置信：**【实锤】**= dump 内可复核证据；**【强推】**= 多源证据收敛的推断；**【假设】**= 无法软件验证的部分，明示验证途径。

---

## 3. 本次开机时间线【时间线】

| 时刻（dmesg 时间戳） | 事件 | 证据 |
|---|---|---|
| 0.000000s（2026-09-04 约 10:35:00） | `Booting Linux on physical CPU 0x0000080000 [0x481fd010]`，内核 6.6.0-145.3.23.154.oe2403sp3.aarch64 #1 | dmesg 行 1 |
| 0~1.5s | 硬件枚举：BERT（HISI HIP08）在位、GHES firmware-first 使能、ghes_edac 注册、192 核启动 | dmesg 行 12/1307/1857/2175 |
| 1.111667s | pstore: crash dump compression: deflate（kdump 就绪） | dmesg 行 1945 |
| 29.2s | RPC rdma transport 注册，网络栈就绪 | dmesg 后段 |
| 41.15s | `hns3 enp189s0f0: link up`（业务网卡上线） | dmesg |
| 91.300631s | `block dm-2: the capability attribute has been deprecated`——**本开机最后一条正常内核消息** | dmesg 行 2579 前最后一行 |
| 91.3s ~ 1456.2s | **静默 1365 秒：0 条内核消息、0 次 WARNING、0 次 spurious fault**（awk 计数为 0；十二案唯一零前兆开机） | 全量核验 |
| 1456.227941s | `Unable to handle kernel paging request at virtual address ffffd77069c697e0`——CPU179 上 sftp-server（PID 56263）经 pipe_write→schedule→newidle_balance 触发负载均衡，`find_busiest_group+0x140` 崩溃 | dmesg 行 2580 |
| 1456.641244s | `Starting crashdump kernel...` → kdump 完成，46.9G vmcore 落盘 | dmesg 行 2633 |

**与既往十案的对照**：既往首症（首次 WARNING）最早也在开机 835s（08-24 案），本案连一次 WARNING 都没有；存活时间从历来最短 418s（15:58 案）刷新认知——**本案 1456s 全程无任何可观测前兆**，"spurious WARNING 先于 panic 出现"的经验规律在本案失效。

---

## 4. 故障现象【故障现象】

Oops 原文（vmcore-dmesg.txt 行 2580 起，摘录）：

```
[ 1456.227941] Unable to handle kernel paging request at virtual address ffffd77069c697e0
[ 1456.240085]   ESR = 0x0000000096000006
[ 1456.244536]   EC = 0x25: DABT (current EL), IL = 32 bits
[ 1456.258147]   FSC = 0x06: level 2 translation fault        <-- 既往零塌缩案均为 0x07 (level 3)
[ 1456.285262] swapper pgtable: 4k pages, 48-bit VAs, pgdp=00004021dc494000
[ 1456.292667] [ffffd77069c697e0] pgd=10006057fffff403, p4d=10006057fffff403, pud=10006057ffffe403, pmd=0000000000000000
                                                                                        ^^^ pmd=0，走表止步于 L2
[ 1456.412409] CPU: 179 PID: 56263 Comm: sftp-server Kdump: loaded Not tainted 6.6.0-145.3.23.154.oe2403sp3.aarch64 #1
[ 1456.439674] pc : find_busiest_group+0x140/0xb60
[ 1456.444916] lr : find_busiest_group+0x11c/0xb60
[ 1456.454163] x29: ffff8000e6f6b8c0 x28: ffff8000e6f6b770 x27: ffffd77069c696c0
[ 1456.462008] x26: ffff604003ed3900 x25: 0000000000000061 x24: ffffd7706a065000
[ 1456.469852] x23: 0000000000000564 x22: ffff604003ed3a80 x21: ffffd7706a05fcb0
[ 1456.477694] x20: 0000000000000000 x19: ffff8000e6f6b950 x18: 0000000000000000
[ 1456.509061] x8 : ffff8000e6f6b7c8 x7 : 0000000000000000 x6 : 0000000000000061
[ 1456.524744] x2 : 0000000000000012740 x1 : ffffd77069c696c0 x0 : 0000000000000061
[ 1456.535731] Call trace:
[ 1456.535731]  find_busiest_group+0x140/0xb60
[ 1456.540616]  load_balance+0x108/0x6c0
[ 1456.545605]  newidle_balance+0x198/0x510
[ 1456.550759]  pick_next_task_fair+0x110/0x718
[ 1456.556227]  pick_next_task+0x60/0x398
[ 1456.561166]  __schedule+0x1b4/0x8a0
[ 1456.570230]  pipe_write+0x1ec/0x558
[ 1456.574874]  new_sync_write+0x140/0x158
[ 1456.579861]  vfs_write+0x21c/0x2b0
[ 1456.584413]  ksys_write+0xf4/0x118
[ 1456.588958]  __arm64_sys_write+0x24/0x38
[ 1456.604767]  el0_svc_common.constprop.0+0xc8/0xf0  ← el0_slow_syscall ← el0t_64_sync
[ 1456.624584] Code: f9400782 f879d814 2a1903e0 8b14003b (f9409377)
```

要点：ESR=0x96000006（DABT、WnR=0 读访问、FSC=0x06 L2）；`Code:` 与既往四案逐字相同；崩溃时 1 分钟负载 15.67（crash `sys`）——24 分钟内机器已在承压。

---

## 5. 业务现象【业务现象】

- **崩溃进程是谁**：`sftp-server`（PID 56263），用户态文件传输服务进程。崩溃时它正在执行 `write()` 系统调用写入管道（`ksys_write → pipe_write`），`pipe_write` 在等待管道容量时调用 `schedule()` 让出 CPU，内核在为新任务选核时进入 `newidle_balance`（idle 平衡）路径触发负载均衡，均衡器遍历调度组内 CPU 时撞上缺陷核装载。
- **对上层服务的表现**：该 sftp 会话的文件传输**当场中断**（用户可见传输停滞/连接复位），且因 Oops 不可恢复直接进入 kdump——**整机所有业务（本机 2225 个任务，含传输、扫描、系统服务）瞬间停摆并重启**。对运维而言，这是一台刚上线 24 分钟、尚在爬负载阶段（load 15.67）的生产机的**无预告宕机**：没有任何日志前兆可供告警系统捕获，监控曲线在 panic 前一根采样点完全正常。
- **业务连续性含义**：与 08-26 案（mi-scavenger）、08-31 案（rcu_sched）等后台线程视角不同，本案与 09-04-10:27 案同为**直接面向用户的传输业务进程**视角——缺陷核杀死的不是"内部维护任务"，而是用户正在使用的服务本身。

---

## 6. 诊断定位过程【诊断定位过程】

### P1 勘察（dmesg 全量法证）

命令与输出见本目录 `dmesg_forensics.txt`。关键结果：
- `grep -c "WARNING: CPU:"` → **0**；`grep -oE "WARNING: CPU: [0-9]+" | sort | uniq -c` → 空输出。**零 WARNING，全 CPU 域干净**。
- 91.3s~1456.2s 之间内核消息数为 0（awk 全量核验）。
- RAS 负证据：BERT 在位内容空、GHES firmware-first 使能、ghes_edac 注册，全程零 CE/UE；无 `Ignoring spurious` 记录（本案连这个都没有）。
- 崩溃块寄存器全量提取（x0~x30 + pstate + Code），见 §4。

### P2 静态反汇编与符号语义重建（vmlinux + DWARF）

`objdump -dl` 于 `find_busiest_group` 静态基址 `0xffff80008013ad08`（nm 输出），故障窗口（与既往四案同窗口，本内核再验证一次）：

```asm
; kernel/sched/fair.c — update_sg_lb_stats(): for_each_cpu_and(i, group_span, env->cpus)
ffff…ae10  bl   _find_next_and_bit        ; x0 = 下一个置位 CPU 编号 i
ffff…ae24  mov  x25, x0                   ; x25 = i（本案 = 0x61 = 97）
ffff…ae34  ldp  x0, x1, [sp, #8]          ; x0 = &__per_cpu_offset[0]; x1 = &runqueues（模板）
ffff…ae3c  ldr  x20, [x0, w25, sxtw #3]   ; x20 = __per_cpu_offset[i]   ← 数据来源（实收 0）
ffff…ae44  add  x27, x1, x20              ; x27 = &per_cpu(runqueues,i) (mod 2^64)
ffff…ae48  ldr  x23, [x27, #288]          ; rq->cfs.avg.load_avg        ← 致命点(+0x140)
```

故障指令字 `f9409377` 解码：`ldr x23, [x27, #288]`（imm12=36, 36×8=0x120）——与 FAR−x27=0x120 精确吻合。
KASLR 锚定【实锤】：崩溃块 `x9 = ffffd7706823ae58 = find_busiest_group+0x150`，反推滑移 `0x576fe8100000`；crash `sym` 四符号（find_busiest_group/runqueues/nr_cpu_ids/__per_cpu_offset）的运行期地址与静态地址之差**五路全部等于同一滑移值**（`algebra_out.txt` A 节）。`x21 = ffffd7706a05fcb0 = &nr_cpu_ids`（值 192）、`x24 = ffffd7706a065000 = &__per_cpu_offset − 0x5d0`（adrp 页基），与 `str x0,[sp,#8]` 构造序列吻合——寄存器现场与指令语义完全自洽。

### P3 crash 动态取证（46.9G 完整转储，决定性实验）

命令批 `forensics_cmds.txt`，完整输出 `crash_session.log`。执行方式：`taskset -c 0-31 timeout 3600 crash <vmlinux> <vmcore> -i forensics_cmds.txt`（隔离 0-31 核，绝不使用 CPU179）。

**(a) 内存真值对照**【实锤】：
```
crash> px __per_cpu_offset[97]
$4 = 0xffffa89017090000        <-- 真值非零；x25=i=97，本指令应取此槽
crash> px __per_cpu_offset[179]
$5 = 0xffffa89017b74000        <-- 崩溃执行核 179 的槽位（亦非零，供交叉对照）
crash> rd -64 __per_cpu_offset 192
ffffd7706a0658d0:  ffffa8901706e000 ffffa89017090000   ← 槽 96/97，与 px 逐位一致
（全数组 192 项完美等差：基址 ffffa890163ae000，步长 0x22000；off[97]−off[0]=0xce2000=97×0x22000 ✓）
```
被读内存完好无损；坏的是**装入寄存器的那个值**（x20=0）。软件写坏内存的可能被排除（等差数列不可能在单槽被写成 0 后还保持）。

**(b) 迭代号 97 的意义**【实锤】：`x25 = x6 = x0 = 0x61`（三寄存器互证），即本次迭代对象是 CPU97 的 rq。这是十一案中**首次**迭代号 ≠ 执行核号（08-26 案 i=179、15:42 案 i=176、08-14 案 i=176）。这一数据点直接否证任何"槽位 179 特异性"假说：腐化跟随**执行核**（CPU179），不跟随**被读数据的位置**（槽 97 与槽 179 物理上都在同一数组的同一 2MB 内，真值都完好）。

**(c) 反事实验证**【实锤】：
```
Python: x27_true(97) = &runqueues + __per_cpu_offset[97] = 0xffffd77069c696c0 + 0xffffa89017090000
      = 0xffff800080cf96c0  (mod 2^64)
crash> p runqueues:97 → 实例内嵌自指针 nohz_csd.info = 0xffff800080cf96c0  ← 逐位一致
        （另一内嵌锚 cfs.rq 自指针同值，见 crash_session.log 行 684）
```
且该实例健全：`cpu = 97`、`nr_running = 1`、`cfs.avg.load_avg = 1044`、`util_avg = 1024`、`nr_switches = 505742`。若那条 `ldr x20,[x0,w25,sxtw#3]` 交付真值，故障指令将平静地读到 1044，程序继续。**异常的唯一必要条件是装载结果被腐化。**

**(d) 崩溃任务与 rq(179) 状态交叉**【实锤】：
```
crash> bt → PID 56263 TASK: ffff402007f26900 CPU: 179 COMMAND: "sftp-server"
crash> p runqueues:179 → cpu = 179, nr_running = 0, curr = 0xffff402007f26900  ← 恰为崩溃任务自身
                            cfs.avg.load_avg = 1987, util_avg = 461, nr_switches = 60653
```
rq(179) `curr` 指针与 bt 报告的 panic task 结构体地址逐位相等；`nr_running=0` 与 newidle_balance 的 idle 平衡场景吻合；rq(179) 内嵌自指针 `nohz_csd.info = cfs.rq = 0xffff8000817dd6c0` 与 `x27_true(179) = &runqueues + __per_cpu_offset[179]` 逐位一致（Python 复算，`algebra_out.txt` D 节）——两条独立通路（i=97 语义通路与 i=179 计划对照通路）均闭合。

### P4 L2/L3 页表变体专项（本案核心新证据）【实锤】

对本案 vmcore 执行 `vtop ffffd77069c696c0`（模板塌缩地址）与 `vtop ffffd77069c697e0`（FAR）：

```
crash> vtop ffffd77069c696c0
PAGE DIRECTORY: ffffd77069a94000
   PGD: ffffd77069a94d70 => 10006057fffff403
   PUD: ffff6057fffffe08 => 10006057ffffe403
   PMD: ffff6057ffffea70 => 0                      ← PMD 表项为 0，走表止步 L2

crash> vtop ffffd77069c697e0
   PGD: ffffd77069a94d70 => 10006057fffff403        ← 与上一走查同 PGD/PUD/PMD 槽
   PUD: ffff6057fffffe08 => 10006057ffffe403
   PMD: ffff6057ffffea70 => 0                      ← 同一 2MB 块，同样止步 L2
```

对 08-26 案 vmcore（13.9G）执行同命令批（`forensics_cmds_0826_vtop_ref.txt`，完整输出 `crash_session_0826_vtop_ref.log`）：

```
crash> vtop ffffa29301d796c0                        （08-26 案模板塌缩地址）
PAGE DIRECTORY: ffffa29301ba4000
   PGD: ffffa29301ba4a28 => 10006057fffff403        ← 与本案 PGD 值逐位相同
   PUD: ffff6057fffff260 => 10006057ffffe403        ← 与本案 PUD 值逐位相同
   PMD: ffff6057ffffe070 => 10006057ffffa403        ← 08-26 案 PMD 表项仍在
   PTE: ffff6057ffffabc8 => 0                       ← 走表推进到 PTE=0，止步 L3

crash> vtop ffff8000817dd6c0                        （08-26 案反事实地址）
   PTE: … => e86057ffe02f03  (VALID|SHARED|AF|NG|PXN|UXN|DIRTY)   ← VALID
```

**并排结论**（两级走查输出逐字对照）：
1. 两案 PGD/PUD 表项值**逐位相同**（`10006057fffff403` / `10006057ffffe403`）——它们都是 init 映射域的同一套上层页表；两案的 x27 都落在**同一个内核映像节**（`.data..percpu`，模板距 `__per_cpu_start` 偏移 `0x176c0`，两案逐位相同，仅 KASLR 滑移不同）。
2. 差异只在 PMD 层之后：本案该 2MB 块的 PMD 表项为 **0**（整块解映射拆除完毕）；08-26 案该 PMD 表项仍指向一个 PTE 页，但对应 PTE 为 **0**。
3. 机理：arm64 `free_initmem()` 在开机末尾对 init 区（含 `.data..percpu` 模板域）做**设计内的永久解映射**，拆除以页表层级从细到粗回收——某次开机里某个 2MB 块的页表处于"PMD 尚存而 PTE 已清"还是"PMD 已清"，取决于该块内各子区间的分布与拆除时序。本案模板的 2MB 块（`0xffffd77069c00000`）内 `.data..percpu` 起点距块首仅 `0x52000`（08-26 案为 `0x162000`）——KASLR 滑移使 percpu 段落在 2MB 块内的**不同相位**，故走表断点层级不同。
4. 因此 **FSC=L2 与 FSC=L3 是同一零塌缩机制在页表几何上的不同投影，不是新故障通路**；两次独立走表（硬件 + 内核 show_pte + crash 复核）一致，证明走表本身诚实，坏的是输入地址。撕裂移位族 FAR 落在非规范域报 L0，零塌缩族 FAR 落在 init 域报 L2 或 L3——FSC 二分/三分法完全由"坏地址落在哪"决定，非两种病。

### P5 软件根因排除

| 假设 | 判定 | 关键反证 |
|---|---|---|
| 内核软件 bug（UAF/越界/竞态） | 排除【实锤】 | 代数闭合 + 反事实验证；内存真值恒完好；同一指令十一案跨 8 个开机的不同 KASLR/不同迭代号均崩溃而软件路径完全自洽 |
| DIMM/DDR 颗粒故障 | 排除【实锤】 | EDAC 零记录；被读数组等差完好；损坏随执行核（179）不随地址（本案槽 97） |
| L3/互连故障 | 排除【强推】 | 槽 97 与 179 数据均完好（同 NUMA 节点内共享路径无恙）；故障 100% 绑定 CPU179 私有通路 |
| 页表/MMU 硬件走表损坏 | 排除【实锤】 | 本案 vtop 与 08-26 vtop 并排证明走表诚实；pmd=0/pte=0 均有 free_initmem 设计性解释 |
| KASLR/装载地址错位 | 排除【实锤】 | 五路符号咬合（algebra_out.txt A 节） |
| "槽位 179 特异"假说 | 排除【实锤·新】 | 本案 i=97：迭代对象不是 179，真值槽 97 完好，仍崩——腐化绑定执行核而非数据槽位 |

---

## 7. 逻辑链条（寄存器代数闭合与反事实）【逻辑链条】

全部等式由 `algebra.py` 机器验证（模 2⁶⁴），输出存 `algebra_out.txt`：

**第一环 · KASLR 五路咬合**：`x9` 锚（find_busiest_group+0x150）、crash `sym` 四符号（runqueues / nr_cpu_ids / __per_cpu_offset / find_busiest_group）的运行期−静态差全部等于 `0x576fe8100000`。寄存器现场与符号表互证，不存在地址错读空间。

**第二环 · 故障点代数闭合（零塌缩）**：
```
x1  = ffffd77069c696c0   (&runqueues 模板，== sym runqueues 逐位)
x20 = 0000000000000000   (实收；应为 __per_cpu_offset[97] = ffffa89017090000)
x27 = x1 + x20 = ffffd77069c696c0   ← 与崩溃块 x27 逐位相等，且 == 模板地址（塌缩）
FAR = x27 + 0x120 = ffffd77069c697e0 ← 与崩溃 FAR 逐位相等（指令字解码 imm12×8=0x120 交叉验证）
x25 = x6 = x0 = 0x61 = 97（迭代 CPU 号，三寄存器互证）
```

**第三环 · 内存真值对照**：`__per_cpu_offset[97]=0xffffa89017090000`（非零）、数组 192 项 `0x22000` 等差完好 → 内存好、寄存器坏。

**第四环 · 反事实验证**：
```
x27_true(97)  = &runqueues + __per_cpu_offset[97]  = 0xffff800080cf96c0
                == p runqueues:97 的 nohz_csd.info 内嵌自指针（逐位）
                → 故障装载将读 rq(97)->cfs.avg.load_avg = 1044，不崩
x27_true(179) = &runqueues + __per_cpu_offset[179] = 0xffff8000817dd6c0
                == p runqueues:179 的 nohz_csd.info / cfs.rq（逐位）
                → 计划要求的 179 通路同样闭合
```
（08-26 案对照：其反事实地址 `0xffff8000817dd6c0` 在其自身 vmcore 中 vtop VALID，PTE=`e86057ffe02f03` VALID|DIRTY，PA=`0x6057ffe026c0`——两案"应然地址有效"同构。）

**第五环 · 页表几何闭合（L2 变体归一）**：本案 vtop 两走查 PMD=0；08-26 案 vtop PMD 非零、PTE=0；两案 PGD/PUD 值逐位相同、模板节内偏移（0x176c0）逐位相同 → L2/L3 之别 = 同一解映射域在不同 KASLR 相位下的页表拆除投影。

**结论**：五环全部机器闭合，无一手工计算。逻辑链的唯一自由变量是 `ldr x20,[x0,w25,sxtw#3]` 的返回值——它在 CPU179 上执行时交付了 0。

---

## 8. 故障根因【故障根因】

- **子族归类：零塌缩族（zero-collapse）【实锤】**——x20 实收 0（真值非零），x27 塌缩回 percpu 模板地址，FAR=x27+0x120 落入 init 解映射域。与 08-26 案、15:42 案同族；本案 FSC 从 L3 变为 L2 已在 §6 P4 归因为页表几何差异。
- **微架构判定：LSU 装载数据返回通路 SDC【强推，十一案收敛】**——"从已验证完好的内存装载 → 寄存器获得腐化值（本例全零）→ 坏值作为地址偏移污染后续访存"。零塌缩（全零交付）与撕裂移位（ROL16/≫8 字节相位错位）同源于**数据返回选路/合并环节交付了错误源或错误相位的数据**，而非存储单元位翻转。
- **本案增量证据**：迭代号 97 ≠ 执行核 179——首次在同一案内直接证明"腐化绑定执行核（CPU179 的装载指令），与被读槽位无关"。结合 12 开机 100% 事件位于 CPU179、其余 191 核零事件，排除共享资源（L3/互连/DRAM）的判定得到最干净的一次验证。
- **零前兆的含义【强推】**：本案 0 次 spurious WARNING，说明 PTW 读出受扰（D3 探针）并非每次装载腐化（D1）发作的必经前奏——D1 可以独立发作且直接致命。这与"装载返回通路与 PTW 读表共享 fill/读出通路但为不同会话"的模型一致：本次发作窗口内只命中了 D-side 装载，未波及任何页表遍历。
- **物理机理层【假设，与既往一致】**：sense-amp/位线均衡在特定调度相位×电压裕量下的边际时序失效；精确到晶体管级需芯片 ATE/DFT/BIST（MBIST/LBIST、shmoo），超出 vmcore 方法论可观测极限——此为证据边界声明，非调查缺失。

---

## 9. 启示【启示】

**对根因模型的增量**：
1. **D1 与 D3 可解耦发作**：十一案中 10 案 panic 前有 spurious WARNING（D3）前兆，本案零前兆——证明 D3 不是 D1 的必要伴随，两者是同一物理病灶在不同会话（D-side 装载 vs PTW 读表）上的独立投影。预测模型若以"先见 D3 后见 D1"为前提，将系统性漏报本案这类发作。
2. **腐化与数据槽位无关的最终确认**：i=97 案例使"槽位特异性"假说的排除从跨案统计（不同案不同 i）升级为单案内证据。
3. **FSC 谱系补全**：零塌缩族现观测到 L3（08-26、15:42）与 L2（本案）两种 FSC；撕裂移位族为 L0。FSC 完全由坏地址落点决定——三值谱系是同一故障的三种页表几何投影，这为快速分诊提供了指纹表（见 §10 监控建议）。

**对"用 WARNING 做预警监控"策略的边界讨论（fail-fast 启示的反面佐证）**：
core179-microarch-rootcause-synthesis/paper_zh.md §6.1 提出的被动遥测路线（把 `WARN_RATELIMIT` 的 spurious translation fault 转化为 fail-fast 信号、核心间对比标记可疑核并热下线）在 10/11 案中成立；**本案是它的边界案例**：零 WARNING 意味着被动遥测在本开机的窗口内没有拿到任何一次拦截机会——机器从"完全健康的外观"直接进入 kdump。这正呼应了该论文 §6.1 边界声明："对纯 D1 类缺陷（加载数据静默损坏、无任何异常前兆），被动遥测无法提前预警——这正是需要主动 SBST 补充的原因"。本案以一个真实的生产宕机为这条边界盖了章：**被动遥测是必要条件而非充分条件**，必须与 fleetscanner/SiliFuzz 式主动测试（论文 §6.1/§6.3 启示 3 的指针解引用级 SBST 语料，模拟 `__per_cpu_offset[i] → cpu_rq(i)` 数据流）组合部署，才能覆盖无前兆发作。24 分钟速死还说明：即便部署了 WARNING 触发的自动 offline，本案也不会给监控回路留出反应时间——**对已知缺陷核，唯一安全的策略是立即 offline，而不是等第一次告警**（论文 §6.1"提前阻断随后必然到来的致命崩溃"）。

**工程启示**：本案再次演示论文 §6.2 的"高 AVF 结构"论断——load-return 通路的输出直接成为地址偏移（`__per_cpu_offset[i] → cpu_rq(i)`），任何损坏都高概率转化为致命访存。若该通路具备论文建议的位置锚定校验（parity/MCE fail-fast），本次全零交付会在进入架构寄存器前被拦截为机器检查，而非静默传播为 panic。

---

## 10. 处置建议

1. **立即**：`echo 0 > /sys/devices/system/cpu/cpu179/online` 下线 CPU179。本案之后本机同日又发生 12:33 第 12 次转储（mi-scavenger，前有 HeapHelper WARNING）——**故障在持续发作，且可无预警杀死刚开机 24 分钟的机器**。
2. **根本**：整机/整 socket 送修（RMA），引用本报告 §6/§7（五环闭合 + 双转储 vtop 并排）与十二案主证据表作为返修凭证；请厂家对 CPU179 执行核内 MBIST/LBIST 与 shmoo 复现（−30mV 欠压曾可控复现同签名〔既往 gem5-fi 活体报告〕）。
3. **不要**再部署 `l1d_disable` 类缓解（既往实证无效）。
4. **监控策略修订**：继续 grep `Ignoring spurious kernel translation fault`（10/11 案仍是最敏感的被动前兆），但**必须认识到其覆盖边界**（本案零前兆）；已知缺陷核不适用"等告警再处置"。有条件时按论文 §6.1 补充周期性主动 SBST（指针解引用级语料）。

---

## 附录：命令索引（本报告全部取证命令，可复核）

```bash
D=/home/sdc/wangxu/vmcore0102/127.0.0.1-2026-09-04-11:00:00/vmcore-dmesg.txt
VL=/usr/lib/debug/usr/lib/modules/6.6.0-145.3.23.154.oe2403sp3.aarch64/vmlinux

# ① dmesg 法证（本目录 dmesg_forensics.txt）
grep -nE "Linux version|Command line|Memory:" $D | head -5
grep -c "WARNING: CPU:" $D                          # → 0
grep -nE "Ignoring spurious|Unable to handle" $D    # → 仅 1 行 (1456.227941)
awk '/Unable to handle/{f=1} f{print; c++} c>110{exit}' $D   # 完整崩溃块
awk '$0 ~ /^\[/ {ts=$1; gsub(/[\[\]]/,"",ts); if (ts+0>91.31 && ts+0<1456) c++} END{print c+0}' $D  # → 0（静默窗）

# ② 静态语义（vmlinux）
nm $VL | grep -wE "find_busiest_group|runqueues|__per_cpu_offset|nr_cpu_ids|__init_begin|__init_end|__per_cpu_start|__per_cpu_end"
objdump -dl --start-address=0xffff80008013ade8 --stop-address=0xffff80008013ae70 $VL

# ③ crash 动态取证（本目录 forensics_cmds.txt → crash_session.log；46.9G，taskset 隔离 0-31）
taskset -c 0-31 timeout 3600 crash $VL \
  /home/sdc/wangxu/vmcore0102/127.0.0.1-2026-09-04-11:00:00/vmcore -i forensics_cmds.txt
#   关键命令：sys / bt / sym runqueues / px __per_cpu_offset[97] / px __per_cpu_offset[179]
#             rd -64 __per_cpu_offset 192 / vtop ffffd77069c696c0 / vtop ffffd77069c697e0
#             p runqueues:97 / p runqueues:179

# ④ 08-26 案 L2/L3 对照（本目录 forensics_cmds_0826_vtop_ref.txt → crash_session_0826_vtop_ref.log）
taskset -c 0-31 timeout 2700 crash $VL \
  /home/sdc/wangxu/vmcore0102/127.0.0.1-2026-08-26-10:37:27/vmcore -i forensics_cmds_0826_vtop_ref.txt
#   关键命令：sym runqueues / vtop ffffa29301d796c0 / vtop ffffa29301d797e0 / vtop ffff8000817dd6c0

# ⑤ 代数复算（本目录 algebra.py → algebra_out.txt）
python3 algebra.py
```

**诚实性备注**：(1) 本报告所有引用输出均摘自上述真实执行日志，关键数值（`0xffffa89017090000`、`0xffff800080cf96c0`、pmd=0、`cpu = 97`、`cpu = 179`、`curr = 0xffff402007f26900`、load_avg=1044/1987 等）已逐条与 `crash_session.log` / `dmesg_forensics.txt` 原文比对。(2) 模板塌缩地址处的直接内存读（`rd -32 ffffd77069c696c0`）返回 `page excluded`——init 解映射域物理页已被回收、不在转储内，这是 pmd=0 的必然结果而非证据缺失；该域内容本就不需要（真值证据来自 `__per_cpu_offset` 数组与 rq 实例）。(3) 十二案横向综合（含本案在内的总表更新）在 Task 8 统一完成，本报告不重复编制。

---
*报告生成：2026-09-04 · 深度诊断会话 · 证据全部源自 127.0.0.1-2026-09-04-11:00:00 与 127.0.0.1-2026-08-26-10:37:27 的 vmcore/vmcore-dmesg.txt 及其 crash 会话*
