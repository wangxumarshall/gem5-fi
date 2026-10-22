# R4-8-FSMC-B：35 项 FS-MULTICORE 收口——FS 传播链 + 注入 pilot + 待构建清单

- 分支：`r4-8-fsmc-b`（worktree `.claude/worktrees/r4-8-fsmcb`）
- base：`lsu-mdspec-20261019` @ `d63a5dd8`（**已含 R4-8/R4-9 的 A、C 两轮集成**）
- 二进制（只读复用，**未做任何 scons 构建**）：
  `.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt`
  sha256 前缀 `54c2c78ce4c84bb2`（**注意**：repo-root `build/ARM/gem5.opt` 是另一支
  `10590f6295bc4dec`，**不含 CHAOSPropagation 的新参数、也不含 chaosBarrierHook**——
  见 §7.1，这是个真实的踩坑点）
- 资产：`gem5-fs/{vmlinux,ubuntu.img,boot.arm64}`；2 核 CHI 检查点
  `/tmp/r4-8-fsmc/mc_boot/cpt.243414599076`（R4-8-FSMC 产物，实测仍在）
- 证据目录：`/tmp/r4-8-fsmcb/{run1,run2}`（不入 git）
- 本报告是 **worktree 本地证据**（未改 MDSPEC 共享文档）

## 0. 结论摘要（先说结论）

上一轮（R4-9-FSMC-A）把 A 组 10 格劈成两半：4 格 `CARRIER_ROUTED_PENDING_RUN`
（载体就绪、本格 campaign 样本未取）、6 格 `BLOCKED_TRIGGER_TIER_UNIMPL`。
本轮**净新增**三件事，全部有真机原始输出：

| # | 净新增 | 结果 |
|---|---|---|
| 1 | **FS 多核传播链挂载**（之前 FS 侧根本没有 `CHAOSPropagation` 实例 ⇒ 注入器发的链事件全部 no-op） | **通过**：两个 run 都产出 `prop_evt.txt.gz` / `prop_trace.csv.gz`；干净臂为**空**（仅表头），注入臂 **616 条事件 / 586 个链节点** |
| 2 | **A 组真正的"注入 vs 无故障"对照**（R4-9-FSMC-A §2.6 明确未做） | **通过**：两臂 oracle **逐字节相同**（`violations=0`，`FINAL=6ca52252681d0c34`）⇒ **O01-F0 在该载体上是 Masked**（LDXR/STXR 重试环吸收了被腐蚀的 reservation），这与 `CHAOSExMon.hh` 对 O01 的规格描述一致 |
| 3 | 多核上的**完整 L0→L5 传播链**（inj → addr_form → exmon_monitor → resp/lq_complete/taint_reg → exmon_rmw/exmon_stxr → consumer → chain_end → errant_commit） | **通过**：链的 `fault_id=1` 全程可追溯，`run_id/sample_run_id` 正确写入 |

**没有任何一格被解锁**（A 组 F0/F5 仍缺"本格 campaign 样本"，F2/F6 仍缺档位语义）。
本轮的价值是：把"多核 FS 上注入到底能不能观测"从**未证**变成**已证（含链证据）**，
并把剩下两个 C++ 缺口写成可施工的清单（§7）。

## 1. 起点事实（复核，不是转述）

| 组 | 数量 | baseline `d63a5dd8` 的既有裁决 |
|---|---|---|
| A（O01/O02/O03 × W7） | 10 | 4 格 `CARRIER_ROUTED_PENDING_RUN`（F0/F5）+ 6 格 `BLOCKED_TRIGGER_TIER_UNIMPL`（F2/F6） |
| B（C08 × W7） | 4 | `BLOCKED_INJECTOR_HOST`（构造性互斥） |
| C（O04/O05/O06/O07/O09 × W7） | 15 | `BLOCKED_MODEL_UNIMPL`（钩子已落地但 **compile-unverified / 未 pilot**） |
| D（O09/P09 × W13） | 6 | `BLOCKED_WORKLOAD_IDENTITY`（PARSEC 本仓库不可得 + 模型/宿主缺口叠加） |

机读裁决表：`tools/lsu_fsmc_verdict.py`（35 行）；断言：`tests/test_lsu_fsmc_verdict.py`。
**本轮不改这张表**——见 §4 的"为什么一格都不解锁"。

