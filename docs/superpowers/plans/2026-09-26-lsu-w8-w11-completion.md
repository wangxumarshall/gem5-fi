# LSU W8(P系/O系) + W10(campaign 完成) + W11(元分析) 收尾 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 补齐 LSU 总纲（`docs/gem5-fi/lsu/09-implementation-plan.md`）剩余可实现工作包：W8 P 系预取器注入器（总纲明确"新建预取器注入器"——当前不存在）、W8 O 系 monitor 模式、W10 campaign 引擎完成（完整模型映射/三阶段自适应/并发/回填）、W11 元分析，并以真实 trial 数据回填 07-expanded-matrix.csv。

**Architecture:** CHAOSPrefetch 四件套挂 `Stride::calculatePrefetch` 尾部（registry 指针模式，同 `BaseCache::chaosVictimHook` 先例），复用 W2 事件归一触发层（`chaos_lsu_trigger.hh`）与 L0 漏斗口径；CHAOSExMon 扩展 O01/O02 两模式挂 `handleLockedRead`；lsu_campaign.py 重写为三阶段自适应引擎 + 完整 68 模型映射表 + blocked 诚实标记；backfill 工具加 LSU 矩阵模式（11 结果列 + col26 状态机 + 守恒断言）。

**Tech Stack:** gem5 v25.1.0.1 vendored C++ (SCons), Python 3 (argparse/csv/json), tools/wilson.py。

**Spec:** `docs/gem5-fi/lsu/09-implementation-plan.md`（§3 W7/W8/W10/W11 + §1.3 口径 + §5 算力预算）；`docs/gem5-fi/lsu/05-frequency-and-sampling.md`（r12-r20 统计规则）；`docs/gem5-fi/lsu/03-design-matrix.csv`（68 模型故障定义）。

## Global Constraints（00–08 口径，逐字执行）

- **SDC 率分母 = activated**；attempted/eligible/activated 分开记录；Injected-not-activated 单列（04 L0 / 05 r12）。
- 试跑 30 activated/格；筛查 ≥385 activated；主结果 Wilson 95% 半宽 ≤2pp 或 5000 停止（05 r13-r15）。
- F1–F4 同一运行内多 activated 属同一 cluster，按运行聚类算区间（05 r19/r20）；每 cell ≥5 独立 seed 批次（05 r16）。
- 并发 gem5 进程 **≤4**（29GB 主机 OOM 纪律）；单次运行超时 = golden 10× + 绝对上限（05 r17）。
- B0 无保护的保护类行（T09/S12/C13/O08）标**不适用**，不填零（09 §6.4）。
- FS/多核依赖格标 **blocked** 而非静默跳过（README §8.3；T 系 42 格 FS-blocked、O 系 31 格多核 FS-blocked、W1/W4/W7/W11/W13 负载格同）。
- 构建纪律：增量 `-j126`，干净构建 `-j16`；**仓库根** `build/ARM/gem5.opt`；零警告。
- 每 patch：真机验证输出为证 + reg_chain golden `f247ef3fe6c02cfd` 回归 + commit + push `fi-ding`（非 main）。
- 每次注入必须有 `--<inj>_rng_seed`（注入器种子），不是通用 `--rng_seed`。

---

### Task 1: CHAOSPrefetch 四件套 + Stride 钩子（P01/P02/P03/P05/P08 原生 + P04 近似）

**Files:**
- Create: `CHAOS/gem5/src/mem/cache/prefetch/CHAOSPrefetch/CHAOSPrefetch.hh`
- Create: `CHAOS/gem5/src/mem/cache/prefetch/CHAOSPrefetch/CHAOSPrefetch.cc`
- Create: `CHAOS/gem5/src/mem/cache/prefetch/CHAOSPrefetch/CHAOSPrefetch.py`
- Create: `CHAOS/gem5/src/mem/cache/prefetch/CHAOSPrefetch/SConscript`
- Modify: `CHAOS/gem5/src/mem/cache/prefetch/stride.hh`（class Stride 加 static 成员声明）
- Modify: `CHAOS/gem5/src/mem/cache/prefetch/stride.cc`（calculatePrefetch 尾部钩子 + static 定义）
- Modify: `CHAOS/gem5/src/mem/cache/prefetch/SConscript`（若子目录需显式列入——按 CHAOSCache 在 `src/mem/cache/` 的接线方式核对）

**Interfaces:**
- Consumes: `gem5::ChaOSLsuTrigger`（`cpu/o3/chaos_lsu_trigger.hh`：`onAttempt()/onEligible()/onF6Event()/summary(name)`，tier F0-F6）。
- Consumes: `gem5::chaosLsuF6Notify`（F6 事件源函数指针，P 系 F6 格的事件入口）。
- Produces: `CHAOSPrefetch` SimObject；`Stride::chaosPrefetchHook` static 指针；方法 `void maybeCorrupt(StrideEntry *entry, std::vector<AddrPriority> &addresses, Addr pf_addr)`；stdout 行 `CHAOS_LSU_TRIGGER: injector=prefetch tier=F# attempted= eligible= injected=`（lsu_l5_classify.py:53 的正则依赖此格式）；日志 `prefetch_injections.log`（"Site: " 行——分类器 fallback 计数依赖）。
- 模式集（03 设计矩阵 P 行语义）：`p01_stride_bitflip`（训练项 stride 1-bit XOR）/ `p02_confidence_corrupt`（confidence 清零/置满，各 50%）/ `p03_addr_subst`（生成地址替换为同 4KiB 页内另一对齐行——合法换值，负对照核心）/ `p05_drop_dup`（丢弃/复制一条预取，各 50%；P04 队列 valid/指针族的诚实近似，实测备注注明）/ `p08_stride_stuck`（stride 固定 0——F5 类持续故障，每次训练后重施加）。
- 诚实边界（写入 .hh 头注释 + 回填实测备注）：P06（预取标 demand/权限赋予——无干净钩子，deferred）、P07（fill way/tag 错配→CHAOSCache tag 近似）、P09（预取致 dirty 逐出写回丢失→CHAOSCache victimFault 近似）——由 campaign 路由到 CHAOSCache，不在本注入器。

