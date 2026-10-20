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
