# 第四轮实测发现（R4-1：S01/S02 触发根因 + seq/idx 关联改造）

> 基线 `76994a16`（worktree `lsu-mdspec-20261019`）。本轮只登记**实测得出**的结论；
> 每条证据都给出可复现命令与真实输出摘录。二进制身份：修复前
> `58fef3c92da60bcb`，重建后 `5cde0a72d58e1d15`（`sha256sum` 前缀）。

## 1.1 根因：S01/S02 activated=0 是 F0 span(1000) > 整条 eligible 流(7)，不是钩子未挂/模式未消费

**复跑命令（正式 campaign 入口）**：

```bash
LSU_GEM5_BIN=$PWD/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py \
  --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv \
  --outdir runs/lsu/r4_t1_repro --cells S01-F0-W5,S02-F0-W5 \
  --phase trial --max-seeds-per-cell 3 --max-parallel 1
```

**实测输出**（`runs/lsu/r4_t1_repro/`，6 个样本全部一致）：

```
  S01-F0-W5: phase=trial n_runs=3 activated=0 sdc=0 stop=seed-cap(3) cons=OK
  S02-F0-W5: phase=trial n_runs=3 activated=0 sdc=0 stop=seed-cap(3) cons=OK
CHAOS_LSU_TRIGGER: injector=CHAOSLSQFwd tier=F0 attempted=7 eligible=7 injected=0 first_eligible_tick=518980 last_eligible_tick=15030400 (activated=W3-L0-layer)
CHAOS_L0_FUNNEL: CHAOSLSQFwd attempted=7 eligible=7 injected=0 activated=0
```

**三个候选假设的逐一裁决**（brief 1.1）：

1. **注入点从未被调用？否。** `attempted=7` = `corrupt()` 被调用 7 次。定向
   debug 运行（同 flags + `--debug-flags=LSQUnit`）数出整条 full-coverage
   转发流恰好 7 条：

   ```bash
   CHAOS/gem5/build/ARM/gem5.opt --outdir=/tmp/out_s01dbg --debug-flags=LSQUnit \
     configs/se/lsu_proxy.py --cmd workloads/directed/sq_forward --cpu O3 \
     --chaos_lsqfwd --lsqfwd_lsu_tier F0 --lsqfwd_warmup_events 0 \
     --lsqfwd_span_events 1000 --lsq_struct_mode byte_flip --rng_seed 1 \
     --chaos_propagation --prop_run_id S01-F0-W5 --prop_sample_run_id s1
   $ grep -c "Forwarding from store idx" /tmp/s01dbg.log
   7
   ```

   sq_forward 负载（32 元素静态数组探针）在 O3 上整个运行只有 7 次
   store→load 全覆盖转发（绝大多数 store 在 load 执行前已写回 L1）。
2. **lsq_struct_mode 未被消费？否。** byte_flip 走 `corrupt()` 主路径；
   若模式未被消费则 `attempted` 不会增长（FwdSourceSub/PhaseOffset 模式在
   `onAttempt()` 之前就返回）。`attempted=7 eligible=7` 证明模式路径活着。
3. **trigger 掩码/window 问题？是。** F0 语义（`chaos_lsu_trigger.hh`）：
   `next_fire = warmup(0) + lcg(seed) % span(1000)`。实测抽取：

   ```
   seed=1: next_fire = lcg(1)%1000 = 412   （eligible 流只有 7 → 永不可达）
   seed=2: next_fire = lcg(2)%1000 = 417
   seed=3: next_fire = lcg(3)%1000 = 806
   ```

   `tools/lsu_campaign.py` `FAMILY_TIER_FLAGS["lsqfwd"]` 的家族默认
   `--lsqfwd_span_events 1000` 大于整条 eligible 流（7）→ F0 永不击发 →
   `injected=0` → 注入日志 0 行、PROP-EVT 0 事件。**与 P01-W8（prefetch
   span 1000 > ~133 eligible）同一结构类**。

## 1.2 修复：lsqfwd F0 span 改为实测流长 7（真 F0-uniform），弃 span=1

`FAMILY_TIER_FLAGS["lsqfwd"]`：`--lsqfwd_span_events 1000 → 7`。
选择依据（两个都实测过）：

- **span=1**（P01-W8 先例的做法）：必然击发，但确定性命中**第一个**
  eligible 事件 —— 实测该事件是错误路径 load `[sn:258]`（debug 日志：
  `574420: Load Instruction PC (0x40c0a0=>0x40c0a4) squashed, [sn:258]`），
  3 个 seed 全部注入在同一死事件上 → 6/6 样本完全相同（`runs/lsu/r4_t1_fixed/`，
  全 Masked，62 事件流全同）。F0"eligible 均匀抽样"退化成"永远第一个"。
