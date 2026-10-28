# R6-A4 最终报告（2026-10-29）— A 单元补救轮：88/90 合格，A08-b 结构性阻塞

## 1. 结论先行（如实）

- 本轮只重跑 R6-A3 未合格的 25 个 (RunID, seed)，**未重跑任何已合格的 65 个样本**。
- **25 格中 23 格合格**（真实注入、正常收口、admitted=True、certified=True、
  violations=[]、conservation=OK、三方注入计数一致）；与上一轮 65 格合并 =
  **88/90 合格**。
- **剩余 2 格（A08-F2-W3 seed2、A08-F2-W5 seed2）是结构性不可达，不是工具
  缺陷、也不是可用 repeat 修复的 NO_FIRE**：A08-b（even seed 的 pair_swap
  子模型）的合格流只统计“同 tick store 先/load 后且同 4KiB 页”的配对
  事件，实测 E1=E5=E10=21（repeat 完全不增加配对 eligible，delta=0）。
  F2 的确定性首火位是 eligible 序数 99,417（seed2），该流永远到不了。
  按用户裁决“达不到时响亮 BLOCKED、不伪造”，resolver 对这两个格输出
  `BLOCKED(delta<=0)`，未注入、未生成样本，也没有用 oracle 推断合格。
- 达到 90/90 需要用户裁决（见 §8），本报告不擅自改实验规格。

## 2. 二进制与来源（混合来源，逐项标注）

| 范围 | 样本数 | 二进制 SHA-256 | binary_source_head |
|---|---|---|---|
| 上一轮 R6-A3（保留，未重跑） | 65 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 本轮 R6-A4（25 格重跑，23 合格） | 23 | `a1632e0f1d24be639044d24bac8e6fd902d0a6642b276fd430927471643e7046` | `167a23ee59b3a2383cdd1eaeeca418b263666a56` |

- 构建：`scons -j16 build/ARM/gem5.opt` → `SCONS_EXIT=0`；本轮改动文件 0 编译警告
  （日志 `/tmp/r6a4_build.log`）。
- workload 仅把 `chaos_repeat.h` 的 `CHAOS_REPEAT_MAX` 4096→131072 后重建；
  四个 golden 输出逐字不变（W3 `728e604ffcec539d` / W0 `07568da9f3ad5665` /
  W5 `1f4cbf14327717df` / W9 `030921682b3731f2`），workload 身份不变。
- 每个样本 manifest 记录 cmd / binary_sha256 / binary_source_head /
  matrix_sha256 / PID+PGID / 起止时间 / timeout / exit_code / .done。

## 3. 25 个重跑样本逐格结果

| RunID | seed | oracle | terminal | admitted | certified | injected | repeat（ITER 实测） | 备注 |
|---|---|---|---|---|---|---|---|---|
| A01-F1-W3 | 2 | Masked | detected_contained | True | True | 1 | 4023（4023） | |
| A01-F2-W3 | 2 | Masked | detected_contained | True | True | 1 | 434（434） | |
| A01-F2-W9 | 1 | Crash | detected_contained | True | True | 1 | 1（0） | |
| A01-F2-W9 | 2 | Masked | full | True | True | 1 | 1（0） | |
| A01-F2-W9 | 3 | Crash | detected_contained | True | True | 1 | 1（0） | |
| A02-F2-W9 | 1 | Masked | full | True | True | 1 | 1（0） | |
| A02-F2-W9 | 2 | Crash | detected_contained | True | True | 1 | 1（0） | |
| A02-F2-W9 | 3 | Crash | detected_contained | True | True | 1 | 1（0） | |
| A04-F2-W3 | 1 | Masked | full | True | True | 1 | 1021（1021） | |
| A04-F2-W3 | 3 | Masked | detected_contained | True | True | 1 | 1021（1021） | |
| A04-F2-W0 | 1 | Masked | full | True | True | 1 | 375（375） | |
| A04-F2-W0 | 3 | Masked | full | True | True | 1 | 375（375） | |
| A05-F2-W3 | 1 | Masked | detected_contained | True | True | 1 | 785（785） | |
| A05-F2-W3 | 2 | Masked | detected_contained | True | True | 1 | 785（785） | |
| A05-F2-W3 | 3 | Masked | detected_contained | True | True | 1 | 785（785） | |
| A06-F2-W3 | 3 | Masked | detected_contained | True | True | 1 | 1123（1123） | |
| A06-F2-W5 | 3 | Masked | detected_contained | True | True | 1 | 1295（1295） | |
| A07-F0-W3 | 1 | Masked | detected_contained | True | True | 1 | 1（0） | |
| A07-F0-W3 | 2 | Masked | detected_contained | True | True | 1 | 1（0） | |
| A08-F2-W3 | 1 | Masked | detected_contained | True | True | 1 | 15706（15706） | |
| A08-F2-W3 | 2 | — | BLOCKED(no sample) | — | — | 0 | 1 | A08-b delta=0 结构不可达（repeat 不增加配对 eligible） |
| A08-F2-W3 | 3 | Masked | detected_contained | True | True | 1 | 15706（15706） | |
| A08-F2-W5 | 1 | Masked | detected_contained | True | True | 1 | 84418（84418） | |
| A08-F2-W5 | 2 | — | BLOCKED(no sample) | — | — | 0 | 1 | A08-b delta=0 结构不可达（repeat 不增加配对 eligible） |
| A08-F2-W5 | 3 | Masked | detected_contained | True | True | 1 | 84418（84418） | |

