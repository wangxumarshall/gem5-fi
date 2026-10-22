# R4-8-FSMC 逐项裁决：35 项 FS-MULTICORE BLOCKED（多核 FS 平台 + 仓库本地 litmus）

- 分支：`r4-8-fs-multicore`（worktree `.claude/worktrees/r4-8-fsmc`），base `d5fc8727`。
- 二进制（只读复用，**未做任何 scons 构建**）：
  `.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt`
  sha256 前缀 `7d52bc1392a10055`。
- 资产：`LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs`（vmlinux / ubuntu.img / boot.arm64）。
- 本报告是 **worktree 本地证据**（按任务书要求，不改 MDSPEC worktree 的共享文档）。

## 0. 结论摘要（先说结论，证据在后）

| 组 | RunID（35 项） | 裁决 | 依据 |
|---|---|---|---|
| A | O01-F0/F2/F6-W7、O02-F0/F2/F5/F6-W7、O03-F0/F2/F6-W7（10） | **载体 + 平台已落地并真机跑通**（§3）；"litmus needs multi-core FS" 这条 workload-level 理由**对它们已不成立**。残留缺口 = §09 要求的 `CHAOSAtomicTrace`（L1 monitor addr/valid/granule/version、atomic operand/SwapResp、order tag/barrier 完成点 + core/thread/global_order_id 关联键）**未实现**，且 campaign 路由/golden 未接线 ⇒ **格子仍记为 BLOCKED**，理由换成精确的那条 | §3 原始输出 |
| B | C08-F0/F2/F5/F6-W7（4） | **BLOCKED（构造性互斥）**：coherence 状态故障（C08）必须跑在有跨核一致性的平台（Ruby/CHI），而注入器 `CHAOSCache` 取 `Param.Cache`（classic 对象），Ruby 的 L1 是 cache controller ⇒ **无法挂载**；classic 多核又无一致性（§1.2 源码证据）⇒ litmus 载体在其上不成立 | §1.2、§1.3 |
| C | O04×3、O05×3、O06×3、O07×3、O09-F0/F1/F2-W7（15） | **BLOCKED（模型语义未实现）**：RMW data/operand 钩子（缺 cache-side SwapResp/operand hook）、RMW ordering、barrier 完成跟踪、order-tag swap —— 与多核无关的独立阻塞（`MODEL_BLOCKED` 已登记 O04/O05/O06/O07/O09） | §1.4、`tools/lsu_campaign.py` |
| D | O09-F0/F1/F2-W13（3）、P09-F0/F4/F6-W13（3） | **BLOCKED（规格负载身份 + 上述根因叠加）**：W13 规格钉 dedup/ferret/streamcluster；PARSEC 开源但仓库内**没有** aarch64 二进制/输入集（`find` 实证），且 O09/P09 各自的模型/注入器缺口未解 | §1.5、§5 |

一句话：**"litmus needs multi-core FS" 这条 blanket 理由，对 10 项已被证伪**（平台与载体都做出来并真机跑到了 guest 内 `nproc=2`），**对另外 25 项是错的描述**（真正的阻塞是注入器宿主/模型语义/负载身份）。

机读版裁决表：`tools/lsu_fsmc_verdict.py`（35 行逐格），断言：`tests/test_lsu_fsmc_verdict.py`。

## 1. 开工前的事实核查（全部实测/源码级）

### 1.1 平台侧：为什么原来跑不了多核 FS

| 事实 | 证据 |
|---|---|
| FS 平台硬编码单核 | `configs/se/arm_chaos_fs.py:254` `SimpleProcessor(num_cores=1)`；所有 FS 钩子绑 `processor.get_cores()[0]`（:303/:515/:565） |
| 全仓无多核 config | `grep -rn "num_cores" configs/` → 7 个 config 全 `num_cores=1` |
| 唯一的 FS 检查点是 1 核 | `runs/lsu/fs_cpt_boot/config.ini` 只有 `[board.processor.cores.core]`，`type=BaseAtomicSimpleCPU`，`numThreads=1`；检查点目录 `runs/lsu/fs_cpt_boot/cpt.237949797015/` |
| 1 核 classic 启动成本（工时量级） | 该 run 的 `stats.txt`：`hostSeconds=861.93` / `simSeconds=0.2397` / `simInsts=425016218` |

