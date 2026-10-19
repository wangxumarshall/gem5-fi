# LSU 历史修复选择性移植 + Markdown 规格 L0–L5 完整传播监控 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 以 `docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案.md` + 4 个子文档为**唯一实验规格**，选择性移植 LSU 历史修复分支中仍适用的提交，并补齐规格要求的注入与 L0–L5 完整传播监控；Phase A–C 完成前**不启动 325 RunID 正式 campaign**。

**Architecture:** 三层递进：Phase A 在隔离 worktree 的新分支上按依赖序 cherry-pick 6 个历史提交（其中 A06S 提交经专项裁决改造，不整分支 merge）并以 TDD 补齐用户指定的测试义务；Phase B 生成"规格→CLI→注入点→钩子→字段"机读映射与 PASS/PARTIAL/BLOCKED 覆盖矩阵，再按 7 个钩子族补齐 gem5 源码钩子与 CHAOSPropagation 的表 11 字段；Phase C 用单一代表性 RunID（A01-F0-W3）跑 golden+fault pilot 验证 L0–L5 全链。Phase D（325 分批）仅在 pilot 全过且 A06 裁决落地后另行提案。

**Tech Stack:** gem5 v25.1.0.1 vendored（C++ 钩子，scons -j16）；Python 工具链（openpyxl/pytest，均已装）；分支 `lsu-mdspec-20261019` + worktree `.claude/worktrees/lsu-mdspec-20261019`（自带 build，二进制身份哈希纪律）。

**Spec（唯一实验规格，冲突时规格胜出）:**
- `docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案.md`（主文档，元数据绑定 xlsx sha256=`389546f0…e273e0`）
- 子文档 `…-07-展开执行矩阵.md`（325 RunID × 43 列）、`…-09-逐RunID传播监控.md`（325 行传播规格）、`…-10-源码监控映射.md`（64 模型钩子映射）、`…-03-位置x模型矩阵.md`（64 模型定义）

---

## Global Constraints

- **规格至上（用户三.6 原文）**：不得为了让运行通过而改变 Markdown 的模型语义、RunID 或激活口径。规格文档与代码冲突 → 规格胜出。
- **Unknown 语义（规格表 9 判定列原文）**：链在某节点后缺事件，只能标"截至该节点可证，后续 Unknown"，**不得推断 Masked**。
- **禁止单键关联（用户三.4）**：跨单元关联必须用复合键（run_id + sample_run_id + fault_id/ptag；event_id + parent_event_id；tick/cycle + core_id + thread_id；dyn_inst_seq + commit_seq + PC/opcode；lq_idx/sq_idx；request_id/pf_request_id/walk_id/mshr_id/fill_id；VA/PA/cache_line；arch_reg/phys_reg）。禁止只用 tick 或 address 连接。
- **空=空/诚实标记**：A06 相关 RunID 在 load 侧与 byte-enable 实现并验证前一律标 **BLOCKED**，不得伪装完成、不得引入 A06S 模型 ID（用户二.3）。
- **F6 单语义**：正式运行只用 `f6Mode=early_stress`（=规格 F6"首次出现指定事件时注入一次"）；steady_state 仅作显式 opt-in 的独立扩展实验，不得与正式 F6 样本混合（用户二.4）。
- **不碰他人遗留**：主树 69 个删除项、176 个未跟踪文件、`.planning/`、OOO 产物一律不 stage、不清理、不还原（用户一.2）。
- **执行场地**：新分支 `lsu-mdspec-20261019`（基于 fi-ding@7d2bb8ca）+ worktree `.claude/worktrees/lsu-mdspec-20261019`；主树零改动。worktree 内构建 `CHAOS/gem5/build/ARM/gem5.opt`（clean 用 **-j16**，增量 -j126），**零新警告**；每个涉及二进制的提交记录 `git rev-parse HEAD` + gem5.opt sha256（沿用 70ff317b 身份纪律）。
- **资源门禁**：并发 gem5 进程 ≤4；pilot 阶段 workers=1 串行（用户二.6：防资源压力制造伪 Timeout/SimFailure）。
- **one-patch-per-unit**：每任务恰好一个 commit，验证后立即 `git push origin lsu-mdspec-20261019`（非 main）。
- **规格完整性门禁**：每个 Phase 开始前重跑 `python3 tools/lsu_xlsx_to_md.py --xlsx <xlsx> --out-dir docs/gem5-fi/lsu --validate` 必须 ALL PASS（xlsx sha 与 MD 元数据绑定 + 325 RunID 唯一 + 表 7∩表 9 集合相等一并复验）；不一致 → 停下报告。

## §0 开始前审计结论（2026-10-19 实测，用户一.1–一.5）

| 项 | 实测结果 |
|---|---|
| HEAD/分支 | fi-ding @ 7d2bb8ca（本特性 8 提交 f5b25a1a..7d2bb8ca 已推送；PR #60 = integration/lsu-xlsx2md-20261019→main OPEN） |
| 工作树 | 69 个 ` D`（evidence 等删除）+ 176 个未跟踪——他 session 遗留，本计划零接触；xlsx 与 5 个 MD 干净入库 |
| 规格绑定 | xlsx sha256=`389546f0…e273e0` 与 MD 元数据一致（V5 PASS）；325 RunID 表 7/表 9 各自唯一且集合相等（V2 PASS）——2026-10-19 复验 |
| 7 历史对象归属 | **全部不在 fi-ding HEAD**：469429f4、28caead8 仅存于 `capacity/lsu-slots-24-20261014`；dd6714c4/83ff9265/35ccda91/dd755d7e/63cacb61 存于 `fix/lsu-p4-simfail-20261015`（基座 21109127 **已在 HEAD**）及 `integration/lsu-p4-20261016`（=5 提交+8657b992 空行清理） |
| cherry-pick 冲突风险 | **零**：`git diff 21109127..HEAD` 对 P4 触碰的全部文件（CHAOSAddrPath/、lsu_proxy.py、lsu_campaign.py、lsu_obs_core.py、guard/hostmon/obs_driver）为空 |
| 现状代码缺口 | 表 9 实现状态：**240 部分已有 + 85 需新增，PASS=0**（诚实基线：无任何 RunID 现状即完整）；HEAD 的 `lsu_obs_core.py` 无 cache Field 解析（grep data_shift/Field=0）；HEAD 的 CHAOSAddrPath 仍含**会触发断言的旧 a06_size**（:271）；CHAOSPropagation 现有链仅 addrpath 家族（inj/addr_form/mem_req/resp/taint_reg/consumer/errant_commit） |

