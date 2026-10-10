# AUDIT_REPORT — LSU PRE 钩子幻影激活只读污染审计（Subagent D）

- **裁决依据**：D-2026-10-10-幻影审计（用户裁决原文：`docs/gem5-fi/lsu/task_plan.md:157`）；
  缺陷发现 F-047(a)（`docs/gem5-fi/lsu/findings.md:63`，commit dbd3f226）。
- **审计日期**：2026-10-10。**性质**：绝对只读——零文件修改、零 git 写、零进程启动；
  原始 `runs/`、`results.json`、`unit_status.json` 未动一字节。
- **产物**（全部在 `/tmp/lsu_analysis_D/`）：
  `contamination_manifest.jsonl`（5,574 条样本记录，含全部非 activated 样本的排除标注）、
  `audit_summary.json`（24 项逐项汇总）、`audit_tool.py`（只读解析工具副本）、
  `RULES.md`（判定规则）、`correction_overlay_draft.jsonl`（35 条 overlay 草案）、本报告。

---

## 1. 审计范围（任务 1）

### 1.1 范围判定方法

PRE 钩子路径由 `tools/lsu_campaign.py` MODEL_FLAGS（:103-165）+ 源码
`CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.cc` 共同确定：

| 族 | 模型 | 挂载 | fire 后 op 类过滤 | pilot 样本 |
|----|------|------|------------------|-----------|
| PRE op-filtered | L01 (`l01_load_addr`) L02 (`l02_load_state`) | `--agu_pre_mode` (:126-127) | **有**（CHAOSAddrPath.cc:303/:309 `if (!isLoad) return`） | 有 |
| PRE op-filtered | S04/S05/S11/S13（store-only） | :119-124 | 有（:257/:264/:273/:294 `if (isLoad) return`） | **无**（pilot 无 Store_Queue 单元） |
| PRE unfiltered | A04/A05/A06/A08 | :108-111 | 无 | 有 |
| POST | A01/A02（A03 被 DR-002 BLOCKED） | `--addrpath_mode` (:105-107) | 无（maybeCorrupt :100-197，XOR 恒变 :137-145） | 有（对照组） |
| LSQFwd L03 站点 | L03 | `--lsqfwd_l03` (:128) | 无（CHAOSLSQFwd.cc:402-421 violationCorrupt：onEligible 后直接写入） | 有（相邻族核查） |

范围 = `runs/lsu/pilot/{AGU,Load_Queue}/unit_status.json` 中 **activated_runs>0 的全部已闭合项**
（波次 1-5 全量；L1d-TLB 单元 39/39 admission BLOCKED、unit_status 0 项，零样本，排除）。
其他轨道核查：`runs/lsu/engineering/` 仅 ITEM-001（A01，POST，1 样本）；
`runs/lsu/det/` 为单发工程验证（A01/C01/O01/P01/S01/T01，非 PRE addrpath）——均不在污染范围。

### 1.2 范围数字

- **入审项目 24 个**（AGU 20 COMPLETE + Load_Queue 4 COMPLETE），**activated 样本 774 个**，逐样本审计。
  - PRE 钩子项（裁决范围）：**17 项 / 558 activated 样本**（A04/A05/A06/A08 ×14 项 462 + L01/L02 ×3 项 96）；
  - POST 对照组：6 项 / 183 样本（A01×3、A02×3）；
  - LSQFwd L03 相邻族：1 项 / 33 样本。
- 排除：16 个 BLOCKED 项（300 attempted / 0 activated，F-041 事件供给不足，非本审计对象）的
  ~4,800 个样本目录仅登记不计审（manifest 中 `in_scope:false`）。

## 2. 幻影判定规则（任务 2，全文见 RULES.md）

- **P1 纯幻影**：trigger 行 `injected>=1` 且模型注入站点日志**零写入行**；
  佐证 = `CHAOS_L0_FUNNEL ... injected=0` + `CHAOS_L0 ... target=0 hit=0`。
- **P2 部分幻影**：trigger injected > 写入行数 ≥1（F1-F4 多 fire 档；范围内 F0/F6 单 fire，实测 0 例）。
- **N 值等同写入**（第二类污染，本次新识别）：写入行存在但故障目标值未变——mode-aware：
  a05 看 `old_addr==new_addr`、a06 看 `old_size==new_size`；**l02 不适用**（故障目标是
  STRICT_ORDER flag，日志不记录，addr/size 相同是 l02 预期格式）。
- **R 真实**：写入行且值变化。
- 三方一致性 7 项核对 + 与 `ITEM-*_result.json` runs 官方记录交叉比对（0 失配）。

