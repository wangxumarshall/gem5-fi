# R6-A-DIAG-C：A07 / A08（AGU）只读诊断

- 诊断者：Lane C 只读 subagent；日期 2026-10-28
- 分支 `fix/r6-a-unit-20261028`，HEAD `eab58f35`（权威起点 `659fa4cf`）
- 二进制 `CHAOS/gem5/build/ARM/gem5.opt`
  - 实测 `sha256sum` = `3db54541b7fbafa47d27ab7a3f71b8c777c2893501078f3eb36fddb91cd866c2`
  - `binary_source_head` = `1f344a5b66da30267c578536e00a1ad4ad56bb31`（`ls -l`：1145678496 bytes，10月28日 10:01）
  - `strings -a` 实测含 A07/A08 标记：`a07b_ready_delay`、`a08_subst`、`, Site: iew_memRef_AGU_ready`、`, Site: iew_memRef_AGU_ready_resume`，以及 panic 串
    `CHAOSAddrPath: agu_ready_mode requires --addrpath_lsu_tier (A07 is LSU-trigger-native; the legacy cycle-window path is not offered at the ready hook)`。
  - **A07-a / A07-c 不在二进制**（`strings | grep -E "a07a|a07c|ready_early|ready_loss"` 仅命中 CHAOSIQ 的 `mode=ready_early`@`Site: iq_insert`，属 I 系列 IQ 模型，见 `CHAOS/gem5/src/cpu/o3/CHAOSIQ/CHAOSIQ.cc:707`，与 AGU 无关）。
- 只读约束遵守：未构建、未启动 gem5、未改任何 T 单元/旧证据文件；仅新增本文件。

---

## 0. 权威源一致性（先给结论）

| 来源 | A07 | A08 |
|---|---|---|
| `docs/gem5-fi/lsu/mdspec/coverage_matrix.md:38-49` | PASS（F0/F4/F6 × W3/W5） | PASS（F0/F2/F6 × W3/W5） |
| `runid_map.json`（同文件 `entries`） | `status=PARTIAL`；`spec_landed` 非空（仅 a07b） | `status=PARTIAL`；`spec_landed=""`；`impl_status`=“部分已有（注入近似：当前a08_subst不能证明错误load/store端口路由；传播仍缺）” |
| `R6-STATUS-TABLE.md:80-91` | 12 格（A07+A08）全部 `NOT_RUN / RUNNABLE`，权威 runs 根内无 prop_evt 流 | 同左 |
| `lsu_campaign.MODEL_BLOCKED` | A07 条目已删除（`tools/lsu_campaign.py:923-930`） | A08 从不在 `MODEL_BLOCKED`（实测 `'A08' in MODEL_BLOCKED == False`） |

**关键口径分歧（必须记住）**：`coverage_matrix.md` 的 PASS 是“**节点级**证据（kind 并集，见其表头判定口径）”得出的，且证据取“全部 pilot 的 kind 并集”。它 **不等于子模型语义落地**。A07 只有 a07b 落地、A08 只有近似 `a08_subst`，两者在 `runid_map` 都是 `PARTIAL`。不要把 coverage_matrix 的 PASS 当作“模型完整”的依据。

---

## 1. A07：AGU address-ready 握手 / EA 流水锁存（时序）

### 1.1 源码 cross-check：clean hook 到底有没有？（回答“不得只信旧标注”）

旧标注 `mode_unimpl_plan.md:22` 写 `A07 | 6 | R4: no clean hook`，但当前源码**确实已有 clean ready hook**，且该旧标注已被 R4-5.8 证伪：

- 钩子点 = `IEW::executeInsts` 的 `isMemRef()` 分支（ready/handshake 点，EA 尚未产生）：
  - `CHAOS/gem5/src/cpu/o3/iew.cc:1194-1218`：`if (inst->isMemRef()) { DPRINTF(IEW, "Calculating address ..."); ... if (cpu->chaosAguReady && cpu->chaosAguReady->maybeDelayAguReady(inst)) continue; }`
  - `maybeDelayAguReady` 返回 true 时跳过本拍常规执行路径，由 `aguResumeEvent` 在延迟拍再入 `IEW::chaosAguResumeInst`（`iew.cc:1412-1483`），逐字镜像 `executeInsts` 的 load/store/atomic 分派与 squash 处理。
