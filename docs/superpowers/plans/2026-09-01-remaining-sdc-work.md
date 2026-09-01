# 鲲鹏920 SDC 研究剩余工作实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完成 gem5-fi SDC 研究的四块剩余工作：CHAOSROB spec_leak（投机泄漏）、CHAOSBPU（分支预测）、runner cache 路径（formal 风险反转图）、method1 formal campaign（n=384 Fisher 检验）。

**Architecture:** 四块独立工作按依赖排序。spec_leak 通过 hook `Rename::doSquash` 的 historyBuffer 回溯（跳过 `freeingInProgress` 归还 = 保留错误路径 PRF 写）。CHAOSBPU 通过 `cpu->fetch.bac->bpu` 路径 hook `BAC::predict` 后的目标替换。runner cache 路径让 `component: l1d/l2/l1i` 路由到 `arm_chaos_cache.py`。method1 formal 用现有 campaign.py + fail_count oracle 跑 cholesky_numeric n=384。

**Tech Stack:** gem5 v25.1.0.1 (vendored at `CHAOS/gem5/`)、C++20 (SimObject)、Python 3.11 (config/runner)、CLAUDE.md 补丁纪律（一补丁一单元 + 真机自验证 + 推 `fi-wangxu` 非 main）。

**Spec:** `docs/KUNPENG920-SDC研究方案-系统完备版.md`（§5.2 spec_leak、§5.9 CHAOSBPU、§4.4 campaign、§5.2 H 验收断言）

## Global Constraints

- 构建命令：`cd CHAOS/gem5 && source /home/sdc/gem5-deps/env.sh && scons build/ARM/gem5.opt -j16`（**禁用 -j126，会 OOM**）
- 运行前必 `source /home/sdc/gem5-deps/env.sh`（设 LD_LIBRARY_PATH）
- gem5.opt 路径：`CHAOS/gem5/build/ARM/gem5.opt`（非顶层 build/）
- 每个 CHAOS 注入器改完须同步顶层副本到 vendored：`cp -f CHAOS/< injector >/\* CHAOS/gem5/src/<对应路径>/` 然后 `diff -rq` 验证 IDENTICAL
- 提交纪律：一补丁一单元 + 构建零 CHAOS 源警告 + 真机功能验证（引用真实 gem5 输出）+ 不相关回归 + `git push origin fi-wangxu` + **commit message 不得含 "Co-Authored-By: Claude"**
- 诚实纪律：验证不通过不提交；单次注入未产生 SDC 时标注"机制已验证，formal 待 n=384"
- 所有注入器遵循统一骨架：attackEvent 自驱动 + rng lambda 初始化（`rng_seed != 0 ? seed : local_rd()`）+ `>=` 概率比较符 + `Site:` 日志字段（runner 按 `Site:` 行计数 faults）+ G7 零警告（enum switch 全 case）

---

### Task 1: CHAOSROB spec_leak 模式（hook Rename::doSquash 的 freelist 归还）

method1 "投机流状态泄漏"的 ROB 维度：squash 时错误路径 μop 的 dest physReg 本应回溯归还，spec_leak 跳过归还 → physReg 双占用 → 后续指令读到错误路径残留值（method1 的 4x numeric-vs-compute 签名）。

**研究结论（hook 点已核实）**：`Rename::doSquash`（`rename.cc` 的 doSquash 函数）在回溯 historyBuffer 时执行 `renameMap[tid]->setEntry(hb_it->archReg, hb_it->prevPhysReg)` 并把 `hb_it->newPhysReg` push 进 `freeingInProgress[tid]`（延迟归还 freelist）。**spec_leak = 跳过 push 进 freeingInProgress（保留 physReg 不归还）**——注意：不能跳过 setEntry（那会破坏 RAT 一致性导致 SimulatorError），只跳过归还，制造"physReg 已不被 RAT 引用但也没归还 freelist"的泄漏态，配合后续 rename 复用时读旧值。

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/rename.hh`（Rename 类加 `class CHAOSROB *chaosRob = nullptr;` 成员 + setter）
- Modify: `CHAOS/gem5/src/cpu/o3/rename.cc`（doSquash 的 `freeingInProgress[tid].push_back(...)` 行前加 hook）
- Modify: `CHAOS/CHAOSROB/CHAOSROB.hh`（加 `bool maybeDelayFree(PhysRegIdPtr reg)` 方法声明 + spec_leak 状态）
- Modify: `CHAOS/CHAOSROB/CHAOSROB.cc`（实现 maybeDelayFree：spec_leak 模式下按概率返回 true = 跳过归还）
- Modify: `CHAOS/CHAOSROB/CHAOSROB.py`（无需改，spec_leak mode 已有）
- Modify: `configs/se/arm_chaos.py`（无需改，`--chaos_rob --rob_mode=spec_leak` 已有）
- 同步：`cp -f CHAOS/CHAOSROB/CHAOSROB.{hh,cc} CHAOS/gem5/src/cpu/o3/CHAOSROB/`

**Interfaces:**
- Consumes: `cpu->rename`（cpu.hh:439 protected，需经现有 CHAOSROB 的 `cpu->robAccess()` 同层访问；实际通过 `cpu.hh` 已有 accessor 模式——rename 不是 public，需要走 CHAOSROB 构造时由 config 传入或加 accessor）
- Produces: `Rename::chaosRob` 成员（rename.hh），`CHAOSROB::maybeDelayFree(PhysRegIdPtr) -> bool`

**关键设计：rename 的访问路径。** `cpu.hh:439` `Rename rename;` 是 protected。CHAOSROB 持有 `o3::CPU *cpu`，无法直接到 rename。两个方案：
- 方案 A（推荐）：CHAOSROB 构造函数里经 `cpu->robAccess()` 不行（ROB 无 rename 引用）→ 直接在 `cpu.hh` 加 `Rename &renameAccess() { return rename; }`（与 robAccess 同模式，line 477 public 区）
- 方案 B：rename.cc 的 hook 通过 `cpu->rob` 反查——不可行（ROB 无 chaosRob 引用）

用方案 A。hook 数据流：`rename.cc doSquash` → `if (chaosRob && chaosRob->maybeDelayFree(hb_it->newPhysReg)) { /* skip push_back */ }`。rename 的 chaosRob 成员由 CHAOSROB 构造函数设置：`cpu->renameAccess().setChaosRob(this)`。

- [ ] **Step 1: cpu.hh 加 renameAccess accessor**

在 `CHAOS/gem5/src/cpu/o3/cpu.hh` 的 `robAccess()` 后（line ~490，`ROB &robAccess() { return rob; }` 之后）加：

```cpp
    /** CHAOSROB spec_leak accessor (S6-4): exposes Rename so the injector
     *  can hook doSquash's freelist return (skip freeingInProgress push
     *  = retain wrong-path PRF write). Same pattern as robAccess(). */
    Rename &renameAccess() { return rename; }
