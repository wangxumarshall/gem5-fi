# OoO W0 平台与机制底座 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立 OoO 故障注入轨道的平台底座：C3-OOO 配置族（ROB128/PRF int128-fp192-vec48/2.6GHz）、F0–F5 统一触发语义助手、事件密度基线工具（probe + 聚合器）。

**Architecture:** 纯增量扩展——新建 `configs/se/ooo_proxy.py`（以 kp920_proxy.py 为模板）+ runner/schema/validator 三处加 `"C3"`；新建 header-only `chaos_trigger.hh`（仿 chaos_event_sample.hh 先例，无 SConscript）+ 独立 g++ 单测；新建 CHAOSProbe SimObject（仿 CHAOSFreeList 四件套，self-attach）+ `tools/event_density.py` 聚合器。不触碰 C0/C2 行为。

**Tech Stack:** gem5 v25.1 stdlib python config / C++ SimObject / python3 tools（stdlib-only）。

**Spec:** `docs/gem5-fi/ooo/06-implementation-plan.md` §4 W0 + `docs/gem5-fi/ooo/00-05`（北极星；冲突以 00-05 为准）。W0.3 在本计划中细化为 3a(probe)+3b(聚合器) 两 patch——原因：gem5 stats 无「ROB/IQ 占用超阈值周期数」与「freelist 低水位」事件计数，06 文档预见的「若 stats 不足则 CHAOSProbe」条件成立。

## Global Constraints

- 分支 `fi-ding`；只 push 非 main；commit message **不得**以 `Co-Authored-By: Claude` 结尾（CLAUDE.md 覆盖默认行为）。
- **one-patch-per-unit**：Task N = 一个 commit；顺序执行，前一 Task 验证+commit 后才开下一 Task。
- 每 patch 验证三件套（真机输出为证，引用进 commit message）：构建零警告（涉及 C++ 时）/ 定向功能验证 / 回归。
- 回归 golden：`workloads/directed/reg_chain` 无注入输出 checksum `f247ef3fe6f02cfd`（runner.py GOLDEN_IDS）。
- gem5.opt 路径 = 仓库根 `build/ARM/gem5.opt`（runner.py:35；`CHAOS/gem5/build/ARM` 是 stale 副本——buildpath 陷阱见 memory）。增量构建 `-j126` 可用；**clean 构建必须 `-j16`**（OOM 教训）。配置类 python 改动不需要重建 gem5.opt。
- 不修改 C0/C2 任何默认行为（本计划全部为新增文件 + 三处纯增量枚举/字典条目）。
- W0.1/W0.3b 是纯 python（不重建）；W0.2 是 header-only（首次 gem5 编译发生在 W4.1，本 Task 用 `-Wall -Wextra -Werror` 独立 g++ 验证）；W0.3a 需要**真实增量构建**。
- Spike 结论已入档（findings.md，本目录）：ROB done 位=CanCommit @ commit.cc:1353（现有 rob.cc:254 hook 在提交后，对 done 注入无效）；FreeList=std::queue 无头尾指针；D55 路由仅时序效应。这些影响 W4/W5 计划，不影响 W0。

---

### Task 1: W0.1 — C3-OOO 配置族

**Files:**
- Create: `configs/se/ooo_proxy.py`（以 `configs/se/kp920_proxy.py` 为模板）
- Modify: `tools/runner.py:43-52`（CONFIG_FAMILY 加 C3）
- Modify: `schemas/manifest.schema.json`（config_family enum 加 "C3"）
- Modify: `tools/manifest_validate.py:36`（CONFIG_FAMILIES 加 "C3"）

**Interfaces:**
- Produces: config family `"C3"`（runner `--config C3` / manifest `platform.config_family: "C3"`）；O3 参数 ROB=128 / numPhysIntRegs=128 / numPhysFloatRegs=192 / **numPhysVecRegs=48** / 2.6GHz；16 个注入器挂载块与 C2 完全同面（arg surface 不变）。
- 后续 Task 依赖：Task 3 在 `ooo_proxy.py` 追加 `--chaos_probe` 挂载块；W1 负载、W4-W7 注入器全部经 C3 运行。

- [x] **Step 1: 创建配置文件**

```bash
cp configs/se/kp920_proxy.py configs/se/ooo_proxy.py
```

对副本做以下精确编辑（其余 589 行原样保留）：

1a. 头部注释块（1-32 行）替换为：