- 注入器实现：`CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.cc:852-952`（`maybeDelayAguReady`）、`964-984`（`resumeDeferredAgu`）。
- 配置面：`CHAOSAddrPath.py:105-110`（`aguReadyMode=off|a07b_ready_delay`，`aguReadyDelayCycles>=1`，默认 1 = spec“延后1周期”）。
- 自校验/响亮拒绝：`CHAOSAddrPath.cc:43-59`——`agu_ready_mode!=off` 时要求 `lsuTier!=off`、且与 `preMode` 互斥（W1-⑦ 单钩子/次），delay>=1。
- CPU 接线：`cpu.hh:522-523` `chaosAguReady`；`cpu.hh:510-515` `chaosAddrPath`/`chaosAddrPathPre`。
- 触发层：`chaos_lsu_trigger.hh:44`（`enum ChaOSLsuTier {F0..F6}`），A07 ready 钩子的 attempt/eligible/F6 源在 `CHAOSAddrPath.cc:862-901`（F6 = 第九事件源，见 `chaos_lsu_trigger.hh:94-108`）。

**结论：A07 “no clean hook” 旧标注已失效；clean ready hook 存在且可审计。** 但“hook 存在”≠“全部子模型落地”——见下。

### 1.2 逐子模型状态

| 子模型 | spec（07 展开矩阵 :38-41 末列） | 实现状态 | 证据 |
|---|---|---|---|
| A07-a ready 过早并读旧 EA | 提前 1 周期置 ready 读旧锁存 EA（**SDC 通道**） | **NOT_IMPLEMENTED** | 源码/二进制均无 a07a（`grep a07a` 仅注释）；`CHAOSAddrPath.hh:93-97`、`.py:101-104` 明写“pending/two-point implementation”；`lsu_runid_map.py:405-407` pending 列表 |
| A07-b ready 延迟 | 延后 1 周期（数据载荷保持正确，仅时序移动） | **IMPLEMENTED + ROUTED**，旧 pilot 已证；本轮未跑 | `CHAOSAddrPath.cc:852-984`；`lsu_campaign.py:381-382`（`--agu_ready_mode a07b_ready_delay --agu_ready_delay_cycles 1`）；`ADDRPATH_F0_SPAN`（`lsu_campaign.py:1095-1096`）=2795/2579 |
| A07-c ready 丢失 | 丢失一次 ready（hang/Timeout 通道） | **NOT_IMPLEMENTED** | 同 a07a 注释；需要超时簿记（L04-a 同类），无超时/丢失代码路径 |

### 1.3 触发语义与频率

- **F0**：locality-correct uniform over eligible events。A07 特判在 `tools/lsu_campaign.py:1107-1113`：`--addrpath_lsu_tier F0 --addrpath_warmup_events 1 --addrpath_span_events <measured span>`，span 来自 `ADDRPATH_F0_SPAN[(A07,binary)]` = `agu_addrmodes:2795` / `sq_forward:2579`（census 实测，源码注释 `lsu_campaign.py:1084-1096`）。
- **F4**：**已有路由**（走 `_addrpath_tier_flags` 的 else 分支 `lsu_campaign.py:1114-1117`：`--addrpath_lsu_tier F4 --addrpath_warmup_events 0 --addrpath_span_events 1000`，span 对 F4 无意义）。但 F4 语义在 `chaos_lsu_trigger.hh:212-216`：`intervalEvents(F4)=100000`，`scheduleNext` 首个 fire ≥ `iv/2=50000` eligible events，burst `2+rng%3`（2-4 连发，`:278-288`）。
  - **A07 的 eligible 流只有 2795 / 2579 ≪ 50000 ⇒ A07-F4-W3/W5 在本负载上结构性不可能 fire**（honest zero）。这与 `runid_map` spec_landed 的记载一致（旧 pilot F4 三 seed 全 0 events）。
  - **缺口**：`LSQFWD_INTERVAL_UNREACHABLE`（`lsu_campaign.py:1226-1272`）只对 **lsqfwd** 家族生效；`_addrpath_tier_flags` **没有** interval-reachability 拒斥。因此 A07-F4 会以“可跑”解析并安静地产出 activated=0（无 `SPAN_UNREACHABLE` 告警，该告警只在 F0 分支打印，`chaos_lsu_trigger.hh:376-406`）。这是应当补的响亮门禁（参照 S10-F2 的 `BLOCKED(interval-tier-unreachable)` 处理）。

### 1.4 ready 延迟/丢失对 oracle 判定的影响

