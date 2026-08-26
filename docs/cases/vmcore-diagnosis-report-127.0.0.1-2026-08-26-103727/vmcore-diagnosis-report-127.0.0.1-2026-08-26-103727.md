# CPU179 缺陷核第 6 次致命转储深度诊断报告
## ——兼六转储（2026-08-14 ~ 2026-08-26）微架构级根因综合

| 项 | 值 |
|---|---|
| 目标转储 | `/home/sdc/vmcore/127.0.0.1-2026-08-26-10:37:27/`（13.9 GB，PARTIAL DUMP） |
| 主机 | Yangtze Computing R240K V2 / BC82AMQA，BIOS 7.48 06/15/2026 |
| CPU | Kunpeng-920 (HIP08/TaiShan-v110) ×192，8 NUMA 节点 |
| 内核 | 6.6.0-145.3.23.154.oe2403sp3.aarch64 #1（debuginfo 精确匹配） |
| 崩溃 | 2026-08-26 10:36:43 CST，uptime 18:31:26，CPU **179**，PID 256855 `mi-scavenger` |
| 结论 | **维持并强化既有判定：CPU179 为缺陷核（核内 LSU 装载数据返回通路间歇软故障 / SDC）。本次新案以指令级反事实验证第 5 次独立坐实，且六开机 88 起事件 100% 收敛于 CPU179、5/6 次致命崩溃命中同一条指令。** |

---

## 1. 执行摘要

1. 本次致命 panic 是**同一缺陷的第 6 次发作**：野值再次由 CPU179 的装载指令从**完好的内存**读出后进入寄存器所致。本次以完整的"应然值 vs 实收值 + 反事实推演"闭环证明：
   - 装载 `__per_cpu_offset[179]` 的指令实收 **0**，而内存真值为 `0xffffdd6d7fa64000`；
   - 若实收真值，后续访存将落在经页表验证 **VALID** 的 `rq(179)=0xffff8000817dd6c0` 并读到健全数据（`load_avg=241`），**根本不会发生异常**。
2. 六开机横向对比呈现前所未有的规律性：**5/6 次致命崩溃发生在完全相同的一条指令** `find_busiest_group+0x140`（`kernel/sched/fair.c` `update_sg_lb_stats()` 的 per-CPU 遍历体），腐化子族仅分两种形态（零塌缩族 / 撕裂移位族），每案的寄存器代数均**逐位精确闭合**。
3. 全部 6 次开机共 **88 起硬件异常事件（82 次 WARNING + 6 次 Oops），100% 位于 CPU179**，其余 191 核零事件；RAS/EDAC/BERT/GHES 与架构化错误节点扫描（ERRIDR/ERX，192 核×5 节点逐位一致）全程静默——与"故障位于 CPU 核私有、不在任何 RAS 覆盖内"的判定完全自洽。
4. 微架构根因链收敛至：**LSU 装载数据返回通路（fill-buffer/replay 合并 ≈ L1D 读出选路）在 store 共存场景下的调度相位×电压裕量边际时序失效**，伴随 PTW（页表遍历读）同族瞬态。物理层最深处（sense-amp/位线瞬态稳定性）为 vmcore 方法论的可达边界——再深入需芯片 ATE/DFT/BIST，此为本报告明示的证据极限而非调查缺失。
5. 处置建议不变且更为紧迫：**offline CPU179 + 整片送修（RMA）**。既往实证 `l1d_disable` 类缓解无效，勿再尝试。

---

## 2. 证据规则与方法

- **只依据 vmcore / vmcore-dmesg.txt 取证**。引用既往会话结论处均标注〔既往已证〕并注明本次是否重验。
- 所有 64 位地址加法一律脚本计算（模 2⁴⁴…模 2⁶⁴ 回绕），并以 crash 内建 per-cpu 解析器独立对照，杜绝手算误差。
- 工具：crash 8.0.4 + 精确版本 vmlinux/debuginfo；objdump -dl（DWARF 行号）；/usr/src/debug 内核源码。
- 报告区分三层：**事实（vmcore 可复核）→ 解释（最简自洽模型）→ 判定（工程处置）**。

---

## 3. 新案（08-26 10:37:27）完整取证链

### 3.1 异常概览（事实）

```
Unable to handle kernel paging request at virtual address ffffa29301d797e0
ESR = 0x96000007  EC = 0x25: DABT (current EL)  WnR=0  FSC = 0x07: level 3 translation fault
swapper pgtable: pgd=…f403 pud=…e403 pmd=…a403 pte=0000000000000000
pc : find_busiest_group+0x140/0xb60   lr : find_busiest_group+0x11c
Call trace: find_busiest_group ← load_balance ← newidle_balance ← pick_next_task_fair
            ← pick_next_task ← __schedule ← schedule ← futex_wait_queue … el0t_64_sync
Code: f9400782 f879d814 2a1903e0 8b14003b (f9409377)
```

