# R4-6-T08 agent 报告：T08 真 walk 路由修复（walk_pairing 不再被 lookup-hit 抢先消费）

> 执行者：R4-6-T08 实现型 subagent（worktree `r4-t08walk`，分支 `r4-6-t08-realwalk`，
> 基线 `ce7523ed`）。本报告只写**已实测**的内容；C++ 改动为 **COMPILE-UNVERIFIED**
> （本 worktree 明令禁 build），真机 FS run 由主 agent 集成后执行。
> 上位：`docs/gem5-fi/lsu/mdspec/round4_findings.md` §R4-5.9 / §5.9.6（T08 BLOCKED）。

## 1. 根因（两项待查问题的答案，逐行源码证据）

### 1.1 (b) `faultType=walk_pairing` 被 lookup-hit 抢先消费 —— **主根因，成立**

`CHAOS/gem5/src/arch/arm/CHAOSArmTLB/CHAOSArmTLB.cc`，`maybeCorrupt`（旧行号
:242-355；hook 调用点 `arch/arm/tlb.cc:171-173`，仅在 `retval && chaosTLB` 即
**lookup 命中**时进入）：

| 行 | 代码 | 后果 |
|---|---|---|
| :245 | `if (!entry \|\| probability <= 0.0f) return;` | campaign 传 `--tlb_probability 1.0` → 通过 |
| :252 | `max_faults != 0 && faults_injected_count >= max_faults` | campaign `--tlb_max_faults 1` → 预算额度 1 |
| :255-256 | 概率门 `probDist(rng) > probability` | 1.0 → 通过 |
| :261 | `events_to_skip` 消耗 | geometric(0.1) 跳几次 |
| :263 | `chosen = fault_type_enum;` → **WalkPairing** | 关键 |
| :274 | `chosen == PfnToMappedPage`? 否 | 跳过 F5 分支 |
| :308 | `mask = fault_mask ? fault_mask : random(bitsToChange)` | 取到非零 mask |
| :316-330 | `switch (chosen)`：StuckAtZero/StuckAtOne/BitFlip 都不是 → **`default: break`** | **不改 pfn** |
| :331-332 | `stats->numFaultsInjected++; ++faults_injected_count;` | **maxFaults=1 的唯一预算在此用光** |
| :341-351 | 打印 `Site: arm_tlb_lookup_hit, old_pfn:, new_pfn:, FaultType: walk_pairing, Mask:` | 逐字等于 pilot 证据 |

pilot 证据（§5.9.6）：
`Tick: 237950940537, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483fa8,
old_pfn: 0x81d75, new_pfn: 0x81d75, FaultType: walk_pairing, Mask: 0x4000000`
—— `old_pfn == new_pfn` 正是 `default: break` 不改 pfn 的指纹；`Mask: 0x4000000`
是 :308 取到的 mask。**这不是"没生效"，而是"在一个不属于该模型的落点上把预算花掉、
没有做任何变异"**。

随后 walk 发出点（`table_walker.cc:332-345`）的 `maybeDropWalkFill` 在
`CHAOSArmTLB.cc:133`（基线行号；每一次 walk 发出都会执行）因
`faults_injected_count >= max_faults` **恒返回 false** → 永不丢 walk → `registerTlbWalkPair` 从未被调用 → PROP-EVT 里没有
`tlb_walk` / `tlb_refill`（与 §5.9.6 现象 2 一致）。

为何 lookup-hit 一定先到：restore 后 TLB 冷，第一次翻译走 walk 填表，此后同 VA 的
翻译都是 lookup **命中**；而 F0 的抽签落点在 walk 流的第 412~806 个事件
（见 §4.3 实算），因此"第 ~10 次命中"必然先于"第 ~412 次 walk 发出"到达
`maybeCorrupt`。

### 1.2 (a) FS 下 `walker=` **确实已接线** —— 不是根因，但此前从未被真机证明

