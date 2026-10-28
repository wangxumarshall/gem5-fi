# R6-V4 T 单元收口最终报告（2026-10-28）

> 工作树 `…/worktrees/r6-f5-noeffect-20261026`；接手 HEAD `2848cd98`（= origin/fi-ding，干净）。
> 本轮最终分析工具头 = 本报告所在提交（见 git log）；三次统一构建的二进制见 §4。
> 权威逐格状态：`R6-V4-T-STATUS.{md,json}`；逐 seed 传播文档：`../R6_COMPLETE_PROPAGATION_PATHS/`（83 份）。
> 口径遵守：不重跑已达 COMPLETE_3_OF_3 的旧 RunID；不跑 F6；不用 SKIP/XFAIL；不放宽 admission；
> 不改原始 `prop_evt*`；不手改 `chain_report`；不把 `chain_end`/截断/强杀当 L5。

## 1. 修改文件与提交

| 提交 | 根因/内容 | 文件 |
|---|---|---|
| `0d49d357` | armtlb 计数接受 `old_<field>/new_<field>` 状态/属性替换行（T05/T06 真实注入被判 malformed） | `tools/lsu_campaign.py`, `tests/test_lsu_campaign_armtlb_count.py` |
| `4e670105` | T08-b/c/d 一次性故障不再重复计数（arm 计一次，refill 不加） | `CHAOSArmTLB.cc` |
| `a0250d51` | T05/T06/T07 状态/CAM 注入点补齐 `numFaultsInjected` | `CHAOSArmTLB.cc` |
| `d0af7d99` | T07 CAM 路径补记 F0 funnel（attempted/eligible） | `CHAOSArmTLB.cc` |
| `a41fbc5e` | 状态/CAM 故障在 PA 真重定向时打开关联臂（T07 链可观测） | `CHAOSPropagation.{hh,cc}`, `CHAOSArmTLB.cc`, 测试 |
| `560174a7` | armtlb 计数把 T08 walk-refill `armed` 握手行视为诊断 | `tools/lsu_campaign.py`, 测试 |
| `c7367a64` | 四子模型覆盖证据包 gate：`--t08-submodels-proven`（校验每个 `prop_evt`） | `tools/lsu_campaign.py`, `tests/test_lsu_campaign_t08_gates.py` |
| `e2eccdec` | 本轮计划文件 | `docs/superpowers/plans/2026-10-28-r6-v4-t-unit-closeout.md` |
| `f11eb1c4` | T08 四子模型动态覆盖证据包 + 报告 | `runs/lsu/r6_reports/R6{-V4-}T08-SUBMODEL-COVERAGE.{md,json}` |
| `0501a00f` | R6-V4-ATTRIB：state/attr/CAM 抽签只落在有 Request 身份的 lookup 上 | `CHAOSArmTLB.{cc,hh}`, `tools/lsu_campaign.py`, 测试 |
| `1f344a5b` | R6-V4-CAMFIRE：CAM+tier funnel 同记 fires/applied，三源核对以 applied 为准 | `CHAOSArmTLB.cc`, `tools/lsu_campaign.py`, 测试 |

另有传播文档/台账提交（`d2c98585`、`98ea5cf8`、`f6263a6f`、`ad1a4711` 及后续文档提交）。

## 2. T05/T06/T07/T08 的真实根因与修复

### T05 / T06（真实注入但 activated=0）

- 根因 A（计数缺陷，实测 T05/T06 seed1）：`applyEntryFieldFault()` 写注入日志、
  `++faults_injected_count`，却漏掉 `stats->numFaultsInjected++`；同时 campaign 的
  “applied 行”判据只认 `old_pfn/new_pfn`，把 `old_valid_clear/new_valid_clear` 判为
  malformed → log=0、trigger=1、stats=0 → count_contradiction。
- 根因 B（并发、真实）：被改字段不参与 PA（valid/ap），有效 PA 不变 ⇒ L2
  `effective_pa_unchanged` 含住；这是真实 containment，不是“没注入”。
- 修复：两处计数补齐（`a0250d51`），判据接受同名字段对（`0d49d357`）。
- 结果：T05-F0/F2、T06-F0/F2 共 12 个 seed 全部 qualified。

### T05-F0-W4 seed2 的额外根因（采样域）

- 抽签落到 `req_seq=0` 的 lookup：真实注入，但完成节点按 (req_seq,va) 关联，永远无法
  归因 → 4 事件、开链于 L2、不可准入。
- 修复（`0501a00f`）：state/attr/CAM 在消费预算/抽签前拒绝 `req_seq==0`；计 attempted、
  一次性写 `Site: arm_tlb_lookup_no_request`；pfn 模型（T01/T02/T10）不动。
- 影响：T05/T06/T07 的采样域收窄为“可归因 lookup”，文档与台账如实记录。