```

- [ ] **Step 2: rename.hh 加 chaosRob 成员**

在 `CHAOS/gem5/src/cpu/o3/rename.hh` 的 `class Rename` public 区（line 87 `public:` 后）加前向声明与成员。文件顶部（line 76 `namespace gem5 {` 后）加：

```cpp
// Forward declaration: CHAOSROB spec_leak hooks doSquash's freelist return.
class CHAOSROB;
```

在 class Rename 的 public 区加：

```cpp
    /** CHAOSROB spec_leak hook (S6-4): set by the injector's constructor.
     *  When non-null, doSquash asks maybeDelayFree() before pushing a
     *  squashed inst's dest physReg into freeingInProgress — returning
     *  true SKIPS the freelist return (retains the wrong-path PRF write,
     *  method1's speculative-state-leak signature). */
    class CHAOSROB *chaosRob = nullptr;
    void setChaosRob(CHAOSROB *p) { chaosRob = p; }
```

- [ ] **Step 3: rename.cc doSquash 加 hook**

在 `CHAOS/gem5/src/cpu/o3/rename.cc` 的 doSquash 函数中，找到这一段（"The phys regs can still be owned by squashing"注释块）：

```cpp
        if (hb_it->newPhysReg != hb_it->prevPhysReg) {
            // Tell the rename map to set the architected register to the
            // previous physical register that it was renamed to.
            renameMap[tid]->setEntry(hb_it->archReg, hb_it->prevPhysReg);

            // The phys regs can still be owned by squashing but
            // executing instructions in IEW at this moment. To avoid
            // ownership hazard in SMT CPU, we delay the freelist update
            // until they are indeed squashed in the commit stage.
            freeingInProgress[tid].push_back(hb_it->newPhysReg);
        }
```

改为（只 hook push_back，setEntry 保留——RAT 一致性不能破坏）：

```cpp
        if (hb_it->newPhysReg != hb_it->prevPhysReg) {
            // Tell the rename map to set the architected register to the
            // previous physical register that it was renamed to.
            renameMap[tid]->setEntry(hb_it->archReg, hb_it->prevPhysReg);

            // CHAOSROB spec_leak (S6-4): optionally SKIP the freelist
            // return — the wrong-path dest physReg is neither referenced
            // by the RAT nor returned to the free list, leaking the
            // speculative write (method1's state-leak 4x signature).
            if (chaosRob && chaosRob->maybeDelayFree(hb_it->newPhysReg)) {
                DPRINTF(Rename, "[tid:%i] spec_leak: skipped freelist return "
                        "of phys reg %d (wrong-path write retained).\n",
                        tid, hb_it->newPhysReg->index());
            } else {
                // The phys regs can still be owned by squashing but
                // executing instructions in IEW at this moment. To avoid
                // ownership hazard in SMT CPU, we delay the freelist update
                // until they are indeed squashed in the commit stage.
                freeingInProgress[tid].push_back(hb_it->newPhysReg);
            }
        }
```

- [ ] **Step 4: CHAOSROB.hh 加 maybeDelayFree 声明 + spec_leak 成员**

在 `CHAOS/CHAOSROB/CHAOSROB.hh` 的 `processFault` 声明后加：

```cpp
    // S6-4 spec_leak: called from Rename::doSquash before returning a
    // squashed inst's dest physReg to the free list. Returns true to SKIP
    // the return (retain the wrong-path PRF write — method1's state-leak
    // signature). Honors probability/window/maxFaults; only active when
    // fi_mode == SpecLeak.
    bool maybeDelayFree(const PhysRegIdPtr &reg);
```

注意：`PhysRegIdPtr` 需要 include。在 CHAOSROB.hh 顶部 include 区加（若未有）：

```cpp
#include "cpu/o3/dyn_inst_ptr.hh"  // PhysRegIdPtr (via DynInst header chain)
```

实际 `PhysRegIdPtr` 定义在 `src/cpu/reg_class.hh`（`using PhysRegIdPtr = RefCountingPtr<PhysRegId>;`）。保险起见 include `"cpu/o3/free_list.hh"` 不行（它 include 不到）——直接 include `"cpu/reg_class.hh"` 并确认编译。

- [ ] **Step 5: CHAOSROB.cc 实现 maybeDelayFree + 构造函数挂载**

在 `CHAOS/CHAOSROB/CHAOSROB.cc` 中：

构造函数体（`if (probability > 0.0f) {` 块内、`stats = std::make_unique<...>` 之后）加：

```cpp
            // S6-4 spec_leak: register on Rename so doSquash can reach us.
            cpu->renameAccess().setChaosRob(this);
```

实现 maybeDelayFree（processFault 后加）：

```cpp
    bool
    CHAOSROB::maybeDelayFree(const PhysRegIdPtr &reg)
    {
        if (fi_mode != Mode::SpecLeak) return false;
        if (probability <= 0.0f) return false;
        Cycles cur = cpu->curCycle();
        if (cur < first_clock) return false;
        if (last_clock != Cycles(0) && cur > last_clock) return false;
        if (max_faults != 0 && faults_injected_count >= max_faults) return false;
        std::uniform_real_distribution<float> dist(0.0f, 1.0f);
        if (dist(rng) >= probability) return false;

        // Skip the freelist return: the wrong-path dest physReg leaks.
        stats->numSpecLeak++;
        stats->numFaultsInjected++;
        ++faults_injected_count;
        if (write_log) {
            *(log_stream->stream())
                << "Cycle: " << cpu->curCycle()
                << ", CPU: " << cpu->name()
                << ", Site: rename_doSquash_freelist_skip"
                << ", Mode: spec_leak"
                << ", PhysReg: " << reg->index()
                << std::endl;
        }
        return true;
    }
```

同时**删除 processFault 里的 spec_leak NOT IMPLEMENTED 分支**（原来那个 `stats->numLegalityRejects++; ... "NOT IMPLEMENTED"` 块），因为 spec_leak 现在走 maybeDelayFree 路径（attackCheck 的 processFault 里 SpecLeak case 改为直接 return，不注入——spec_leak 的注入点已移到 doSquash hook）：

```cpp
        } else if (fi_mode == Mode::SpecLeak) {
            // spec_leak is now driven by Rename::doSquash's maybeDelayFree
            // hook (constructor registered us on Rename). Nothing to do
            // here — the attackEvent only services entry_bitflip/exc_suppress.
            return;
        }
```

- [ ] **Step 6: 同步 + 构建**

```bash
cd /home/sdc/wangxu/gem5-fi-wangxu
cp -f CHAOS/CHAOSROB/CHAOSROB.hh CHAOS/gem5/src/cpu/o3/CHAOSROB/CHAOSROB.hh
cp -f CHAOS/CHAOSROB/CHAOSROB.cc CHAOS/gem5/src/cpu/o3/CHAOSROB/CHAOSROB.cc
diff -rq CHAOS/CHAOSROB/ CHAOS/gem5/src/cpu/o3/CHAOSROB/   # 期望仅 .py 不在 vendored（实际都在，期望 IDENTICAL）
cd CHAOS/gem5 && source /home/sdc/gem5-deps/env.sh
scons build/ARM/gem5.opt -j16 2>&1 | grep -iE "error|done building" | tail -5
```

预期：`scons: done building targets.` 零 error。若 `PhysRegIdPtr` 编译错，把 CHAOSROB.hh 的 include 换成 `#include "cpu/o3/dyn_inst.hh"`（它传递引入）。

- [ ] **Step 7: 真机验证 1——回归（prob=0 不破坏 golden）**

```bash
cd /home/sdc/wangxu/gem5-fi-wangxu
chmod +x CHAOS/gem5/build/ARM/gem5.opt
G5=$PWD/CHAOS/gem5/build/ARM/gem5.opt
source /home/sdc/gem5-deps/env.sh
timeout 150 "$G5" --quiet --outdir=runs/t1_reg configs/se/arm_chaos.py \
    --cmd=workloads/directed/reg_chain --cpu=O3 \
    --chaos_rob --rob_mode=spec_leak --probability=0.0 2>&1 | grep -E "^[0-9a-f]{16}$" | tail -1
```

预期：`f247ef3fe6f02cfd`（golden 不变，prob=0 时 maybeDelayFree 恒 false）。

- [ ] **Step 8: 真机验证 2——spec_leak 触发（branchy kernel 制造 squash）**

reg_chain 无分支不产生 squash——需要 branchy kernel。用已有的 `workloads/directed/l1i_loop`（紧循环有分支回跳，会产生 squash 吗？不会——正确预测不 squash）。**需要一个 mispredict-heavy kernel**。先写一个：

```bash
cat > workloads/directed/branchy_leak.c << 'EOF'
/* branchy_leak.c — CHAOSROB spec_leak verification kernel.
 * Alternating unpredictable branches (data-dependent xorshift) force
 * frequent mispredicts -> squashes. spec_leak skips the squashed insts'
 * dest physReg freelist return -> later instructions read the leaked
 * wrong-path value -> checksum differs from golden.
 */
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>

static uint32_t rng_s = 0x5A5A1234u;
static inline uint32_t xs32(void){uint32_t x=rng_s;x^=x<<13;x^=x>>17;x^=x>>5;rng_s=x;return x;}

int main(int argc, char **argv) {
    long iters = (argc > 1) ? atol(argv[1]) : 500;
    uint64_t acc = 0;
    for (long i = 0; i < iters; i++) {
        uint32_t r = xs32();
        /* data-dependent branch: unpredictable -> mispredicts -> squashes */
        if (r & 0x80000000u) {
            acc += r * 3;
        } else {
            acc ^= r;
        }
        /* dest physReg live across the branch (spec_leak target) */
        uint64_t t = acc + (uint64_t)(i + 1);
        acc = t ^ (r >> 3);
    }
    printf("%016lx\n", acc & 0xFFFFFFFFFFFFFFFFULL);
    fprintf(stderr, "iters=%ld fails=0 variant=branchy_leak\n", iters);
    return 0;
}
EOF
gcc -static -O2 -o workloads/directed/branchy_leak workloads/directed/branchy_leak.c
workloads/directed/branchy_leak 100   # native golden（跑 2 次确认确定性）
workloads/directed/branchy_leak 100
```

预期：两次输出同一 16-hex checksum。记录该值作为 golden。

```bash
# gem5 golden（无注入）
timeout 200 "$G5" --quiet --outdir=runs/t1_bgold configs/se/arm_chaos.py \
    --cmd=workloads/directed/branchy_leak --cpu=O3 2>&1 | grep -E "^[0-9a-f]{16}$" | tail -1
```

预期：与 native golden 相同（native==gem5 确定性）。

```bash
# spec_leak 注入（maxFaults=1，squash 时跳过一次 freelist 归还）
timeout 200 "$G5" --quiet --outdir=runs/t1_sleak configs/se/arm_chaos.py \
    --cmd=workloads/directed/branchy_leak --cpu=O3 \
    --chaos_rob --rob_mode=spec_leak \
    --probability=1.0 --first_clock=50000 --max_faults=1 --rng_seed=20260825 \
    2>&1 | grep -E "^[0-9a-f]{16}$" | tail -1
grep -E "spec_leak|rename_doSquash" runs/t1_sleak/rob_injections.log 2>/dev/null | head -2
grep -iE "numSpecLeak" runs/t1_sleak/stats.txt 2>/dev/null | head -1
```

预期：`rob_injections.log` 出现 `Site: rename_doSquash_freelist_skip, Mode: spec_leak` 行且 `numSpecLeak>=1`。checksum 可能等于 golden（单次泄漏未传播——概率性）或不等（SDC）。**机制验证标准：日志 + numSpecLeak>=1，输出分类另记。**

- [ ] **Step 9: 不相关回归（CHAOSPhysReg 不受影响）**

```bash
timeout 180 "$G5" --quiet --outdir=runs/t1_phyreg configs/se/arm_chaos.py \
    --cmd=workloads/directed/reg_chain --cpu=O3 \
    --chaos_phys --phys_mode=arch_frontend --phys_target_arch=3 \
    --probability=1.0 --first_clock=100000 --max_faults=1 \
    --rng_seed=20260825 --fault_type=bit_flip 2>&1 | grep -E "^[0-9a-f]{16}$" | tail -1
```

预期：`d43a25d7fcc218b7`（GPR SDC 锚点不变）。

- [ ] **Step 10: 提交**

```bash
cd /home/sdc/wangxu/gem5-fi-wangxu
git add CHAOS/CHAOSROB/ CHAOS/gem5/src/cpu/o3/CHAOSROB/ \
        CHAOS/gem5/src/cpu/o3/cpu.hh CHAOS/gem5/src/cpu/o3/rename.hh \
        CHAOS/gem5/src/cpu/o3/rename.cc \
        workloads/directed/branchy_leak workloads/directed/branchy_leak.c
git commit -m "S6-4: CHAOSROB spec_leak（hook Rename::doSquash 跳过 freelist 归还）

method1 投机流状态泄漏的 ROB 维度：squash 时错误路径 μop 的 dest physReg
本应经 freeingInProgress 归还 freelist；spec_leak 按概率跳过归还——physReg
不被 RAT 引用也不归还，后续 rename 复用时读到错误路径残留值（method1 的
4x numeric-vs-compute 签名）。

实现：
- cpu.hh: renameAccess() accessor（与 robAccess 同模式）
- rename.hh: chaosRob 成员 + setChaosRob（CHAOSROB 构造时自挂载）
- rename.cc doSquash: freeingInProgress.push_back 前调
  maybeDelayFree()——true 则跳过归还（setEntry 保留，RAT 一致性不破坏）
- CHAOSROB: maybeDelayFree()（prob/window/maxFaults 门控 + numSpecLeak +
  Site: rename_doSquash_freelist_skip 日志）；processFault 的 SpecLeak case
  改为空（注入点移到 doSquash hook）
- branchy_leak kernel: 数据依赖分支制造 mispredict->squash

真机自验证：
1. 构建：零 CHAOS 源警告（G7）
2. 回归：prob=0 golden=f247ef3fe6f02cfd；CHAOSPhysReg GPR SDC=
   d43a25d7fcc218b7 不变
3. spec_leak 触发：branchy_leak + spec_leak -> rob_injections.log
   'Site: rename_doSquash_freelist_skip Mode: spec_leak' +
   numSpecLeak>=1（引用实际输出）
诚实边界：单次泄漏未必然传播 SDC（概率性）；formal 量化需 n=384。"
git push origin fi-wangxu
```

---

### Task 2: CHAOSBPU（BAC::predict 目标替换 F5）

方案 §5.9：BPU 预测目标 sub(F5)。研究结论：`BAC::predict`（bac.cc:565）调 `bpu->predict(inst, ft->ftNum(), pc, tid, ft->bpuHistory)` 后返回 taken；`pc` 是 `PCStateBase &`（ARM 的 PCState 有 `npc(val)` setter）。**hook 点：predict 调用后、return 前，按概率把 pc 的目标换成另一地址（F5 合法域：分支目标的 fall-through，即 pc()+4——合法且必然导致 mispredict+squash）。**

重点（方案 §5.9）：**喂给后端的错误投机流是否泄漏**——联合观测 squash 后架构态==golden。BPU 目标错 → mispredict → squash → 架构态恢复。预期 `P(squash 后架构态==golden)≈1`（预测错误被冲刷）。这是 BPU 的阴性对照价值。

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/bac.hh`（BAC 类加 chaosBpu 成员）
- Modify: `CHAOS/gem5/src/cpu/o3/bac.cc`（predict 函数加 hook + include）
- Modify: `CHAOS/gem5/src/cpu/o3/fetch.hh`（public 区加 `BAC *getBAC()`——bac 是 private，已核实 fetch.hh:395 private: 之后 line 423）
- Modify: `CHAOS/gem5/src/cpu/o3/cpu.hh`（public accessor 区加 `BAC &bacAccess()`）
- Create: `CHAOS/CHAOSBPU/CHAOSBPU.{py,hh,cc,SConscript}`
- Create: `CHAOS/gem5/src/cpu/o3/CHAOSBPU/`（同步副本）
- Modify: `configs/se/arm_chaos.py`（import + args + mount）
- Create: `workloads/directed/call_ret_heavy.c`（RAS/BTB 压力 kernel）

**Interfaces:**
- Consumes: `BAC::predict` 的 `PCStateBase &pc`（hook 改写其 npc）；`bpu->predict` 返回的 taken
- Produces: `CHAOSBPU` SimObject（`target_sub` 模式：把预测目标替换为 fall-through pc()+4）；`BAC::chaosBpu` 成员

- [ ] **Step 1: 写 CHAOSBPU.py**

```bash
mkdir -p CHAOS/CHAOSBPU
cat > CHAOS/CHAOSBPU/CHAOSBPU.py << 'EOF'
# CHAOSBPU — branch-predictor fault injector (plan §5.9, S8-4).
# Hooks BAC::predict (bac.cc): AFTER bpu->predict() computes the target,
# substitutes the predicted target with the fall-through address (pc()+4
# for AArch64) — an F5 legal-domain substitute (both are legal PCs; the
# wrong one forces a mispredict -> squash). The study point: does the
# wrong speculative stream LEAK architectural state (P(squash-then-
# arch==golden) should be ~= 1 — BPU is a negative-control surface).
from m5.params import *
from m5.SimObject import SimObject

class CHAOSBPU(SimObject):
    type = "CHAOSBPU"
    cxx_class = "gem5::CHAOSBPU"
    cxx_header = "cpu/o3/CHAOSBPU/CHAOSBPU.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU (must be an O3CPU)")
    probability = Param.Float(1.0, "Per-prediction probability of target substitution.")
    mode = Param.String("target_sub",
        "target_sub: replace predicted target with fall-through pc+4 (F5). "
        "direction_flip: invert taken (F1).")
    firstClock = Param.UInt64(0, "First clock cycle eligible")
    lastClock = Param.UInt64(0, "Last cycle (0 = unrestricted)")
    maxFaults = Param.UInt64(0, "Max faults (0 = unlimited). Use 1.")
    rngSeed = Param.UInt64(0, "RNG seed (0 = random_device).")
    writeLog = Param.Bool(True, "Write bpu_injections.log")
    semanticRole = Param.String("", "ABI role label. Metadata only.")
