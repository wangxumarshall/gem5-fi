# R0202-T02F2-SEED1-DIAG — T02-F2-W4：seed 身份表达 + F2 多 fault 判定一致性 + 整数 seed 1 诊断复现

**结论（先给结果）**：**NOT-ACCEPTED（情况 B）**。

- 0101 R6 的 T02-F2-W4 **seed1 成功轨迹可以在 0202 复现**：显式整数 seed `1` 的
  diagnostic run 里 **fault 1 独立形成完整连续 parent-event 的 L0→L5**
  （`inj → … → errant_commit`，五条边全 proven），与 0101 记录的 seed1 `terminal=full/L5`
  一致；且**按修复前（pre-U7）的旧准入规则，该样本 `admitted=True, path=full_chain,
  violations=[]`** —— 与 0101 的 `certified=True/admitted=True` 完全对齐。
- 但**按本轮确立的保守 all() 规则**（每个 activated fault 都必须独立闭合）该样本
  **不 admitted**：fault 2 止于 L4、第 3 次注入的事件在 **gem5 断言崩溃（SIGABRT）**
  中丢失，证据流被截断（`truncated=True`、无 `chain_end`、无 funnel 摘要）。
- 该崩溃是 **gem5 自身的 cache 模型断言**（`src/mem/cache/base.cc:783
  BaseCache::recvTimingResp: Assertion 'mshr' failed`），**不是** parent-event 发射器的
  确定性错误 ⇒ **不是情况 C**；也**没有**修改 checker。

机器可读：`R0202-T02F2-SEED1-DIAG.json` / `.csv`；
修复前后逐 fault 基线与六项复判：`R0202-T02F2-PRE-U7-BASELINE.json` /
`R0202-T02F2-POST-U7-BASELINE.json`。
原始证据（未提交）：`runs/lsu/0202_t02f2_legacy_seed1_diag_20261027T000814/`
（标 `DIAGNOSTIC_REPLICATION_ONLY`）。

---

## 1. seed 语义：修改前 vs 修改后

| | 修改前 | 修改后（U6） |
|---|---|---|
| 轴 | 只有派生轴 `sample_index` | 派生轴 **或** 显式轴（互斥） |
| seed 值 | `lsu_seed(run_id, phase, sample_index)`（64 位哈希） | 派生同左；显式则直接取整数原值 |
| manifest 字段 | `sample_index`, `seed`, `seed_rule` | `sample_index`, `seed`, **`seed_source`**, `seed_rule`, **`explicit_seed`** |
| 下发 | `--tlb_rng_seed <哈希>` | `--tlb_rng_seed <哈希>` 或 `--tlb_rng_seed <整数>` |
| 运行目录标签 | `s<sample_index>` | 派生 `s<idx>`；显式 `x<seed>`（**不混用同一身份轴**） |
| 命名风险 | `sample_index=0` 易被误读为"数值 seed1" | 显式禁止该表述；两轴同给即响亮失败 |

复算核对：`lsu_seed("T02-F2-W4","engineering",0)` = `14201167915699637708`（= 0202 六项里
T02-F2-W4 实际使用的值），`lsu_seed(...,1)` = `9077160986263414499`。
**整数 seed `1` 与上述任何一个都不相等。**

## 2. 0101 的整数 seed1 与 0202 的哈希 seed 是不同样本

- 0101 R6 campaign：整数 seed（`lsu_campaign.py:2884` "Seeds are 1..N per cell"；
  `:2923` 目录 `seed{seed}`；`:2536` `--tlb_rng_seed str(seed)`）。真实证据
  `docs/gem5-fi/lsu/mdspec/R4-8-SPEC-residual-report.md:170` 实测命令行含
  `--tlb_rng_seed 1`，落在 `.../seed1/`。
- 0202 runner（修复前）：哈希 seed（`lsu_runner.py:175`）。
- ⇒ 0202 的 hash-seed T02-F2-W4（seed `14201167915699637708`）与 0101 的 seed1
  （整数 `1`）在**注入点/RNG 轨迹上就不同**，是**两个不同样本**，结论不可互相替代。
  0101 记录（`R6-EVIDENCE-DEDUP.md:20-22`）：T02-F2-W4 seed1 `terminal=full`、
  `certified=True`、`admitted=True`。

