# R6-FIXB — checker 终局语义修复（L5/containment 只认真实检测事件；截断流不得含住准入）

Owner: Lane B（检查器唯一负责人）。
Branch: `r6-fixb`（base `07c004e5`）。独占文件：`tools/lsu_chain_check.py`、
`tests/test_lsu_chain_check.py`、`tests/test_lsu_r6_reconcile_realroot.py`。
**不**改 C++、`tools/lsu_campaign.py`、`tools/lsu_ready_contract.py`。不 push 集成分支。

## 根因（3 条 lane 独立确认）

`chain_end`（CHAOSPropagation 退出回调发射的**生命周期标记**，`corr=none`）在**两处**
被当成真实 L5：

1. `containment_from_events`：只需 `contained∈{1,true,…}` + 非空 `detection_layer` +
   非空 `outcome`，**未**要求 `kind` 非生命周期、**未**要求链关联 `corr` —— 于是
   `chain_end`（`detection_layer=L5 contained=1 outcome=errant_commit_seen corr=none`）
   被采信为含住见证，返回 `layer=L5` 的"含住束"。
2. `_terminal()` 的"explicit contained"扫描：读**原始** `detection_layer`/`contained`，
   吃掉了 `chain_end` 自带的 `contained=1` → 判 `detected_contained`。

**决定性证据（P6，`runs/lsu/r6_p1_T01-F0-W4/T01-F0-W4/seed2`）**：真流 425 事件，
真实 L4→L5 见证 = `errant_commit`(event 259, `detection_layer=L5 outcome=errant_commit
corr=taint_prop`)；`chain_end`(event 424) 带 `contained=1 detection_layer=L5`。
原样 → `detected_contained`；删掉 `chain_end` → 翻成 `full`。即 `chain_end` 不仅冒充
L5，还在**拉低**真实结论。

第三处（缺陷 #5，独立）：`containment_from_events` 不区分证据流是否**完整**。真实
`T06-F0-W4` / `T08-F0-W4` 的 `prop_evt.txt.gz` **被截断**（`read_events` → `trunc=True`），
却在截断流上被判含住准入（`ready_contract.json` 里唯一的 2 个 `chain.admitted=True`）。
C++ 侧铁证（`CHAOSPropagation.cc:438`）："a crash/abort sample never reaches the exit
callback, **so the gz chain_end is absent**" —— 即 `chain_end` 的有无就是"流是否完整收口"
的带内标记；含住（"故障止于 Ln，之后无传播"）是对**缺席**的断言，只在流完整时可证。

## 修法（One patch per unit：本计划 = 1 commit）

`tools/lsu_chain_check.py`：

- [x] **T1** `_explicit_l5` 收口第 1 处：`containment_from_events` 的见证筛选改为
      `contained ∈ _CONTAINED_VALUES` **且** `_explicit_l5(e)` **且** 关键字段非空
      （零字节关键证据拒收）**且** `_event_has_prefix` **且** 无更深层见证。
- [x] **T2** 收口第 2 处：`_terminal()` 的 "explicit contained" 扫描改为
      `contained ∈ _CONTAINED_VALUES` **且** `_explicit_l5(e)`。`chain_end`（生命周期，
      `corr=none`）由构造永不命中 → P6 形状翻回 `full`。
- [x] **T3** 含住主张须建立在**完整（已收口）**的流上：
      `containment_from_events(events, run_id, fault_id=None, truncated=False)` 在
      `truncated=True` 或 `not _stream_closed(chain)`（无 `chain_end`）时返回 `None`；
      `check_admission` 额外接受 `bundle["truncated"]`/`bundle["evidence_truncated"]`，
      并在"存在含住候选却拿不出束"时**响亮**点名
      `containment_on_unclosed_stream` / `containment_on_truncated_stream`
      （登记进 `GATE_VIOLATIONS`）。`GATE_VIOLATIONS` 新增两 token。

测试（TDD：真实 FAIL → 实现 → 真实 PASS）：

- [x] **T4** `tests/test_lsu_chain_check.py` 新增 [17]/[18]：
      chain_end-only（富化载荷）→ 不得 `full`、不得 admitted、束=`None`；
      截断真流（T08）→ 不得因 containment 准入 + 响亮原因；显式 `truncated=True` →
      同拒；**合法含住（同形状 + `chain_end` 收口）→ 仍 admitted=True**（反证不过度收紧）；
      P6 真流：删/不删 `chain_end` 结论`同` `full`。