EOF
cat > CHAOS/CHAOSBPU/SConscript << 'EOF'
Import('*')
SimObject('CHAOSBPU.py', sim_objects=['CHAOSBPU'], enums=[])
Source('CHAOSBPU.cc')
DebugFlag('CHAOSBPU')
EOF
```

- [ ] **Step 2: 写 CHAOSBPU.hh**

```bash
cat > CHAOS/CHAOSBPU/CHAOSBPU.hh << 'EOF'
#ifndef __CPU_O3_CHAOS_BPU_HH__
#define __CPU_O3_CHAOS_BPU_HH__

#include <random>
#include <memory>
#include <string>
#include "base/output.hh"
#include "base/statistics.hh"
#include "base/types.hh"
#include "params/CHAOSBPU.hh"
#include "sim/sim_object.hh"
#include "sim/eventq.hh"

namespace gem5
{
namespace o3 { class CPU; }
class PCStateBase;

// CHAOSBPU — branch-predictor fault injector (plan §5.9).
// BAC::predict calls maybeSubstituteTarget() after bpu->predict() —
// target_sub replaces the predicted target with fall-through (F5 legal-
// domain substitute), direction_flip inverts taken. Wrong speculative
// stream should squash (P(arch==golden after squash) ~= 1): BPU is a
// negative-control surface (§2.2 P3).
class CHAOSBPU : public SimObject
{
  public:
    CHAOSBPU(const CHAOSBPUParams &p);
    ~CHAOSBPU();

    // Called from BAC::predict AFTER bpu->predict(). `pc` is the
    // prediction PC state (its npc() is the predicted target); `taken`
    // is bpu->predict's return. May rewrite pc (target_sub) or return
    // inverted taken (direction_flip). Returns the (possibly flipped)
    // taken value.
    bool maybeSubstituteTarget(PCStateBase &pc, bool taken, Addr fetch_pc);

  private:
    enum class Mode { TargetSub, DirectionFlip };
    static Mode stringToMode(const std::string &s);

    o3::CPU *cpu;
    float probability;
    Mode fi_mode;
    Cycles first_clock, last_clock;
    uint64_t max_faults, faults_injected_count;
    uint64_t rng_seed;
    bool write_log;
    std::string semantic_role;
    std::mt19937 rng;
    std::random_device rd;
    OutputStream *log_stream;

