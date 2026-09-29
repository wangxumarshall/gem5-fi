# gem5-fi LSU/OoO V2.0 端到端实现与验证方案（Implementation & Verification Plan）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. 一个任务 = 一个 commit（repo 一补丁一单元纪律）。

**Goal:** 把 `docs/gem5-fi/lsu/`（64 模型 / 178 子模型 / 325 展开格）与 `docs/gem5-fi/ooo/`（57 模型 / 193 子模型 / 310 展开格）两份 V2.0 忠实层完整落地为**可执行、可验证、可回填**的故障注入 campaign，并给出端到端验证方案。

**Architecture:** 以 V1.0 执行轨道为基座**重锚 + 补全**，不重建。基座已含：事件归一化 F0–F6 触发器（`chaos_lsu_trigger.hh`）、L0 激活判读契约（`chaos_l0.hh`）、LSU 五族注入器（AddrPath/LSQFwd/Cache/Prefetch/ExMon + F6 四通知源）、三阶段自适应抽样编排（`lsu_campaign.py`：30 试跑 → ≥385 筛查 → Wilson ≤2pp/5000）、L5 守恒分类器、runner/campaign/backfill 管线（打过 72,024 正式运行）。V2.0 增量 = ①矩阵重锚（V1.0 27 列 → V2.0 43 列）②OoO 轨道触发器从周期窗口迁移到事件归一化 F0–F6 ③分类学对齐 V2.0 L5（RAS-silent 拆分 + 首检四类）④LSU 10 个 deferred 模型补全 ⑤负载补齐 ⑥OoO B0 对齐。

**Tech Stack:** vendored gem5 v25.1.0.1（C++ 注入器四件套 + stdlib Python 配置）；tools/ 纯 Python（stdlib + pyyaml + jsonschema）；无新第三方依赖。

**Spec（唯一口径，数字永不混用 V1.0）:**
- `docs/gem5-fi/lsu/` —— V2.0 忠实层（commit `06cceb6a`；xlsx sha256 `1f652936…`）
- `docs/gem5-fi/ooo/` —— V2.0 忠实层（commit `94dfce2e`；xlsx sha256 `b73b6304…`）
- 两目录 `README.md` 的「与仓库源码的映射」节（2026-09-29 grep 核实）为本计划 §1 的事实源。

---

## 0. Global Constraints（全局约束，逐任务隐含生效）

1. **口径唯一**：一切模型/格数/频率/负载定义以两份 V2.0 忠实层为准；V1.0 数字（337/226 格、D 行、68 模型）永不与 V2.0 混算。V1.0 执行产物在姊妹仓 `/home/sdc/gem5-fi/runs/`，本仓 `runs/` 为空壳（`tools/ooo_harvest.py` 头注）。
2. **B0 基线**：LSU = `configs/se/lsu_proxy.py` B0（O3_ARM_v7a_3 + LSU 修正，`--variant B0|S1|S2|S3|S4`，`lsu_proxy.py:157-159,589-693`）；OoO = 3/6/8 宽 + ROB=40 + IQ=32 + PRF 128/192/48（`O3_ARM_v7a.py:163-204`）——`ooo_proxy.py` 默认是 4-wide/ROB=128（`:45-52`），**跑 V2.0 B0 必须显式传参或用本计划 WS5 的 `--b0_v2`**。
3. **触发语义**：V2.0 两簿 05 表均为 **eligible-event 归一化**（F1=每 1,000,000 / F2=每 100,000 / F3=每 10,000 / F4=每 100,000 触发一次连染 2–4 / F6=首次指定事件注入一次；±50% 抖动；warm-up）。机器实现以 `CHAOS/gem5/src/cpu/o3/chaos_lsu_trigger.hh` 为准（已逐条对应）；周期基 `chaos_trigger.hh` 已无引用者（全仓 grep 证实），不得复活。
4. **L0/L5 口径**：activated 由 L0 契约（`chaos_l0.hh`：reads_before_overwrite>0）判定；未 activated 不入 SDC 率分母；L5 守恒式 `Activated = Masked + Detected-contained + SDC + Crash + Timeout`（`tools/lsu_l5_classify.py` 头注）；可分析 activated = activated − Simulator failure。
5. **资源纪律**：gem5 并行上限 **4 进程**；构建 `cd CHAOS/gem5 && scons -j16 build/ARM/gem5.opt`（clean 必须 -j16，增量才可 -j126）；工具一律调**仓库根** `build/ARM/gem5.opt`。cpu179 实测 ~92 s/run（`tools/campaign.py` 头注）。
6. **诚实规则**：BLOCKED/DEFERRED 格显式标记绝不静默跳过（`lsu_campaign.py` 先例）；不可得值记 `n/a` 不记 0；未实现能力 `EXIT_SKIP`；预期列是可证伪假设，实测列保持待执行直到有数据。
7. **提交纪律**：一任务一 commit，显式路径 `git add`（绝不 `git add -A`）；分支 `fi-wx-paper`；每 commit 附真实验证输出。
8. **子模型维度**：采纳 V2.0 提取层裁决 D4——执行 310/325 格（模型×频率×负载），子模型**格内分层记录**（结果记录带 submodel 字段），不扩建 1050/922 全展开格。

---

## 1. 现状总账（全部 file:line 已于 2026-09-29 实证）

### 1.1 已就绪（V1.0 执行轨道遗产，直接复用）