- [x] **Step 1: 读参照实现**（模式骨架复制的三个先例）
  - `CHAOS/gem5/src/mem/cache/CHAOSCache/CHAOSCache.py`（Param 声明风格 + lsuTier/lsuWarmupEvents/lsuSpanEvents 三参数——fb81ac97 刚加的）。
  - `CHAOS/gem5/src/mem/cache/base.cc:73-74`（`BaseCache::chaosVictimHook` static registry 模式）。
  - `CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.cc`（LSU 触发层消费者的接线：tier!=off 走 trigger、tier=off 走 legacy firstClock/lastClock 窗口；exit callback 打 summary）。
  - `CHAOS/gem5/src/mem/cache/prefetch/stride.cc:128-210`（calculatePrefetch 全文——确认 entry 指针在函数尾部的存活状态与 addresses 的填充点）。
  - `CHAOS/gem5/src/mem/cache/prefetch/SConscript` + `CHAOS/gem5/src/mem/cache/SConscript`（子目录如何进构建——CHAOSCache 的先例在 `src/mem/cache/CHAOSCache/SConscript`，核对父 SConscript 的列出方式）。

- [x] **Step 2: 写 CHAOSPrefetch.hh**（核心结构，复制 CHAOSAddrPath 的触发接线风格）

```cpp
// CHAOSPrefetch.hh — W8 P-series prefetcher injector (09 §3 W8).
// 模式语义按 03-design-matrix P 行；P04=队列族近似(p05_drop_dup 同族)、
// P06/P07/P09 为 cache 侧近似(CHAOSCache 路由), 不在本注入器 — 诚实边界.
#ifndef __MEM_CACHE_PREFETCH_CHAOS_CHAOSPREFETCH_HH__
#define __MEM_CACHE_PREFETCH_CHAOS_CHAOSPREFETCH_HH__

#include <random>
#include <vector>

#include "cpu/o3/chaos_lsu_trigger.hh"
#include "mem/cache/prefetch/stride.hh"
#include "params/CHAOSPrefetch.hh"
#include "sim/sim_object.hh"

namespace gem5
{

class CHAOSPrefetch : public SimObject
{
  public:
    enum class Mode { P01StrideBitflip, P02ConfidenceCorrupt, P03AddrSubst,
                      P05DropDup, P08StrideStuck };
    static Mode stringToMode(const std::string &s);

    CHAOSPrefetch(const CHAOSPrefetchParams &p);
    ~CHAOSPrefetch() override;

    // Stride::calculatePrefetch 尾部调用 (entry 可能 nullptr — 见各模式
    // 的 eligible 判定). pf_addr = 本次 demand 地址 (行对齐基准).
    void maybeCorrupt(prefetch::Stride::StrideEntry *entry,
                      std::vector<AddrPriority> &addresses, Addr pf_addr);

  protected:
    void startup() override;      // SELF-ATTACH: Stride::chaosPrefetchHook = this
    void drainResume() override;  // detach (防御性)

  private:
    Mode fi_mode;
    float probability;        // legacy 路径 (tier=off)
    Tick first_clock, last_clock;
    uint64_t max_faults;
    uint64_t rng_seed;
    uint64_t faults_injected = 0;
    std::mt19937_64 rng;
    bool tiered;              // lsuTier != "off"
    ChaOSLsuTrigger trigger;  // 事件归一触发层 (W2)
    OutputStream *log_stream = nullptr;

    bool legacyWindow();      // tier=off 的 firstClock/lastClock 判定
    void logInjection(const char *site, Addr a, const char *detail);
};

} // namespace gem5
#endif
```

- [x] **Step 3: 写 CHAOSPrefetch.cc**（语义骨架——`trigger.onAttempt()` 每次 hook、`onEligible()` 通过模式判定后调用、`injected` 计数在 trigger 内）

```cpp
// 关键路径 (完整实现照此骨架展开):
void
CHAOSPrefetch::maybeCorrupt(prefetch::Stride::StrideEntry *entry,
                            std::vector<AddrPriority> &addresses, Addr pf_addr)
{
    if (tiered) trigger.onAttempt(); else if (!legacyWindow()) return;

    // eligible = 模式目标存在:
    //   P01/P02/P08: entry != nullptr (训练表命中)
    //   P03/P05:     !addresses.empty() (本周期有生成)
    bool eligible = (fi_mode == Mode::P01StrideBitflip ||
                     fi_mode == Mode::P02ConfidenceCorrupt ||
                     fi_mode == Mode::P08StrideStuck) ? (entry != nullptr)
                                                    : !addresses.empty();
    if (!eligible) return;
    if (tiered) { if (!trigger.onEligible()) return; }
    else {
        if (max_faults && faults_injected >= max_faults) return;
        // legacy: probability 门 (rng 均匀采样, 同 CHAOSCache)
    }
    ++faults_injected;
    const Addr line = 64;  // 与 lsu_proxy L1D/L2 cacheline 对齐, 从 params 读
    switch (fi_mode) {
      case Mode::P01StrideBitflip: {
          // stride 是 int: 均匀选 bit 0..(bits(int)-1) XOR — 记录 bit 编号
          entry->stride ^= (1 << (rng() % (sizeof(int)*8)));
          logInjection("p01_stride_bitflip", pf_addr, "stride XOR 1 bit");
          break; }
      case Mode::P02ConfidenceCorrupt: {
          // 清零(false clear) / 置满(fake set) 各 50%
          if (rng() % 2) entry->confidence = SatCounter8(entry->confidence);
          // SatCounter8 无直改 — 用饱和写: 见 Step 1 的 SatCounter8 API,
          // 实现为: 清零分支 confidence.reset(); 置满分支循环 ++到饱和
          break; }
      case Mode::P03AddrSubst: {
          // 合法换值: 同 4KiB 页内另一行 (页边界内 +1/-1 行, 随机)
          Addr page = pf_addr & ~Addr(0xfff);
          Addr alt = page | ((pf_addr + line) & 0xfff);
          if (alt == addresses[0].first) alt = page | ((pf_addr - line) & 0xfff);
          addresses[rng() % addresses.size()].first = alt;
          break; }
      case Mode::P05DropDup: {
          if (rng() % 2) addresses.erase(addresses.begin() + rng() % addresses.size());
          else addresses.push_back(addresses[rng() % addresses.size()]);
          break; }
      case Mode::P08StrideStuck: {
          entry->stride = 0;   // 持续故障: 每次训练后重施加 (F5 语义)
          break; }
    }
}
// exit callback: trigger.tiered ? trigger.summary("prefetch")
//               : printf legacy 漏斗行 (同 CHAOS_LSU_TRIGGER 格式)
```

