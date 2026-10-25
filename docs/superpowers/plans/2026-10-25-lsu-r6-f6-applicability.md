# R6-F6APP 实现计划：模型可应用性属于 eligibility（T04-F6-W4 收口）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 `CHAOSArmTLB` 的 `pfn_to_mapped_page` 只在"本 TLB hit 确有合法替换候选"时才向 tier 报 eligible、才消费 F6 唯一机会/F1–F4 间隔槽位，从而消除 trigger `injected=1` 而 `numFaultsInjected=0` 的 phantom 注入。

**Architecture:** 把"候选只读扫描"（不消耗 RNG、不改 TLB、不改状态）上提到 tier 决策**之前**：一次 TLB-hit lookup 先记 `attempted`；若模型无合法候选则立刻诚实 no-op 返回（不调用 `onEligible`/`onF6Event`，不增 `eligible`/`injected`，不置 F6 `spent`）；有候选才进入 tier eligibility，tier 放行后才用 RNG 从**已确认合法**的候选集里选目标并写 PFN。原先打包了 attempt+poll 的 `lookupTierAllowsInjection` 拆成 `lookupTierBookAttempt()`（只记 attempted + 一次性通知）与 `lookupTierFires(is_hit)`（tier 放行判定）。F0 legacy 分支**逐字节不动**。

**Tech Stack:** C++17（vendored gem5 v25.1.0.1 @ `CHAOS/gem5/src/`，scons 构建）、Python3 脚本式测试（`python3 tests/xxx.py`，退出码 0=全 PASS）、独立 g++ 单测（`g++ -std=c++17 -Wall -Wextra -Werror -I CHAOS/gem5/src`）。

**Spec:** 本轮用户裁决（2026-10-25，见本文 §0 设计记录）＋ `docs/gem5-fi/lsu/mdspec/R6-RULINGS-20261024.md`（F0–F6 漏斗语义：attempted/eligible/injected）。

## §0 设计记录（本轮的 spec）

### 已确认的原始事实（T04-F6-W4 / seed1，`runs/lsu/r6_c7_T04-F6-W4_s1`，binary `a9b2c236…`）

| 事实 | 值 | 来源 |
|---|---|---|
| `CHAOS_LSU_TIER_CAP` | `requested=F6 effective=F6 lookup_tier_enabled=1` | `seed1/run.out:2` |
| `CHAOS_LSU_TRIGGER` | `attempted=66310644 eligible=1 injected=1 first_eligible_tick=237950233578` | `seed1/run.out:21` |
| stats | `board.chaos_armtlb.numFaultsInjected 0` | `seed1/stats.txt:871` |
| armtlb 日志 | **仅** `Site: arm_tlb_lookup_tier` 诊断行；**0** 条 `arm_tlb_lookup_hit` | `seed1/armtlb_injections.log` |
| prop_evt | 0 事件 | `chain_report.json` |
| campaign | `count_contradiction=true` / `admission=NO-ACTIVATION` | `cell_results.json` |

对照基线（同一 binary、同 checkpoint）：
- **T04-F0-W4** seed1 真注入：`Tick 237950940537, VA 0xffffffc009483fa8, old_pfn 0x81d75, new_pfn 0xffbce, candidates: 3`，`numFaultsInjected 1`。
- **T04-F2-W4** seed1 真注入 4 次（首条 candidates=30）。
- `first_eligible_tick=237950233578` == 恢复后**第一个** TLB hit 的 tick ⇒ F6 在第一个 hit 上就消费了唯一机会。

### 根因（定论）

`CHAOSArmTLB::maybeCorrupt` 在进入 `FaultType::PfnToMappedPage` 分支**之前**先调
`lookupTierAllowsInjection(true)`；后者对该档位调用 `ChaOSLsuTrigger::onF6Event(false)`，
**立即** `spent=true; ++eligible; ++injected;`。此后才做候选扫描；第一个 hit 时
`entryTable()` 里没有第二条"valid、同页大小、不同非零 PFN"的活映射 ⇒ `candidates.empty()`
⇒ 诚实 no-op（不写日志、不计数、不注册 prop 事件）。于是 trigger 说 injected=1 而模型 0 写入。
F1–F4 同形：`onEligible()` 已在无候选事件上 `++eligible`、`scheduleNext()` 推进间隔槽，
放行后同样 no-op。

### 裁决（本轮冻结语义，适用**所有 tiered** `pfn_to_mapped_page` 档位）

1. TLB hit 仍计 `attempted`；
2. 先只读收集合法候选：**不消耗 RNG、不修改 TLB、不改变任何状态**；
3. 无合法候选 ⇒ 不调 `onEligible`/`onF6Event`、不增 `eligible`、不增 `injected`、不置 F6 `spent`、不消耗唯一机会、不写注入日志、不产生 prop_evt；
4. 出现第一个有合法候选的 TLB hit ⇒ 才进入 tier eligibility（F6 此时才消费唯一机会），tier 放行后才用 RNG 从**已确认合法**的候选集选目标；
5. 成功后 `trigger injected == stats numFaultsInjected == 注入日志真实应用行数 == 1`（三源一致）；
6. 不改 checker / campaign admission / conservation / 原始证据；不放宽合法候选条件；不伪造候选；F0 legacy 路径逐字节不变。

### 不做（本轮明确排除）

- 不顺带重构其它模型的同类提前消费（walk 家族、T05/T06/T07、mask 家族）——本轮只治 `pfn_to_mapped_page`。
- 不改 `tools/lsu_chain_check.py`、`tools/lsu_campaign.py`、admission/conservation 规则、`CHAOSPropagation` 既有 containment 修复、五格已通过报告、原始运行证据、三个既有未提交/未跟踪文档。

---

## Global Constraints

- 唯一 C++ 所有者目录：`CHAOS/gem5/src/arch/arm/CHAOSArmTLB/`（`.cc` / `.hh` / `chaos_tlb_pfn.hh`）。`chaos_lsu_trigger.hh` **本轮不改**（`onAttempt` / `onEligible` / `onF6Event` 已是分离接口，拆分在注入器侧完成，无需动触发头）。
- 构建：`cd CHAOS/gem5 && scons -j16 build/ARM/gem5.opt`（增量可 `-j126`；首次配置慢属正常，**不要中止**）。任何新增 warning/error = 失败。
- 二进制路径恒为 worktree 内 `CHAOS/gem5/build/ARM/gem5.opt`（**非** repo-root）。
- 测试跑法：脚本式 `python3 tests/<name>.py`（rc=0 即全 PASS）；独立 C++ 单测 `g++ -std=c++17 -Wall -Wextra -Werror -I CHAOS/gem5/src <file> -o /tmp/x && /tmp/x`。
- 一个提交 = 一个单元。本计划只有 **1 个代码提交**（Task 1），其后是运维阶段（构建/回归/跑格），不产生提交。
- commit 消息**不得**以 `Co-Authored-By: Claude <noreply@anthropic.com>` 结尾。
- 提交后自动 `git push` 到 `origin/lsu-mdspec-20261019`（**非** `main`）。
- 禁止 `git add -A`；只 stage 显式路径。

## Review Focus