- **span=7**（实测流长）：`next_fire = lcg(seed)%7 ∈ [0,6]`，必然击发
  （流长 7 ≥ 最大 next_fire+1），且按 seed 变化（真 F0-uniform）。
  seed1→第5事件（0x48fb70 buf 转发）、seed2→第3事件（0x496798）、
  seed3→第6事件（stack 转发）。

**已知限制（诚实登记）**：S08（fwd_source_sub）走
`maybeSubstituteSource` 的独立 eligible 流（需"存在更老有数据 SQ 项"），
**未测量**——若小于 7，S08 的 F0 cell 仍可能不击发；正式 campaign 应按
workload/model 实测流长重调。另：argparse 取**最后一次**出现，此 lambda
在 `FAMILY_MOUNT` 之后拼接，span 必须改在这里（MOUNT 里改会被静默覆盖，
已实验验证）。

## 1.3 关联改造：seq/idx/request_id 为 PRIMARY，地址只剩显式 fallback

用户裁决（2026-10-20）：`dyn_inst_seq`/`sq_idx`/`lq_idx`/`request_id` 必须
成为传入 `CHAOSLSQFwd` 的主关联键；仅地址关联只能作为**显式标注的
fallback** 存在。

改动（详见 commit）：

- `lsq_unit.cc` 转发点构造 `CHAOSLSQFwd::FwdCorrelKeys{store_dyn_inst_seq,
  sq_idx, store_request_id, load_dyn_inst_seq, lq_idx, load_request_id}`
  传入 `corrupt()`。**取值与下游事件同源**：store 侧 `DynInst::sqIdx`/
  `seqNum`（与 sq_execute/sq_writeback/sq_complete 同源），load 侧
  `read()` 的 `load_idx` 参数（与 lq_read 同源）；request_id 用
  Request-stamped seq（`getReqInstSeqNum()`，未盖戳=0 —— lsq_sendfrag
  约定）。
- `CHAOSPropagation::registerLSQForwardFault(...)`（新）：
  - **PRIMARY**：addr registry 条目 [vaddr, vaddr+size) 绑定**生产 store
    的 seq**（store 转发时刻必在 SQ 中 → 其 sq_writeback/sq_complete 在
    注册之后发生，按 seq 入链）。
  - **FALLBACK（标注）**：同一字节范围进 blk registry（供无 seq 的
    correlateBlock / noteMemResponse cache 分支）；与 HEAD 行为相同，现
    明确为次级。
- `lsq_fwd` 事件新增字段：`dyn_inst_seq`(消费 load)、`store_dyn_inst_seq`
  (生产 store)、`sq_idx`、`lq_idx`、`request_id`、`corr`
  （`seq_primary` | `addr_fallback`——store seq 不可得时才降级并标注）。
- `PROP_EVT_FIELDS` 注册表（C++ 与 Python 双源，pin 测试钉死）追加
  `store_dyn_inst_seq`、`corr`——发射端会丢弃未注册键，这是它们必须
  进注册表的原因。
- `REQUIRED_FIELDS["lsq_fwd"]` = fault_id, **dyn_inst_seq,
  store_dyn_inst_seq, sq_idx, lq_idx, request_id**, va, field, before,
  after（brief 列的 4 个新键 + 裁决点名的消费 load seq）。

### 仍走地址 fallback 的调用点（裁决要求逐点登记）

1. `registerLSQForwardFault` 的 blk registry 注册本身——服务于无 seq 的
   关联面（cache 结构事件 `correlateBlock`、`noteMemResponse` cache 分支）。
   设计上标注为 fallback；`lsq_fwd` 事件自身带 `corr` 标注。
2. **下游同地址观测事件未带 corr 标注**：转发注册地址上的后续 load（如
   seed 流里 dyn 294/330/…）经地址重叠入链，其 lsq_push/mem_req/
   lsq_sendfrag/tlb_translate 事件只带自己的 seq，没有"此边由地址
   fallback 关联"的标记。这些钩子是 H1/H2 共享设施（cache 家族也用），
   加标注属后续任务，本轮未动（**未解决，登记在案**）。
3. `maybeSubstituteSource`（S08）与 `maybeDelayForward`（phase_offset）
   完全不向 CHAOSPropagation 注册（诚实缺席——无链无事件，不是静默地址
   路径）；S08 的注册属其自身任务。
4. `tlb_pfn`（H2-FS）沿用地址域关联——先前裁决已登记，本轮不动。

## 1.4 契约测试

- 新增 `tests/test_lsu_hook_lsqfwd.py`（16 项全 PASS）：lsq_fwd→L3、
  必录字段（新键）、注册表双源一致（store_dyn_inst_seq/corr 两源同名同序）、
  完整行过 validate、缺键行被拒（"不得静默地址关联"）、addr_fallback
  标注可往返、sq_*/lq_read join 面字段名同源。