| 能力 | 位置 | 证据 |
|---|---|---|
| 事件归一化 F0–F6 触发器（含漏斗 attempted/eligible/injected、warm-up、±50% 抖动、F4 连染 2–4、F6 四事件源） | `CHAOS/gem5/src/cpu/o3/chaos_lsu_trigger.hh`（全文 186 行） | `enum ChaOSLsuTier {F0..F6}`；`intervalEvents()` F1=1M/F2=100K/F3=10K/F4=100K；`chaosLsuF6Notify` 单消费者钩子 |
| F6 事件通知源（4 处调用点） | `cpu/o3/lsq_unit.cc`（SqForward）、`mem/cache/cache.cc`（DirtyEviction）、`mem/cache/base.cc`（CasSuccess/SwapReq）、`arch/arm/tlb.cc`（TlbHit，FS-only） | chaos_lsu_trigger.hh 头注 + grep -rl |
| L0 激活判读契约 | `cpu/o3/chaos_l0.hh` | `chaosL0Register/CountRead/Overwrite`；reads==0 ⇒ 不入分母 |
| LSU 五族注入器 | `cpu/o3/CHAOSAddrPath`（A 系 + pre_mode `off\|a04_subst\|a05_shift\|a06_size\|a08_subst\|s13_store_addr\|l01_load_addr`，`.hh:90`）、`cpu/o3/CHAOSLSQFwd`（S 系）、`mem/cache/CHAOSCache`（C 系，targetField/faultType）、`mem/cache/prefetch/CHAOSPrefetch`（P01/02/03/05/08；P06 无干净钩子、P07/P09 走 Cache 近似——.hh 诚实边界注）、`arch/arm/CHAOSExMon`（`StxrForceSuccess/StxrForceFail/O01MonitorAddrBitflip/O02MonitorStateCorrupt`） | 各 .hh；`lsu_campaign.py` 头注 git 溯源（W4 9fbec314 / W5 c7743989..a0ecfd20 / W6 65e5d022..2b967a9b / W8 f76f5632、1b97b714） |
| LSU B0 平台 + S1–S4 变体 + 全注入器 tier 旋钮 | `configs/se/lsu_proxy.py` | `--variant`（:157）；`--l1d_lsu_tier` choices `off,F0..F6`（:172）；`--prefetch_lsu_tier/--prefetch_warmup_events/--prefetch_span_events/--prefetch_f6_event`（:179-197）；`--lsqfwd_lsu_tier`（:249）；`--addrpath_lsu_tier`（:445） |
| LSU FS 平台 | `configs/fs/lsu_b0_fs.py`（经 `arm_chaos_fs.py --lsu_b0` 施加 B0 增量） | 文件头注 |
| 三阶段自适应抽样引擎（=V2.0 05 r12–r15） | `tools/lsu_campaign.py`（670 行） | 头注：试跑 30 activated → 筛查 ≥385 → Wilson ≤2pp 或 5000；`--matrix …07-expanded-matrix.csv --max-parallel 4` |
| L5 守恒分类器 | `tools/lsu_l5_classify.py` | 守恒式 + `CHAOS_LSU_TRIGGER` 漏斗正则 + crash 双拆分（simulator_assert vs guest） |
| OoO 平台（挂 17 注入器） | `configs/se/ooo_proxy.py:28` | Reg/PhysReg/Mem/LSQFwd/RenameMap/FreeList/ROB/IQ/Exec/FPU/L1DForward/BPU/AddrPath/Decode/ExMon/RAS/Probe/CommitTrace/MicroSnap |
| OoO campaign（two_phase + event_coverage） | `tools/campaign.py`（1809 行） | two_phase/counting 段；`count_eligible_events()`（:236）；manifest schema-v3 `ooo` 扩展块（design_unit_id/experiment_cell_id/frequency_tier/counting_basis/phase） |
| 结果回填闭环 | `tools/backfill_expanded_matrix.py`（1016 行）+ `audit_expanded_matrix.py` + `ooo_harvest.py` | pilot 永不入列、未达标留空、Wilson 入格 |
| 统一分类器 / Wilson | `tools/classify.py`（九类有序 + 6 种 oracle）、`tools/wilson.py`（`wilson_ci/cell_stats`） | 两 track 共用无漂移 |
| runner | `tools/runner.py`：CONFIG_FAMILY C0/C2/**C3**/**C4-LSU**/C0-CACHE/C0-FS/C2-FS（:43-59）；GOLDEN_IDS 全体现存负载（:61-140+） | manifest→config args→单跑→classify→断言 faults∈{0,1} |
| manifest schema v2 | `schemas/manifest.schema.json`：trigger.mode 含 `event`；fault.f5_substitute_target/f6_phase_offset/trigger_value_pattern 已预声明 | 字段树实证 |

### 1.2 缺口（本计划工作项的来源）

| # | 缺口 | 证据 | 工作项 |
|---|---|---|---|
| G1 | OoO 族注入器（Decode/RenameMap/FreeList/ROB/IQ/PhysReg/FPU）用**周期窗口**（`scheduleAttackEvent(Cycles)`，`CHAOSPhysReg.hh:104-109`）+ `--first_clock/--last_clock`，无事件归一化 tier、无 F4/F6 | chaos_trigger.hh（周期基）全仓无引用者；ooo_proxy 无 `*_lsu_tier` 旋钮 | WS4 |
| G2 | `target.component` 枚举（21 项）缺 `bpu/decode/exmon/ras/addr_path/prefetch`（runner.py:1197-1388 已分派前五个） | schema 字段树 | WS2 |
| G3 | classify.py 九类 ≠ V2.0 L5 分类学（无 RAS-silent Crash/Timeout 拆分、无 Detected-uncontained、无首检四类、无 RAS 任意时点） | classify.py 头注 vs 两簿 04 表 L5 行 | WS3 |
| G4 | 矩阵口径 V1.0（LSU 337 格 27 列 / OoO E001-E226 7 结果列）≠ V2.0（325/310 格 43 列 22 值槽） | `lsu_campaign.py` 头注、`backfill_expanded_matrix.py` 头注 vs 两份 `07-expanded-matrix.md` | WS1/WS6 |
| G5 | LSU 10 个 deferred 模型：notify-only（消费端损坏未实现）S10/L04/C11/C12/C14/C15；无干净钩子 A07/P06/O04/O09 | `lsu_campaign.py` 头注 HONEST DEFERRED | WA1 |
| G6 | LSU 负载缺 W1 MiBench-TC23、W4 TLB-AliasPerm（FS）、W11 SPEC（许可证）、W13 PARSEC（多核 FS） | `workloads/directed/` 清单 vs `06-workloads.md` | WA2/WA3/WA4 |
| G7 | OoO 负载缺 W1/W2/W3/W8/W9/W13（W12 SPEC 同许可证门；W0/W2/W12 在展开矩阵未接线——先例允许后补） | `workloads/ooo/` 清单 vs `06-workloads.md` | WB2 |
| G8 | OoO B0 ≠ ooo_proxy 默认（4-wide/ROB=128） | `ooo_proxy.py:45-52` vs `02-ooo-params-baseline.md` | WS5 |
| G9 | OoO 57 模型 × 注入器模式面的逐模型覆盖未审计（V1.0 91 D 行 → 57 模型桥在 git `ad5a8a06`，未入库） | d-bridge csv（git 历史 117 行） | WB1 |
| G10 | 统计编排数字是 V1.0 口径（pilot 20/formal 2000/two_phase）≠ V2.0（30 activated/≥385/Wilson≤2pp/5000 + run-level cluster + CRN） | `campaign.py` two_phase 段 vs 两簿 05 表 r12–r20 | WS1（引擎复用）+WA5/WB4（接线） |