1. **F0 legacy 逐字节不变** —— `--tlb_lsu_tier` 未挂/为 F0 时，注入 tick、VA、old/new PFN、mask、`legacy_attempted/eligible` 必须与 `a9b2c236` 完全相同。风险最高的输入：F0 + `pfn_to_mapped_page`。测试：Task 1 Step 1-c 的源码契约 + Phase C 用 `T04-F0-W4` seed1 与 `runs/lsu/r6_c7_T04-F0-W4_s1` 基线**逐字段比对**。
2. **F2/F1/F3 间隔档位的注入点会移动** —— eligible 现在只数"有候选"的事件，间隔槽位按该子流计。可接受（裁决 4），但必须重跑五格验证仍达标。风险输入：`T04-F2-W4`。
3. **`attempted` 不得因新 gate 减少** —— 每个 TLB hit 仍须计 1 次 attempt（含无候选者）。测试：Task 1 Step 1-a 断言 `attempted == 流长`。
4. **F6 `spent` 不得在无候选事件上被置位** —— 后续有候选时仍须能触发。测试：Task 1 Step 1-a 断言 `fire_index == 首个有候选的 index`（非 0）。
5. **热路径代价** —— `maybeCorrupt` 每 TLB lookup 调用一次（本格 6631 万次）。新增的 `std::vector` 默认构造不得分配堆；候选扫描只在 pfn 模型档位且 tier 已挂时发生。测试：Task 1 Step 4 目视 + 构建零 warning（无专门基准，如实记录）。

---

## File Structure

| 文件 | 责任 |
|---|---|
| `CHAOS/gem5/src/arch/arm/CHAOSArmTLB/chaos_tlb_pfn.hh`（改） | 增加依赖自由的纯判定 `PfnHookAction` / `pfnHookAction(candidate_count)` —— 注入器与独立单测共用的**唯一**可应用性规则 |
| `CHAOS/gem5/src/arch/arm/CHAOSArmTLB/CHAOSArmTLB.hh`（改） | 拆 `lookupTierAllowsInjection` → `lookupTierBookAttempt()` + `lookupTierFires(bool is_hit)`；新增私有 `collectPfnCandidates()` |
| `CHAOS/gem5/src/arch/arm/CHAOSArmTLB/CHAOSArmTLB.cc`（改） | `maybeCorrupt` 重排：attempt → 只读候选扫描 → 无候选诚实返回 → tier 放行 → 应用；pfn 分支复用已扫结果 |
| `tests/chaos_tlb_pfn_candidate_test.cc`（改） | 既有候选谓词用例 + 新增 `pfnHookAction` 三例 |
| `tests/chaos_tlb_f6_applicability_test.cc`（新） | 驱动**真** `ChaOSLsuTrigger` + **真** 谓词 + **真** `pfnHookAction`，验证 F6/F2/F5 的 phantom 消除 |
| `tests/test_lsu_r6_f6_applicability.py`（新） | 真编译真跑上两者；`CHAOSArmTLB.cc` 调用顺序源码契约；F0 legacy 块不变契约 |
| `docs/superpowers/plans/2026-10-25-lsu-r6-f6-applicability.md`（本文） | 设计记录（§0） |

---

### Task 1: pfn 可应用性 gate —— attempt/eligible/application 三段式

**Files:**
- Create: `tests/chaos_tlb_f6_applicability_test.cc`
- Create: `tests/test_lsu_r6_f6_applicability.py`
- Modify: `tests/chaos_tlb_pfn_candidate_test.cc`
- Modify: `CHAOS/gem5/src/arch/arm/CHAOSArmTLB/chaos_tlb_pfn.hh`
- Modify: `CHAOS/gem5/src/arch/arm/CHAOSArmTLB/CHAOSArmTLB.hh`
- Modify: `CHAOS/gem5/src/arch/arm/CHAOSArmTLB/CHAOSArmTLB.cc:477-600`
- Modify: `CHAOS/gem5/src/arch/arm/CHAOSArmTLB/CHAOSArmTLB.cc:909-930`

**Interfaces:**
- Consumes: `gem5::chaos_tlb::PfnCandidateView` / `isSelectablePfnTarget` / `selectPfnCandidateIndex`（既有）；`gem5::ChaOSLsuTrigger::{onAttempt,onEligible,onF6Event}`（既有）。
- Produces:
  - `gem5::chaos_tlb::PfnHookAction { AttemptOnly, PollTier }`
  - `gem5::chaos_tlb::PfnHookAction pfnHookAction(std::size_t candidate_count)`
  - `void CHAOSArmTLB::lookupTierBookAttempt()`
  - `bool CHAOSArmTLB::lookupTierFires(bool is_hit)`
  - `void CHAOSArmTLB::collectPfnCandidates(const ArmISA::TlbEntry *entry, std::vector<std::pair<const ArmISA::TlbEntry *, int>> &out) const`

---

- [ ] **Step 1-a: 写失败测试 —— 独立 C++ 单测（旧代码必然失败）**

创建 `tests/chaos_tlb_f6_applicability_test.cc`：