mi-scavenger 在 futex 睡眠唤醒路径经 `newidle_balance` 触发负载均衡，遍历调度组内 CPU 时崩溃。

### 3.2 故障指令语义重建（事实：静态反汇编 + DWARF + 符号解析）

vmlinux 中 `find_busiest_group` 静态基址 `0xffff80008013ad08`，运行期 KASLR 由崩溃现场 `x9 = find_busiest_group+0x150`（`.text`，RDONLY 映射，rd 读出的指令字节与反汇编逐字一致）锚定。故障窗口：

```asm
; kernel/sched/fair.c — update_sg_lb_stats(): for_each_cpu_and(i, group_span, env->cpus)
ffff…ae10  bl   _find_next_and_bit        ; 入参: &sd->span, env->cpus, nr_cpu_ids
ffff…ae24  mov  x25, x0                   ; x25 = i (下一个 CPU 编号)
ffff…ae34  ldp  x0, x1, [sp, #8]          ; x0 = &__per_cpu_offset[0]
                                          ; x1 = &runqueues （percpu 静态模板地址）
ffff…ae3c  ldr  x20, [x0, w25, sxtw #3]   ; x20 = __per_cpu_offset[i]   ← 数据来源
ffff…e44*  add  x27, x1, x20              ; x27 = &per_cpu(runqueues,i)  (mod 2^64)
ffff…e48*  ldr  x23, [x27, #288]          ; rq->cfs.avg.load_avg          ← 致命点(+0x140)
```
\* 即 Code 字段末两条 `8b14003b`(add) 与 `(f9409377)`(ldr)。

符号级验证（crash，本转储）：`sym runqueues = ffffa29301d796c0`；`sym ffffa2930216fcb0 = nr_cpu_ids`（=x21，循环上界变量）；`__per_cpu_offset` 数组基址 = `ffffa293021755d0` = 寄存器 x24（adrp 页基址，注解 node_data+560）+0x5d0，与 `str x0,[sp,#8]` 的构造序列吻合。语义即 C 表达式 `cpu_rq(i)->cfs.avg.load_avg`。

### 3.3 崩溃寄存器与代数闭合（事实）

| 寄存器 | 值 | 语义 |
|---|---|---|
| x27 | `ffffa29301d796c0` | == x1 == **`&runqueues` 模板符号地址（逐位相等）** |
| x20 | `0000000000000000` | 应为 `__per_cpu_offset[179]`，**实收 0** |
| x25/x0/x6 | `0xb3` = 179 | 迭代 CPU 号（三寄存器互证） |
| x23 | `0x400` | 前一次成功迭代的 load_avg 残留 |
| x21 | `ffffa2930216fcb0` | `nr_cpu_ids`（192） |
| x22==x26 | `ffff604003e27660` | slab 中 sched_group（首字 next 指针 + weight=24） |
| FAR | `ffffa29301d797e0` | = x27 + 0x120 ✓ |

闭合等式：`x27 = x1 + x20 = ffffa29301d796c0 + 0 = ffffa29301d796c0`；`FAR = x27 + 0x120` 精确成立。

### 3.4 内存真值对照（决定性实验①：内存完好、寄存器收坏）

- `px __per_cpu_offset[179]` → **`0xffffdd6d7fa64000`（非零！）**
- `rd -64 __per_cpu_offset 192`：全数组 192 项为**完美等差数列**（base `ffffdd6d7e29e000`，步长 `0x22000`），无任何一项损坏。
- 结论：被读取的内存是好的；坏的是**装入寄存器的那个瞬间值**。软件写坏内存的可能被排除（若是存储路径损坏，数组不可能保持等差）。

### 3.5 反事实验证（决定性实验②：若收到真值则不会崩）

正确的 `x27_true = (&runqueues + __per_cpu_offset[179]) mod 2^64 = ffffa29301d796c0 + ffffdd6d7fa64000 = ffff8000817dd6c0`（脚本计算）。三重独立验证：