- **延迟（a07b）**：resume 在延迟拍重入同一执行路径，数据载荷正确；squash 语义安全——`chaosAguResumeInst` 对 `isSquashed()` 的处理与 `executeInsts` 相同（`iew.cc:1415-1422`：置 executed/canCommit，不执行 AGU），延迟窗内被 squash 时故障诚实记为 Injected-not-activated（`CHAOSAddrPath.cc:957-963`）。功能模拟下纯时序平移**不应改变架构值** ⇒ `agu_addrmodes`/`sq_forward` 的 FNV 校验和 oracle 应与 golden 相同 ⇒ 判定为 **Masked**（数据无 SDC）。旧 pilot `sdc=0`（`round4_findings.md:1271-1277`）与此一致。**即：a07b canary 能证明“路由/激活”，但按构造不可能产出 SDC。**
- **提前+旧 EA（a07a，未实现）**：才是 SDC 通道（复用上一条 EA，改变实际访问地址）——需要 EA 流水锁存值观测 + 值替换的“两点实现”，当前没有。
- **丢失（a07c，未实现）**：会走 hang/Timeout 通道（需要超时簿记），oracle 判定是 Timeout 而非 SDC。

### 1.5 触发条件诚实性

A07 spec 触发 = “连续相关访存”。源码明确自认**未做真正数据依赖门控**：`CHAOSAddrPath.cc:864-873` 注释——“a true data-dependency gate needs producer tracking the ready point does not expose … honest registration, C11's same-page proxy class”。即当前鉴权 = op-class 过滤（plain load/store，排除 atomic/prefetch，`:874-879`）+ 负载选择代理。这点必须在传播文档如实登记。

---

## 2. A08：请求类型/端口路由 + 同周期 EA 互换（换值）

### 2.1 当前 a08_subst 到底是什么

`CHAOSAddrPath.cc:585-595`：
```
if (pre_mode == "a04_subst" || pre_mode == "a08_subst") {
    const Addr page = addr & ~(Addr)0xFFF;
    Addr cand;
    do { cand = page | ((Addr)(rng() % 256) << 4); } while (cand == addr);
    addr = cand;
}
```
即：在**同一个 4KiB 页内**把请求 vaddr 换成另一个 16B 对齐、不等于原值的地址。这是 A04 的“同页代理”换值，**既不改变请求的 load/store 通道，也不做同周期两条请求的 EA 互换**。

- `runid_map` A08 `spec_landed=""`、`impl_status` 明写“当前 a08_subst 不能证明错误 load/store 端口路由；传播仍缺”。
- `lsu_campaign.py:374` 路由：`"A08": ("addrpath", ["--agu_pre_mode", "a08_subst"])`。
- 钩子点 = `LSQ::pushRequest` 入口（`lsq.cc:793-826`，PRE hook）。

**结论：A08-a 与 A08-b 均未按 spec 语义实现；现有的是一个已路由、可运行的“同页地址换值”代理。**

### 2.2 请求身份 / 配对可行性（回答“身份是否可获取、配对是否可实现”）

可用身份（均在 `pushRequest` 可见）：
- `inst->seqNum`（dyn seq）、`inst->lqIdx`（load）/`inst->sqIdx`（store）（`lsq.cc:847-856` 已写入 `lsq_push` 事件）；
- `isLoad` 布尔（`pushRequest` 形参）；
- 真正 `Request` 级 `request_id`：同一请求在 L3 事件里用 `request->id`（`lsq_unit.cc:1574-1588` 对 lq_read 写 `request_id`；forward 键也有 `store_request_id`/`load_request_id`，`lsq_unit.cc:1801-1807`）。

同周期配对的结构性障碍：
1. **Request 在 hook 之后才构造**：PRE hook 修改 `addr/size`（`lsq.cc:800-802`），随后才 `new SingleDataRequest/SplitDataRequest`（`lsq.cc:887-933`）并 `initiateTranslation()`（`:933`）。也就是说，请求 #1 在 pushRequest 返回时已构造并已发起翻译/可能已读，**事后无法安全交换两条请求的 EA**。
2. 若要做“同周期两条请求 EA 互换”，必须在两条请求都尚未构造/翻译前持有缓冲（需单/双槽 stash + 同 tick 判定 + 第二拍回填），等价于给 LSU 增加一个两拍缓冲——会改变发射时序，且与 A07 的单槽纪律（C12）、以及 store 的 data/byte_enable 强耦合。
3. **通道路由（A08-a）本身是内建的**：`IEW::executeInsts` 以 `inst->isLoad()/isStore()/isAtomic()` 分派 `executeLoad/executeStore`（`iew.cc:1220-1255`），`LSQUnit::insert()` 以 `isLoad()` 选 `insertLoad/insertStore`（`lsq_unit.cc:409-419`）。把 load 强行走 store 通道会违反 `executeStore` 的 `assert(storeQueue.size()!=0)`（`lsq_unit.cc:784`）与 store 完成合同（byte_enable/data），高危断言/崩溃；spec 自己也写“非法路由多触发断言”（07 矩阵 :44）。