## 3. 多 fault 判定：旧 vs 新

**修复前**（三处选择器不一致，同一事件流上可指向不同 fault）：
`check_admission` = `max by len(path_event_ids)`；`containment_from_events` =
`max by len(chain)`；`lsu_campaign` 顶层 terminal = `sorted(faults)[0]`。
仓库中多 fault 样本的准入口径**无定义**（全仓检索 `tests/`、`mdspec/`、完整清单、
R6 裁决文档均无）。

**修复后**（U7，保守 `all()`）：每个实际 activated fault 必须独立形成
（a）连续 parent-event 完整 L0→L5，或（b）真实/非 lifecycle/字段完整的提前 containment；
任一未闭合 ⇒ 整样本不 admitted。三个消费者改为**消费同一份 per-fault 结果**
（`evaluate_sample`）；`containment_from_events(fault_id=None)` 在多 fault 时返回 `None`
（拒绝静默重选）。**未放宽任何 checker 规则**，未改 fault model / F2 周期 / jitter /
oracle / checkpoint / binary。

### 3.1 对现有六项 raw evidence 的离线复判（old → new）

| RunID | faults | pre-U7 admitted/path/terminal | post-U7 admitted/path/terminal | 变化 |
|---|---|---|---|---|
| T01-F0-W4 | 1 | True / full_chain / full | True / full_chain / full | 无 |
| T02-F0-W4 | 1 | True / full_chain / full | True / full_chain / full | 无 |
| **T02-F2-W4** | 1,2 | **False / None / provable_to_L4_then_unknown** | **False / None / 同** | 无 |
| T04-F0-W4 | 1 | True / full_chain / full | True / full_chain / full | 无 |
| T04-F2-W4 | 1,2 | True / full_chain / full | True / full_chain / full | 无 |
| T04-F6-W4 | 1 | True / full_chain / full | True / full_chain / full | 无 |

**零样本被提升为 PASS，零样本被降级** —— 六个样本的 `admitted`/`path`/`terminal` 与
修改前逐字节相同。U7 在这六个流上是**潜在一致性修复**（三处选择器恰好都指向 fault 1），
其实际收紧效果体现在下文 §5 的 seed1 诊断样本上。

## 4. 当前 hash-seed T02-F2-W4 的两个 fault 逐条 verdict（保持 NOT-ACCEPTED）

| fault | activated | terminal | provable_to | contained | fault admission | 根因 |
|---|---|---|---|---|---|---|
| 1 | True | `provable_to_L4_then_unknown` | L4 | False | **False** | 有 `errant_commit`(ev32, det=L5) 但与其 L4 见证(ev22) 分属 event 4 的两个子分支 ⇒ 无单一路径覆盖 L4→L5（`cross_branch_edge`） |
| 2 | True | `provable_to_L4_then_unknown` | L4 | False | **False** | 含住主张只写在**生命周期** `chain_end`(ev2938, corr=none) 上 ⇒ 不构成检测/含住证据 |

样本级：`admitted=False`，`all_activated_faults_closed=False`。**未改动**该结果，
raw evidence 原样保留（`runs/lsu/0202_verify6_20261026T221213/runs/engineering/ITEM-049_engineering_s0/`）。

## 5. 显式整数 seed 1 诊断运行

| 项 | 值 |
|---|---|
| 标签 | **`DIAGNOSTIC_REPLICATION_ONLY`**（不进入正式统计） |
| manifest | `runs/lsu/0202_t02f2_legacy_seed1_diag_20261027T000814/manifest/ITEM-049_explicit_seed1.json` |
| seed | `1`（`seed_source=explicit`, `explicit_seed=1`, `sample_index=null`） |
| 命令关键片段 | `… --tlb_fault_type bit_flip --tlb_bits_to_change 2 --tlb_lsu_tier F2 **--tlb_rng_seed 1** --chaos_propagation --prop_run_id T02-F2-W4 **--prop_sample_run_id s1**` |
| binary | `a99031a86e8e108b9278af53044d873a8262ea20d73bd7d94c6dba1300b49e0a`（同一 freeze） |
| checkpoint | `cpt.239515184727`（同一）；golden `b6d81b360a5672d80c27430f39153e2c` |
| 并发 | **1**（单进程） |
| tier | `CHAOS_LSU_TIER_CAP: requested=F2 effective=F2 lookup_tier_enabled=1`（F2 未坍缩） |
| 计数 | `injected=3`, `activated=3`, `conservation=OK`；**`attempted`/`eligible = null`（funnel 缺失）** |
| 终止 | `exit_code=-6`（**SIGABRT**），`src/mem/cache/base.cc:783 BaseCache::recvTimingResp: Assertion 'mshr' failed`，abort tick `240017009067` |
| stream | `truncated=True`、`n_events=2620`、`chain_end` 缺失、Unknown=0、fault_id ∈ {1,2}（**第 3 次注入无任何事件**） |

