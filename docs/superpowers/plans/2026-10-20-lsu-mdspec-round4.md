# LSU 收口第四轮：S 系真实触发 + SQ/MSHR/TLB 观测补证 + 49 项 MODE-UNIMPL + FS/A06 + 325 项 READY 契约

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development（fresh-context 顺序 subagent）。
> 复选框 `- [ ]` 逐项勾；每个 Task = 一个 commit（one-patch-per-unit）。
> 本文件是**唯一事实来源**（source of truth），用于跨会话/压缩后恢复。

**用户指令（2026-10-20 第四轮，顺序执行）**

1. 查明 S01/S02 三 seed 均 `activated=0` 的原因，修复真实触发条件；把生产 store / 消费 load 的
   `dyn_inst_seq`、`sq_idx`/`lq_idx`、`request_id` 传入 `CHAOSLSQFwd`，**禁止仅地址关联**。
2. 修复并真实观测 `sq_execute`。
3. 构造**可重复 miss 载体**并真实观测 `mshr_alloc` → merge/fill/free。
4. 解决 `CHAOSArmTLB` 地址域关联的**并发歧义**，改为 Request/seq 关联或提供**可验证的复合键**。
5. 按 `C11 → C12 → L04 → P06 → C14/C15 → S10 → A07 → T08` 实现**全部 49 个 MODE-UNIMPL**。
6. 继续解决 A06、FS-INFRA、FS-MULTICORE；完成 SPEC 适配——**只有合法 SPEC 数据缺失**可保留为外部输入。
7. 生成 **325 个 RunID 逐项 READY 契约**，完成最终构建、全测试、SE/FS smoke 与资源准入。

**停止条件（只有两个）**：(a) 达到正式实验 GO 并停在启动前；(b) 所有其他工作完成、仅剩用户才能提供的
合法授权数据/凭据。**阶段报告、commit、pilot 失败、发现新 bug 都不是停止条件。**

**正式 campaign 禁止启动。**

## Global Constraints（沿用，绑定每个 Task）

- **规格至上 / Unknown 语义 / 禁止单键关联 / 诚实优先**：缺事件只报 Unknown，绝不推断 Masked；
  地址域关联在**并发歧义**下必须改为 seq/Request 关联或给出可验证复合键。
- **one-patch-per-unit**：每 Task 一 commit，真机验证后 push 到 `lsu-mdspec-20261019`（非 main）。
- **不碰他人遗留**；绝不 `git add -A`；并发 gem5 ≤4；`-j16` 构建（`-j126` 仅在增量时）。
- **构建必须显式核验成功**（不得 `scons | grep` 吞错误）；**不做未验证的声明**。
- 二进制：worktree `CHAOS/gem5/build/ARM/gem5.opt`；工具经 `LSU_GEM5_BIN` 环境变量指认。
- FS 资产：`LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs`（worktree 无 3GB 子模块）。
- 主 agent 控上下文：子 agent 只回**精简证据摘要**，详细证据写仓库文件。

**基线（本轮开始时实测）**：HEAD `76994a16`，分支 `lsu-mdspec-20261019`，
worktree `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019`；
二进制 sha256 前缀 `58fef3c92da60bcb`；覆盖矩阵 PASS=101 / PARTIAL=98 / BLOCKED=126（163 项分类：
RULING 6 / LICENSE 12 / FS-MULTICORE 35 / FS-INFRA 24 / MODE-UNIMPL 49… 合计 126）。

---

## Task 1 [R4-1][S-TRIGGER]: S01/S02 真实触发条件 + seq/idx/request_id 关联

**Files:** `CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.{hh,cc}`；
`CHAOS/gem5/src/cpu/o3/lsq_unit.cc`（必要时 `lsq.cc`）；`CHAOS/gem5/src/cpu/o3/cpu.hh`（如需转交）；
`configs/se/lsu_proxy.py`（模式 flag）；`tools/lsu_prop_fields.py`；`tests/test_lsu_hook_lsq.py`（或新增）。

