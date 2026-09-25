# LSU W2 — 触发语义 F0–F6（事件归一化触发层）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans / subagent-driven-development.

**Goal:** 实现 LSU 北极星的 F0–F6 七档触发语义（05 r2–r8，**eligible-event 归一化**）+ attempted/eligible/injected 三计数，并以 CHAOSAddrPath 为首个消费者实证（F4 突发∈[2,4]、F6 首事件单发、F0–F3 事件比率、F5 永久）。

**Architecture:** 新建 header-only `src/cpu/o3/chaos_lsu_trigger.hh`（LSU 事件分母触发器 + 漏斗计数 + F6 事件枚举），**不改** ooo 轨道的 `chaos_trigger.hh`（周期分母，语义冲突见裁决 R1）；四个 F6 事件源各加一行守卫通知钩子（W1 §2.1 映射表落点）；CHAOSAddrPath 加 LSU 触发消费路径（默认关，零回归）。

**Spec:** `docs/gem5-fi/lsu/05-frequency-and-sampling.md` r2–r8（裁决权威）+ `04-observation-points.md` L0 + `09-implementation-plan.md` W2 + §2.1（W1 F6 映射表/chaos_l0 现状）。

## Global Constraints

- 分支 fi-ding；显式路径 staging；commit 无 Co-Authored-By 尾注；push 被拒先 rebase。
- **R1 裁决（分母冲突）**：现有 `chaos_trigger.hh` 的 F1/F2/F3 = 2.6M/260K/26K **cycles** 固定均值间隔（ooo 02 频率语义）；LSU 05 r3–r5 = 每 **1M/100K/10K eligible events**——分母不同，不可混用。按 09 §6.1（00–08 优先）+ 轨道隔离纪律：**新建** `chaos_lsu_trigger.hh`，`chaos_trigger.hh` 逐字节不动（ooo 轨道财产）。
- **R2 裁决（activated 口径分期）**：04 L0 的 activated =「故障被下游读取/使用」（read-back 判定，chaos_l0.hh 已有该口径的 per-item 机制）。W2 触发层输出 **attempted/eligible/injected** 三计数 +「activated 交付 W3 L0 层」的显式声明（05 r12 激活率分母=activated 的完整落地在 W3）。
- **R3 裁决（消费者范围）**：W1 ⑧ 证实 fire() 当前零消费。W2 = 触发层 + **一个**消费者（CHAOSAddrPath——W4 宿主，eligible event = 每次 sendFragmentToTranslation）实证全链；其余注入器在 W4–W8 各自改造时切换（各单元计划内含），不在 W2 批量重接。
- 构建纪律：增量构建允许 `-j126`（仅重编改动文件）；C++ 零警告；改动默认路径行为零变化（新逻辑全部在新参数之后，默认 off）。
- 回归锚：reg_chain golden `f247ef3fe6f02cfd` 在 C4-LSU（新参数全默认，即不启用 LSU 触发）不变；mini_check golden `07568da9f3ad5665` 不变。

## 已核实事实（W1 §2.1 + chaos_trigger.hh 全文 2026-09-25 亲读）

- `chaos_trigger.hh`（93 行，header-only，无 SConscript 条目）：`ChaOSTier{F0,F1,F2,F3,F5}` 周期分母；`chaosSampleLCG` 来自 `chaos_event_sample.hh`（复用同一 LCG）。
- F6 事件源落点（W1 映射表）：TLB hit=`TLB::lookup` tlb.cc:150（**FS-only**，SE 零调用）；SQ forward=`LSQUnit::read` FullAddrRangeCoverage 分支 lsq_unit.cc:1483（CHAOSLSQFwd 已挂 :1536）；dirty eviction=`Cache::evictBlock` DirtyBit 判定 cache.cc:965；CAS 成功=`BaseCache::satisfyRequest` SwapReq 分支 base.cc:1185/:1198。
- CHAOSAddrPath 现状：挂 `LSQ::sendFragmentToTranslation`（lsq.cc:1137-1139），Byte7Zero/LowBitFlip 两模式，自带 inWindow+max_faults+probability（CHAOSAddrPath.cc:38-51/:57/:62），SE-inert 诚实标注。
- chaos_l0.hh：per-item read-back（reads_before_overwrite/overwritten），无三计数漏斗。

## File Structure

```
CHAOS/gem5/src/cpu/o3/chaos_lsu_trigger.hh   [Create — header-only，无 SConscript 改动]
CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.hh/.cc  [Modify — LSU 触发消费路径]
CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.py      [Modify — 新参数]
configs/se/lsu_proxy.py                       [Modify — --freq_tier/--warmup_events/--f6_event 参数]
```