```cpp
/*
 * chaos_tlb_f6_applicability_test.cc — [R6-F6APP] standalone unit test for the
 * pfn_to_mapped_page funnel order. NOT part of the gem5 build; compiled:
 *
 *   g++ -std=c++17 -Wall -Wextra -Werror -I CHAOS/gem5/src \
 *       tests/chaos_tlb_f6_applicability_test.cc -o /tmp/tlb_f6app \
 *       && /tmp/tlb_f6app
 *
 * Defect under test (measured 2026-10-25, T04-F6-W4 seed1, binary a9b2c236):
 * CHAOSArmTLB::maybeCorrupt polled the tier BEFORE it scanned for a legal
 * substitute, so F6 consumed its one shot on the very FIRST TLB hit — a hit
 * with no other live same-page-size frame. Trigger reported
 * eligible=1/injected=1 while numFaultsInjected stayed 0 (phantom injection).
 * F1-F4 had the same shape: onEligible() already incremented eligible and
 * advanced next_fire on a candidate-less lookup.
 *
 * The rule under test: one TLB-hit lookup books the funnel ATTEMPT
 * unconditionally; it is ELIGIBLE only when the read-only candidate scan
 * found >= 1 legal substitute; the tier fires (consuming RNG/state) only for
 * an eligible lookup, and the mutation is applied iff the tier fired.
 */
#include <cstdint>
#include <cstdio>
#include <string>
#include <vector>

#include "arch/arm/CHAOSArmTLB/chaos_tlb_pfn.hh"
#include "cpu/o3/chaos_lsu_trigger.hh"

// standalone link shim (same as tests/chaos_armtlb_lookup_ftier_test.cc):
// chaos_lsu_trigger.hh calls curTick(), which dereferences the gem5 TLS
// pointer the event queue maintains. Outside the gem5 build nothing defines
// it — define it here and point it at a static tick in main().
namespace gem5 { namespace Gem5Internal {
__thread Tick *_curTickPtr;
} }
static gem5::Tick standalone_tick = 0;

using gem5::ChaOSLsuTier;
using gem5::ChaOSLsuTrigger;
using gem5::chaos_tlb::PfnCandidateView;
using gem5::chaos_tlb::PfnHookAction;
using gem5::chaos_tlb::isSelectablePfnTarget;
using gem5::chaos_tlb::pfnHookAction;

static int failed = 0;

static void
check(const std::string &name, bool cond, const std::string &detail = "")
{
    if (cond) {
        std::printf("PASS %s\n", name.c_str());
    } else {
        std::printf("FAIL %s%s\n", name.c_str(),
                    detail.empty() ? "" : ("  [" + detail + "]").c_str());
        ++failed;
    }
}

static PfnCandidateView
view(bool valid, uint64_t pfn, uint8_t n = 12, bool is_hit = false)
{
    PfnCandidateView v;
    v.valid = valid;
    v.pfn = pfn;
    v.page_size_bits = n;
    v.is_hit_entry = is_hit;
    return v;
}

// The legal-substitute count for a hit on `hit_idx` in `tbl` — the same
// predicate the injector and the pfn candidate unit test already share.
static std::size_t
countCandidates(const std::vector<PfnCandidateView> &tbl, std::size_t hit_idx)
{
    std::size_t n = 0;
    for (std::size_t i = 0; i < tbl.size(); ++i)
        if (i != hit_idx && isSelectablePfnTarget(tbl[hit_idx], tbl[i])) ++n;
    return n;
}

// One full hook pass over a candidate-count stream, in the order under test.
//   eligibility_gate=false reproduces the PRE-FIX order (the tier is polled
//     for every lookup; the model then honestly no-ops when no candidate
//     exists) — that is the phantom-injection shape.
//   eligibility_gate=true is the FIXED order.
// `fires` = times the tier said "inject now"; `applied` = fires that also had
// a legal candidate (the only ones the model can actually write).
struct Run
{
    uint64_t attempted = 0, eligible = 0, injected = 0;
    std::size_t fires = 0, applied = 0;
    long first_fire = -1, first_applied = -1;
};

static Run
drive(ChaOSLsuTier tier, uint64_t seed, uint64_t warmup, uint64_t span,
      bool eligibility_gate, const std::vector<std::size_t> &cands)
{
    ChaOSLsuTrigger tr(tier, seed, warmup, span);
    Run r;
    for (std::size_t i = 0; i < cands.size(); ++i) {
        tr.onAttempt();                       // (1) every TLB-hit lookup
        if (eligibility_gate &&
            pfnHookAction(cands[i]) == PfnHookAction::AttemptOnly)
            continue;                         // (2) honest no-op, nothing consumed
        const bool fire = (tier == ChaOSLsuTier::F6)
                              ? tr.onF6Event(false)   // (3) the hit IS the event
                              : tr.onEligible();
        if (fire) {
            if (r.first_fire < 0) r.first_fire = (long)i;
            ++r.fires;
            if (cands[i]) {
                if (r.first_applied < 0) r.first_applied = (long)i;
                ++r.applied;
            }
        }
    }
    r.attempted = tr.attempted;
    r.eligible = tr.eligible;
    r.injected = tr.injected;
    return r;
}

// A real mini-TLB: the hit entry, two stale zero-frame slots, and — from
// `epoch` on — a live 4 KiB frame that is a legal substitute. The counts fed
// to drive() come from the SHARED predicate, not from a magic constant.
static std::vector<std::size_t>
candidateStream(std::size_t n, std::size_t epoch)
{
    std::vector<PfnCandidateView> tbl = {
        view(true, 0x81d75, 12, /*is_hit=*/true),  // 0: the hit entry
        view(false, 0),                            // 1: stale slot (pfn 0)
        view(false, 0),                            // 2: stale slot (pfn 0)
    };
    std::vector<std::size_t> counts(n, 0);
    for (std::size_t i = 0; i < n; ++i) {
        if (i == epoch)
            tbl.push_back(view(true, 0x80000, 12));  // a live frame appears
        counts[i] = countCandidates(tbl, 0);
    }
    return counts;
}

int
main()
{
    gem5::Gem5Internal::_curTickPtr = &standalone_tick;

    const std::size_t N = 500000;
    const std::size_t EPOCH = 200000;   // first 200k hits have NO candidate
    const std::vector<std::size_t> cands = candidateStream(N, EPOCH);
    const uint64_t seed = 7;

    std::printf("[0] the synthetic stream really switches candidate supply\n");
    check("no candidate before the epoch", cands.front() == 0);
    check("a legal candidate from the epoch on",
          cands[EPOCH] == 1 && cands[N - 1] == 1);

    std::printf("[1] F6: the one shot is NOT spent on a candidate-less hit\n");
    {
        const Run fixed = drive(ChaOSLsuTier::F6, seed, 0, 0,
                                /*gate=*/true, cands);
        check("F6+gate: every hit books an attempt",
              fixed.attempted == N, std::to_string(fixed.attempted));
        check("F6+gate: eligible == 1 (only the first hit WITH a candidate)",
              fixed.eligible == 1, std::to_string(fixed.eligible));
        check("F6+gate: injected == 1", fixed.injected == 1,
              std::to_string(fixed.injected));
        check("F6+gate: exactly one fire, and it applied",
              fixed.fires == 1 && fixed.applied == 1,
              std::to_string(fixed.fires) + "/" + std::to_string(fixed.applied));
        check("F6+gate: fires at the FIRST candidate-bearing hit (not index 0)",
              fixed.first_fire == (long)EPOCH,
              std::to_string(fixed.first_fire));

        const Run pre = drive(ChaOSLsuTier::F6, seed, 0, 0,
                              /*gate=*/false, cands);
        check("pre-fix order reproduces the phantom: injected=1, applied=0",
              pre.injected == 1 && pre.fires == 1 && pre.applied == 0,
              std::to_string(pre.injected) + "/" + std::to_string(pre.applied));
        check("pre-fix order fires at index 0 (the candidate-less first hit)",
              pre.first_fire == 0, std::to_string(pre.first_fire));
        check("F6+gate has NO phantom (injected == applied)",
              fixed.injected == fixed.applied);
    }

    std::printf("[2] F2: a candidate-less fire is never counted as injected\n");
    {
        const Run fixed = drive(ChaOSLsuTier::F2, seed, 0, 0,
                                /*gate=*/true, cands);
        check("F2+gate: at least one fire", fixed.fires > 0,
              std::to_string(fixed.fires));
        check("F2+gate: every fire had a candidate (no phantom)",
              fixed.applied == fixed.fires,
              std::to_string(fixed.applied) + "/" + std::to_string(fixed.fires));
        check("F2+gate: injected == applied", fixed.injected == fixed.applied,
              std::to_string(fixed.injected) + "/" + std::to_string(fixed.applied));
        check("F2+gate: no fire before the candidate epoch",
              fixed.first_fire >= (long)EPOCH, std::to_string(fixed.first_fire));

        const Run pre = drive(ChaOSLsuTier::F2, seed, 0, 0,
                              /*gate=*/false, cands);
        check("pre-fix F2 fires inside the candidate-less prefix (phantom)",
              pre.first_fire >= 0 && pre.first_fire < (long)EPOCH,
              std::to_string(pre.first_fire));
        check("pre-fix F2: injected > applied (the defect class)",
              pre.injected > pre.applied,
              std::to_string(pre.injected) + " vs " + std::to_string(pre.applied));
    }

    std::printf("[3] F5 (permanent): same gate, every eligible hit applies\n");
    {
        const Run fixed = drive(ChaOSLsuTier::F5, seed, 0, 0,
                                /*gate=*/true, cands);
        check("F5+gate: eligible == the candidate-bearing hits",
              fixed.eligible == N - EPOCH, std::to_string(fixed.eligible));
        check("F5+gate: injected == applied == eligible", 
              fixed.injected == fixed.applied && fixed.applied == fixed.eligible,
              std::to_string(fixed.injected) + "/" + std::to_string(fixed.applied));

        const Run pre = drive(ChaOSLsuTier::F5, seed, 0, 0,
                              /*gate=*/false, cands);
        check("pre-fix F5: injected == stream length, applied < injected",
              pre.injected == N && pre.applied == N - EPOCH,
              std::to_string(pre.injected) + "/" + std::to_string(pre.applied));
    }

    std::printf("[4] the gate is a pure read (no state, no RNG)\n");
    {
        // pfnHookAction depends on the count alone and is deterministic.
        check("pfnHookAction(0) == AttemptOnly",
              pfnHookAction(0) == PfnHookAction::AttemptOnly);
        check("pfnHookAction(1) == PollTier",
              pfnHookAction(1) == PfnHookAction::PollTier);
        check("pfnHookAction(31) == PollTier",
              pfnHookAction(31) == PfnHookAction::PollTier);
        // Repeated runs with the same seed are identical (no hidden state).
        const Run a = drive(ChaOSLsuTier::F2, seed, 0, 0, true, cands);
        const Run b = drive(ChaOSLsuTier::F2, seed, 0, 0, true, cands);
        check("reproducible for a fixed seed",
              a.fires == b.fires && a.first_fire == b.first_fire &&
              a.injected == b.injected);
    }

    std::printf("\n");
    if (failed) {
        std::printf("FAILED (%d)\n", failed);
        return 1;
    }
    std::printf("ALL PASS\n");
    return 0;
}
```