## §1 历史提交裁决表（deliverable 1）与移植顺序（deliverable 2）

| # | 提交 | 裁决 | 理由（实证） | 移植方式 |
|---|------|------|--------------|----------|
| 1 | `469429f4` [OBS-FIX-5] | **采用** | cache Field 系列（tag/valid/dirty/data_shift/toggle）注入行解析是 C04–C09 模型 L0 的前提；HEAD 缺失已实证；+57 行纯 Python，其提交信息自带 TDD 记录 | cherry-pick（自 capacity 分支），随后补 C04–C09 → 合法 L0 fault_applied 测试（Task A1，用户指定义务） |
| 2 | `dd6714c4` [P4-FIX-RECLASS] | **部分采用** | 离线重分类 v2 七规则只读工具（rule_version/逐样本记录/守恒）；可复用规则逻辑，但输出须适配新版结果字段与 L0–L5 终止判定；离线分类不得替代传播证据（R2.6/R2.7 保留 SimulatorFailure tag 的纪律可取） | cherry-pick 原样入库（独立新文件），适配改造随后一个 commit（Task A5） |
| 3 | `83ff9265` [P4-FIX-A06S] | **部分采用（经 §2 裁决改造）** | 其安全机制（store-only、load 候选显式 REJECT 日志、isLoad/isStore/reject_reason）正确；但其"a06_size 退役 + a06s_store_size 新名 + 新 RunID 族 A06S-*"**违反新规格**（Markdown 定义 A06、无 A06S） | 先按分支序 cherry-pick 保持链干净，再以专门改造提交反转命名与语义（Task A4） |
| 4 | `35ccda91` [P4-FIX-GEOM] | **采用** | 64B line 合法性检查 + 16 次重采样/拒斥 + `obs_post_geomreject` 可观测计数 + 真实 mode 标签；拒斥计为 phantom decline 不计 injected（不静默改变目标分布） | cherry-pick + 分布守恒测试（Task A3） |
| 5 | `dd755d7e` [P4-F6] | **采用** | `f6Mode` 参数实测：`early_stress` 默认 = 首次事件注入（与规格 F6 语义一致）；`steady_state` 显式 opt-in 且事件流耗尽则永不注入 | cherry-pick 整提交 + 正式运行门禁测试（Task A3 步骤合并：GEOM 与 F6 各自独立测试） |
| 6 | `28caead8` [CAPACITY] | **拒绝（暂不移植）** | 8→24 槽扩容与新版实验语义无关；pilot 保守并发（≤4）由资源门禁保证 | 不移植；仅作参考 |
| 7 | `63cacb61` [P4-FIX-DOCS] | **拒绝** | 其设计/矩阵/提案文档属旧 P4 修复轮语境，已被新 Markdown 规格取代 | 不移植 |
| 8 | `integration/lsu-p4-20261016` | **不合并** | 上述 P4 提交的集合视图（+8657b992 空行清理）；重复合并会引入已拒绝项 | 仅作 cherry-pick 源参考 |

**移植顺序（依赖与分支序驱动，逐个一 commit）**：
`A1: 469429f4`（独立 Python）→ `A2: dd6714c4`（独立新文件）→ `A3: 83ff9265`（AddrPath 链 1/3）→ `A4: 35ccda91`（AddrPath 链 2/3）→ `A5: dd755d7e`（AddrPath 链 3/3）→ `A6: A06 安全化改造`（手工提交，§2 裁决落地）→ `A7: 构建与回归门禁`。
（83ff9265/35ccda91/dd755d7e 共改 CHAOSAddrPath.cc 且原分支序即 dd6714c4→83ff9265→35ccda91→dd755d7e，乱序 cherry-pick 会互相冲突；dd6714c4 是无依赖新文件，提前到 A2 不破坏链。）

## §2 A06 专项裁决（deliverable 5）

**规格定义（表 3/10）**：A06 = AGU/LSU access-size（1/2/4/8/16B）与 byte-enable 字段注入，地址不变；子模型 A06-a size 改另一合法值、A06-b byte-enable 改另一合法掩码；激活口径 = 子字节或向量访存且故障值被下游实际消费；6 个 RunID（A06-{F0,F2,F6}×{W3=AGU-AddrModes, W5=SQ-Forward}）。

**a. 可安全实现的语义**：store 侧 size 替换安全（内存写以 packet 字节落盘，短写架构合法——83ff9265 代码注释与 1,030 样本审计共证）；load 侧 size **缩小**不安全（见 b）；load 侧 **放大**未验证（可能触发对齐/跨行拆分路径，无实证）；A06-b byte-enable 在 `lsq_pushRequest_PRE` 钩子处为 const（83ff9265 注释实证），需在 packet 构建层另立钩子（Phase B H1/H3 范围）。

**b. 旧 load-size 断言根因**：缩小的 load packet 命中 gem5 定宽完成路径断言 `LDRX completeAcc getRaw<T>`（`sizeof(T) <= size` 类断言，P4 审计 1,030 checklist + 737 W1 样本，ITEM-026/027 全灭；reclass_v2 R2.6 以 `A06_MODEL_CONFLICT` tag 保留该签名）。