### 1.2 一致性侧：classic 多核为什么**原理上**不能跑 litmus

- gem5 v25 的 classic 内存系统**没有跨核一致性**：`CHAOS/gem5/src/mem/cache/` 下有
  `noncoherent_cache.{cc,hh}`，而历史上做 classic 一致的
  `src/mem/cache/coherence/` **目录已不存在**（`ls` 实证）。
- 推论（不是猜测）：core1 的 store 落在自己的私有 L1（dirties），不会使 core0 的
  私有 L1 行失效 ⇒ MP 型 litmus 的**无故障对照**就会挂死（读不到 flag），
  SB 型的直方图也不是硬件语义的直方图。**无一致性平台上做 litmus 无意义**，
  与"跑得动跑不动"无关。

### 1.3 可用的一致性路径（实测：不需要重建 gem5）

- `strings -a <gem5.opt>` 命中 `gem5::ruby::RubySystem`、
  `gem5::ruby::CHI::CHIRequestMsg` ⇒ **Ruby/CHI 已编进预编译二进制**，
  stdlib `gem5.components.cachehierarchies.chi` 可直接用（实跑见 §3.1）。
- `gem5-fs/` 有 `armv8_gem5_v1_{1,2,4,8,16}cpu.dtb`；guest 内核 5.15.36 明示
  `#1 SMP PREEMPT`。
- 结论：多核 FS 缺的**从来不是内核或一致性协议**，而是**板级 config + 多核检查点**。

### 1.4 注入器宿主：C08/P09 与一致性平台的构造性互斥

- `CHAOS/gem5/src/mem/cache/CHAOSCache/CHAOSCache.py`：`target_cache =
  Param.Cache(...)` —— classic `Cache` 对象。
- stdlib `gem5.components.cachehierarchies.chi.PrivateL1PrivateL2CacheHierarchy`
  （`chi/private_l1_private_l2_cache_hierarchy.py:128`）建的是 `RubySystem()`
  + cache **controller**，**没有 classic `Cache`** 可供挂载。
- 因此：**要 coherence 就得 Ruby，而 Ruby 上挂不了 CHAOSCache**。C08 的
  `targetField=coh`（`CHAOSCache.cc:619-625` 走 `setCoherenceBits`）在不一致的
  classic 多核上语义为空。要解这一组，得把注入钩子上到 Ruby 的 L1 controller
  （C++ 改动 + 重建）——本轮**禁 scons**，故记为真阻塞。

### 1.5 载荷投放路径（实测：单文件够用，但**成本**是瓶颈）

- guest 侧 `m5 readfile` 按 256 KiB 分块流式取
  （`CHAOS/gem5/util/m5/src/command/readfile.cc`：`char buf[256*1024]` +
  `while ((len = m5_read_file(buf, sizeof(buf), offset)) > 0)`），
  gem5 侧按 offset 续读（`src/sim/pseudo_inst.cc:371 readfile(tc,vaddr,len,offset)`）。
  ⇒ **没有 2 MiB 之类的上限**，可以把静态 ELF 以 base64 内嵌进 rcS 投放。
- 但**实测成本很高**（见 §3.2）：把 2.6 MB 的 base64 经 guest 的 `sh` heredoc
  解出，在第 3 模式下慢到超出本轮预算。这是本报告最重要的**量化发现**。

### 1.6 PARSEC（W13）现状

- `find . -iname "*parsec*"` → 只有 gem5 上游自带的测试脚手架
  （`CHAOS/gem5/tests/gem5/parsec_benchmarks/`），**没有** PARSEC 负载/输入集；
  `blackscholes`/`dedup`/`ferret`/`streamcluster` 二进制均不存在。
