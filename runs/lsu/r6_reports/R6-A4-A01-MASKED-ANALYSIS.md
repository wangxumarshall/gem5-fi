# R6-A4 Lane C — A01 Masked 流只读生命周期分析

日期：2026-10-28 · 角色：Lane C（只读） · 未改任何代码/证据，未运行 gem5，未做 git 操作。
本文件是本次唯一写入。

## 0. 结论摘要

1. **两个 seed 都具备真实、可证的生命周期终局**：注入的 EA 让该访存请求在翻译阶段
   硬件检测到 page-table fault（`tlb_fault`, `detection_layer=Hardware`），该请求随后被
   **LSQUnit 真实 squash/discard**（`squash_discarded`, L4, `contained=1`,
   `state_before=load_queue_uncommitted`），同一 `request_id` / `dyn_inst_seq`，tick 单调，
   流以生命周期 `chain_end` 收口且未截断。**不是** abort 截断、不是仅 oracle=Masked、
   不是仅 chain_end。
2. **请求没有退休，也没有污染架构值**：无 `arch_translation_fault`（fault 未交付给 guest）、
   无 `consumer` / `taint_reg` / `errant_commit` / 任何 load 完成事件；load 在
   `load_queue_uncommitted` 状态被 pop 丢弃；oracle=Masked 且最终 checksum 等于 golden
   `728e604ffcec539d`。**本次证据不构成停点（无架构污染）。**
3. 当前 worktree HEAD（`d9864cff`，其中 `c90fe85f` 为 A01 白名单提交）的 checker
   **已经**把这两个流判为 `detected_contained` 并 `admitted=true`（`path=contained`,
   containment layer L4）。**runs 目录里的 `chain_report.json` 是 R6-A3 旧工具产物，
   仍写 `admitted=false`，已过期，必须用当前工具重生成。**
4. 但现实现的白名单比"严格契约"宽，审计出 **9 类仍会误放行的最小反例**
   （最严重：oracle=SDC/Crash 仍经 containment 准入；同链出现已交付 arch fault 不否决；
   `tlb_fault/tlb_translate` 的 request/VA 不校验；同一 tick 的更深处观测不否决）。
   见 §8。建议按 §7 收紧后再作为正式判据。

## 1. 输入、方法与溯源

### 1.1 输入文件（均为绝对路径，SHA-256 实测）

| 文件 | SHA-256 | 备注 |
|---|---|---|
| `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F1-W3_s2/A01-F1-W3/seed2/prop_evt.txt.gz` | `97b257eda7afc294c422ab6799c0a1cd9cab1447c9d7f1bf48c15903f0d19360` | `gzip -t` OK，915 B |
| 同上 `chain_report.json` | `4c5f2a4a02763051ed37169ef66937232b80e330a566658a908f0e39f0b6b2fe` | R6-A3 旧产物 |
| 同上 `addrpath_injections.log` | `4b3cc2e4983c1f2fa78f47be1dc422e256ba3e1634e4d659503d7193c60027a8` | |
| 同上 `run.out` | `c29e471bb732fc980434a7bcf31ddd3813eadd5e6716816ae18b34fe65792475` | |
| 同上 `run.err` | `82790b1e6fc9fb5cadb88f2ebcce5f73fa48a90b613ea160375cbfe7991ef2b9` | |
| 同上 `stats.txt` | `cee42490c3ef99cae0dcebe9e50afeb600c3f3c654a539726574afdb69b67bf5` | |
| `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F2-W3_s2/A01-F2-W3/seed2/prop_evt.txt.gz` | `44d6a209d3b386f974acf194df16ab67d94d8368bd026ec46481760ba889ffe5` | `gzip -t` OK，912 B |
| 同上 `chain_report.json` | `871b32342116e44b440265f3759b935c38b1650828122191c79912c2df4c0bbb` | R6-A3 旧产物 |
| 同上 `addrpath_injections.log` | `5b18655a99ef560327500e3e00a776bcce8d457baf62f18ef9877d4036f903a3` | |
| 同上 `run.out` | `a86d96911d46682120a5161da8854a7abf61b1a3a647761ab7f1c66e9bc9d4ed` | |
| 同上 `run.err` | `5c8de06bae63aa5f52fb80babe441e4bd242fe13be863b061961ce01c27209f0` | |
| 同上 `stats.txt` | `0cb6e4da5f1d6d6016252c464d519353f8d7e26530a9f245dd72c82c50deceaa` | |

### 1.2 工具与构建溯源（worktree `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026`）

- worktree 分支 `fix/r6-a-unit-20261028`，HEAD `d9864cff445bc0102003330529d685915da5204b`
  （`[R6-A4][BATCH] 25 格补救批次驱动 + 单格 TIMEOUT 覆盖`）；
  `c90fe85f` = `[R6-A4][A01] 翻译 fault 请求真实 squash 生命周期终局（窄白名单）+ 组合负向测试`。
  分析期间 HEAD 从会话初始的 `df39c4e8` 前进到 `d9864cff`（并发 lane 提交），本报告引用的是后者。