**对照组实证（缺陷为 PRE 特有）**：6 个 POST 项 183 样本全部 trigger==写入==1（零幻影、零值等同）。
例：`ITEM-001_s1`：trigger injected=1，`Site: lsq_sendFragmentToTranslation` 写入 1 行，
`CHAOS_L0_FUNNEL injected=1`，`CHAOS_L0 target=4262280`（item 已注册）——与幻影签名逐字段相反。

## 3. 污染统计总表（任务 3+4）

774 样本逐样本审计结果（完整字段见 contamination_manifest.jsonl；汇总见 audit_summary.json）：

| 项 | RunID | 钩子类 | 原 activated | 幻影 P1 | P2 | noop N | 真实 R | uncertain | 暂定 effective activated | 修正五类（原 → 修正） |
|----|-------|--------|-------------|--------|----|--------|--------|-----------|--------------------------|----------------------|
| **ITEM-271** | L01-F0-W5 | PRE filtered | 30 | **14** | 0 | 0 | 16 | 0 | **16**（裁决"暂定 16/30"吻合） | Masked 23→**9**，simfail Crash 7 保留 |
| **ITEM-279** | L02-F0-W5 | PRE filtered | 33 | **14** | 0 | 0 | 19 | 0 | **19** | Masked 33→**19** |
| ITEM-283 | L02-F6-W5 | PRE filtered | 33 | 0 | 0 | 0 | 33* | 0 | 33* | 不变（*flag 写入确认；值等同不可从日志判定） |
| ITEM-285 | L03-F0-W5 | LSQFwd | 33 | 0 | 0 | 0 | 33** | 0 | 33** | 不变（**模型身份 caveat，见 §7） |
| **ITEM-019** | A05-F0-W3 | PRE unfiltered | 33 | 0 | 0 | **2** | 31 | 0 | **31**（write-confirmed 33） | Masked 23→21 |
| **ITEM-022** | A06-F0-W3 | PRE unfiltered | 33 | 0 | 0 | **1** | 32 | 0 | **32**（write-confirmed 33） | Masked 15→14 |
| ITEM-013/014/017/018/021/023/026/027/034/035/038/039 | A04/A05/A06/A08 F0/F6 | PRE unfiltered | 各33 | 0 | 0 | 0 | 33 | 0 | 33 | 不变 |
| ITEM-001/002/006/007/008/010 | A01/A02 | POST 对照 | 30/30/30/30/30/33 | 0 | 0 | 0 | 全部 | 0 | 不变 | 不变 |

**合计**：幻影 P1 = **28 样本**（271:14 + 279:14，占 PRE 范围 558 的 5.0%，全部原判 Masked）；
noop N = **3 样本**（019:2 + 022:1，全部原判 Masked）；P2 = 0；uncertain = 0；
守恒修正后：五类之和 + simfail == effective（271: 9+7=16 ✓；279: 19 ✓）。

### 幻影机制定量佐证

sq_forward 负载 eligible 流 2,570（271/279 的 census N，F-012 两遍法 span）含 load+store 两种
pushRequest；F0 单 fire 均匀落点 → 落在 store 的概率 ≈ store 占比。271 幻影率 14/30=46.7%、
279 = 14/33=42.4%——与 sq_forward 访存流中 store 占比一致（结构必然，非随机事故）。

## 4. ITEM-271 精确清单（14 幻影，精确到 seed）

seed 取自 guard.out run-finish cmd 的 `--addrpath_rng_seed` 值；全部证据 =
`guard.out: CHAOS_LSU_TRIGGER ... injected=1` + `addrpath_injections.log: 零写入行 +
CHAOS_L0_FUNNEL injected=0 activated=0 + CHAOS_L0 target=0 hit=0` + checksum==golden(1f4cbf14327717df)
+ 原判 Masked：

| # | 样本 | seed | run_dir |
|---|------|------|---------|
| 1 | s1 | 3231772775696662153 | runs/lsu/pilot/Load_Queue/ITEM-271_s1 |
| 2 | s4 | 14220662628011763827 | .../ITEM-271_s4 |
| 3 | s8 | 7314480661960411098 | .../ITEM-271_s8 |
| 4 | s9 | 2918720215254650879 | .../ITEM-271_s9 |
| 5 | s10 | 1104283824945151516 | .../ITEM-271_s10 |
| 6 | s11 | 3644790987648343144 | .../ITEM-271_s11 |
| 7 | s12 | 3146404204243220023 | .../ITEM-271_s12 |
| 8 | s13 | 2044320197041765009 | .../ITEM-271_s13 |
| 9 | s18 | 15553366145682610768 | .../ITEM-271_s18 |
| 10 | s19 | 11664470366148803856 | .../ITEM-271_s19 |
| 11 | s23 | 14421788718221512215 | .../ITEM-271_s23 |
| 12 | s24 | 15036956443682331124 | .../ITEM-271_s24 |
| 13 | s27 | 4686767063524219699 | .../ITEM-271_s27 |
| 14 | s29 | 13262952530216425239 | .../ITEM-271_s29 |