## 2. Task 1：FS 多核传播链挂载（Python-only，已真机验证）

`configs/fs/lsu_multicore_fs.py` 新增 `--chaos_propagation` / `--prop_trace_file` /
`--prop_run_id` / `--prop_sample_run_id`，挂 `CHAOSPropagation(cpu=core0.core, ...)`；
镜像 1 核 FS 先例（`configs/se/arm_chaos_fs.py:551-575`）。

**为什么这是必需的**：`CHAOSExMon.cc` 早已会发 O 系链事件
（`exmon_monitor` L1 @ :255、`exmon_rmw` L2 @ :97、`exmon_stxr` L3 @ :113），
但这些调用都走 `CHAOSPropagation::instance()` —— FS 配置里**没有**这个 SimObject ⇒
`instance()` 为 `nullptr` ⇒ 事件静默丢弃（"oracle 有、链没有"）。补齐后：

```
$ grep -E "CHAOSPropagation attached|num_cores=" /tmp/r4-8-fsmcb/run1.stdout
[lsu_multicore_fs] num_cores=2 coherence=chi cpu=O3 l1d=16KiB/4 l2=256KiB/8
[lsu_multicore_fs] CHAOSPropagation attached on core 0 (trace=prop_trace.csv.gz, run_id='O01-pilot', sample_run_id='s1')
```

**O3-only 响亮拒绝**（真机验证）：
```
$ <gem5> ... --cpu=Atomic --chaos_propagation
[lsu_multicore_fs] FATAL: --chaos_propagation is O3-only (got --cpu Atomic). The FS roadmap is Atomic boot -> O3 restore; set --cpu O3.
```

> **平台坑（诚实记录）**：在本 build 上 `raise SystemExit("<字符串>")` **不会**打印该字符串——
> 它会变成 tick 0 的
> `pybind11::cast_error: Unable to cast Python instance of type <class 'str'> to C++ type 'int'` abort。
> 这不是本块引入的：配置里**既有**的 `--num-cores < 1` 守卫（我未改动）用同样的
> `raise SystemExit`，在 `--num-cores=0` 下产生**逐字相同**的 abort（实测）。因此本块的
> 拒绝路径改为"**先 print 再 `raise SystemExit(1)`**"，理由是让拒绝可读（上一条输出即证据）。

## 3. Task 2：A 组双核 O3+CHI 注入 pilot（真机原本）

命令模板（`flock /tmp/lsu_gem5_slotN.lock`；outdir 只写 `/tmp/r4-8-fsmcb/`）：

```
<CHAOS-binary> --outdir=/tmp/r4-8-fsmcb/run<N> configs/fs/lsu_multicore_fs.py \
    --kernel=gem5-fs/vmlinux --disk=gem5-fs/ubuntu.img --bootloader=gem5-fs/boot.arm64 \
    --num-cores=2 --coherence=chi --cpu=O3 \
    --restore-checkpoint=/tmp/r4-8-fsmc/mc_boot/cpt.243414599076 \
    --chaos_propagation --prop_run_id <id> --prop_sample_run_id s1 \
    [--chaos_exmon --exmon_mode o01_monitor_addr_bitflip --exmon_max_faults 1] \
    --readfile=configs/fs/litmus_free_pilot.rcS
```

### 3.1 为什么需要一个"小轮次 pilot 载体"（不是省事）

canonical `litmus_free.rcS`（SB 64 / ATOM 8×2）是 campaign 与 `FSMC_GOLDEN_FINAL`
钉死的身份，**不能漂**。但它的 ATOMIC 相位在 2 核 Ruby/O3 恢复态下**跑不完**
（R4-9-FSMC-A §2.4/§2.5 已量化；本轮再次复现），于是干净臂拿不到 ATOMIC oracle、
也就没有"注入 vs 无故障"的对照。本轮新增 `litmus_free_pilot`：**同一份源码**、
只改轮次（`-DLITMUS_FREE_SB_ROUNDS=8 -DLITMUS_FREE_ATOM_ROUNDS=2
-DLITMUS_FREE_ATOM_INCR=1`），产出**独立的** `configs/fs/litmus_free_pilot.rcS`。
它是**注入观测载体**，不是 canonical 载体的替代。