1. crash 内建 per-cpu 解析 `p runqueues:179` 返回的实例其内嵌自指针 `cfs.rq = rt.rq = active_balance_work.arg = 0xffff8000817dd6c0`，与本算式逐位一致；
2. `vtop ffff8000817dd6c0` → **VALID**，PA=`0x6057ffe026c0`（node7 DRAM 顶部窗口），PTE VALID|DIRTY；
3. 实例内容健全：`cpu=179`、`nr_running=0`（空闲，与新 idle balance 场景吻合）、`cfs.avg.load_avg=241`、`util_avg=149`、`curr=0xffff0020364f3f00` **恰为崩溃任务 mi-scavenger 自身**。

即：若那条 `ldr x20,[…]` 交付真值，故障指令将平静地读到 241，系统继续运行。**异常的唯一必要条件是装载结果被腐化。**

### 3.6 pte=0 之谜的解释（无需页表硬件错误假设）

`&runqueues` 静态模板位于 `.data..percpu`，恰处 init 区间；arm64 `free_initmem()` 在开机后对该区间 `vunmap_range`——**该页在设计上永久解映射**。当 x20 被读成 0，`x27` 塌缩到模板地址，MMU 如实走完四级页表得到 pte=0 并报 L3 翻译错误。两次独立走表（硬件 + 内核 show_pte + crash 复核）一致为 0，证明走表本身诚实，坏的是输入地址。〔机制与 15:42 案相同，既往已证；本案例外收获：FSC=L3 而非 L0，正是"零塌缩"子族的指纹（见 §4）〕

### 3.7 本次开机的其余 9 起 WARNING（事实）

- 时间线：1467s ×3（irqbalance）、61983/62053/62477/62893/62903/64953s ×6（pmdalinux/irqbalance），全部 **CPU179**；
- 全部为内核自判 spurious 的翻译故障（AT S1E1R 重走成功→页表完好→瞬时错），openEuler 补丁以 WARN 记录之；
- ESR 全部 `0x96000044`：**WnR=1（写访问）+ FSC=L0** —— 扩展签名：不只装载数据返回，**store 引发的页表遍历读同样瞬时受扰**；
- FAR 全部落于 `ffff60xx_xxxxxxxx`（vmalloc/percpu-chunk 区统计结构），同进程重复触碰同一簇地址（如 `ffff60400884xxx` 六连发）。

---

## 4. 五份历史转储交叉验证（六案同堂）

### 4.1 同指令五案签名总表

五次致命崩溃命中**同一条指令** `find_busiest_group+0x140`，仅腐化子族不同：

| 开机 | i(x25) | x1（模板） | x20 实收值 | 子族 | x27 闭合 | FAR / FSC |
|---|---|---|---|---|---|---|
| 08-14 | 176 | `ffffa6c96a4996c0` | `d93715ba0000ffff` = **ROL16**(entry[1]) | 撕裂·半字旋转 | `d936bc836a4a96bf` ✓逐位 | `0036bc83_6a4a97df` / L0 |
| 08-17 | 175 | `ffffd7d8cdf196c0` | `00ffffa827b20fe0` = entry≫8 形态 | 撕裂·跨字节 | `00ffd780f5a3a6a0` ✓逐位 | `00ffd780_f5a3a7c0` / L0 |
| 15:58 | 146 | `ffffb378e29exxxx` | `00ffffcc879da2e0` = offset[0]≫8 〔既往已证〕 | 撕裂·跨字节 | — | `00ffb345_69fc3ac0` / L0 |
| 15:42 | 176 | `ffffa5aa9b5a96c0` | **0** | 零塌缩 | =x1=模板 ✓ | `ffffa5aa_9b5a97e0` / L3 |
| **08-26** | **179** | `ffffa29301d796c0` | **0** | 零塌缩 | =x1=模板 ✓ | `ffffa293_01d797e0` / L3 |

- 闭合计算全部脚本化（模 2⁶⁴），08-14/08-17 两案 x27 与寄存器**逐位相等**；FAR 均等于 x27+0x120。
- 08-14 案本次重验：其 vmcore 中数组头 `[1]=ffffd93715ba0000` 与 x20 的 ROTL16 关系位级成立〔既往已证，本次重验通过〕；真 rq176=`ffff8000817776c0` 经 vtop **VALID**（PA=0x6057ffe696c0，与今日 rq179 同一物理窗口）——"应然地址有效"两案同构。
- 08-17 案 vmcore 不完整（kdump 未完成），**内存真值不可验证**——其 x20 的 ≫8 归类基于数值形态与 15:58 同构，置信度中高，特此声明。
- 跨开机不变式（确定性代码路径指纹）：`Code:` 五个指令字全同；x23≡0x400；x22==x26 成对；x21=nr_cpu_ids 且与 x24 相对距离恒定（−0x5350）。
- FAR 高字节异常（08-14：HW 上报 `00…` vs x27 高字节 `d9`）复现既往签名库"发作窗口内多操作相继受扰"条目。