---

### Task 1: chaos_lsu_trigger.hh（触发层 + 三计数）

**Files:** Create `CHAOS/gem5/src/cpu/o3/chaos_lsu_trigger.hh`

- [x] **Step 1: 写入完整头文件**（代码如下，逐字）

```cpp
/*
 * chaos_lsu_trigger.hh — LSU north-star F0-F6 trigger semantics
 * (docs/gem5-fi/lsu/05-frequency-and-sampling.md r2-r8), EVENT-normalized:
 * the denominator is the injector's eligible-event stream, NOT CPU cycles
 * (the ooo track's chaos_trigger.hh stays cycle-based — different tracks,
 * different denominators, no mixing; W2 R1 ruling 2026-09-25).
 *
 * Tiers (05 r2-r8):
 *   F0 single transient — uniform over eligible events after warm-up;
 *   F1/F2/F3 — mean interval 1,000,000 / 100,000 / 10,000 eligible events,
 *              each next interval = U[iv/2, 3*iv/2) (±50% jitter, 05 r3-r5);
 *   F4 short burst — every 100,000 eligible events fire once, then pollute
 *              2-4 consecutive eligible events (05 r6);
 *   F5 permanent — from the first eligible event after warm-up to end of run
 *              (one bit/field per run; target choice is the injector's);
 *   F6 deterministic event — inject ONCE at the first occurrence of the
 *              specified event type (05 r7; event sources per 09 §2.1 map:
 *              TlbHit[FS-only]/SqForward/DirtyEviction/CasSuccess).
 *
 * Funnel counts (04 L0): attempted (hook invocations) / eligible (passed the
 * injector's eligibility filter) / injected (fault written). The ACTIVATED
 * count (fault consumed downstream) is the L0 read-back layer's verdict —
 * deliberately NOT counted here (W3 delivers it; W2 R2 ruling). End-of-run
 * summary line: CHAOS_LSU_TRIGGER: tier= attempted= eligible= injected=.
 */
#ifndef __CPU_O3_CHAOS_LSU_TRIGGER_HH__
#define __CPU_O3_CHAOS_LSU_TRIGGER_HH__

#include <cstdint>

#include "cpu/o3/chaos_event_sample.hh"

namespace gem5
{

enum class ChaOSLsuTier : uint8_t { F0, F1, F2, F3, F4, F5, F6 };

// F6 event sources (09 §2.1 W1 map). TlbHit is FS-only — SE never calls
// TLB::lookup (arm/mmu.cc:323-365 translateSe); the enum value exists so the
// config surface is uniform, and an SE run selecting it logs zero events.
enum class ChaOSLsuEvent : uint8_t { TlbHit, SqForward, DirtyEviction,
                                     CasSuccess };

struct ChaOSLsuTrigger
{
    ChaOSTierLikeDummyRemoveMe;  // (placeholder removed in Step 1 final)
    ChaOSLsuTier tier;
    ChaOSLsuEvent f6_event = ChaOSLsuEvent::SqForward;
    uint64_t rng;
    uint64_t warmup_events = 0;   // eligible events skipped before arming
    uint64_t span_events   = 0;   // F0: uniform window size (0 = fire at warmup)

    // funnel (04 L0; activated lands in W3 — R2)
    uint64_t attempted = 0;
    uint64_t eligible  = 0;
    uint64_t injected  = 0;

  private:
    uint64_t next_fire = 0;       // eligible-count threshold (F1-F4)
    uint64_t burst_left = 0;      // F4: remaining burst shots (this shot incl.)
    bool spent  = false;          // F0/F6 fired once
    bool armed  = false;

    static constexpr uint64_t
    intervalEvents(ChaOSLsuTier t)
    {
        switch (t) {
          case ChaOSLsuTier::F1: return 1000000;
          case ChaOSLsuTier::F2: return  100000;
          case ChaOSLsuTier::F3: return   10000;
          case ChaOSLsuTier::F4: return  100000;   // burst trigger period
          default:               return       0;   // F0/F5/F6 not interval-based
        }
    }

    void
    scheduleNext(uint64_t from)
    {
        const uint64_t iv = intervalEvents(tier);
        rng = chaosSampleLCG(rng);
        next_fire = from + iv / 2 + rng % iv;      // mean ±50% (05 r3-r5)
    }

  public:
    ChaOSLsuTrigger(ChaOSLsuTier t, uint64_t seed, uint64_t warmup,
                    uint64_t span, ChaOSLsuEvent ev = ChaOSLsuEvent::SqForward)
        : tier(t), f6_event(ev), rng(seed ? seed : 1),
          warmup_events(warmup), span_events(span)
    {}

    // The injector calls this once per hook invocation (before any filter).
    void
    onAttempt()
    {
        ++attempted;
    }

    // The injector calls this when a candidate PASSED its eligibility filter
    // (target exists, window open, ...). Returns true => inject now.
    bool
    onEligible()
    {
        ++eligible;
        switch (tier) {
          case ChaOSLsuTier::F5: {
              if (!armed && eligible > warmup_events) armed = true;
              if (!armed) return false;
              ++injected;                 // every eligible event from warm-up on
              return true;
          }
          case ChaOSLsuTier::F0: {
              if (spent) return false;
              if (!armed) {
                  armed = true;
                  const uint64_t span = span_events ? span_events : 1;
                  rng = chaosSampleLCG(rng);
                  next_fire = warmup_events + rng % span;
              }
              if (eligible >= next_fire) { spent = true; ++injected; return true; }
              return false;
          }
          case ChaOSLsuTier::F1:
          case ChaOSLsuTier::F2:
          case ChaOSLsuTier::F3: {
              if (!armed) { armed = true; scheduleNext(warmup_events); }
              if (eligible < next_fire) return false;
              scheduleNext(next_fire);
              ++injected;
              return true;
          }
          case ChaOSLsuTier::F4: {
              if (burst_left) { --burst_left; ++injected; return true; }
              if (!armed) { armed = true; scheduleNext(warmup_events); }
              if (eligible < next_fire) return false;
              scheduleNext(next_fire);
              rng = chaosSampleLCG(rng);
              burst_left = 2 + rng % 3;   // 2-4 consecutive incl. this one
              --burst_left;               // this shot consumes one
              ++injected;
              return true;
          }
          case ChaOSLsuTier::F6:
              return false;               // F6 fires on the event, not here
        }
        return false;
    }

    // The F6 event source calls this when the configured event occurs.
    // Returns true => inject at this event, once ever.
    bool
    onF6Event()
    {
        if (tier != ChaOSLsuTier::F6 || spent) return false;
        spent = true;
        ++attempted; ++eligible; ++injected;
        return true;
    }

    // End-of-run summary (the injector's exit callback prints this).
    void
    summary(const char *injector) const
    {
        printf("CHAOS_LSU_TRIGGER: injector=%s tier=F%d attempted=%lu "
               "eligible=%lu injected=%lu (activated=W3-L0-layer)\n",
               injector, static_cast<int>(tier),
               (unsigned long)attempted, (unsigned long)eligible,
               (unsigned long)injected);
    }
};

} // namespace gem5

#endif // __CPU_O3_CHAOS_LSU_TRIGGER_HH__
```