- [ ] **1.1 根因**：用正式 campaign 入口复跑 `S01-F0-W5`、`S02-F0-W5`（各 3 seed），
      结合 `--debug-flags=LSQUnit,CHAOSLSQFwd`（若存在该 flag）确证 `activated=0` 的**真实原因**
      （是 trigger 掩码/window 问题，还是注入点从未被调用，还是 lsq_struct_mode 未被消费）。
      **必须给出可直接引用的实测输出**，不得推测。
- [ ] **1.2 修复触发条件**：使 S01/S02 在真实负载上产生非零注入（注入日志非空）。
- [ ] **1.3 关联改造**：把生产 store 的 `dyn_inst_seq`/`sq_idx`/`request_id` 与消费 load 的
      `dyn_inst_seq`/`lq_idx`/`request_id` 传入 `CHAOSLSQFwd`；`lsq_fwd` 事件必录字段加入
      `store_dyn_inst_seq`/`sq_idx`/`lq_idx`/`request_id`；**移除仅地址关联**路径（或标注为 fallback 并记录）。
- [ ] **1.4 测试**：契约测试（事件必录字段含新 key）+ 既有 suite 不回归。
- [ ] **1.5 真机**：S01/S02 各 1 RunID 经**正式 campaign 入口**运行，`lsu_chain_check.py` 逐边记录；
      证据写入 `docs/gem5-fi/lsu/mdspec/round4_findings.md`。
- [ ] **1.6** commit + push。

## Task 2 [R4-2][SQ-EXEC]: 修复并真实观测 `sq_execute`

**Files:** `CHAOS/gem5/src/cpu/o3/lsq_unit.cc`（`executeStore` 钩子时序）；必要时 `CHAOSPropagation`。

- [ ] **2.1 定论**：以 `--debug-flags=LSQUnit` 定向运行证明 `sq_execute` 缺失属
      (a) 注册可见性时序 还是 (b) 注入指令为 load。引用实测输出。
- [ ] **2.2 修复**：使被污染 store 在 `executeStore` 时能关联到链（键取自 R4-1 的 seq/sq_idx）。
- [ ] **2.3 真机**：S 系 RunID 真实运行，观测到 `sq_execute`，Store Queue 7/7。
- [ ] **2.4** commit + push。

## Task 3 [R4-3][MSHR]: 可重复 miss 载体 + `mshr_alloc`→merge/fill/free 真实观测

**Files:** `docs/gem5-fi/lsu/mdspec/targeted_pilot_sq_mshr.md`（更新）；
必要时 `configs/se/lsu_proxy.py` + workload（`workloads/` 下新增 miss 载体）。

- [ ] **3.1 载体**：构造**可重复**的"故障行被驱逐后再取回"场景（W6 2×L1D working set 或新增
      定向 workload），证明 `mshr_alloc` 可复现出现。
- [ ] **3.2 观测**：真实观测 `mshr_alloc` → `mshr_merge`/`mshr_fill`/`mshr_free` 全链；L1d-Cache 11/11。
- [ ] **3.3** 覆盖矩阵重生成 + 证据更新 + commit + push。

## Task 4 [R4-4][TLB-CORR]: ArmTLB 关联去地址歧义（Request/seq 或可验证复合键）

**Files:** `CHAOS/gem5/src/arch/arm/CHAOSArmTLB/CHAOSArmTLB.{hh,cc}`；
`CHAOS/gem5/src/arch/arm/tlb.cc`（调用点传 Request/seq）；`CHAOSPropagation.{hh,cc}`（复合键 API）。

- [ ] **4.1 歧义实证**：给出并发同 VA 不同 seq（或同 VA 不同 PA）下地址域关联**错配**的可复现实证。
- [ ] **4.2 改造**：改为 Request/seq 关联；若确无 Request 可用，提供**可验证复合键**
      （如 `va+asid+vmid+seq`）并给出其唯一性/无歧义的验证证据。
- [ ] **4.3 真机**：FS（或 SE 探针）真实运行，链完整且无错配。
- [ ] **4.4** commit + push。

## Task 5 [R4-5][MODE-UNIMPL]: 49 项 MODE-UNIMPL（按序，每模型一 commit）

顺序：**C11 → C12 → L04 → P06 → C14/C15 → S10 → A07 → T08**（依据 `mode_unimpl_plan.md`）。