- [ ] **Step 1-b: 运行，确认旧代码红**

Run: `cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019 && g++ -std=c++17 -Wall -Wextra -Werror -I CHAOS/gem5/src tests/chaos_tlb_f6_applicability_test.cc -o /tmp/tlb_f6app`
Expected: **编译失败** —— `error: 'PfnHookAction' is not a member of 'gem5::chaos_tlb'`（旧代码无该规则）。这是预期的红。

- [ ] **Step 1-c: 写源码契约失败测试**

创建 `tests/test_lsu_r6_f6_applicability.py`：

```python
#!/usr/bin/env python3
"""[R6-F6APP] T04-F6-W4 收口：模型可应用性属于 eligibility。

原始事实（runs/lsu/r6_c7_T04-F6-W4_s1，binary a9b2c236，seed1）：
  CHAOS_LSU_TRIGGER attempted=66310644 eligible=1 injected=1
  stats board.chaos_armtlb.numFaultsInjected 0
  armtlb_injections.log 只有 arm_tlb_lookup_tier 诊断行
  cell_results.count_contradiction=true / admission=NO-ACTIVATION
根因：maybeCorrupt 在候选扫描**之前**就调 onF6Event，第一个（无合法候选的）
TLB hit 便消费了 F6 唯一机会。

本测试：
  [1] 真编译 + 真运行 tests/chaos_tlb_f6_applicability_test.cc（红→绿承载）
  [2] 真编译 + 真运行 tests/chaos_tlb_pfn_candidate_test.cc（既有谓词不回归）
  [3] CHAOSArmTLB.cc 调用顺序契约：attempt → 只读候选扫描 → 无候选诚实返回
      → tier 放行 → 应用
  [4] F0 legacy 分支逐字节不变契约

用法：python3 tests/test_lsu_r6_f6_applicability.py   （退出码 0=全 PASS）
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "CHAOS/gem5/src"
TLB = ROOT / "CHAOS/gem5/src/arch/arm/CHAOSArmTLB"
ARM_CC = TLB / "CHAOSArmTLB.cc"
ARM_HH = TLB / "CHAOSArmTLB.hh"
PFN_HH = TLB / "chaos_tlb_pfn.hh"

failed = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name
          + ("" if cond or not detail else f"  [{detail}]"))
    if not cond:
        failed.append(name)


def build_and_run(harness):
    with tempfile.TemporaryDirectory() as td:
        exe = Path(td) / harness.stem
        cc = subprocess.run(
            ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
             f"-I{SRC}", str(harness), "-o", str(exe)],
            capture_output=True, text=True, cwd=str(ROOT))
        if cc.returncode != 0:
            return False, (cc.stderr or "").strip()[:300], ""
        r = subprocess.run([str(exe)], capture_output=True, text=True)
        return (r.returncode == 0 and "ALL PASS" in (r.stdout or "")), \
               (r.stdout or "").strip(), (r.stderr or "").strip()


def main():
    print("[1] 独立 C++ 单测：F6/F2/F5 的 phantom 消除（真编译 + 真运行）")
    ok, out, err = build_and_run(ROOT / "tests/chaos_tlb_f6_applicability_test.cc")
    print(out or err)
    check("f6_applicability harness compiles clean", out != "" or ok, err[:200])
    check("f6_applicability harness ALL PASS", ok, out[-160:])

    print("[2] 既有候选谓词单测不回归")
    ok2, out2, err2 = build_and_run(ROOT / "tests/chaos_tlb_pfn_candidate_test.cc")
    print(out2 or err2)
    check("pfn_candidate harness ALL PASS", ok2, out2[-160:])

    print("[3] 调用顺序契约：CHAOSArmTLB.cc 必须 attempt → 扫描 → gate → 应用")
    arm = ARM_CC.read_text()
    hh = ARM_HH.read_text()
    pfn = PFN_HH.read_text()

    check("chaos_tlb_pfn.hh defines the applicability rule",
          "pfnHookAction" in pfn and "PfnHookAction" in pfn)
    check("chaos_tlb_pfn.hh keeps the rule dependency-free (no gem5 includes)",
          "chaos_lsu_trigger.hh" not in pfn)

    check("header splits the tier poll into book-attempt + fires",
          "lookupTierBookAttempt" in hh and "lookupTierFires" in hh)
    check("the bundled attempt+poll method is gone",
          "lookupTierAllowsInjection" not in hh and
          "lookupTierAllowsInjection" not in arm)
    check("the read-only candidate scan only EXISTS once (shared helper)",
          "collectPfnCandidates" in hh and arm.count("collectPfnCandidates") >= 2)

    # The one ordering that matters: inside maybeCorrupt, on the tiered path,
    # the candidate scan + AttemptOnly early-return precede the tier poll.
    i_scan = arm.find("collectPfnCandidates(entry, pfn_candidates)")
    i_gate = arm.find("PfnHookAction::AttemptOnly")
    i_fires = arm.find("lookupTierFires(")
    check("tiered path scans candidates before it polls the tier",
          -1 < i_scan < i_fires, f"scan@{i_scan} fires@{i_fires}")
    check("the empty-candidate early return sits between them",
          -1 < i_scan < i_gate < i_fires, f"scan@{i_scan} gate@{i_gate} fires@{i_fires}")
    check("attempt is booked before the scan",
          -1 < arm.find("lookupTierBookAttempt(") < i_scan)
    check("the pre-fix bundled poll is not called from maybeCorrupt",
          "lookupTierAllowsInjection(" not in arm)
    check("the legacy F0 counters are untouched by the new gate",
          "pfnHookAction" not in arm.split("} else {", 1)[1]
          .split("FaultType chosen", 1)[0])

    print("[4] F0 legacy 分支逐字节不变契约")
    legacy = re.search(
        r"\{\s*//\s*\[R6-F0FUNNEL 2026-10-25\][\s\S]*?"
        r"if \(events_to_skip > 0\) \{ --events_to_skip; return; \}\s*\}",
        arm)
    check("legacy F0 gate sequence unchanged (attempted→cap→prob→eligible→skip)",
          legacy is not None)
    if legacy:
        block = legacy.group(0)
        for frag in ("++legacy_attempted;",
                     "if (max_faults != 0 && faults_injected_count >= max_faults) return;",
                     "if (probDist(rng) > probability) return;",
                     "++legacy_eligible;",
                     "if (events_to_skip > 0) { --events_to_skip; return; }"):
            check(f"legacy fragment present: {frag[:40]}", frag in block)

    print()
    if failed:
        print("FAILED (%d): %s" % (len(failed), ", ".join(failed)))
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 1-d: 运行，确认契约测试旧代码红**

Run: `cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019 && python3 tests/test_lsu_r6_f6_applicability.py`
Expected: 多条 FAIL —— 至少 `header splits the tier poll into book-attempt + fires`、`the bundled attempt+poll method is gone`、`tiered path scans candidates before it polls the tier`；退出码 1。（`f6_applicability harness compiles clean` 因编译失败而 FAIL。）

- [ ] **Step 1-e: 在 `chaos_tlb_pfn.hh` 落最小实现**

在 `selectPfnCandidateIndex` 之后、`} // namespace chaos_tlb` 之前插入：