**ITEM-279（L02-F0-W5）14 幻影**（本次审计新发现，F-047 未知）：
s0(11794819054188178730) s1(2222706465755025893) s2(17895250044056175995) s5(15397346828217975189)
s7(9148908685905501625) s8(15447184284597597237) s12(15598956354020285854) s14(8952663765688124190)
s19(15297348815083509230) s21(4047062006652611366) s22(6048682467287876848) s25(2698824109735263124)
s26(17952756997885474499) s31(12960430028604927504)。
**noop 3 样本**：ITEM-019 s25(seed 2999347131946168170, 0x7ffffefd00 低位 0x00 旋转不动)、
s28(seed 462675473560075632, 0x499d00 同理)；ITEM-022 s0(seed 3806046103827626521,
`old_size=2, new_size=2` —— A06 目标 size=2 而原访问 size 已是 2)。

**实证签名样本**（可直接复核）：
- 幻影：`ITEM-271_s1_guard.out` 行 `CHAOS_LSU_TRIGGER: injector=CHAOSAddrPath tier=F0 attempted=2570
  eligible=2570 injected=1`；`ITEM-271_s1/addrpath_injections.log` 全文仅 2 行
  `CHAOS_L0: ... hit=0` + `CHAOS_L0_FUNNEL: ... injected=0 activated=0`。
- 真实：`ITEM-271_s2/addrpath_injections.log` 行 `Tick: 554400, Site: lsq_pushRequest_PRE,
  mode=l01_load_addr, old_addr=0x7ffffefe80, new_addr=0x107ffffefe80, ... faults_injected: 1`
  （bit40 翻转，exit -6 simulator_assert）。

## 5. Schema 能力核查（任务 5）

**结论：现有 L5 schema 不能表达"triggered 但未施加故障"。**

证据：
1. `tools/lsu_l5_classify.py:103` 五类闭集 `{"Masked","Detected/Contained","SDC","Crash","Timeout"}`；
   :94 checksum==golden → Masked；:101 `activated = injected`（直接采用 trigger 口径——污染入口）。
2. `docs/gem5-fi/lsu/总方针.md:33`"主结局必须且只能是 Masked、Detected-contained、Data Corruption、
   Crash、Timeout 中的一项"；:34 守恒式；:35 SDC 分母。
3. **无** NoEffect / NoInjection / InvalidInjection / Inactive 任何一类（`grep -rn` 全 lsu docs+tools
   仅命中裁决文本自身）；`schemas/manifest.schema.json`（KP 轨道 per-run manifest）无 outcome 枚举可复用。
4. 最接近的现有概念是 `injected_not_activated`（lsu_l5_classify.py:111、unit_pilot audit() 的
   `injected_not_activated_runs`）——但语义相反（"已注入未消费" vs 幻影的"计数注入实未注入"），
   且在 trigger 口径下恒为 0（injected==activated）。`INCONCLUSIVE`（:53）是输入缺失拒判，不适用
   （幻影样本证据完备，结论明确是"无注入"）。

**处置**（按裁决"schema 无法表达则先报告不擅自改共享 schema"）：
- 幻影样本：从 activated 与有效注入分母**剔除**（与 总方针.md:30 "未真正被下游消费的注入不得进入
  结果率分母"一致——幻影更弱：连注入都未发生）；终类建议 `InvalidInjection(triggered_not_applied)`
  **标注"schema 缺此类，待用户/schema 决策"**，不得判 Masked、不得伪装 Inactive。
- noop 样本：建议 `NoEffect(applied_but_value_identical)`（A03 先例：CHAOSAddrPath.cc:156-164
  no-op application 应从 activated 口径扣除）——同样标注 schema 缺类，最终归属待用户裁决。
- **需报告用户的 schema 缺口**：L5 五类闭集缺"triggered_not_applied"（幻影）与
  "applied_value_identical"（noop）两个终类表达；在补类前，overlay 以
  `remove_from_activated_denominator + suggested_class + final_class_adjudication=PENDING` 表达。

## 6. Correction overlay 草案（任务 6）

草案文件：`/tmp/lsu_analysis_D/correction_overlay_draft.jsonl`（35 条 = 28 幻影 + 3 noop 样本级 +
4 项目级汇总）。**提案落库路径**（只设计，未落仓库）：
`docs/gem5-fi/lsu/evidence/f047-phantom-correction-overlay.jsonl`（或 tools/draft/ 评审位）。

设计原则：
1. **零改动原始数据**：overlay 只引用 `run_dir`（repo 相对路径）+ seed + sample_index，
   不复制不修改 `l5_verdict.json` / `unit_status.json` / `result.json`；
   每条带 `"original_data_untouched": true` 与 `original` 快照（改前值+来源文件）。