- [x] **Step 4: stride.hh/.cc 钩子**（base.cc:73-74 registry 先例）

```cpp
// stride.hh class Stride 内 (public: 供 CHAOSPrefetch startup() 赋值):
class CHAOSPrefetch;  // 文件级前向声明 (namespace gem5)
    static CHAOSPrefetch *chaosPrefetchHook;   // 单消费者 (同 chaosLsuF6Notify 注释的 SE 单核范围)

// stride.cc:
CHAOSPrefetch *Stride::chaosPrefetchHook = nullptr;
// calculatePrefetch 尾部 (函数 return 前):
if (chaosPrefetchHook)
    chaosPrefetchHook->maybeCorrupt(entry, addresses, pf_addr);
// 注意: entry 在 findVictim+insertEntry 路径后仍有效 (StrideEntry* 被表持有);
// 若某分支 entry 未定义, 传 nullptr — 实现时以 Step 1 通读的代码流为准.
```

- [x] **Step 5: CHAOSPrefetch.py + SConscript**（四件套；Param 表照抄 fb81ac97 的 CHAOSCache lsuTier 三参数 + mode/probability/firstClock/lastClock/maxFaults/rngSeed/writeLog）

- [x] **Step 6: 构建**（增量）

```bash
cd CHAOS/gem5 && scons -j126 build/ARM/gem5.opt 2>&1 | tail -5
```
预期 exit=0 零警告。失败则修到干净（CLAUDE.md：引入的警告即失败）。

- [x] **Step 7: 定向验证 — 负对照 P01–P03（README §5.4：预取错误不得改变架构结果；SDC>0 = 注入器污染 fill 路径，先回修）**

```bash
cd /home/sdc/gem5-fi-lsu
for m in p01_stride_bitflip p02_confidence_corrupt p03_addr_subst p05_drop_dup p08_stride_stuck; do
  build/ARM/gem5.opt --outdir=/tmp/pf_$m configs/se/lsu_proxy.py \
    --cmd workloads/directed/prefetch_stride --cpu O3 \
    --chaos_prefetch --prefetch_mode $m --prefetch_lsu_tier F0 \
    --prefetch_warmup_events 100 --prefetch_span_events 500 \
    --prefetch_max_faults 1 --prefetch_rng_seed 7 2>&1 | tail -3
done
```
预期（逐模式核对）：① 每模式 stdout 有 `CHAOS_LSU_TRIGGER: injector=prefetch` 行且 `injected=1`；② `prefetch_injections.log` 有 "Site: " 行；③ checksum == golden `629727c0ad9ca8ef`（P01/P02/P03 负对照 = Masked；P05/P08 允许非 SDC 结局但记录实际值）。

- [x] **Step 8: 回归**（零侵入证明：钩子 nullptr 时字节等价）

```bash
build/ARM/gem5.opt --outdir=/tmp/reg_pf configs/se/lsu_proxy.py \
  --cmd workloads/directed/reg_chain --cpu O3 2>&1 | tail -2
```
预期 checksum = `f247ef3fe6c02cfd`。

- [x] **Step 9: Commit + push**

```bash
git add CHAOS/gem5/src/mem/cache/prefetch/CHAOSPrefetch/ \
        CHAOS/gem5/src/mem/cache/prefetch/stride.hh \
        CHAOS/gem5/src/mem/cache/prefetch/stride.cc \
        CHAOS/gem5/src/mem/cache/prefetch/SConscript
git commit -m "feat(lsu): W8 P-series CHAOSPrefetch injector — 5 native modes on Stride hook (P01-P03 negative controls Masked)"
git push origin fi-ding
```

---

### Task 2: lsu_proxy 挂载 P 系参数 + atomics 探针负载（O 系验证载体）

**Files:**
- Modify: `configs/se/lsu_proxy.py`（--chaos_prefetch 参数组 + mount；--chaos_exmon 模式 choices 扩展预告位）
- Create: `workloads/src/atomics_probe.c`（若 src 目录名不同，按现有 W9 负载源码位置放置——先 `ls workloads/`）
- Create: 编译产物 `workloads/directed/atomics_probe`（host `gcc -O2 -static`）