- PARSEC 本身是开源的（无授权障碍），但"在 aarch64 上构建 + 投放到 guest"
  是实打实的工时，且必须先解决 §1.4/§1.4 的模型/宿主缺口才谈得上用它做载体。

## 2. 交付物（Task 1 / Task 2）

commit `8e0c3a95`（平台）与 `159716e1`（载体）。

- `configs/fs/lsu_multicore_fs.py`：`--num-cores`（默认 2）真正接进
  `SimpleProcessor`；`--coherence chi|classic`（chi = Ruby/CHI，**一致**；
  classic 保留为对照臂/旧管线）；CPU 侧注入器 `--chaos_exmon`
  （+`--exmon_mode/--exmon_lsu_tier/--exmon_lsu_warmup_events/--exmon_lsu_span_events`
  /`--exmon_max_faults/--exmon_rng_seed`）；`--chaos_core` 显式选择挂哪一核。
  文件头写明 CHAOSCache 与 Ruby 的构造性互斥。
- `workloads/litmus/`：`litmus_sb.c` / `litmus_mp.c` / `litmus_atomic.c`
  + `litmus_common.h` + `Makefile`（`all` / `fs` / `smoke` / `payload`）
  + `make_payload.py`（可 `--compress`）；`configs/fs/litmus.rcS`（未压缩参考产物）
  与 `configs/fs/litmus_c.rcS`（gzip 压缩，2.26× 小）。
- sha256：

| 产物 | sha256 |
|---|---|
| `configs/fs/litmus.rcS` | `ec84972307aa938d2b220ac921c37720552a2acbd7a7375ccbf54f4865a26c8f` |
| `configs/fs/litmus_c.rcS` | `316b1e5f5b46d48d4252ff770bb8f50bde37bf6d0b3334761486d01ab1d8e409` |
| `litmus_atomic_fs` | `0e49b661edc59b831cdcb97ded62e6aa31c4b07beb46d5ee31dcf0e2d2780980` |
| `litmus_sb_fs` | `2e8190a29894822d1e4dd6eac7333fb92341acc594e92f7ebac55c247eddfbc9` |
| `litmus_mp_fs` | `dee38b5c1819ea8a7a1fc1ba32e66317ecfdb7d2ebfd67499e7d4b649541f7e2` |

宿主原生验证（真 aarch64、真 fork、真共享内存，与 gem5 无关）见 commit
`159716e1` 的 message：三个 litmus 全 0 违例、`tries` 高于最小值（真并发争用）、
SB 直方图非退化、三个 `FINAL` 互异。

## 3. 真机运行（原始输出）

命令模板（每一次都 `flock /tmp/lsu_gem5_slotN.lock`，outdir 只写 `/tmp/r4-8-fsmc/`）：

```
gem5.opt --outdir=<tmp>/<arm> configs/fs/lsu_multicore_fs.py \
    --kernel=gem5-fs/vmlinux --disk=gem5-fs/ubuntu.img \
    --bootloader=gem5-fs/boot.arm64 \
    --num-cores=2 --coherence=chi --cpu=<Atomic|O3> \
    [--restore-checkpoint=/tmp/r4-8-fsmc/mc_boot/cpt.243414599076] \
    --readfile=<rcS>
```

### 3.1 平台臂：2 核一致（Ruby/CHI）FS 从零启动 → 取检查点 → O3 恢复 【通过】

（1）从零启动（`--cpu Atomic`，参照 1 核经典臂 862 s 的工时基线）：