- `tools/lsu_chain_check.py` = `e2b4ed7a8e22bce092e1fb7d45fa1366329d51caa73f0d76e35a00fd5a66c39c`
- `tools/lsu_prop_fields.py` = `af9aec3d38e343bd6c34c751e7d5d4ac3429367599152f72c7ed64b52646b1ea`
- `tests/test_lsu_r6a4_a01_squash_terminal.py` = `fec55761e0b48d8229ea1d3252ee4975a7ab7f49d3e43d05ffdbfdcb962238cd`
- 生成证据的二进制（run.out 命令行引用，实测 SHA 与 R6-A4 进度记录的"旧二进制"一致）：
  `CHAOS/gem5/build/ARM/gem5.opt` = `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e`
- 源钩子：`CHAOS/gem5/src/cpu/o3/lsq_unit.cc`
  `1106b26ea49b73b863432df70bad2aa18010ab740673aa3e30c7a6a285eb35ad`；
  `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc`
  `0534022ad2bdeb9c871614ae5a26353c8daf09fd41f1b40f06e8af47b4195fb2`；
  `CHAOS/gem5/src/sim/faults.cc`
  `79624d4e6b76b8ba2c9d105e8ea7db05aafdbeb070bf1bec41700b5468e34063`；
  负载 `workloads/directed/agu_addrmodes`
  `a702f3abf3a495177b222ebec60d765bad5c26c5c3fa8adcb1073b4e30f759fc`
  （golden checksum 见 `tools/runner.py:70` / `tools/lsu_campaign.py:76`：
  `agu_addrmodes -> 728e604ffcec539d`）。

### 1.3 方法

- 事件流用 `lsu_prop_fields.read_events` 逐行/流式解析（`gzip` 迭代，`EVENT_CAP=200000`
  有界，绝不整文件读入）；两文件均 8 条事件、`truncated=False`。
- 用当前 worktree 的 `lsu_chain_check` 的 `check_chain` / `containment_from_events` /
  `check_admission` 复算；另在内存中做字段级变异（deepcopy 真实事件后改单字段），
  不落盘、不生成新证据。
- 源级机制核对只读 `lsq_unit.cc` / `CHAOSPropagation.cc` / `faults.cc`。

## 2. 问题 1：注入真实性（fault_id / corr / event_id / tick / VA / mask）

### 2.1 两条流的注入事件（解析后的真实字段）

| 字段 | A01-F1-W3 s2 | A01-F2-W3 s2 |
|---|---|---|
| `kind` | `inj` | `inj` |
| `run_id` / `fault_id` / `event_id` | `A01-F1-W3` / `1` / `1` | `A01-F2-W3` / `1` / `1` |
| `tick` / `cycle` | `1336019300` / `3470180` | `140579285` / `365141` |
| `dyn_inst_seq` | `6126737` | `585139` |
| `va`（旧 VA） | `493170` = 0x493170 | `7ffffefb50` | 
| `before` -> `after` | `493170 -> 49b170` | `7ffffefb50 -> 7ffffe7b50` |
| `corr` | `origin` | `origin` |
| `field/opcode` | 空 / 空 | 空 / 空 |

`addrpath_injections.log`（同一目录，真实发射日志）：

```
F1: Tick: 1336019300, Site: lsq_sendFragmentToTranslation, mode=a01_bit,
    old_vaddr=0x493170, new_vaddr=0x49b170, faults_injected: 1,
    geom_candidates=1, geom_rejects=0, geom_bitmask=0x8000
F1: FUNNEL: attempted=1049417 eligible=1049417 injected=1
F1: CHAOS_L0_FUNNEL: CHAOSAddrPath attempted=1426611 eligible=1426611 injected=1 activated=1
F2: Tick: 140579285, Site: lsq_sendFragmentToTranslation, mode=a01_bit,
    old_vaddr=0x7ffffefb50, new_vaddr=0x7ffffe7b50, faults_injected: 1,
    geom_candidates=1, geom_rejects=0, geom_bitmask=0x8000
F2: FUNNEL: attempted=156107 eligible=156107 injected=1
```

`run.out` 终局触发行（两 seed）：`CHAOS_LSU_TRIGGER: injector=CHAOSAddrPath tier=F1|F2
attempted=1426611|156107 eligible=... injected=1 first_eligible_tick=80080
last_eligible_tick=1813200235|214421130 ... (activated=W3-L0-layer)`。

- **bit mask = 0x8000（bit 15，XOR）**：`0x493170 ^ 0x8000 = 0x49b170`；
  `0x7ffffefb50 ^ 0x8000 = 0x7ffffe7b50`。F1 为置位方向，F2 为清零方向，都是**单 bit 翻转**。