**Interfaces:**
- Produces: `--chaos_prefetch --prefetch_mode {off,p01_stride_bitflip,p02_confidence_corrupt,p03_addr_subst,p05_drop_dup,p08_stride_stuck} --prefetch_lsu_tier {off,F0..F6} --prefetch_warmup_events --prefetch_span_events --prefetch_first_clock --prefetch_max_faults --prefetch_rng_seed`。
- Produces: atomics_probe golden（native==gem5 校验后入 lsu_campaign goldens 表——Task 4 消费）。

- [x] **Step 1: lsu_proxy.py 参数 + mount**（照 CHAOSCache mount 的 `_pre_instantiate` 钩子模式——W6 65e5d022 先例：CHAOSCache 挂 l1d-cache-0；CHAOSPrefetch 挂 L2 的 prefetcher 对象；`lsu_proxy.py` 中 L2 在 B0 挂 StridePrefetcher(degree=8)——找到该实例化点，`Stride::chaosPrefetchHook` 由 SimObject startup 自连，py 侧只需实例化 CHAOSPrefetch 一次）
  - 核对 `chaosPrefetch` 的实例化不依赖目标对象引用（registry 模式 → 无 target Param 也可；若加 `Param.StridePrefetcher target` 更明确则加）。

- [x] **Step 2: atomics_probe.c**（LDXR/STXR 定向探针——**校验和只覆盖最终数据态**，不含重试计数，使 O01/O02 的瞬时 reservation 失效表现为 Masked 而非伪 SDC）

```c
#include <stdint.h>
#include <stdio.h>
/* W8 O-series verification probe: LDXR/STXR retry loop + CAS-ish RMW.
 * CHECKSUM COVERS FINAL DATA STATE ONLY (retry counts excluded by design):
 * monitor-address (O01) / monitor-state (O02) corruption => transient
 * reservation loss => Masked, NOT fake-SDC. */
int main(void)
{
    uint64_t v = 0, data[8] = {1,2,3,4,5,6,7,8};
    uint64_t sum = 0;
    for (int i = 0; i < 300; i++) {
        uint64_t tmp; uint32_t st;
        do {
            __asm__ volatile("ldxr %0, [%1]" : "=r"(tmp) : "r"(&v));
            tmp += 1;
            __asm__ volatile("stxr %w0, %1, [%2]"
                             : "=&r"(st) : "r"(tmp), "r"(&v));
        } while (st);
        data[i % 8] += v;
    }
    for (int i = 0; i < 8; i++) sum = sum * 31 + data[i];
    sum = sum * 131 + v;
    printf("ATOMICS_PROBE v=%lu\n", v);
    printf("%016lx\n", sum);   /* 16-hex checksum 行 — 分类器正则依赖 */
    return 0;
}
```

- [x] **Step 3: 编译 + native==gem5 校验**

```bash
gcc -O2 -static -o workloads/directed/atomics_probe workloads/src/atomics_probe.c
./workloads/directed/atomics_probe   # 记 native checksum
build/ARM/gem5.opt --outdir=/tmp/ap configs/se/lsu_proxy.py \
  --cmd workloads/directed/atomics_probe --cpu O3 2>&1 | tail -2
# 两 checksum 必须一致 → 记为 golden
```

- [x] **Step 4: P 系端到端冒烟**（Task 1 Step 7 的命令改走 lsu_proxy 新参数，确认 argparse 无 exit=2——鲲鹏轨道 lsqfwd argparse 事故的同型防御）

- [x] **Step 5: 回归 + Commit + push**（同 Task 1 Step 8/9 模式；commit 信息含真实 golden 值）

---

### Task 3: CHAOSExMon O01/O02 模式 + handleLockedRead 钩子

**Files:**
- Modify: `CHAOS/gem5/src/arch/arm/CHAOSExMon/CHAOSExMon.hh`（Mode 枚举 + `maybeCorruptMonitor` 方法）
- Modify: `CHAOS/gem5/src/arch/arm/CHAOSExMon/CHAOSExMon.cc`（两模式实现 + 采样偏差防御 events_to_skip 已有——新路径复用）
- Modify: `CHAOS/gem5/src/arch/arm/CHAOSExMon/CHAOSExMon.py`（mode choices + lsuTier 参数已有——核对 48861e43 所加）
- Modify: `CHAOS/gem5/src/arch/arm/isa.cc`（handleLockedRead 尾部钩子——W1 ⑥ 落点 isa.cc:1871-1960 区）
- Modify: `configs/se/lsu_proxy.py`（exmon mode choices 加 `o01_monitor_addr_bitflip,o02_monitor_state_corrupt`）

**Interfaces:**
- Produces: `--exmon_mode {stxr_force_success,stxr_force_fail,o01_monitor_addr_bitflip,o02_monitor_state_corrupt}`；O03（状态码翻转）= 现有 stxr_force_* 语义（campaign 映射注明）；O05–O07 多核 blocked；O08 B0 N/A；O04/O09（RMW 数据通路）deferred——需 cache 侧 SwapResp 钩子，超出总纲 W8 "isa.cc handleLocked 路径" 范围，实测备注注明。
- 方法：`void maybeCorruptMonitor(const RequestPtr &req)`（handleLockedRead 尾部调用；O01 = LOCKADDR XOR 1 bit；O02 = LOCKFLAG 清零 50%/置位 50%——gem5 monitor 模型仅 flag+addr，无 version/granule，诚实边界写头注释）。

- [x] **Step 1: 读 isa.cc handleLockedRead/handleLockedWrite 现状**（W1 ⑥：1871-1960；CHAOSExMon 现挂 1953-1955——确认 handleLockedRead 的 monitor 置位点与 misc reg 写法）
- [x] **Step 2: 实现两模式**（结构照 stxr_force_* 的 maybeCorrupt：inWindow + max_faults + events_to_skip 几何采样防御 + logInjection "Site: " 行）
- [x] **Step 3: isa.cc 钩子**（handleLockedRead 置 monitor 后：`if (chaosExMon) chaosExMon->maybeCorruptMonitor(req);`——注入器判模式，非 O01/O02 模式直接 return）
- [x] **Step 4: 构建**（同 Task 1 Step 6；零警告）
- [x] **Step 5: 定向验证**（atomics_probe 载体）