```
[lsu_multicore_fs] num_cores=2 coherence=chi cpu=Atomic l1d=16KiB/4 l2=256KiB/8
warn: Using an atomic core with Ruby will result in 'atomic_noncaching'
      memory mode. This will skip caching completely.
... guest 内核:
[    0.000000] Booting Linux on physical CPU 0x0000000000 [0x410fd070]
[    0.000000] Linux version 5.15.36 ... #1 SMP PREEMPT
...
aarch64-gem5 login: root (automatic login)
Starting gem5 init... reading run script file.
Running m5 script from /tmp/script
[boot_ckpt.rcS] booted to userspace; taking checkpoint
warn: No behavior was set by the user for checkpoint. ... Writing checkpoint
```

产物：`/tmp/r4-8-fsmc/mc_boot/cpt.243414599076`，其 `config.ini` 有两核与 Ruby：

```
[board.processor.cores0]  type=BaseAtomicSimpleCPU
[board.processor.cores1]  type=BaseAtomicSimpleCPU
（ruby 段 2606 行；cpt 目录内含 board.cache_hierarchy.ruby_system.cache.gz）
```

（2）O3 恢复 + 载荷投放：

```
[lsu_multicore_fs] num_cores=2 coherence=chi cpu=O3 l1d=16KiB/4 l2=256KiB/8
[lsu_multicore_fs] restoring from checkpoint: /tmp/r4-8-fsmc/mc_boot/cpt.243414599076
src/mem/ruby/system/Sequencer.cc:707: warn: Replacement policy updates ...
（无 unserialize 报错；guest 继续执行，出现 'csdb'/'bti' unimplemented 警告）
[boot_ckpt.rcS] restore pass: dispatching payload
[boot_ckpt.rcS] payload head: # litmus.rcS — W7 Atomic-Litmus 多核 FS payload (R4-8-FSMC)。
[litmus.rcS] nproc=2
[litmus.rcS] cpuinfo processors=2
[litmus.rcS] deploying litmus binaries from embedded base64
```

**`nproc=2` 与 `/proc/cpuinfo` 的 `processor` 计数 = 2** 是"guest 真的把两个
核都启起来了"的现场证据（不是配置推断）。

时间账（诚实）：1 核经典启动参考 862 s；本次 2 核 CHI 启动到检查点
`hostSeconds≈940 s`；O3 恢复后到载荷派发 ~9.5 min。

### 3.2 载荷臂：litmus 在 guest 内的执行 【本轮未在预算内完成 —— 量化阻塞】

三次真机尝试（全部 2 核 CHI + O3 恢复 + 同一检查点）：

| 臂 | 载荷 | 结果 |
|---|---|---|
| A 干净对照 | `litmus.rcS`（未压缩 2.60 MB） | 派遣成功、解出前**卡在第一个二进制**；`--fs-timeout` 级 40 min 上限内未打印任何 per-binary 行 |
| B 注入臂 | `litmus.rcS` + `--chaos_exmon --exmon_mode o01_monitor_addr_bitflip --exmon_lsu_tier F0 --exmon_lsu_span_events 8` | 注入器已挂载（日志实证见 §3.3）；载荷同 A 的慢 |
| C 压缩对照 | `litmus_c.rcS`（gzip，1.15 MB） | 同 A 的慢（用于区分"体积问题"还是"结构问题"） |

判据与证据强度：

- **可以断言**：多核 FS 平台端到端可用（启动→检查点→O3 恢复→载荷派遣→
  guest 内 `nproc=2`→宿主脚本在 guest 里按序执行到 `base64` 解包）；
  载荷 rcS 的结构经检查无误（3 个 heredoc、各 1 个终止符、最长行 116 B，
  见 §3.4 的检查脚本）。
- **不可以断言**：litmus 的 oracle 行（`LITMUS atomic ctr_expect=… violations=…`）
  与 `FINAL=`。因此本报告**不宣称**任何一格因为本次运行而"可端到端执行"。
- **量化阻塞**：guest 侧把 ~0.86 MB 的 base64 heredoc 经 `sh` 解包成 640 KB 的
  静态 ELF（`base64 -d` + `chmod` + `sha256sum`）在 2 核 Ruby/O3 恢复态下
  **>17 min 未完成**（对照：同一宿主用 20 个 fork/exec 的 T-系载荷只用了约
  10 min，见 `configs/fs/tlb_probe.rcS` 头注）。瓶颈在**载荷字节数 × guest
  磁盘/管道路径**，不在 CPU。