```cpp
// [R6-F6APP] Model-applicability is part of ELIGIBILITY.
//
// Root cause this encodes the fix for (measured 2026-10-25, T04-F6-W4 seed1,
// binary a9b2c236): the substitution hook polled the tier BEFORE it looked
// for a legal substitute, so the F6 one-shot was consumed by the very FIRST
// TLB hit — a hit with no other live same-page-size frame. F6 recorded
// spent/eligible=1/injected=1 while the model applied nothing
// (numFaultsInjected=0, no injection log, no prop_evt): exactly the
// count_contradiction the campaign raised. F1-F4 had the same shape — a
// fired interval slot on a candidate-less lookup advanced next_fire and
// counted an injection that was never written.
//
// The rule: one TLB-hit lookup on this model books the funnel ATTEMPT (it
// reached the hook) unconditionally; it is ELIGIBLE only when the read-only
// candidate scan found at least one legal substitute; the tier fires — and
// therefore consumes RNG/state — only for an eligible lookup, and the
// mutation is applied iff the tier fired.
enum class PfnHookAction
{
    // No legal substitute: book `attempted`, then stop. No onEligible /
    // onF6Event call, no eligible/injected increment, no F6 `spent`.
    AttemptOnly,
    // A legal substitute exists: the lookup is eligible; poll the tier and
    // apply the substitution iff it fires.
    PollTier,
};

inline PfnHookAction
pfnHookAction(std::size_t candidate_count)
{
    return candidate_count ? PfnHookAction::PollTier
                           : PfnHookAction::AttemptOnly;
}
```

- [ ] **Step 1-f: 在 `tests/chaos_tlb_pfn_candidate_test.cc` 补 `pfnHookAction` 用例**

在 `using gem5::chaos_tlb::selectPfnCandidateIndex;` 之后加：
```cpp
using gem5::chaos_tlb::PfnHookAction;
using gem5::chaos_tlb::pfnHookAction;
```
在 `std::printf("[5] deterministic, reproducible selection\n");` 块**之后**、`std::printf("\n");` **之前**插入：

```cpp
    std::printf("[6] [R6-F6APP] model applicability is part of eligibility\n");
    check("no legal candidate -> AttemptOnly (nothing may be consumed)",
          pfnHookAction(0) == PfnHookAction::AttemptOnly);
    check("one legal candidate -> PollTier",
          pfnHookAction(1) == PfnHookAction::PollTier);
    check("many legal candidates -> PollTier",
          pfnHookAction(31) == PfnHookAction::PollTier);
```

- [ ] **Step 1-g: 跑两个独立单测，确认 Step 1-e/f 后绿**

Run: `cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019 && g++ -std=c++17 -Wall -Wextra -Werror -I CHAOS/gem5/src tests/chaos_tlb_f6_applicability_test.cc -o /tmp/tlb_f6app && /tmp/tlb_f6app && g++ -std=c++17 -Wall -Wextra -Werror -I CHAOS/gem5/src tests/chaos_tlb_pfn_candidate_test.cc -o /tmp/tlb_pfn && /tmp/tlb_pfn`
Expected: 两者均以 `ALL PASS` 结束，rc=0。

- [ ] **Step 1-h: 注入器侧 —— 拆接口（`CHAOSArmTLB.hh`）**

把 `CHAOSArmTLB.hh:151-152` 的
```cpp
    bool lookupTierMounted() const;
    bool lookupTierAllowsInjection(bool is_hit);
```
替换为
```cpp
    bool lookupTierMounted() const;
    // [R6-F6APP] The tier poll is SPLIT so model applicability can sit
    // between its two halves: `BookAttempt` runs for every TLB-hit lookup
    // (funnel: attempted) and is the only half the candidate-less case may
    // reach; `Fires` is the tier's inject-now decision for one ELIGIBLE
    // lookup and must only be called once a legal candidate is known to
    // exist (F6 consumes its one shot here; F1-F4 advance their interval
    // slot here). See the ruling in chaos_tlb_pfn.hh.
    void lookupTierBookAttempt();
    bool lookupTierFires(bool is_hit);
```
并在 `private:` 区（`snapshotEntry` 声明之后）加：
```cpp
    // [R6-F6APP] Read-only collection of the legal pfn-substitute candidates
    // for `entry`, in deterministic entryTable() order, paired with their
    // table index. Pure scan: no RNG draw, no TLB mutation, no member state
    // change — this IS the applicability test the tier gate must consult
    // BEFORE consuming a fire opportunity.
    void collectPfnCandidates(
        const ArmISA::TlbEntry *entry,
        std::vector<std::pair<const ArmISA::TlbEntry *, int>> &out) const;
```
在 `#include <random>` 一行之前加 `#include <utility>` 与 `#include <vector>`。

- [ ] **Step 1-i: 注入器侧 —— 实现拆分（`CHAOSArmTLB.cc`）**

把 `CHAOSArmTLB::lookupTierAllowsInjection` 整个函数体（`.cc:163-187`）替换为：

```cpp
    // [R6-F6APP] The funnel ATTEMPT half of the lookup-tier poll. One TLB-hit
    // lookup books one attempted, unconditionally: the hook really ran. The
    // one-shot reachability/budget notice is emitted here (the first lookup
    // of a tiered run), so the proof line lands in armtlb_injections.log even
    // when no candidate ever appears.
    void
    CHAOSArmTLB::lookupTierBookAttempt()
    {
        lsuTrigger->onAttempt();
        if (!tier_lookup_notice) {
            tier_lookup_notice = true;
            if (write_log && log_stream) {
                *(log_stream->stream())
                    << "Tick: " << curTick()
                    << ", Site: arm_tlb_lookup_tier"
                    << ", FaultType: " << faultTypeToString(fault_type_enum)
                    << " (lookup path now polls lsuTrigger; tier=F"
                    << static_cast<int>(lsuTrigger->tier)
                    << "; a tiered run does NOT consume --tlb_max_faults="
                    << max_faults << " — the tier is the frequency model)"
                    << std::endl;
            }
        }
    }

    // [R6-F6APP] The tier's inject-now decision for one ELIGIBLE lookup.
    // Callers must have established model applicability first (for
    // pfn_to_mapped_page that means a non-empty legal-candidate scan): this
    // is the only place a tier consumes its fire opportunity — F6 sets
    // `spent`, F1-F4 advance `next_fire` — so it must never be reached by a
    // lookup the model cannot act on.
    bool
    CHAOSArmTLB::lookupTierFires(bool is_hit)
    {
        if (lsuTrigger->tier == ChaOSLsuTier::F6) {
            // The F6 event source for the lookup path IS a TLB hit
            // (09 §2.1 map): a miss never consumes the arm.
            return is_hit ? lsuTrigger->onF6Event(false) : false;
        }
        return lsuTrigger->onEligible();
    }

    // [R6-F6APP] Read-only candidate scan (see the header). Deterministic
    // entryTable() order; the legality test is the shared predicate
    // chaos_tlb::isSelectablePfnTarget (chaos_tlb_pfn.hh).
    void
    CHAOSArmTLB::collectPfnCandidates(
        const ArmISA::TlbEntry *entry,
        std::vector<std::pair<const ArmISA::TlbEntry *, int>> &out) const
    {
        out.clear();
        if (!tlb || !entry) return;
        const auto &tbl = tlb->entryTable();
        chaos_tlb::PfnCandidateView hit_view{};
        hit_view.valid = entry->valid;
        hit_view.pfn = entry->pfn;
        hit_view.page_size_bits = entry->N;
        hit_view.is_hit_entry = false;
        int table_idx = 0;
        for (auto it = tbl.begin(); it != tbl.end(); ++it) {
            chaos_tlb::PfnCandidateView cand{};
            cand.valid = it->valid;
            cand.pfn = it->pfn;
            cand.page_size_bits = it->N;
            cand.is_hit_entry = (&(*it) == entry);
            if (chaos_tlb::isSelectablePfnTarget(hit_view, cand))
                out.emplace_back(&(*it), table_idx);
            ++table_idx;
        }
    }
```