宿主原生自检（真 aarch64、真 SMP、两次运行）：
```
LITMUS free sb hist r0r1: 00=0 01=7 10=1 11=0 forbidden(00)=0 bad=0 child_status=0
LITMUS free atomic ctr_expect=2 violations=0 tries cpu0=6 cpu1=2 min=1 child_status=0
FINAL=6ca52252681d0c34        (第二次运行 FINAL 相同)
```

### 3.2 Run 1（干净臂，`--chaos_propagation`，无注入）【通过】

```
[boot_ckpt.rcS] restore pass: dispatching payload
[litmus_free.rcS] nproc=2 / cpuinfo processors=2
[litmus_free.rcS] sha256=03db6af0038af3ea9bf8d9da06922a7d439a81341f167bb28ee496e0c66f9d64 size=8032
LITMUS free begin nproc=2
LITMUS free sb nproc=2 rounds=8
LITMUS free sb hist r0r1: 00=0 01=4 10=4 11=0 forbidden(00)=0 bad=0 child_status=0
LITMUS free mp SKIPPED (LITMUS_FREE_WITH_MP=0)
LITMUS free atomic nproc=2 rounds=2 incr_per_core=1
LITMUS free atomic ctr_expect=2 violations=0 tries cpu0=7 cpu1=2 min=1 child_status=0
FINAL=6ca52252681d0c34
LITMUS free end
[litmus_free.rcS] exit=0
[litmus_free.rcS] payload finished
```
`FINAL` 与**宿主原生 golden 逐字节相同**；SB 直方图两侧都出现（01=4/10=4）⇒ 2 核
CHI 上核心间 store 双向可见（真一致性），禁出现结果 = 0。传播流为**空**
（`prop_evt.txt.gz` 只有表头）⇒ 链是注入引起的，不是平台的常驻噪声。

### 3.3 Run 2（注入臂，`--chaos_exmon --exmon_mode o01_monitor_addr_bitflip --exmon_max_faults 1`）【通过】

**注入确实发生在 guest 内**：
```
$ cat /tmp/r4-8-fsmcb/run2/exmon_injections.log
Tick: 255378874491, Site: isa_handleLockedRead, mode=o01_monitor_addr_bitflip, addr=0x80c92648 -> monitor addr=0x84c92648, flag=1, faults_injected: 1
```

**同一臂的 oracle（与干净臂逐字相同）**：
```
LITMUS free sb hist r0r1: 00=0 01=4 10=4 11=0 forbidden(00)=0 bad=0 child_status=0
LITMUS free atomic ctr_expect=2 violations=0 tries cpu0=7 cpu1=2 min=1 child_status=0
FINAL=6ca52252681d0c34
[litmus_free.rcS] exit=0
```
⇒ **两臂 FINAL 与三条禁出现计数完全一致**。按 ITC'23 口径，这是 **Masked**（故障在
SUT 内部被吸收，程序可见结果不变），**不是** "注入没打到点子上"——证据是下面的链：
链上有 `taint_reg(phys_reg=179, class=int)` 与 `errant_commit(trigger=faulting_load_commit)`，
说明被腐蚀的 reservation **确实传播到了寄存器与提交点**，只是 STXR 失败重试后最终值正确。

**传播链（L0→L5，`prop_evt.txt.gz` 616 行 / `prop_trace.csv.gz` 586 节点）**：
```
kind=inj           tick=255378874491  va=80c92648 after=84c92648   (L0 注入)
kind=addr_form     tick=255378874491  before=80c92648 after=84c92648 (L0→L1 地址成形)
kind=exmon_monitor tick=255378874491  request_id=13652940 field=o01_monitor_addr_bitflip state_before=1 state_after=1 (L1)
kind=resp          tick=255378875158  family=cache data_fnv=b5d445774c80560f      (cache 返回)
kind=lq_complete / kind=taint_reg(phys_reg=179,class=int) / kind=errant_commit(trigger=faulting_load_commit)
kind=exmon_rmw  ×104  (L2，reservation compare；每一次 STXR 尝试一条)
kind=exmon_stxr ×104  (L3，STXR 消费；带 1-based 尝试号)
kind=consumer   ×529
kind=chain_end  tick=268114607010 event_id=809
```
节点种类统计：`inj=1 addr_form=1 exmon_monitor=1 resp=24 lq_complete=15 taint_reg=29
exmon_rmw=104 exmon_stxr=104 consumer=529 chain_end=1 errant_commit=1`。