每项落地模板（`mode_unimpl_plan.md` §逐项落地模板）：注入端 Mode + 观测端节点 +
`configs/se/lsu_proxy.py` 路由 + `lsu_campaign.MODEL_FLAGS` + 从 `MODEL_BLOCKED` 删除（**只有断言可跑才删**）
+ 契约测试 + 真机证据（先证注入日志非空）+ 矩阵重生成。

- [ ] **5.1 C11（8 RunID）**：MSHR merge 腐蚀注入模式 + 观测。
- [ ] **5.2 C12（6）**：fill 时序偏移注入模式 + 观测。
- [ ] **5.3 L04（6）**：响应配对的可注入且可追踪映射。
- [ ] **5.4 P06（6）**：预取属性标记钩子 + 注入。
- [ ] **5.5 C14（2）**：MSHR busy 注入点 + busy 观测。
- [ ] **5.6 C15（6）**：MSHR occupancy/entry 选择注入。
- [ ] **5.7 S10（6）**：StoreSet SSID 事件源 + 注入。
- [ ] **5.8 A07（6）**：AGU clean ready/握手钩子。
- [ ] **5.9 T08（3，FS-only）**：FS 页表遍历 walk/fill 配对。
- [ ] **5.10** 49 项不可实现者**如实列为需裁决**（不得伪装完成）；矩阵重生成。

## Task 6 [R4-6][A06/FS/SPEC]: A06 + FS-INFRA + FS-MULTICORE + SPEC 适配

- [ ] **6.1 A06**：load 侧 size 注入（放大器路径或 LSQRequest 层）+ byte-enable 钩子 + spike 证据；
      成功后从 RULING 类移除这 6 项。
- [ ] **6.2 FS-INFRA（24）**：FS checkpoint 流水线跑通 TLB 翻译负载（4KiB/2MiB、ASID、同VA不同PA、权限、TLBI）。
- [ ] **6.3 FS-MULTICORE（35）**：多核 FS（SMP + 跨核一致性）落地；O 系 litmus 多核可判别。
- [ ] **6.4 SPEC 适配**：完成 SPEC 侧的**可替代部分**适配；**只有合法 SPEC 数据缺失**（授权数据/凭据）
      才保留为外部输入并明确列出。
- [ ] **6.5** 每项独立 commit + push；每项真实运行证据。

## Task 7 [R4-7][READY-CONTRACT]: 325 RunID 逐项 READY 契约 + 最终验收

- [ ] **7.1** 逐 RunID 契约表：每个 RunID 一行 = 状态(READY/PARTIAL/BLOCKED) + 精确命令 + 前置条件
      + 验收判据。**325 = READY + PARTIAL + BLOCKED**（计数必须自洽）。
- [ ] **7.2** 最终构建（`scons -j16` 干净）+ 全测试（`pytest tests/ -q`）+ SE smoke + FS smoke。
- [ ] **7.3** 资源准入核验（CPU/内存/磁盘/并发上限）+ 二进制身份（sha256）。
- [ ] **7.4** 若全部 READY → 达到 GO，停在**启动前**；否则列出仅剩的用户侧输入。
- [ ] **7.5** commit + push；更新 memory。

---

## 进度节（第四轮实测）

- [x] **Task 1 [S-TRIGGER]** `152f6569` + fix `2de6c332`：根因实测 = F0 `next_fire =
      warmup + lcg(seed)%span`，campaign 侧 lsqfwd span=1000 在 7 条 eligible 流上**不可达**
      （`attempted=7 eligible=7 injected=0`）；改 span + 真实 seq/idx 关联（`FwdCorrelKeys`）。
      审查 2 项 Important 已在 1 轮修复闭环（corr 标注贯通 21 个关联点 + 逐(模型,负载)实测 span
      + 双模式响亮告警）。真机：S01/S02×3 seed，`activated=3+3`，6/6 注入，链至 L3。
      证据 `docs/gem5-fi/lsu/mdspec/round4_findings.md`。
- [x] **Task 1 全部子项 1.1–1.6** 完成（见上）。
- [ ] Task 2–7 未开始。
- **正式 campaign 未启动。**