```python
# ooo_proxy.py — C3-OOO SE config (docs/gem5-fi/ooo north-star platform).
#
# Mirrors configs/se/kp920_proxy.py (stdlib SimpleBoard + classic L1/L2 +
# SimpleProcessor + the 16 CHAOS injector mount blocks) BUT sets the OoO
# fault-injection north-star platform parameters
# (docs/gem5-fi/ooo/00-overview.md 平台假设 + README §7):
#   width=4 all stages, ROB=128, PRF int128/fp192/vec48, 2.6GHz.
#
# HONEST NOTES (north-star 边界⑤: params are A72-public + gem5-example
# estimates, NOT Kunpeng 920 silicon values):
#   1. IQ: gem5 v25 unified IQ (instQueues=vector<IQUnit>); the default
#      IQUnit is numEntries=64 — matches north-star IQ=64. Int/FP split-IQ
#      (Neoverse V2 style, configs/common/cores/arm/neoverse_v2.py:120-198)
#      deferred pending the FUPool spike follow-up.
#   2. LQ/SQ: north star is silent on LSQ sizes -> gem5 defaults, no knobs.
#   3. SVE predicate pool (numPhysVecPredRegs) reserved for the C3-SVE
#      variant (north-star D78-D82, deferred; 920 has no SVE).
#   4. Default ArmO3CPU FUPool (IntALU×6/IntMultDiv×2/FP_ALU×4/FP_MultDiv×2)
#      — custom port map is separate work.
#
# USAGE (identical injector arg surface to arm_chaos.py / kp920_proxy.py):
#   gem5.opt --outdir=<dir> configs/se/ooo_proxy.py --cmd=<bin> --cpu O3 \
#       [--chaos_phys --phys_mode arch_frontend ...] \
#       [--rob 128 --phys_int 128 --phys_float 192 --phys_vec 48]
```

1b. `V110 = {...}` 字典（53-62 行）替换为：

```python
OOO = {
    "fetch_width": 4, "decode_width": 4, "rename_width": 4,
    "issue_width": 4, "dispatch_width": 4, "commit_width": 4,
    "rob": 128,            # 北极星边界⑤（A72+gem5 示例估计，非 920 真值）
    "phys_int": 128,       # docs/gem5-fi/ooo README §7
    "phys_float": 192,
    "phys_vec": 48,        # numPhysVecRegs（gem5 默认 256；北极星向量 PRF）
    "clk": "2.6GHz",       # 北极星 00-overview（公开资料折算）
}
```

1c. sweep 参数块：`--rob/--phys_int/--phys_float` 的 default 从 `V110[...]` 改为 `OOO[...]`；**删除** `--lq/--sq` 两个参数（北极星未规定 LSQ）；新增：

```python
p.add_argument("--phys_vec", type=int, default=OOO["phys_vec"],
               help=f"numPhysVecRegs (north star vec48={OOO['phys_vec']})")
```

1d. 应用块（274-289 行）替换为：

```python
if args.cpu == "O3":
    cpu0.fetchWidth = OOO["fetch_width"]
    cpu0.decodeWidth = OOO["decode_width"]
    cpu0.renameWidth = OOO["rename_width"]
    cpu0.issueWidth = OOO["issue_width"]
    cpu0.dispatchWidth = OOO["dispatch_width"]
    cpu0.commitWidth = OOO["commit_width"]
    cpu0.numROBEntries = args.rob
    cpu0.numPhysIntRegs = args.phys_int
    cpu0.numPhysFloatRegs = args.phys_float
    cpu0.numPhysVecRegs = args.phys_vec
    print(f"[ooo_proxy] C3-OOO params applied: width=4-wide, ROB={args.rob}, "
          f"physInt={args.phys_int}, physFloat={args.phys_float}, "
          f"physVec={args.phys_vec} (IQ=64 unified default; LQ/SQ=gem5 "
          f"default, north star silent; 2.6GHz)")
```

（删除 `cpu0.LQEntries/SQEntries` 两行。）CHAOSMem 比率块中的 `V110["clk"]` 全部改 `OOO["clk"]`（2.6GHz → ratio 385 不变），`[kp920_proxy]` 打印标签改 `[ooo_proxy]`。

- [x] **Step 2: runner 加 C3 路由**

`tools/runner.py:43-52` CONFIG_FAMILY 字典追加一行（C2 行之后）：