- [ ] **Step 1-j: 注入器侧 —— `maybeCorrupt` 重排**

把 `CHAOSArmTLB.cc:477-513` 的 tier 闸门整块（从 `// [MDSPEC][R6-FIXCPP/B] F-tier gate.` 注释起，到 `if (events_to_skip > 0) { --events_to_skip; return; }` 及其闭合 `}` 止）替换为：

```cpp
        // [MDSPEC][R6-FIXCPP/B] F-tier gate. A mounted non-F0 tier IS the
        // frequency model for the lookup path (event-normalized, one
        // eligible event per TLB-hit lookup) and replaces the legacy
        // chain (--tlb_max_faults / --tlb_probability / the seed-varied
        // eligible-event skip) — the latter would silently cap every tier
        // back to a single F0 shot, which is exactly the R6-FTIER defect.
        // F0 / no tier mounted: legacy path, byte-equivalent to pre-R6.
        //
        // [R6-F6APP] Model applicability is part of ELIGIBILITY. The pfn
        // substitution model can only act on a hit that has a legal
        // substitute, so for it the read-only candidate scan runs BEFORE the
        // tier is polled (no RNG, no TLB write, no state change): a hit with
        // an empty candidate set books the funnel ATTEMPT and returns — it
        // never books eligible/injected and never consumes a tier's fire
        // opportunity (F6's one shot, an F1-F4 interval slot). Without this,
        // F6 spent its shot on the first TLB hit of the restored checkpoint
        // (T04-F6-W4 seed1: trigger injected=1, numFaultsInjected=0).
        std::vector<std::pair<const ArmISA::TlbEntry *, int>> pfn_candidates;
        bool pfn_scanned = false;
        if (lookupTierMounted()) {
            lookupTierBookAttempt();      // attempted, for every TLB hit
            if (fault_type_enum == FaultType::PfnToMappedPage) {
                collectPfnCandidates(entry, pfn_candidates);
                pfn_scanned = true;
                if (chaos_tlb::pfnHookAction(pfn_candidates.size())
                        == chaos_tlb::PfnHookAction::AttemptOnly)
                    return;               // honest no-op, nothing else consumed
            }
            if (!lookupTierFires(/*is_hit=*/true)) return;
        } else {
            // [R6-F0FUNNEL 2026-10-25] PASSIVE observation, legacy F0 path.
            // One attempted per F0 lookup-hook call that reaches the legacy
            // chain (walk/CAM models returned above, so nothing is double
            // counted across hooks). Increment only — no draw, no branch.
            // [R6-F6APP] BYTE-EQUIVALENT: the legacy path does NOT consult
            // the applicability gate — its gate order (attempted -> fault
            // cap -> probability draw -> eligible -> skip budget) is the
            // pre-R6 sequence verbatim.
            ++legacy_attempted;

            if (max_faults != 0 && faults_injected_count >= max_faults) return;

            // Probability gate: per-lookup Bernoulli.
            std::uniform_real_distribution<float> probDist(0.0f, 1.0f);
            if (probDist(rng) > probability) return;

            // [R6-F0FUNNEL] Eligible = past the entry + fault-cap + probability
            // gates, BEFORE the skip budget is consumed — the same junction
            // the tier path's onEligible() counts at. Observation only: the
            // counters are written after every gate has already decided, so
            // the skip/cap/RNG arithmetic below is untouched.
            ++legacy_eligible;
            if (legacy_eligible == 1)
                legacy_first_eligible_tick = curTick();
            legacy_last_eligible_tick = curTick();

            // Sampling-bias fix (see .hh): consume the skip budget on ELIGIBLE
            // events (past the entry + probability gates) before the first
            // fault, so distinct seeds inject at distinct lookup sites.
            if (events_to_skip > 0) { --events_to_skip; return; }
        }
```

再把 `FaultType::PfnToMappedPage` 分支（`.cc:537-600`）中的候选收集段替换为复用：

找到
```cpp
        if (chosen == FaultType::PfnToMappedPage) {
            if (!tlb) return;
```
在其后、`// [R6-FIXC] Collect candidate entries,` 注释块与那段 `std::vector<std::pair<const ArmISA::TlbEntry *, int>> candidates; ... for (auto it = tbl.begin(); ...) { ... }` 的整段，替换为：
```cpp
            // [R6-F6APP] Tiered runs already scanned read-only, before the
            // tier was polled (and are guaranteed non-empty here); the legacy
            // F0 path scans now, at exactly the pre-R6 point in the sequence,
            // so its RNG stream and injection site are byte-identical.
            std::vector<std::pair<const ArmISA::TlbEntry *, int>> candidates;
            if (pfn_scanned) {
                candidates.swap(pfn_candidates);
            } else {
                collectPfnCandidates(entry, candidates);
            }
            if (candidates.empty()) return;  // no legal substitute (honest no-op)
```
保留其后的 `Addr old_pfn = entry->pfn;` 起至 `return;` 的全部内容不变（RNG 选择、`entry->pfn` 写入、stats、日志、`registerTrace`）。

- [ ] **Step 1-k: 跑两个单测 + 契约测试，确认全绿**

Run: `cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019 && python3 tests/test_lsu_r6_f6_applicability.py && python3 tests/test_lsu_tlb_pfn_candidate.py`
Expected: 两者均 `ALL PASS`，rc=0。

- [ ] **Step 1-l: 关联回归 —— 必须仍绿**

Run:
```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019
python3 tests/test_lsu_r6_lookup_ftier_trigger.py
python3 tests/test_lsu_r6_f0funnel.py
python3 tests/test_lsu_ftier_armtlb_lookup.py
python3 tests/test_lsu_r6_contained_chain_contract.py
python3 tests/test_lsu_campaign_count_contradiction.py
```
Expected: 全部 rc=0。任一非 0 → 停止，先修再继续。

- [ ] **Step 1-m: 构建 gem5（零新增 warning/error）**

Run:
```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5
scons -j16 build/ARM/gem5.opt 2>&1 | tail -30
```
Expected: 构建成功；`CHAOSArmTLB.cc.o` 重编；无新增 warning/error。记录新二进制身份：
```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019
sha256sum CHAOS/gem5/build/ARM/gem5.opt; stat -c '%s %y' CHAOS/gem5/build/ARM/gem5.opt
git rev-parse HEAD
```

- [ ] **Step 1-n: 提交（唯一原子提交）**

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019
git add CHAOS/gem5/src/arch/arm/CHAOSArmTLB/chaos_tlb_pfn.hh \
        CHAOS/gem5/src/arch/arm/CHAOSArmTLB/CHAOSArmTLB.hh \
        CHAOS/gem5/src/arch/arm/CHAOSArmTLB/CHAOSArmTLB.cc \
        tests/chaos_tlb_pfn_candidate_test.cc \
        tests/chaos_tlb_f6_applicability_test.cc \
        tests/test_lsu_r6_f6_applicability.py \
        docs/superpowers/plans/2026-10-25-lsu-r6-f6-applicability.md
git commit -F - <<'EOF'
[LSU][MDSPEC][R6-F6APP] pfn_to_mapped_page 模型可应用性属于 eligibility

原始缺陷（T04-F6-W4 seed1，binary a9b2c236）：maybeCorrupt 在候选扫描之前
就调 onF6Event，第一个 TLB hit（恢复后无第二条合法活映射）便消费了 F6 唯一
机会 → trigger attempted=66310644 eligible=1 injected=1 而
stats numFaultsInjected=0、注入日志 0 条真注入、prop_evt 0 事件、
count_contradiction=true。