**c. 不违反契约的实现路径**：正式 A06-a load 侧不得通过缩小 Request/packet 实现；候选路径为（i）验证放大侧的对齐/拆分行为（Request 契约 spike），或（ii）在 LSQRequest 构建层注入 size 字段并让完成路径走对应宽度分支——两者均需 gem5 `lsq_unit.cc` completeAcc/Request 契约的源码级验证后另提裁决。A06-b 在 packet 构建（`LSQRequest`/byteEnable 路径）注入。

**d. 现状裁决**：在 load 侧与 byte-enable 实现并实证前，**A06 全部 6 RunID 标记 BLOCKED**（覆盖矩阵与 campaign 调度双层阻止）；代码保留 store-only 安全路径（Task A6 改造后以 `a06_size` 模式名承载，load 候选 REJECT 日志留证）；`a06s_store_size` 成为被拒绝的别名；**不引入 A06S 模型 ID**。解除 BLOCKED 的条件：c 中至少一条路径通过 spike 验证 + 测试。

## §3 覆盖基线统计（deliverable 3）与缺失钩子清单（deliverable 4）

**325 RunID 实现覆盖基线（Phase A 完成后由 Task B2 再生成精确矩阵）**：

| 状态 | 数量 | 说明 |
|------|------|------|
| PASS（现状即完整） | **0** | 诚实基线：无一 RunID 现状即满足表 9 全链+全字段 |
| PARTIAL（部分已有） | **240** | 按 单元族：A33/C48/L21/O10/P47/S57/T24 |
| BLOCKED（需新增） | **85** | 按 单元族：A6/C25/L9/O18/P6/S6/T15；含 A06 的 6 个（§2 裁决） |

**64 模型现有代码覆盖（表 10 实测分类）**：15 AddrPath（注入+部分传播：inj/addr_form/mem_req/resp/taint_reg/consumer/errant_commit）｜12 CHAOSCache（仅 data/data_shift 跟踪 delivery，tag/valid/dirty/coh/victim 仅 inj 节点）｜6 CHAOSLSQFwd（Propagation 明确不支持）｜6 CHAOSPrefetch（不支持）｜5 CHAOSArmTLB（无 lookup→walk/refill→PA trace）｜3 CHAOSExMon（不支持）｜17 无模型专属注入/监控（仅通用 CommitTrace/MicroSnap/Probe 可启用）。

**缺失钩子清单（7 个钩子族，覆盖全部 325 RunID；源锚点来自表 9/10）**：

| 族 | RunID 数 | 源码锚点 | 新增内容 |
|----|---------|---------|---------|
| H1 lsq.cc 统一事件 | 39 | `src/cpu/o3/lsq.cc::pushRequest`、`LSQRequest::sendFragmentToTranslation` | 统一事件 + lq_idx/sq_idx + PC/opcode + event_id/parent_event_id |
| H2 CHAOSTLBTrace | 39 | `src/arch/arm/tlb.cc::lookup/translateTiming`、`table_walker.cc` walk/refill 完成点 | translate/walk/refill 节点 + walk_id/tlb_entry/way |
| H3 CHAOSLSQTrace（SQ） | 63 | `src/cpu/o3/lsq_unit.cc` insertStore/executeStore/checkViolations/writebackStores/commit-drain | SQ 逐事件 + state_before/after |
| H4 cache.cc 扩展 | 73 | `src/mem/cache/cache.cc` access/handleTimingReqMiss/recvTimingResp/handleFill/evictBlock/writeback | mshr_id/fill_id + 结构事件 |
| H5 CHAOSPrefetchTrace | 53 | `src/mem/cache/prefetch/stride.cc::calculatePrefetch`、`queued.cc` 队列、`base.cc::notify` | pf_request_id：training→queue→request→fill→demand |
| H6 CHAOSAtomicTrace | 28 | `src/arch/arm/isa.cc` locked read/write monitor、atomic Request/Packet 与 cache SWAP 路径 | 原子事件链 |
| H7 LQ 逐事件 | 30 | `src/cpu/o3/lsq_unit.cc` insertLoad/read/checkViolations/completeDataAccess 与 replay | lq_idx 生命周期 |
| （横切）CH AOSPropagation 字段扩展 | 全部 325 | `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/` | 表 11 缺失字段（见下） |

**表 11 字段缺口（横切，H0 任务）**：新增必需——`sample_run_id`、`parent_event_id`、`core_id/thread_id`、`pc/opcode`（传播事件）、`lq_idx/sq_idx`、真唯一 `request_id/transaction_id`（保留 instSeqNum）、`walk_id/tlb_entry/way`、`mshr_id/fill_id`、`pf_request_id`、`state_before/state_after`、`detection_layer/contained`、`evidence_status`（observed/derived/missing/conflict——Unknown 语义的载体）。

## §4 Pilot RunID 选择（deliverable 6）

**选定：`A01-F0-W3`**（AGU 单比特翻转 · F0 单发 · AGU-AddrModes 探针）。

理由（全部实证）：① 现有传播链最全——表 10 A01 属 AddrPath 15 模型族，CHAOSPropagation 已有 inj→addr_form→mem_req→resp→taint_reg→consumer→errant_commit 全节点；② 规格全链 L0→L1→L2→L3→L4→L5 明确（表 9 行全文已核）；③ 负载已存在（`workloads/directed/agu_addrmodes`，directed 确定性、秒级、golden 可即时生成）；④ F0 单发 + 触发"任一已完成地址生成"最易复现；⑤ 是矩阵第一行且子模型覆盖低/中/高位单 bit 三种几何，能同时验证 GEOM（A3）移植后的行为；⑥ 其缺失项（H1 统一事件 + H2 TLB 节点 + 关联字段 + CommitTrace v2）恰是 39-RunID 共用路径——pilot 直接驱动该家族首装并使 39 RunID 受益。**pilot 样本量 ≤5 activated（远小于 385 目标），仅验证链与指标，不产正式统计**。