> **诚实边界 1**：`exmon_rmw/exmon_stxr` 各 104 条，**大于** ATOMIC oracle 里的
> `tries(cpu0)=7`。原因是 `CHAOSExMon` 的 `active_monitor_ptag` 在注入后**不会清零**，
> 于是此后**每一次** STXR 都把消费事件挂到最后一次 monitor 故障的 `fault_id` 上
> （`CHAOSExMon.cc:96` 的守卫是 `active_monitor_ptag != 0`）。这是 tracer 记账的
> **保真度缺口**（不是本轮的注入缺陷），记录在此，供下一轮决定是否"消费后清空 ptag"。
> **诚实边界 2**：Run 2 的 payload 跑完后 gem5 进程没有自行退出（该 rcS 不以
> `m5 exit` 收尾），在证据取齐后被我 `SIGTERM` 停止；`board.terminal`/`prop_*` 完整。
> **诚实边界 3**：驱动 STOP 的是 `o01_monitor_addr_bitflip`（**声明位 CAS 提交事件**仍是
> 未实现的 F 档位之一，见 §7.2），本 pilot 用的是既有 legacy 窗（`firstClock` +
> `maxFaults=1`），不是 F 档位——这与 §4 里"F2/F6 仍阻塞"一致。

### 3.4 预算

本轮共 **5 次** gem5 调用：Run 1（干净）、Run 2（注入）、reject5（O3-only 拒绝验证）、
reject3/reject2（隔离用，各 <90 s）；全部用 `flock` 占槽（slot1/2/3），无进程留存。

## 4. 35 项逐项裁决表（RunID | 分类 | 证据 | 状态）

分类取自任务书五类：**(a) 已有载体 / (b) 缺模型 hook / (c) 缺负载身份 /
(d) 构造性互斥 / (e) 真正外部**。

| RunID | 分类 | 证据 | 状态 |
|---|---|---|---|
| O01-F0-W7 | (a) | §3.2/§3.3：载体+平台+投放+**传播链**+**注入对照**全部真机通过 | **PILOTED（Masked）**；campaign 全样本未取 ⇒ 仍记 BLOCKED |
| O02-F0-W7 | (a) | 同 family `exmon-fsmc`；O02 mode 未 pilot | 仍 BLOCKED（载体就绪） |
| O03-F0-W7 | (a) | 同 family；O03 = `stxr_force_fail` 语义 | 仍 BLOCKED（载体就绪） |
| O02-F5-W7 | (a) | F5 = `maxFaults=0`（永久），由 `_fsmc_tier_flags` 表达 | 仍 BLOCKED（载体就绪，未 pilot） |
| O01-F2-W7 | (b) | `lsuTier/lsuSpanEvents/lsuWarmupEvents` 在 `.py` 声明、`.hh/.cc` **0 次**出现 | BLOCKED（见 §7.2） |
| O01-F6-W7 | (b) | 同上；F6 = 首个合格事件一次性 | BLOCKED（见 §7.2） |
| O02-F2-W7, O02-F6-W7 | (b) | 同上 | BLOCKED（见 §7.2） |
| O03-F2-W7, O03-F6-W7 | (b) | 同上 | BLOCKED（见 §7.2） |
| C08-F0/F2/F5/F6-W7 | (d) | §5：`CHAOSCache` 取 classic `Param.Cache`，Ruby L1 是 controller | BLOCKED（构造性互斥） |
| O04-F0/F2/F6-W7 | (b)+(c) | 钩子已落地（`rmw_mux`，compile-unverified）；W7 身份可满足但 F0 还需 RMW 流普查 | BLOCKED（见 §7.1） |
| O05-F0/F4/F6-W7 | (b)+(c) | 钩子 `rmw_order` 已落地；"提前 done"子模型平台不可达 | BLOCKED |
| O06-F0/F4/F6-W7 | (b)+(c) | `chaos_barrier_hook.hh` early/stuck 已落地 | BLOCKED |
| O07-F0/F2/F6-W7 | (b)+(c) | order-tag 已落地（诚实近似） | BLOCKED |
| O09-F0/F1/F2-W7 | (b)+(c) | `rmw_latch` 已落地；operand 锁存器子集 land-subset | BLOCKED |
| O09-F0/F1/F2-W13 | (c)+(d) | W13 钉 PARSEC；O09 的 RMW 宿主是 classic cache | BLOCKED |
| P09-F0/F4/F6-W13 | (c)+(d) | 同 §5.2：classic 多核无一致性 ⇒ 多线程语义与其宿主构造性互斥 | BLOCKED |