- **真实注入成立**：日志（site/mode/old/new/injected=1）+ 流内 `inj`（VA 前后不同、
  `corr=origin`）+ run.out 漏斗计数三方可互证；`injected=1`，无重复注入。
- **一致性异常（不影响本结论，但需记录）**：两份日志都带
  `(NOTE: SE-inert — byte7 zero lands in SE 512MiB range)`，但本轮实际观察到
  `tlb_fault`（corrupted VA 落进未映射页），说明这条"SE-inert"注记与真实几何位
  （bit15）并不匹配，属于日志注记与 mask 的文案错配，建议后续修正，不能据此把
  SE 下的 A01 一律当"inert"。

## 3. 问题 2：faulted request 的真实后续

### 3.1 逐事件表（F1 s2；F2 s2 结构/字段完全同构）

| ev | kind | tick | cycle | dyn_seq | request_id | va | dl | contained | outcome | corr | parent |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | inj | 1336019300 | 3470180 | 6126737 | - | 493170 | - | - | - | origin | - |
| 2 | addr_form | 1336019300 | 3470180 | 6126737 | - | 49b170 | - | - | - | origin | 1 |
| 3 | mem_req | 1336019300 | 3470180 | 6126737 | 6126737 | 49b170 | - | - | - | seq_primary | 2 |
| 4 | lsq_sendfrag | 1336019300 | 3470180 | 6126737 | 6126737 | 49b170 | - | - | - | seq_primary | 3 |
| 5 | tlb_translate | 1336019300 | 3470180 | 6126737 | 6126737 | 49b170 | - | - | - | seq_primary | 4 |
| 6 | tlb_fault | 1336019300 | 3470180 | 6126737 | 6126737 | 49b170 | Hardware | （空） | Generic* | seq_primary | 5 |
| 7 | squash_discarded | 1336029695 | 3470207 | 6126737 | 6126737 | - | L4 | 1 | contained | seq_primary | 6 |
| 8 | chain_end | 1813259525 | 4709765 | - | - | - | - | 0 | run_end | none | 7 |

\* 原始行是 `outcome=Generic page table fault`，但 PROP-EVT 是空格分隔格式，
解析器把多词值截成 `outcome=Generic`（`table`/`fault` 两个无 `=` token 被丢弃）。
见 §9.1。

F2 s2：`inj..tlb_fault` tick=140579285/cycle=365141，squash tick=140585830/cycle=365158，
chain_end tick=214480420/cycle=557092；`request_id` 585139 全链一致；`dyn_inst_seq` 585139 一致。

### 3.2 关键判定

- **request_id 出现位置**：`mem_req`(3)、`lsq_sendfrag`(4)、`tlb_translate`(5)、
  `tlb_fault`(6)、`squash_discarded`(7) 全部等于同一值（F1=6126737，F2=585139）；
  `addr_form`/`inj` 不带 request_id，但 `dyn_inst_seq` 与 squash 完全一致。
- **是否进入 L3 cache / LSQ 数据下游**：**没有**。链中不存在 `lq_read` / `lq_complete` /
  `resp` / `sq_execute` / `sq_writeback` / `cache_access` / `cache_return` / `cache_fill` /
  `mshr_*` 任何 L3 族事件。这不是采集缺失：翻译 fault 使该请求**从未进入下游访存通路**，
  L3 见证结构性不存在（对照 F2 s3 的 store 路径有 `sq_execute`）。
  按通用层映射（`KIND_LAYER`），`mem_req/lsq_sendfrag/tlb_translate/tlb_fault` 都是 L2，
  所以旧规则要求"L4 squash 目标之前有 L0..L3 连续前缀"时永远凑不齐 L3。
- **tlb_fault**：`detection_layer=Hardware`，`contained` 为空（**不是** contained=1），
  `outcome=Generic`（原始文本 Generic page table fault），`corr=seq_primary`。
  即"硬件检测到翻译 fault"，但未记录交付。
- **squash_discarded**：`request_id`/`dyn_inst_seq` 与 `mem_req`、`lsq_sendfrag`、
  `tlb_translate`、`tlb_fault` **完全一致**；`detection_layer=containment_layer=L4`，
  `contained=1`，`outcome=contained`，`containment_reason=squash_discarded`，
  `corr=seq_primary`，`field=load`，`state_before=load_queue_uncommitted`。
- **tick 单调**：`inj = addr_form = mem_req = lsq_sendfrag = tlb_translate = tlb_fault`
  （同周期）`<` squash `1336029695`（F1，+10395 ticks = **+27 core cycles**，tick/cycle=385）
  `<` chain_end。F2：squash +6545 ticks = **+17 core cycles**。squash 紧跟 fault（17–27 周期），
  与"fault 立即触发 redirect / 该请求被立刻丢弃"的时间尺度一致。