## 4. 根因与修复（全部有真实证据）

### 4.1 F2 NO_FIRE 的 repeat 重标定（Lane A）

- F2 首火位在 eligible 序数空间，seed 决定（`chaos_lsu_trigger.hh`
  `scheduleNext` + `chaosSampleLCG`），独立重算：
  **seed1=106,412 / seed2=99,417 / seed3=140,806（max）；1.2×max=168,967.2**。
  冻结二进制真实在 eligible=106,412 发射（A01-F2-W9 r1 FUNNEL 行逐位印证）。
- 旧 `REPEAT_FACTOR` 按**裸访存流**标定；A04-a/A05-d/A06/A08 的 eligible 是
  **子模型过滤后**的流。新增 `tools/lsu_repeat_census.py`，用真实 campaign
  命令构造（同一二进制/频率/seed/seed-parity 子模型），repeat=1/5/10 三点
  测 E1/delta；delta 在 5 与 10 差异 >2% 时取 min 并以第三点复核。
- 关键测量陷阱：F2 一旦在测量运行中真实注入，会截断 eligible 流
  （A01-F2-W9 r1 注入后 eligible 106,414 vs 未注入 264,751）。census 对受污染
  的键用 `--addrpath_warmup_events 10000000`（超出流长，完全不触发）重测
  未注入流；tier/seed/LCG 不变。
- 计算：`R = 1 + ceil((1.2*max_first_fire − E1_filtered)/delta_filtered)`。
  子模型键 `(model, freq, binary, submodel)`，submodel 由 seed 奇偶唯一推导；
  `resolve_cell(seed=...)` 选键，缺键仍响亮 BLOCKED。
- 上界：`REPEAT_MAX=131072`（config + workload + 新二进制一致），依据
  `REPEAT_MAX_BASIS`：A08-a W3 R=15,706 实测 161.3 s（~10 ms/iter），
  W5 R=84,418 实测约 9 分钟；超过上界响亮 BLOCKED，不无限循环。
- gap_bfs F2：未注入流 E1=264,751（新器件 264,774）≥ 1.2×max ⇒ **R=1**，
  首趟即确定性首火；A01/A02-F2-W9 六格不再 BLOCKED。

### 4.2 maxFaults 在 LSU trigger 路径真正生效

长 repeat 的 F2 会在第一个间隔后再次发射（census 实测 injected=2），而配置
声明 `maxFaults=1`。修复：`maybeCorrupt` / `maybeCorruptAguOperands` /
`maybePairA08` / `maybeCorruptPre` 在真实注入点前检查配置上限
（A05 ISA hook 的 claim 块在其之前，单个合法故障的 EA 绑定不被跳过）。
canary 与 25 格全部 `injected=1`，三方计数一致（CHAOS_LSU_TRIGGER /
addrpath FUNNEL / campaign）。

### 4.3 A07-b 真实 ready-delay 生命周期与可证终局（Lane B）

- 真实钩子：`maybeDelayAguReady`（IEW memRef ready 点）注入；`resumeDeferredAgu`
  在真实 delayed tick 重入并观测 `isSquashed()`；`Commit::commitHead` 真实
  退休、`Commit::squashAll`/commit squash 真实取消。watchdog 不参与 A07-b。