```bash
for m in o01_monitor_addr_bitflip o02_monitor_state_corrupt; do
  build/ARM/gem5.opt --outdir=/tmp/em_$m configs/se/lsu_proxy.py \
    --cmd workloads/directed/atomics_probe --cpu O3 \
    --chaos_exmon --exmon_mode $m --exmon_first_clock 1000 \
    --exmon_max_faults 1 --exmon_rng_seed 11 2>&1 | tail -3
done
```
预期：① `exmon_injections.log` 各 ≥1 行；② O01/O02 结局 = Masked（瞬时 reservation 失效被重试环吸收——探针设计使然）或 livelock→超时；**不得 SDC**（monitor 故障不写数据）。若 SDC 出现先回修（可能误触 store 数据路径）。
- [x] **Step 6: 回归 reg_chain + mini_check golden + Commit + push**

---

### Task 4: campaign 完整 68 模型映射表 + blocked 诚实标记

**Files:**
- Modify: `tools/lsu_campaign.py`（MODEL_FLAGS 表替换现有 mode_map/pre_map 片段；wl_map 补 `sqlite_like`；BLOCKED 表）

**Interfaces:**
- Produces: `MODEL_FLAGS: dict[str, list[str] | None]`（68 模型 → gem5 旗标组或 None+原因）；`resolve_cell(cell) -> (flags, blocked_reason)`；blocked 原因枚举 `fs-infra`（T 系/W1/W4 负载）、`multicore-fs`（O05-O07/W7/W13）、`spec-license`（W11）、`b0-na`（S12/T09/C13/O08 保护行）、`deferred`（A07 R4、O04/O09、P06）。
- 映射数据源（实现时逐条核对，不许臆造）：`git show 9fbec314`（A 系双钩 7 模式）、`git show c7743989..c8d6fa6b`（W5/W6 各 commit 的 argparse choices 增量）、`lsu_proxy.py:413-484` choices 现值。

- [x] **Step 1: 提取 W5/W6 diff 中的模式名**（`git show c7743989 25d3b37b cdee55f4 7af6eed4 1beea50d d8051157 754b048e a0ecfd20 2b967a9b fcb919f8 067c31c7 c8d6fa6b -- '*lsu_proxy.py' '*CHAOSLSQFwd*' '*CHAOSCache*'`），与下表骨架合并：