- 既有 suite 不回归：`python3 -m pytest tests/ -q` →
  `16 passed, 5 errors`（5 个 error 为 `test_claim_concurrency.py`
  **改动前基线即有**，与本轮无关，已在同一 worktree 改动前实测确认）。
  脚本式测试：test_lsu_prop_fields / hook_lsq / hook_lsqfwd / hook_sq /
  hook_lq / chain_check / campaign_propagation 全 ALL PASS；
  test_lsu_f6_gate exit 0。
- 构建验证（不接管道吞错）：`scons -j16 build/ARM/gem5.opt` →
  `scons exit code: 0`、`scons: done building targets.`、
  `grep -c "error:" = 0`、本轮触碰文件 0 warning。

## 1.5 真机证据（正式 campaign 入口，span=7，`runs/lsu/r4_t1_fixed2/`）

命令同 1.1（outdir 换 `runs/lsu/r4_t1_fixed2`）。

```
  S01-F0-W5: phase=trial n_runs=3 activated=3 sdc=0 stop=seed-cap(3) cons=OK
  S02-F0-W5: phase=trial n_runs=3 activated=3 sdc=0 stop=seed-cap(3) cons=OK
```

注入日志（非空，含新键；S02 为 2-bit 掩码）：

```
S01 s1: Cycle: 33479, Site: store->load_forward, FaultType: bit_flip, Vaddr: 0x48fb70, FwdSize: 8, ByteOffset: 5, Mask: 10000000, StoreSeq: 11024, SqIdx: 839, LoadSeq: 11026, LqIdx: 657
S01 s2: Cycle: 22315, ... Vaddr: 0x496798, ByteOffset: 0, Mask: 10000000, StoreSeq: 5939, SqIdx: 565, LoadSeq: 5945, LqIdx: 322
S01 s3: Cycle: 34148, ... Vaddr: 0x7ffffefd00, ByteOffset: 5, Mask: 01000000, StoreSeq: 11117, SqIdx: 855, LoadSeq: 11128, LqIdx: 677
S02 s1: ... Mask: 10000001 ...（双比特）
```

`lsu_chain_check.py` 逐边记录（seed2，18 事件，无截断）：

```
edges: {'L0->L1': 'proven' (inj@t8591275 → lsq_push, fault_id),
        'L1->L2': 'proven' (lsq_push → mem_req, fault_id+dyn_inst_seq),
        'L2->L3': 'missing', 'L3->L4': 'missing', 'L4->L5': 'missing'}
terminal: provable_to_L3_then_unknown
```

**seq 主键入链实测**（seed2 流，parent_event_id 链）：

```
kind=lsq_fwd     dyn_inst_seq=5945 store_dyn_inst_seq=5939 lq_idx=322 sq_idx=565 corr=seq_primary
kind=sq_writeback dyn_inst_seq=5939 sq_idx=565  parent_event_id=1  ← 生产 store 按 seq 入链
kind=sq_complete  dyn_inst_seq=5939 sq_idx=565  parent_event_id=3
kind=chain_end   (exit 回调)
```

**oracle 结果**（S01/S02 同型）：seed1 **Crash**（真实 guest 故障：
`panic: Page table fault when accessing virtual address 0x4b9000`——被
污染的转发值被用作地址；exit=-6，流截断前缀 5 事件被 C1 路径保留，
`truncated=true`）；seed2/seed3 Masked（终态 checksum == golden
`1f4cbf14327717df`）。

**不受影响族回归**（S04-F0-W5，addrpath 家族，1 seed，正式入口）：
`activated=1`，`addrpath_injections.log` 非空（`FUNNEL: attempted=772
eligible=412 injected=1`），chain `provable_to=L3`——共享的
lsq.cc/lsq_unit.cc/CHAOSPropagation 改动无附带破坏。

## 仍未解决（诚实清单）

- **L3→L4 断链**：转发 load 经 `WritebackEvent→writeback()` 完成，不经
  `completeDataAccess→noteMemResponse`，故无 resp/taint_reg——被污染值
  进入目的寄存器这一步在事件流中不可见（`lsu_chain_check` 的
  `L3->L4: missing`）。链终于 L3、`beyond=Unknown`。
- 下游同地址观测事件（1.3 节第 2 条）无 corr 标注。
- S08（fwd_source_sub）eligible 流未测量、未接 CHAOSPropagation。
- 本轮 6 样本无 SDC（seed1 的 Crash 是地址型消费；checksum 型消费在
  seed2/3 落在被 squash/无下游读取的转发上）。样本量 3+3 仅为证据性
  pilot，**非正式 campaign**。

## R4-1-fix（评审 Important 1/2 修复，2026-10-20，binary 14a1c7fe3418a3d8）

### I1：fallback 关联事件现在显式携带 corr 标注

评审裁决："仅地址关联只能作为带标注的 fallback 存活"——但其**消费者**此前
无标注：经 `correlateRequest` 的 blk 臂 / `correlateBlock` 加入链的事件与
seq 关联边在 PROP-EVT 流中不可区分（含消费 load 的下游同地址观测事件，
即 §1.5 呈现为 "proven" 的 L0→L1→L2 边实为地址关联、未标注）。