**可行性结论**：
- **A08-b（同周期 EA 互换）**：身份可获取（seq/lqIdx/sqIdx/request_id 都有），但**配对需新增两点/缓冲实现**，不能在现有 PRE hook 内原地完成；属可设计、非平凡。
- **A08-a（错误通道）**：路由点可定位，但“错通道”在 O3 的 load/store 分离结构里**大概率直接断言崩溃**，难以形成合法“被下游消费”的 activated 事件；资源泄漏/死锁风险高（写入错误队列后位宽/掩码/完成合同不匹配）。建议作为“可能只产出 Crash/断言”的高风险模型，单独裁决。

### 2.3 触发密度（静态指令混合，不运行）

spec 触发 = “同周期存在 load 与 store”。`agu_addrmodes.c` 的访存序列（`workloads/directed/agu_addrmodes.c:31-58` 等）与 `sq_forward.c`（`workloads/directed/sq_forward.c:22-48`）都是**紧密的 load/store 交替/成对**（store-then-load 转发、LDP/STP 成对、interleaved store/load pairs）。O3 每拍可发射/执行多条访存，因此“同周期存在 load 与 store”的**静态可达密度很高**（连续 store→load 相邻指令即可同拍窗口）。但“同周期”取决于运行时发射窗口，静态只能断定“高概率可满足”，不能给精确计数（不运行 ⇒ 记 UNKNOWN 精确值）。旧 trial（非权威）A08-F0 的 `attempted≈12.8k–13.9k` 可作为流长量级参考（见 §4）。

### 2.4 频率语义与可到达性

- **F0**：`_addrpath_tier_flags` 走到 else 分支（A08 非 A07），即 `--addrpath_lsu_tier F0 --addrpath_warmup_events 0 --addrpath_span_events 1000`（`lsu_campaign.py:1114-1117`）。span=1000 是家族默认“F0-uniform 近似”（注释 `:1104-1106`）。**A08 的 F0 span 未按 (model,workload) 实测**（`ADDRPATH_F0_SPAN` 只有 A07 两行）。后果：A08 流长约 1.3e4 ≫ 1000，会触发 `EARLY_BIAS` 告警（`chaos_lsu_trigger.hh:390-406`，`eligible >= draw_end`），即注入偏向流前段——属“early bias”近似，formal 前应补 A08 的 span 实测。
- **F2**：**已有路由**（else 分支给 `--addrpath_lsu_tier F2`）。语义 `intervalEvents(F2)=100000`，首 fire ≥ 50000（`chaos_lsu_trigger.hh:212-225`）。旧 trial 实测 A08 eligible 流 ≈1.28e4–1.39e4（见 §4），**50000 > 流长 ⇒ A08-F2-W3/W5 结构性 zero**，且 addrpath 家族**没有** interval 拒斥门禁 ⇒ 会安静产出 activated=0（无告警）。与 A07-F4 同类问题。

---

## 3. 频率语义小结（F0/F2/F4）

- **定义源**：LSU track 用 `chaos_lsu_trigger.hh`（事件归一化），**不是** `chaos_trigger.hh`（后者是 OoO track、周期归一化，且枚举只有 F0/F1/F2/F3/F5，无 F4/F6——`chaos_trigger.hh:23-26`，两 track 不可混用，见 `chaos_lsu_trigger.hh:1-6`）。
- **F0**：warm-up 后 eligible 事件流上均匀抽 1 次（`chaos_lsu_trigger.hh:257-268`）。
- **F2**：每 ~100000 eligible events ±50% 抖动（`intervalEvents=100000`，`:212-225`）。
- **F4**：每 100000 eligible 触发一次，连续污染 2-4 个（`:215,278-288`）。
- **A07 有 F0/F4，A08 有 F0/F2**；F4/F2 **都已路由**（`_addrpath_tier_flags`）；但两者对 W3/W5 短定向负载都**结构性不可达**（见 §1.3、§2.4）。
- `lsu_freq_policy`：`docs/gem5-fi/lsu/mdspec/R6-FREQUENCY-POLICY.md/.json` 与 `tools/lsu_*` 的 tier 契约一致（F0-F6 事件归一化）；本轮未发现 A07/A08 的频率定义与策略冲突。