- **squash 之后**：F1/F2 流内除 `chain_end` 外无任何事件；squash 的 `parent_event_id=6`
  指向 `tlb_fault`，DAG 上无更深分支。

## 4. 问题 3：squash 是否真实机制、是否 abort 截断

**真实机制（源码实证）**

- `CHAOS/gem5/src/cpu/o3/lsq_unit.cc` `LSQUnit::squash(const InstSeqNum&)`：
  在 `while (loadQueue.size()!=0 && loadQueue.back().instruction()->seqNum > squashed_num)`
  循环里 `setSquashed()` 后调用
  `cpu->chaosPropagation->noteSquashDiscarded(loadQueue.back().instruction().get(),
  true, "load_queue_uncommitted")`，随后 `clear()` + `pop_back()`（约 L1181–1207）。
  这就是本事件 `state_before=load_queue_uncommitted` 的来源。store 侧同构（L1277，
  `"store_queue_uncommitted"`）。
- `CHAOSPropagation::noteSquashDiscarded`（`CHAOSPropagation.cc` L2097 起）先用
  `correlateRequestBySeq(inst->seqNum)` 在该故障链的 `addr_registry` 里匹配注入记录，
  匹配不到直接返回（不会给无关指令发事件）；匹配到才发 `squash_discarded`
  （`request_id=dyn_inst_seq=inst->seqNum`, `detection_layer=L4`, `contained=1`,
  `outcome=contained`, `containment_reason=squash_discarded`, `corr` 来自注册表）。
  因此事件只可能由**真正被 squash 的、携带本注入的 LSQ 条目**产生。

**不是 abort 截断（四重证据）**

1. `gzip -t` 通过，gzip 成员完整（有 EOF trailer），不是 panic 截断的半截文件；
2. `prop_evt` 是退出回调收口：流内有 `chain_end`（`corr=none`, `outcome=run_end`），
   `chain_report.truncated=false`、`evidence_truncated=false`、`stream_present=true`，
   解析器 `read_events` 返回 `truncated=False`；
3. 仿真在 squash 之后又跑了很久并正常结束：F1 squash 在 cycle 3,470,207，chain_end
   在 cycle 4,709,765（+1,239,558 cycles）；F2 +191,934 cycles；
4. 负载跑满计划重复次数并输出最终 digest：F1 `chaos_repeat 4023`，run.out 恰有 4023 行
   `ITER:`，末行为 `728e604ffcec539d`（== golden）；F2 `chaos_repeat 434`，434 行，末行同为
   golden。崩溃对照 seed（F1 s1/s3）则在 iteration 543/640 处提前结束并写
   `run.err: chaos: injected address ... faulted (guest SEGV)`。

**诚实边界（必须保留）**：事件流**没有记录 squash 的触发原因**。`parent_event_id=6` 由
`notePropEvt` 按"当前故障链上下文"赋值，表达的是**链归属**，不是因果；gem5 里任何
redirect（例如分支误预测）都会执行 `LSQUnit::squash`。因此可以严格证明的是
"该携带注入的未提交请求被真实丢弃"，不能仅凭事件证明"是翻译 fault 直接触发了这次
squash"。不过 17–27 周期的紧邻时序 + `addr_registry` 命中 + oracle 全序 golden，
使"该 fault 没有产生架构后果"这一结论仍然成立（这是终局 (3) squash/replay/mask
语义，不是"检测并恢复到正确值"的终端 (2)）。

## 5. 问题 4：arch fault / consumer / taint / errant commit / retire

- **无 `arch_translation_fault`**。该事件只在 `sim/faults.cc`
  `GenericPageTableFault::invoke` 里、且 fault 真正被交付/调用时发出
  （`prop->noteArchTranslationFault(vaddr, exact)`）。seed2 的 `run.err` 中**没有**
  `chaos: injected address ... faulted (guest SEGV)`；同批 crash 对照（F1 s1/s3）
  则有该行，并在流内产生 `arch_translation_fault(delivered=1, contained=1, dl=L2)`。
  因此"fault 未交付、guest 未取异常"是强证据，不只是缺席。
- **无 `consumer` / `taint_reg` / `errant_commit` / `store_not_retired` / `resp` /
  `lq_*` / `sq_*`**：该 load 从未完成（无数据返回），没有可被消费的值；事件总数仅 8 条。
  对照 A01-F0-W9/W3 的 full 样本（同族不同 seed）确有 `taint_reg`+`errant_commit`+
  多条 `consumer`，说明这些 kind 在本采集器/负载下是会被发出的，不存在"结构性永不出现"。