修复：`CHAOSPropagation::{correlateRequest, correlateRequestBySeq,
correlateBlock, noteMemRequest}` 全部增加 `const char **corr_out` 出参
（seq 绑定臂 → `seq_primary`；仅地址 blk 臂 → `addr_fallback`；
`CORR_SEQ_PRIMARY`/`CORR_ADDR_FALLBACK` 常量单源定义于
CHAOSPropagation.hh）；`noteMemResponse` 内部记录命中臂并在 `lq_complete`
上发射。21 个调用点（lsq.cc×3 / lsq_unit.cc×4 / mmu.cc×2 / cache.cc×4 /
base.cc×5 / queued.cc×3）全部传出命中臂并把 `{"corr", ...}` 写进事件；
`tools/lsu_prop_fields.py` 将 corr 列入一切"经 correlate* 加入链"的 kind
的必录字段（`pf_demand`/`pf_fill` 除外——允许 fault_id=0 的纯预取链，
corr 留空是诚实缺席）。

真机（`runs/lsu/r4_t1_i2_fixed/`，正式 campaign 入口 6 样本）：所有
fault-correlated 事件 corr 缺失数 = **NONE**；S01 s2 逐事件摘录：

```
lsq_fwd        seq=9904  store_seq=9901 corr=seq_primary    va=48fb70
sq_writeback   seq=9901                  corr=seq_primary
sq_complete    seq=9901                  corr=seq_primary
lsq_push       seq=10275                 corr=addr_fallback va=48fb70   <- 消费 load 的下游观测，现在显式标注
lsq_sendfrag   seq=10275                 corr=addr_fallback
tlb_translate  seq=10275                 corr=addr_fallback
```

即评审指出的"L0→L1→L2 地址关联未标注"边现在全部带 `corr=addr_fallback`
（5 个下游 load，seq 10275/10312/10897/10968/10970），seq 关联边
（lsq_fwd→sq_writeback→sq_complete）带 `corr=seq_primary`。

### I2：span 从家族常量改为逐 (模型,负载) 实测 + 双失效模式响亮告警

- **S08 结构性修复**：`maybeSubstituteSource`（fwd_source_sub 的注入点）
  此前从不查询 lsuTrigger（tier flags 对 S08 完全惰性，注入走 legacy
  Bernoulli）。现与 corrupt() 相同走 `onAttempt/onEligible`——S08 的 F0
  由此获得与其他 S 模型一致的"eligible 流上均匀"契约。
- **逐 (模型,负载) 实测**（真实运行，tier=F0 + span=10^6 使抽样永不落地，
  teardown `eligible=` 即流长；测量 binary cd49e8dfabe531c4）：

```
S01@sq_forward: attempted=7  eligible=7  injected=0
S02@sq_forward: attempted=7  eligible=7  injected=0
S03@sq_forward: attempted=7  eligible=7  injected=0
S08@sq_forward: attempted=2  eligible=2  injected=0   <- fwd_source_sub 自身的流（alt-SQ-entry 机会），不是 7
S09@sq_forward: attempted=7  eligible=7  injected=0
L03@sq_forward: attempted=571   eligible=571   injected=0
L03@sqlite_like: attempted=18681 eligible=18681 injected=0
```

  L03 证明**模型级 span 表不成立**（同模型两负载差 33 倍）→
  `LSQFWD_F0_SPAN` 以 `(model, binary)` 为键；未测量对**响亮拒绝**
  （resolve_cell → BLOCKED(F0-span-unmeasured)，guard 侧 lsu_runner 同样
  SystemExit），绝不静默复用他对流长。
- **真 F0-uniform 参数化**：`warmup=1 + span=N` ⇒ next_fire=1+lcg%N ∈[1,N]
  每事件 1/N（旧 `warmup=0+span=7` 双计事件 1 且事件 7 永不可达——那是
  真实存在的偏置，本轮修正）。
- **teardown 响亮告警**（chaos_lsu_trigger.hh summary，紧随
  CHAOS_LSU_TRIGGER 行；campaign 汇总行再升一层 `ALARM <RunID>: ...` 并
  写入 cell_results.json）：
  - `SPAN_UNREACHABLE`：attempted>0 && injected==0（span 不可达）
  - `EARLY_BIAS`：injected>0 && eligible≥warmup+span，携带
    `fired_at`（命中时的 eligible 计数）并诚实区分两种读法：span 低覆盖
    golden 流（真偏置）vs 注入故障自身延长流（非采样偏置，事后裁决）。

### I2 真机验证（正式 campaign 入口，S01/S02 各 3 seed）

```
S01-F0-W5: phase=trial n_runs=3 activated=3 sdc=0 stop=seed-cap(3) cons=OK
S02-F0-W5: phase=trial n_runs=3 activated=3 sdc=0 stop=seed-cap(3) cons=OK
```