- 新 prop 事件（单一 ancestry）：
  `inj`（ready_tick/delayed_tick/delay_cycles/state_before=ready/state_after=delayed，
  request_id=dyn_inst_seq=seq） →
  `ready_delay_resume`（parent=inj，consumed=1，squashed=0|1） →
  `ready_delay_squashed`（parent=resume，outcome=contained，dl=L4，
  reason=squash_before_retire）或 `ready_delay_retired`（dl=L5，
  delay_transparent_retire）或 `ready_delay_discarded`（dl=L4，
  squash_after_resume_before_retire）。
- 本单元两个真实 seed 都是 resume-squashed：
  真实值 `ready_tick=12,606,440 → delayed_tick=12,606,825`、
  `resume tick=12,606,825, consumed=1, squashed=1`、
  `ready_delay_squashed tick=12,606,825, dl=L4, contained=1`，
  `chain_end tick=19,928,370 > squash`。checker 的
  `check_a07b_lifecycle` 逐字段/逐 ancestry/tick 校验后判 `detected_contained`。
- 诚实边界：resume 时的 squash 触发原因（例如分支误预测）未记录；
  `parent_event_id` 表达链归属，不是因果。终局是“该延迟访存未退休、其架构
  影响消失”的真实生命周期观测，不是 oracle 推断。

### 4.4 两个 A01 Masked 的真实 squash containment（Lane C + checker）

- 真实流（两 seed 同构）：注入单 bit EA → `addr_form` → `mem_req` →
  `lsq_sendfrag` → `tlb_translate` → `tlb_fault(detection_layer=Hardware,
  contained 空)` → `LSQUnit::squash` 在 pop 点真实发射
  `squash_discarded(dl=L4, contained=1, outcome=contained,
  state_before=load_queue_uncommitted, request_id≡mem_req)` → `chain_end`。
- 翻译 fault 的请求**从未进入下游**，L3 见证结构性缺失；旧通用规则要求
  L0→L3 前缀因此误拒。新白名单
  `_a01_translation_squash_witness` 要求：全 run_id=A01、family=agu、
  唯一 fault/squash/chain_end（chain_end 在流末且 corr=none/outcome=run_end/
  contained=0/dl 空）、squash 字段精确、严格 ancestry 七事件序列、
  request_id/dyn_inst_seq/va 全等且非空、inj 确有改值、
  tlb_fault=Hardware 且 contained≠1、tick 非降、squash 后无任何更深真实观测、
  链内禁 arch/consumer/taint/errant/L3 族；终局/准入另要求 oracle=Masked 且
  rc=0。通用门禁未放宽（`test_lsu_r6a2_gate_negatives.py` 全过；新增 15 个
  正负组合用例覆盖 Lane C 的 G1–G8/G17–G20）。
- 结论：这两格是**真实 Masked**（请求被真实 discard，未退休、无架构污染），
  不是“oracle 干净所以 Masked”。

## 5. 测试与回归（真实命令/输出）

- 定向：`python3 tests/test_lsu_r6a4_a01_squash_terminal.py` → ALL PASSED；
  `tests/test_lsu_r6a4_a07b_lifecycle.py` → ALL PASS（含 checker 集成）；
  `tests/test_lsu_r6a4_a07b_admission.py` → ALL PASSED；
  `tests/test_lsu_r6a2_gate_negatives.py` → ALL PASSED；
  `tests/test_lsu_prop_fields.py` → ALL PASS。
- repeat：`pytest tests/test_lsu_r6a4_repeat_census.py -m "not slow"` → 15 passed；
  `python3 tests/test_lsu_r6a2_repeat.py` → ALL PASSED。
- 完整回归：`pytest tests -q -m "not slow"
  --ignore=tests/test_lsu_r6_reconcile_realroot.py` → **170 passed, EXIT=0**。
  - `tests/test_lsu_r6_reconcile_realroot.py` 是脚本式测试（import 期执行并
    `sys.exit`），pytest 无法收集（既有测试入口问题）；其两项计数断言按
    **全证据目录**扫描，新增样本目录即改变计数（evaluated 64 / evidence_missing
    203 vs 旧期望 62/201），属既有 ledger 测试对证据根敏感，非本轮代码回归。
  - 两个 lane 已复核的既有失败（`test_lsu_ready_contract_category.py`、
    `test_lsu_runid_map.py` 的 A06 陈旧断言）在 HEAD 工具下同样失败，与本轮无关。

## 6. 25 格重跑的验收明细

全部 23 个合格样本满足：RunID/seed 身份正确；二进制 SHA 与本轮候选一致；
`injected=1`；三方计数一致；exit_code=0；gzip 完整；stats 非零；
terminal ∈ {full, detected_contained}；admitted=True；certified=True；
violations=[]；conservation=OK；无 cross_request_edge / time_reversed_edge /
truncated。逐 seed 文档见
`runs/lsu/R6_COMPLETE_PROPAGATION_PATHS/<RunID>/seedN.md`。

