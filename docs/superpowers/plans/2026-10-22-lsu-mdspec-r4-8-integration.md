# LSU MDSPEC R4-8 集成轮：七分支串行收口到 325 RUNID READY 契约

> **For agentic workers:** 主 agent 独占执行（语义合并 / 构建 / census / pilot / chain-check / 证据 / commit / push）。
> 复选框 `- [ ]` 逐项勾；每个 Task = 一个独立 commit（one-patch-per-unit）。subagent 不得执行本文件任何步骤。
> 本文件是**唯一事实来源**。

**起点**：`lsu-mdspec-20261019` @ `d5fc8727`（== origin）。契约基线 **READY=220 / PARTIAL=0 / BLOCKED=105**
（RULING 6 / FS-INFRA 24 / MODE-UNIMPL 3 / UNRESOLVED 19 / PLATFORM-DEFECT 6 / FS-MULTICORE 35 / LICENSE 12）。
二进制身份：worktree `CHAOS/gem5/build/ARM/gem5.opt` = `7d52bc1392a10055`（仓库根 `build/` = `10590f6295bc4dec` 陈旧，禁用）。

**待集成分支（全部基于 `d5fc8727`）**

| 分支 | 内容 | 语言面 |
|---|---|---|
| `r4-7-s10-span` | S10 F0 实测窗解锁（真机 injected=1）/ F2 结构性不可达响亮拒绝 | Python |
| `r4-7-a06-full` | A06 load shrink + byte-enable + 传播观测 | **C++** |
| `r4-7-fsinfra-w1` | FS-INFRA 24 项精确化 + W1(MiBench) 19 项口径订正 | Python |
| `r4-8-spec-residual` | W11/SPEC 12 项粒度订正 + T08-W9 残口 + 契约分类兜底报警 | Python |
| `r4-9-fsmc-a` | 多核 FS 平台 + freestanding litmus 载荷投放（**含** `r4-8-fs-multicore`） | Python+资产 |
| `r4-9-fsmc-c` | O04–O09 RMW/barrier/order-tag 钩子 + 定向载体 | **C++** |

`r4-8-fs-multicore` 被 `r4-9-fsmc-a` 通过 merge 包含 → **不单独集成**。

**全局约束（绑定每个 Task）**

- **不做未经验证的声明**；`n/a` 与 Unknown 优先于静默零值。
- 每 Task 顺序 = 审查 → 语义合并 → （必要时）构建 → 回归 → census → 真机 pilot → chain-check →
  coverage_matrix / ready_contract / runid_map 重生成 → commit → push（非 main）。
- 构建：`scons -j16 build/ARM/gem5.opt`，必须显式核验 exit 与**零新警告**；Python-only 变更无需构建。
- 并发纪律：gem5 严格串行（团队槽锁 `/tmp/lsu_gem5_slot*.lock`，≤4）；`-j16` 构建期间不跑 gem5。
- 禁止 `git add -A`；禁止触碰共享 `runs/` 的无关内容；禁止引用过期统计 239/86。

---

## Task 0 [R4-8-HYG][WORKLOAD-BIN]: 未跟踪负载二进制纳入

**依据**：`a06_size_be` / `ssit_dual_set` 的 `.c` 源已跟踪（`5082dd8f` / `8276087b`）；
两二进制与 `gcc -O2 -static` 从源重建结果**逐字节一致**（sha256 实测相等）；
仓库惯例是**提交**同级负载二进制（`sq_forward`/`alias_sites`/`gemm_float_kernel` 等 30+ 均已被 git 跟踪）。

- [ ] 0.1 复核 sha256 与重建一致性（记录到 commit message）
- [ ] 0.2 `git add workloads/directed/a06_size_be workloads/directed/ssit_dual_set` → commit → push

## Task 1 [R4-8-PYTEST][GATE]: pytest 入口错误修复 + gate 测试口径诚实化

**结论（已实证）**：5 项错误全部在 `tests/test_claim_concurrency.py` —— 该文件是**脚本式测试**
（`check` 是 `main()` 内定义的**位置回调**，非 pytest fixture），`pytest` 将其当作 fixture 请求 → ERROR。
**是测试入口错误，不是功能错误**（该文件 `python3 tests/test_claim_concurrency.py` 可正常自跑）。

- [ ] 1.1 使 5 个子测试在 pytest 下可真实执行（提供 `check` fixture，断言失败即 FAIL，不静默）
- [ ] 1.2 核验 `pytest tests/ -q` → 0 error，且脚本式自跑仍 `rc=0`
- [ ] 1.3 gate 如实报告测试口径（pytest + 脚本式）/ commit / push