- seed1/seed3：eligible=7（=实测 golden）、injected=1、**无告警**。
- seed2：eligible=8、injected=1、fired_at=4 → EARLY_BIAS 告警触发；
  **裁决为故障延长**（非偏置）：无注入 golden 三次实测 7；注入在事件 4
  （Cycle 32810, LoadSeq 9904），被污染值被 5 个下游同地址 load 消费
  （corr=addr_fallback 链），产生第 8 个 eligible——超出部分全部晚于
  fired_at。此为告警设计内的诚实行为（trigger 无法区分两种读法，
  消息同时列出并给出裁决键 fired_at）。
- **旧偏置配置对照**（warmup=0+span=7，/tmp/r4_i2_measure/oldbias*）：
  seed2 fired_at=3、seed3 fired_at=6 均 EARLY_BIAS 告警（窗口 [0,6) 永不
  覆盖事件 7）；seed1 注入后 guest 页表 fault Abort（与上轮 Crash 同型）。
  即：若沿用旧配置，告警在每个完成 seed 上都会响——它确实抓得住评审
  所指的 silent early bias。
- 链路：6 样本全部 `provable_to=L3`（terminal provable_to_L3_then_unknown，
  L3→L4 断链仍是上一轮诚实清单第 1 条，未变）。

## R4-2（2026-10-20）：`sq_execute` 根因定论 + 修复 + 真实观测，Store Queue 7/7

> 基线 `2de6c332`（binary `14a1c7fe3418a3d8`），修复重建后 binary
> `cb58c9ed01ed7eb7`（sha256 前缀）。改动仅
> `CHAOS/gem5/src/cpu/o3/lsq_unit.cc::executeStore` 钩子位置。

### 2.1 定论（真实 `--debug-flags=LSQUnit` 输出，非猜测）

两个假设**按载体分属**，均有实测输出：

**(b) 对 S01/S02（lsqfwd 转发污染载体）成立——被注入指令是 load。**
定向运行（与 campaign 解析出的 flags 一致 + debug）：

```bash
CHAOS/gem5/build/ARM/gem5.opt --outdir /tmp/r4t2_s01_pre --debug-flags=LSQUnit \
  --debug-file=lsqunit.log configs/se/lsu_proxy.py \
  --cmd workloads/directed/sq_forward --cpu O3 --chaos_lsqfwd \
  --lsqfwd_lsu_tier F0 --lsqfwd_warmup_events 1 --lsqfwd_span_events 7 \
  --lsq_struct_mode byte_flip --rng_seed 2 \
  --chaos_propagation --prop_run_id S01-F0-W5 --prop_sample_run_id s2
```

注入日志（`lsq_fwd_injections.log`）：`Cycle: 32810, Site: store->load_forward,
..., Vaddr: 0x48fb70, ..., StoreSeq: 9901, SqIdx: 793, LoadSeq: 9904, LqIdx: 587`
（Cycle×385=tick 12631850）。debug 追踪（`/tmp/r4t2_s01_pre/lsqunit.log`）：

```
12631465: Executing store PC (0x444470=>0x444474) [sn:9901]   ← 生产 store 先执行（比注入早 385 tick）
12631850: Executing load PC (0x4448a4=>0x4448a8) [sn:9904]    ← 受害指令是 load
12631850: Read called, load idx: 586, store idx: 794, storeHead: 792 addr: 0x74b70
12631850: CHAOSLSQFwd: corrupted forwarded byte 0 (vaddr=0x48fb70 mask=0x80 type=bit_flip)
12631850: Forwarding from store idx 793 to load to addr 0x48fb70
$ grep -c "Executing store.*sn:9904]" /tmp/r4t2_s01_pre/lsqunit.log
0                                                              ← 受害 load 永不进入 executeStore
```

即：`corrupt()` 污染的是 **load 的 memData**（lsq_unit.cc:1687，
`cpu->lsqFwd->corrupt(load_inst->memData, ...)`）；生产 store 的 executeStore
（tick 12631465）**早于**注入（12631850）——其 seq 注册发生在它执行之后。
**任何钩子位置都无法为该载体诚实地发射 sq_execute**（发射即把事件回溯到
inj 根之前）。按任务预案的裁决路径：SQ 执行期观测的载体是 store 侧模型。

**(a) 对 S04–S07/S11/S13（agu_pre store 侧载体）成立——但精确形态是
"同一 executeStore 调用内钩子在注册之前"，不是 dispatch-vs-issue。**
定向运行（S04-F0-W5 s1，同上形式 + `--chaos_addrpath --addrpath_lsu_tier F0
--addrpath_warmup_events 0 --addrpath_span_events 1000 --agu_pre_mode
s04_store_subst --addrpath_rng_seed 1`）。注入日志：
`Tick: 5920530, Site: lsq_pushRequest_PRE, mode=s04_store_subst,
old_addr=0x4903e8, new_addr=0x490250, ..., isLoad=0, isStore=1`；
PROP-EVT `inj` 事件 `dyn_inst_seq=3998 tick=5920530`。debug 追踪：