- [x] **T5** `tests/test_lsu_r6_reconcile_realroot.py`：§6 合法含住夹具补 `chain_end` 收口；
      §8/§9 把"T06/T08 因截断流被准入"的**过期结论**改为**更强**断言（不得准入 + 响亮
      点名截断），契约 `admitted` 由 2 变 0（逐条引用真实命令输出）。
- [x] **T6** 依赖同一结论的既有套件同步收口（`tests/test_lsu_ready_contract_gate.py`、
      `tests/test_lsu_ready_contract_chain_wiring.py`）：断言点从"T08 admitted=True"
      改为"工位照跑 + 如实判 False"，并用**已收口的合法含住**夹具证明 option-2 通路
      仍可达（不弱化、不删除）。

## 验证（真实输出）

- [x] `python3 tests/test_lsu_chain_check.py`（改动前 FAIL → 改动后 ALL PASS）
- [x] `python3 tests/test_lsu_r6_reconcile_realroot.py`
- [x] `python3 tools/lsu_test_runner.py`：基线 `FAIL=13`，**NEW FAIL 必须为 0**；
      不得把 FAIL 改写成 SKIP/ENV；不跑 pilot。
- [x] 逐条引用真实命令输出（契约 `chain_gate` 计数、T08/T06 判决）。

## 诚实边界 / 未决风险

- 含住准入在**当前**证据下从 2 行（旧 T06/T08，皆截断流）变为 **1 行**：截断的 T06/T08
  一律不再准入，而**完整**运行的 T05-F0-W4（`truncated=False` + `chain_end` 收口）成为唯一
  准入行——这不是"收紧到拒绝合法含住"（合法含住仍可准入），也不是"放宽"：旧口径下
  **只有截断流解得开**（`chain_end` 被当成更深的 L5 见证，反而挡住已收口的样本），
  收口后方向被扶正。
- `lsu_ready_contract.py`（他 lane 所有，禁止改）未透传 `truncated`；本修法用带内收口标记
  自证，无需该文件配合。若他 lane 后续透传 `truncated`，本检查器同样遵守（双信号）。

## 验证实录（真实命令输出）

TDD：新断言先**真实 FAIL**（改动前 `python3 tests/test_lsu_chain_check.py`）：
`FAIL chain_end-only 诚实止于 L4（provable_to_L4_then_unknown） provable_to_L0_then_unknown` /
`FAIL P6：chain_end 的存在不改变结论（不被拉低） detected_contained vs full` /
`FAIL 截断流不得推出含住束（束=None）` / `FAIL 截断流不得因 containment 被准入` /
`FAIL 已收口的合法含住证据 → 束合法（layer=L2 / na=L3,L4,L5） None`。

实现后（真实输出）：

- `python3 tests/test_lsu_chain_check.py` → `ALL PASS`（含 `INFO P6 带 chain_end=full / 删除后=full`）
- `python3 tests/test_lsu_r6_reconcile_realroot.py` → `ALL PASS`，其中
  `INFO chain_gate={'admitted': 1, 'evaluated': 64, 'unproven': 44,
  'evidence_missing': 197, 'blocked_upstream_admitted': ['T05-F0-W4']}`，
  `INFO T08-F0-W4: admitted=False ... violations=["containment_on_unclosed_stream: ..."]`
- `python3 tests/test_lsu_ready_contract_gate.py` → `ALL PASS`
- `python3 tests/test_lsu_ready_contract_chain_wiring.py` → `ALL PASS`
- `python3 tools/lsu_test_runner.py` → `suites=61 ENV=5 FAIL=13 PASS=42 SKIP=1`；
  FAIL 集合与基线（`pytest::collect` + 11 个 `test_lsu_hook_*` + `campaign_propagation`）
  **逐条相同** ⇒ **NEW FAIL = 0**；未把任何 FAIL 改写成 SKIP/ENV。

## 未决风险

- `T05-F0-W4` 由「未准入」翻为「准入」（完整运行的真实含住证据，`outcome=NoFault`
  + `field=effective_pa_unchanged` + `contained=1`）：这是"含住只在完整流上可证"的
  必然结果（旧口径**只有**截断流解得开，即缺陷 #5 的反面）。`outcome=NoFault`
  是否应算"真实检测"属**发射端词汇表**问题（他 lane 所有），本 lane 未改。
- `tools/lsu_ready_contract.py`（他 lane 所有，禁止改）未透传 `truncated`；本修法
  靠带内收口标记自证，无需其配合。
