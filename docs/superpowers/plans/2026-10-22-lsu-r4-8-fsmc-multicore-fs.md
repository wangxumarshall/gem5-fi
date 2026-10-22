# R4-8-FSMC：35 项 FS-MULTICORE BLOCKED 的落地裁决（多核 FS 平台 + 仓库本地 litmus）

> 计划文件 = 工作清单（source of truth）。每个 Task = 一个 commit（one-patch-per-unit）。
> 复选框 `- [ ]` 完成即勾，随后 commit + push 到 `r4-8-fs-multicore`（非 main）。
> 分支 base：`d5fc8727`（= `lsu-mdspec-20261019`）；worktree
> `/home/sdc/gem5-fi-ding/.claude/worktrees/r4-8-fsmc`。

## 背景与目标

`blocked_triage.md` 把 35 个 RunID 记为
`workload-level:blocked(multicore-fs: litmus needs multi-core FS)`。
**项目负责人裁定（本轮绑定）**：先用仓库内已有的合法载体、开源替代负载、
可复现的小 litmus 测试去满足；**只有授权数据本身真正不可替代**才保留外部阻塞。
→ 默认是"解决"，不是"延期"；但"沉默地不可执行的解锁"比"诚实阻塞"更糟。

35 项构成（按可执行性拆开，见 Task 4 的逐项裁决）：

| 组 | RunID | 现状根因（本计划开始前） |
|---|---|---|
| A | O01-F0/F2/F6-W7, O02-F0/F2/F5/F6-W7, O03-F0/F2/F6-W7（10） | 注入器已实现（CHAOSExMon，CPU 侧）；只缺多核 FS 载体 |
| B | C08-F0/F2/F5/F6-W7（4） | 注入器是 **classic cache 侧**（CHAOSCache `Param.Cache`）；coherence 模型需要多核一致性 |
| C | O04×3, O05×3, O06×3, O07×3, O09-F0/F1/F2-W7（15） | 模型语义本身未实现（RMW data/operand hook、order-tag、barrier 完成） |
| D | O09-F0/F1/F2-W13, P09-F0/F4/F6-W13（6） | W13=PARSEC 身份 + C/D 组根因叠加 |

## 已核实的平台事实（Task 1 前的前置调查，均为实测/源码证据）

1. `configs/se/arm_chaos_fs.py:254` 硬编码 `num_cores=1`；所有 CHAOS FS 钩子绑
   `processor.get_cores()[0]`（:303/:515/:565）。
2. 全仓**无**多核 config（7 个 `configs/se/*` 全 1 核）、**无**多核 checkpoint
   （唯一 FS 检查点 `runs/lsu/fs_cpt_boot/cpt.237949797015` 的 sibling
   `config.ini` 只有 `[board.processor.cores.core]`，`numThreads=1`，
   `type=BaseAtomicSimpleCPU`）。
3. FS 用的是 **classic** `PrivateL1PrivateL2CacheHierarchy`；gem5 v25 的 classic
   内存系统**跨核不保证一致性**（`src/mem/cache/noncoherent_cache.{cc,hh}` 存在；
   旧 `src/mem/cache/coherence/` 目录已不存在）→ 经典多核上 litmus 的**无故障
   对照**就跑不通（core1 的 store 不会使 core0 的私有 L1 行失效）。
4. 一致性只能来自 Ruby。**实测**：预编译二进制（sha256 前缀 `7d52bc1392a10055`）
   含 `gem5::ruby::RubySystem` / `gem5::ruby::CHI::CHIRequestMsg` 符号 ⇒ stdlib
   CHI 层次（`gem5.components.cachehierarchies.chi`）**无需重建**即可用。
5. `gem5-fs/` 有 `armv8_gem5_v1_{1,2,4,8,16}cpu.dtb`，guest 内核 Linux 5.15.36 SMP。
6. 1 核 classic 启动到用户态实测 `hostSeconds=861.93`（`simSeconds=0.2397`）——
   多核 boot 的工时量级由此确定。
7. guest 侧 `m5 readfile` 是按 256 KiB 分块流式取（
   `CHAOS/gem5/util/m5/src/command/readfile.cc`）⇒ 单文件投放**没有 2 MiB 限制**，
   可以 base64 内嵌二进制。

## 资源与纪律

- 禁 scons（不改 C++）；只跑预编译二进制；≤8 次 gem5；每次 `flock /tmp/lsu_gem5_slot1.lock`；
  outdir 只写 `/tmp/r4-8-fsmc/*`；绝不写共享 `runs/`。
- FS 资产 `LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs`；
  checkpoint `/home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015`（只读）。
- 诚实优先：**没有端到端真机跑通的格子一律保持 BLOCKED**，但理由必须换成精确的那条。

---

## Task 1 [R4-8-FSMC-1]：多核 FS 平台 config（含一致性选择）

**Files:** `configs/fs/lsu_multicore_fs.py`（新增）；`tests/test_lsu_fs_infra.py`（改断言）。