修复：attempt / eligibility / application 三段式。每次 TLB-hit lookup 只记
attempted；pfn 模型先做只读候选扫描（不消耗 RNG、不改 TLB、不改状态）；
无合法候选则诚实返回，绝不调 onEligible/onF6Event、不增 eligible/injected、
不置 F6 spent；有候选才进 tier eligibility，tier 放行后才用 RNG 从已确认
合法的候选集选目标。lookupTierAllowsInjection 拆为
lookupTierBookAttempt + lookupTierFires。F0 legacy 分支逐字节不变。

测试：tests/chaos_tlb_f6_applicability_test.cc（真 ChaOSLsuTrigger + 真谓词
驱动，F6/F2/F5 假注入消除、attempted 不减、F6 不在无候选事件上置 spent）；
tests/test_lsu_r6_f6_applicability.py（真编译真跑 + 调用顺序契约 + F0 legacy
不变契约）；chaos_tlb_pfn_candidate_test.cc 补 pfnHookAction 用例。
EOF
```
Expected: 提交成功，且 `git show --stat HEAD` 只含上述 7 个文件。确认消息**不含** `Co-Authored-By: Claude`。

- [ ] **Step 1-o: 推送集成分支**

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019
git push origin lsu-mdspec-20261019
```
Expected: push 成功，远端 HEAD == 新提交 SHA。

---

## Phase B（运维，无提交）：完整回归对比基线

- [ ] **B1: 归一化 baseline 回归产物**

Run: `ls -la /home/sdc/gem5-fi-ding/runs/lsu/r6_f6app_regress_baseline.tsv && tail -3 /home/sdc/gem5-fi-ding/runs/lsu/r6_f6app_regress_baseline.tsv`
Expected: 末行为 `DONE`（若仍在跑，等其结束；该脚本在改动**之前**已启动，用的是 4e61725f 基线树）。

- [ ] **B2: 跑 after 回归**

Run: `cd /home/sdc/gem5-fi-ding && ./runs/lsu/r6_f6app_regress.sh after`
Expected: `runs/lsu/r6_f6app_regress_after.tsv` 末行 `DONE`。

- [ ] **B3: 差集，要求 NEW FAIL=0**

Run:
```bash
cd /home/sdc/gem5-fi-ding
python3 - <<'EOF'
b = dict(l.split('\t')[:2] for l in open('runs/lsu/r6_f6app_regress_baseline.tsv') if l.strip())
a = dict(l.split('\t')[:2] for l in open('runs/lsu/r6_f6app_regress_after.tsv') if l.strip())
new = [k for k in a if a[k] != '0' and b.get(k) == '0']
fixed = [k for k in a if a[k] == '0' and b.get(k) not in (None, '0')]
print("NEW FAIL:", new)
print("newly green:", fixed)
print("baseline non-zero:", {k: v for k, v in b.items() if v != '0'})
EOF
```
Expected: `NEW FAIL: []`。**非空 → 立即停止并汇报**（不继续构建/跑格）。

- [ ] **B4: 记录构建身份**

Run:
```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019
echo "binary_source_head=$(git rev-parse HEAD)"
sha256sum CHAOS/gem5/build/ARM/gem5.opt
stat -c 'size=%s mtime=%y' CHAOS/gem5/build/ARM/gem5.opt
```
Expected: 记入本轮汇报；该 SHA 取代 `a9b2c236…` 成为后续唯一二进制身份。若 B3 显示 NEW FAIL=0 但构建已在 Step 1-m 完成，**不要重建**。

---

## Phase C（运维，无提交）：先单独验证 T04-F6 seed1，再补五格，再 seed2/seed3

- [ ] **C1: 更新运行身份文件**

把新 SHA 写入 `/home/sdc/gem5-fi-ding/runs/lsu/r6_c8_bin_identity.txt`（格式同 `r6_c7_bin_identity.txt`：`NEW_BIN_SHA=<sha>`）。
把 `runs/lsu/r6_c7_run.sh` 复制为 `runs/lsu/r6_c8_run.sh`，改其中 `r6_c7_` 前缀为 `r6_c8_`、身份文件为 `r6_c8_bin_identity.txt`，并在**每个 cell 结束**时（`echo "$rc" > "$OUT/.exit_code"` 之后）用 `flock` 串行重写 manifest 以带上 exit_code（见 C2）。
把 `runs/lsu/r6_mkmanifest.py` 复制为 `r6_mkmanifest2.py`，新增：
```python
    ec = out / ".exit_code"
    "exit_code": (int(ec.read_text().strip()) if ec.exists()
                  and ec.read_text().strip().lstrip("-").isdigit() else None),
```
并把它加进 `man` 字典（放在 `"status"` 之后）。

- [ ] **C2: 只跑 T04-F6-W4 / seed1（全新目录，gem5 并发 1）**

Run:
```bash
cd /home/sdc/gem5-fi-ding
tmux new-session -d -s r6c8-f6 'cd /home/sdc/gem5-fi-ding && ./runs/lsu/r6_c8_run.sh f6 1 T04-F6-W4 >> runs/lsu/r6_c8_f6.log 2>&1; tmux kill-session -t r6c8-f6'
```
（若 `r6_c8_run.sh` 的 cell 循环不认 `f6` 批次，直接传 RunID：`./runs/lsu/r6_c8_run.sh 9 1 T04-F6-W4`。）

- [ ] **C3: 判据（全部必须成立，任一不成立 → 停止，不跑其它格）**

Run:
```bash
cd /home/sdc/gem5-fi-ding
O=runs/lsu/r6_c8_T04-F6-W4_s1
grep -n "CHAOS_LSU_TIER_CAP\|CHAOS_LSU_TRIGGER" $O/T04-F6-W4/seed1/run.out
grep -n "numFaultsInjected" $O/T04-F6-W4/seed1/stats.txt
cat $O/T04-F6-W4/seed1/armtlb_injections.log
python3 - <<'EOF'
import json
d = json.load(open('runs/lsu/r6_c8_T04-F6-W4_s1/T04-F6-W4/cell_results.json'))
r = d['runs'][0]; c = r['chain']
print("attempted", d['attempted'], "activated", d['activated'])
print("outcome", r['outcome'], "terminal", c['terminal'], "provable_to", c['provable_to'])
print("admitted", c['admitted'], "certified", c['certified'], "violations", c['admission']['violations'])
print("contradiction", r['count_contradiction'], "conservation", d['conservation'])
print("gate", d['admission_gate_status'])
EOF
sha256sum .claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt
cat $O/.exit_code; python3 -c "import json;print(json.load(open('$O/manifest.json'))['exit_code'])"
```
Expected 全部成立：`requested=F6 effective=F6 lookup_tier_enabled=1`；`attempted>0`；`eligible=1`；`injected=1`；`numFaultsInjected 1`；日志**有 1 条** `Site: arm_tlb_lookup_hit` 真应用行（含 `VA:`/`old_pfn:`/`new_pfn:`）；`contradiction False`；`conservation OK`；`gate` 不再是 `NO-ACTIVATION`；`admitted True`；`violations []`；`certified True`；`terminal` 为 `full` 或真实显式 containment；正常 EOF；stats 非零；二进制 SHA 前后不变；`.exit_code`=0 且 manifest `exit_code`=0（非 null）。
**该格通过后即为新 SHA 下 T04-F6 的权威 seed1，不重跑。**

- [ ] **C4: 同 SHA 补齐其余五格 seed1（全新目录，gem5 并发 ≤2，分批）**