### T07（false_hit：开放 L2 + 5400s 超时 + attempted/eligible=0）

- 根因 1：CAM 路径从不 book F0 funnel（attempted/eligible 只在 hit 钩子计）。
- 根因 2：`registerTlbStateFault()` 从不调用 `chaos_chain::tlbRegistrationArms`，
  也不登记 addr/blk registry ⇒ 下游 LSQ/内存事件**在结构上**无法关联，链只能停在 L2。
- 修复：CAM funnel 补记（`d0af7d99`）；状态/CM 故障在 `pa_changed` 时打开关联臂
  （`a41fbc5e`，新增可选 `pa_span`；PA 中立的 T05/T06 不开臂、语义不变）。
- 修复后 T07-F0 seed1/2/3 均为 **full/L5**（errant_commit 见证），运行在墙钟上限被
  优雅终止（证据完整、未截断；结局由链而非超时定义，文档单列说明）。
- T07-F4 另暴露第三根因：CAM+tier 时 funnel 的 `injected` 是 **fires**，而落在 HIT 上
  的 fire 不能伪造注入（seed1：fires=762、applied=4/log=4/stats=4）⇒ 假矛盾。
  修复（`1f344a5b`）：打印 `CHAOS_LSU_TRIGGER_CAM … fires=… applied=…`，campaign
  以 applied 覆盖 injected（log/stats/applied 仍须逐字相等）。修复后 T07-F4 3/3。

### T08（复合模型四子模型）

- 根因 1：T08-b/c/d 在 arm 点与 refill 点**各**递增一次 `numFaultsInjected`
  ⇒ 一次故障 stats=2（`4e670105`）。
- 根因 2：一次故障写两行（`armed` 握手 + `refill` 应用），计数把两行都算
  ⇒ log=2 vs trigger=1（`560174a7`）。
- 根因 3：campaign 把 T08 硬锁在“仅 T08-a canary、仅 seed1”，与“官方 3 seed”冲突。
  新增 `--t08-submodels-proven`（`c7367a64`）：只有四子模型各有真实 `prop_evt`
  签名的证据包才能解锁 T08-F0/F4-W4 的正式 seed；F6/W9 仍被硬门拒绝。
- 四子模型动态覆盖（辅助 canary，不冒充正式 seed）：T08-a（walk_id=703，refill
  field=lost）、T08-b（duplicated）、T08-c（early_done；**按设计零硬件效应**）、
  T08-d（old_pfn 0x8001e → stale_pfn 0x8002f，下游 pa=0x8002f240）。

## 3. 测试、完整回归与构建结果

- 定向测试（真实输出）：`test_lsu_campaign_armtlb_count.py`、`test_lsu_hook_t05_state.py`、
  `pytest tests/test_lsu_campaign_t08_gates.py` 全 PASS（新增用例先红后绿）。
- 完整回归：`tools/lsu_test_runner.py`（全 84 套）。基线（HEAD `2848cd98`，独立 worktree
  `/tmp/base-r6-v4`）为 **FAIL=13**（A07/C11/C12/C14/C15/cpf/L04/O0x/P06/S10/sq +
  campaign_large_stream + campaign_propagation），全部为pre-existing。本轮最终回归
  见 `r6_v4_logs/regress-final.log` 与 `regress-final.json`：
  `suites=84 FAIL=13 PASS=70 SKIP=1`；与基线失败集合逐名比对 **NEW FAIL=[]**、
  FIXED=[]（基线当时含未完成的 t05_state 断言，故 PASS 69→70）。
- 构建（三次统一构建，全部 `BUILD_EXIT=0`、0 error/0 warning）：
  - `b13a60ab…`（source head `e2eccdec`）— 首轮 C++ 修复；
  - `e379cc5b…`（source head `0501a00f`）— 归因门；首建因 `field` 作用域错误
    BUILD_EXIT=2，修正后通过；
  - `3db54541…`（source head `1f344a5b`）— CAM funnel；构建日志
    `runs/lsu/r6_v4_logs/build-v4{,b,c,d}.log`。

## 4. 最终二进制与工具头

- 最终二进制：`…/CHAOS/gem5/build/ARM/gem5.opt`，
  sha256 `3db54541b7fbafa47d27ab7a3f71b8c777c2893501078f3eb36fddb91cd866c2`，
  source head `1f344a5b66da30267c578536e00a1ad4ad56bb31`，size 见 `stat`（~1.145 GB），
  构建日志 `build-v4d.log`（exit 0，warnings 0）。
- analysis tool head：本报告提交；逐 seed manifest 各自记录其运行时的 analysis head
  （`e2eccdec` 或 `0501a00f` 或 `1f344a5b`），二者不混用。
- 旧证据的二进制 SHA（`e8052842…` / `8a229009…` / `20fda699…`）保持不变。

## 5. T 单元逐 RunID 3-seed 状态