```python
    # OoO north-star platform (docs/gem5-fi/ooo): vec48 PRF, ROB128, 2.6GHz
    "C3": os.path.join(REPO, "configs/se/ooo_proxy.py"),
```

- [x] **Step 3: schema 枚举加 C3**

`schemas/manifest.schema.json` config_family enum（约 73-81 行）在 `"C2-FS"` 后加 `,\n            "C3"`。

- [x] **Step 4: validator 加 C3**

`tools/manifest_validate.py:36`：

```python
CONFIG_FAMILIES = ("C0", "C1", "C2", "C0-CACHE", "C0-FS", "C2-FS", "C3")
```

- [x] **Step 5: 语法与校验器自检**

```bash
python3 -m py_compile configs/se/ooo_proxy.py tools/runner.py tools/manifest_validate.py && echo SYNTAX-OK
python3 -m tools.manifest_validate
```
Expected: `SYNTAX-OK`；validator 自检通过（既有行为，schema 编辑后惯例回跑）。

- [x] **Step 6: 定向功能验证（C3 跑通 reg_chain golden）**

```bash
build/ARM/gem5.opt --outdir=/tmp/ooo_w01_c3 configs/se/ooo_proxy.py \
    --cmd workloads/directed/reg_chain --cpu O3 > /tmp/ooo_w01_c3.out 2>&1
grep -c "f247ef3fe6f02cfd" /tmp/ooo_w01_c3.out
```
Expected: `1`（FINAL checksum 命中 golden）；进程 exit 0；stdout 出现 `[ooo_proxy] C3-OOO params applied: ... physVec=48`。（~2 min）

- [x] **Step 7: 参数真实生效证明（config.ini）**

```bash
grep -E "^ *num(PhysVecRegs|PhysIntRegs|PhysFloatRegs|ROBEntries)=" /tmp/ooo_w01_c3/config.ini
```
Expected: `numPhysVecRegs=48` / `numPhysIntRegs=128` / `numPhysFloatRegs=192` / `numROBEntries=128`（config.ini 是 gem5 instantiate 时写出的最终解析参数——比 print 更强的证据）。

- [x] **Step 8: 回归（未受影响路径 C0）**

```bash
build/ARM/gem5.opt --outdir=/tmp/ooo_w01_c0 configs/se/arm_chaos.py \
    --cmd workloads/directed/reg_chain --cpu O3 > /tmp/ooo_w01_c0.out 2>&1
grep -c "f247ef3fe6f02cfd" /tmp/ooo_w01_c0.out
```
Expected: `1`（C0 不受影响）。

- [x] **Step 9: manifest C3 路由冒烟**

写 `/tmp/ooo_c3_manifest.yaml`（platform: {isa: arm64, mode: SE, cpu_model: O3, config_family: C3} + 必需字段，参照 `manifests/p1-gpr-regchain-000384.yaml` 结构），运行 `python3 tools/manifest_validate.py /tmp/ooo_c3_manifest.yaml`。Expected: exit 0，无 config_family 枚举错误。

- [ ] **Step 10: Commit + push**

```bash
git add configs/se/ooo_proxy.py tools/runner.py schemas/manifest.schema.json tools/manifest_validate.py
git commit -m "feat(ooo): W0.1 C3-OOO config family (ROB128/PRF int128-fp192-vec48/2.6GHz)

- configs/se/ooo_proxy.py 基于 kp920_proxy.py，北极星平台参数（06 §4 W0.1）
- runner CONFIG_FAMILY/schema/validator 三处加 C3（纯增量，C0/C2 不变）
- 验证：<引用 Step 6-9 实际输出——golden 命中×2、config.ini numPhysVecRegs=48、validator exit 0>"
git push origin fi-ding
```

---

### Task 2: W0.2 — chaos_trigger.hh 统一触发语义（F0–F5）

**Files:**
- Create: `CHAOS/gem5/src/cpu/o3/chaos_trigger.hh`（header-only，无需 SConscript——chaos_event_sample.hh 先例：cpu/o3 在所有 o3 源与 CHAOS 注入器子目录的 CPPPATH 上）
- Test: `tests/chaos_trigger_test.cc`（独立 g++ 编译，不进 gem5 构建）