**分组计数**：A = 10（(a)4 + (b)6）；B = 4（(d)）；C = 15（(b)+(c)）；
D = 6（(c)+(d)）。合计 **35**，与任务书列表逐字一致（守恒）。

> **为什么一格都不解锁**（纪律）：A 组 4 格虽然现在有了**一条**真机样本（Masked），
> 但按仓库铁律"格子可执行"= campaign 能把这些格跑完并分类（含 n 样本 + 分类器），
> 本轮只取了**一条 pilot**，且它的载体是 pilot 参数化（不是 canonical 身份）。
> 故 `tools/lsu_fsmc_verdict.py` **保持原样**，`tests/test_lsu_fsmc_verdict.py`
> 的"任何一格静默解锁都 FAIL"仍然成立。

## 5. 构造性互斥 / 不可达：结构化证明

### 5.1 B 组（C08 ×4）：`Param.Cache` vs Ruby controller 是**类型事实**

1. `CHAOSCache.py` 的挂载参数是 `target_cache = Param.Cache(...)` ⇒ C++ 侧需要
   `gem5::BaseCache*` 的 **classic `Cache`** 血统对象。
2. stdlib 的 `chi.PrivateL1PrivateL2CacheHierarchy` 建的是 `RubySystem()` +
   **cache controller**；Ruby 的 L1 不是 classic `Cache` 的子类实例 ⇒ **无处可挂**。
3. 要一致性就必须 Ruby：gem5 v25 的 classic 内存系统**没有跨核一致性**
   （`src/mem/cache/noncoherent_cache.*` 存在；历史 `src/mem/cache/coherence/` 目录已删）。
4. 于是 C08（coherence 状态故障）的 SUT 语义（"一个核的 store 使另一个核的私有行失效"）
   在**能挂 CHAOSCache 的平台上不成立**，在**语义成立的平台上挂不上 CHAOSCache**。
   ⇒ **不是配置问题，是类型问题**；解除必须在 Ruby L1 controller 上加钩子（C++ + 重建，见 §7.3）。

### 5.2 P09（W13 ×3）：载荷语义与注入器宿主互斥（与"换哪个开源负载"无关）

P09 走 classic `CHAOSCache`（dirty-evict / victim 选择）。W13 的语义是"**多线程真实应用**"。
由 §5.1(3)，classic 多核**无跨核一致性** ⇒ 在 P09 能挂载的平台上，多线程共享内存语义
**不成立**。**换任何开源多线程负载都不改变这一点**。用"单线程脏逐出微探针"替代虽然
能立刻推进 3 格，但会把结论适用范围从"多线程真实应用"缩成"单线程微探针"——
**那是改写格子定义，属规格级决定**（本轮不擅自替换）。

### 5.3 C 组的两个"平台不可达"子模型（用代码路径证明，不是"我的负载没触发"）

- **O05 的"提前 done 允许后续 load 越过"**：classic 的原子 RMW 在
  `BaseCache::satisfyRequest` 内**同步**完成（`base.cc:1376-1419`），**不存在**可被提前的
  done 信号 ⇒ 无节点可注入。记为**平台不可达**。
- **O04-c/d 与 O09 的 compare/replacement/addend 锁存器**：这些操作数是 ISA 生成的
  `AtomicGeneric3Op<T>` 的**不透明成员**（`amo64.isa:201-215` + `amo.hh:87-105`），
  CPU 侧没有独立可寻址的锁存器可翻转。记为 **landed-subset**。