```python
# 骨架 — 每行实现时以 diff + lsu_proxy choices 为准, 标 ※ 的需 Step 3 真机复核
MODEL_FLAGS = {
    # AGU (W4 9fbec314): 位族走 addrpath_mode, PRE 族走 agu_pre_mode
    "A01": ["--chaos_addrpath", "--addrpath_mode", "a01_bit"],
    "A02": ["--chaos_addrpath", "--addrpath_mode", "a02_2bit"],
    "A03": ["--chaos_addrpath", "--addrpath_mode", "a03_stuck0"],   # ※ stuck1 由 seed 奇偶交替
    "A04": ["--chaos_addrpath", "--agu_pre_mode", "a04_subst"],
    "A05": ["--chaos_addrpath", "--agu_pre_mode", "a05_shift"],
    "A06": ["--chaos_addrpath", "--agu_pre_mode", "a06_size"],     # ※ --agu_size_to
    "A07": None,   # deferred R4 (W4 诚实近似记录)
    "A08": ["--chaos_addrpath", "--agu_pre_mode", "a08_subst"],
    # SQ (W5): data 族走 lsqfwd structMode, addr/状态族走 PRE hook
    "S01": ["--chaos_lsqfwd", "--lsq_struct_mode", "byte_flip"],
    "S02": ["--chaos_lsqfwd", "--lsq_struct_mode", "byte_flip", "--bits_to_change", "2"],  # ※
    "S03": ["--chaos_lsqfwd", "--lsq_struct_mode", "byte_lane_skew"],  # ※ stuck 族
    "S04": ["--chaos_addrpath", "--agu_pre_mode", "s04_store_subst"],
    "S05": ["--chaos_addrpath", "--agu_pre_mode", "s05_store_size"],
    "S06": ["--chaos_addrpath", "--agu_pre_mode", "s06_store_state"],
    "S07": ["--chaos_addrpath", "--agu_pre_mode", "s07_store_ptr"],
    "S08": ["--chaos_lsqfwd", "--lsq_struct_mode", "fwd_source_sub"],
    "S09": ["--chaos_lsqfwd", "--lsq_struct_mode", "phase_offset"],  # ※ 拼接族=byte_lane_skew? 以 W5 diff 定
    "S10": None,  # ※ StoreSet (7af6eed4) — 落点 store_set.cc, 调用旗标以 diff 定
    "S11": ["--chaos_addrpath", "--agu_pre_mode", "s11_store_lost"],
    "S12": None,   # b0-na: B0 无保护 (09 §6.4)
    "S13": ["--chaos_addrpath", "--agu_pre_mode", "s13_store_addr"],
    # LQ (W5)
    "L01": ["--chaos_addrpath", "--agu_pre_mode", "l01_load_addr"],
    "L02": ["--chaos_addrpath", "--agu_pre_mode", "l02_load_state"],
    "L03": ["--chaos_lsqfwd", "--lsqfwd_l03"],                      # ※ d8051157
    "L04": ["--chaos_lsqfwd", "--lsq_struct_mode", "stale_line_replay"],  # ※ a0ecfd20 recvTimingResp F6 钩子 — 以 diff 定
    # Cache (W6): CHAOSCache targetField × faultType + 事件钩子族
    "C01": ["--chaos_l1d", "--l1d_target_field", "data", "--l1d_fault_type", "bit_flip"],
    "C02": ["--chaos_l1d", "--l1d_target_field", "data", "--l1d_fault_type", "bit_flip", "--l1d_bits", "2"],  # ※ 位数字段名以 CHAOSCache.py 定
    "C03": ["--chaos_l1d", "--l1d_target_field", "data", "--l1d_fault_type", "stuck_at_zero"],
    "C04": ["--chaos_l1d", "--l1d_target_field", "tag", "--l1d_fault_type", "bit_flip"],
    "C05": ["--chaos_l1d", "--l1d_target_field", "tag", "--l1d_fault_type", "bit_flip"],   # 近似=C04 重标记, 实测备注注明
    "C06": ["--chaos_l1d", "--l1d_target_field", "valid"],
    "C07": ["--chaos_l1d", "--l1d_target_field", "dirty"],
    "C08": ["--chaos_l1d", "--l1d_target_field", "coh"],
    "C09": ["--chaos_l1d", "--l1d_target_field", "data_shift"],
    "C10": ["--chaos_l1d", "--l1d_target_field", "valid"],   # 近似=PLRU→valid 失效, 备注注明
    "C11": None,  # ※ allocateTarget 事件钩子 (fcb919f8) — 启用旗标以 diff 定
    "C12": None,  # ※ handleFill 时序 (067c31c7) — 同上
    "C13": None,   # b0-na: B0 无保护
    "C14": None,  # ※ deallocate MSHR-busy (067c31c7)
    "C15": None,  # ※ mshr_queue free 事件 (c8d6fa6b)
    # Prefetcher (Task 1 新建)
    "P01": ["--chaos_prefetch", "--prefetch_mode", "p01_stride_bitflip"],
    "P02": ["--chaos_prefetch", "--prefetch_mode", "p02_confidence_corrupt"],
    "P03": ["--chaos_prefetch", "--prefetch_mode", "p03_addr_subst"],
    "P04": ["--chaos_prefetch", "--prefetch_mode", "p05_drop_dup"],   # 近似: 队列族, 备注注明
    "P05": ["--chaos_prefetch", "--prefetch_mode", "p05_drop_dup"],
    "P06": None,   # deferred: 无干净钩子 (demand 标记/权限赋予)
    "P07": ["--chaos_l1d", "--l1d_target_field", "tag", "--l1d_fault_type", "bit_flip"],  # 近似: fill way/tag 错配→tag
    "P08": ["--chaos_prefetch", "--prefetch_mode", "p08_stride_stuck"],
    "P09": ["--chaos_l1d", "--l1d_target_field", "dirty"],  # 近似: 预取致 dirty 逐出写回→dirty 面
    # Atomic (Task 3 + 现有)
    "O01": ["--chaos_exmon", "--exmon_mode", "o01_monitor_addr_bitflip"],
    "O02": ["--chaos_exmon", "--exmon_mode", "o02_monitor_state_corrupt"],
    "O03": ["--chaos_exmon", "--exmon_mode", "stxr_force_fail"],   # 状态码翻转=现有模式语义
    "O04": None, "O09": None,   # deferred: RMW 数据通路需 cache 侧 SwapResp 钩子
    "O05": None, "O06": None, "O07": None,  # multicore-fs
    "O08": None,                 # b0-na
    # TLB: 全部 fs-infra (SE 走 translateSe, TLB::lookup 零调用, W1 ③)
    **{f"T{i:02d}": None for i in range(1, 11)},
}
```

- [x] **Step 2: 频率/触发参数生成**——`resolve_cell` 按单元格 F 档生成触发旗标：A 系→`--addrpath_lsu_tier F# --addrpath_warmup_events 0 --addrpath_span_events 1000`；S/L 系→`--lsqfwd_lsu_tier`；C 系→`--l1d_lsu_tier`（若 F 档在 C 系走 legacy firstClock——以 0f967a10 C 系路由 commit 为准）；P 系→`--prefetch_lsu_tier`；O 系→exmon lsuTier。F5/F6 语义由触发层内部实现（chaos_lsu_trigger.hh），campaign 只传档位。
- [x] **Step 3: 真机复核每个映射族**（每族 ≥1 次真实运行断言 `faults_injected ≥ 1`；injected=0 的映射 = 错误映射，修到对——A01/S01/S13/L01/C01/C04/C07 七格已有 trial 数据可直接引用 84c863d5）

```bash
python3 tools/lsu_campaign.py --matrix docs/gem5-fi/lsu/07-expanded-matrix.csv \
  --outdir /tmp/mapcheck --phase trial --n-seeds 1 \
  --cells A01-F0-W3,S02-F0-W5,S08-F0-W5,S10-F0-W5,L03-F0-W5,L04-F6-W5,C11-F0-W6,C12-F0-W6,C14-F0-W6,C15-F0-W6,P01-F0-W8,P05-F0-W8
# 逐格核对 summary.json: total_injected ≥ 1
```

- [x] **Step 4: blocked 完备性断言**（`--dry-run` 全 337 格 → 每格要么 flags 要么 blocked 原因；脚本内断言零 "not mapped" 残留）：

```bash
python3 tools/lsu_campaign.py --matrix docs/gem5-fi/lsu/07-expanded-matrix.csv --dry-run 2>&1 | tail -5
# 预期: runnable=约183 blocked=约136 na=9 deferred=9 (以实际矩阵分布为准, 打印分原因计数)
```

- [x] **Step 5: Commit + push**（`feat(lsu): W10 campaign complete 68-model mapping + honest blocked classification`）

---

### Task 5: 三阶段自适应采样引擎 + 并发槽位 + 超时 + seed 批次/聚类