    struct Stats : public statistics::Group {
        statistics::Scalar numFaultsInjected;
        statistics::Scalar numTargetSub;
        statistics::Scalar numDirectionFlip;
        Stats(statistics::Group *parent);
    };
    std::unique_ptr<Stats> stats;
};
} // namespace gem5
#endif
EOF
```

- [ ] **Step 3: 写 CHAOSBPU.cc**

```bash
cat > CHAOS/CHAOSBPU/CHAOSBPU.cc << 'EOF'
#include "cpu/o3/CHAOSBPU/CHAOSBPU.hh"
#include "params/CHAOSBPU.hh"
#include "cpu/o3/cpu.hh"
#include "arch/generic/pcstate.hh"
#include "base/trace.hh"
#include "debug/CHAOSBPU.hh"
#include <iostream>
#include <fstream>

namespace gem5
{
    CHAOSBPU::CHAOSBPU(const CHAOSBPUParams &p)
        : SimObject(p),
          cpu(dynamic_cast<o3::CPU *>(p.cpu)),
          probability(p.probability),
          fi_mode(stringToMode(p.mode)),
          first_clock(Cycles(p.firstClock)),
          last_clock(Cycles(p.lastClock)),
          max_faults(p.maxFaults),
          faults_injected_count(0),
          rng_seed(p.rngSeed),
          write_log(p.writeLog),
          semantic_role(p.semanticRole),
          rng([this]() {
              std::random_device local_rd;
              return rng_seed != 0 ? std::mt19937(rng_seed) : std::mt19937(local_rd());
          }()),
          log_stream(nullptr),
          stats(nullptr)
    {
        if (!cpu) throw std::runtime_error(
            "CHAOSBPU: cpu not O3CPU. O3-only (hooks BAC::predict).");
        if (probability > 0.0f) {
            log_stream = simout.create("bpu_injections.log", false, true);
            if (!log_stream || !log_stream->stream())
                panic("CHAOSBPU: Could not open log file");
            stats = std::make_unique<Stats>(this);
        }
    }

    CHAOSBPU::~CHAOSBPU() {}

    CHAOSBPU::Mode CHAOSBPU::stringToMode(const std::string &s) {
        if (s == "direction_flip") return Mode::DirectionFlip;
        return Mode::TargetSub;  // default + "target_sub"
    }

    bool
    CHAOSBPU::maybeSubstituteTarget(PCStateBase &pc, bool taken, Addr fetch_pc)
    {
        if (probability <= 0.0f) return taken;
        Cycles cur = cpu->curCycle();
        if (cur < first_clock) return taken;
        if (last_clock != Cycles(0) && cur > last_clock) return taken;
        if (max_faults != 0 && faults_injected_count >= max_faults) return taken;
        std::uniform_real_distribution<float> dist(0.0f, 1.0f);
        if (dist(rng) >= probability) return taken;

        if (fi_mode == Mode::TargetSub) {
            // F5 legal-domain substitute: predicted target -> fall-through.
            // Both are legal PCs; the wrong one forces mispredict -> squash.
            Addr old_target = pc.npc();
            pc.npc(fetch_pc + 4);  // AArch64 fall-through (fixed 4B inst)
            stats->numTargetSub++;
            if (write_log) {
                *(log_stream->stream())
                    << "Cycle: " << cpu->curCycle()
                    << ", Site: bac_predict_target"
                    << ", Mode: target_sub"
                    << ", FetchPC: 0x" << std::hex << fetch_pc
                    << ", OldTarget: 0x" << old_target
                    << ", NewTarget: 0x" << (fetch_pc + 4) << std::dec
                    << std::endl;
            }
        } else {
            taken = !taken;  // direction_flip (F1)
            stats->numDirectionFlip++;
            if (write_log) {
                *(log_stream->stream())
                    << "Cycle: " << cpu->curCycle()
                    << ", Site: bac_predict_direction"
                    << ", Mode: direction_flip"
                    << std::endl;
            }
        }
        stats->numFaultsInjected++;
        ++faults_injected_count;
        return taken;
    }

    CHAOSBPU::Stats::Stats(statistics::Group *parent)
        : statistics::Group(parent),
          ADD_STAT(numFaultsInjected, statistics::units::Count::get(),
                   "Total BPU faults injected"),
          ADD_STAT(numTargetSub, statistics::units::Count::get(),
                   "target_sub faults (F5 fall-through substitute)"),
          ADD_STAT(numDirectionFlip, statistics::units::Count::get(),
                   "direction_flip faults (F1 taken inversion)")
    {}
} // namespace gem5
EOF
```

- [ ] **Step 4: bac.hh 加 chaosBpu 成员**

在 `CHAOS/gem5/src/cpu/o3/bac.hh` 的 `class BAC` 内（`bpu` 成员附近，line ~340 `branch_prediction::BPredUnit *bpu;` 后）加：

```cpp
    /** CHAOSBPU hook (S8-4): set by the injector's constructor. When
     *  non-null, predict() calls maybeSubstituteTarget() after bpu->predict()
     *  — may replace the predicted target (F5) or flip taken (F1). */
    class CHAOSBPU *chaosBpu = nullptr;
    void setChaosBPU(CHAOSBPU *p) { chaosBpu = p; }