**Interfaces:**
- Consumes: `chaosSampleLCG`（`cpu/o3/chaos_event_sample.hh:48`）。
- Produces（W4.1 起的注入器接线用）：`gem5::ChaOSTier{F0,F1,F2,F3,F5}` + `gem5::ChaOSTrigger`：
  `ChaOSTrigger(ChaOSTier t, uint64_t seed, uint64_t first_cycle, uint64_t last_cycle)`；`bool fire(uint64_t now_cycle)`；`static constexpr uint64_t intervalCycles(ChaOSTier)`（F1=2600000/F2=260000/F3=26000，2.6GHz 折算）。
  语义（北极星 02）：F0=窗口内单次均匀（**要求显式 last_cycle**，0 时退化为 first_cycle 立即触发并在头注释声明）；F1–F3=固定平均间隔±50% 抖动；F5=恒真（永久缺陷，写路径 mask 语义由注入器负责）。契约：在注入器 hook 点轮询（cycle 或事件粒度均可，间隔按 CPU cycle 计）。

- [x] **Step 1: 写 chaos_trigger.hh**

```cpp
/*
 * chaos_trigger.hh — OoO north-star F0-F5 unified trigger semantics
 * (docs/gem5-fi/ooo/02-frequency-and-sampling.md; 06-implementation-plan
 * W0.2). Header-only like chaos_event_sample.hh (no SConscript entry).
 *
 * Tiers: F0 single uniform over [first,last) — REQUIRES explicit last_cycle
 * (last_cycle==0 degenerates to firing at first_cycle); F1/F2/F3 fixed mean
 * interval with ±50% jitter (1ms/100µs/10µs @2.6GHz = 2.6M/260K/26K cycles);
 * F5 permanent defect (always true — the injector applies the stuck mask on
 * every write; timing is not its dimension). Poll fire() at the injector's
 * hook; intervals are in CPU cycles.
 */
#ifndef __CPU_O3_CHAOS_TRIGGER_HH__
#define __CPU_O3_CHAOS_TRIGGER_HH__

#include <cstdint>

#include "cpu/o3/chaos_event_sample.hh"

namespace gem5
{

enum class ChaOSTier : uint8_t
{
    F0, F1, F2, F3, F5
};

struct ChaOSTrigger
{
    ChaOSTier tier;
    uint64_t rng;
    uint64_t first_cycle;
    uint64_t last_cycle;   // 0 = unbounded (F0: see header comment)
    uint64_t next_fire = 0;
    bool spent = false;    // F0 fired once
    bool armed = false;

    ChaOSTrigger(ChaOSTier t, uint64_t seed, uint64_t first, uint64_t last)
        : tier(t), rng(seed ? seed : 1), first_cycle(first), last_cycle(last)
    {}

    static constexpr uint64_t
    intervalCycles(ChaOSTier t)
    {
        switch (t) {
          case ChaOSTier::F1: return 2600000;
          case ChaOSTier::F2: return   260000;
          case ChaOSTier::F3: return    26000;
          default:            return        0;   // F0/F5: not interval-based
        }
    }

    bool
    fire(uint64_t now)
    {
        switch (tier) {
          case ChaOSTier::F5:
            return true;
          case ChaOSTier::F0: {
            if (spent) return false;
            if (!armed) {
                armed = true;
                const uint64_t span = (last_cycle > first_cycle)
                                    ? last_cycle - first_cycle : 1;
                next_fire = first_cycle + chaosSampleLCG(rng) % span;
            }
            if (now >= next_fire) { spent = true; return true; }
            return false;
          }
          default: {              // F1/F2/F3
            if (!armed) { armed = true; scheduleNext(first_cycle); }
            if (now < next_fire) return false;
            scheduleNext(next_fire);
            return true;
          }
        }
    }

  private:
    void
    scheduleNext(uint64_t from)
    {
        // mean interval ±50%: from + U[iv/2, 3*iv/2)
        const uint64_t iv = intervalCycles(tier);
        rng = chaosSampleLCG(rng);
        next_fire = from + iv / 2 + rng % iv;
    }
};

} // namespace gem5

#endif // __CPU_O3_CHAOS_TRIGGER_HH__
```

- [x] **Step 2: 写独立单测 tests/chaos_trigger_test.cc**

断言：①F1 抽 1000 个相邻 fire 间隔全部 ∈ [1.3M, 3.9M)（±50% of 2.6M）；②F0 在 [1000, 2000) 窗口恰好 fire 一次且同 seed 复现同 cycle；③F5 恒真；④同 seed 两次构造的 F1 序列逐项相等（确定性）。main() 末尾打印 `CHAOS_TRIGGER_TEST PASS`。