三次注入（`armtlb_injections.log`）：
`239515618626`（tier 臂）、`239589696141`（`0x81cf1→0x800400000081cf1`，Mask `0x800400000000000`）、
`240016366044`（`0x1c090→0x1c191`，Mask `0x101` —— 目标 PFN 落在**低地址/设备区**，
`0x1c090000` 即 PL011 UART 地址区）。断言紧随第 3 次注入发生。

### 5.1 逐 fault 结果与 ancestry

| fault | activated | terminal | provable_to | contained | fault admission | n_path |
|---|---|---|---|---|---|---|
| **1** | True | **`full`** | **L5** | False | **True** | 6 |
| 2 | True | `provable_to_L4_then_unknown` | L4 | False | False | 5 |

**fault 1 完整 ancestry（连续父链，根为该 fault 自己的 `inj`）**：
```
inj → tlb_lookup → tlb_pfn → tlb_translate_result → sq_execute → sq_writeback →
cache_access → cache_return → mshr_alloc → cache_access → cache_return → mshr_alloc →
resp → taint_reg → sq_complete → errant_commit (det=L5, outcome=errant_commit)
```
路径 event_id = `['0','1','2','4','28','44']`，五条边 `L0->L1 … L4->L5` 全部 `proven`。

**fault 2 ancestry**：`inj → tlb_lookup → tlb_pfn → tlb_translate_result → lq_read →
cache_access → cache_access → resp → lq_complete → taint_reg`（止于 L4）。

### 5.2 是否复现 0101 的完整链

| 判据 | 0101 记录（`R6-EVIDENCE-DEDUP.md`） | 本次 seed1 诊断 |
|---|---|---|
| 主 fault terminal | `full` | **`full`** ✅ |
| provable_to | L5 | **L5** ✅ |
| 修复前规则下的样本 admitted | True（`certified=True`） | **True**（`path=full_chain`, `violations=[]`）✅ |
| 修复后规则下的样本 admitted | —（0101 无此规则） | **False**（fault 2 未闭合） |

⇒ **0101 的成功轨迹在 0202 复现**（主 fault 的完整 L0→L5 链重现，且旧规则下同样准入）；
区别在于本轮新增的保守 all() 规则与本次运行的**仿真器断言截断**共同使它不构成严格 PASS。

### 5.3 严格验收逐项

| 项 | 结果 |
|---|---|
| attempted/eligible/injected/applied/activated 守恒 | injected=3=activated=3，`conservation=OK`；但 **attempted/eligible=null（funnel 缺失，abort 未跑退出回调）** ⇒ 不满足 |
| F2 effective tier 未坍缩 | ✅ `requested=F2 effective=F2 lookup_tier_enabled=1` |
| stream 完整 / gzip EOF / `truncated=False` | ❌ `truncated=True`（SIGABRT） |
| 各 fault 从自己 `inj` 起始有连续父链 | ✅ fault 1、fault 2 均 `ancestry_root_is_own_inj=True` |
| request/corr 合法连续 | ✅ fault 1 逐事件 corr ∈ {origin,seq_primary,taint_prop} |
| terminal 为真实检测/真实含住 | fault 1 ✅ `errant_commit`；fault 2 ❌ 止于 L4 |
| `chain_end` 不参与 terminal 准入 | ✅ 未参与（`chain_end` 全程缺失） |
| 无跨 fault / 跨 request / 跨 sibling 拼链 | ✅ 无 |
| 无 Unknown | ✅ 0 |
| 样本级用所有 activated fault 的 `all()` | ❌ 因此不 admitted |