### 1.3 V2.0 数量底账（写入所有验收断言）

| 维度 | LSU | OoO |
|---|---|---|
| 模型 / 子模型 | 64 / 178（每模型 1–4） | 57 / 193（每模型 2–5） |
| 展开格 | **325**（多重集 = 设计矩阵适用频率×适用负载） | **310**（重放含顺序全等） |
| 频率分布 | F0=105 F1=24 F2=77 F3=4 F4=26 F5=25 F6=64 | F0=104 F1=12 F2=76 F3=0 F4=28 F5=10 F6=80 |
| 负载接线 | 14/14 全接（W0=6…W6=55 最大） | 11 接线；W0/W2/W12 定义未接线 |
| 单元格数 | AGU39/TLB39/SQ63/LQ30/Cache73/原子28/预取53 | 六单元 48/48/54/52/54/54 |
| 子模型全展开上界（不执行，仅记录） | 922 | 1050 |
| V1.0→V2.0 模型 delta | 68−4（剔除保护行 S12/T09/C13/O08） | 91 D 行合并为 57（d-bridge） |

---

## 2. Part WS —— 共享基座（里程碑 M0，顺序执行）

> 范围说明（writing-plans scope check）：M0 完成后 LSU/OoO 两 track 可作为独立子计划并行执行（Part WA / Part WB），各自产出可独立验证的交付。

### Task WS1: V2.0 展开矩阵装载器 `tools/v2_matrix.py`

**Files:**
- Create: `tools/v2_matrix.py`

**Interfaces:**
- Produces: `load_v2_matrix(csv_path) -> list[V2Cell]`；`V2Cell` 字段 `run_id / model_id / unit / freq / workload_id / workload_name / submodels(list[str]) / design_cols(dict, 14 列原文)`；CLI `--matrix PATH [--cells RUNID,…] [--dry-run]`。WA5/WB4/WS6 的 campaign 与回填工具 import 本模块取格清单（**唯一矩阵入口，杜绝各自解析**）。

**Steps:**

- [ ] **Step 1: 实现装载器。** csv 读取 44 列（`Excel行` 管理列 + 源表 43 列）；列名断言与 `docs/gem5-fi/{lsu,ooo}/07-expanded-matrix.md` 列文档一致；RunID 解析 `模型ID-频率-W#`；`子模型` 列按 `<模型ID>-<字母>` 解析为 list。
- [ ] **Step 2: 内嵌自校验（脚本退出非零即失败）。** 断言：LSU 325 行 / OoO 310 行；RunID 唯一；频率分布 == §1.3 底账；负载集合 LSU 14 个 / OoO 11 个（OoO 容许 W0/W2/W12 不出现）；值槽（P..AP 除 Z/公式列）全空。
- [ ] **Step 3: 运行验证（真实命令）：**

```bash
python3 tools/v2_matrix.py --matrix docs/gem5-fi/lsu/07-expanded-matrix.csv --dry-run
# 预期输出含: cells=325 F0=105 F1=24 F2=77 F3=4 F4=26 F5=25 F6=64 workloads=14/14
python3 tools/v2_matrix.py --matrix docs/gem5-fi/ooo/07-expanded-matrix.csv --dry-run
# 预期输出含: cells=310 F0=104 F1=12 F2=76 F3=0 F4=28 F5=10 F6=80 workloads=11/14
```

- [ ] **Step 4: Commit:** `feat(tools): WS1 V2.0 矩阵装载器 v2_matrix.py（325/310 格自校验）`

### Task WS2: manifest schema 组件枚举补齐

**Files:**
- Modify: `schemas/manifest.schema.json`（`properties.target.properties.component.enum`）
- Test: `tools/manifest_validate.py` 回归

**Steps:**

- [ ] **Step 1:** 在枚举数组追加 `"bpu", "decode", "exmon", "ras", "addr_path", "prefetch"`（前五个 `tools/runner.py:1197-1388` 已有分派；`prefetch` 由 WA1-P 系接线后生效，先登记枚举不破坏 v2 向后兼容——schema 描述原文即"ADDITIVE"）。
- [ ] **Step 2: 验证：**

```bash
python3 - <<'EOF'
import json, jsonschema
s = json.load(open('schemas/manifest.schema.json'))
enum = s['properties']['target']['properties']['component']['enum']
need = {'bpu','decode','exmon','ras','addr_path','prefetch'}
assert need <= set(enum), need - set(enum)
m = json.load(open('schemas/manifest.schema.json'))  # 结构仍可加载
print('component enum OK:', len(enum), 'values')
EOF
python3 tools/manifest_validate.py --help   # 工具仍可运行（回归）
```

- [ ] **Step 3: Commit:** `feat(schema): WS2 target.component 枚举补 bpu/decode/exmon/ras/addr_path/prefetch`

### Task WS3: classify V2.0 L5 分类学层

**Files:**
- Modify: `tools/classify.py`（新增 `classify_run_v2()`，**不改** `classify_run()` 既有行为——V1.0 结果可复算）
- Create: 验证用例内嵌于模块 docstring 下的 `--selftest-v2` CLI 分支