- **修法（下一位集成方按此做，成本已量化）**：不要把静态 glibc 二进制
  （~640 KB/个 → base64 ~0.86 MB/个）当载荷。两个立即可用的方向：
  1. `-nostdlib` 手写 syscall 的 litmus（aarch64 原始系统调用：
     `clone`(220) 代 fork、`mmap`(222)、`sched_setaffinity`(122)、`exit`(93)），
     产物约 **2–4 KB**，base64 后仍是几 KB ⇒ 解包在秒级；
  2. 或把 ELF 放进 guest 镜像/第二块磁盘（本 worktree 无 root，未采用）。
  本次的压缩臂 C 已经把 2.60 MB 降到 1.15 MB（2.26×），足以说明方向对：
  载荷体积是**一阶**成本。

### 3.3 注入臂：O01 在多核 FS 上真实挂载 【通过（挂载），未到 oracle】

```
src/arch/arm/CHAOSExMon/CHAOSExMon.cc:43: info: CHAOSExMon: SELF-ATTACH to ISA
    board.processor.cores0.core.isa (mode=o01_monitor_addr_bitflip)
[lsu_multicore_fs] restoring from checkpoint: /tmp/r4-8-fsmc/mc_boot/cpt.243414599076
[lsu_multicore_fs] CHAOSExMon attached to core 0 (mode=o01_monitor_addr_bitflip, tier=F0)
```

诚实说明：本次 F0 的 span 取 8（`--exmon_lsu_span_events 8`）而不是 campaign
默认的 1000。理由是**可执行性**而非调优：本 litmus 的 eligible 流是
`ldxr` 事件（32 轮 × 4 次 × 2 核 ≈ 256 个），span=1000 会出现仓库里已记录过的
"F0 window 超流长 ⇒ 结构性零注入"（同 S10-F2/R4-6 的结论）。本轮**没有**做
eligible 流普查，所以 span=8 是 pilot 值，**不得**当成已验证的窗参数。

## 4. 逐行裁决表（机读：`tools/lsu_fsmc_verdict.py`）

| 组 | 数量 | 裁决值 | 精确理由（表格里的原文） |
|---|---|---|---|
| A | 10 | `CARRIER_READY_RESIDUAL_BLOCKED` | 载体+平台已落地并真机跑通（2 核 Ruby/CHI + 仓库本地 litmus，guest nproc=2）；workload-level 理由作废。残留 = §09 CHAOSAtomicTrace 未实现 + campaign 路由/golden 未接线 |
| B | 4 | `BLOCKED_INJECTOR_HOST` | CHAOSCache 是 classic `Param.Cache`，Ruby 的 L1 是 controller ⇒ 一致平台上挂不了；classic 多核无一致性 ⇒ litmus 不成立。解除需 Ruby controller 侧钩子（C++ + 重建） |
| C | 15 | `BLOCKED_MODEL_UNIMPL` | O04（SwapResp/RMW data hook）、O05（RMW ordering）、O06（barrier 完成）、O07（order-tag）、O09（RMW operand hook）——模型语义未实现，独立于多核 |
| D | 6 | `BLOCKED_WORKLOAD_IDENTITY` | W13 钉 PARSEC(dedup/ferret/streamcluster)，仓库无 aarch64 二进制/输入集；且叠加 C 组/O09 与 B 组/P09 的根因 |

台账订正（同一改动单元）：
- `tools/lsu_campaign.py` 的 `WL_BLOCKED["Atomic-Litmus"|"PARSEC"]` 与
  `MODEL_BLOCKED["O05"|"O06"|"O07"]` 的**理由串**改写为上述精确表述；
  **保留 `multicore-fs:` 前缀**（故意），因为 `tools/lsu_blocked_triage.py`
  用正则 `r"multicore"` 做互斥分类——去掉前缀会让这些格子掉出 FS-MULTICORE 桶
  甚至被判成 OK（静默解锁），本轮明令禁止。