**Files:**
- Modify: `tools/lsu_campaign.py`（phase 循环重写；`--max-parallel` 真实生效；进程池）

**Interfaces:**
- Consumes: `tools/wilson.py` 的 `wilson_ci(k, n)`（返回 (lo, hi) 或同构——实现时读 wilson.py:34 签名适配）。
- Produces: 每格 `runs/lsu/<RunID>/cell_results.json`：

```json
{"runid": "A01-F0-W3", "phase": "screening", "seed_batches": 5,
 "clustered": false, "n_runs": 25, "attempted": 250, "eligible": 210,
 "activated": 24, "classes": {"Masked": 24, "Detected/Contained": 0,
 "SDC": 0, "Crash": 0, "Timeout": 0}, "sdc_rate": 0.0,
 "activation_rate": 0.096, "wilson": {"lo": 0.0, "hi": 0.14},
 "stop_reason": "screening-target-met", "conservation": "OK",
 "runs": [{"seed": 1, "cluster_id": "A01-F0-W3#1", "activated": 5, "outcome": "Masked"}]}
```

- [x] **Step 1: 三阶段循环**（05 r13-r15 逐字实现）

```python
def run_cell_adaptive(cell, outdir, args, golden_runtime_s):
    activated, classes = 0, {"Masked":0,"Detected/Contained":0,"SDC":0,"Crash":0,"Timeout":0}
    runs, seed = [], 0
    target = {"trial": 30, "screening": 385, "main": 5000}[args.phase]
    while (activated < target
           and seed < args.max_seeds_per_cell
           and not (args.phase == "main" and wilson_halfwidth(classes, activated) <= 0.02)):
        seed += 1
        r = run_single_cell(cell, args, seed, outdir / f"seed{seed}")
        runs.append(r)
        activated += r["activated"]
        classes[r["outcome"]] += r["activated"]
        # F1-F4: 单运行多 activated = 同 cluster — run 记录带 cluster_id=f"{runid}#{seed}",
        # 区间计算按运行聚类 (05 r19/r20): 见 Step 3
    ...
```

- [x] **Step 2: 并发槽位 ≤4 + 超时**——`subprocess.Popen` + 槽位信号量（`threading.Semaphore(4)` + ThreadPoolExecutor(max_workers=4)）；超时 = `max(10 × golden_runtime_s, 300)` 秒（05 r17；golden_runtime 由首次 no-inject 运行实测，缓存到 `runs/lsu/.golden_runtime.json`）。
- [x] **Step 3: 聚类区间**（F1–F4 格）：SDC 率 = SDC_runs/total_runs（按运行聚类）；F0/F5/F6 = SDC_activated/activated。Wilson 用 `tools/wilson.py`。
- [x] **Step 4: seed 批次 ≥5 + CRN**——每格 seed 集 = `{batch*1000 + k}`（batch=1..5）；同 workload 的格共享 seed 基（CRN，05 r16）。
- [x] **Step 5: 玩具网格端到端验证**（总纲 W10 验收原文："试跑→筛查→停止规则触发→回填"全链）：

```bash
python3 tools/lsu_campaign.py --matrix docs/gem5-fi/lsu/07-expanded-matrix.csv \
  --outdir /tmp/toygrid --phase trial --trial-target 5 --max-seeds-per-cell 3 \
  --cells S01-F0-W5,S13-F0-W5,C01-F0-W6,P01-F0-W8
# 断言: 每格 cell_results.json 存在、conservation=OK、stop_reason 非空
# 筛查档同理用 --screening-target 10 缩小跑一遍; main 档用 --wilson-stop-hw 0.30 触发停止规则
```

- [x] **Step 6: 回归 + Commit + push**

---

### Task 6: 回填工具 LSU 扩展（11 结果列 + col26 状态机 + 守恒断言）

**Files:**
- Modify: `tools/backfill_expanded_matrix.py`（加 LSU 矩阵模式：按表头自动识别 `07-expanded-matrix.csv` vs ooo `05-expanded-matrix.csv`）

**Interfaces:**
- Produces: `--matrix docs/gem5-fi/lsu/07-expanded-matrix.csv --campaign runs/lsu [--dry-run]` → 写回 col17–27（Seed/注入索引、Attempted、Activated、Masked、Detected/Contained、SDC、Crash、Timeout、SDC率(activated)、激活率、记录状态）+ col27 实测备注（近似/deferred 原因落此列）；col26 状态机 `待执行 → 试跑 → 已筛查 → 主结果`，blocked 格写 `blocked(fs-infra)` 等带原因值（**不伪造完成**——M5 里程碑口径）。
- 守恒断言：逐格 `Activated == Masked+Detected+SDC+Crash+Timeout`（04 L5），违例格拒写并报错。

- [x] **Step 1: 读现有工具结构**（853 行 ooo 版：`--matrix`/`--campaign`/`--dry-run` 参数与 CSV 读写骨架保留，新增 LSU 列布局分支——ooo 是 7 列、LSU 是 11 列+状态机）。
- [x] **Step 2: LSU 分支实现**（读 `runs/lsu/*/cell_results.json` 按 RunID 聚合 → 算 SDC率=SDC/activated、激活率=activated/attempted → 状态机按 phase 字段映射 trial→试跑/screening→已筛查/main→主结果）。
- [x] **Step 3: 玩具回填验证**（Task 5 产物回填到矩阵 **scratch 副本**——07-expanded-matrix.csv 是源表忠实提取，回填产物写到 `runs/lsu/07-expanded-matrix-backfilled.csv`，不覆盖源文件；`extract.py`/`verify_extraction.py` 的源表完整性不受影响）：