## §5 测试/构建/资源门禁与回滚（deliverable 7）

| 门禁 | 内容 |
|------|------|
| 构建 | 每 C++ 提交：worktree 内 `cd CHAOS/gem5 && scons -j16 build/ARM/gem5.opt`（首装 clean）/后续 -j126 增量；**零新警告零错误**；记录 HEAD + gem5.opt sha256 于提交信息 |
| 单元测试 | 每任务 TDD RED→GREEN；全套件（含 `tests/test_lsu_obs_core.py`、`tests/test_lsu_obs_driver_workers.py`、`tests/test_lsu_xlsx_to_md.py` 等）全绿 |
| 不受影响回归 | `python3 -m pytest tests/ --collect-only -q` 基线对照 + `python3 tools/manifest_validate.py --help` exit 0 + 至少一个无注入 directed smoke（如 agu_addrmodes golden 短跑） |
| 规格门禁 | 每 Phase 前重跑 xlsx↔MD `--validate` ALL PASS |
| 资源 | gem5 并发 ≤4；pilot workers=1；hostmon/巡检不干扰 |
| Phase 门禁 | C→D：pilot 全链 PASS + A06 裁决状态明确 + 覆盖矩阵更新后才允许起草 325 分批提案（另行计划与批准） |
| 回滚 | 每提交独立可 revert；worktree 整体可弃（`git worktree remove` + 删分支）；主树与 fi-ding 全程零改动；pilot 产物只写 worktree 内 runs/ |

## §6 正式 campaign 未启动声明（deliverable 8）

**本计划执行完毕 ≠ campaign 启动。** 325 RunID × 385 activated 的正式量产，需 Phase C pilot 全部通过 + A06 等 BLOCKED 项裁决明确后，**另立计划文档并经用户批准**方可启动。本计划 Phase D 仅产出提案骨架。

## Review Focus

1. **把"部分已有"误当"完整实现"**（用户一.5）→ Task B2 覆盖矩阵必须以 PASS=0 起步，每个 PASS 都有钩子+字段双重证据；矩阵生成器测试钉住"部分已有≠PASS"。
2. **A06 静默替换/伪装完成**（用户二.3）→ Task A6 测试：`a06_size` 为唯一合法模式名、`a06s_store_size` 被 config 层拒绝、campaign A06 条目 BLOCKED、无 A06S RunID 泄入 map。
3. **离线分类替代传播证据**（用户二.5）→ Task A5 适配测试：`evidence_status=missing` 时输出 Unknown 而非 Masked/Crash；reclass 输出带 rule_version 与只读保证。
4. **steady_state 混入正式 F6 样本**（用户二.4）→ Task A5 门禁测试：mdspec track 拒绝 `f6Mode=steady_state`。
5. **GEOM 拒斥静默改变 A01/A02 目标分布**（用户二.2）→ Task A4 分布守恒测试：固定种子下注入前后 old/new EA 分布逐位相等 + geomreject 计数可观测非零路径。

---

### Task 0: 计划入库

**Files:** Create `docs/superpowers/plans/2026-10-19-lsu-mdspec-port-and-l05.md`（本文件）

- [x] **Step 0.1** 记录规格指纹：`python3 tools/lsu_xlsx_to_md.py --xlsx "docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案.xlsx" --out-dir "docs/gem5-fi/lsu" --validate` → ALL PASS；`sha256sum` xlsx = `389546f0…e273e0`。抄录进提交信息。
- [x] **Step 0.2** `git add docs/superpowers/plans/2026-10-19-lsu-mdspec-port-and-l05.md && git commit -m "[LSU][MDSPEC][PLAN] 历史修复选择性移植 + Markdown 规格 L0-L5 监控计划（含 A06 裁决/pilot 选择/门禁）" && git push origin fi-ding`

---

### Task A0: 执行场地（分支 + worktree + 首装构建）

**Files:** 无仓库文件改动（worktree 建立 + 构建产物）

- [ ] **Step A0.1** `git worktree add .claude/worktrees/lsu-mdspec-20261019 -b lsu-mdspec-20261019 fi-ding`；在 worktree 内确认 `git log --oneline -1` = 7d2bb8ca。
- [ ] **Step A0.2** 首装构建：worktree 内 `cd CHAOS/gem5 && scons -j16 build/ARM/gem5.opt`（预计 30–60 分钟，首配置 ~2 分钟/项为正常）。记录 gem5.opt sha256 + HEAD 于台账。
- [ ] **Step A0.3** 基线冒烟：worktree 内 `build/ARM/gem5.opt --outdir=/tmp/mdspec_a0_golden configs/se/lsu_proxy.py --cmd workloads/directed/agu_addrmodes --cpu O3`（无注入 golden）正常退出；此 golden 留作 Phase C 对照。
- [ ] **Step A0.4** 规格门禁：worktree 内跑 `--validate` ALL PASS（worktree 的 docs/ 与 xlsx 与主树同源）。

> 以下 A1–A6 全部在 worktree 内执行；每个 cherry-pick 任务的模式统一为：**先写失败测试（RED）→ cherry-pick → 测试转绿（GREEN）→ 全套件回归 → commit（若 pick 本身即构成 commit，则测试以紧随 commit 的验证步骤呈现，测试文件单独 commit）**。cherry-pick 保留原作者信息；测试提交独立。

### Task A1: 移植 469429f4（cache Field 解析）+ C04–C09 L0 测试（用户指定义务）