- **是否实际退休并污染架构值**：没有证据支持，且有正面反证：
  1) squash 事件在 `load_queue_uncommitted` 状态把该 `dyn_inst_seq` 条目 squash 后
     `clear()+pop_back()`；已提交的指令不会再留在 LQ 里被 pop；
  2) 同一 `dyn_inst_seq` 之后没有新的 commit/消费事件（注入注册表按 dyn_seq 关联，
     重新取指产生的指令是新 DynInst/新 seqNum，不会带着被腐蚀的 VA 再次提交）；
  3) oracle=Masked：进程 exit 0、跑满计划次数、最终 checksum `728e604ffcec539d`
     == golden（`tools/runner.py:70`）。
- **停点判定**：**未命中**"请求实际退休并污染架构值"的停点。残余不确定性只有两点：
  (a) 事件流无 `retire/commit` kind，"未退休"由 squash pop + 队列状态证明，而不是由
  显式 retire 事件证明（结构限制，需在报告中如实标注）；
  (b) squash 触发原因未记录（见 §4）。

## 6. 问题 5：对照（已合格）seed 的终局与误放行检查

| 样本 | oracle / exit | 事件种类（终局路径） | 旧 gate 终局 | 当前工具 |
|---|---|---|---|---|
| A01-F1-W3 s1 | Crash / 1 | inj→addr_form→mem_req→lsq_sendfrag→tlb_translate→tlb_fault→**arch_translation_fault(L2, delivered, contained=1)**→chain_end | detected_contained / L2 | 同（arch 路径） |
| A01-F1-W3 s3 | Crash / 1 | 同上（arch_translation_fault 交付） | detected_contained / L2 | 同 |
| A01-F2-W3 s1 | Crash / 1 | 同上（arch_translation_fault 交付） | detected_contained / L2 | 同 |
| A01-F2-W3 s3 | Masked / 0 | inj→…→tlb_fault→**sq_execute(L3)**→**squash_discarded(store, L4)**→chain_end | detected_contained / L3 | 同（通用 L3 前缀路径） |
| A01-F0-W3 s2（参照） | Masked / 0 | inj→…→tlb_translate→sq_execute→sq_writeback→resp→taint_reg→sq_complete→**store_not_retired(L4)**→chain_end | detected_contained / L4 | 同 |
| A01-F1-W9 s2（参照 full） | SDC | inj→…→lq_read→resp→lq_complete→taint_reg→**errant_commit**→consumer…→chain_end | full（逃逸） | 同 |

- 合格对照的终局只有两类：**交付型 arch fault（L2）** 与 **有 L3 见证的 store squash /
  store 生命周期（L3/L4）**；没有任何合格对照是"无 L3 的 load squash"。
- 用新白名单契约（§7）在内存中复算：4 个合格对照 + F0-W3 s2 + F1-W9 s2 全部被判
  "非本类"（不适用），**不会被本类误放行**；它们仍按原有路径各自准入。唯一的 L0-only
  真实对照 `r6_a_segv2_A01-F0-W9_s1`（7 条事件：inj..tlb_fault + chain_end，无 squash）
  被明确拒绝（`admitted=false`，`crash_translation_blocked`）。
- A01 全量 census（35 条流）：仅 3 条含 `squash_discarded`——F1 s2、F2 s2（无 L3）与
  F2 s3（有 L3）。因此本白名单的影响面就是这 2 个样本，不会连带改变其他 A01 样本。

## 7. 问题 6：严格 checker 白名单契约（字段级）

命名建议：终局类型保留 `detected_contained`（现实现）**或**新增独立终局
`translation_fault_squash_contained`（更诚实，避免与"检测并恢复/交付型含住"混计）。
若新增，必须同步 `CLOSED_TERMINALS`、campaign 统计与所有 dashboard；且**不得**因此放宽
通用 L0→L4 前缀规则。

谓词（全部为 `AND`；任一不满足 → `False`，继续走旧的拒绝路径）：

**A. 作用域与流完整性**
1. 事件全部 `run_id` 前缀 `A01`，且与 bundle `run_id` 相同；`family=="agu"`；
   非空 `fault_id` 唯一（只允许 1 个 fault）。
2. `truncated == False`；`rc == 0`；`oracle_outcome == "Masked"`（校验和 == golden）。
   仅 oracle=Masked **绝不**可作为准入依据（它是必要条件，不是充分条件）。
3. 流内恰有 1 个 `chain_end`，且是流中最后一条；`kind=chain_end`, `corr=none`,
   `outcome=run_end`, `contained=0`，`detection_layer` 为空（生命周期标记）。

**B. 见证字段（squash_discarded，唯一一个）**
4. `kind=squash_discarded`，`event_id/kind/detection_layer/outcome` 均非空，
   `evidence_status=observed`（或空，按默认 observed）。
5. `contained=1`；`outcome=contained`；`detection_layer=L4`；`containment_layer=L4`；
   `containment_reason=squash_discarded`；`corr=seq_primary`。