## 7. 90 格状态表

| RunID | s1 | s2 | s3 | 合格 |
|---|---|---|---|---|
| A01-F0-W3 | ✅ | ✅ | ✅ | 3/3 |
| A01-F0-W9 | ✅ | ✅ | ✅ | 3/3 |
| A01-F1-W3 | ✅ | ✅ | ✅ | 3/3 |
| A01-F1-W9 | ✅ | ✅ | ✅ | 3/3 |
| A01-F2-W3 | ✅ | ✅ | ✅ | 3/3 |
| A01-F2-W9 | ✅ | ✅ | ✅ | 3/3 |
| A02-F0-W3 | ✅ | ✅ | ✅ | 3/3 |
| A02-F0-W9 | ✅ | ✅ | ✅ | 3/3 |
| A02-F2-W3 | ✅ | ✅ | ✅ | 3/3 |
| A02-F2-W9 | ✅ | ✅ | ✅ | 3/3 |
| A03-F5-W3 | ✅ | ✅ | ✅ | 3/3 |
| A03-F5-W10 | ✅ | ✅ | ✅ | 3/3 |
| A04-F0-W3 | ✅ | ✅ | ✅ | 3/3 |
| A04-F0-W0 | ✅ | ✅ | ✅ | 3/3 |
| A04-F2-W3 | ✅ | ✅ | ✅ | 3/3 |
| A04-F2-W0 | ✅ | ✅ | ✅ | 3/3 |
| A05-F0-W3 | ✅ | ✅ | ✅ | 3/3 |
| A05-F2-W3 | ✅ | ✅ | ✅ | 3/3 |
| A06-F0-W3 | ✅ | ✅ | ✅ | 3/3 |
| A06-F0-W5 | ✅ | ✅ | ✅ | 3/3 |
| A06-F2-W3 | ✅ | ✅ | ✅ | 3/3 |
| A06-F2-W5 | ✅ | ✅ | ✅ | 3/3 |
| A07-F0-W3 | ✅ | ✅ | ✅ | 3/3 |
| A07-F0-W5 | ✅ | ✅ | ✅ | 3/3 |
| A07-F4-W3 | ✅ | ✅ | ✅ | 3/3 |
| A07-F4-W5 | ✅ | ✅ | ✅ | 3/3 |
| A08-F0-W3 | ✅ | ✅ | ✅ | 3/3 |
| A08-F0-W5 | ✅ | ✅ | ✅ | 3/3 |
| A08-F2-W3 | ✅ | ❌(None/None) | ✅ | 2/3 |
| A08-F2-W5 | ✅ | ❌(None/None) | ✅ | 2/3 |

## 8. A08-b 结构性阻塞（唯一未达 90/90 的原因）与可选裁决

- 事实：A08-b 的合格流在 W3/W5 上 E1=E5=E10=21，delta=0（census 三次独立
  测量一致）；F2 首火位 seed2=99,417、max=140,806，远大于 21。repeat 只重复
  同一 workload，不改变“同 tick store 先/load 后且同页”的发生条件
  （首个冷启动迭代产生 21 次，热迭代为 0）。
- 不伪造：resolver 输出 `BLOCKED(delta<=0)`，未运行、未注入；没有改用 A08-a
  冒充 even seed；没有改 F2 阈值/seed/算法；没有换 workload 身份。
- 达到 90/90 需要修改实验规格之一（需用户裁决）：
  (a) 承认 A08-b 在 F2 下不适用（该子模型只适合 F0/F5/F6 事件触发），
      把 A08-F2-W3/W5 seed2 标为 `n/a(F2-not-applicable)` 并计入完成；
  (b) 为 A08-b 定义事件触发档（例如 F6 same-tick-pair 事件），但这改变频率法；
  (c) 更换 A08-b 的 workload（改变 workload 身份）；
  (d) 允许 even seed 使用 A08-a（改变注入模型）。
  本轮严格按原规格执行，未选择任何一项。

## 9. 合并 origin/fi-ding 的条件

- 未合并 `origin/fi-ding`（仍为 `659fa4cf6ea2095e178f43df9f177bff8260bda2`）。
- A 单元当前 88/90；按用户完成条件（90/90）**尚未满足**，因此不具备合并
  条件。除 A08-b 两格外，其余工程/文档/证据均已落地并推送。