| 环节 | 证据 |
|---|---|
| CLI → SimObject | `configs/se/arm_chaos_fs.py:290`（旧 :288-306）`walker=cpu0.mmu.walker if args.tlb_fault_type == "walk_pairing" else None` |
| ctor 自挂 | `CHAOSArmTLB.cc:59-61` `if (walker) walker->setChaosTLB(this);`（**在 `probability>0` 块之外**，无条件执行） |
| 谁接收 | `table_walker.hh:1079-1083` `class ::gem5::CHAOSArmTLB *chaosTLB = nullptr; void setChaosTLB(...)` —— **成员变量，不是全局**（问题清单里问的"全局还是成员"：**成员**，挂在 `ArmISA::TableWalker` 上） |
| 谁设置 | 只有 CHAOSArmTLB ctor（`setChaosTLB` 无 python binding，故靠自挂） |
| 钩子点 | `table_walker.cc:189`（`curr_state->chaosWalkId = ++chaosNextWalkId`）+ `:332-345`（`if (chaosTLB) { ... maybeDropWalkFill(...) }`） |
| 实例唯一性 | `ArmMMU.py:117` 全 MMU 只有 1 个 `walker = Param.ArmTableWalker(...)`；`mmu.cc:71` 构造、`:104-109` itb/dtb/stage2 **共用同一实例**；`mmu.cc:1814` `walker->walk(req, tc, ...)` 即钩子所在函数 `TableWalker::walk`（非 walk_unit） |

结论：接线存在，钩子可达；pilot 零 walk-drop 的**唯一**充分解释就是 1.1 的预算被抢先消费。
本报告把这条接线在契约测试里钉死（tests/test_lsu_hook_t08_walk.py [B] 段），并加了一条
真机可见的**接线证明**（§3.2 的 probe 行）。

附带事实（支撑"真机必有真 walk"）：`arch/arm/tlb.hh` 中 `class TLB` **没有
serialize/unserialize** → checkpoint 不保存 TLB 表项 → restore 后 TLB 冷 → 第一条
翻译必为 miss → 必产生 walk；pilot 里 lookup-hit 的存在本身即证明此前已有 walk 完成过。

## 2. 改动清单（一项一 commit，均在本地分支 `r4-6-t08-realwalk`，**未 push**）

| # | commit | 文件 | 内容 |
|---|---|---|---|
| 1 | `6f4d1cce` | `CHAOS/gem5/src/arch/arm/CHAOSArmTLB/CHAOSArmTLB.{hh,cc}` | maybeCorrupt 对 WalkPairing 早退（零预算消耗）+ 一次性诊断行；switch 内显式 `case WalkPairing: return;`；maybeDropWalkFill 入口一次性 probe 行 |
| 2 | `d288c81e` | `configs/se/arm_chaos_fs.py` | walk_pairing 缺 `--chaos_armtlb` 或缺 tier → Python 侧 SystemExit（早失败，点名 flag） |
| 3 | `58de52d1` | `tools/lsu_campaign.py` | `--allow-blocked-models` 显式 opt-in（解开 MODEL_BLOCKED 死锁，理由仍留痕） |
| 4 | `07a325d6` | `tools/lsu_campaign.py` | T08 的 F0 采样窗显式钉住（warmup=0 / span=1000，值同配置默认） |
| 5 | `c134810a` | `tests/test_lsu_hook_t08_walk.py` | 契约测试（新增，约 50 项断言） |
| 6 | 本 commit | `docs/gem5-fi/lsu/mdspec/R4-6-T08-agent-report.md` + `docs/superpowers/plans/2026-10-22-r4-6-t08-realwalk.md` | 本报告 + 计划 |

### 2.1 语义不变量（明确声明）

- `bit_flip` / `stuck_at_zero` / `stuck_at_one` / `random` / `pfn_to_mapped_page`
  路径**逐字节不变**：新代码只在 `fault_type_enum == FaultType::WalkPairing` 时进入；
  T01-T04/T10 仍不带 tier、仍不传 walker（`walker=None`），contract test [C] 有断言。
- 新日志行只在 walk_pairing 模式出现；`Site: arm_tlb_walk_issue_drop` 的格式与
  R4-5.9 判据**保持一致**（未改字符串）。
- `MODEL_BLOCKED["T08"]` **保留原样**（未解阻塞）；`--allow-blocked-models` 只是
  开关，不是解除。

## 3. 修复要点

### 3.1 maybeCorrupt：lookup-hit 不是本模型的 eligible 事件

```cpp
if (!entry || probability <= 0.0f) return;

// [MDSPEC][R4-6-T08] walk_pairing is a WALK-ISSUE-ONLY model.  ...
if (fault_type_enum == FaultType::WalkPairing) {
    if (write_log && log_stream && !walk_pairing_lookup_notice) {
        walk_pairing_lookup_notice = true;
        *(log_stream->stream())
            << "Tick: " << curTick()
            << ", Site: arm_tlb_lookup_hit_skipped"
            << ", VA: 0x" << std::hex << va << std::dec
            << ", FaultType: walk_pairing (T08 walk-issue-only: NOT "
               "consumed at lookup-hit; see maybeDropWalkFill)"
            << std::endl;
    }
    return;
}
```