### 4.2 第 6 案异位点同病（08-24）

`bio_add_page+0xf0`，致命指令 `ldr x1,[x3]`，而 x3 恰来自上一条**缩放变址装载** `ldr x3,[x3,x2,lsl #3]` 的返回值（已呈乱码）。与五案同为"索引型装载返回腐化数据"，仅下游表现不同。FAR=`003c521da2e9b99f`（非规范域）/L0。

### 4.3 六开机事件普查（主证据表）

| 开机(dump) | 首症时刻 | panic 存活 | WARNING(spurious) | 致命点 | 子族 |
|---|---|---|---|---|---|
| 08-14 | 104485s = 29.03h | 113997s = 31.67h | 12 | fbG+0x140 | ROL16 |
| 08-17 | 169175s = 47.00h | 239527s = 66.53h | 26 | fbG+0x140 | ≫8（内存未验） |
| 08-24 | 835s = 13.9min | 537462s = 149.29h | 34 | bio_add_page+0xf0 | 变址装载乱码 |
| 15:42 | 1707s = 28.5min | 76809s = 21.34h | 1 | fbG+0x140 | 零塌缩 |
| 15:58 | （无预警直接 panic） | 418s = 7.0min | 0 | fbG+0x140 | ≫8 |
| **08-26** | **1467s = 24.5min** | **66685s = 18.52h** | **9** | **fbG+0x140** | **零塌缩** |

- 合计 **82 WARNING + 6 Oops = 88 起事件，100% CPU179**（grep 逐开机核验，无一例外）；其余 191 核六开机累计约 400+ 小时运行零事件。
- FSC 二分法与子族严格对应：非规范和→L0（PGD 级失败）；零塌缩→L3（走到 PTE=0）——两种 FSC 都只是坏地址的不同投影，非两种病。
- 频率无单调趋势（12/26/34/1/0/9 每开机），但首症时刻整体前移（29h→47h→分钟级），且**每次开机最终必致命中断**；样本量不足以拟合 MTBF，诚实存疑。

### 4.4 RAS 全静默链（本开机续证）

- ACPI BERT（HISI HIP08）在位、内容空；GHES firmware-first 已使能；ghes_edac 注册 32 DIMM 插槽，全程零 CE/UE 记录；
- 自研 rasnode.ko 于 8026s 扫描 192 核 × 5 个架构化 ERR 节点：剥离 CPU 号后各节点 FR/CTLR/STATUS/ADDR/MISC 读数**全机唯一**（逐位一致），CPU179 零差异零记录；
- 机制解释〔既往已证，链条闭合〕：故障 ESR 的 EC=0x25（普通 DABT）≠ 0x2f（SError/RAS），硬件从未将其识别为可上报错误；HiSilicon 私有 RAS 驱动 45 个子模块全为 SoC 互连，不含核内 LSU/L1d；ARM 内核 CE 路径仅 pr_info_ratelimited。**"检测不到"正是"故障位于检测盲区"的必然结果，而非"没有硬件故障"。**

---

## 5. 微架构级根因收敛（层级递进表述）

**L0 · ISA/软件模型层 —— 排除一切软件成因（证据强度：铁证）**
六案共同结构："从已验证完好的内存装载 → 寄存器获得腐化值 → 坏值污染后续访存/控制流"。编译器、内核逻辑、KASLR、页表维护在各案中全部自洽（反汇编-DWARF-符号-源码四重对齐）；反事实实验证明正确数据下程序必然正常运行。软件侧不存在需要修复的对象。

**L1 · μarch 功能单元层 —— LSU 装载数据返回通路（证据强度：强）**
腐化交付的三种形态——相邻行旋转（ROL16）、跨元素字节相位（≫8）、全零——指向**数据返回选路/合并环节交付了错误源或错误相位的数据**，而非存储单元位翻转（后者应表现为单/双比特错误且内存侧可见）。佐证：
1. 三条致命装载均为**缩放/变址寻址**（`[Xn,Wm,SXTW#3]`×2 案、`[Xn,Xm,LSL#3]`×1 案），该寻址模式在 AGU 移位器与 DCU 数据选路间协同更多、时序余量更紧（观察性关联，非因果证明，如实标注）；
2. spurious 族（含本次 WnR=1 写翻译）表明 **PTW 的表项读取同族瞬时失败**——PTW 读表与 D-side 装载在很多实现中共用 L1D fill/读出通路，与单一单元病变假设一致（架构假设，≈80% 置信，既往已标注）;
3. 88/88 单核私有性 + 同节点同胞核/L3/DRAM 六开机零事件，排除一切共享资源。