- [x] **Step 3: 运行单测（真机输出为证）**

```bash
g++ -std=c++17 -Wall -Wextra -Werror -I CHAOS/gem5/src -I CHAOS/gem5/src/cpu/o3 \
    tests/chaos_trigger_test.cc -o /tmp/chaos_trigger_test && /tmp/chaos_trigger_test
```
Expected: `CHAOS_TRIGGER_TEST PASS`（零 warning——`-Wall -Wextra -Werror` 近似 gem5 编译纪律；首次 gem5 旗标编译在 W4.1 接线时）。
〔执行注 2026-09-23：原命令只有 `-I CHAOS/gem5/src/cpu/o3`，与 header 的仓库惯例 include "cpu/o3/chaos_event_sample.hh" 不自洽（g++ 需要相对 src/ 解析）——补 `-I CHAOS/gem5/src` 镜像 gem5 真实 CPPPATH（CHAOSFPU.cc:11 同款 include 在真实构建中即如此解析），已修正上方命令。实测输出：5 项 PASS（F1 mean=2653066；F0 落点 cycle 1733 同 seed 复现；F5 恒真；同 seed 序列逐项相等；F2 mean=267273/F3 mean=26179）+ CHAOS_TRIGGER_TEST PASS，EXIT=0。〕

- [x] **Step 4: Commit + push**（同 Task 1 格式，引用 Step 3 输出）

---

### Task 3: W0.3a — CHAOSProbe 占用/阈值事件探针

**Files:**
- Create: `CHAOS/gem5/src/cpu/o3/CHAOSProbe/CHAOSProbe.hh` / `.cc` / `.py` / `SConscript`（以 `CHAOS/gem5/src/cpu/o3/CHAOSFreeList/` 四件套为模板）
- Modify: `configs/se/ooo_proxy.py`（追加 `--chaos_probe` 参数 + 挂载块）

**Interfaces:**
- Produces: SimObject `CHAOSProbe(cpu=, sampleEvery=1, robThresholdPct=80, iqThresholdPct=80, flIntLe=8, flFloatLe=12, flVecLe=6, writeLog=True)`；self-attach（startup() dynamic_cast O3CPU，仿 CHAOSFreeList.cc:155-165）；每 sampleEvery 周期采样一次；仿真结束时打印一行：
  `CHAOS_PROBE samples=<n> robOver80=<n> iqOver80=<n> flIntLe8=<n> flFloatLe12=<n> flVecLe6=<n> robMax=<n> iqMax=<n> flIntMin=<n> flFloatMin=<n> flVecMin=<n>`
- Consumes（已核实的访问器）: `cpu->o3ROB()` 上 `countInsts()`（rob.hh:268）；IEW 侧 IQ 占用 `getCount(ThreadID)`（inst_queue.hh:391，线程 0）；`cpu->physFreeList().numFreeRegs(RegClassType)`（free_list.hh:255；IntRegClass/FloatRegClass/VecRegClass）。
- 下游：Task 4（event_density.py 解析该行）；W1.5 探针核达标验证；W2.4 CHAOSMicroSnap 复用本骨架。

- [ ] **Step 1: 阅读模板**——`CHAOSFreeList/` 四件 + `free_list.hh:189-195`（setChaosFreeList self-attach 样板）+ `CHAOSReg.hh:61`（periodic event 样板：EventFunctionWrapper + cpu->schedule(cpu->clockEdge(...))）。
- [ ] **Step 2: 写四件套**——.hh：参数+计数器成员+`tick()`；.cc：startup() self-attach + 首次调度、tick() 采样（读三处占用，越阈值计数，重调度 `cpu->clockEdge(Cycles(sampleEvery))`）、end-of-sim（`drain()` 或 startup 注册 exit callback——用 CHAOSPhysReg.cc:566 `ReadTraceFinal` 同款机制）打印汇总行；.py：SimObject 参数声明（Param.Unsigned/Param.Percent 或 Float/Bool writeLog）；SConscript：仿 CHAOSFreeList 的 Source 列表。
- [ ] **Step 3: 增量构建（零警告）**

```bash
cd CHAOS/gem5 && scons -j126 build/ARM/gem5.opt 2>&1 | tail -5
```
Expected: `scons: Building targets ...` 完成无新 warning/error（输出二进制时间戳更新；注意 buildpath 陷阱——最终产物必须在**仓库根** `build/ARM/gem5.opt`）。