6. `field=load`；`state_before=load_queue_uncommitted`（证明是未提交 LQ 条目的真实 pop；
   若日后允许 store，必须显式改写为 store 变体并单列，不得默默共用）。
7. `request_id` 与 `dyn_inst_seq` 均非空、非 `"0"`。

**C. ancestry（同一 parent DAG，逐边校验）**
8. 事件序列（以 `parent_event_id` 逐级相连）必须恰好是
   `inj → addr_form → mem_req → lsq_sendfrag → tlb_translate → tlb_fault →
   squash_discarded → chain_end`；不允许缺项、额外项或乱序。
   （`inj`/`addr_form`/`mem_req`/`tlb_fault` 为必需；`lsq_sendfrag`/`tlb_translate`
   在两个真实 seed 均存在，作为本版本必需项；若未来生成器不产这两条，需显式版本化放宽。）
9. 身份一致：`dyn_inst_seq` 在 `inj/addr_form/mem_req/lsq_sendfrag/tlb_translate/
   tlb_fault/squash_discarded` 七个事件上**全部非空且完全相等**（禁止空值豁免）。
10. 同一请求：`request_id` 在 `mem_req/lsq_sendfrag/tlb_translate/tlb_fault/
    squash_discarded` 上全部非空且完全相等。
11. 同一地址：`va` 在 `addr_form/mem_req/lsq_sendfrag/tlb_translate/tlb_fault` 上
    全部非空且完全相等；`inj.before == inj.va`，`inj.after == addr_form.va`，
    且 `inj.before != inj.after`（确有注入改值，排除 no-change 假注入）。
12. `tlb_fault.detection_layer == "Hardware"`，`tlb_fault.outcome` 非空
    （原始文本为 `Generic page table fault`；受 §9.1 解析截断影响，判据用
    `startswith("Generic")`），`tlb_fault.contained` 为空或 `0`（不得=1）。
13. `corr == "seq_primary"` 在 `mem_req/lsq_sendfrag/tlb_translate/tlb_fault/
    squash_discarded` 上成立（链关联；`inj/addr_form` 为 `origin`）。

**D. 时间与后验**
14. `tick` 沿 ancestry 非降；`squash.tick > tlb_fault.tick`（本类要求严格大于）；
    `chain_end.tick > squash.tick`。
15. squash 之后（流序与 tick 两个口径同时检查）除 `chain_end` 外**不得有任何事件**；
    更一般地，不允许同一 fault 链里存在 `tick >= squash.tick` 的其它非生命周期事件。
16. 同一 fault 链内不得出现 `arch_translation_fault`、`consumer`、`taint_reg`、
    `errant_commit`、`store_not_retired`、`resp`、`lq_*`、`sq_*`、`cache_*`、`mshr_*`。
17. 逃逸优先：若同一链存在以 `errant_commit` 收口的可证 L0→L5 路径，本白名单一律让位
    （保留现 `_errant_commit_escape` 护栏）。

**E. 否则**
18. 其余情况一律 `False`。尤其是：仅 oracle=Masked、仅 chain_end、`truncated=True`、
    未收口（无 chain_end）、request/corr 不匹配、VA 不一致、跨请求拼接、非 A01、
    非 load squash、oracle 为 SDC/Crash、出现更深的真实观测——全部拒绝。

实现落点（现有代码，已在此分支提交）：`_a01_translation_squash_witness`（L1137）、
`_terminal` 的调用点（L515-520）、`_containment_candidate`（L1224 起）、
`containment_from_events` / `check_admission` 的收口/截断强制。收口与截断的强制已经生效
（截断/无 chain_end 时 admission=False），但**终局标签**仍会在 `check_chain` 里显示
`detected_contained`，需要一并修正（见 §8 的 G21/G22）。

## 8. 现实现审计：与严格契约的差异（在内存中对真实流逐字段变异实测）

当前实现（HEAD `d9864cff`）对两个真实流的判定：
`terminal=detected_contained`，`containment.layer=L4`，`check_admission.admitted=true`，
`path=contained`，`violations=[]`。正确性符合预期。

但对真实事件做单字段变异后，下列反例**仍被准入**（当前实现过宽）：