- [x] 1.1 写 `configs/fs/lsu_multicore_fs.py`：`--num-cores`（默认 2）、
      `--coherence {chi,classic}`、kernel/disk/bootloader/readfile/restore-checkpoint、
      CPU 侧注入器 `--chaos_exmon`(+tier/seed/mode)。文件头写清"为什么"、
      classic 无一致性的源码证据、CHAOSCache 无法挂 Ruby 的构造性事实。
- [x] 1.2 **真机验证**：2 核 Atomic + CHI 启动（`--readfile boot_ckpt.rcS`）
      → 产出 2 核 checkpoint；`config.ini` 出现 `cores0/cores1` + ruby 段；
      guest `dmesg`/`board.terminal` 出现 SMP 双核证据（`/proc/cpuinfo`）。
      **判据：checkpoint 目录存在且其 config.ini 是 2 核。**
- [x] 1.3 改 `tests/test_lsu_fs_infra.py`：把"FS 平台单核"这条断言改成
      （a）legacy `arm_chaos_fs.py` 仍单核 且（b）新的多核 config 存在、默认 2 核、
      CHI 可选、classic 保留；再断言站内没有多核 checkpoint 的检测是**诚实**的
      （有则报有）。
- [x] 1.4 commit + push。

## Task 2 [R4-8-FSMC-2]：仓库本地 litmus 载体（自造、自 oracle、可复现）

**Files:** `workloads/litmus/{litmus_common.h,litmus_sb.c,litmus_mp.c,litmus_atomic.c,Makefile,make_payload.py}`（新增）。

- [x] 2.1 三个 litmus：SB（dmb 保护）、MP（跨核可见性）、ATOMIC（LDXR/STXR
      CAS counter，同时报总重试次数 ⇒ 区分"重试吸收=Masked"与"丢失更新=SDC"）。
      oracle = 规格 §6 W7 的"每轮检查禁出现结果"计数（必须 0），
      另打 `FINAL=<16hex>`（只哈希 测试标识+违例数+轮次，不含非确定的分布）。
- [x] 2.2 **宿主原生验证**（真多核 aarch64，与 gem5 无关）：三个都 0 违例、
      且观察到真并发（ATOMIC tries > 最小、SB 直方图非退化）。
- [x] 2.3 `make payload` 从 ELF 生成 `configs/fs/litmus.rcS`（base64 内嵌，幂等，
      打印 sha256）。
- [x] 2.4 commit + push。

## Task 3 [R4-8-FSMC-3]：多核 FS litmus 真机端到端 + O01/O02/O03 注入臂

**Files:** `configs/fs/litmus.rcS`（Task 2 生成）；证据入 `R4-8-FSMC-report.md`。

> **未达成（如实）**：平台臂通过（guest `nproc=2`），但载荷臂三次真机尝试都卡在 guest 侧 base64 解包（≥18 min 未完），litmus 的 oracle/FINAL 未取到；原因与量化见报告 §3.2，故本项**不勾**，也不据此宣称任何格子可执行。
- [ ] 3.1 从 Task 1 的 2 核 checkpoint 恢复，`--cpu O3 --coherence chi`，
      `--readfile configs/fs/litmus.rcS`：三个 litmus 全跑完并打印 oracle 行 +
      `FINAL`（无故障时违例=0）。
- [ ] 3.2 同一次运行加 `--chaos_exmon --exmon_mode o01_monitor_addr_bitflip
      --exmon_lsu_tier F0`：观测注入日志非空 + litmus 的 tries/oracle 变化。
- [x] 3.3 记录原始输出（board.terminal 摘录 + 文件 sha256）；若任一步不成立，
      **如实记录失败**，并把该格保持 BLOCKED。
- [x] 3.4 commit + push。

## Task 4 [R4-8-FSMC-4]：35 行逐项裁决 + 断言钉死 + 证据报告

**Files:** `docs/gem5-fi/lsu/mdspec/R4-8-FSMC-report.md`（新增，worktree 本地）；
`tests/test_lsu_fs_infra.py`、`tests/test_lsu_runid_map.py`（增断言）；
`tools/lsu_campaign.py`（只在**可端到端执行**时才允许改路由，否则不改）。

- [x] 4.1 逐行裁决表：row → verdict → 证明它的产物/命令 → 原始输出摘录。
- [x] 4.2 测试断言：把"这 35 项各自为什么阻塞"机读化，**任何一格静默解锁都算 bug**。
- [x] 4.3 只在 Task 3 真的端到端跑通时才写 campaign 路由（否则明确记录"未接线，
      因为会变成半接线"）。
- [x] 4.4 commit + push；`git rebase lsu-mdspec-20261019` 后 push 最终版。

## 停止条件

所有 Task 完成，或（a）真机证据证明某条路不可达且已如实记录，或（b）预算/时长耗尽
且已把"做到了哪一步、剩什么、为什么"写进报告。**不得**在未跑通时宣称解锁。
