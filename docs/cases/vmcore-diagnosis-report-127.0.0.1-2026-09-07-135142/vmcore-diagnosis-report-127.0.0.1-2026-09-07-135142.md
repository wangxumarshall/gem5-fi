# 零塌缩族第 6 案 + 超长静默新纪录：CPU 179 上 `find_busiest_group` 把 `__per_cpu_offset[8]` 读成 0，末次前兆后 42.2 小时才致命

## 副标题：vmcore 127.0.0.1-2026-09-07-13:51:42 深度诊断报告（core179 第 18 次致命转储）

| 项 | 值 |
|---|---|
| 转储 | `/home/sdc/wangxu/vmcore0102/127.0.0.1-2026-09-07-13:51:42/vmcore`（17.4G，PARTIAL DUMP）+ `vmcore-dmesg.txt`（4342 行） |
| 内核 | 6.6.0-145.3.23.154.oe2403sp3.aarch64 #1 SMP（KASLR on） |
| vmlinux | `/usr/lib/debug/lib/modules/6.6.0-145.3.23.154.oe2403sp3.aarch64/vmlinux`；crash 8.0.4-17.oe2403sp4 |
| 整机 | Yangtze Computing R240K V2/BC82AMQA，BIOS 7.48 06/15/2026 |
| CPU | 192 核 / 8 NUMA 节点，故障核 CPU 179 = MPIDR 0x7a0300，节点 7 |
| 崩溃时刻 | 2026-09-07 13:50:53 CST（sys 输出），uptime 223640.8s ≈ 62.12h |
| 崩溃进程 | mi-scavenger（PID 1177282），futex_wait → newidle_balance 路径 |
| 唯一致命块 | CPU 179 / ESR=0x96000006 / FSC=L2（pmd=0）/ FAR=`ffffdf9b728097e0` |
| 前兆 | 38 次 spurious translation fault WARNING，全部 CPU 179；末次距 panic **152076.3s ≈ 42.24h**（全谱新纪录） |
| 子族 | 零塌缩（x20 实收 0，x27 塌缩回 `runqueues` 模板）【实锤】 |
| 报告产物 | 本报告 + `dmesg_forensics.txt` + `algebra.py`/`algebra_out.txt`（13/13 PASS）+ `crash_session{1,2,3,5,6}*.log`（5 份） |

## 1. 执行摘要

1. **【实锤】** 本案与既往 11 个 `find_busiest_group+0x140` 案完全同型：致命指令字 `(f9409377)` = `ldr x23,[x27,#0x120]`（fair.c:5024 内联 `cpu_util_cfs` 读 `cfs_rq.load_avg`），Code 字段五指令字与既往逐字相同。
2. **【实锤】** `sym ffffdf9b728096c0` → **`runqueues`**：x1 精确等于 `.data..percpu` 模板地址；x20 实收 0（内存真值 off[8]=`ffffa0650d91e000` 非零且数组 0x22000 等差完好）→ x27 塌缩到模板 → FAR = 模板+0x120 落 init 解映射域 → L2/pmd=0 翻译故障。零塌缩族第 6 案（继第 4/6/10/11/12 次），L2 变体第 2 案（继第 11 次）。
3. **【实锤】** 反事实三重闭合：`x1 + off[8] = 0xffff8000801276c0` 与 crash `p runqueues` 显示的 `[8]` 实例**逐位相等**；`vtop(该地址)` VALID（PTE `e80037ffeb6f03`）；`rd(该地址+0x120) = 0x400` **恰好等于崩溃时 x23 残留值**——上一次迭代从真实 per-cpu 实例正常读到 0x400，本次迭代 x20 读到 0 而塌缩。真值路径平静可读，不崩。
4. **【实锤】** KASLR 不变式三件套全部成立（x9−x1、x21−x1、x24−x21，见 §7），确认同一确定性代码路径的同一执行点，与 12 案 census §2.8 指纹库完全对齐。
5. **【实锤】** 迭代号 x25=8 ≠ 执行核 179：腐化绑定"哪条装载指令在 CPU179 上执行"而非被读槽位，与既往 10/11 案 i≠179 的谱系一致。
6. **【强推】** 42.24h 超长前兆-panic 间隔刷新全谱纪录（旧纪录第 9 次 10.67h 的 4 倍），进一步压实 census §2.5 "WARNING 频度与剩余寿命无相关"：末次 WARNING 时间对致命时刻零预测力，被动遥测只能做"标记可疑核"不能做"预测窗口"。