| # | 变异（基于 F1 s2 真实字段） | 期望 | 当前实测 | 级别 |
|---|---|---|---|---|
| G19 | `oracle_outcome="SDC"`（其余不变） | 拒 | **admitted=true**（`sdc_translation_blocked` + containment L4） | 高 |
| G20 | `oracle_outcome="Crash"` | 拒 | **admitted=true**（`crash_translation_blocked` + containment L4） | 高 |
| G7 | 在 squash 前插入已交付的 `arch_translation_fault(contained=1, dl=L2, tick=1336020000, parent=6)` 兄弟分支 | 拒 | **admitted=true** | 高 |
| G2 | squash 之后同 tick 插入 `consumer(L4, corr=taint_prop, tick=1336029695)` | 拒 | **admitted=true**（后验检查用 `tick > t` 的严格大于，同 tick 漏网） | 中 |
| G3 | `tlb_fault.request_id="999"` | 拒 | **admitted=true**（身份只校验 mem_req/lsq_sendfrag） | 中 |
| G4 | `tlb_translate.request_id="999"` | 拒 | **admitted=true** | 中 |
| G5 | `tlb_fault.va="49b171"` | 拒 | **admitted=true**（VA 完全未校验） | 中 |
| G6 | `inj.after="493170"`（无改值） | 拒 | **admitted=true**（未校验 VA 确有变化） | 中 |
| G1 | `mem_req.dyn_inst_seq=""` | 拒 | **admitted=true**（`not in ("", seq)` 允许空值） | 中 |
| G8 | `chain_end` 改成 `corr=seq_primary, outcome=arch_exception, contained=1` | 拒 | **admitted=true**（只检查"存在 chain_end"，不校验生命周期字段） | 中 |
| G17 | 流内复制第二条 `chain_end` | 拒 | **admitted=true**（不要求恰一条） | 低 |
| G18 | squash 改为 `field=store, state_before=store_queue_uncommitted` | 需显式裁决 | **admitted=true**（未限定 load） | 低 |

已正确拒绝（与契约一致，实测）：`evidence_status=unknown`（报
`unknown_in_activated_chain`）、squash 的 `request_id` 不匹配、`corr=none`、
`contained=0`、`detection_layer=L3`、`containment_reason` 为空/改成 `squash_masked`、
tick 倒挂、非 A01（target 或 inj 的 run_id 改成 `T02-F2-W4`）、parent 断链、
缺 `tlb_fault`、缺 `lsq_sendfrag`、缺 chain_end、`truncated=True`。
另有两条**行为正确但标签误导**：`truncated=True` 或删掉 chain_end 时
`check_admission` 正确拒绝，但 `check_chain` 的 `terminal` 仍是
`detected_contained`（应改成开放终局或 `containment_on_unclosed_stream` 的响亮理由）。

> 说明：G15 的实测结果与 `_has_unknown` 的代码路径不一致，建议实现方用
> `tests/test_lsu_r6a4_a01_squash_terminal.py` 补一条断言并在 `_containment_candidate`
> 里显式要求 `evidence_status in ("", "observed")`，避免依赖别处逻辑。

**结论**：现有白名单的"窄"只窄在 `kind=field` 与 request/dyn 相等上；
**oracle 一致性、交付型 arch fault 否决、同 tick/流序后验、VA/tlb 身份、生命周期字段**
六处需要补齐，否则在多发/混合故障或异构生成器下存在 READY 虚增风险。

## 9. 其他真实发现（影响主 agent 的后续动作）

### 9.1 `outcome` 多词值被解析器截断

`PROP-EVT` 为空格分隔 `k=v`。真实行
`... outcome=Generic page table fault ...` 被 `parse_line` 解析为 `outcome="Generic"`，
`table`/`fault` 两个 token 因无 `=` 被丢弃（实测：
`{'kind': 'tlb_fault', 'outcome': 'Generic', 'detection_layer': 'Hardware', 'contained': ''}`）。
当前 `_terminal` 只比较 `detection_layer`/`contained`，未受影响；但任何
"`outcome == "Generic page table fault"`" 的精确比较都会失效。建议：
发射端改为单 token（如 `GenericPageTableFault`）或解析器支持引号/转义；在修改前，
契约按 `outcome.startswith("Generic")` 判定。

### 9.2 `chain_report.json` 已过期（必须重生成）

runs 目录里的 `chain_report.json`（SHA 见 §1.1）是 R6-A3 工具产物，
`admitted=false`、`terminal=provable_to_L2_then_unknown`；用当前工具复算同一文件的
`prop_evt` 得到 `terminal=detected_contained`、`admitted=true`、`path=contained`。
R6-A4 的状态表/去重清单/FINAL-REPORT 若继续引用旧 JSON，会把这两个样本误记为"未合格"。
**必须用当前 checker 重生成这两格的 chain_report 并更新状态表**（只读 lane 不做）。

### 9.3 `addrpath_injections.log` 的 "SE-inert" 注记与实测矛盾

见 §2；建议作为工具文案 bug 单独修，且不要再用该注记推断"SE 下 A01 无效果"。

## 10. 问题 7：负向测试用例清单（真实字段构造的最小反例）

基线正向：F1 s2 的真实 8 事件（`request_id=6126737`, `dyn_inst_seq=6126737`,
`va=49b170`, squash tick 1336029695）与 F2 s2（585139 / 7ffffe7b50 / 140585830）。
以下每行 = 基于真实流的一次单字段/单事件变异 + 期望（当前实现是否已拒见 §8）：