**Interfaces:**
- Produces: `classify_run_v2(result_v1: dict, *, first_detection: str|None = None, ras_any: bool = False) -> dict`，返回 `{"outcome": …, "first_detection": "HW_RAS"|"OS"|"Application"|"None", "ras_any": bool, "in_denominator": bool}`。
- 映射表（V1.0 九类 → V2.0 L5，SE 轨道）：

| V1.0 类 | V2.0 outcome | 说明 |
|---|---|---|
| SimulatorError | `Simulator failure` | 不入任何架构结局分母 |
| Inactive | `Injected-not-activated` | 不入 SDC 率分母（L0 口径） |
| Masked | `Masked` | |
| Corrected / DetectedContained | `Detected-contained` | 需检测器证据；SE 无保护模型时不会出现 |
| （无对应） | `Detected-uncontained` | 预留：检测到但未遏制 |
| SDC | `Data Corruption` | |
| Crash | `RAS-silent Crash` | SE 无硬件 RAS，全部 Crash 即 RAS-silent |
| Hang | `RAS-silent Timeout` | 同上 |
| Latent | `Latent`（报告列，不进结局五类） | |

  首检四类在 SE 轨道的诚实取值：无保护模型时 `None`（程序正常完成而 oracle 离线发现 SDC）或 `Application`（程序自检退出非零归 Crash 前）；`ras_any=False` 恒定（B0 无 ECC/parity，两簿 02 表「保护机制核验」行原文）。

**Steps:**

- [ ] **Step 1:** 实现 `classify_run_v2()` + 映射表（作为模块级常量 `V2_OUTCOME_MAP`）。
- [ ] **Step 2:** `--selftest-v2` 分支覆盖 9 个输入类各一例 + 断言 `in_denominator` 只对五类结局为真。
- [ ] **Step 3: 验证：**

```bash
python3 tools/classify.py --selftest-v2
# 预期: V2 taxonomy selftest PASS (9 mappings, denominator gate OK)
```

- [ ] **Step 4: Commit:** `feat(tools): WS3 classify_run_v2 V2.0 L5 分类学层（RAS-silent/首检四类/分母门）`

### Task WS4: OoO 轨道事件归一化触发迁移（F0–F6）

> 最大 C++ 工作项。目标：OoO 六单元（Int Decode/Int Rename/Int Dispatch-ROB/FP-SIMD ×3）注入器的触发语义从周期窗口迁移到 `chaos_lsu_trigger.hh` 同款事件归一化 F0–F6，满足 V2.0 OoO 05 表与 d-bridge 的事件触发锚点（D14→R03+F6 误预测事件、D18→R05-c+F6）。按注入器族分 6 个 commit。

**Files:**
- Create: `CHAOS/gem5/src/cpu/o3/chaos_event_trigger.hh`（header-only，无 SConscript 条目——同 chaos_lsu_trigger.hh 先例）
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSDecode/`、`CHAOSRenameMap/`、`CHAOSFreeList/`、`CHAOSROB/`、`CHAOSIQ/`、`CHAOSPhysReg/`、`CHAOSFPU/` 各 `.hh/.cc`
- Modify: `configs/se/ooo_proxy.py`（tier 旋钮面）

**Interfaces:**
- `chaos_event_trigger.hh`：`enum ChaOSEventTier { F0..F6 }`（**别名复用 chaos_lsu_trigger.hh 的语义实现**——直接 `#include` 并 typedef，或整段复制并改名；两簿 05 表口径相同，不允许出现第三种语义）+ `enum ChaOSOooEvent { BranchMispredict, RenameSquash, CommitSquash }`（OoO 的 F6 事件源，源自 d-bridge D14/D18 的事件语义）+ 单消费者通知钩子 `chaosOooF6Notify`。
- 每个注入器：定义自身 **eligible-event 流**（= V2.0 04 表 L0 的 eligible 口径按单元实例化：Decode=译码完成的有效指令、RenameMap/FreeList=重命名周期有效映射分配、ROB/IQ=分派入队事件、PhysReg=写回/读事件、FPU=FP 操作完成）；`onAttempt()/onEligible()` 接入；summary 行沿用 `CHAOS_LSU_TRIGGER:` 前缀改名 `CHAOS_EVENT_TRIGGER:`（runner/lsu_l5_classify 的正则同步放宽）。
- `ooo_proxy.py`：每注入器旗标加 `--<name>_tier {off,F0..F6}` + `--<name>_warmup_events/--<name>_span_events/--<name>_f6_event`（对齐 `lsu_proxy.py:172-197` 的旋钮面）。

**Steps（每步一 commit）:**

- [ ] **WS4.1:** 建 `chaos_event_trigger.hh`（泛化 + OoO F6 事件枚举 + 钩子）；`cd CHAOS/gem5 && scons -j16 build/ARM/gem5.opt` 零警告零错误。Commit: `feat(chaos): WS4.1 chaos_event_trigger.hh 泛化事件触发器 + OoO F6 事件源`
- [ ] **WS4.2:** CHAOSDecode 接入（Int Decode + FP/SIMD Decode 共用；eligible=有效译码指令）。验证：`build/ARM/gem5.opt --outdir=/tmp/ws4d configs/se/ooo_proxy.py --cmd workloads/ooo/smoke/smoke --cpu O3 --chaos_decode --decode_tier F6 --decode_f6_event branch_mispredict` → stdout 含 `CHAOS_EVENT_TRIGGER: injector=CHAOSDecode tier=F6 … injected=1`。回归：同一命令去掉注入旗标 → FINAL==`GOLDEN_IDS["smoke…"]`。Commit: `feat(ooo): WS4.2 CHAOSDecode 事件归一化 tier 接入`
- [ ] **WS4.3:** CHAOSRenameMap + CHAOSFreeList 接入（eligible=重命名周期映射分配；F6 源 RenameSquash）。同款验证（改 `--chaos_rat`）。Commit: `feat(ooo): WS4.3 Rename/FreeList 事件 tier 接入`
- [ ] **WS4.4:** CHAOSROB + CHAOSIQ 接入（eligible=分派入队）。Commit: `feat(ooo): WS4.4 ROB/IQ 事件 tier 接入`
- [ ] **WS4.5:** CHAOSPhysReg + CHAOSFPU 接入（eligible=写回事件；FPU 含 FP 完成）。Commit: `feat(ooo): WS4.5 PhysReg/FPU 事件 tier 接入`
- [ ] **WS4.6:** `ooo_proxy.py` 旋钮面 + runner.py `decode/rat/freelist/rob/iq/physreg/fsu` 分派传参（runner 组件分支在 `:751-1156` 已存在，补 tier 参数映射）。回归：`python3 tools/runner.py <样例 manifest> --config C3` 全链路一次。Commit: `feat(runner): WS4.6 ooo_proxy/runner 事件 tier 参数面贯通`
- [ ] **每步回归（硬门）:** 无注入 golden 跑 `build/ARM/gem5.opt --outdir=/tmp/reg configs/se/ooo_proxy.py --cmd workloads/ooo/coremark/coremark --cpu O3` FINAL==`000000000000cf56`。