见 `R6-V4-T-STATUS.md`（权威）。摘要：**10/11 可执行格 COMPLETE_3_OF_3**，T08-F4-W4 为 2/3
（第 3 个 seed 在 F4 频率模型下 0 次发射，见 §8）。旧 17 格 COMPLETE_3_OF_3 未重跑。

## 6. 每个 seed 的 terminal / provable_to / admitted / certified / violations / 结局

| RunID | seed | terminal | provable_to | admitted/certified | violations | 结局 | 二进制 |
|---|---|---|---|---|---|---|---|
| T05-F0-W4 | 1/2/3 | detected_contained | L2 | True/True | [] | Masked（PA 不变含住） | b13a60ab / e379cc5b ×2 |
| T05-F2-W4 | 1/2/3 | detected_contained | L2 | True/True | [] | Masked | e379cc5b ×3 |
| T06-F0-W4 | 1/2/3 | detected_contained | L2 | True/True | [] | Masked | b13a60ab / e379cc5b ×2 |
| T06-F2-W4 | 1/2/3 | detected_contained | L2 | True/True | [] | Crash（含住后内核 oops） | e379cc5b ×3 |
| T07-F0-W4 | 1/2/3 | full | L5 | True/True | [] | errant_commit→墙钟上限（Timeout 记录） | b13a60ab / e379cc5b ×2 |
| T07-F4-W4 | 1 | full | L5 | True/True | [] | Crash | 3db54541 |
| T07-F4-W4 | 2/3 | detected_contained | L5 | True/True | [] | Crash | 3db54541 ×2 |
| T08-F0-W4 | 1/2/3 | detected_contained | L2 | True/True | [] | Masked / Timeout ×2 | e379cc5b ×3 |
| T08-F4-W4 | 1/2 | detected_contained | L2 | True/True | [] | Masked | e379cc5b ×2 |
| T08-F4-W4 | 3 | — | — | — | — | **NO_FIRE（非样本）** | e379cc5b |
| T10-F0/F1/F2-W4 | 1 | full | L5 | True/True | [] | Crash | 20fda699 |
| T10-F0/F1/F2-W4 | 2/3 | full（F2 s2 为 L5 containment） | L5 | True/True | [] | Crash | b13a60ab ×2 |

## 7. T08 四子模型覆盖

`R6-V4-T08-SUBMODEL-COVERAGE.md` + `R6-T08-SUBMODEL-COVERAGE.json`（bundle）：
a covered（官方 seed + canary）、b covered（duplicated，弱效应）、c covered（仅注解，
零硬件效应）、d covered（真实 stale PA）。辅助 canary 不是第 4 个正式 seed，不解锁 W9。

## 8. 仍 BLOCKED 的格与不可执行证据

- **F6（6 格）**：政策排除，本轮未运行。
- **T10-F0/F1/F2-W11**：SPEC CPU2017 许可缺失（BLOCKED_SPEC）。
- **T08-F0-W9 / T08-F4-W9**：FS 镜像无 GAP/Graph500（debugfs 只读复核，含阳性对照）；
  载体硬编码 `tlb_probe.rcS`；拒绝用 W4 替代（会静默改变实验身份）。
- **T08-F4-W4 seed3（NO_FIRE）**：F4 首次发射位置 = `iv/2 + rng%iv`（iv=100,000）
  落在 [50k,150k)，本 seed 的 walk-issue eligible 流长 126,005，抽样超出 ⇒ 0 次注入。
  这是频率模型在该流长下的合法“非样本”，不是证据失败；campaign 频率政策拒绝
  seed4（required_seeds=3），未绕过。要取得第 3 个样本需扩展流长或改 F4 模型，
  属规格变更，本轮不做。

## 9. 传播文档

- 目录：`runs/lsu/R6_COMPLETE_PROPAGATION_PATHS/`（83 份 = 旧 51 + 本轮 32）。
- 本轮索引：`INDEX-V4.md`；总索引 `INDEX.md`；README 已加 R6-V4 增量说明。
- 每份含：身份与复现、注入前后字段/地址/值、按真实事件顺序的传播叙事、逐层对照表、
  事件索引（event_id/parent/tick/corr/request_id）、结局形成原因、checker/campaign 判定、
  原始证据与 SHA、实验有效性 vs 观测链完整性两轴。

## 10. 是否达到 T 单元实际可执行格全部完成

**否，10/11。** 唯一未达 3/3 的是 `T08-F4-W4`：其第 3 个 canonical seed 在 F4 频率模型下
合法地没有注入（NO_FIRE），而政策禁止用 seed4 替换。其余 10 个可执行格均 3/3，
证据逐项满足合格判据（真实注入、三源一致、EOF、未截断、stats 非空、full/L5 真实
ancestry 或真实含住、admitted/certified、violations=[]、conservation=OK）。