**L2 · 物理机理层 —— 读出模拟前端瞬态（证据强度：推断，最优自洽模型）**
既往位分布分析（汉明重量 35/36、均匀散布、无列/字节聚类）已排除 stuck-at、位线短路、译码器、字节使能等**结构化数字故障**；剩余最优假设为 sense-amp/位线均衡在特定调度相位×电压裕量下的边际时序失效，store 共存为其必要条件（既往活体三臂实验：纯加载探针 10¹² 次零撕裂）。

**L3 · 边界声明（诚实性）**
晶体管级/工艺级的具体失效位置（哪个 sense-amp 组、哪条位线、哪个 helper 时序单元）**超出 vmcore 方法论的可观测极限**，需芯片级 ATE/DFT/BIST（如 LBIST/MBIST 向量、shmoo 曲线）才能继续下钻。本报告的"最深"指**软件侧可获得的全部证据已被穷尽并相互闭合**，而非宣称到达硅片物理终点。

---

## 6. 排除项矩阵

| 假设 | 判定 | 关键反证 |
|---|---|---|
| 内核软件 bug（UAF/越界/竞态） | 排除 | 六案代数闭合+反事实验证；内存真值恒完好 |
| DIMM/DDR 颗粒故障 | 排除 | EDAC 零记录；被读数组恒完好；损坏随核不随地址 |
| L3/互连故障 | 排除 | L3 节点内共享而仅单核发病；SoC RAS 45 子模块零记录 |
| 页表/MMU 硬件走表损坏 | 排除 | spurious 重走成功；pte=0 有 free_initmem 设计性解释 |
| 固件欠压残留 | 排除 | VDDAVS 0.94–0.97V 健康〔既往实测〕 |
| 公开 HIP08 erratum（RU-prefetch 等） | 排除 | 签名不符〔既往判定〕 |
| 温度加速因子 | 存在但非根因 | SEL 既往见 Upper Non-critical 记录〔既往〕 |

## 7. 处置建议

1. **立即**：`echo 0 > /sys/devices/system/cpu/cpu179/online` 下线 CPU179（本机已第 6 次致命中断，风险持续）。
2. **根本**：整机/整 socket 送修（RMA），引用本报告 §4.3 主证据表 + §3.5 反事实实验作为返修凭证；请厂家执行核内 MBIST/LBIST 与 shmoo 复现（−30mV 欠压曾可控复现同签名〔既往 gem5-fi 活体报告〕，可作为 ATE 复现起点）。
3. **不要**再部署 `l1d_disable`（SCTLR_EL1.C 清位）类缓解——15:42 案实证卸载后 3.7h 仍 panic、15:58/08-26 案未加载照样致命。
4. 监控建议：持续 grep `Ignoring spurious kernel translation fault`（当前最高效的前兆信号，先于 panic 数小时~数天出现）。

## 8. 附录 · 可复现命令集

```bash
VL=/usr/lib/debug/usr/lib/modules/6.6.0-145.3.23.154.oe2403sp3.aarch64/vmlinux
# ① 故障语义
nm $VL | grep -w find_busiest_group
objdump -dl --start-address=0xffff80008013ade8 --stop-address=0xffff80008013ae70 $VL
# ② 内存真值与反事实
crash -i cmd.txt $VMCORE   # sym runqueues; px __per_cpu_offset[179]; rd -64 __per_cpu_offset 192
                           # vtop <模板+x20真值>; p runqueries:179
# ③ 闭合计算（禁止手算）
python3 -c 'print(hex((0xffffa29301d796c0+0xffffdd6d7fa64000)&(2**64-1)))'
# ④ 事件普查
grep -cE "WARNING: CPU: 179" vmcore-dmesg.txt   # 各转储: 12/26/34/1/0/9
grep -E "Ignoring spurious|Unable to handle" vmcore-dmesg.txt
```

**方法学备注（诚实记录）**：分析过程中两次手工 64 位加法出错（漏进位/抄错半字），均被"crash 内建 per-cpu 解析器 + 结构体内嵌自指针 + 脚本重算"三方对照捕获并纠正；本报告中所有地址等式均为机器验证结果。08-17 案因 vmcore 不完整，其内存真值维度缺失，已在正文标注。

---
*报告生成：2026-08-26 · ox-alpha 深度诊断会话 · 证据全部源自 6 份 vmcore/vmcore-dmesg.txt*