### Task WS5: ooo_proxy `--b0_v2` 预设

**Files:**
- Modify: `configs/se/ooo_proxy.py`

**Steps:**

- [ ] **Step 1:** 加 `--b0_v2` 旗标：置 `fetch/decode/renameWidth=3、dispatchWidth=6、issue/wb/commitWidth=8、rob=40、phys_int=128、phys_float=192、phys_vec=48`（`O3_ARM_v7a.py:163-204` 逐项；IQ=32 为类默认，打印核验）。**不改默认值**（V1.0 结果可比性保护——`ooo_proxy.py:45-52` 默认 4-wide/rob128 保留）。
- [ ] **Step 2: 验证：**

```bash
build/ARM/gem5.opt --outdir=/tmp/b0v2 configs/se/ooo_proxy.py --cmd workloads/ooo/smoke/smoke --cpu O3 --b0_v2 2>&1 | grep -E "numROBEntries|width"
# 预期: ROB=40, widths 3/6/8, PRF 128/192/48; FINAL 与 golden 一致（参数不应改结果）
```

- [ ] **Step 3: Commit:** `feat(ooo): WS5 --b0_v2 预设（V2.0 B0=3/6/8+ROB40，默认不动保 V1.0 复现）`

### Task WS6: 回填/审计工具 V2.0 模式

**Files:**
- Modify: `tools/backfill_expanded_matrix.py`、`tools/audit_expanded_matrix.py`

**Interfaces:**
- Consumes: WS1 `load_v2_matrix`；WS3 `classify_run_v2`。
- Produces: `--v2-matrix` 模式——目标矩阵为 V2.0 43 列版；回填映射键 = RunID（模型ID-频率-负载ID）；写入 22 个值槽中的 campaign 可得列（Attempted/Activated/Masked/Detected-contained/Data Corruption/Crash/Timeout/SDC/首检四类/RAS-silent×2/Simulator failure/Seed 备注），并**机器复算两个差额自检列**（检测计数差额 = SUM(首检四类) − (Activated − Simulator failure) 应为 0；结局计数差额 = SUM(五类结局) + Simulator failure − Activated 应为 0）——即把 xlsx 公式列 X/Y/AL/AM/AN 的语义（提取层注记 (b)/(e)）做成回填侧断言。pilot/试跑永不入列（沿用既有 phase 门）。

**Steps:**

- [ ] **Step 1:** 实现 `--v2-matrix` 路径 + 差额自检断言。
- [ ] **Step 2: 验证（用一个小规模假 campaign 或 dry-run）：**

```bash
python3 tools/backfill_expanded_matrix.py --v2-matrix docs/gem5-fi/lsu/07-expanded-matrix.csv --campaign <dir> --dry-run
# 预期: 325 格清单打印、无可回填数据时全部留空并报告（不填 0）
```

- [ ] **Step 3: Commit:** `feat(tools): WS6 backfill/audit V2.0 43 列模式 + 差额自检列机器断言`

---

## 3. Part WA —— LSU track（里程碑 M1→，依赖 M0）

### Task WA1: 10 个 deferred 模型补全（每模型一 commit）

**依据:** `lsu_campaign.py` 头注 HONEST DEFERRED + 各模型行定义（`docs/gem5-fi/lsu/03-design-matrix.md` 对应行，实施时逐行对齐「故障模型（实施步骤与激活口径）」列原文）。

**Files（按系列）:**
- S10/L04：`cpu/o3/lsq_unit.cc`（请求/应答、response 配对的消费端损坏）+ `CHAOSLSQFwd`
- C11/C12：`mem/cache/CHAOSCache/` + `mem/cache/base.cc`（MSHR merge 消费端、fill/writeback 事务配对）
- C14/C15：`mem/cache/CHAOSCache/`（V2.0 追加行，语义以 03 表原文为准）
- A07：`cpu/o3/CHAOSAddrPath/`（byte-enable/ready 时序——V1.0 裁决"无干净钩子"，本任务重审钩子点：EA 生成后送 DTLB 前的 mask 路径）
- P06：`mem/cache/prefetch/CHAOSPrefetch/`（prefetch 标记为 demand/错误权限——重审 `BasePrefetcher`/请求标志路径）
- O04：`arch/arm/CHAOSExMon/`（order tag/屏障完成）
- O09：按 03 表 O09 行原文裁决（V1.0 判 no-clean-hook；若为保护链预留类则按 02 表保护核验行记不适用，**永不填零**）

**每模型统一验收（真实命令模式）:**

```bash
build/ARM/gem5.opt --outdir=/tmp/wa1_<mid> configs/se/lsu_proxy.py \
  --cmd workloads/directed/<对应负载> --cpu O3 \
  --chaos_<族旗标> --<族>_lsu_tier <该模型适用频率档> --<族>_mode <模型模式>
# 预期: CHAOS_LSU_TRIGGER 行 injected≥1（F5/F6 按 tier 语义）；分类非 SimulatorError；
#       同 seed 双跑逐字节一致（确定性）
```