## 6. 真正外部 / 需裁决的缺失清单（精确）

| 项 | 精确缺失 | 性质 |
|---|---|---|
| PARSEC（W13，6 格） | 仓库内**无** PARSEC 源码 tarball / 输入集 / aarch64 二进制；唯一痕迹是 gem5 上游脚手架且自身被禁用（"PARSEC disk image is too big"）+ `valid_hosts=(host_x86_64_tag,)` | **不是授权问题**（PARSEC 开源），是**工程量 + 规格身份决定**：换钉 W13 的负载身份属规格级决定 |
| 2 核 CHI 检查点 | `/tmp/r4-8-fsmc/mc_boot/cpt.243414599076` 是 `/tmp` 临时产物（启动约 16 min），en 不在 git 内 | 集成方需重生成或固化到 git 外并设 `LSU_FS_MC_CHECKPOINT`；缺失时 campaign 已"大声拒绝" |
| `gem5-fs/` 子模块 | worktree 内不含 vmlinux/ubuntu.img（~2.6 GB） | 跑这些格需 `LSU_FS_DIR` 指向真实目录 |

## 7. 待主 agent 构建的 C++ 清单（本轮**禁 scons**，全部 compile-unverified）

### 7.1 已有但未构建的（R4-9-FSMC-C 产物，baseline 已含源码）

构建命令（主 worktree，`-j16`）：`cd CHAOS/gem5 && scons -j16 build/ARM/gem5.opt`
- 新增：`src/cpu/o3/chaos_barrier_hook.hh`（header-only，无 SConscript 改动）
- 改动：`src/mem/cache/base.{hh,cc}`、`src/mem/cache/CHAOSCache/CHAOSCache.{hh,cc,py}`、
  `src/cpu/o3/mem_dep_unit.cc`、`src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.{hh,cc,py}`
- **实测参照**：本轮用的二进制 `54c2c78ce4c84bb2` 已含 `chaosBarrierInsertHook`
  （`strings` 命中），说明 C 组钩子在某次构建里已进去过；集成方应以本轮 sha 为准重钉。
- 断言：`python3 tests/test_lsu_hook_o0x.py`（45 断言）与
  `python3 tests/test_lsu_fsmc_verdict.py` 必须全绿。
- 前置普查（F0 格）：`CHAOS_LSU_TRIGGER eligible=` 流长填进 `CACHE_F0_SPAN` /
  `LSQFWD_F0_SPAN`（命令见 R4-9-FSMC-C 报告 §7.2）。

### 7.2 **新**：`CHAOSExMon` 的 F 档位（解除 A 组 6 格）

`CHAOSExMon.py:40-42` 声明了 `lsuTier` / `lsuWarmupEvents` / `lsuSpanEvents`，
但 `CHAOSExMon.{hh,cc}` 里**一次都没读**（实测 grep 为空）⇒ F2 的 interval 与
F6 的确定性路径层没有落点，硬跑会让 F2/F6 与 F0 逐字节相同（错标）。

落点（复用既有触发器，不新造机制）：
```
CHAOSExMon.hh:
  #include "cpu/o3/chaos_lsu_trigger.hh"
  ChaOSLsuTrigger *lsuTrigger = nullptr;          // null = legacy window (现状)
  static ChaOSLsuTier stringToLsuTier(const std::string &);   // "off"→不建

CHAOSExMon.cc (ctor):
  if (p.lsuTier != "off")
      lsuTrigger = new ChaOSLsuTrigger(stringToLsuTier(p.lsuTier),
                                       p.rngSeed, p.lsuWarmupEvents,
                                       p.lsuSpanEvents, ChaOSLsuEvent::CasSuccess);

maybeCorruptMonitor()（LDXR 侧，O01/O02 的合格事件）与 maybeCorrupt()（STXR 侧）:
  if (lsuTrigger) { lsuTrigger->onAttempt();
                    if (!lsuTrigger->onEligible()) return <原有值>; }
  // F6：在"指定事件"处直接 lsuTrigger->onF6Event(false)（header 指定的非 ride 用法）

退出回调（CHAOSExMon 目前**没有** exit callback，需新增）:
  chaosLsuF6EventsReport();   // CHAOS_LSU_F6_EVENTS: TlbHit=.. SqForward=.. ...
  printf("CHAOS_LSU_TRIGGER: injector=chaoexmon tier=%s attempted=%lu eligible=%lu injected=%lu\n", ...)
```
- 语义等价性：`lsuTrigger == nullptr` 时原路径（`inWindow()` + geometric skip +
  `max_faults`）**逐字节不变** ⇒ 零回归。