Run:
```bash
cd /home/sdc/gem5-fi-ding
tmux new-session -d -s r6c8-b1 'cd /home/sdc/gem5-fi-ding && ./runs/lsu/r6_c8_run.sh 1 1 >> runs/lsu/r6_c8_b1.log 2>&1; tmux kill-session -t r6c8-b1'
tmux new-session -d -s r6c8-b2 'cd /home/sdc/gem5-fi-ding && ./runs/lsu/r6_c8_run.sh 2 1 >> runs/lsu/r6_c8_b2.log 2>&1; tmux kill-session -t r6c8-b2'
```
（batch 1 = `T01-F0-W4 T02-F0-W4 T04-F0-W4`；batch 2 = `T02-F2-W4 T04-F2-W4`——T04-F6 已在 C2 完成。若脚本默认 batch 2 仍含 T04-F6，用显式 RunID 传参。）

- [ ] **C5: 六格 seed1 验收（必须 6/6）**

每格逐项核对：`admitted=True`、`violations=[]`、`certified=True`、无 `Unknown`、funnel 完整、三源一致、`count_contradiction=false`、`conservation=OK`、campaign 与 checker 一致、同一二进制 SHA；T01 为真实 L2 `detected_contained`；T02/T04 传播格为 full L0→L5。
另**逐字段比对 F0 基线**：

Run:
```bash
cd /home/sdc/gem5-fi-ding
diff <(sed 's/^Tick: //' runs/lsu/r6_c7_T04-F0-W4_s1/T04-F0-W4/seed1/armtlb_injections.log) \
     <(sed 's/^Tick: //' runs/lsu/r6_c8_T04-F0-W4_s1/T04-F0-W4/seed1/armtlb_injections.log) && echo "F0 IDENTICAL"
```
Expected: `F0 IDENTICAL`（与 Review Focus 1 一致）。任一格不达标 → 立即停止，保存现场，汇报。

- [ ] **C6: seed1 6/6 后，直接补 seed2 / seed3（不再等确认）**

Run:
```bash
cd /home/sdc/gem5-fi-ding
for s in 2 3; do
  tmux new-session -d -s r6c8-s$s "cd /home/sdc/gem5-fi-ding && ./runs/lsu/r6_c8_run.sh 3 $s >> runs/lsu/r6_c8_s$s.log 2>&1; tmux kill-session -t r6c8-s$s"
done
```
要求：每 RunID×seed 独占 flock；全新目录；detached tmux；SSH 断开不停；每 seed 独立 manifest/.done/.exit_code；gem5 并发 ≤2；**任一 seed 失败立即停止未完成任务并保存现场**；不得用一个 seed 的成功替代另一个。

- [ ] **C7: 清理与记录**

Run: `tmux ls`
Expected: 无遗留空 `r6c8-*` session（每个 batch 结束自 `tmux kill-session`）。若 `tmux ls` 报 "no server running" 也属正确。
确认全部 manifest 的 `exit_code` 非 null 且等于对应 `.exit_code`：
```bash
cd /home/sdc/gem5-fi-ding
python3 - <<'EOF'
import json, glob
bad = []
for m in glob.glob("runs/lsu/r6_c8_*/manifest.json"):
    d = json.load(open(m))
    if d.get("exit_code") is None: bad.append(m)
print("manifests with null exit_code:", bad or "none")
EOF
```

---

## Phase D（运维，无提交）：18/18 之后

- [ ] **D1: 冻结候选 + 状态表更新**：把新 SHA 标为最终冻结候选；更新六格权威状态与证据索引（新文件，**不改** `R6-STATUS-TABLE.json`/`.md`）。
- [ ] **D2: 输出六格 × 三 seed 汇总**。
- [ ] **D3: 选下一批 6 个 RunID**：条件 = 当前未证明完整链、配置已实现、无外部资源/规格阻塞、可在当前冻结二进制上运行。列出 RunID 与选择理由。
- [ ] **D4: 直接开始下一批每格 1 个 seed 的 pilot**（gem5 并发 ≤2；任一失败停止该批并汇报）。
- [ ] **D5: 仍不启动完整正式实验、不合并 fi-ding。**

---

## Self-Review

**1. Spec coverage**

| 裁决条款 | 落点 |
|---|---|
| 1 TLB hit 仍计 attempted | Step 1-j `lookupTierBookAttempt()` 在 gate 之前无条件调用；1-a 断言 `attempted == N` |
| 2 先只读收集候选 | Step 1-i `collectPfnCandidates`（无 RNG/无写/无状态）；1-a 单测经真谓词驱动 |
| 3 无候选不调 onEligible/onF6Event、不增 eligible/injected、不置 spent、不写日志、不产 prop_evt | Step 1-j `AttemptOnly` 早返回；1-a 断言 `eligible==1 && fires==1 && applied==1 && first_fire==EPOCH` |
| 4 首个有候选 hit 才进 eligibility；tier 放行后才用 RNG 选目标 | Step 1-j 顺序 + Step 1-… 保留 `selectPfnCandidateIndex(candidates.size(), rng())` 于 fire 之后 |
| 5 三源一致 | Phase C3 逐项核对 trigger/stats/日志 |
| 6 不改 checker/campaign/admission/conservation/原始证据；不放宽候选；F0 不变 | 只有 3 个 C++ 文件 + 3 个测试被改；Step 1-c `[4]` 契约 + C5 `F0 IDENTICAL` |
| 三 6 项定向测试 | 1-a（第 1/2/3 项：F6 首无候选、后续首触发、后续不再注入）、1-a `[2]`（第 4 项 F2）、C5（第 5 项 F0）、C5 + `test_lsu_r6_contained_chain_contract.py`（第 6 项 T01） |
| 四 顺序：红→实现→定向绿→原子提交→串行合入→完整回归→构建一次→记录身份→推送 | Step 1-b/1-d 红；1-e..1-j 实现；1-k 绿；1-n 提交；1-o 推送；Phase B 回归（NEW FAIL=0）；1-m 构建；B4 记录 |
| 五 先单独验证 T04-F6 seed1（并发 1，全新目录，全部判据） | Phase C1-C3 |
| 六 补齐其余五格 seed1（并发 2，分批） | Phase C4-C5 |
| 七 seed1 6/6 后自动补 seed2/seed3（flock/全新目录/detached tmux/独立 manifest） | Phase C6 |
| 八 manifest exit_code 非 null + tmux 回收 | Phase C1（mkmanifest2）、C7 |
| 九 18/18 后下一批 6 个 RunID + pilot | Phase D |
| 十 最终汇报清单 | 交付说明 |

**2. Placeholder scan**：无 TBD/TODO；每个代码步给出完整可编译内容；Phase C 的脚本改动给出具体补丁行。

**3. Type consistency**：`PfnHookAction`/`pfnHookAction` 在 `.hh`、`.cc`、两个 C++ 单测、Python 契约中拼写一致；`lookupTierBookAttempt`/`lookupTierFires`/`collectPfnCandidates` 在 `.hh` 声明与 `.cc` 定义一致；`collectPfnCandidates(const ArmISA::TlbEntry*, std::vector<std::pair<const ArmISA::TlbEntry*,int>>&) const` 签名在 `.hh`/`.cc`/调用点一致。

**4. Review Focus**：5 条已分别落到 Step 1-a（第 3、4 条）、Step 1-a `[2]`（第 2 条）、Step 1-c `[4]` + Phase C5（第 1 条）、Step 1-j 注释 + 构建零 warning + 1-m（第 5 条）。

## 已知风险（如实记录）

- **F2/F1/F3 注入点会移动**（Review Focus 2）：`T04-F2-W4` 的 eligible 子流变小，间隔槽位落点后移；若移位后链路不再 full L0→L5，Phase C5 将失败 → 按用户停点规则立即停止汇报，不放宽判据。
- **F6 实现层无法在 gem5 外做端到端单测**：Step 1-a 覆盖纯规则 + 真触发器交互，Step 1-c `[3]` 用源码顺序契约钉住注入器确实按该顺序调用；最终真值由 Phase C3 的 FS 运行给出。