- [ ] **WA1.1–WA1.10:** 每模型：读 03 表行原文 → 实现模式/钩子 → 上面的验收命令 → 更新 `lsu_campaign.py` 的 DEFERRED 清单（移出）→ commit `feat(lsu): WA1.x <模型ID> <一句话>（03 表 <模型ID> 行落地）`

### Task WA2: T 系 FS 路径 + W4 负载

**Files:**
- Modify: `configs/fs/lsu_b0_fs.py`（TLB 注入挂载核验）
- Create: `workloads/directed/tlb_aliasperm/`（4KiB/2MiB 页、ASID 切换、同 VA 不同 PA、只读/不可执行、TLBI 后重填、跨页——`06-workloads.md` W4 行定义）+ golden 注册 `tools/runner.py` GOLDEN_IDS
- 依赖事实: TlbHit F6 源 FS-only（`arch/arm/tlb.cc` 钩子已在；SE 不调 `TLB::lookup`——chaos_lsu_trigger.hh 头注）

**验收:** `build/ARM/gem5.opt --outdir=/tmp/w4 configs/fs/lsu_b0_fs.py …`（FS 依赖 gem5-fs 子模块）跑 T01 单 bit（TC'22 锚点，见 WV2）+ F6/TlbHit 模式 injected=1。
- [ ] Steps: 实现 → golden（native==gem5==双跑一致）→ 注册 → FS 单跑验收 → commit `feat(lsu): WA2 T 系 FS 路径 + W4 TLB-AliasPerm 负载`

### Task WA3: W1/W11/W13 负载补齐

- W1 MiBench-TC23（10 基准，`06-workloads.md` W1 行清单）→ `workloads/directed/mibench_tc23/`（一基准一子目录，host gcc -O2 -static）
- W11 SPEC CPU2017（mcf/omnetpp/xalancbmk/lbm SimPoint）——**许可证门**：无许可证则整格 BLOCKED 台账记录，不降级替代（G6 诚实规则）
- W13 PARSEC-Selected（dedup/ferret/streamcluster）→ 依赖 WA4 多核 FS
- 验收: 各负载 golden 双跑一致 + GOLDEN_IDS 注册 + `tools/v2_matrix.py --cells <该 W 的格>` 可解析
- [ ] 每负载一 commit: `feat(workloads): WA3 W1 MiBench-TC23 …`

### Task WA4: O 系多核 FS（W7/W13）

**Files:**
- Create: `configs/fs/lsu_b0_fs_mc.py`（多核：N 核 B0 + ExMon 挂载；现 `configs/fs/` 仅单核代理——G 缺口）
- Create: `workloads/directed/atomic_litmus/`（MP/SB/LB/IRIW/Dekker/ticket/CAS counter，禁出现结果 oracle——W7 行定义）
- 诚实边界: `chaosLsuF6Notify` 单消费者单核 SE 域（chaos_lsu_trigger.hh 头注）——多核泛化在本任务内解决或显式记 BLOCKED
- [ ] Steps: 多核配置 → litmus 负载 → 无注入全 litmus 通过（负对照）→ O01/O02 注入单跑 → commit `feat(lsu): WA4 多核 FS + W7 Atomic-Litmus`

### Task WA5: LSU campaign 重锚 + 全格试跑

**Files:**
- Modify: `tools/lsu_campaign.py`（矩阵入口换 WS1 `load_v2_matrix`；V1.0 337 格 → V2.0 325 格；分类出口接 WS3 `classify_run_v2`；DEFERRED 判定更新为 WA1 后剩余集）

**验收（分阶段真实命令）:**

```bash
python3 tools/lsu_campaign.py --matrix docs/gem5-fi/lsu/07-expanded-matrix.csv --outdir runs/lsu_v2 --max-parallel 4 --dry-run
# 预期: 325 格全列出（BLOCKED 仅 W11-许可/W13-多核类，行数与台账一致）
python3 tools/lsu_campaign.py --matrix … --outdir runs/lsu_v2_trial --cells A01-F0-W3  # 先锋格
# 预期: 试跑阶段累计 30 activated 停止；results 带 funnel 三计数 + L0 activated + L5 守恒通过
```

- [ ] WA5.1 重锚 commit；WA5.2 全格试跑（30 activated/格；~325×30≈万级 runs——按 §7 机器预算执行）；WA5.3 筛查（≥385 activated/格）。每阶段 commit `feat(lsu): WA5.x …` + 结果台账（BLOCKED 率、激活率分布）。

### Task WA6: S1–S4 敏感性 campaign

- `--variant S1/S2/S3/S4`（`lsu_proxy.py:589-693`）各跑 02 表指定的对照格集（敏感性配置列 E 原文划定范围）；产出 S 系 vs B0 的每格对比表。
- [ ] 验收: `python3 tools/lsu_campaign.py --matrix … --variant S1 --cells <02 表 E 列标注 S1 的格>` 逐格 Wilson CI 输出。commit `feat(lsu): WA6 S1 敏感性 …`（S2–S4 各一）

---

## 4. Part WB —— OoO track（里程碑 M2→，依赖 M0；可与 WA 并行）

### Task WB1: 桥审计（V1.0 91 D 行 ↔ V2.0 57 模型）

**Files:**
- Create: `docs/gem5-fi/ooo/d-bridge-v1-v2.csv`（从 git `ad5a8a06` 恢复，117 行原文）
- Create: `docs/gem5-fi/ooo/09-v2-coverage-audit.md`（57 模型 × 14 列 → 注入器模式面映射表）

**方法:** 逐模型对 `03-design-matrix.md` 行的「故障模型/子模型」列 vs WS4 后各注入器模式面，标注 `已实现 / 部分（子模型缺口）/ 未实现`；与 d-bridge 的 V1.0 D 行血统交叉（V1.0 已执行的 Int Rename 72k 运行血统=可信基线）。产出缺口清单直接生成 WB3 任务列表。
- [ ] 验收: 审计表 57 行全覆盖、每行有判定与证据（file:line 或 d-bridge 行号）；`python3 - <<'EOF'` 断言表行数==57。commit `feat(ooo): WB1 d-bridge 入库 + 57 模型覆盖审计`