### 3.1 W3 / W5 负载与 oracle 可判定性

| W | 负载 | binary | golden（`lsu_campaign.GOLDENS`） | oracle |
|---|---|---|---|---|
| W3 | AGU-AddrModes（base+imm/index/LSL/UXTW/SXTW/pre-post/LDP-STP/非对齐/页边界 + store 回读） | `agu_addrmodes` | `728e604ffcec539d` | 进程写 16-hex FNV-1a 校验和（`agu_addrmodes.c:7-12, 末尾 put_hex(acc)`）；golden 为无故障运行的校验和 |
| W5 | SQ-Forward（同址/部分重叠转发、字节掩码、alias、replay、memset/memcmp） | `sq_forward` | `1f4cbf14327717df` | 同形 FNV 校验和（`sq_forward.c` 末尾 `put_hex(acc)`） |

两者都是 **SE 定向探针 + 主机侧校验和 oracle**（`GOLDENS` 定义 `tools/lsu_campaign.py:251-262`），oracle 可判定（差异=SDC，崩溃=Crash，超时=Timeout，相同=Masked）。W5 是 SQ 转发探针，对 A07/A08 的 value 侧影响同样可被校验和捕获。

---

## 4. 既有旧证据核查（**不得作为本轮完成证据**）

### 4.1 A07 旧 pilot（旧 worktree，不同二进制）

- 位置：`.claude/worktrees/lsu-mdspec-20261019/runs/lsu/r4_a07_pilot/`（不在本 worktree 权威 runs 根内）。
- `pilot_evidence.json`（`generated_by tools/lsu_r6_register_evidence.py`, `generated_at 2026-10-23T04:08:45+00:00`, `generator_repo_head 97f74786`）记载：
  - A07-F0-W3/W5、A07-F6-W3/W5：各 3 seed，`faults=1`，kinds 含 `inj/lsq_push/lsq_sendfrag/mem_req/resp/tlb_translate`（F6 达 234 events 且含 `consumer/taint_reg/errant_commit`）。
  - A07-F4-W3/W5：各 3 seed，`events=0, faults=0`（honest zero）。
- `round4_findings.md:1217-1285`（§R4-5.8）：集成二进制 sha256 前缀 **`09d70dd0987c57d1`**（≠ 当前 `3db54541…`）；注入日志样本：`Site: iew_memRef_AGU_ready` + `_resume`，`isLoad=0,isStore=1`，`consumed=1,squashed=0`。
- `R6-STATUS-TABLE.md:80-85` 明确：这些 pilot 路径“**不在权威 runs 根内（草稿/他处产物，不构成权威证据）**”。

**判定**：旧 A07 pilot 是**不同二进制（09d70dd0…）下的真实运行**，可作为“a07b 曾真机注入并激活”的历史旁证，但**不是当前二进制（3db54541…）本轮证据**，且其 seed/workload 不能直接搬用。

### 4.2 A08 旧 trial（无 binary sha 记录）

- 位置：`/home/sdc/gem5-fi-ding/artifacts/lsu-trial/cells/A08-*/cell_results.json`（主树 artifacts，非本 worktree 权威 runs）。
- 实测内容：
  - A08-F0-W3：`n_runs=5, attempted=13933, activated=5, Masked=5, SDC=0`；A08-F0-W5：`attempted=12845, activated=5, Masked=5`。
  - A08-F2-W3：`attempted=13935, activated=0, Masked=0`；A08-F2-W5：`attempted=12845, activated=0`（与“F2 首 fire ≥50000 > 流长”一致）。
  - A08-F6-W3/W5：`attempted=0, activated=5, Crash=5`（**可疑**：attempted=0 表示 PRE hook 从未进入，Crash 更像基线崩溃/配置问题，而非注入；F6 属 POLICY_EXCLUDED，仅记录）。