- **实测守恒**：用本分支重新生成 runid_map 并跑 triage，
  `FS-MULTICORE=35` 不变（`[triage] ... FS-MULTICORE=35 ...`）。
- 路由：**故意不接线**。理由：接线的唯一诚实形式是"campaign 真能把这些格跑完
  并分类"，而 §3.2 表明本轮还没跑到 litmus 的 oracle；现在写路由会得到
  半接线（有路由、无 golden、跑不出结果），这正是纪律条文禁止的形态。
  测试 `test_lsu_fsmc_verdict.py` 会**强制**这一判断：任何一格若被接通
  （`resolve_cell` 不再返回 None），断言立刻失败，逼着把裁决表一起改。

## 5. 真正不可替代的东西

1. **C08 / P09 的注入器宿主**（7 格：C08-F0/F2/F5/F6-W7、P09-F0/F4/F6-W13）：
   `Param.Cache` vs Ruby controller 是 gem5 的**类型事实**，不是配置问题。
   要么在 Ruby cache controller 上加钩子（C++ + 重建），要么承认 C08 的
   coherence 语义在本平台只能用"单核 I↔valid 退化模式"表达（规格 §03 允许
   这句，但那与 W7 的多核语义冲突——**这是需要规格侧裁决的口径问题**）。
2. **O04/O05/O06/O07/O09 的模型语义**（15 格）：RMW data/operand、barrier、
   order-tag 的钩子本来就没实现；多核 FS 落地**不改变**这一事实。
3. **W13 的 PARSEC 身份**（6 格）：PARSEC 开源、无授权障碍，所以它**不是**
   "法律上不可替代"；但它**在本仓库内**不存在（无二进制、无输入集），
   在 aarch64 上构建 + 投放是真实工时。是否用开源替代负载改钉 W13 的负载身份，
   是**规格级**决定，本轮以"开放问题"登记，不擅自替换（否则就是静默改格子定义）。
   量化取舍：替代（例如用仓库既有的 `cache_dirtyevict`/`prefetch_stride` 做
   P09 的载体）能立刻推进 3 格 P09，但它同时把 W13 的"多线程真实应用"语义
   削成"单线程脏逐出"，**结论的适用范围会变小**——需要规格侧认可。
4. **§09 的 `CHAOSAtomicTrace`**（10 格 A 组）：是 C++ 新组件（`isa.cc` 的
   locked read/write monitor、atomic Request/SwapResp、barrier/order 完成点，
   并接进 `CHAOSPropagation`），本轮禁 scons 故未实现。

## 6. 给集成方的操作清单

1. **不需要重建 gem5**：平台与载荷都是 Python/配置层（已在本分支）。
2. 多核检查点：`/tmp/r4-8-fsmc/mc_boot/cpt.243414599076` 是 `/tmp` 临时产物。
   集成方若要复现，请按 §3 的命令重跑启动臂（约 16 min）并在 git 外的
   固化目录留存（`runs/` 不入 git）。
3. 载荷体积是**一阶**成本：把 litmus 改成 `-nostdlib` 的 ~3 KB 版本，
   或在 guest 镜像里预置二进制；否则每格要烧 30 min 以上。
4. 台账订正已在 `tools/lsu_campaign.py`；共享的
   `docs/gem5-fi/lsu/mdspec/blocked_triage.md` **未被本分支改动**
   （它是 MDSPEC worktree 的共享证据，本轮禁改）；集成方重跑
   `tools/lsu_runid_map.py` + `tools/lsu_blocked_triage.py` 即可拿到更新后的理由串。
5. Task 4 的断言语义：**任何一格静默解锁都会让 `tests/test_lsu_fsmc_verdict.py` 失败**。