### Task WB2: OoO 负载补齐（W1/W2/W3/W8/W9/W13）

- W1 MiBench-TC23（复用 WA3 产物——**同一负载仓两个 track 共用**，golden 各自注册）
- W2 BEEBS-DelayAVF（`workloads/directed/beebs_kernels` 已有，需按 V2.0 定义对齐 md5/libbubblesort/libstrstr/matmult/libfibcall 子集）
- W3 A64-DecodeProbe（自设：data-processing imm/reg、shift/extend、cond-select、branch、load/store 解码边界 + expected decode tuple——06 表 W3 行）
- W8 FP-ScalarProbe / W9 NEON-LaneProbe（`workloads/directed/neon_lane` 为 W9 近似物，按定义补齐 lane 全覆盖）
- W13 FP-ExceptionRecovery（FPSR/FPCR + 精确异常交叉）
- [ ] 每负载一 commit，验收同 WA3 模式（golden 双跑 + GOLDEN_IDS + v2_matrix 可解析）。

### Task WB3: 注入器补全（按 WB1 缺口清单）

- 逐缺口模型一 commit（同 WA1 模式：03 表行原文 → 模式实现 → ooo_proxy 单跑验收 → 确定性双跑）。
- [ ] 验收命令模式:

```bash
build/ARM/gem5.opt --outdir=/tmp/wb3_<mid> configs/se/ooo_proxy.py \
  --cmd workloads/ooo/<负载> --cpu O3 --b0_v2 --chaos_<族> --<族>_tier F6 --<族>_f6_event <事件>
# 预期: CHAOS_EVENT_TRIGGER … injected=1；分类非 SimulatorError；双跑一致
```

### Task WB4: OoO campaign 重锚（310 格三阶段）

**Files:**
- Modify: `tools/lsu_campaign.py`（泛化为双 track：`--track lsu|ooo`，C4-LSU/C3 配置族与负载根目录参数化）或 Modify `tools/campaign.py` 加 V2.0 抽样模式（two_phase 数字改 30/≥385/Wilson≤2pp-5000 + run-level cluster）——**二选一，裁决依据：复用 lsu_campaign 的矩阵驱动架构（推荐，它已实现 V2.0 抽样）**，campaign.py 的 two_phase 保留给 V1.0 复现。

- [ ] WB4.1 重锚 commit（--track ooo 分派 + C3 + --b0_v2 默认传入）；WB4.2 全格试跑 30 activated；WB4.3 筛查 ≥385。验收同 WA5 命令模式（`--track ooo`）。

### Task WB5: OoO B0 验证 + S0–S6 敏感性

- `--b0_v2` 全参数打印核对 `02-ooo-params-baseline.md`（23 行逐项）；S1（4-wide decode/rename）/S2（dispatch 8）/S3（squash 无限制）/S4（IQ64+ROB128+IntPRF192+FloatPRF256）/S5（ROB192+IntPRF256）/S6（1 FP/SIMD FU）按 02 表 E 列格集跑对照。
- [ ] commit `feat(ooo): WB5 B0_v2 验证 + S<n> 敏感性 …`

---

## 5. Part WV —— 端到端验证方案（横切，随各任务执行并汇总）

### WV1 注入器自检（每注入器/每模式，先于任何 campaign）

| 检查 | 命令模式 | 通过判据 |
|---|---|---|
| 确定性 | 同 seed 双跑 `--outdir=/tmp/a /tmp/b` | FINAL 与注入日志逐字节一致（`cmp`） |
| golden 稳定 | 无注入双跑 + 宿主原生 | 三方一致（workloads/ooo/README 先例） |
| 漏斗单调 | `CHAOS_EVENT_TRIGGER` 行 | attempted ≥ eligible ≥ injected |
| L0 激活 | L0 钩子输出 | reads_before_overwrite ≥ 1 才入分母；0 ⇒ Injected-not-activated |
| 无注入零污染 | 去旗标回归跑 | FINAL == GOLDEN_IDS（**每 commit 硬门**） |

### WV2 文献锚点复现（注入器正确性的外部证据）

- **TC'23 LQ/SQ SDC=0**：S01/S13/L01 以 TC'23 设置（MiBench、2000 次/负载）复现 0%——`01-units-and-research.md` 行原文；复现不出先怀疑注入器。
- **TC'22 DTLB**：T01 单 bit 对照（Crash AVF ~50%、Hang ~10%、SDC AVF<1%）——FS 路径（WA2 后）。
- 判据: 锚点格 Wilson CI 覆盖文献值域即 PASS；偏离则注入器审计前置。

### WV3 负对照（设计矩阵自带的证伪锚点）

- C10（replacement 只影响性能 → 应 Masked 主导）；P01/P02/P03（预取地址/控制错误不应改变架构结果——**出现 SDC 优先怀疑注入器污染 fill 路径**，03 表设计理由列原文）。
- W7 litmus 无注入全通过（禁出现结果零违例）。

### WV4 L5 守恒 + 差额自检（每格机器断言）

- 每跑: `Activated = Masked + Detected-contained + SDC + Crash + Timeout`（`lsu_l5_classify.py`）。
- 每格（回填侧 WS6）: 检测计数差额 = 0、结局计数差额 = 0（xlsx AM/AN 列语义的机器化）；违例格整格标记审计，不入汇总。

### WV5 统计口径（05 表 r12–r20 的机器化）

- 三计数分开（attempted/eligible/activated）；SDC 率分母=可分析 activated；激活率=activated/attempted——`wilson.py` 扩展 `cell_stats_v2`（或 WA5 内）。
- F1–F4 按运行聚类（cluster bootstrap 区间），不得把运行内事件当独立 Bernoulli（05 r19）。
- CRN：跨模型比较用 common random numbers（seed 清单分层：seed/bit/entry/eligible——05 r16）。
- 超时 = golden wall/sim/committed-inst 的 10× + 绝对上限（05 r17；F5 可预注册提高）。
- 主结果停止: Wilson 95% 半宽 ≤2pp 或 activated=5000（05 r14）。