## 2. 证据规则与方法

1. 一手证据：dmesg 法证（`dmesg_forensics.txt`）+ crash 8.0.4 对 17.4G PARTIAL dump 实测（5 份 session log 全存本目录）；64 位运算全部 `algebra.py` 机器完成，零手算。
2. PARTIAL DUMP 限制如实声明：runqueues 模板页（ffffdf9b728096c0）自身 page excluded（free_initmem 后该 init 页未进 dump——这本身就是"模板位于 init 解映射域"的又一佐证）；per-cpu 实例页与 `__per_cpu_offset` 数组页在 dump 内可读，本案所有真值对照均落在可读页上。
3. 标注分级：【实锤】dump 内可复核；【强推】多源收敛推断；【假设】无法软件验证部分。

## 3. 本次开机时间线【时间线】

| 时刻（uptime） | 事件 | 证据 |
|---|---|---|
| 0.000s | 开机（≈2026-09-04 23:47 推算），KASLR enabled | dmesg L1/L3 |
| 0.330s | CPU179（MPIDR 0x7a0300）上线 | dmesg L1206 |
| ~33497.05s | **首症**：第 1 次 spurious translation fault（`ffff60401452b50b`），CPU 179，irqbalance 读 `/proc/interrupts` 路径（show_interrupts→seq_printf→__memcpy） | dmesg §dmesg_forensics |
| 33497~39465s | 簇 1：31 条，跨度 5967s | WARNING 时间戳谱 |
| 44094.5s | 簇 2：1 条 | 同上 |
| 56754~57409s | 簇 3：3 条，跨度 655s | 同上 |
| 70534~71565s | 簇 4：3 条，跨度 1030s | 同上 |
| 71564.50s | **末次 WARNING**（第 38 次），此后 dmesg 完全静默 | dmesg |
| 223640.37s | mi-scavenger（PID 1177282）futex_wait 睡入 → newidle_balance → find_busiest_group 迭代至 i=8 时 x20 读出 0 → 塌缩地址解引用 → L2 翻译故障 → Oops → kdump | dmesg L4295 起 |
| 223640.80s | `Starting crashdump kernel...` | dmesg 尾 |

前兆谱要点：38 条 WARNING 100% `CPU: 179`（38/38），宿主进程只有 irqbalance（21）/pmdalinux（17）两个 `/proc/interrupts` 周期读者，spurious 地址全部是 `ffff6040…`/`ffff2040…` 形态的 slub/per-cpu 对象地址（非规范偏移 +非对齐特征与既往各案一致，D3 型 PTW/读出瞬态）。**末次 WARNING→panic 间隔 152076.3s ≈ 42.24h，为 19 案全谱新纪录**（旧纪录：第 9 次 10.67h）。

## 4. 故障现象【故障现象】

dmesg L4295 起崩溃块原文（摘录）：

```
[223640.370375] Unable to handle kernel paging request at virtual address ffffdf9b728097e0
[223640.383047]   ESR = 0x0000000096000006
[223640.394034]   EC = 0x25: DABT (current EL), IL = 32 bits
[223640.402147]   FSC = 0x06: level 2 translation fault
[223640.438229] [ffffdf9b728097e0] pgd=10006057fffff403, p4d=10006057fffff403, pud=10006057ffffe403, pmd=0000000000000000
[223640.559014] CPU: 179 PID: 1177282 Comm: mi-scavenger Kdump: loaded Tainted: G        W
[223640.588889] pc : find_busiest_group+0x140/0xb60
[223640.588889] lr : find_busiest_group+0x11c/0xb60
[223640.604159] x27: ffffdf9b728096c0 ... x25: 0000000000000008 ... x20: 0000000000000000
[223640.778406] Code: f9400782 f879d814 2a1903e0 8b14003b (f9409377)
Call trace:
 find_busiest_group+0x140/0xb60
 load_balance+0x108/0x6c0
 newidle_balance+0x198/0x510
 pick_next_task_fair+0x110/0x718
 ... __schedule → schedule → futex_wait_queue → futex_wait → do_futex → __arm64_sys_futex（用户态 mi-scavenger 发起 futex 系统调用）
```