**Files:**
- Modify（经 cherry-pick）: `tools/lsu_obs_core.py`
- Test: `tests/test_lsu_obs_core.py`（追加）

**Interfaces:** 产出 `_CACHE_FIELD_INJ_RE`（格式 `Tick: <t>, Cache Block Addr: <addr>, Field: <spec>[, <detail>]`）；C04/C05/C09 注入行 → 合法 L0 fault_applied 记录。

- [ ] **Step A1.1（RED）** 追加测试（fixture 行取自 469429f4 提交信息中的实测隔离证据格式）：

```python
# ---------- OBS-FIX-5 port: cache Field-series injection lines (C04-C09) ----------
# 沿用本文件既有约定：C = lsu_obs_core 模块，FUNNEL 为既有触发行 fixture
FIELD_FIXTURE_LINES = [
    "Tick: 1000000, Cache Block Addr: 576640, Field: tag (F5 alias), old_tag=0x23 -> new_tag=0x0",
    "Tick: 1000001, Cache Block Addr: 576640, Field: valid (invalidate)",
    "Tick: 1000002, Cache Block Addr: 576640, Field: data_shift (C09 rotate by 1 byte)",
    "Tick: 1000003, Cache Block Addr: 576640, Field: dirty (toggle bit 3)",
]

def test_cache_field_inj_lines_parse_to_l0_fault_applied():
    """用户义务：证明 C04-C09 类型日志可形成合法 L0 fault_applied 记录。"""
    l0 = C.parse_l0(FUNNEL + "\n030921682b3731f2\n",
                    "\n".join(FIELD_FIXTURE_LINES) + "\n")
    assert len(l0["injections"]) == 4                      # 四格式全解析
    assert l0["injections"][0]["tick"] == 1000000
    assert l0["injections"][0]["dynamic_target"] == "cache_block"  # Field 系记录族
    # 无未解析行（injection_line_unparsed==0，即 finalize 不会拒绝）
    # 具体字段名（如 field/old_tag/new_tag 子键）以 cherry-pick 后 469429f4
    # 的实际记录结构为准，断言逐字段还原 spec（tag 行含 old/new 明细）。
    # Byte Offset 原格式不回退：既有用例（Byte Offset fixture）保持全绿。
```

（`C.parse_l0(funnel_text, inj_log_text)` 与 `FUNNEL` 均为 `tests/test_lsu_obs_core.py` 既有符号——:123 `C.parse_l0(FUNNEL + …, real_inj_line() + …)` 实测模式；Field 子键名执行时对照 pick 后代码补精确断言。）
- [ ] **Step A1.2** 运行确认 RED（Field 行不被现行 `_CACHE_INJ_RE` 解析）。
- [ ] **Step A1.3** `git cherry-pick 469429f4`（在 worktree 分支上）。
- [ ] **Step A1.4** GREEN：Field 四格式全解析 + Byte Offset 回归全绿；全套件 `python3 -m pytest tests/test_lsu_obs_core.py tests/test_lsu_obs_driver_workers.py -q` exit 0。
- [ ] **Step A1.5** commit 测试文件（`[LSU][MDSPEC][A1] OBS-FIX-5 移植验证测试：C04-C09 Field 行→合法 L0 fault_applied`）并 push。

### Task A2: 移植 dd6714c4（reclass_v2，原样入库）

**Files:** Create（经 cherry-pick）`tools/lsu_reclass_v2.py`（+422 行，独立新文件）

- [ ] **Step A2.1** `git cherry-pick dd6714c4`（无依赖，先于 AddrPath 链）。
- [ ] **Step A2.2** 冒烟：`python3 tools/lsu_reclass_v2.py --help` exit 0；若有旧 P4 批次数据（runs/ 只读）跑一次 `--dry-run` 验证守恒输出格式（只读纪律：不写 runs/）。
- [ ] **Step A2.3** 回归：全套件绿；push。（适配改造在 Task A5。）

### Task A3: 移植 83ff9265（AddrPath 链 1/3）

**Files:** Modify（经 cherry-pick）`CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/{.cc,.hh,.py}`、`configs/se/lsu_proxy.py`、`tools/lsu_campaign.py`

- [ ] **Step A3.1** `git cherry-pick 83ff9265`（worktree 分支）。
- [ ] **Step A3.2** 重建（-j126 增量）零新警告；记录 gem5.opt sha256。
- [ ] **Step A3.3** 行为验证（暂按其原语义，A6 将改造）：跑一个 store-only 小样本（`--agu_pre_mode a06s_store_size --agu_size_to 2`，`workloads/directed/sq_forward`，n=2）确认注入行含 `isLoad/isStore/reject_reason` 且 load 候选产生 REJECT 日志；`a06_size` 字符串被 lsu_proxy 拒绝（config-time error）。
- [ ] **Step A3.4** 全套件回归 + push。

### Task A4: 移植 35ccda91（GEOM）+ 分布守恒测试（Review Focus #5）

**Files:**
- Modify（经 cherry-pick）`CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/{.cc,.hh}`
- Test: `tests/test_lsu_geom_distribution.py`（新建）

**Interfaces:** 产出 `obs_post_geomreject` 计数（phantom decline 不计 injected）；`a04/a08` 翻译位翻转的 64B 合法性检查 + 固定位一次检查/随定位 16 次重采样。

- [ ] **Step A4.1（RED）** 新建 `tests/test_lsu_geom_distribution.py`：
  - 用固定 rngSeed 的合成 EA 位翻转向量（含同 64B 行内翻转与跨行翻转各若干）跑 GEOM 判定纯函数（若 cherry-pick 后判定逻辑在 .cc 内不可独立调用，则以真实 gem5 小跑 + 日志统计替代：两种 mode 各 n=2），断言：① 跨行位被拒斥且 `obs_post_geomreject` 递增；② 同行位全部按原分布注入（**A01/A02 目标分布逐位不变**）；③ 拒斥行含真实 mode 标签。