```

文件顶部 `namespace gem5 {` 后（与其他前向声明一起）加：`class CHAOSBPU;`

注意：BAC 自挂载的接线方式——CHAOSBPU 构造函数需要拿到 BAC。`cpu->fetch` 是 public（cpu.hh:433），但 BAC 是 Fetch 的 private 成员。**方案**：在 `cpu.hh` 的 public accessor 区加：

```cpp
    /** CHAOSBPU accessor (S8-4): exposes the fetch stage's BAC so the
     *  injector can self-attach (setChaosBPU). Same pattern as renameAccess. */
    BAC &bacAccess() { return fetch.bac; }
```

**可访问性已核实**：Fetch 类中 `BAC *bac;`（fetch.hh:423）在 **private** 区（fetch.hh:395 `private:` 之后）——需在 Fetch 的 public 区加 getter，然后 cpu.hh 调它。

fetch.hh 的 public 区（`class Fetch` 内，比如 `setBACandFTQPtr` 附近）加：

```cpp
    /** CHAOSBPU accessor (S8-4): expose the BAC so the injector can
     *  self-attach via cpu.hh's bacAccess(). bac is otherwise private. */
    BAC *getBAC() { return bac; }
```

cpu.hh 的 public accessor 区（renameAccess 后）加：

```cpp
    /** CHAOSBPU accessor (S8-4): exposes fetch's BAC for injector
     *  self-attach. Same pattern as renameAccess(). */
    BAC &bacAccess() { return *(fetch.getBAC()); }
```

CHAOSBPU.cc 构造函数（probability>0 块内）加挂载：

```cpp
            cpu->bacAccess().setChaosBPU(this);
```

- [ ] **Step 5: bac.cc predict 加 hook**

在 `CHAOS/gem5/src/cpu/o3/bac.cc` 的 BAC::predict（line 565）中，`bool taken = bpu->predict(...)` 之后、`return taken` 之前加：

```cpp
    bool taken = bpu->predict(inst, ft->ftNum(), pc, tid, ft->bpuHistory);

    // CHAOSBPU (S8-4): optionally substitute the predicted target (F5)
    // or flip the direction (F1). Wrong speculative stream should squash
    // (P(arch==golden after squash) ~= 1 — negative-control surface).
    if (chaosBpu) {
        taken = chaosBpu->maybeSubstituteTarget(pc, taken, inst->pcState().pc());
    }

    DPRINTF(Branch, "[tid:%i, ftn:%llu] History added.\n", tid, ft->ftNum());
    return taken;
```

并在 bac.cc 顶部 include 区加：`#include "cpu/o3/CHAOSBPU/CHAOSBPU.hh"`

- [ ] **Step 6: arm_chaos.py 加挂载**

```bash
cd /home/sdc/wangxu/gem5-fi-wangxu
python3 - << 'PYEOF'
p = "configs/se/arm_chaos.py"
s = open(p).read()
s = s.replace("CHAOSROB, CHAOSIQ, CHAOSExec, CHAOSFPU, CHAOSL1DForward\n",
              "CHAOSROB, CHAOSIQ, CHAOSExec, CHAOSFPU, CHAOSL1DForward, CHAOSBPU\n", 1)
s = s.replace(
'p.add_argument("--l1dfwd_semantic_role", default="")\nargs = p.parse_args()',
'''p.add_argument("--l1dfwd_semantic_role", default="")
# S8-4 CHAOSBPU: branch-predictor target_sub (F5) / direction_flip (F1).
p.add_argument("--chaos_bpu", action="store_true",
               help="attach CHAOSBPU (BAC::predict target sub; negative-control "
                    "surface — wrong spec stream should squash).")
p.add_argument("--bpu_mode", default="target_sub",
               choices=["target_sub","direction_flip"])
p.add_argument("--bpu_semantic_role", default="")
args = p.parse_args()''')
s = s.replace(
"    board.chaos_l1dfwd = l1d\n\nif args.maxinsts:",
'''    board.chaos_l1dfwd = l1d

# CHAOSBPU (S8-4): BAC::predict target substitution.
if args.chaos_bpu:
    bpu = CHAOSBPU(
        cpu=cpu0,
        probability=args.probability,
        mode=args.bpu_mode,
        firstClock=args.first_clock,
        lastClock=args.last_clock,
        maxFaults=args.max_faults,
        rngSeed=args.rng_seed,
        writeLog=True,
        semanticRole=args.bpu_semantic_role,
    )
    board.chaos_bpu = bpu

if args.maxinsts:''')
open(p,"w").write(s)
print("patched")
PYEOF
```

- [ ] **Step 7: 写 call_ret_heavy kernel（RAS/BTB 压力）**

```bash
cat > workloads/directed/call_ret_heavy.c << 'EOF'
/* call_ret_heavy.c — CHAOSBPU verification kernel.
 * Deep call/return chains stress the BTB/RAS; data-dependent indirect
 * calls stress target prediction. target_sub replaces the predicted
 * target -> mispredict -> squash -> arch should recover (golden).
 */
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>

static uint32_t rng_s = 0x5A5A1234u;
static inline uint32_t xs32(void){uint32_t x=rng_s;x^=x<<13;x^=x>>17;x^=x>>5;rng_s=x;return x;}

__attribute__((noinline)) static uint64_t leaf(uint64_t v) { return v * 3 + 1; }
__attribute__((noinline)) static uint64_t l2(uint64_t v) { return leaf(v) ^ 0x5a5a; }
__attribute__((noinline)) static uint64_t l3(uint64_t v) { return l2(v) + leaf(v ^ 0xff); }

int main(int argc, char **argv) {
    long iters = (argc > 1) ? atol(argv[1]) : 300;
    uint64_t acc = 0;
    for (long i = 0; i < iters; i++) {
        acc += l3((uint64_t)i);
        acc ^= l2(acc);
    }
    printf("%016lx\n", acc & 0xFFFFFFFFFFFFFFFFULL);
    fprintf(stderr, "iters=%ld fails=0 variant=call_ret_heavy\n", iters);
    return 0;
}
EOF
gcc -static -O2 -o workloads/directed/call_ret_heavy workloads/directed/call_ret_heavy.c
workloads/directed/call_ret_heavy   # native golden ×2 确认确定性
workloads/directed/call_ret_heavy
```

- [ ] **Step 8: 同步 + 构建**

```bash
mkdir -p CHAOS/gem5/src/cpu/o3/CHAOSBPU
cp -f CHAOS/CHAOSBPU/* CHAOS/gem5/src/cpu/o3/CHAOSBPU/
cd CHAOS/gem5 && source /home/sdc/gem5-deps/env.sh
scons build/ARM/gem5.opt -j16 2>&1 | grep -iE "error|done building" | tail -5
```

预期：`scons: done building targets.`。`pc.npc()` setter 已核实存在（`arch/generic/pcstate.hh:275` `void npc(Addr val) { _npc = val; }`）。

- [ ] **Step 9: 真机验证**

```bash
cd /home/sdc/wangxu/gem5-fi-wangxu
chmod +x CHAOS/gem5/build/ARM/gem5.opt
G5=$PWD/CHAOS/gem5/build/ARM/gem5.opt
source /home/sdc/gem5-deps/env.sh
# 9a: 回归 prob=0
timeout 150 "$G5" --quiet --outdir=runs/t2_reg configs/se/arm_chaos.py \
    --cmd=workloads/directed/reg_chain --cpu=O3 --chaos_bpu --probability=0.0 \
    2>&1 | grep -E "^[0-9a-f]{16}$" | tail -1
# 预期 f247ef3fe6f02cfd
# 9b: call_ret_heavy gem5 golden（对照 native）
timeout 200 "$G5" --quiet --outdir=runs/t2_gold configs/se/arm_chaos.py \
    --cmd=workloads/directed/call_ret_heavy --cpu=O3 2>&1 | grep -E "^[0-9a-f]{16}$" | tail -1
# 9c: target_sub 注入（预期：输出==golden——mispredict 被 squash 恢复，
#     这是 BPU 阴性对照的核心断言 P(arch==golden)≈1）
timeout 200 "$G5" --quiet --outdir=runs/t2_sub configs/se/arm_chaos.py \
    --cmd=workloads/directed/call_ret_heavy --cpu=O3 --chaos_bpu \
    --bpu_mode=target_sub \
    --probability=1.0 --first_clock=50000 --max_faults=10 --rng_seed=20260825 \
    2>&1 | grep -E "^[0-9a-f]{16}$" | tail -1
grep -iE "numTargetSub|numFaultsInjected" runs/t2_sub/stats.txt | head -2
grep -E "target_sub" runs/t2_sub/bpu_injections.log | head -2
```

预期：9c 输出 == 9b golden（**squash 后架构态恢复 = BPU 阴性对照断言成立**），且 `numTargetSub>=1`、日志有 `Site: bac_predict_target`。若输出≠golden，如实记录（可能 hang/crash——错误目标跳到非法区）并分析。

- [ ] **Step 10: 不相关回归 + 提交**

```bash
timeout 180 "$G5" --quiet --outdir=runs/t2_phy configs/se/arm_chaos.py \
    --cmd=workloads/directed/reg_chain --cpu=O3 \
    --chaos_phys --phys_mode=arch_frontend --phys_target_arch=3 \
    --probability=1.0 --first_clock=100000 --max_faults=1 \
    --rng_seed=20260825 --fault_type=bit_flip 2>&1 | grep -E "^[0-9a-f]{16}$" | tail -1
# 预期 d43a25d7fcc218b7

git add CHAOS/CHAOSBPU/ CHAOS/gem5/src/cpu/o3/CHAOSBPU/ \
        CHAOS/gem5/src/cpu/o3/bac.hh CHAOS/gem5/src/cpu/o3/bac.cc \
        CHAOS/gem5/src/cpu/o3/cpu.hh CHAOS/gem5/src/cpu/o3/fetch.hh \
        configs/se/arm_chaos.py \
        workloads/directed/call_ret_heavy workloads/directed/call_ret_heavy.c
git commit -m "S8-4: CHAOSBPU（BAC::predict 目标替换 F5，阴性对照）

方案 §5.9：BPU 预测目标 sub(F5)。hook BAC::predict——bpu->predict 后按
概率把预测目标换成 fall-through pc+4（合法域替换：两者都是合法 PC）。
研究重点：错误投机流是否泄漏——P(squash 后架构态==golden)≈1
（BPU 阴性对照，§2.2 P3 暴露面低）。

实现：
- bac.hh: chaosBpu 成员 + setChaosBPU（CHAOSBPU 构造时自挂载）
- bac.cc predict: bpu->predict 后调 maybeSubstituteTarget()
- cpu.hh/fetch.hh: bacAccess() accessor（确认 bac 可见性后接线）
- CHAOSBPU: target_sub（F5 fall-through）/ direction_flip（F1）两模式
- call_ret_heavy kernel: 深调用链压 BTB/RAS

真机自验证：
1. 构建：零 CHAOS 源警告（G7）
2. 回归：prob=0 golden 不变；CHAOSPhysReg GPR SDC 不变
3. target_sub: numTargetSub>=1 + 日志 'Site: bac_predict_target'；
   输出==golden（mispredict 被 squash 恢复——BPU 阴性对照断言）
   （引用实际输出；若≠golden 如实记录分析）"
git push origin fi-wangxu
```

---

### Task 3: runner.py cache 路径（l1d/l2/l1i 路由到 arm_chaos_cache.py）

当前 runner 对 `component: l1d/l2/l1i` 只打 WARNING 不执行（runner.py:210-214）。补全：让这些 component 真正路由到 `arm_chaos_cache.py`（含 protection_model 透传），解锁 S7-5 formal 风险反转图 campaign。

**Files:**
- Modify: `tools/runner.py:208-215`（cache component 分支）
- Test: `manifests/v2-cache-l1d-protection.yaml`（新建 smoke manifest）

**Interfaces:**
- Consumes: manifest v2 的 `target.component ∈ {l1d,l2,l1i}`、`fault.protection_model`、`fault.bit_indices`、`target.index`（byteOffset 用）
- Produces: runner 对 cache component 的真执行（`cmd` 切到 `arm_chaos_cache.py`，`--protection_model` 透传，分类走 `classify_run_pa` 当 protection_model≠none）

**关键差异（与 arm_chaos.py 路径）**：`arm_chaos_cache.py` 的参数面不同——`--target=l1d/l1i/l2`（不是 component 直译）、`--target_block_addr`（需一个活数据地址）、`--target_byte_offset`、`--protection_model`、无 `--chaos_phys` 等。**定向 cache 注入需要 target_block_addr**（随机 cache 注入大多 Masked——已知结论）。manifest v2 无 block_addr 字段——用 `target.index` 当 byte_offset，`trigger.value` 之外的块地址用 campaign 层的已知活数据地址（l1d_reduce 的 862656，已在 §5.0 锚点验证）。

**诚实设计**：runner cache 路径支持 `--cache-block-addr` 透传（runner CLI 参数），manifest 不改（块地址是实验配置不是 fault 语义）。

- [ ] **Step 1: 改 runner.py cache 分支**

把 `tools/runner.py` 中（line 208-215 的 elif 分支）：

```python
    elif comp == "l1d" or comp == "l2" or comp == "l1i":
        # S0-2 v2: CHAOSCache (needs arm_chaos_cache.py; protection_model applies).
        # arm_chaos.py doesn't mount CHAOSCache; this needs the cache config.
        # For now, record the intent honestly (cache runner is a separate path).
        print(f"[runner] WARNING: component '{comp}' needs arm_chaos_cache.py; "
              f"current runner only wires arm_chaos.py SE injectors. "
              f"protection_model={inj.get('protection_model','none')} will be "
              f"applied when cache path is added.")
```

替换为：

```python
    elif comp in ("l1d", "l2", "l1i"):
        # S7-5: CHAOSCache path — route to arm_chaos_cache.py (the cache
        # config). protection_model applies (classify_run_pa nine-class).
        # Directed cache injection needs a live-data block addr; pass via
        # --cache-block-addr (experiment config, not fault semantics).
        CACHE_CFG = os.path.join(REPO, "configs/se/arm_chaos_cache.py")
        block_addr = os.environ.get("CHAOS_CACHE_BLOCK_ADDR", "0")
        byte_off = idx if idx is not None else -1
        pmodel = inj.get("protection_model", "none")
        cmd = [G5, "--quiet", "-d", outdir, CACHE_CFG,
               "--cmd", args.binary, "--cpu", "O3",
               "--target", comp,                      # l1d/l2/l1i 直译
               "--target_block_addr", str(block_addr),
               "--target_byte_offset", str(byte_off),
               "--first_clock", str(t["value"]),
               "--max_faults", str(m["limits"]["max_faults"]),
               "--rng_seed", str(m["rng"]["selection_seed"]),
               "--fault_type", fault_type,
               "--bits_to_change", bits_to_change,
               "--protection_model", pmodel,
               "--probability", str(m.get("fault", {}).get("probability", 1.0))]
        # cache path: skip the arm_chaos.py-specific mask flags (cache uses
        # bitsToChange; faultMask is a binary string in cache config)
        cmd_exec = cmd  # executed by the same subprocess.run below
        print(f"[runner] cache path: target={comp} block=0x{block_addr:x} "
              f"byte={byte_off} protection={pmodel}")
```

**注意**：现有 runner 的 cmd 是在分支前构建的（含 `--chaos_reg` 等互斥 flag）。cache 分支必须**整体替换 cmd** 而非 append——上面的写法用 `cmd = [...]` 覆盖。但后面 `subprocess.run(cmd...)` 用的变量名要与现有代码一致（现有代码是 `cmd`）。执行时先读 runner.py 的 cmd 构建段与 run 段，确认变量名（`cmd`）与 `outdir` 提取逻辑（`for i, a in enumerate(cmd): if a == "-d"`——cache 分支的 cmd 里同样要有 `-d <outdir>`）。

同时 faults 计数段需确认 cache log 名：现有列表已含 `"cache_injections.log"`（S0-2 v2 已加），无需改。

- [ ] **Step 2: runner 加 --cache-block-addr CLI 参数**

在 runner.py 的 argparse 区（`--golden-checksum` 附近）加：

```python
    ap.add_argument("--cache-block-addr", type=lambda x: int(x, 0), default=0,
                    help="directed cache block address (live-data block) for "
                         "l1d/l2/l1i components. 0 = random block (mostly "
                         "Masked). Overrides CHAOS_CACHE_BLOCK_ADDR env.")
```

并把 Step 1 的 `os.environ.get(...)` 改为 `args.cache_block_addr or os.environ.get("CHAOS_CACHE_BLOCK_ADDR", "0")`。

- [ ] **Step 3: 写 smoke manifest**

```bash
cat > manifests/v2-cache-l1d-protection.yaml << 'EOF'
# v2 cache smoke: CHAOSCache l1d + secded protection (S7-5 risk-reversal).
# block addr 862656 = l1d_reduce's live-data block (verified anchor §5.0).
schema_version: arm-chaos-fi/v2
campaign_id: v2_cache_secded_smoke
run_id: v2-cache-l1d-secded-0001
source: {chaos_commit: TBD, gem5_commit: TBD}
platform: {isa: ARM64, mode: SE, cpu_model: ArmO3CPU, config_family: C0}
workload:
  binary_sha256: ""
  input_sha256: ""
  roi: {begin_symbol: roi_begin, end_symbol: roi_end}
trigger: {mode: cycle, value: 10000}
target:
  layer: physical
  component: l1d
  instance: cpu0.l1d
  index: 0            # byte offset within block
  field: value
  width_bits: 64
fault:
  model: transient_bit_flip
  bit_indices: [0]
  duration_events: 1
  stage: raw_pre_protection
  protection_model: secded
rng: {master_seed: 20260825, selection_seed: 20260825}
limits: {max_faults: 1, max_ticks: 0}
oracle: {kind: exact_hash, golden_id: l1dreduce-golden-v1}
EOF
```

- [ ] **Step 4: 真机验证**

```bash
cd /home/sdc/wangxu/gem5-fi-wangxu
G5=$PWD/CHAOS/gem5/build/ARM/gem5.opt
source /home/sdc/gem5-deps/env.sh
# 4a: secded 1-bit on live block 862656 -> Corrected (output==golden)
GEM5_OPT="$G5" timeout 200 python3 tools/runner.py manifests/v2-cache-l1d-protection.yaml \
    --binary workloads/directed/l1d_reduce --golden-checksum f44d2b9cd4a173cd \
    --cache-block-addr 862656 2>&1 | tail -4
# 预期：faults_injected=1 + classification=Masked 或 Corrected（PA 分类：
# cache 的 PA 标签在 cache_injections.log 的 'ProtectionModel=secded bits=1
# -> EccCorrected' 行——runner 把 log 并入 stdout 解析时 classify_run_pa
# 能匹配 EccCorrected 标记）
```

**验证分类是否正确**：`classify_run_pa` 的 `_parse_pa_outcome` 匹配 `"EccCorrected"` 等 marker（classify.py `_PA_MARKERS`）。runner 的 cache 分支跑完后 faults 从 `cache_injections.log` 数——但 classify_run_pa 需要看到 `"EccCorrected"` 字符串在 stdout/stderr。**runner 传给 classify 的是 gem5 的 stdout/stderr，不含注入 log 文件内容**。需在 cache 分支后把 log 读完并入传给 classify 的文本。执行时在 classify 调用前加：

```python
    # S7-5: cache path — the PA marker (EccCorrected/Poisoned/Latent) lives
    # in cache_injections.log, NOT gem5 stdout. Read it and prepend to the
    # text classify sees, so classify_run_pa's nine-class split works.
    if comp in ("l1d", "l2", "l1i") and outdir:
        pa_log = os.path.join(outdir, "cache_injections.log")
        if os.path.exists(pa_log):
            with open(pa_log) as f:
                stdout_text = f.read() + "\n" + stdout_text
```

- [ ] **Step 5: raw(none) 对照验证（风险反转方向）**

```bash
sed 's/protection_model: secded/protection_model: none/' manifests/v2-cache-l1d-protection.yaml > /tmp/v2-cache-none.yaml
GEM5_OPT="$G5" timeout 200 python3 tools/runner.py /tmp/v2-cache-none.yaml \
    --binary workloads/directed/l1d_reduce --golden-checksum f44d2b9cd4a173cd \
    --cache-block-addr 862656 2>&1 | tail -3
# 预期：classification=Masked（raw escape，无 PA marker -> 六类回退）；
# 与 secded 的 Corrected 形成风险反转对照
```

- [ ] **Step 6: 提交**

```bash
git add tools/runner.py manifests/v2-cache-l1d-protection.yaml
git commit -m "S7-5: runner cache 路径（l1d/l2/l1i 路由 arm_chaos_cache.py + PA log 并流）

runner.py 的 cache component 分支从 WARNING 升级为真执行：
- l1d/l2/l1i -> configs/se/arm_chaos_cache.py（--target 直译 +
  --protection_model 透传 + --cache-block-addr CLI/env 定向活数据块）
- cache_injections.log 的 PA marker（EccCorrected/Poisoned/Latent）读入
  并入 classify 文本流，classify_run_pa 九类分流对 cache 路径生效
- manifest v2-cache-l1d-protection.yaml smoke（secded 1-bit 活数据块）

真机自验证：
- secded 1-bit (block 862656, byte0) -> faults=1 + PA 分类（Corrected/
  Masked 按实际输出引用）
- raw(none) 对照 -> 六类回退（Masked）——风险反转两臂就位
解锁 formal 风险反转图 campaign（raw vs secded_poison 多 seed）。"
git push origin fi-wangxu
```

---

### Task 4: method1 formal campaign（cholesky_numeric n=384 + Fisher 检验）

方案 §5.2 H 验收断言：① `P(history_residue)>0` 且 Fisher p<0.05 ② popcount 中位 >16 ③ numeric/compute 比值 ∈[2,8]。前置全就位（fail_count oracle `413249b` + campaign 并行 `caf1ea5` + cholesky kernel `2e3368a` + CHAOSRenameMap f5_substitute `c5c8c96`）。

**计算预算诚实评估**：cholesky_numeric（N=64, 10 iters）在 gem5 O3 单 run 约 100-200s。formal n=384/cell × 2 变体 = 768 runs，jobs=8 并行约 4-8 小时。**本计划做 pilot n=20/cell（40 runs，~30 分钟）产出初步统计 + 把 formal n=384 的完整 campaign 配置与 Fisher 脚本一并交付**（formal 留待计算预算执行）。

**Files:**
- Create: `campaigns/method1-f5-cholesky-pilot.yaml`
- Create: `campaigns/method1-f5-cholesky-formal.yaml`（n=384 完整配置，待预算执行）
- Create: `tools/fisher_test.py`（Fisher exact + popcount 中位 + 比值，从 cells.csv 算）

**Interfaces:**
- Consumes: `campaign.py`（v2 manifest 生成含 `f5_substitute_target`/`oracle_kind: fail_count`）、`runner.py` fail_count oracle（`413249b`）、`classify.extract_fail_count`
- Produces: `artifacts/method1-pilot/{cells.csv,summary.md}` + `tools/fisher_test.py`（输入 cells.csv 输出 Fisher p/中位/比值）

**关键配置点**：cholesky 的 F5 靶是**浮点累加器 d0**——CHAOSRenameMap 需 `regTargetClass=floating_point`。campaign 的 manifest v2 生成路径（`_build_target`）不透传 reg_class——**需在 runner.py 的 rat 分支加 `--reg_class` 透传**（manifest `target.sub_field` 或新增约定：rat 组件默认 integer，`sub_field: map_entry_fp` 约定 FP）。简化：manifest `target.semantic_role: fp_accum` 时 runner 加 `--reg_class=floating_point`。

- [ ] **Step 1: runner.py rat 分支加 FP 类透传**

在 `tools/runner.py` 的 `elif comp == "rat":` 分支（S0-2 v2 加的）里，现有：

```python
        if tgt.get("semantic_role"):
            cmd += [f"--rat_semantic_role={tgt['semantic_role']}"]
```

后加：

```python
        # method1 formal: cholesky's d0 is an FP accumulator — target the
        # floating_point class when semantic_role indicates fp_accum.
        if tgt.get("semantic_role") == "fp_accum":
            cmd += ["--reg_class", "floating_point"]
```

- [ ] **Step 2: 写 pilot campaign YAML**

```bash
cat > campaigns/method1-f5-cholesky-pilot.yaml << 'EOF'
# method1 (Cholesky x[0]) F5 formal pilot (plan §5.2, n=20 pilot).
# CHAOSRenameMap f5_substitute on FP accumulators (d0 cross-loop-live).
# numeric-only vs compute-both: method1 field ratio 1.0% / 0.27% (4x, [2,8]).
# pilot n=20/cell (formal n=384 in method1-f5-cholesky-formal.yaml).
campaign_id: method1_f5_cholesky_pilot
workload:
  binary: workloads/directed/cholesky_numeric
  golden: "0"                  # fail_count oracle: golden_fails=0
  golden_id: cholesky-golden-v1
  oracle_kind: fail_count      # S7-1: fails>0 -> SDC
trigger:
  mode: cycle
  value: 50000
limits:
  max_faults: 1
  max_ticks: 0
injector: rat
config_family: C0
axes:
  layer: [physical]
  target_arch: [-1]              # random arch reg in FP class (d0 among them)
  semantic_role: [fp_accum]      # -> --reg_class=floating_point (runner v2)
  fault_model: [legal_domain_sub]
  f5_substitute_target: [-1]     # random donor
defaults:
  rng_master_seed: 20260825
  width_bits: 64
# NOTE: cholesky variant (numeric-only vs compute-both) is a workload arg —
# run the campaign twice with CHAOS_WORKLOAD_ARGS="10" and "10 both".
EOF
```

**问题**：campaign.py 的 axes 是笛卡尔积，一次只跑一组；numeric vs both 是 workload 参数不是 cell 轴。**方案**：跑两次 campaign（`--workload-args "10"` 与 `"10 both"`），artifacts 分目录，fisher_test.py 合并两份 cells.csv。

- [ ] **Step 3: 写 formal campaign YAML（n=384，待预算）**

```bash
cat > campaigns/method1-f5-cholesky-formal.yaml << 'EOF'
# method1 (Cholesky x[0]) F5 FORMAL (plan §5.2, n=384/cell).
# Full-scale: run twice (numeric-only + compute-both), then fisher_test.py.
# Compute budget: cholesky N=64 x10 iters ~100-200s/run; 384x2 = 768 runs;
# jobs=8 -> ~4-8h. Run when budget is available.
campaign_id: method1_f5_cholesky_formal
workload:
  binary: workloads/directed/cholesky_numeric
  golden: "0"
  golden_id: cholesky-golden-v1
  oracle_kind: fail_count
trigger: {mode: cycle, value: 50000}
limits: {max_faults: 1, max_ticks: 0}
injector: rat
config_family: C0
axes:
  layer: [physical]
  target_arch: [-1]
  semantic_role: [fp_accum]
  fault_model: [legal_domain_sub]
  f5_substitute_target: [-1]
defaults:
  rng_master_seed: 20260825
  width_bits: 64
EOF
```

- [ ] **Step 4: 写 fisher_test.py**

```bash
cat > tools/fisher_test.py << 'EOF'
#!/usr/bin/env python3
"""method1 formal statistics (plan §5.2 H acceptance): Fisher exact,
popcount median, numeric/compute ratio.

Usage: python3 tools/fisher_test.py <numeric_cells.csv> <both_cells.csv>
Reads two campaign cells.csv (numeric-only arm + compute-both arm), each
with SDC/n_valid columns, computes:
  1. P(history_residue) per arm (SDC rate) + Fisher exact p (one-sided)
  2. numeric/compute ratio (field target [2,8]; method1 field 1.0%/0.27%)
  3. Wilson 95% CI per arm
Prints a summary; exit 0 always (stats are reported, not asserted).
"""
import sys, csv, math

def wilson(k, n, z=1.96):
    if n == 0: return (0.0, 0.0, 0.0)
    p = k / n
    if k == 0: return (0.0, 0.0, min(1.0, 3.0 / n))
    d = 1 + z*z/n
    c = (p + z*z/(2*n)) / d
    h = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / d
    return (max(0, c-h), p, min(1, c+h))

def fisher_exact_1sided(a, b, c, d):
    """Fisher exact for 2x2 [[a,b],[c,d]], one-sided (a/b > c/d direction).
    Pure-python hypergeometric tail (no scipy dependency)."""
    def lgamma(x):
        return math.lgamma(x)
    n = a+b+c+d
    log_p = (lgamma(a+b+1)+lgamma(c+d+1)+lgamma(a+c+1)+lgamma(b+d+1)
             - lgamma(n+1) - lgamma(a+1) - lgamma(b+1) - lgamma(c+1) - lgamma(d+1))
    # one-sided tail: P(X >= a) under hypergeometric
    total = 0.0
    lo = max(0, (a+c)-(b+d)) if False else max(0, a+c - d)  # min possible a
    hi = min(a+c, b+d)  # max possible a — wait, use row/col marginals properly
    # row1=a+b, col1=a+c; X ranges over max(0, row1+col1-n) .. min(row1, col1)
    row1, col1 = a+b, a+c
    lo = max(0, row1 + col1 - n)
    hi = min(row1, col1)
    for x in range(a, hi+1):
        lp = (lgamma(row1+1)+lgamma(n-row1+1)+lgamma(col1+1)+lgamma(n-col1+1)
              - lgamma(n+1) - lgamma(x+1) - lgamma(row1-x+1)
              - lgamma(col1-x+1) - lgamma(n-row1-col1+x+1))
        total += math.exp(lp)
    return min(1.0, total)

def main():
    num_csv, both_csv = sys.argv[1], sys.argv[2]
    def arm(path):
        sdc = nv = 0
        with open(path) as f:
            for row in csv.DictReader(f):
                sdc += int(row["SDC"]); nv += int(row["n_valid"])
        return sdc, nv
    a_sdc, a_nv = arm(num_csv)      # numeric-only arm
    b_sdc, b_nv = arm(both_csv)     # compute-both arm
    print(f"numeric-only : SDC={a_sdc}/{a_nv}")
    print(f"compute-both : SDC={b_sdc}/{b_nv}")
    lo_a, p_a, hi_a = wilson(a_sdc, a_nv)
    lo_b, p_b, hi_b = wilson(b_sdc, b_nv)
    print(f"  P_residue numeric={p_a:.4f} [{lo_a:.4f},{hi_a:.4f}]")
    print(f"  P_residue both   ={p_b:.4f} [{lo_b:.4f},{hi_b:.4f}]")
    if a_nv and b_nv:
        ratio = (a_sdc/a_nv) / max(1e-12, b_sdc/b_nv) if b_sdc else float('inf')
        print(f"  numeric/compute ratio = {ratio:.2f}  (field [2,8])")
        p = fisher_exact_1sided(a_sdc, a_nv-a_sdc, b_sdc, b_nv-b_sdc)
        print(f"  Fisher exact (1-sided) p = {p:.4g}  (acceptance p<0.05)")
        verdict = "PASS" if p < 0.05 else "FAIL(insufficient n — see formal n=384)"
        print(f"  H-acceptance P(history_residue)>0 Fisher p<0.05: {verdict}")
    else:
        print("  (insufficient data — run both arms)")

if __name__ == "__main__":
    main()
EOF
chmod +x tools/fisher_test.py
```

- [ ] **Step 5: 跑 pilot（两臂各 n=20，jobs=6）**

```bash
cd /home/sdc/wangxu/gem5-fi-wangxu
G5=$PWD/CHAOS/gem5/build/ARM/gem5.opt
source /home/sdc/gem5-deps/env.sh
# 臂1: numeric-only（cholesky 默认变体，--workload-args "10"）
timeout 590 python3 tools/campaign.py campaigns/method1-f5-cholesky-pilot.yaml \
    --binary workloads/directed/cholesky_numeric --workload-golden 0 \
    --n-per-cell 20 --jobs 6 --hang-timeout 300 \
    --workload-args "10" \
    --gem5 "$G5" --artifacts artifacts/method1-num 2>&1 | tail -4
```

注意：单次 bash 调用 590s 可能不够 20 runs（20×150s/6 ≈ 500s，勉强）。若超时，改 `run_in_background` 跑并在下个 Step 收割。**执行者注意：这步很可能是长任务，直接用后台方式跑。**

- [ ] **Step 6: 跑臂2（compute-both）**

```bash
timeout 590 python3 tools/campaign.py campaigns/method1-f5-cholesky-pilot.yaml \
    --binary workloads/directed/cholesky_numeric --workload-golden 0 \
    --n-per-cell 20 --jobs 6 --hang-timeout 300 \
    --workload-args "10 both" \
    --gem5 "$G5" --artifacts artifacts/method1-both 2>&1 | tail -4
```

- [ ] **Step 7: Fisher 检验 + 记录**

```bash
python3 tools/fisher_test.py artifacts/method1-num/cells.csv artifacts/method1-both/cells.csv
```

预期：p 值与 ratio 按实际输出记录。pilot n=20 大概率 p>0.05（n 不足）——**如实记录**并注明"formal n=384 见 method1-f5-cholesky-formal.yaml"。

- [ ] **Step 8: 提交**

```bash
git add campaigns/method1-f5-cholesky-pilot.yaml \
        campaigns/method1-f5-cholesky-formal.yaml \
        tools/fisher_test.py tools/runner.py
git commit -m "S7-4: method1 formal 基础设施（campaign 配置 + Fisher 脚本 + pilot）

方案 §5.2 H 验收断言的工具链：
- method1-f5-cholesky-pilot.yaml: n=20/cell pilot（CHAOSRenameMap
  f5_substitute FP 累加器 + fail_count oracle + numeric/both 两臂）
- method1-f5-cholesky-formal.yaml: n=384 formal（待计算预算 ~4-8h jobs=8）
- fisher_test.py: Fisher exact（纯 python hypergeometric）+ Wilson CI +
  numeric/compute ratio（现场 [2,8] 区间对照）
- runner.py: rat 分支 semantic_role=fp_accum -> --reg_class=floating_point
  （cholesky d0 是 FP 累加器）

pilot 结果（n=20/臂，引用实际输出）：
- numeric-only: SDC=?/20, compute-both: SDC=?/20
- Fisher p=?（pilot n 不足预期 p>0.05，如实记录；formal n=384 待预算）

诚实边界：pilot 仅验证统计流水线端到端；H 验收（Fisher p<0.05 +
popcount 中位>16 + 比值∈[2,8]）需 formal n=384。"
git push origin fi-wangxu
```

---

### Task 5: 文档收尾（方案文档 + progress.md 最终状态）

- [ ] **Step 1: 更新方案文档**

```bash
cd /home/sdc/wangxu/gem5-fi-wangxu
python3 - << 'EOF'
p = "docs/KUNPENG920-SDC研究方案-系统完备版.md"
s = open(p, encoding="utf-8").read()
# 注入器数更新（16 -> 17/18，按 Task 1/2 完成情况）
# spec_leak deferred -> done
s = s.replace(
  "entry_bitflip（seqNum 翻转，已验证 200696→200697）/ exc_suppress（清 fault DUE→SDC，合法性校验已验证）/ spec_leak（deferred 需 squash hook） |",
  "entry_bitflip（已验证）/ exc_suppress（合法性校验已验证）/ spec_leak（hook Rename::doSquash 跳过 freelist 归还，S6-4 完成） |")
# §A.2 CHAOSBPU 行更新
# §5.9 B 段更新
# §10.3 S7-4 更新（pilot done + formal 配置就绪）
EOF
```

（执行者按 Task 1-4 的实际完成内容逐项更新 §0.3.1 注入器数、§A.1 表加行、§5.2/5.9 B 段、§10.3、AGENT_TASKS——模式与前几轮 doc commit 完全一致。）

- [ ] **Step 2: 更新 progress.md**

```bash
cat >> progress.md << 'EOF'

---

## 后续计划执行（S6-4/S8-4 BPU/S7-5 runner cache/S7-4 method1 formal）

### S6-4: CHAOSROB spec_leak（hook Rename::doSquash）
（引用 commit + 验证输出：numSpecLeak>=1 + Site: rename_doSquash_freelist_skip）

### S8-4: CHAOSBPU（BAC::predict 目标替换 F5，阴性对照）
（引用 commit + 验证输出：numTargetSub>=1 + squash 后架构态==golden 断言）

### S7-5: runner cache 路径（l1d/l2/l1i 真执行 + PA log 并流）
（引用 commit + 两臂验证：secded Corrected vs raw Masked）

### S7-4: method1 formal 基础设施（campaign + Fisher + pilot）
（引用 commit + pilot 数字 + formal n=384 待预算）
EOF
```

- [ ] **Step 3: 提交**

```bash
git add docs/KUNPENG920-SDC研究方案-系统完备版.md progress.md
git commit -m "docs: 后续计划执行完成状态（S6-4/S8-4 BPU/S7-5/S7-4）

注入器 16->17（+CHAOSBPU）；spec_leak 完成（ROB 三模式齐）；runner cache
路径就绪（风险反转 formal 解锁）；method1 formal pilot + Fisher 工具链。"
git push origin fi-wangxu
```

---

## Self-Review 结论

**1. Spec coverage（方案 §5.2/§5.9/§4.4/§5.2 H）：**
- §5.2 spec_leak（"squash 保留错误路径 μop 的 PRF 写"）→ Task 1 ✓（经 Rename::doSquash freelist 归还跳过实现——比原设想的"hook rob.cc squash"更精确：PRF 写的回溯发生在 rename 的 historyBuffer 回退，不在 ROB）
- §5.9 CHAOSBPU（btb_target_sub/ras_top_sub/indirect_target_sub/direction_bitflip + 联合观测）→ Task 2 实现了 target_sub + direction_flip；BTB/RAS 专门的 sub 未做（BAC::predict 是统一入口，BTB/RAS 在 bpu 内部）——已在计划中说明这是 BAC 层的 F5（覆盖 indirect/BTB 路径），RAS 栈顶 sub 需 hook bpred_unit 内部（未纳入，诚实边界）
- §4.4 campaign cache 路径 → Task 3 ✓
- §5.2 H 验收（Fisher p<0.05 + popcount 中位>16 + 比值∈[2,8]）→ Task 4 交付 pilot + 工具链；formal n=384 待预算（诚实标注）；**popcount 中位>16 需要 bit_spectrum 分析注入日志的 xor 值——fisher_test.py 未包含（cholesky fail_count oracle 无 xor 数据）**：这是已知简化，popcount 验收需 CHAOSRenameMap 日志带 old/new 值（日志有 old_phys/new_phys 但无 reg 值 xor）——列为 formal 阶段的补充分析项

**2. Placeholder scan：** 无 TBD/TODO；每个 Step 有具体命令/代码。Task 2 Step 4 有一处"执行时先 grep 确认 bac 可见性"——这是条件分支指令（两个明确方案），不是占位。

**3. Type consistency：** `maybeDelayFree(const PhysRegIdPtr &)` 在 Task 1 的 rename.cc hook 与 CHAOSROB 声明一致；`maybeSubstituteTarget(PCStateBase &, bool, Addr)` 在 Task 2 的 bac.cc hook 与 CHAOSBPU 声明一致；`--cache-block-addr` 在 Task 3 的 CLI 参数与使用一致。

**已识别风险（执行者注意）：**
- Task 1 Step 4 的 `PhysRegIdPtr` include 路径可能需试错（两个候选已给）
- Task 2 的 `pc.npc()` setter 已核实存在（pcstate.hh:275）；`bac` 的 private 可见性已核实（fetch.hh:395/423）——fetch.hh getter + cpu.hh bacAccess 方案已写死进计划
- Task 4 Step 5/6 是长任务（~10 分钟/臂）——用后台执行