## Task 2 [R4-8-S10]: 集成 Agent1
- [ ] 2.1 审查 diff（`tools/lsu_campaign.py` span/interval 门禁 + 4 个测试）
- [ ] 2.2 合并 → 回归（`test_lsu_hook_s10*` + `c11/c12/l04` + pytest 基线）
- [ ] 2.3 census：S10 逐 (model, workload) eligible 实测（真机）
- [ ] 2.4 pilot：S10-F0-W5 / W9 经 campaign 入口真机激活 + chain-check 逐边
- [ ] 2.5 重生成 runid_map / coverage_matrix / ready_contract
- [ ] 2.6 commit + push

## Task 3 [R4-8-FS-W1]: 集成 Agent3
- [ ] 3.1 审查 diff（`WL_BLOCKED["MiBench"]` 删除 + `ARMTLB_MODELS` + `SE_W1_TIMEOUT`）
- [ ] 3.2 合并 → 回归（`test_lsu_fs_infra` / `test_lsu_runid_map`）
- [ ] 3.3 FS-INFRA 真机复核（campaign 入口，W4 行）
- [ ] 3.4 W1 合法性复核（二进制/golden/合法路径三段证据）
- [ ] 3.5 重生成三件套 → commit + push

## Task 4 [R4-8-SPEC]: 集成 Agent5
- [ ] 4.1 审查 diff（SPEC 键收窄 + T08-W9 理由 + `ready_contract._classify` 兜底）
- [ ] 4.2 合并 → 回归（新增 `test_lsu_w11_spec_residual` / `test_lsu_ready_contract_category`）
- [ ] 4.3 复核 `runid_map.json` 重生成结果与契约分类（RULING 不再吞 MODE-UNIMPL）
- [ ] 4.4 重生成三件套 → commit + push

## Task 5 [R4-8-FSMC-A]: 集成 Agent6（含 Agent4）
- [ ] 5.1 审查 diff（多核 FS config + litmus 载体 + `exmon-fsmc` 家族）
- [ ] 5.2 合并 → 回归（`test_lsu_fsmc_verdict`）
- [ ] 5.3 多核检查点可用性核验（`LSU_FS_MC_CHECKPOINT`；缺失则响亮拒绝）
- [ ] 5.4 真机 litmus 无故障对照复核 + A 组 4 格 campaign dry-run/真跑
- [ ] 5.5 重生成三件套 → commit + push

## Task 6 [R4-8-FSMC-C]: 集成 Agent7（C++）
- [ ] 6.1 审查 diff（RMW/barrier 钩子 + `mem_dep_unit` + 载体）
- [ ] 6.2 合并 → **构建 `-j16`**（零新警告）
- [ ] 6.3 回归（`test_lsu_hook_o0x` + 全 pytest）
- [ ] 6.4 census（CACHE_F0_SPAN / LSQFWD_F0_SPAN 新条目）+ 真机 pilot（RMW 路径 + barrier 路径）
- [ ] 6.5 重生成三件套 → commit + push

## Task 7 [R4-8-A06]: 集成 Agent2（C++）
- [ ] 7.1 审查 diff（`CHAOSAddrPath` size 包络 + `lsq_unit` buffer floor + `dyn_inst` 字段）
- [ ] 7.2 合并 → **构建 `-j16`**（零新警告）
- [ ] 7.3 回归（`test_lsu_a06_*` + 全 pytest）
- [ ] 7.4 真机 spike：widen / shrink / byte-enable 三臂 + chain-check
- [ ] 7.5 决定 A06 6 格的最终状态（删 `MODEL_BLOCKED` 仅当 3 seed 真机通过）
- [ ] 7.6 重生成三件套 → commit + push

## Task 8 [R4-8-GO]: 最终准入
- [ ] 8.1 最终构建（显式核验）+ 全测试（pytest + 脚本式）+ SE/FS smoke
- [ ] 8.2 `python3 tools/lsu_ready_contract.py --gate`（**准入检查命令**，非启动命令）
- [ ] 8.3 资源门禁（mem/disk/并发上限）+ 二进制 SHA256 定格
- [ ] 8.4 唯一的正式 campaign 启动命令（GO 前不执行）
- [ ] 8.5 停在启动前，向用户报告 READY/PARTIAL/BLOCKED + 剩余外部阻塞 + 证据