- **无 manifest / 无 binary sha / 无 prop_evt 链**（`find artifacts/lsu-trial -name '*sha*'` 无命中，仅 `07-expanded-matrix-backfilled.csv` + `cells/`）。
- **判定**：旧 A08 trial 是“a08_subst 近似模型”的运行痕迹（F0 activated=5 全 Masked），**不足以证明 spec 的 A08-a/A08-b**，且无二进制指纹，绝不能作为本轮完成证据。

### 4.3 当前权威 runs

`find runs/lsu -maxdepth 3 -iname '*A07*' -o -iname '*A08*'` **无命中** ⇒ 本轮（当前二进制）A07/A08 尚未运行。

---

## 5. 逐 RunID 建议分类

分类词表：READY_FOR_CANARY / IMPLEMENTED_NOT_ROUTED / ROUTED_NOT_RUN / NOT_IMPLEMENTED / REVIEW_REQUIRED。

| RunID | 建议分类 | 依据（一句话） |
|---|---|---|
| A07-F0-W3 | **READY_FOR_CANARY**（限 a07b） | clean ready hook + a07b 已实现/已路由/F0 span=2795 已实测；但 a07a/a07c 未实现 ⇒ 子模型覆盖不全，canary 只证 a07b（预期 Masked，非 SDC） |
| A07-F0-W5 | **READY_FOR_CANARY**（限 a07b） | 同上，F0 span=2579 |
| A07-F4-W3 | **REVIEW_REQUIRED** | 已路由但 F4 首 fire≥50000 ≫ 流长 2795 ⇒ 结构性 honest zero，且 addrpath 无 interval 拒斥门禁（会静默 activated=0） |
| A07-F4-W5 | **REVIEW_REQUIRED** | 同上，流长 2579 |
| A07-F6-W3 | **POLICY_EXCLUDED_F6**（确认） | R6 正式 track 禁 F6；旧 pilot 有历史证据但不作本轮 |
| A07-F6-W5 | **POLICY_EXCLUDED_F6**（确认） | 同上 |
| A08-F0-W3 | **REVIEW_REQUIRED** | 仅 a08_subst（同页换值代理），非 A08-a/b 语义；已路由；F0 span 未实测（默认 1000 → EARLY_BIAS）；须先裁决“代理是否可作为正式格” |
| A08-F0-W5 | **REVIEW_REQUIRED** | 同上 |
| A08-F2-W3 | **REVIEW_REQUIRED** | 代理语义 + F2 首 fire≥50000 ≫ 流长 ≈1.3e4 ⇒ 结构性 zero，无门禁 |
| A08-F2-W5 | **REVIEW_REQUIRED** | 同上 |
| A08-F6-W3 | **POLICY_EXCLUDED_F6**（确认） | 正式 track 禁 F6；旧 trial attempted=0/Crash 可疑 |
| A08-F6-W5 | **POLICY_EXCLUDED_F6**（确认） | 同上 |

> 备注：A08 若主 agent 决定“以 a08_subst 代理跑 F0 并显式标注子模型不可证”，则可把 A08-F0-W3/W5 降到 ROUTED_NOT_RUN（可跑、未跑）。但按 spec 忠实度，**A08-a/A08-b = NOT_IMPLEMENTED**，建议先裁决再跑，避免把代理当正式模型。

---

## 6. 拟修改文件清单（供主 agent 排 owner）

### 6.1 共享实现文件（单一 owner，串行修改；多模型可能触碰）

- `CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.hh` / `.cc` / `.py`
  - A07-a（ready early + 旧 EA 值替换，需 EA pipeline-latch 观测）与 A07-c（ready loss + 超时簿记）；A08-a/b 若实现则同文件（PRE hook `a08_subst` 扩为 channel-swap/pair-swap）。**A04/A05/A06/S13/S04/L01 也共用此注入器** ⇒ 必须单一 owner 串行改。
- `CHAOS/gem5/src/cpu/o3/iew.cc` / `iew.hh`
  - A07-a 的旧 EA 获取点若需在 ready 点/execute 点加观测（`chaosAguResumeInst` 附近）；**该文件为全 O3 共享**，任何改动需回归全家族。
- `CHAOS/gem5/src/cpu/o3/lsq.cc` / `lsq_unit.cc`
  - A08-b 的同周期配对需在 `pushRequest` 前建两点缓冲 / 访问 `inst->lqIdx/sqIdx`/`request->id`；**全 LSU 模型共享**，高风险串行文件。