页表几何（crash session2 `vtop FAR`）：PGD `10006057fffff403` / PUD `10006057ffffe403` / **PMD 0**。与第 11 次案（11:00，唯一 L2 变体）PGD/PUD 逐位同构——同一套 init 上层页表，拆除止步 PMD 层。L2/L3 变体已由 census §2.7 归一为"同一 init 解映射域在不同 KASLR 相位下的拆除投影"。

## 5. 业务现象【业务现象】

- 受害进程 **mi-scavenger**（PID 1177282）：minio 对象存储的垃圾回收辅助进程（mi- 前缀族）。崩溃时它正通过 `futex(FUTEX_WAIT)` 等待锁，睡眠入队触发 `newidle_balance`（CPU 179 即将进入 idle 前的最后负载均衡）。与第 6 次（08-26，同为 mi-scavenger + futex→newidle + 零塌缩）完全同型。
- 业务表现：机器第 18 次非计划重启，minio 服务中断；崩溃时刻 load average 16.21（1min），传输业务在跑。
- 崩溃路径属"所有 CPU 共享的内核热路径"（负载均衡 per-CPU 遍历），业务侧无法规避（census §5.6）。

## 6. 诊断定位过程【诊断定位过程】

**P1 勘察（dmesg）**：38/38 WARNING 全 CPU179；崩溃块六要素提取（§4）。

**P2 静态反汇编**（crash session2 `dis -l find_busiest_group+0x100 30`，/tmp/crash-0907 既有 + 本报告目录 crash_session2_vtop_dis.log）：

```
find_busiest_group+300: ldp x0, x1, [sp, #8]     ← x0=&__per_cpu_offset[], x1=&runqueues（模板）
find_busiest_group+308: ldr x2, [x28, #8]
find_busiest_group+312: ldr x20, [x0, w25, sxtw #3]  ← 按 i=w25 缩放变址装载 off[i]，本次实收 0
find_busiest_group+316: add x27, x1, x20          ← x27 = 模板 + off[i]
find_busiest_group+320: ldr x23, [x27, #288]      ← (f9409377) 致命指令：读 cfs_rq.load_avg（0x120=288）
```

**P3 crash 动态取证**（session5/6，taskset -c 0-31 隔离执行）：

| 命令 | 输出（摘录） | 结论 |
|---|---|---|
| `sym ffffdf9b728096c0` | `ffffdf9b728096c0 (D) runqueues` | x1 语义钉死【实锤】 |
| `p &__per_cpu_offset` | `0xffffdf9b72c055d0` | 数组基址 |
| `p runqueues`（PER-CPU ADDRESSES） | `[8]: ffff8000801276c0`（192 实例 0x22000 等差列出） | 反事实锚点 |
| `rd -64 __per_cpu_offset`（session3） | off[0]=`ffffa0650d80e000`；`p __per_cpu_offset[8/179]` 等差 0x22000 | 数组完好 |
| `vtop ffff8000801276c0` | PTE `e80037ffeb6f03` VALID，物理 37ffeb6000 | 反事实地址真实存在【实锤】 |
| `rd -64 ffff8000801277e0` | `0000000000000400` | **= 崩溃时 x23 残留**，真值路径可平静读出 |
| `rd -64 ffffdf9b728096c0` | `page excluded` | 模板页已解映射/未入 dump（init 域佐证） |

**P4 软件根因排除**：反汇编序列软件自洽（x20 是唯一自由变量且其装载位于塌缩链上游）；数组真值完好排除"内存被写坏"；x25=8 且 off[8] 非零排除"迭代号越界读 BSS 零区"；KASLR 不变式成立排除地址错位。

**P5 定论**：见 §8。

## 7. 逻辑链条（寄存器代数闭合与反事实）【逻辑链条】

`algebra.py` → `algebra_out.txt`，**13/13 PASS**：