2. **per-sample 声明式更正**：`correction.remove_from_activated_denominator` +
   `remove_from_classes` + `reason` + `evidence[]`（文件级证据引用）+
   `suggested_class` + `schema_status` + `final_class_adjudication: PENDING`。
3. **item 级汇总**：corrected five_class / write_confirmed / tentative_effective /
   phantom/noop/uncertain 计数 + 修正后守恒式 + 状态"暂定（不得冻结）"。
4. **可追溯**：每条含 `decision`（裁决 ID）、`finding`（F-047(a)/D）、`audit_tool`（工具副本路径）、
   `audit_date`；overlay_version 字段供后续重跑数据再审计时演进。
5. **消费规则**（建议）：统计工具读 overlay 时对 `record_type=sample_correction` 的样本从分母剔除、
   从原类别减去；`uncertain` 类（本次 0 例）单列不得计入——与裁决口径逐条对应。

## 7. 数据缺口与建议（任务 7 / 输出 g）

**数据缺口**：
1. **op 类不可直接观测**：PRE 写入行不记录 isLoad/isStore（CHAOSAddrPath.cc:321-329 无该字段），
   "fire 落在 store"是机制推理（过滤在写入之前，写入行存在⇒op 类匹配）+ 幻影率≈store 占比的
   定量吻合，而非逐 fire 直接观测。建议 OBS 补丁在 PRE 日志行加 op 类字段（与已计划的
   OBS-1..4 同批）。
2. **l02 值等同性不可观测**：STRICT_ORDER flag 不落日志。ITEM-283/279 的"真实"判定依据是
   写入行存在（flags.set 语句执行）；若个别请求已预设 STRICT_ORDER 则该次写入为 no-op——
   SE 负载不预设该 flag（源码注释 :296-304 亦称 flags 是"externally controllable lifecycle proxy"），
   风险低但非零。建议 OBS 补丁记录 flags 写入前后值。
3. **CHAOS_L0 read-back 层对 AddrPath 未实现**：CHAOSAddrPath 从不调用 chaosL0CountRead/
   chaosL0Overwrite（全源码 grep 零命中），故所有样本 `CHAOS_L0 ... reads=0 hit=0`——
   hit 字段对本注入器是惰性的，不能作为"注入未消费"证据（本审计未使用该字段作判定，仅作
   target=0 的注册证据）。这正是 trigger 摘要行 "(activated=W3-L0-layer)" 指向的未完成层。
4. **stats.txt 无 addrpath 故障计数器**（三方一致性的第三源缺失，已用日志双行替代）；
   CHAOSLSQFwd 有 numFaultsInjected 统计但 L03 站点写入不走它。
5. **ITEM-285 模型身份存疑**（F-047(b)）：config.ini 实证 `structMode=byte_flip` 而
   `--lsqfwd_l03` 不接线（lsu_proxy.py:793-811 挂载块不传）；33/33 写入实际落在
   checkViolations_L03 站点（共享 trigger 的落点竞争结果，本审计逐样本实证）。
   该项**无幻影**（写入必然执行），但"L03 语义"是偶然达成而非参数接线达成——
   与 SEM-B 修复联动裁决。
6. engineering/ITEM-001（POST，1 样本）与 det/ 验证运行未纳入逐样本审计（均非 PRE 幻影范围）；
   W1 重跑后的新数据需用同一工具+规则再审计（overlay_version 演进）。

**建议**：
1. [LSU][DATA] 更正提交按裁决先行：AUDIT_REPORT + overlay + 勘误 + 离线审计工具
   （audit_tool.py 副本建议入库 `tools/draft/lsu_f047_audit_tool.py`），不改共享 schema。
2. ITEM-271/279 按"暂定 16/30、19/33"记载，冻结等 SEM 修复后重跑。
3. SEM 修复（PRE 过滤前移到 onEligible 之前，或 trigger 只在实际写入时计数）应同时修
   a05/a06 的 no-op 写入日志标注（A03 先例的 "logged distinctly"），从根上消除两类污染。
4. S 族 store-only PRE 模式（s04/s05/s11/s13）未来进 pilot 时将呈现对称幻影（fire 落 load）——
   修复验证需含正对照。
5. schema 决策请求：是否为 L5 增补 `InvalidInjection(triggered_not_applied)` 与
   `NoEffect(applied_value_identical)` 终类（或以 sidecar 列表达），由用户裁决。

## 8. 复核方法（可重复性）

只读复跑：`python3 /tmp/lsu_analysis_D/audit_tool.py`（重生成 manifest+summary 并打印总表）；
单样本复核：对照 §4 签名样本的 guard.out 与日志两文件即可肉眼判定。