1. 仅 `inj + chain_end`（oracle=Masked）→ 拒（无 squash）。
2. 只有 oracle=Masked / 只有 `chain_end(contained=1)` → 拒（生命周期不充当见证）。
3. 删 `chain_end`（未收口）或 `truncated=True` → 拒（即使事件内容完好）。
4. squash `request_id=6126738` → 拒。
5. `mem_req.request_id=6126737`、squash `request_id=6126738` → 拒（跨请求拼接）。
6. `tlb_fault.request_id=999` → 拒（同一 request 的身份链断裂）。
7. squash `dyn_inst_seq=6126738` → 拒。
8. `mem_req.dyn_inst_seq=""` → 拒（空值不得豁免）。
9. squash `corr=none`（或 `corr=origin`）→ 拒。
10. squash `contained=0` → 拒。
11. squash `detection_layer=L3`（或空）→ 拒。
12. squash `containment_layer` 空 → 拒。
13. squash `containment_reason=""` 或 `squash_masked` → 拒（本类只认 `squash_discarded`）。
14. squash `outcome=masked`/空 → 拒。
15. squash `event_id=""` 或 `outcome=""` → 拒（空壳见证）。
16. squash `field=store, state_before=store_queue_uncommitted` → 拒（显式裁决；不共用）。
17. `tlb_fault.va=49b171`（与 mem_req 不同）→ 拒。
18. `inj.before==inj.after`（VA 未变）→ 拒。
19. `addr_form.va != inj.after` → 拒。
20. `tlb_fault.detection_layer="L4"`（非 Hardware）→ 拒。
21. `tlb_fault.contained=1` → 本类拒（走通用 containment 路径另行判定，且 oracle 通常非 Masked）。
22. squash `tick=1336010000`（早于 tlb_fault）→ 拒；`tick == tlb_fault.tick` → 拒（本类要求严格大于）。
23. squash 后插入 `consumer(L4)` 或 `lq_complete(L3)`（tick 更大）→ 拒；**同 tick 也必须拒**。
24. squash 前插入已交付 `arch_translation_fault(contained=1, dl=L2)` 兄弟分支 → 拒。
25. 链内出现 `errant_commit` 且收口 L0→L5 full → 拒（逃逸优先，现有护栏）。
26. `oracle_outcome=SDC` 或 `Crash` → 拒（本类只用于"无错误副作用"的 Masked 终局）。
27. 非 A01（run_id 改成 `A05-F1-W3` / `T02-F2-W4`）→ 拒。
28. 缺 `tlb_fault` 或 `lsq_sendfrag` → 拒。
29. `parent_event_id` 断链（squash 指向 5 而不是 6）→ 拒。
30. 两条 `chain_end` 或 `chain_end` 被改成检测事件 → 拒。
31. `evidence_status=unknown` → 拒（严格契约）。
32. 同一链不同事件 `run_id` 混合（如 mem_req 改 `A02-F1-W3`、target 仍 A01）→ 拒
    （当前实现依赖 family 推断"偶然"拒绝，应显式校验全部事件 run_id 一致）。

## 11. 复现命令（只读，均未运行 gem5）

```bash
# 1) 流完整性 / 哈希
gzip -t /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F1-W3_s2/A01-F1-W3/seed2/prop_evt.txt.gz
sha256sum /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F*/A01-F*-W3/seed2/{prop_evt.txt.gz,chain_report.json,addrpath_injections.log,run.out,run.err,stats.txt}

# 2) 当前 checker 复算（在 worktree 内）
cd /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026
python3 tools/lsu_chain_check.py \
  /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A01-F1-W3_s2/A01-F1-W3/seed2/prop_evt.txt.gz \
  --oracle-outcome Masked
#   -> faults.1.terminal = detected_contained, provable_to = L2, truncated_stream = false

# 3) admission（脚本在内存中调用 containment_from_events + check_admission）
#    -> admitted=true, path=contained, path_layers=[L0,L1,L2], violations=[]
```

## 12. 交付判定

- 两个 seed 的 **containment 真实性：成立**（真实硬件翻译 fault + 真实未提交 LQ 条目的
  squash discard + 同一 request/dyn + 收口完整 + oracle golden；无交付型异常、无消费/污染）。
- **停点风险：未命中**。唯一需在对外结论里保留的诚实边界：squash 的触发原因不在事件里，
  且事件流无 retire kind；"未退休"由 `load_queue_uncommitted` 的 pop 与 golden checksum 证明。
- **白名单：现实现可准入这两个真实样本，但需按 §7 收紧 6 处（§8 的高/中级项）后才可作为
  正式判据；并须重生成两格 chain_report（§9.2），否则仓库内证据与工具结论不一致。**