```
5918990: Inserting store PC (0x402b18=>0x402b1c) idx:338 [sn:3998]  ← dispatch（另一拍）
5920530: Executing store PC (0x402b18=>0x402b1c) [sn:3998]          ← executeStore 开始（旧钩子在此，查不到注册）
5920530: Doing write to store idx 338, addr 0x75250 [sn:3998]       ← initiateAcc→writeMem→pushRequest 已注入并注册（0x75250=被替换地址 0x490250 的 paddr）
5929385: D-Cache: Writing back store idx:339 ... [sn:3998]          ← sq_writeback 可关联（已注册）
5930155: Completing store [sn:3998]                                 ← sq_complete 可关联
```

注册点 `registerInjection("lsq_pushRequest_PRE", inst->seqNum, ...)` 在
`LSQ::pushRequest`（lsq.cc:793），经 `DynInst::writeMem → cpu->pushRequest`
（dyn_inst.cc:449）被**同一个 executeStore 调用里的 `initiateAcc()`**（原
lsq_unit.cc:755）同步调到——旧钩子（原 :726，函数顶部）在其**之前**执行，
故 `correlateRequestBySeq(3998)` 返回 0、不发事件；而 sq_writeback/
sq_complete 在注册之后发生，正常落流。这正是第三轮 G3 观察到的不对称。

### 2.2 修复

`lsq_unit.cc::executeStore`：sq_execute 钩子从函数顶部**移到
`initiateAcc()` 之后**（翻译延迟早退之前）。键不变（R4-1 的
seq/sq_idx：`correlateRequestBySeq(store_inst->seqNum)` +
`DynInst::sqIdx`）；字段契约不变（fault_id/corr/dyn_inst_seq/sq_idx/va/
state_before，`tools/lsu_prop_fields.py` REQUIRED_FIELDS 未动）。
被污染 store（S04 载体，pushRequest 处污染自身地址）由此在执行时刻
按 seq 入链；S01/S02 的生产 store 执行早于注入，sq_execute **诚实保持
缺席**（不回溯造假）。翻译延迟重进（FS PTW 路径）按实际执行遍数发射
（SE 载体实测每 store 恰好一次 "Executing store" 行）。

修复后同一定向运行（binary `cb58c9ed01ed7eb7`，`/tmp/r4t2_s04_post/`），
sq_execute 出现且链完整：

```
PROP-EVT: kind=sq_execute run_id=S04-F0-W5 sample_run_id=s1 fault_id=1 event_id=7
  parent_event_id=6 tick=5920530 cycle=15378 dyn_inst_seq=3998 sq_idx=339
  va=490250 state_before=issued ... corr=seq_primary
```

链：inj(1)→addr_form(2)→lsq_push(3)→mem_req(4)→lsq_sendfrag(5)→
tlb_translate(6)→**sq_execute(7)**→sq_writeback(8)→resp(9)→sq_complete(10)，
全链 `dyn_inst_seq=3998`，`sq_idx=339` 与 lsq_push/sq_writeback/sq_complete
同源一致。

### 2.3 真机证据（正式 campaign 入口）

```bash
LSU_GEM5_BIN=$PWD/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py \
  --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv \
  --outdir runs/lsu/r4_t2_sqexec --cells S04-F0-W5 \
  --phase trial --max-seeds-per-cell 3 --max-parallel 1
```

```
  S04-F0-W5: phase=trial n_runs=3 activated=3 sdc=0 stop=seed-cap(3) cons=OK
```

逐 seed（`runs/lsu/r4_t2_sqexec/S04-F0-W5/`）：

| seed | oracle | 流 | Store Queue 单元节点（7 项） |
|---|---|---|---|
| s1 | Crash（被替换地址触发 guest 页表 fault，exit=-6） | 截断前缀 10 事件 | inj/lsq_push/lsq_sendfrag/**sq_execute**/sq_writeback/sq_complete（无 chain_end——Crash 截断，C1 路径保留前缀） |
| s2 | Masked | 完整 11 事件 | **7/7**（含 chain_end） |
| s3 | Masked | 完整 11 事件 | **7/7**（含 chain_end） |

s2 的 sq_execute：`dyn_inst_seq=4015 sq_idx=344 va=490a80 corr=seq_primary
tick=5942475`；s3：`dyn_inst_seq=8579 sq_idx=723 va=4976a0 corr=seq_primary`。
三 seed 链终点均 `provable_to=L3`（`chain_report.json`：
`terminal=provable_to_L3_then_unknown`）。触发漏斗（run.out）：
`attempted=2582 eligible=1307 injected=1`（s1 同型）。