```bash
python3 tools/backfill_expanded_matrix.py --matrix docs/gem5-fi/lsu/07-expanded-matrix.csv \
  --campaign /tmp/toygrid --out /tmp/toygrid/backfilled.csv
python3 - <<'EOF'
import csv
rows = list(csv.reader(open('/tmp/toygrid/backfilled.csv', encoding='utf-8')))
done = [r for r in rows[1:] if r[26] not in ('待执行',)]
assert done, "no cells backfilled"
for r in done:
    a = int(r[18] or 0); s = sum(int(r[c] or 0) for c in (19,20,21,22,23))
    assert a == s, f"conservation violated at {r[1]}: {a} != {s}"
print(f"BACKFILL CHECK PASSED: {len(done)} cells, conservation OK")
EOF
```

- [x] **Step 4: Commit + push**

---

### Task 7: SE 可测格 trial 阶段实跑 + 回填落盘

**Files:**
- Create: `runs/lsu/`（campaign 产物——按仓库纪律 runs/ 不入 git，summary JSON 入 `artifacts/lsu-trial/`）
- Create: `docs/gem5-fi/lsu/10-trial-results.md`（trial 阶段结果记录 + 诚实边界）

- [x] **Step 1: 全 SE 格 trial**（约 183 可跑格 × seed 批次 1（trial 首批；30-activated 目标受 max_seeds 限制时如实记录 stop_reason=seed-cap）：

```bash
python3 tools/lsu_campaign.py --matrix docs/gem5-fi/lsu/07-expanded-matrix.csv \
  --outdir runs/lsu --phase trial --max-seeds-per-cell 5 --max-parallel 4 \
  2>&1 | tee /tmp/lsu_trial.log | tail -20
```
（预计 183 格 × 5 seeds × ~20s ÷ 4 并行 ≈ 1.5–2h——后台 `run_in_background` 跑，期间做 Task 8 的工具准备；OOM 纪律：并发 ≤4 硬顶。）
- [x] **Step 2: 回填**（Task 6 工具，产物 `runs/lsu/07-expanded-matrix-backfilled.csv`，col26=试跑/blocked 按原因）。
- [x] **Step 3: 诚实性抽查**——分族抽 8 格（A/S/L/C/P 各 ≥1）人工核对：cell_results.json 的 classes 与 backfilled CSV 数字一致；全 Crash/零激活格按 05 r13 记 injector-suspect 标注（trial 阶段职责就是发现这类）。
- [x] **Step 4: 10-trial-results.md 撰写**（每单元族汇总表 + 异常格清单 + 「trial 只用于发现注入器错误/全 Crash/零激活，不用于最终窄置信区间」口径声明）。
- [x] **Step 5: Commit + push**（artifacts + 文档；**不 commit runs/ 与 m5out**——显式路径纪律）。

---

### Task 8: W11 元分析报告（trial 数据 + 337 完整性审计 + 边界声明）

**Files:**
- Modify: `tools/lsu_meta_analysis.py`（若 trial 数据暴露缺口：配对对照 S01 vs S04（bitflip vs 合法换值）、F6 vs F1/F2 同模型行配对——读 backfilled CSV 支持这两组配对输出）
- Create: `docs/gem5-fi/lsu/11-meta-analysis.md`（最终报告）

- [x] **Step 1: 跑元分析**：

```bash
python3 tools/lsu_meta_analysis.py --matrix runs/lsu/07-expanded-matrix-backfilled.csv \
  --output docs/gem5-fi/lsu/11-meta-analysis.md
```
- [x] **Step 2: 337×11 完整性审计断言**（报告内嵌审计表：每格状态 ∈ {试跑,已筛查,主结果,blocked(原因),不适用,deferred,待执行}；非 blocked 格无空值；守恒逐格闭合；CI 齐——trial 阶段 CI 半宽必然 >2pp，如实呈现不粉饰）。
- [x] **Step 3: 三问回答（trial 级，预注册边界）**——Q1 位置×SDC 潜力（trial 数据排序 + 文献锚点对照：TC'23 SDC=0 复现格）；Q2 前兆（L0 漏斗 attempted/eligible/activated 差异最大的格）；Q3 结构化 vs 随机（S01 vs S04、S13 vs S04 配对差——trial 级若有数据先出方向，无数据标待筛查）。**每条结论带 RunID + n + Wilson CI 或明确标注 trial 级局限**。
- [x] **Step 4: 边界声明**（B0 实验模型非 920 复刻；SE 233 格 trial 级 vs FS/多核 104 格 blocked 明细；O04/O09/P06 deferred 明细；下一步 = 筛查档 ≥385 activated/cell）。
- [x] **Step 5: Commit + push**（`feat(lsu): W11 meta-analysis — trial-level three-question report + 337-cell audit`）。

---

## Self-Review 记录

- **Spec 覆盖**：总纲 W8 P 系"新建预取器注入器"→Task 1；W8 O 系 handleLocked 扩展→Task 3；W10 三阶段/聚类/CRN/回填/玩具验证→Task 4-6；W11→Task 8；W9 余 5 负载 + W7 T05-T08 = FS/多核/SPEC 结构性阻塞→blocked 标记（Task 4）+ 边界声明（Task 8），**不写不可验证的 C++ 死代码**（FS 子模块空——CLAUDE.md 自验证纪律禁止提交无法真机验证的行为声明）。
- **占位符扫描**：无 TBD；映射表中 ※ 标记 = 实现时以 W5/W6 git diff 为唯一事实源并经 Step 3 真机复核——这是数据提取动作不是占位。
- **类型一致性**：CHAOS_LSU_TRIGGER stdout 行格式与 lsu_l5_classify.py:53 正则一致；prefetch_injections.log "Site: " 行与分类器 fallback 一致；cell_results.json 字段与 backfill/meta-analysis 消费一致。
