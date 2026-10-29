# R6-A4 最终报告（2026-10-29，收口）— A 单元：88/88 applicable qualified + 2 SPEC_EXCLUDED

## 1. 结论先行（权威口径）

- **applicable_samples=88；qualified_applicable_samples=88；
  spec_excluded_samples=2；failed_applicable_samples=0；
  unit_status=COMPLETE_WITH_SPEC_EXCLUSIONS。**
- 规范表述：**88/88 applicable samples qualified; 2/2 structurally
  inapplicable samples explicitly excluded; 0 applicable failures; A unit
  closed as COMPLETE_WITH_SPEC_EXCLUSIONS.**
- 本轮只重跑 R6-A3 未合格的 25 个 (RunID, seed)，**未重跑任何已合格的 65 个
  样本**。25 格中 **23 格合格**（真实注入、正常收口、admitted=True、
  certified=True、violations=[]、conservation=OK、三方注入计数一致）。
- 两个 SPEC_EXCLUDED 样本（A08-F2-W3 seed2、A08-F2-W5 seed2）由用户
  2026-10-29 裁决按“规格不适用项”收口：`status=N/A`、
  `classification=SPEC_EXCLUDED`、
  `reason=A08-b structurally unreachable under F2`。它们**不是 PASS、不是
  FAIL**，admitted/certified 为空，无传播链，不计入 88 的 applicable 分母。
- 本报告**不把结果写成 90/90 PASS**。

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
| A08-F2-W3 | 2 | — | N/A (SPEC_EXCLUDED) | — | — | 0 | 1 | A08-b structurally unreachable under F2；E1=E5=E10=21、delta=0、首火位 99,417；不注入、无传播链 |
| A08-F2-W3 | 3 | Masked | detected_contained | True | True | 1 | 15706（15706） | |
| A08-F2-W5 | 1 | Masked | detected_contained | True | True | 1 | 84418（84418） | |
| A08-F2-W5 | 2 | — | N/A (SPEC_EXCLUDED) | — | — | 0 | 1 | A08-b structurally unreachable under F2；E1=E5=E10=21、delta=0、首火位 99,417；不注入、无传播链 |
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
- **同源复核（新二进制 a1632e0f…，与 25 格重跑同一二进制）**：
  `runs/lsu/r6_a4_census_newbin/summary.json` + 逐 run manifest（config/workload
  pin + SHA）。15 键 repeat=1/5/10 + R 处 verify；所有可运行键 verify
  `injected=1`（maxFaults 封顶生效），三方计数一致；A08-a W3 R'=15,349
  （161.9 s）、W5 R'=84,418（520.7 s）、W9 R=1；A08-b 两键仍 `delta<=0`。
  正式样本使用的是表内 R（旧冻结 census 标定，W3=15,706/W5=84,418），
  均 **≥** 新 census 的最小 R，同样满足 ≥1.2×max 覆盖（不是伪造）。
  旧二进制 census 与 summary 完整保留（`summary.frozen_c52ef225.json`、
  `batch_manifest.frozen_c52ef225.json`），未删除任何证据。

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
- 同源慢测试：`pytest tests/test_lsu_r6a4_repeat_census.py -q -m slow`
  → **1 passed**（真实 gem5：A05-d-W3 R=785，injected=1，三方计数一致，
  15706/84418 等 R 的 ITER 行数完整；证据二进制与 batch_manifest 一致）。
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
`runs/lsu/R6_COMPLETE_PROPAGATION_PATHS/<RunID>/<RunID>-seedN.md`。

## 7. 90 格状态表（30 非 F6 RunID × seed1/2/3）