**不受影响族回归**（同入口，S01-F0-W5 3 seed，`runs/lsu/r4_t2_s01_regr/`）：
`activated=3 sdc=0 stop=seed-cap(3) cons=OK`，三 seed 链型与 R4-1-fix 完全
一致（lsq_fwd→sq_writeback→sq_complete + 5 个 addr_fallback 下游 load +
chain_end），且**无 sq_execute**（诚实缺席，符合 2.1(b) 的定论）；seed2
的 EARLY_BIAS 告警与 §R4-1-fix I2 记录同型（已裁决为故障延长）。

### 2.4 诚实登记

- **addrpath F0 span 未测量（Task-1 parked 项，本轮如实再现）**：S04
  seed2/seed3 出现 `EARLY_BIAS ... eligible=1307 span=1000` 告警——
  span=1000 < 实测 eligible 流 1307，属 R4-1-review-I2 已 park 的
  "addrpath/prefetch F0 span 不在 lsqfwd 表内"的既有偏置检测，本轮未修
  （修它=给 LSQFWD_F0_SPAN 之外建 addrpath 表，超出本任务单元）。
- **S01/S02（转发污染载体）sq_execute 结构性缺席**：见 2.1(b)。这不是
  缺陷而是因果事实——受害指令是 load，生产 store 的执行先于故障存在。
  SQ 执行期观测由 store 侧载体（S04–S07/S11/S13）承担。
- `lsq_fwd` 事件 `parent_event_id=0`（根事件显式 0 而非空串）——修复前
  后逐字节一致（/tmp/r4t2_s01_pre vs /tmp/r4t2_s01_post），R4-1 既有发射
  行为，本轮未动，登记备查。
- 本轮 3+3 样本为证据性 pilot，**非正式 campaign**。


## R4-3（2026-10-21）：mshr_alloc 双根因定论 + 钩子修复 + 可重复 evict→refill 载体，L1d-Cache 11/11

> 基线 `15fa094b`（binary `cb58c9ed01ed7eb7`），修复重建后 binary
> `2462dc0fcf1d3d96`（sha256 前缀）。改动两件：`base.cc` mshr_alloc 钩子
> 卫条件修复 + 新定向负载 `workloads/directed/cache_mshr_refetch.c`。

### 3.1 根因定论（真实 `--debug-flags=Cache` 输出 + gem5 命令表，非猜测）

此前结论（§3 旧文）：注入行必须"先驱逐再取回"（evict→refill）才可能观测
mshr_alloc。**R4-3 实测证明这是必要不充分条件**——构造出可重复载体后
merge/fill/free 全落流、alloc 仍缺席。定向 debug 运行（载体 s1 复跑 +
`--debug-flags=Cache`，`/tmp/r4t3_dbg/cache.log`）：

```
47051620: l1d-cache-0: access for ReadReq [76e00:76e07] miss
47052390: l1d-cache-0: sendMSHRQueuePacket: MSHR ReadReq [76e00:76e07]
47052775: l1d-cache-0: handleTimingReqMiss coalescing MSHR for ReadReq [76e08:76e0f]
47057780: l1d-cache-0: recvTimingResp: Handling response ReadResp [76e00:76e3f]
```

miss→MSHR→coalesce→fill 全链真实发生在故障行 0x76e00 上，地址关联命中
（同 tick 的 merge/fill/free 事件都在流里），唯独 alloc 缺席。根因：
`base.cc::handleTimingReqMiss` 的 alloc 钩子卫条件 `pkt->hasData()`。
gem5 的 **request 包不带 payload**：`ReadReq` 属性 `{IsRead, IsRequest,
NeedsResponse}`（`packet.cc` 命令表），无 HasData；只有 response 和
`WriteReq`（`{IsWrite, NeedsWritable, IsRequest, NeedsResponse, HasData}`）
带。该卫条件**结构性丢弃一切 demand-read miss**——"miss→MSHR allocate"
（规格表 9 C 链 L2）的规范场景。同一根因解释 P01（预取链）只见
merge/fill/free 从未见 alloc：SoftPFReq/HardPFReq 亦无 HasData。

### 3.2 修复

`base.cc` mshr_alloc 钩子：`if (h4a && pkt && pkt->hasData())` →
`if (h4a && pkt)`。到达该处的包必是分配 MSHR 的 miss（eviction/WriteClean
此前已分流 writebuffer），读/写/预取一视同仁；correlateBlock/corr 标注/
字段契约（fault_id, corr, cache_line, mshr_id）全部未动，
`lsu_prop_fields.py` 未动。构建：`scons -j126` exit 0、
`done building targets`、error/warning 计数 0（base.cc 单文件重编）。

### 3.3 载体：cache_mshr_refetch.c（可重复 evict→refill）

- 48KiB 连续 region = L1D（32KiB/2-way/64B，256 组）每组恰好 3 行 →
  顺序全扫时**每行每轮必然 miss**（2-way LRU）；每轮另做 noinline
  volatile 栈帧读写（栈行同样每轮驱逐→重取）；region 外启动杂项行在
  round 0 后不可再被抽中。单轮 ≈28K cycle ≈10.8M tick < 20M tick
  注册窗 → 注入后 ≤1 轮内该行必再 miss。