- [ ] **Step A4.2** `git cherry-pick 35ccda91`；重建零警告。
- [ ] **Step A4.3** GREEN + 真实小跑（`a04_subst` 模式，`workloads/directed/agu_addrmodes`，n=2）：日志中 geomreject 可见、无分布漂移；`a01`（`low_bit_flip`）n=2 注入 old/new EA 与移植前基线一致（用 A0.3 golden 同 seed 对照）。
- [ ] **Step A4.4** 全套件回归 + push。

### Task A5: 移植 dd755d7e（F6）+ F6 单语义门禁 + reclass 适配（Review Focus #3/#4）

**Files:**
- Modify（经 cherry-pick）`CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/{.cc,.hh,.py}`、`configs/se/lsu_proxy.py`；随后 Modify `tools/lsu_campaign.py`、`tools/lsu_reclass_v2.py`
- Test: `tests/test_lsu_f6_gate.py`（新建）、`tests/test_lsu_reclass_v2_adapt.py`（新建）

**Interfaces:** `f6Mode` 参数（`early_stress` 默认 | `steady_state` 显式）；campaign 级 `track=mdspec` 门禁函数 `assert_formal_f6_mode(mode)`；reclass 适配输出含 `evidence_status`。

- [ ] **Step A5.1（RED）** `tests/test_lsu_f6_gate.py`：

```python
import pytest, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

def test_formal_track_rejects_steady_state():
    import lsu_campaign as lc
    with pytest.raises(SystemExit):
        lc.assert_formal_f6_mode("steady_state")   # 正式 track 拒绝

def test_formal_track_accepts_early_stress():
    import lsu_campaign as lc
    assert lc.assert_formal_f6_mode("early_stress") is None  # 规格 F6 语义

def test_f6_default_is_early_stress():
    """规格 F6 = 首次出现指定事件时注入一次；默认必须落在该语义。"""
    import lsu_campaign as lc
    assert lc.F6_DEFAULT_MODE == "early_stress"
```

- [ ] **Step A5.2** RED 确认（函数不存在）。
- [ ] **Step A5.3** `git cherry-pick dd755d7e`；重建零警告。在 `tools/lsu_campaign.py` 增 `F6_DEFAULT_MODE = "early_stress"` 与 `assert_formal_f6_mode()`（mdspec track 下非 early_stress → SystemExit，理由写入 stderr）；GREEN。
- [ ] **Step A5.4（reclass 适配，独立 commit）** `tests/test_lsu_reclass_v2_adapt.py`：

```python
def test_missing_evidence_yields_unknown_not_masked():
    """用户二.5：链路缺失必须标 Unknown，不得推断 Masked。"""
    # 构造：injected>=1 且传播链在 L2 后无事件（evidence_status=missing）
    # 断言：适配输出 outcome=Unknown, evidence_status=missing, rule_version="2"
    ...

def test_reclass_output_carries_version_and_readonly():
    # 断言：每条移动记录含 rule_id/证据文件/原新类别；对 runs/ 无写
    ...
```

RED → 在 `tools/lsu_reclass_v2.py` 增适配层（输出结构含 `evidence_status`；缺事件→`Unknown`）→ GREEN。
- [ ] **Step A5.5** 全套件回归 + push（F6 提交与适配提交分开）。

### Task A6: A06 安全化改造（§2 裁决落地；Review Focus #2）

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.cc`（模式名反转）、`configs/se/lsu_proxy.py`（choices）、`tools/lsu_campaign.py`（A06 条目 + BLOCKED）
- Test: `tests/test_lsu_a06_ruling.py`（新建）

**Interfaces:** 合法模式名 `a06_size`（store-only 安全路径 + load 候选 REJECT 日志）；`a06s_store_size` 为 config 层拒绝别名；campaign `A06` 条目状态 `BLOCKED`。

- [ ] **Step A6.1（RED）** `tests/test_lsu_a06_ruling.py`：

```python
def test_a06_mode_name_is_legal_and_store_only():
    import lsu_campaign as lc
    family, extra = lc.MODEL_FLAGS["A06"]                 # 既有表（:109）
    assert family == "addrpath"
    assert "--agu_pre_mode" in extra and "a06_size" in extra   # 规格模型名承载安全路径
    assert "A06" in lc.MODEL_BLOCKED                       # 既有 BLOCKED 机制（:185/215）

def test_a06s_runid_family_absent():
    import lsu_campaign as lc
    assert not any(m.startswith("A06S") for m in lc.MODEL_FLAGS)   # 无 A06S 模型 ID
    assert not any(m.startswith("A06S") for m in lc.MODEL_BLOCKED)

def test_a06s_alias_rejected_at_config(subprocess_gem5):
    """旧别名必须在 config-time 被拒（83ff9265 对 a06_size 的拒绝逻辑反转到 a06s_store_size）。"""
    # subprocess：worktree gem5.opt + lsu_proxy.py --agu_pre_mode a06s_store_size …
    # 断言：非零退出 + stderr 含 a06s_store_size 拒绝说明（模式与 83ff9265 的
    # config-time 拒绝相同，仅对象反转）。
    ...

def test_no_a06s_runid_in_map():
    # B1 完成后：325 RunID 无 A06S-*；A06-* 6 条均 status=BLOCKED（§2.d）
    ...