- `CHAOS/gem5/src/cpu/o3/chaos_lsu_trigger.hh`
  - 若需为 addrpath 家族加 interval-reachability 告警（F4/F2 zero 的响亮化），可能在此加观测计数（注意它是 header-only 共享 trigger，改语义会影响所有家族）。
- `tools/lsu_campaign.py`
  - 加 `ADDRPATH_F0_SPAN` 的 A08 行（F0 span 实测）；加 `ADDRPATH_INTERVAL_UNREACHABLE`（或扩 `LSQFWD_INTERVAL_UNREACHABLE` 为家族无关门禁）让 A07-F4 / A08-F2 响亮 BLOCKED，而不是静默 zero。
- `tools/lsu_runid_map.py`
  - `SPEC_IMPL_LANDED`：A07 更新（a07a/c 状态）、新增 A08 条目（当前 A08 无 SPEC_IMPL_LANDED）。

### 6.2 测试文件（可各自 owner，独立增补）

- `tests/test_lsu_*`（既有 `tools/lsu_*` 单测族）：新增 A07 `_addrpath_tier_flags` F4 可达性门禁单测、A08 F0 span 行存在性单测、A08 子模型未实现时的响亮拒斥/标注单测。
- `tests/chaos_lsu_trigger_test.cc`：若改 interval 告警，补 addrpath 场景的 trigger 单测。

### 6.3 只读/文档（本轮不改）

- `docs/gem5-fi/lsu/mdspec/runid_map.json`、`coverage_matrix.md`、`R6-STATUS-TABLE.*`：由主 agent 汇总后更新（本诊断只读）。
- 原始 XLSX `gem5-fi-LSU单元故障注入方案-R6实验结果.xlsx`：本轮以 runid_map（已由 XLSX 派生）核对，未改动；如需精确备注/豁免列原文，可由主 agent 用 openpyxl 复核（本 Lane 未载入大表）。

---

## 7. 风险与待决（给主 agent）

1. **A07 子模型覆盖不全**：F0 canary 只能证 a07b（时序、预期 Masked）。若 R6 要求每模型子模型动态覆盖，A07-a/a07c 必须先实现或显式登记 NOT_IMPLEMENTED（计划阶段 5 已允许如实登记）。
2. **A07-F4 / A08-F2 结构性 zero**：当前工具不会拒斥，会安静产出 activated=0。建议加 addrpath 版 interval-reachability 响亮门禁（参照 S10-F2 的 BLOCKED 措辞），否则 formal 会把“不可达”误记成“0 次激活”。
3. **A08 语义缺口**：a08_subst 既非错误通道也非同周期互换；A08-a/b 未实现。A08 的“可执行”是“代理可执行”，不是“spec 可证”。需裁决：实现 a08-a/b，或明确以代理跑并登记子模型不可证。
4. **A08-F0 早偏**：span=1000 默认对 ~1.3e4 流会触发 EARLY_BIAS；建议先做 A08 的 F0 span census。
5. **coverage_matrix PASS 的误导性**：不要据此认为 A07/A08 已完整；runid_map 的 PARTIAL 才是语义真相。

---

## 附：本次只读核验用到的关键真实命令/输出（摘录）

```
$ sha256sum CHAOS/gem5/build/ARM/gem5.opt
3db54541b7fbafa47d27ab7a3f71b8c777c2893501078f3eb36fddb91cd866c2  CHAOS/gem5/build/ARM/gem5.opt

$ strings -a CHAOS/gem5/build/ARM/gem5.opt | grep -E "iew_memRef_AGU_ready|a07b_ready_delay|a08_subst"
a07b_ready_delay
a08_subst
CHAOSAddrPath: agu_ready_mode and agu_pre_mode are mutually exclusive ...
, Site: iew_memRef_AGU_ready
, Site: iew_memRef_AGU_ready_resume

$ python3 -c "import sys;sys.path.insert(0,'tools');import lsu_campaign as lc;print('A08 blocked', 'A08' in lc.MODEL_BLOCKED); print('A07 blocked', 'A07' in lc.MODEL_BLOCKED); print(lc.ADDRPATH_F0_SPAN)"
A08 blocked False
A07 blocked False
{('A07','agu_addrmodes'):2795, ('A07','sq_forward'):2579}

$ find runs/lsu -maxdepth 3 -iname "*A07*" -o -maxdepth 3 -iname "*A08*"
(空)
```