```
x1 == &runqueues（crash sym 实锤）                     PASS
x27 == x1 + x20 (mod 2^64)        0xffffdf9b728096c0   PASS
FAR == x27 + 0x120                0xffffdf9b728097e0   PASS
x9 - x1 == 0xfffffffffe5d1798     （12案指纹）          PASS
x21 - x1 == 0x3f65f0 / x24 - x21 == 0x5350              PASS
x9 低16位 == ae58 / x23 == 0x400                        PASS
off[8]-off[0] == 8*0x22000 / off[179]-off[0] == 179*0x22000  PASS（数组等差完好）
x27_true == crash p runqueues [8]（逐位）               PASS
```

反事实推演：若 x20 收到真值 `ffffa0650d91e000`，则 x27 = `ffff8000801276c0`（= crash 实测 cpu8 rq 实例，逐位相等），访问 `+0x120` 得 `0x400`（实测内存值），一切平静。实收 x20=0 使 x27 塌缩到 init 模板，`+0x120` 落入 free_initmem 已解映射页 → PMD=0 → L2 fault → panic。**内存非零 + 寄存器零 = 读出路径 SDC**，与第 23:37 案（get_pfnblock_flags_mask 读出 SDC）同判。

x23=0x400 的双重身份是本案独有亮点：既是崩溃时寄存器残留（上一次迭代的 load_avg 读出），又是反事实地址的实测内存值——上一次装载正常、本次塌缩，同一指令序列内的时序对照。

## 8. 故障根因【故障根因】

**【实锤】零塌缩族第 6 案**：`ldr x20,[x0,w25,sxtw#3]` 在 CPU 179 上把非零内存 `__per_cpu_offset[8]`（=`ffffa0650d91e000`）装载为 0。内存真值完好（三点等差验证）+ 装载结果全零 = 核私有读出通路 SDC。

**【强推】微架构定位**：CPU 179（MPIDR 0x7a0300，Kunpeng-920 Taishan-v110，node 7）核私有 load 返回通路（fill-buffer 合并/返回 mux 一族）间歇性全零交付；无 ECC 覆盖（核私有结构）、无 RAS 记录（EC=0x25 DABT）。零塌缩与撕裂移位（第 19 案，同日 15:16）是同一选路失控的两种交付形态。

## 9. 启示【启示】

1. **42.24h 静默纪录的监控含义**：被动遥测的"末次事件时间"对致命时刻零预测力（census §2.5 的 4 个数量级方差再添一个极端样本）。"过去 42 小时无事件"曾被误读为安全窗口——本案证明静默期长度本身无信息量；唯一可靠的仍是"是否出现过任意一次 CPU179 spurious fault"这个二值标记（本案 9.3h 时已给出）。
2. **x23=0x400 时序对照**：同一指令序列内"上次装载真值可见、本次装载塌缩"，把 SDC 的"间歇性"从跨案统计压缩到单次执行序列内部，进一步排除"数据本身长期损坏"的任何解释。
3. **L2 变体复现**：零塌缩+L2 组合第二次出现（继第 11 次），census §2.7 的"KASLR 相位决定 FSC 层级"模型再获一枚独立样本。
4. 处置建议（第 18 次重申）：立即 offline CPU179 并持久化；整机 RMA。截至本案，19 案 18 案崩在 CPU179（1 案 CPU168 邻核），CPU179 仍带病在线。

## 附录：命令索引

```
# dmesg 法证
grep -oE "WARNING: CPU: [0-9]+" vmcore-dmesg.txt | sort | uniq -c
grep "Ignoring spurious" vmcore-dmesg.txt
# crash（taskset -c 0-31，全部输出存本目录 crash_*.log）
crash <vmlinux> ../127.0.0.1-2026-09-07-13:51:42/vmcore
  bt / sys / vtop ffffdf9b728097e0
  dis -l find_busiest_group+0x100 30
  sym ffffdf9b728096c0 / p &__per_cpu_offset / p runqueues
  rd -64 __per_cpu_offset / p __per_cpu_offset[8] / p __per_cpu_offset[179]
  vtop ffff8000801276c0 / rd -64 ffff8000801277e0
# 代数
python3 algebra.py  # 13/13 PASS
```