```

- [ ] **Step A6.2** RED 确认 → 改造（一个 commit）：① `.cc`：现 `a06s_store_size` 分支改名 `a06_size`（保留 store-only + REJECT 日志 + isLoad/isStore/reject_reason）；删除"retired a06_size"空壳块；新增 `a06s_store_size` 一次性 warn + REJECT（防旧 manifest 误用）。② `lsu_proxy.py`：choices 含 `a06_size`、拒 `a06s_store_size`。③ `lsu_campaign.py`：`A06` 条目指向 `a06_size` + `MODEL_STATUS["A06"]="BLOCKED"`（理由注释引用 §2）；删除 `A06S` 条目。④ 重建零警告。
- [ ] **Step A6.3** GREEN + 真实小跑（`a06_size` store-only，sq_forward，n=2）：store 注入行正常、load 候选 REJECT 日志在案。
- [ ] **Step A6.4** 全套件回归 + push。**A06 裁决状态记录**：BLOCKED（load 侧 + byte-enable 待 §2.c spike）。

### Task A7: Phase A 门禁（构建 + 全量回归 + 覆盖矩阵基线快照）

- [ ] **Step A7.1** worktree 内全套件 + `pytest tests/ --collect-only` 对照 + `manifest_validate --help` + 无注入 golden 复跑（与 A0.3 二进制哈希一致或差异可解释）。
- [ ] **Step A7.2** 记录 Phase A 完成态：HEAD、gem5.opt sha256、移植清单（6 提交 + 2 改造）、测试计数。写入计划文件进度节并 commit。

---

### Task B1: RunID 机读映射生成器（用户三.1）

**Files:**
- Create: `tools/lsu_runid_map.py`
- Test: `tests/test_lsu_runid_map.py`

**Interfaces:** `generate_map(xlsx_path: Path) -> dict`：每 RunID 一条 `{run_id, model_id, unit, freq, fault_type, submodels, trigger, workload:{name,spec_id}, injection_point, path_nodes[L0..L5], monitors[], correlation_keys[], missing_hooks[], result_fields[], status}`；CLI `--xlsx <p> --out <json>`；输出 `docs/gem5-fi/lsu/mdspec/runid_map.json`。

- [ ] **Step B1.1（RED）** 测试：用主 xlsx 生成 → 325 条、RunID 唯一、表 7∩表 9 集合相等、每条含上述全部键、A06-* 6 条 status=BLOCKED、无 A06S-*；快照关键字段（model_id/unit/freq/workload）与表 7 逐行相等。
- [ ] **Step B1.2** 实现（openpyxl 读表 6/7/9/10/11 联结；workload 名→路径映射表内置：AGU-AddrModes→workloads/directed/agu_addrmodes 等 10 项，未命中报错不猜）→ GREEN。
- [ ] **Step B1.3** 生成 `runid_map.json` 入库 + commit + push。

### Task B2: 覆盖矩阵与统计（deliverable 3 的精确化）

**Files:**
- Create: `tools/lsu_coverage_matrix.py`（读 runid_map.json + 钩子可用性清单 → PASS/PARTIAL/BLOCKED）
- Test: `tests/test_lsu_coverage_matrix.py`

- [ ] **Step B2.1（RED）** 测试：基线（Phase A 后、钩子未装）统计必须为 **PASS=0**（部分已有≠PASS——Review Focus #1）；A06 6 条 BLOCKED；85 需新增全 BLOCKED；240 部分已有全 PARTIAL；输出含 per-unit/per-hook-family 分解。
- [ ] **Step B2.2** 实现：status 判定 = `model_implemented AND hooks_available AND fields_complete AND not ruling_blocked`；钩子可用性来自显式注册表（H1–H7 逐族在装好后翻转）。→ GREEN。
- [ ] **Step B2.3** 生成 `docs/gem5-fi/lsu/mdspec/coverage_matrix.md`（325 行 + 统计表）入库 + commit + push。

### Task H0: CHAOSPropagation 表 11 字段扩展（横切，先于 H1–H7）

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.{cc,hh,py}`
- Test: `tests/test_lsu_prop_fields.py`（解析侧）+ 真实日志冒烟

**Interfaces:** 统一事件行 schema（表 11 全 24 字段；缺失字段输出空值不省略；`evidence_status` 缺省 `observed`）：

```
PROP-EVT: run_id sample_run_id fault_id event_id parent_event_id tick cycle core_id
thread_id dyn_inst_seq commit_seq pc opcode lq_idx sq_idx request_id walk_id mshr_id
fill_id pf_request_id va pa cache_line set way entry_index field before after
state_before state_after arch_reg phys_reg detection_layer contained outcome
oracle_diff evidence_status
```

- [ ] **Step H0.1（RED）** 测试：构造含全字段的合成行 → 解析器逐字段还原；缺字段行 → 空值 + `evidence_status` 语义保留；**Unknown 语义测试**（Review Focus #3 关联）：链断于 L2 → 离线链检查输出 `provable_to=L2, beyond=Unknown`（不得输出 Masked）。
- [ ] **Step H0.2** 实现 .cc/.hh/.py（字段注册表 + 发射/解析同源，参照现有 addrpath 家族行格式扩展）→ 重建零警告 → GREEN。
- [ ] **Step H0.3** 真实冒烟：agu_addrmodes + a01 注入 n=1，PROP-EVT 行含新字段 → commit + push。

### Task H1–H7: 七个钩子族（每族一个任务单元，统一模式）