位置在**概率门/events_to_skip/RNG/switch 之前** → 预算、抽签、mask 全不受影响。
判定依据是模型规格的触发列（"DTLB miss 并启动 walk"，即 walk 发出流），
`arch/arm/tlb.cc` 的 lookup-hit 不属于该流。诊断行一次性打印，不静默。

### 3.2 maybeDropWalkFill：一次性接线证明

在 `lsuTrigger->onAttempt()` 之后、任何门之前，run 内首次进入时打印
`Site: arm_tlb_walk_issue_probe`（含 walk_id / VA）。它的价值：R4-5.9 pilot 无法区分
"钩子没到达"与"钩子到达但预算已空"；这一行直接把两种情形分开，且写在
`armtlb_injections.log`（Z_SYNC_FLUSH 语义与既有行一致）里，**即使 run 被 timeout
杀掉也留存** —— 而 exit-callback 的 `CHAOS_LSU_TRIGGER:` 摘要在被杀时不会打印。

### 3.3 配置早失败 + campaign 开关

- `configs/se/arm_chaos_fs.py`：`--tlb_fault_type walk_pairing` 且（未 `--chaos_armtlb`
  | `--tlb_lsu_tier off`）→ `SystemExit`，消息点名 flag 并指向本报告。
- `tools/lsu_campaign.py`：`--allow-blocked-models` 让被 MODEL_BLOCKED 的 cell
  可跑，理由回显 stdout + 写入 cell JSON 的 `model_blocked_reason`。

## 4. 主 agent 集成后**必须执行**的步骤（确切命令 + 判据）

### 4.0 集成死锁（本轮实测发现，必须先解决才能跑）

**`MODEL_BLOCKED["T08"]` 存在 → `resolve_cell` 直接返回 Blocked →
T08 三个 cell 在集成分支上根本不会被执行**（R4-5.9 的 pilot 是在**尚未加该
block** 的隔离 worktree 上跑的，因此那时能跑）。这就是 R4-6-T08 加的
`--allow-blocked-models` 的用途（下面命令已带）。

### 4.1 编译（C++ 改动 COMPILE-UNVERIFIED，必须真编译并核 warning）

```bash
cd /home/sdc/gem5-fi-ding/CHAOS/gem5 && scons -j16 build/ARM/gem5.opt
# 期望：SCONS_EXIT=0，error 0；并核 CHAOSArmTLB.cc 无新增 warning
# （基线已知 CHAOSCache -Wreorder 警告，非本轮引入）
```

### 4.2 真机 FS pilot（**精确命令**）

```bash
cd /home/sdc/gem5-fi-ding
LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py \
  --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv \
  --outdir runs/lsu/r4_t6_pilot --cells T08-F0-W9 --phase trial \
  --max-seeds-per-cell 1 --max-parallel 1 --fs-timeout 3600 \
  --allow-blocked-models \
  --fs-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015
```

要点：
- **必须**加 `--allow-blocked-models`（否则 cell 被 block 跳过，零 gem5 进程）。
- `--fs-timeout 3600`（R4-5.9 用 1500s 被杀；T08-a 的预期结局就是"翻译永不完成
  → Timeout 通道"），外层 `timeout` 要明显大于它。
- 该 checkpoint（`cpt.237949797015`）与 `gem5-fs/` 资产本轮已核实存在。
- 先跑 F0 一个 cell 一个 seed 即可判定；F4/F6 见 §5 的预算风险。

### 4.3 判据（全部为 grep/文件级，可机械核验）

产物目录：`runs/lsu/r4_t6_pilot/T08-F0-W9/seed1/`

1. `armtlb_injections.log` **必须**含（接线证明）：
   `Site: arm_tlb_walk_issue_probe` + `walk_id:` + `VA: 0x...`
   → 证明 `TableWalker::walk` 真到达了注入器。
2. `armtlb_injections.log` **必须**含（真注入）：
   `Site: arm_tlb_walk_issue_drop` + `walk_id:` + `VA: 0x...`
   → T08-a 的 walk 丢弃落点（R4-5.9 判据字符串不变）。
3. `armtlb_injections.log` **必须不含**：
   `Site: arm_tlb_lookup_hit` 且同一行含 `FaultType: walk_pairing`
   → 即 §5.9.6 的失败指纹必须消失；预期只出现一行
   `Site: arm_tlb_lookup_hit_skipped ... (T08 walk-issue-only: NOT consumed ...)`。