| RunID | s1 | s2 | s3 | applicable | qualified |
|---|---|---|---|---|---|
| A01-F0-W3 | PASS | PASS | PASS | 3 | 3 |
| A01-F0-W9 | PASS | PASS | PASS | 3 | 3 |
| A01-F1-W3 | PASS | PASS | PASS | 3 | 3 |
| A01-F1-W9 | PASS | PASS | PASS | 3 | 3 |
| A01-F2-W3 | PASS | PASS | PASS | 3 | 3 |
| A01-F2-W9 | PASS | PASS | PASS | 3 | 3 |
| A02-F0-W3 | PASS | PASS | PASS | 3 | 3 |
| A02-F0-W9 | PASS | PASS | PASS | 3 | 3 |
| A02-F2-W3 | PASS | PASS | PASS | 3 | 3 |
| A02-F2-W9 | PASS | PASS | PASS | 3 | 3 |
| A03-F5-W3 | PASS | PASS | PASS | 3 | 3 |
| A03-F5-W10 | PASS | PASS | PASS | 3 | 3 |
| A04-F0-W3 | PASS | PASS | PASS | 3 | 3 |
| A04-F0-W0 | PASS | PASS | PASS | 3 | 3 |
| A04-F2-W3 | PASS | PASS | PASS | 3 | 3 |
| A04-F2-W0 | PASS | PASS | PASS | 3 | 3 |
| A05-F0-W3 | PASS | PASS | PASS | 3 | 3 |
| A05-F2-W3 | PASS | PASS | PASS | 3 | 3 |
| A06-F0-W3 | PASS | PASS | PASS | 3 | 3 |
| A06-F0-W5 | PASS | PASS | PASS | 3 | 3 |
| A06-F2-W3 | PASS | PASS | PASS | 3 | 3 |
| A06-F2-W5 | PASS | PASS | PASS | 3 | 3 |
| A07-F0-W3 | PASS | PASS | PASS | 3 | 3 |
| A07-F0-W5 | PASS | PASS | PASS | 3 | 3 |
| A07-F4-W3 | PASS | PASS | PASS | 3 | 3 |
| A07-F4-W5 | PASS | PASS | PASS | 3 | 3 |
| A08-F0-W3 | PASS | PASS | PASS | 3 | 3 |
| A08-F0-W5 | PASS | PASS | PASS | 3 | 3 |
| A08-F2-W3 | PASS | N/A (SPEC_EXCLUDED) | PASS | 2 | 2 |
| A08-F2-W5 | PASS | N/A (SPEC_EXCLUDED) | PASS | 2 | 2 |

说明：N/A (SPEC_EXCLUDED) 不是 PASS/FAIL；A08-F2-W3 与 A08-F2-W5 的 applicable=2、qualified=2（seed2 被规格排除，不进入分母）。F6 RunID 属独立的 F6 政策排除，与本轮两个 A08-b N/A 互不混淆。

## 8. A08-b 两个样本的 SPEC_EXCLUDED 收口（用户裁决 2026-10-29）

- 事实：A08-b 的合格流在 W3/W5 上 E1=E5=E10=21，delta=0（census 三次独立
  测量一致）；F2 首火位 seed2=99,417、max=140,806，远大于 21。repeat 只重复
  同一 workload，不改变“同 tick store 先/load 后且同页”的发生条件
  （首个冷启动迭代产生 21 次，热迭代为 0）。
- 不伪造：resolver 输出 `BLOCKED(delta<=0)`，未运行、未注入；没有改用 A08-a
  冒充 even seed；没有改 F2 阈值/seed/算法；没有换 workload 身份。
- 用户裁决（2026-10-29）：接受两格为规格不适用项，按
  `status=N/A` / `classification=SPEC_EXCLUDED` /
  `reason=A08-b structurally unreachable under F2` 收口。
- 两格明确：不是 PASS、不是 FAIL；没有 admitted=True；没有 certified=True；
  没有生成伪造传播链；不计入 88 个可执行样本的分母；不再补跑；
  原始 BLOCKED/census 证据完整保留（未删除、未改写）。
- 没有换 seed、没有换 workload、没有改成 A08-a、没有修改 F2 频率定义。

## 9. 合并 origin/fi-ding（收口后执行）

- 合并前 `origin/fi-ding` = `659fa4cf6ea2095e178f43df9f177bff8260bda2`。
- 用户裁决：A 单元按 `COMPLETE_WITH_SPEC_EXCLUSIONS` 收口后，将 A 分支以
  `--no-ff` 合并进 fi-ding（保留 A 单元边界），不使用 force push。
- 合并提交与推送结果见 `R6-A4-PROGRESS.md` 的“最终状态”与 git 历史；
  本报告的计数口径不因 merge commit 改变。