（注意：上面 `ChaOSTierLikeDummyRemoveMe;` 一行是笔误占位，写入时**删除**——最终文件不得含此行。）

- [x] **Step 2: F6 事件源钩子（四处，每处一行守卫调用）**

- `CHAOS/gem5/src/cpu/o3/lsq_unit.cc:1483` 区域（FullAddrRangeCoverage 命中分支）：`CHAOSLSQFwd` 挂点旁加 `if (chaosLsuF6EventSource) chaosLsuF6EventSource(ChaOSLsuEvent::SqForward);` 形式的全局通知（具体机制：在 chaos_lsu_trigger.hh 末尾加 `inline void (*chaosLsuF6Notify)(ChaOSLsuEvent) = nullptr;` 全局函数指针，四源各一行 `if (chaosLsuF6Notify) chaosLsuF6Notify(ChaOSLsuEvent::X);`，消费者注册回调——零 SimObject 接线，单核 SE 单消费者假设如实记录于头注释）。
- `mem/cache/cache.cc:965` 区域（DirtyBit 判定真分支前）→ `DirtyEviction`
- `mem/cache/base.cc:1185` 区域（SwapReq/AMO 提交成功分支）→ `CasSuccess`
- `arch/arm/tlb.cc:158` 区域（TLB 命中）→ `TlbHit`（FS-only；SE 零调用实证，钩子存在但 SE 不达）

- [x] **Step 3: CHAOSAddrPath 消费路径**