### WV6 覆盖台账（诚实收口）

- 两矩阵 325+310 格终态二元：`executed / BLOCKED(原因)`——`audit_expanded_matrix.py --v2-matrix` 产出；BLOCKED 原因枚举（许可证/多核 FS 未建/依赖未达）与 §8 风险表对账。
- 未接线负载格（OoO W0/W2/W12）在补建前显式列 BLOCKED-unwired。

### WV7 回归纪律（每 commit）

- Python-only 变更: `python3 tools/manifest_validate.py --help` + 受影响工具 `--help`/自校验 + 一个无注入 golden 跑。
- C++ 变更: `scons -j16` 零警告 + 无注入 golden 跑 + 该注入器单跑验收（WV1 表）。

---

## 6. 里程碑与依赖序

```
M0 共享基座   WS1 → WS2 → WS3 → WS4(.1-.6) → WS5 → WS6        [纯基座，无 campaign]
M1 LSU 纵切   WA5.1(重锚+dry-run) → WA1 先锋模型(S10) → WA5.2 试跑（可跑格）
M2 OoO 纵切   WB1(审计) → WB2(负载) → WB3(按缺口) → WB4.1/.2   ‖ 与 M1 并行
M3 全格试跑   WA5.2 + WB4.2 完成（325+310 格 × 30 activated）
M4 筛查       WA5.3 + WB4.3（≥385 activated/格）→ WV6 首轮覆盖台账
M5 主结果     Wilson ≤2pp/5000 停止规则的顺序加样 + S 系敏感性 + 锚点/负对照终验
```

依赖硬边：WA5/WB4 依赖 WS1+WS3+WS6；WB3 依赖 WB1+WS4；WA2/WA4 依赖 FS 子模块；WV2-TC'22 依赖 WA2；W11/W12 格依赖许可证门裁决。

## 7. 算力预算与机器（诚实估算）

- 筛查下限: **635 格 × 385 = 244,475** 次 activated 运行；主结果上限: 635 × 5,000 = 3,175,000。
- 单机（cpu179 ~92 s/run、4 并行）: 筛查下限 ≈ 244,475 × 92 / 4 / 3600 ≈ **1,562 小时 ≈ 65 天**——与 V1.0 结论一致（campaign.py 头注："formal campaigns belong on a healthy 2nd machine"）。M3 起需双机；试跑阶段（~635×30≈19,050 runs ≈ 5 天单机）可单机先行。
- V1.0 先例: Int Rename 单元 72,024 正式运行（commit `be1a05d3`）——量级可行性已证。
- 产物落盘纪律: 本仓 `runs/` 为空壳先例——大宗产物按 V1.0 惯例外置（姊妹仓），本仓只入工具/文档/汇总 CSV。

## 8. 风险登记与预裁决

| # | 风险/自由度 | 预裁决（写入实施，遇新证据可修订并记档） |
|---|---|---|
| R1 | OoO F6 事件源集合（05 表只说"指定稀有事件"） | 以 d-bridge 锚点为初集：BranchMispredict（D14）、RenameSquash（D18）；WB1 审计可扩，每增一源须配无注入事件计数证据 |
| R2 | LSU sheet8 13 行 F6 定义文本与表5 不一（提取层注记 (c)） | **以表5 定义为准**；13 行集合已机器锁定，差异记录在案不改提取层 |
| R3 | LSU sheet8 12 行 SPEC oracle 文本改写（注记 (d)） | W11 负载实现时以表6 D 列为定义源；两文本差异随 BLOCKED-unwired 台账携带 |
| R4 | SPEC CPU2017 许可证 | 无证 → W11（LSU 12 格）/W12（OoO，未接线）全格 BLOCKED-license，**不降级替代** |
| R5 | 多核 FS 成本（O 系/W7/W13 + `chaosLsuF6Notify` 单核域） | WA4 内解决或显式 BLOCKED-multicore；禁止用单核近似冒充 |
| R6 | F3 高频压力（LSU 4 格） | 保留执行（05 表"只用于压力边界"），与 F0 结果分开报告 |
| R7 | ooo_proxy 默认值变更破坏 V1.0 复现 | 用 `--b0_v2` 显式预设，**不改默认**（WS5） |
| R8 | deferred 模型需新钩子（A07/P06/O04/O09 no-clean-hook） | WA1 逐个重审钩子点；确实无干净钩子 → 该模型对应格 BLOCKED-no-hook 台账，不近似实现 |
| R9 | V2.0 组合故障类型（换值/时序、状态/换值、时序/状态、翻转） | 以 03 表「故障类型」列原文为准逐模型实现，不拆成两个独立模型 |
| R10 | 分类学双轨期（V1.0 九类与 V2.0 L5 并存） | `classify_run()` 不动（V1.0 复算），`classify_run_v2()` 为增量层；两轨结果永不混表（`denominator` 列先例） |

## 9. 与 V1.0 资产的关系（不混数声明）

- V1.0 忠实层与提取产物已随 2026-09-29 清库移除（commit `26cff381`/`3415ae69`）；git 历史可查。V1.0 执行产物在姊妹仓 `/home/sdc/gem5-fi/runs/`。
- 本计划所有率/计数/区间仅以 V2.0 43 列矩阵为回填目标；引用 V1.0 运行仅作注入器血统与量级证据（WB1 审计），不进 V2.0 结果列。
- `tools/campaign.py` 的 two_phase（pilot 20/formal 2000）保留为 V1.0 复现路径；V2.0 抽样一律走 `lsu_campaign.py` 三阶段引擎（WA5/WB4）。

---

*本文档由 2026-09-29 会话基于两份 V2.0 忠实层与源码实现级深读撰写；全部 file:line 与数量断言当日 grep/运行实证。计划按 writing-plans 规范组织（一任务一 commit、checkbox 步骤、真实命令、无占位符）；执行前先读 `docs/gem5-fi/{lsu,ooo}/README.md` 的诚实性注记。*