- [ ] **Step 4: 挂载进 C3**——ooo_proxy.py 加 `--chaos_probe` 参数与 `CHAOSProbe(cpu=cpu0, ...)` 挂载块（`board.chaos_probe = probe`）。
- [ ] **Step 5: 定向验证 + 观测无扰动证明（同一命令完成）**

```bash
build/ARM/gem5.opt --outdir=/tmp/ooo_w03a configs/se/ooo_proxy.py \
    --cmd workloads/directed/reg_chain --cpu O3 --chaos_probe > /tmp/ooo_w03a.out 2>&1
grep -E "CHAOS_PROBE" /tmp/ooo_w03a.out
grep -c "f247ef3fe6f02cfd" /tmp/ooo_w03a.out
```
Expected: CHAOS_PROBE 行出现且 samples/robMax 数值合理（robMax ≤ 128）；**golden 仍 =1**（探针只读不改架构状态——这是「观测无扰动」的证明）；记录有无探针两次运行的 wall time 差（采样开销）。

- [ ] **Step 6: Commit + push**

---

### Task 4: W0.3b — tools/event_density.py 事件密度聚合器

**Files:**
- Create: `tools/event_density.py`（stdlib-only）

**Interfaces:**
- Produces: `python3 tools/event_density.py --runs DIR [DIR...] [--json OUT]`——每个 DIR = 一个 gem5 outdir（含 stats.txt；若 stdout 留存则顺带解析 CHAOS_PROBE 行）。输出表：`workload | branch_mispred/run | squash/run | renamed_insts/run | commits/run | robOver80/run | iqOver80/run | flIntLe8/run | ...`（--json 同内容机器可读版）。
- 下游：W3.2 事件覆盖计数倒推（密度表 → 运行数）；W1.5 探针核达标验收。

- [ ] **Step 1: 从真实产物发现 stats 字段名**（Step 2 写码的前置——名字必须来自实测，不猜）

```bash
grep -iE "mispred|squash|renamedInsts|committedInst" /tmp/ooo_w01_c3/stats.txt | head
```
Expected: 得到形如 `system.cpu.commit.branchMispredicts` / `system.cpu.rename.squashedInsts` / `system.cpu.rename.renamedInsts` / `system.cpu.commit.committedInsts` 的**实际字段名**（记下，写入 Step 2 的 STATS_KEYS；stats.txt 由 Task 1 的 C3 冒烟运行产出——依赖 Task 1 已完成）。

- [ ] **Step 2: 写解析器**——STATS_KEYS = Step 1 实测名（缺键时大声失败 exit 1，不静默）；`--runs` 每目录读 stats.txt（文本格式 `name value ...`）+ 可选 `gem5.out`/stdout 抓 `CHAOS_PROBE` 行；聚合均值/最小/最大；打印 markdown 表 + 可选 --json。
- [ ] **Step 3: 验证（两源一致 + 确定性）**

```bash
python3 tools/event_density.py --runs /tmp/ooo_w03a --json /tmp/dens_w03a.json
```
Expected: 表中 mispredict 数与 `grep branchMispredicts /tmp/ooo_w03a/stats.txt` 的原值一致（解析正确性）；再跑一次 reg_chain（不同 outdir）密度一致（确定性）。**注意**：若 /tmp/ooo_w03a 的 stats.txt 不含 CHAOS_PROBE（probe 在 stdout），确认解析路径取的是 .out 文件。
- [ ] **Step 4: Commit + push**

---

## Self-Review 记录

- **Spec 覆盖**：06 §4 W0.1→Task 1；W0.2→Task 2（F0/F1/F2/F3/F5 语义 + ±50% 抖动 + manifest trigger 的 fixed_interval 模式留待 W3.1 编排层统一加——W0.2 只交付 C++ 语义层，与 06「共享 helper」表述一致）；W0.3→Task 3+4（细化理由已注明）。
- **占位符扫描**：Task 4 Step 1 的 stats 字段名是显式的「实测发现」步骤（有具体 grep 命令与产出物去向），非占位符；其余步骤均含完整代码/命令。
- **类型一致性**：ChaOSTrigger API 在 Task 2 定义、W4.1（未来）消费——签名已在 Interfaces 固定；CHAOS_PROBE 行格式在 Task 3 定义、Task 4 消费——字段名一致。