- 值只进 checksum（绝不当地址）→ 不 crash，链到 chain_end。

### 3.4 真机证据（定向载体 ×6 seed + campaign 入口 ×2 cell）

载体（C09 data_shift flags + `--chaos_propagation`，first_clock=40000）：
**6/6 seed 全部观测 mshr_alloc，alloc 的 cache_line 与注入行逐一相同**
（s1:76e00/s2:78180/s3:7ed40/s4:7e300/s5:77780/s6:79500；每 seed
alloc=2 merge=13-14 fill=2 free=2——恰好 2 轮落在 20M tick 注册窗内，
第 3 轮起注册过期事件停发）。s1 完整 ID 链：

```
inj(76e00@40000000) → cache_evict+cache_writeback(76e00@43823780) →
mshr_alloc(76e00, mshr_id=1 @47051620) → mshr_merge×3(76e08/e10/e18,
mshr_id=1) → mshr_fill(76e00, mshr_id=1, fill_id=1 @47057780) →
cache_fill(pa=76e00, fill_id=1) → mshr_free(76e00, mshr_id=1 @47057780)
```

`lsu_chain_check.py`：**L0→L1→L2→L3→L4→L5 全 proven，terminal=full**
（cache 家族首个满深链）。故障行驱逐时为脏（warm-up 写脏；fill 后 L1D
持 M/dirty 态），writeback 把损坏数据带回 L2、refill 取回损坏数据 →
6/6 checksum 偏离 golden 682fe66c2cbbec4b（SDC）——**故障数据经 MSHR
refill 真实传播**，非仅地址巧合。

**归因口径**：alloc 的 miss 地址==故障行 → 分配的 MSHR 就是**故障行自己的
MSHR**（mshr_id 1/2 与 merge/fill/free 同 ID 闭环）；关联方式为地址
（blk registry，corr=addr_fallback——cache 故障无 seq 主键，R4-1 契约的
显式 fallback 臂）。少量 merge 来自相邻行 load（64B 关联窗口与注册区间
重叠，mshr_id=0=查无此行）——correlateBlock 块窗口既有语义，corr 标注
如实区分，不计入归因。

campaign 入口诚实对照：
- **C09-F0-W6**（W6=cache_dirtyevict，家族 first_clock=1000，3 seed，
  `runs/lsu/r4_t3_c09w6/`）：`activated=6 sdc=0 stop=seed-cap(3) cons=OK`，
  三 seed prop_evt **均无 mshr_\* 事件**——W6 单遍相位结构对故障行的重取
  在 phase 4，超出 20M tick 注册窗；cell 语义不变、如实保留。
- **S04-F0-W5 不受影响族回归**（3 seed，`runs/lsu/r4_t3_s04_regr/`）：
  `activated=3`，三 seed 事件流与 R4-2 记录（`runs/lsu/r4_t2_sqexec/`）
  **逐 kind 且 seed2 逐字节一致**——base.cc 卫条件移除对无关联 miss 的
  链零影响（钩子只在 correlateBlock 命中时发射）。seed2/3 的 EARLY_BIAS
  告警与 R4-2 §2.4 记录同型（addrpath span parked 项，未变）。

### 3.5 覆盖矩阵

`pilot_evidence.json` 重生成（20 pilot：原 13 项全保留、S04-F0-W5 重指向
R4-2 sqexec 运行、新增 C09-F0-W6 与载体 ×6）；`coverage_matrix.md` 重生成：
**PASS=199 / PARTIAL=0 / BLOCKED=126**（前值 101/98/126）——199 个非阻塞
cell 全部节点均有真实运行证据（L1d-Cache 11/11 补 mshr_alloc、Store Queue
7/7 补 sq_execute）；126 BLOCKED 均为外部阻塞（FS/multicore/SPEC）。
`atomic_op` 仍诚实未观测（O 系全 BLOCKED=multicore-FS，载体不可用）。

### 3.6 诚实登记

- 载体 6 样本 + campaign 2 cell 均为证据性 pilot，**非正式 campaign**。
- 载体的 `--l1d_first_clock 40000` 是定向运行参数（campaign 家族默认 1000
  不变）；该值经实测校准（warm-up+round0 完成于 ~85K cycle 前，
  40e6 tick=104K cycle 落在 round 3 附近）。
- 相邻行 merge（mshr_id=0）是 correlateBlock 块窗口语义的既有行为，
  修复前后一致（修复前 merge 已如此发射），本轮未改关联语义。
- `mshr_alloc` 修复后亦会为**软件预取 miss** 发射（此前同被 hasData 屏蔽；
  SoftPFReq 分配 MSHR 是事实行为）——本轮未在预取载体上复测，登记备查。