`CHAOSAddrPath.hh`：加成员 `gem5::ChaOSLsuTrigger *lsuTrigger = nullptr;` + 模式枚举值 `LsuTier`; `CHAOSAddrPath.cc`：`maybeCorrupt` 入口 `if (lsuTrigger) { lsuTrigger->onAttempt(); ... }`——LSU 路径下 eligibility=原 inWindow 判定，注入决定=`onEligible()`（替代原 probability/max_faults 路径，仅当 `--addrpath_lsu_tier` 启用）；`startup()` 注册 F6 回调（tier==F6 时 `chaosLsuF6Notify = myCallback`）；exit 回调加 `lsuTrigger->summary("CHAOSAddrPath")`。`CHAOSAddrPath.py`：新参数 `lsuTier`（string, "off" 默认）、`warmupEvents`、`spanEvents`、`f6Event`。
**默认 off = 现有 Byte7Zero/LowBitFlip 路径逐字节不变**（零回归的结构保证）。

- [x] **Step 4: lsu_proxy.py 参数**

```python
p.add_argument("--addrpath_lsu_tier", default="off",
               choices=["off","F0","F1","F2","F3","F4","F5","F6"],
               help="W2: LSU event-normalized trigger tier on CHAOSAddrPath (05 r2-r8)")
p.add_argument("--addrpath_warmup_events", type=lambda x: int(x,0), default=0)
p.add_argument("--addrpath_span_events", type=lambda x: int(x,0), default=1000)
p.add_argument("--addrpath_f6_event", default="sq_forward",
               choices=["tlb_hit","sq_forward","dirty_eviction","cas_success"])
```
挂载块：`--addrpath_lsu_tier != "off"` 时传新参数（ChaOSLsuTrigger 由注入器内部构造）。

### Task 2: 构建与验证

- [x] **Step 5: 增量构建**：`cd CHAOS/gem5 && scons -j126 build/ARM/gem5.opt`（仅重编 lsq_unit/cache/base/tlb/CHAOSAddrPath 链，预期 <10 分钟）；零警告零错误。
- [x] **Step 6: F4 突发实证**：`build/ARM/gem5.opt --outdir=/tmp/lsu_w2_f4 configs/se/lsu_proxy.py --cmd workloads/directed/mini_check --cpu O3 --chaos_addrpath --addrpath_mode low_bit_flip --addrpath_lsu_tier F4 --addrpath_warmup_events 100 --max_faults 0`（max_faults 语义在 LSU 路径下由触发层接管，注入器侧需允许 0=unlimited 当 tier 启用）→ stdout 断言：`CHAOS_LSU_TRIGGER ... injected=N` 且注入器逐次日志中连续注入游程长度 ∈ [2,4]（grep 注入日志行人工核对 ≥3 个游程）。
- [x] **Step 7: F6 首事件单发**：`--addrpath_lsu_tier F6 --addrpath_f6_event sq_forward`（mini_check 的指针链产生 forward 机会较少——改用 reg_chain? 它无 store；用 mini_check round-trip 段）→ 断言 injected==1 且发生在首个 sq_forward 事件后；`dirty_eviction` 同理（mini_check working set 小，需 64KiB 变体 S2 或加大数组——若零事件，如实记录并换负载）。
- [x] **Step 8: F0-F3 比率 + F5**：F3（每 10K eligible 一次）在 mini_check（约 10^5 eligible 量级）上 injected≈eligible/10K±50% 量级；F5 warmup 后全 eligible 注入。逐档日志为证。
- [x] **Step 9: 零回归**：默认参数跑 reg_chain + mini_check（C4-LSU，无 LSU 触发）→ 双 golden 不变；`python3 /tmp/lsu_w0_check.py /tmp/lsu_w2_regress B0`（B0 断言仍过）。
- [x] **Step 10: 提交**：`git add` 六个显式路径（chaos_lsu_trigger.hh + CHAOSAddrPath 三件 + lsu_proxy.py + 四个 gem5 源文件）→ `feat(lsu): W2 event-normalized F0-F6 trigger layer (chaos_lsu_trigger.hh + CHAOSAddrPath consumer)` → push。

## Self-Review

- 覆盖 09 W2 三要素：F4/F6 新档（Step 1/2）✓；三计数统一输出（R2 分期：attempted/eligible/injected 现世 + activated 归 W3，头注释与 summary 行显式声明）✓；实证验证（Step 6-8）✓；F0-F3/F5 周期版零回归（R1：新文件不动旧文件 + Step 9）✓。
- 占位符：唯一占位行已在文中标注删除指令；F6 四源钩子的具体插入行号来自 W1 §2.1（执行时以现场 Read 为准——本会话三次教训：引文必须 Read 实文再 Edit）。
- 命名一致：`ChaOSLsuTier/ChaOSLsuEvent/ChaOSLsuTrigger/chaosLsuF6Notify/onAttempt/onEligible/onF6Event/summary` 全文一致；config 参数 `--addrpath_lsu_tier` 三处（py/cc/proxy）一致。