## 6. 测试与退出码

| 套件 | 结果 |
|---|---|
| `tests/test_lsu_runner_explicit_seed.py`（U6 专项，20 项） | **ALL PASS** rc=0 |
| `tests/test_lsu_multifault_admission.py`（U7 专项，26 项） | **ALL PASS** rc=0 |
| `tools/lsu_test_runner.py` 全套 | **suites=90 PASS=72 FAIL=15 SKIP=3**；**NEW FAIL=0**（15 个 FAIL 与基线**同名同集合**：陈旧 hook 合成链缺 `parent_event_id`、依赖 gitignored `runs/` 状态、约定不匹配） |
| 六项离线复判 | admitted/path/terminal **零变化** |

## 7. 身份

| 项 | 值 |
|---|---|
| 分支 / HEAD | `fix/0202-six-chain-20261026` / `fa40428a`（U6 `d1038e97`、计划 `c81b3a07`） |
| gem5 binary SHA256 | `a99031a86e8e108b9278af53044d873a8262ea20d73bd7d94c6dba1300b49e0a`（**未变**） |
| checkpoint | `runs/lsu/0202_fs_cpt_boot_20261026T193235/cpt.239515184727` |
| golden | `b6d81b360a5672d80c27430f39153e2c` |
| 原始证据（本次诊断） | `runs/lsu/0202_t02f2_legacy_seed1_diag_20261027T000814/` |
| 原始证据（hash-seed 六项，未改动） | `runs/lsu/0202_verify6_20261026T221213/` |

## 8. 诚实限制

- **L1（证据在仿真器断言下丢失）**：gem5 在 `BaseCache::recvTimingResp` 断言后 SIGABRT，
  进程不跑退出回调 ⇒ 传播流缺 gzip trailer 与 `chain_end`、缺 funnel 摘要，
  且**已缓冲的第 3 次注入事件全部丢失**（stream 只见 fault 1/2，而注入计数为 3）。
  仓库既有 R6-GRACEEXIT 只覆盖**超时**（SIGINT）路径，未覆盖**断言中止**。
  彻底修复需在 tracer 侧周期性 flush/收口（C++ 改动）——**本次未改 C++**，
  故列为候选 DECISION REQUEST：*是否让 CHAOSPropagation 在异常中止时也保留可读前缀*
  （拟改文件 `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc`；
  错误事件 = 第 3 次注入 `fault_id=3` 的事件全部缺失；为何违反既有语义：
  现有语义要求"每个 activated fault 都有可核查的事件链"，而 abort 路径下
  已 activated 的 fault 可以零事件，违反 L0 观测完备性）。
- **L2（仿真器断言 vs 架构结局）**：本次 abort 是 gem5 cache 模型断言，属
  **post_activation_simulator_failure**，不应计入架构级 Crash/SDC。第 3 次注入把
  低地址（`0x1c090000`，PL011 UART 区）的映射位翻成 `0x1c191000`，访问该设备映射
  触发断言。**无证据**表明 parent-event 发射器存在确定性错误（因此不是情况 C）。
- **L3（未重复运行）**：按任务约束只跑 seed 1 一次（且 FS 本身非比特可复现，见
  `R0202-VERIFY6.md` H3），故"断言是否每次必现"未作重复采样，不下结论。
- **L4（funnel 缺失不等于 0）**：abort 路径下 `attempted/eligible=None`，按仓库规则
  **不得**填 0；本次如实记 `null`。

## 9. 停止

- 已完成：只读复核、修改前基线复现、U6（seed 身份）、U7（多 fault 一致性）、
  显式整数 seed 1 单进程诊断复现、逐 fault 严格验收、报告。
- 未运行：seed 2/3、其他 seed、其他 RunID、pilot/screening/confirmatory/325 formal。
- 未改动：checker 严格性、现有失败 raw evidence、`R0202-VERIFY6.*`、fault model、
  F2 周期/jitter、oracle、checkpoint、binary、C++。
- 结论：**NOT-ACCEPTED（情况 B）** + §8 L1 的候选 DECISION REQUEST。