**统一 Files/模式**（每族按此执行，源锚点与新增内容见 §3 表）：
- Modify: 该族源锚点文件 + 新建 `CHAOS/gem5/src/…/CHAOS<X>Trace.{cc,hh,py}` + `SConscript` 注册 + `configs/se/lsu_proxy.py` 挂载开关 + `tools/lsu_campaign.py` 路由
- Test: `tests/test_lsu_hook_<family>.py`（合成日志行 → H0 schema 解析 → 字段断言）+ directed 真实小跑（该族代表 RunID n=2）
- 统一步骤：**RED（测试先行，合成行含该族全部必录字段）→ 实现（self-attach SimObject，四件套，参照 CHAOSFreeList 骨架；事件经 H0 emitter 发射）→ 重建零警告 → GREEN → 真实小跑链检查 → 覆盖矩阵钩子注册表翻转该族 → commit + push**
- 每族必录字段（来自表 9 必监控列）：H1 = lq_idx/sq_idx/PC/opcode/event_id/parent_event_id（lsq.cc pushRequest + sendFragmentToTranslation）；H2 = VA/ASID/hit/way/walk_id/PPN/PA/权限/页大小/fault（tlb.cc + table_walker.cc）；H3 = sq_idx 生命周期 + state_before/after（insertStore/executeStore/checkViolations/writebackStores/commit-drain）；H4 = request_id/PA/line/set/way/hit/miss/mshr_id/fill_id/响应hash（cache.cc 六函数）；H5 = pf_request_id 全链 training→queue→request→fill→demand（stride/queued/base）；H6 = 原子 locked read/write monitor + atomic Request/Packet + SWAP（isa.cc）；H7 = lq_idx 生命周期（insertLoad/read/checkViolations/completeDataAccess/replay）。
- [ ] H1（39 RunID 解锁基础；**pilot A01-F0-W3 依赖，最先做**）
- [ ] H2（39；pilot 依赖）
- [ ] H7（30；LQ）
- [ ] H3（63；SQ）
- [ ] H4（73；cache——与 469429f4 解析衔接：C04-C09 注入行 → fault_applied → delivery 事件）
- [ ] H5（53；prefetch）
- [ ] H6（28；atomic）
- [ ] 每族完成后 `tools/lsu_coverage_matrix.py` 再生成 + 统计更新 commit。

### Task B9: 覆盖矩阵终版（Phase B 出口）

- [ ] **Step B9.1** 七族全装后重生成矩阵：输出 PASS/PARTIAL/BLOCKED 精确计数（含 A06 6 条 BLOCKED 与 85→剩余 BLOCKED 的变化）；与 §3 基线对照写入差异说明。
- [ ] **Step B9.2** 入库 + commit + push。**Phase B 出口门禁**：pilot 依赖的 A01-F0-W3 相关钩子族（H1/H2/H0）必须 PASS。

---

### Task C1: Pilot 准备（golden + 链完整性检查器）

**Files:**
- Create: `tools/lsu_chain_check.py`
- Test: `tests/test_lsu_chain_check.py`

**Interfaces:** `check_chain(events_jsonl: Path, spec_nodes: list) -> dict`：按规格表 9 判定列实现——每条边由共享复合键 + 时间/可达性同时证明；输出 `{edges: {L0→L1: proven|missing, …}, terminal: {verdict: full|provable_to_Ln_then_unknown|detected_contained|squash_replay_masked, evidence: …}}`；**缺边 → Unknown，绝不 Masked**。

- [ ] **Step C1.1（RED）** 测试：合成事件流三例（全链 / 断于 L2 / 检测 contained）→ 三种 terminal 判定；断链例必须输出 Unknown（Review Focus #3 钉死）。
- [ ] **Step C1.2** 实现 → GREEN → commit + push。
- [ ] **Step C1.3** A01-F0-W3 golden（无注入，agu_addrmodes，O3）产出 oracle 基线与无故障事件流。

### Task C2: Fault Pilot（A01-F0-W3，n≤5 activated，workers=1）

- [ ] **Step C2.1** 运行：`lsu_proxy` + `a01`（low_bit_flip 族，F0，触发=任一已完成地址生成）× ≤5 activated 样本，串行；产物只写 worktree runs/。
- [ ] **Step C2.2** 链验证：`lsu_chain_check.py` 对每样本 → L0→L1→L2→L3→L4→L5 逐边 proven（H1/H2 钩子在案）；before/after 指标逐单元在案；first divergence 定位（commit_seq/PC）；终局 = 五类之一 + 证据 + `evidence_status`。
- [ ] **Step C2.3** 指标变化验证：golden 对照（A0.3/C1.3）显示注入前后相关单元指标差异可观测。
- [ ] **Step C2.4** 全部通过 → pilot 报告 `docs/gem5-fi/lsu/mdspec/pilot_A01-F0-W3.md`（含真实输出引用）commit + push。任一失败 → systematic-debugging，不得放宽口径。

### Task C3: Phase C 出口门禁与 Phase D 提案骨架（不启动）

- [ ] **Step C3.1** 门禁核对：pilot 全链 PASS、A06 裁决状态明确（BLOCKED 及理由）、覆盖矩阵终版、构建/测试/资源门禁全绿——逐项写入计划进度节。
- [ ] **Step C3.2** Phase D 提案**骨架**（仅文档，明确标注"未批准不执行"）：325 RunID 分批建议序（按钩子族解锁顺序 + BLOCKED 项排除）、385 activated/RunID 口径、保守并发策略、产出与回填约定。
- [ ] **Step C3.3** 计划文件收官 commit + push。**正式 campaign 保持未启动。**

---

## 执行注意事项

- **cherry-pick 源**：`capacity/lsu-slots-24-20261014`（469429f4）与 `fix/lsu-p4-simfail-20261015`（其余）；integration/lsu-p4-20261016 仅作参考不合并。
- **gem5 源路径**：钩子锚点均指 vendored 树 `CHAOS/gem5/src/…`（唯一会构建的源）；顶层 `CHAOS/<Name>/` 陈旧副本不碰。
- **规格活变动**：xlsx 是活文档——每 Phase 前的 `--validate` 若 FAIL（源 SHA 漂移），停下向用户报告，不得自行再生成规格文档。
- Phase B 钩子族任务的执行者须先读表 9 对应单元行全文（`docs/gem5-fi/lsu/…-09-逐RunID传播监控.md`）——必录字段以规格原文为准，本计划 §3 表为摘要。