- **诚实标注**：F6 的"指定事件类型"对 O01/O02 应为 `CasSuccess`（09 §2.1），但
  `CHaOSLsuEvent` 的四源通知是**单消费者**设计（`chaosLsuF6Notify` 是单函数指针，
  header 自陈"multicore/FS generalization is W8's business"）——多核 FS 上若已有别的
  消费者注册，会互相覆盖。**FS 多核下 F6 需先解决单消费者假设**，否则 F6 仍不能诚实落地。
  这条必须在构建前裁决（我把它留给主 agent，而不是静默实现）。

### 7.3 **新**：Ruby/CHI L1 controller 上的 coherence-state 钩子（解除 B 组 4 格）

最小落点（尚未写码，给出设计与断言）：
- 目标：在 CHI 的 L1 controller（`src/mem/ruby/slicc_interface/AbstractController` 子类，
  stdlib CHI 的 `L1Cache_Controller`）的**状态迁移点**（`setState` /
  `action` 表执行处）插入 CHAOS 钩子，使 C08 的 `coh`/`valid`/`dirty` 故障在
  **一致语义**下可注入。
- 注入器侧需要一个**新**SimObject（`CHAOSRubyCache`）：因为它拿不到 classic
  `BaseCache*`（§5.1），必须直接持有 Ruby controller 指针。
- 断言：注入后同一行的另一核 cache 行状态可观测变化（`RubySystem` 的
  `cache_line` 输出 / `--debug-flags=RubySlicc`）；未注入时 `reg_chain` golden 不变。
- **风险提示**：这是 C++/SLICC 两个层面的改动，且 Ruby 的状态机是生成代码
  （`.sm` → 生成 C++），比 §7.2 大一个量级。**若规格侧允许 C08 退化为单核
  I↔valid 模式**（§03 允许该表述），则 4 格可走 SE/单核路径解锁；否则就是本节工程量。
  **这是需要裁决的口径问题**，不是纯工程问题。

## 8. 命令 / 指纹 / 复核

产物指纹（本轮新增，canonical 未动）：
| 产物 | sha256 |
|---|---|
| `workloads/litmus/litmus_free_pilot` | `03db6af0038af3ea9bf8d9da06922a7d439a81341f167bb28ee496e0c66f9d64` |
| `configs/fs/litmus_free_pilot.rcS` | `f7a5a754feb7a253868744734a6bf3f1d268e21ae3c1a2a791c0aac92c21caab` |
| `workloads/litmus/litmus_free`（canonical，**未改**） | `6823afeb57194ded0aaf0dc2d7236468d973f252dc6b76abc72adc4789f4fed6` |
| `configs/fs/litmus_free.rcS`（canonical，**未改**） | `1112dc8f56fbbd21f02dcaf5a41d7206fc150ef7b4057ef559a155f831dfb642` |

本轮真实执行的命令（全部可复现）：
```
make -C workloads/litmus payload_free_pilot     # 生成 pilot ELF + rcS
taskset -c 0,1 ./litmus_free_pilot               # 宿主 golden：violations=0, FINAL=6ca52252681d0c34
python3 -m py_compile configs/fs/lsu_multicore_fs.py
<CHAOS-binary> ... run1（干净臂 + 传播）          # FINAL=6ca52252681d0c34；prop 流仅表头
<CHAOS-binary> ... run2（注入臂 o01 + 传播）      # 同一 FINAL；injections.log 1 行；616 事件
<CHAOS-binary> ... --cpu Atomic --chaos_propagation   # FATAL ... (O3-only)
```

**给集成方的一句话**：载体的"能不能观测"这一问已经答完（含链证据）；剩下的
两个 C++ 缺口（§7.2 ExMon F 档位、§7.3 Ruby 钩子）都不需要新的实验设计，
需要的是构建窗口 + 一次 §7.3 的口径裁决。