4. `prop_evt.txt.gz`（PROP-EVT）**必须**同时含 `kind=tlb_walk` 与 `kind=tlb_refill`，
   且二者 `walk_id` **相同**、`fault_id` 相同；`tlb_refill` 行 `field=lost` /
   `outcome=lost`；`tlb_walk.tick` == walk 发出 tick。
   → 这就是"walk/fill 配对"的可证物。
   ⚠ 诚实提示：T08-a 的丢弃发生在 `TableWalker::walk` 的同一次调用内
   （构造 WalkerState 的 tick 与丢弃 tick 相同），因此**两个节点的 `tick` 很可能是
   同一个值** —— tick 相等**不是**失败判据（`CHaOSPropagation.hh` 里
   "two distinct ticks" 的措辞对 T08-a 不适用，配对键是 `walk_id`）。
5. 机器判读：`write_chain_report` 产出的 `chain_report.json` / `chain_summary.md`
   中该 sample 的 `terminal` 应落在 L2（`provable_to == "L2"`）；若 run 被
   timeout 杀掉，campaign 的 Timeout 分支仍应保留上述 PROP-EVT 前缀
   （`Z_SYNC_FLUSH`），`injected` 计数 ≥1。
6. 期望分类：T08-a 的预期结局是 **Timeout**（翻译永不完成），**不是** PASS/SDC；
   `CHAOS_LSU_TRIGGER: injector=CHAOSArmTLB tier=F0 attempted=<N> eligible=<M>
   injected=1`（`attempted>0` 是钩子活着的第二条独立证据，若 run 正常退出才打印）。

### 4.4 通过后

判据 1–4 全满足 → 可把 T08-a 的"真机断言"写入 evidence，并按
`MODEL_BLOCKED` 纪律决定是否改写/删除 `MODEL_BLOCKED["T08"]`
（删除条件按 §R4-5.9 原文：真 campaign run + 非空注入日志 + lsu_chain_check 边）。
**本轮不替主 agent 做这个判断**。

## 5. 未决 / 风险（诚实列出，不含推测性结论）

1. **C++ 未编译**：本轮禁 build。修复在逻辑上自洽并有源码级顺序断言，但
   "能否编译通过"必须由主 agent 的 `scons` 证实（历史上 T08 首次集成即出现过
   一个真实编译错误，见 §5.9.1）。
2. **F4/F6 cell 的预算风险（未实测）**：F0 的落点可算（§4.3 的 seed1 → walk#412），
   但 F4 的首发 burst 落点是 `50000 + chaosSampleLCG(seed) % 100000`，即
   **约 9.9 万~14.1 万个 walk 事件**之后才注入；FS run 在 3600s 内能否产生这么多
   walk-issue 事件**没有任何实测数据**（walk 流从未被普查过）。若 F4 跑不出注入，
   正当处置是：延长预算 / 缩短 ROI / 先做该流的 F0 普查（tier=F0,
   span=很大的纯普查 pass）后按 `F0 census` 纪律重钉 span —— **不得**因此就说
   "F4 不成立"。
3. **F6 语义确认（结构推断，非实测）**：`onF6Event(false)` 在
   `chaos_lsu_trigger.hh:298-308` 对 tier=F6 首次调用即返回 true，故 T08-F6-W9
   会在**第 1 个** walk 发出事件丢弃 → 几乎必然在 restore 早期就把该翻译打死，
   run 会立刻卡死到 timeout（证据仍在，但 oracle（md5）行很可能不再产生）。
   这条是读代码得出的，需真机确认。
4. **span 未普查**：`ARMTLB_T08_WARMUP_EVENTS/SPAN_EVENTS = 0/1000` 取的是配置默认值
   （显式钉住只为可审计），**不是** walk 流的实测 eligible 数；F0 census 纪律下
   应以后续实测重钉。
5. **`maybeCorrupt` 的 firstClock 窗口本来就没生效**（源码注释自述"advisory"），
   本轮未改；`--ckpt-first-clock` 的重基对 T08 也不参与（walk 钩子不看窗口）。
   两者都是既有行为，未改变。
6. **walk 钩子的结构性盲区（未改）**：`table_walker.cc:313-323` 中若
   `wait_for_other || !walk_unit`（无空闲 walk unit，只可能发生在 timing 模式），
   请求走 `pendingQueue`，**不经过**注入器 —— 即这类 walk 不会成为 eligible 事件。
   F0 抽签因此少算这部分事件（对本轮判据无影响，但记录在案）。
7. 测试面：本轮的"实测证据"是**纯 Python 契约测试 + 源码顺序断言**，不含任何
   gem5/FS 运行（明令禁止）。因此本报告**不宣称** T08 已解阻塞。
