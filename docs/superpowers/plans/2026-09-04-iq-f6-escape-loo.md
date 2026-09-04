# IQ F6 补齐 + 逃逸集合分解 + 指纹库留一法实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 补齐方案 §5.5 CHAOSIQ 的 wake_omit/wake_phase 两个 deferred 模式（IQ 唤醒 F6 真实现）、§8.1 逃逸集合分解工具、§8.3 指纹库留一法验证。

**Architecture:** 三个独立单元。①CHAOSIQ 增加事件驱动 hook（InstructionQueue::wakeDependents 内，经 CPU 级 chaosIQ 指针——同 CHAOSLSQFwd 范式）实现"漏唤醒/延迟唤醒"；②`tools/escape_decomp.py` 聚合现有 formal cells.csv 按逃逸机理（A–F）归因分解；③`tools/loo_validate.py` 对指纹库做留一法（leave-one-out）有效性检验。①需重建 gem5 并真机验证；②③纯 Python（pytest TDD）。

**Tech Stack:** gem5 v25.1.0.1（C++ SimObject + inst_queue.cc hook）、Python 3.11（pytest）、CLAUDE.md 补丁纪律。

**Spec:** `docs/KUNPENG920-的SDC故障的微架构故障注入和规律研究的详细方案设计和需求开发实现文档.md` §5.5（IQ F6 验收③"相位敏感性曲线非平坦"）、§8.1（逃逸机理 A–F 归因）、§8.3（留一法验证——"20% SDC 事件预测来源单元，Top-3 命中率 ≥60% 即有效"）。

## 执行前必读的现状事实（已核实，2026-09-04）

1. **CHAOSIQ 现状**：`CHAOS/gem5/src/cpu/o3/CHAOSIQ/`——四模式 enum 已定义（SrcReadyBitFlip/TagSub/WakePhase/WakeOmit），但 WakePhase/WakeOmit 在 `processFault()` 走 `NOT IMPLEMENTED` 分支（CHAOSIQ.cc:159）。现有实现是 attackEvent 轮询 ROB-head 代理（IQ 内部 list 不可迭代）。
2. **wakeDependents 结构**（`inst_queue.cc:1074-1168`）：`for dest_reg → dependGraph.pop(dest_reg->flatIndex()) → dep_inst->markSrcRegReady(); addIfReady(dep_inst)`——唤醒点在 markSrcRegReady。**InstructionQueue 有 `CPU *cpu` 成员**（inst_queue.hh:385），CPU 已有 lsqFwd/addrPath 等 self-attach 指针先例（cpu.hh:504-510）。
3. **wake_omit 语义**：跳过某依赖者的 markSrcRegReady + addIfReady——该指令不被唤醒（其源永远不 ready）→ 若无人再唤醒则 Hang/重执行；**wake_phase 语义**：延迟唤醒——本次不 ready，下一次 wakeDependents 调用时补发（N 拍延迟近似）。注意 dependGraph.pop 已把依赖者摘链——omit/phase 时必须**压回链**否则依赖者永久丢失（指令卡死=Hang）。压回用 `dependGraph.push(dest_reg->flatIndex(), dep_inst)`（检查 dep_graph.hh 的 API）。
4. **逃逸分解数据源**：`artifacts/l1d-ecc/*.csv`（schema `tag,protection,bits,classification`）、`artifacts/{prf-formal,prf-readtrace-formal,m1-formal-num,m1-formal-both,h2-window,lsq-matrix}/cells.csv`（schema 含 SDC/Crash/Hang/Masked/Inactive/SimulatorError 列）。机理映射：A（RAS 范围外 raw escape）= 各 units raw none 模式的 SDC；B/C（SED ≥2-bit、≥3-bit 超 SECDED）= l1d-ecc raw-b2/b3 的非 Corrected 结局；D（PCE）= 无数据（标注）；E/F（ECC 逻辑/毒化丢失）= 无数据（标注）。
5. **指纹库现状**：`docs/paper/tables/fingerprint-library.json` 只有 lsq_fwd 一个单元（n=6）——留一法需要多单元。诚实路径：用合成多单元数据验证留一法**方法论**（工具正确性），真实多单元库扩充（需 per-run xor 收集机制）标注后续。
6. **构建纪律（memory）**：`scons -C CHAOS/gem5 build/ARM/gem5.opt -j16` 产物在**仓库根 build/**，构建后必须 `cp build/ARM/gem5.opt CHAOS/gem5/build/ARM/`；campaign 与构建绝不并行。

## Global Constraints

- 构建：`source /home/sdc/gem5-deps/env.sh && scons -C CHAOS/gem5 build/ARM/gem5.opt -j16`（禁 -j126）→ **构建后必 cp 到 canonical 路径** → 测试用 `CHAOS/gem5/build/ARM/gem5.opt`
- 提交纪律：一补丁一单元 + 真机验证引用实际输出 + `git push origin fi-wangxu` + 无 "Co-Authored-By: Claude" 尾注
- 注入器改 .cc/.hh 后需顶层同步副本到 `CHAOS/CHAOSIQ/`
- 诚实纪律：wake_omit/wake_phase 是"漏/延迟唤醒的架构级近似"（gem5 同步 IQ 的时序语义有限）——commit 与文档如实标注；逃逸分解的 D/E/F 无数据时输出"no data"而非编造
- 每 commit 前：`grep -c "warning.*CHAOSIQ" 构建输出` = 0（G7 零警告）+ reg_chain golden `f247ef3fe6f02cfd` 回归

---

### Task 1: CHAOSIQ wake_omit/wake_phase 事件驱动 hook（IQ F6 真实现）

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/cpu.hh`（加 chaosIQ 指针，~504 行 lsqFwd 旁）
- Modify: `CHAOS/gem5/src/cpu/o3/inst_queue.cc`（wakeDependents 依赖者循环 hook，~1150 行）
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSIQ/CHAOSIQ.hh/.cc`（新增 hook API + pending 列表）
- Modify: `configs/se/arm_chaos.py`（无需改动——wake 模式复用现有 --chaos_iq/--iq_mode 参数）
- Create: `workloads/directed/dep_chain.c` + 编译（wake 验证 kernel——asm 钉寄存器依赖链）
- Sync: `CHAOS/CHAOSIQ/` 顶层副本

**Interfaces:**
- Produces: `CHAOSIQ::hookWakeDependents(const DynInstPtr &dep_inst, const PhysRegIdPtr &dest_reg) -> HookAction`（enum {None, Omit, Defer}，由 inst_queue.cc 在 markSrcRegReady 前调用）；`CHAOSIQ::deliverPending(const DynInstPtr &producer)`（下一次 wakeDependents 补发延迟唤醒）；CPU 成员 `CHAOSIQ *chaosIQ`（chaosIQ 模式专用，src_ready/tag_sub 仍走 attackEvent 轮询）

**关键设计**：
- wake_omit：hook 返回 Omit → inst_queue 跳过 markSrcRegReady/addIfReady，但**必须把 dep_inst 压回 dependGraph**（`dependGraph.push(dest_reg->flatIndex(), dep_inst)`，先核实 dep_graph.hh 的 push 签名）否则依赖丢失。注：压回后该依赖者会在**下一次**同 dest_reg 完成时被再唤醒——若生产者不重写该寄存器则永不唤醒 → reg_chain 型 kernel 表现为 Hang。这正是"漏唤醒"的语义。
- wake_phase(N=1)：hook 返回 Defer → 本次压回 dependGraph（同 omit 的压回），**但把 dep_inst 记入 CHAOSIQ 的 pending 集**；下一次**任意** wakeDependents 调用时（hook 通知）补发 markSrcRegReady——一拍延迟近似。实现：CHAOSIQ::deliverPending 在每个 wakeDependents 入口被调，遍历 pending 集对仍存活的 inst 补发（用 `inst->isSquashed()` 过滤）。markSrcRegReady/addIfReady 是 DynInst/InstructionQueue 公有方法（核实 addIfReady 可见性——private 则需 friend 或经 hook 返回值让 inst_queue 代做）。

- [x] **Step 1: 核实 dep_graph push API 与 addIfReady 可见性**

```bash
grep -n "push\|pop" CHAOS/gem5/src/cpu/o3/dep_graph.hh | head -8
grep -n "addIfReady" CHAOS/gem5/src/cpu/o3/inst_queue.hh | head -3
grep -n "markSrcRegReady" CHAOS/gem5/src/cpu/o3/dyn_inst.hh | head -2
```

预期：DepGraph 有 `push(RegIndex, DynInstPtr)`；addIfReady 若 private → hook 设计改为"inst_queue.cc 代做动作，CHAOSIQ 只决策"（推荐此方案——hook 返回枚举，动作在 inst_queue.cc，避免可见性问题）。

- [x] **Step 2: CPU 加 chaosIQ 指针 + CHAOSIQ 加 hook API**

cpu.hh（lsqFwd 块旁）：
```cpp
    /** CHAOSIQ wake-hook: issue-queue wake-dependents injector (S8-1
     *  wake_omit/wake_phase F6 modes). Self-attach (ctor sets it);
     *  inst_queue.cc's wakeDependents checks it per dependent. */
    class CHAOSIQ *chaosIQ = nullptr;
    void setChaosIQ(CHAOSIQ *p) { chaosIQ = p; }
```

CHAOSIQ.hh 公有段加：
```cpp
    enum class HookAction { None, Omit, Defer };
    /** Called from InstructionQueue::wakeDependents per dependent, BEFORE
     *  markSrcRegReady. Returns Omit (skip this wakeup — dependent pushed
     *  back onto the dep graph, re-woken on the next producer completion)
     *  or Defer (same push-back, but recorded to be re-woken on the NEXT
     *  wakeDependents call — one-cycle delay approximation). */
    HookAction hookWakeDependents(const DynInstPtr &dep_inst,
                                  const PhysRegIdPtr &dest_reg);
    /** Called at the head of every wakeDependents: re-deliver (mark ready)
     *  dependents deferred by a previous call. Returns the list of insts
     *  to markSrcRegReady+addIfReady (caller performs the actions). */
    std::vector<DynInstPtr> takePendingWakeups();
```
私有段加 `std::vector<DynInstPtr> pending_wakeups;` 与 `uint64_t pending_count;`（stats）。

- [x] **Step 3: 实现 hookWakeDependents/takePendingWakeups（CHAOSIQ.cc）**

要点：仅 WakeOmit/WakePhase 模式激活（SrcReadyBitFlip/TagSub 仍走 attackEvent 轮询，**这两个模式的 attackEvent 逻辑不动**）；shouldInject 复用现有时间窗/概率/maxFaults 逻辑（醒目注释：wake_omit 是持续语义时 maxFaults 计第一次——参照 CHAOSExMon 的 persistent 先例，若单次 omit 即可观测则保留 maxFaults；执行时用 Step 6 冒烟实测决定并如实记录）；写 exmon 式证据日志到 `iq_injections.log`（含 dep_inst seqNum、dest_reg、action）。ctor 里 `cpu->setChaosIQ(this)` 仅当 mode 是 wake 类。

- [x] **Step 4: inst_queue.cc wakeDependents hook**

在 `dep_inst->markSrcRegReady(); addIfReady(dep_inst);` 处改造（动作留在 inst_queue，CHAOSIQ 只决策）：
```cpp
        while (dep_inst) {
            // S8-1 CHAOSIQ F6 hook: wake_omit (skip wakeup) / wake_phase
            // (defer to next wakeDependents — one-cycle delay). The
            // dependent is PUSHED BACK onto the dep graph so it is not
            // lost (it will be re-popped by a later producer completion).
            CHAOSIQ::HookAction act = CHAOSIQ::HookAction::None;
            if (cpu->chaosIQ)
                act = cpu->chaosIQ->hookWakeDependents(dep_inst, dest_reg);
            if (act != CHAOSIQ::HookAction::None) {
                dependGraph.push(dest_reg->flatIndex(), dep_inst);
                dep_inst = dependGraph.pop(dest_reg->flatIndex());
                // NOTE: pop after push may return the SAME inst — need
                // careful iteration; see implementation note below.
                continue;   // 动作处理见实现注意
            }
            dep_inst->markSrcRegReady();
            addIfReady(dep_inst);
            dep_inst = dependGraph.pop(dest_reg->flatIndex());
            ++dependents;
        }
```
**实现注意（执行者必读）**：push 后立刻 pop 会拿回同一 inst → 死循环。正确做法：omit/defer 时不 push 回同一链，而是**先 pop 下一个再 push 被省略者**：
```cpp
            if (act != CHAOSIQ::HookAction::None) {
                DynInstPtr skipped = dep_inst;
                dep_inst = dependGraph.pop(dest_reg->flatIndex());  // next
                dependGraph.push(dest_reg->flatIndex(), skipped);   // requeue
                if (act == CHAOSIQ::HookAction::Defer)
                    cpu->chaosIQ->recordDeferred(skipped);          // 见 Step 3
                ++dependents;
                continue;
            }
```
（`recordDeferred` 把 skipped 存入 pending_wakeups；方法名与 Step 2 的 takePendingWakeups 配套——若 Step 2 用了不同名，以 Step 2 为准统一。）
在 wakeDependents **函数入口**加 pending 补发：
```cpp
    // S8-1 CHAOSIQ: deliver wakeups deferred by a previous call
    // (wake_phase one-cycle delay approximation).
    if (cpu->chaosIQ) {
        for (auto &deferred : cpu->chaosIQ->takePendingWakeups()) {
            if (!deferred->isSquashed()) {
                deferred->markSrcRegReady();
                addIfReady(deferred);
            }
        }
    }
```
头文件 include：inst_queue.cc 加 `#include "cpu/o3/CHAOSIQ/CHAOSIQ.hh"`（核实相对路径与 include guard）。

- [x] **Step 5: dep_chain kernel（wake 验证）**

`workloads/directed/dep_chain.c`——asm 钉死寄存器依赖链（生产者→消费者链，中间无旁路）：
```c
/* S8-1 dep_chain: register dependency chain (producer -> consumer) for
 * IQ wake_omit/wake_phase verification. Each iteration: x9 = x9 + i (add),
 * checksum folds x9. A missed/deferred wakeup on the chain stalls the
 * dependent — output checksum diverges or the loop never completes. */
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>

int main(int argc, char **argv) {
    long iters = (argc > 1) ? atol(argv[1]) : 10000;
    register uint64_t acc __asm__("x9") = 0;
    register uint64_t v __asm__("x10") = 0;
    uint64_t golden = 0;
    for (long i = 0; i < iters; i++) {
        __asm__ volatile(
            "add %0, %0, %2\n"
            "add %1, %0, %3\n"     /* v depends on acc (chain) */
            : "+r"(acc), "+r"(v)
            : "r"((uint64_t)i), "r"((uint64_t)1)
            : /* no clobber */);
        golden += (uint64_t)i + 1;
    }
    uint64_t acc_out = acc, v_out = v;
    long fails = (acc_out != golden) || (v_out != golden + iters) ? 1 : 0;
    printf("iters=%ld fails=%ld acc=%016lx golden=%016lx\n",
           iters, fails, acc_out, golden);
    return fails ? 1 : 0;
}
```
编译 `gcc -static -O2 -o workloads/directed/dep_chain dep_chain.c`；native 2 次确定性（fails=0，checksum 一致）。

- [x] **Step 6: 构建 + 冒烟验证（真机）**

```bash
source /home/sdc/gem5-deps/env.sh && scons -C CHAOS/gem5 build/ARM/gem5.opt -j16 2>&1 | grep -cE "error|错误"   # 0
cp build/ARM/gem5.opt CHAOS/gem5/build/ARM/gem5.opt
G5=$PWD/CHAOS/gem5/build/ARM/gem5.opt
# 回归 1: golden 不变
$G5 --quiet -d /tmp/iq1 configs/se/arm_chaos.py --cmd workloads/directed/reg_chain --cpu=O3 2>&1 | grep -E "^[0-9a-f]{16}$"
# 回归 2: dep_chain 无注入 golden
$G5 --quiet -d /tmp/iq2 configs/se/arm_chaos.py --cmd workloads/directed/dep_chain --cpu=O3 2>&1 | grep "iters="
# 回归 3: src_ready_bitflip 旧模式不回归（用 reg_chain）
$G5 --quiet -d /tmp/iq3 configs/se/arm_chaos.py --cmd workloads/directed/reg_chain --cpu=O3 \
  --chaos_iq --iq_mode=src_ready_bitflip --probability=1.0 --first_clock=100000 \
  --max_faults=1 --rng_seed=20260825 2>&1 | tail -1
# 新功能: wake_omit（期望: dep_chain Hang 或 fails=1——依赖链断）
timeout 300 $G5 --quiet -d /tmp/iq4 configs/se/arm_chaos.py \
  --cmd workloads/directed/dep_chain --cpu=O3 \
  --chaos_iq --iq_mode=wake_omit --probability=0.01 --first_clock=10000 \
  --max_faults=1 --rng_seed=20260825 2>&1 | grep -E "iters=|^[0-9a-f]{16}$" | head -1
grep -c "wake_omit" /tmp/iq4/iq_injections.log 2>/dev/null
# 新功能: wake_phase（期望: 延迟一拍——多数情况 Masked/SDC 而非 Hang）
timeout 300 $G5 --quiet -d /tmp/iq5 configs/se/arm_chaos.py \
  --cmd workloads/directed/dep_chain --cpu=O3 \
  --chaos_iq --iq_mode=wake_phase --probability=0.01 --first_clock=10000 \
  --max_faults=1 --rng_seed=20260825 2>&1 | grep -E "iters=" | head -1
grep -c "wake_phase" /tmp/iq5/iq_injections.log 2>/dev/null
```
判定：回归 1-3 全过（golden f247ef3fe6f02cfd / dep_chain fails=0 / 旧模式行为不变）；iq4/iq5 的注入日志非零且 dep_chain 输出改变（Hang 或 fails=1 或 checksum 变）。若 wake_omit 无输出（死循环→timeout 杀），即 Hang 语义——如实记录。

- [x] **Step 7: 提交**

```bash
git add CHAOS/gem5/src/cpu/o3/cpu.hh CHAOS/gem5/src/cpu/o3/inst_queue.cc \
  CHAOS/gem5/src/cpu/o3/CHAOSIQ/ CHAOS/CHAOSIQ/ workloads/directed/dep_chain*
git commit -m "S8-1b: CHAOSIQ wake_omit/wake_phase 事件驱动实现（IQ F6 补齐）

hook InstructionQueue::wakeDependents 依赖者循环（经 cpu->chaosIQ
self-attach 指针，同 lsqFwd 范式）：
- wake_omit：跳过本次唤醒，依赖者压回 dependGraph（下次生产者完成时再唤醒）
- wake_phase：同样压回 + 记入 pending，下一次 wakeDependents 入口补发
  （一拍延迟近似——gem5 同步 IQ 时序语义的诚实边界）
- src_ready_bitflip/tag_sub 的 attackEvent 轮询路径不动
dep_chain kernel（asm 钉寄存器依赖链）验证。
（引用 Step 6 实际输出：回归 3 项 + wake 两模式的注入日志与 dep_chain 行为）"
git push origin fi-wangxu
```

---

### Task 2: 逃逸集合分解工具 `tools/escape_decomp.py`（方案 §8.1/S5-2）

**Files:**
- Create: `tools/escape_decomp.py`
- Test: `tests/test_escape_decomp.py`
- Create: `docs/paper/tables/t6-escape-decomp.md`（产出表）

**Interfaces:**
- Consumes: `artifacts/l1d-ecc/raw-b{1,2,3}.csv`（schema `tag,protection,bits,classification,faults`）、各 campaign `cells.csv`（列 `SDC,Crash,Hang,Inactive,Masked,SimulatorError,n_valid`）
- Produces: `python3 tools/escape_decomp.py --l1d artifacts/l1d-ecc --campaigns artifacts/prf-formal artifacts/m1-formal-num ... [--out docs/paper/tables/t6-escape-decomp.md]` → 机理 A–F 归因表（Markdown + CSV）。函数：`classify_escape_mechanism(unit, protection, bits, classification) -> str`（返回 "A".."F" 或 "None"）、`decompose(paths...) -> dict[mech] -> {count, share, sources}`、`render_markdown(decomp) -> str`

**机理映射（方案 §8.1 的 A–F）**：
- **A**（RAS 范围外结构 raw escape）：unit ∈ {prf, rat, freelist, rob, iq, lsq_fwd, l1_tlb…} 且 protection=none 且 classification=SDC
- **B**（SED-only ≥2-bit 静默）：protection=sed 且 bits≥2 且 classification ∈ {Masked, SDC}（l1d-ecc 无 sed 臂时 no data）
- **C**（≥3-bit 超 SECDED）：protection=secded 且 bits≥3 且 classification=SDC/Latent
- **D**（post-check escape）：CHAOSL1DForward 数据（无 → no data 诚实输出）
- **E**（ECC 逻辑自身故障）：无数据 → no data
- **F**（毒化传播丢失）：无数据 → no data
- 非 SDC 结局（Crash/Hang/Masked/Corrected/DetectedContained）单独列"非逃逸"对照行

- [x] **Step 1: 写失败测试**

```python
# tests/test_escape_decomp.py
import os, sys, csv, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

def _mk_l1d(path, tag, prot, bits, cls):
    with open(path, "a", newline="") as f:
        w = csv.writer(f)
        if f.tell() == 0:
            w.writerow(["tag","protection","bits","classification","faults"])
        w.writerow([tag, prot, bits, cls, 1])

def test_mechanism_A_for_unprotected_SDC():
    from escape_decomp import classify_escape_mechanism as c
    assert c("prf", "none", 1, "SDC") == "A"
    assert c("rat", "none", 1, "SDC") == "A"

def test_mechanism_C_for_3bit_beyond_secded():
    from escape_decomp import classify_escape_mechanism as c
    assert c("l1d", "secded", 3, "SDC") == "C"
    assert c("l1d", "secded", 3, "Latent") == "C"

def test_non_SDC_is_not_escape():
    from escape_decomp import classify_escape_mechanism as c
    assert c("l1d", "secded", 1, "Corrected") == "None"
    assert c("prf", "none", 1, "Crash") == "None"
    assert c("l1d", "secded", 2, "DetectedContained") == "None"

def test_decompose_counts_by_mechanism():
    from escape_decomp import decompose
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "raw-b3.csv")
        _mk_l1d(p, "raw-b3", "secded", 3, "SDC")    # C
        _mk_l1d(p, "raw-b3", "secded", 3, "SDC")    # C
        p2 = os.path.join(d, "raw-b1.csv")
        _mk_l1d(p2, "raw-b1", "none", 1, "Masked")  # 非逃逸
        dec = decompose(l1d_dir=d, campaigns=[])
        assert dec["C"]["count"] == 2
        assert "A" not in dec or dec["A"]["count"] == 0

def test_render_markdown_contains_rows():
    from escape_decomp import render_markdown
    md = render_markdown({"A": {"count": 10, "share": 0.5, "sources": "prf-formal"},
                          "C": {"count": 10, "share": 0.5, "sources": "l1d-ecc"}})
    assert "| A |" in md and "| C |" in md
    assert "no data" in md   # D/E/F 无数据行如实标注
```

- [x] **Step 2: 运行确认失败**

```bash
python3 -m pytest tests/test_escape_decomp.py -v 2>&1 | tail -3
```
预期：FAIL `No module named 'escape_decomp'`。

- [x] **Step 3: 实现 escape_decomp.py**

```python
#!/usr/bin/env python3
"""escape_decomp.py — SDC escape-set decomposition (plan §8.1 / task S5-2).

Attributes every SDC (and SDC-class) outcome across the formal campaigns to
one of the six escape mechanisms (§8.1 A–F), producing the paper's escape
pie-chart table. Honest: mechanisms without data (D post-check escape via
CHAOSL1DForward, E ECC-logic fault, F poison-loss) are reported as "no data".

Usage:
  python3 tools/escape_decomp.py --l1d artifacts/l1d-ecc \
      --campaigns artifacts/prf-formal artifacts/m1-formal-num [...] \
      [--out docs/paper/tables/t6-escape-decomp.md]
"""
import argparse, csv, os, sys, glob

# units whose protection baseline is "none" (N1 TRM Table 9-1 proxy §2.3):
# RAS 范围外结构 — raw fault IS the escape (mechanism A).
UNPROTECTED_UNITS = {"prf", "rat", "freelist", "rob", "iq", "lsq_fwd",
                     "l1_tlb", "l2_tlb", "exec", "fsu", "mem"}

def classify_escape_mechanism(unit, protection, bits, classification):
    """Map one outcome to §8.1 mechanism A–F, or 'None' (not an escape)."""
    if classification not in ("SDC", "Latent"):
        return "None"          # Corrected/DetectedContained/Crash/Hang/Masked: contained or DUE
    if protection == "none" and unit in UNPROTECTED_UNITS:
        return "A"             # RAS 范围外结构 raw escape
    if protection == "sed" and bits >= 2:
        return "B"             # SED-only ≥2-bit silent
    if protection == "secded" and bits >= 3:
        return "C"             # beyond SECDED
    if protection in ("secded", "secded_poison") and bits == 2:
        return "None"          # 2-bit under SECDED: contained (DetectedContained), not escape
    return "A" if protection == "none" else "None"

def decompose(l1d_dir=None, campaigns=None):
    """Tally outcomes by mechanism. l1d_dir: per-rep raw-b*.csv files;
    campaigns: cells.csv files (aggregate rows)."""
    mechs = {}
    def add(m, src):
        if m == "None":
            return
        e = mechs.setdefault(m, {"count": 0, "sources": set()})
        e["count"] += 1
        e["sources"].add(src)
    if l1d_dir and os.path.isdir(l1d_dir):
        for path in sorted(glob.glob(os.path.join(l1d_dir, "*.csv"))):
            src = os.path.basename(path).replace(".csv", "")
            with open(path) as f:
                for row in csv.DictReader(f):
                    add(classify_escape_mechanism(
                            "l1d", row.get("protection", "none"),
                            int(row.get("bits", 1)),
                            row.get("classification", "")), src)
    for camp in (campaigns or []):
        path = os.path.join(camp, "cells.csv")
        if not os.path.exists(path):
            continue
        src = os.path.basename(os.path.dirname(path))
        with open(path) as f:
            for row in csv.DictReader(f):
                for cls, col in (("SDC", "SDC"), ("Latent", "Latent")):
                    n = int(row.get(col, 0) or 0)
                    for _ in range(n):
                        add(classify_escape_mechanism(
                                src, "none", 1, cls), src)
    out = {}
    total = sum(e["count"] for e in mechs.values())
    for m in ("A", "B", "C", "D", "E", "F"):
        e = mechs.get(m)
        out[m] = {"count": e["count"] if e else 0,
                  "share": (e["count"] / total if total else 0.0),
                  "sources": ",".join(sorted(e["sources"])) if e else ""}
    return out

MECH_DESC = {
    "A": "RAS 范围外结构 raw escape（PRF/RAT/ROB/IQ/LSQ-fwd/TLB none）",
    "B": "SED-only ≥2-bit 静默",
    "C": "≥3-bit 超 SECDED",
    "D": "post-check escape（ECC 后数据通路）",
    "E": "ECC 逻辑自身故障（漏检/误纠）",
    "F": "毒化传播丢失",
}

def render_markdown(dec):
    lines = ["# SDC 逃逸集合分解（§8.1 机理 A–F）", "",
             "| 机理 | SDC 事件数 | 占比 | 数据源 |",
             "|---|---|---|---|"]
    for m in "ABCDEF":
        e = dec[m]
        if e["count"] == 0:
            lines.append(f"| {m} | no data | — | {MECH_DESC[m]} |")
        else:
            lines.append(f"| {m} | {e['count']} | {e['share']:.1%} | {e['sources']} |")
    lines += ["", "> All counts are gem5-proxy conditional outcomes, NOT FIT.",
              "> D/E/F 无 formal 数据（CHAOSL1DForward/CHAOSRAS 未跑 formal）——如实标注 no data。"]
    return "\n".join(lines)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--l1d", default="artifacts/l1d-ecc")
    ap.add_argument("--campaigns", nargs="*", default=[])
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    dec = decompose(l1d_dir=a.l1d, campaigns=a.campaigns)
    md = render_markdown(dec)
    print(md)
    if a.out:
        with open(a.out, "w") as f:
            f.write(md + "\n")

if __name__ == "__main__":
    main()
```

- [x] **Step 4: 测试通过 + 真机数据跑**

```bash
python3 -m pytest tests/test_escape_decomp.py -v 2>&1 | tail -2   # PASS
python3 tools/escape_decomp.py --l1d artifacts/l1d-ecc \
  --campaigns artifacts/prf-readtrace-formal artifacts/prf-formal \
  artifacts/m1-formal-num artifacts/h2-window \
  | tee docs/paper/tables/t6-escape-decomp.md
```
预期（基于已知数据形态）：A 机理占绝对多数（PRF X3 1536 + m1 114 + H2 的 SDC cells 合计）；l1d-ecc raw-b2/b3 的 Masked 不计入（非 SDC）；C 若 secded-b3 有 SDC 则非零、否则 no data。

- [x] **Step 5: 提交**

```bash
git add tools/escape_decomp.py tests/test_escape_decomp.py docs/paper/tables/t6-escape-decomp.md
git commit -m "S5-2: 逃逸集合分解工具（§8.1 机理 A–F 归因，t6 表）

classify_escape_mechanism（unit/protection/bits/classification → A–F）+
decompose（l1d per-rep csv + campaign cells.csv 聚合）+ render_markdown。
D/E/F 无 formal 数据如实标 no data。pytest 5 用例覆盖 A/C/非逃逸/聚合/渲染。
（引用 Step 4 实际 t6 表——A 机理计数与占比）"
git push origin fi-wangxu
```

---

### Task 3: 指纹库留一法验证工具 `tools/loo_validate.py`（方案 §8.3）

**Files:**
- Create: `tools/loo_validate.py`
- Test: `tests/test_loo_validate.py`
- Create: `docs/paper/tables/t7-loo-validation.md`（产出表）

**Interfaces:**
- Consumes: `tools/sdc_fingerprint.py` 的 `build_library(unit_masks: dict) -> dict` 与 `lookup(lib, xor) -> list[(unit, score)]`（直接 import 复用）
- Produces: `python3 tools/loo_validate.py --lib docs/paper/tables/fingerprint-library.json [--masks-file unit:masks.txt ...] [--out t7.md]`。函数：`loo_cross_validate(unit_masks: dict, topk: int = 3) -> dict`（返回 `{"top1_hit_rate", "topk_hit_rate", "n_events", "per_unit": {unit: {"n", "top1", "topk"}}}`）、`render_markdown(result) -> str`

**留一法语义（方案 §8.3）**：每个 xor 事件作为测试样本，其余事件建库（`build_library`），`lookup` 该样本 → 检查真实单元是否在 Top-K。汇总 Top-1/Top-K 命中率；方案验收线：**Top-3 命中率 ≥60% 即指纹库有效**。现有单单元库（lsq_fwd n=6）的 LOO 是平凡 100%（唯一单元必中）——诚实处理：跑真实数据（作为记录）+ 用合成双单元数据验证工具判别力（方法论检验）。

- [x] **Step 1: 写失败测试**

```python
# tests/test_loo_validate.py
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

def test_loo_perfect_library():
    from loo_validate import loo_cross_validate
    # 两个可分单元：lsq 尾数主导 vs prf 高位主导
    masks = {
        "lsq_fwd": [0x00000004, 0x00000100, 0x00000200, 0x00000001, 0x00000800],
        "prf":     [0x80000000, 0x40000000, 0x20000000, 0x10000000, 0x08000000],
    }
    r = loo_cross_validate(masks, topk=3)
    assert r["n_events"] == 10
    assert r["top1_hit_rate"] == 1.0     # 完全可分 → 100%

def test_loo_single_unit_trivial():
    from loo_validate import loo_cross_validate
    r = loo_cross_validate({"lsq_fwd": [1, 2, 3, 4]}, topk=3)
    assert r["n_events"] == 4
    assert r["top1_hit_rate"] == 1.0     # 唯一单元平凡命中（诚实标注）

def test_loo_ambiguous_library_below_one():
    from loo_validate import loo_cross_validate
    # 两个相同位谱的单元 → 不可分 → 命中率 < 1
    masks = {
        "a": [0x00000001, 0x00000002, 0x00000004],
        "b": [0x00000001, 0x00000002, 0x00000004],
    }
    r = loo_cross_validate(masks, topk=1)
    assert r["top1_hit_rate"] < 1.0

def test_render_markdown():
    from loo_validate import render_markdown
    md = render_markdown({"top1_hit_rate": 0.9, "topk_hit_rate": 1.0,
                          "topk": 3, "n_events": 10,
                          "per_unit": {"lsq_fwd": {"n": 5, "top1": 5, "topk": 5}}})
    assert "Top-3" in md and "100.0%" in md
```

- [x] **Step 2: 运行确认失败**

```bash
python3 -m pytest tests/test_loo_validate.py -v 2>&1 | tail -2
```
预期：FAIL `No module named 'loo_validate'`。

- [x] **Step 3: 实现 loo_validate.py**

```python
#!/usr/bin/env python3
"""loo_validate.py — fingerprint-library leave-one-out validation (plan §8.3).

For each observed XOR event: build the library from all OTHER events, look
up the held-out event's field mix, and check whether its true unit lands in
the Top-K candidates. Acceptance (§8.3): Top-3 hit rate >= 60% ⇒ library is
diagnostically valid. Reuses sdc_fingerprint.build_library/lookup.

Usage:
  python3 tools/loo_validate.py --lib docs/paper/tables/fingerprint-library.json \
      [--masks unit:masks.txt ...] [--top 3] [--out docs/paper/tables/t7-loo-validation.md]
"""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sdc_fingerprint import build_library, lookup   # reuse, do not rewrite

def loo_cross_validate(unit_masks, topk=3):
    """Leave-one-out over all XOR events across units.

    unit_masks: {unit_name: [xor values]}. Returns per-unit and aggregate
    Top-1/Top-K hit rates. An event whose unit is the ONLY unit in the
    remaining library still counts (trivial hit — flagged by the caller for
    single-unit libraries)."""
    events = [(u, m) for u, masks in unit_masks.items() for m in masks]
    n = len(events)
    top1_hits = 0
    topk_hits = 0
    per_unit = {}
    for i, (true_unit, xor) in enumerate(events):
        # training set: all events except this one
        train = {}
        for j, (u2, m2) in enumerate(events):
            if j == i:
                continue
            train.setdefault(u2, []).append(m2)
        if not train:
            continue   # single event total: cannot validate
        lib = build_library(train)
        ranked = lookup(lib, xor)
        names = [u for u, _ in ranked[:topk]]
        pu = per_unit.setdefault(true_unit, {"n": 0, "top1": 0, "topk": 0})
        pu["n"] += 1
        if ranked and ranked[0][0] == true_unit:
            top1_hits += 1
            pu["top1"] += 1
        if true_unit in names:
            topk_hits += 1
            pu["topk"] += 1
    return {"top1_hit_rate": top1_hits / n if n else 0.0,
            "topk_hit_rate": topk_hits / n if n else 0.0,
            "topk": topk, "n_events": n, "per_unit": per_unit}

def render_markdown(res):
    lines = ["# 指纹库留一法验证（§8.3——Top-3 命中率 ≥60% 即有效）", "",
             f"- 事件数: {res['n_events']}",
             f"- Top-1 命中率: {res['top1_hit_rate']:.1%}",
             f"- Top-{res['topk']} 命中率: {res['topk_hit_rate']:.1%}",
             "",
             "| 单元 | 事件数 | Top-1 | Top-K |",
             "|---|---|---|---|"]
    for u, pu in sorted(res["per_unit"].items()):
        lines.append(f"| {u} | {pu['n']} | {pu['top1']} | {pu['topk']} |")
    verdict = "VALID (≥60%)" if res["topk_hit_rate"] >= 0.6 else "NOT VALID (<60%)"
    lines += ["", f"**验收判定: {verdict}**",
              "> 诚实边界：当前库仅单单元（lsq_fwd）时 LOO 为平凡命中",
              "（唯一候选必中）——多单元判别力需扩充库（per-run xor 收集，后续）。"]
    return "\n".join(lines)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lib", default=None, help="existing library JSON (info only)")
    ap.add_argument("--masks", nargs="*", default=[],
                    help="unit:masks_file pairs (one hex xor per line)")
    ap.add_argument("--top", type=int, default=3)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    unit_masks = {}
    for spec in a.masks:
        unit, path = spec.split(":", 1)
        with open(path) as f:
            unit_masks[unit] = [int(line.strip(), 0) for line in f if line.strip()]
    if not unit_masks and a.lib and os.path.exists(a.lib):
        # single-unit library: LOO over it (trivial — recorded honestly)
        with open(a.lib) as f:
            unit_masks = {u: [0] * fp["n"] for u, fp in json.load(f).items()}
        print(f"[loo] WARNING: library {a.lib} has no raw masks; "
              f"single-unit trivial validation only", file=sys.stderr)
    res = loo_cross_validate(unit_masks, topk=a.top)
    md = render_markdown(res)
    print(md)
    if a.out:
        with open(a.out, "w") as f:
            f.write(md + "\n")

if __name__ == "__main__":
    main()
```

- [x] **Step 4: 测试通过 + 真机跑（真实库 + 判别力演示）**

```bash
python3 -m pytest tests/test_loo_validate.py -v 2>&1 | tail -2   # PASS
# 真实库（单单元，平凡——如实记录）
python3 tools/loo_validate.py --lib docs/paper/tables/fingerprint-library.json \
  | tee /tmp/loo-real.txt
# 判别力演示：lsq_fwd 真实 masks + 合成 prf 高位 masks（方法论检验）
grep -oE "xor=[0-9a-f]+" runs/t1_sleak2/lsq_fwd_injections.log 2>/dev/null | cut -d= -f2 > /tmp/lsq_masks.txt || \
  (for i in 1 2 3 4 5 6; do printf '%x\n' $(( (1 << (i+1)) )); done > /tmp/lsq_masks.txt)
for i in 8 9 10 11 12 13; do printf '%x\n' $((1 << i)); done > /tmp/prf_masks.txt
python3 tools/loo_validate.py \
  --masks lsq_fwd:/tmp/lsq_masks.txt prf:/tmp/prf_masks.txt \
  --out docs/paper/tables/t7-loo-validation.md
```
预期：双单元可分 → Top-3 命中 100%（VALID）；t7 表含真实 lsq + 合成 prf 的判别力数据与诚实标注。

- [x] **Step 5: 提交**

```bash
git add tools/loo_validate.py tests/test_loo_validate.py docs/paper/tables/t7-loo-validation.md
git commit -m "S5-3: 指纹库留一法验证工具（§8.3 Top-3 ≥60% 验收线）

loo_cross_validate（留一建库+lookup 判 Top-K）+ render_markdown。
复用 sdc_fingerprint 的 build_library/lookup（不重写字段分类）。
pytest 4 用例：完全可分 100%/单单元平凡/不可分 <100%/渲染。
真实库（单单元 lsq_fwd）平凡命中如实标注；双单元判别力演示（真实
lsq masks + 合成 prf 高位）验证方法论。多单元真实库扩充留后续
（需 per-run xor 收集机制）。"
git push origin fi-wangxu
```

---

### Task 4: 收尾——progress.md + 方案文档回填 + 论文 t6/t7 引用

**Files:**
- Modify: `progress.md`
- Modify: `docs/KUNPENG920-SDC研究方案-系统完备版.md`（§5.5 IQ 模式状态、§8.1/§8.3 回填）
- Modify: `docs/paper/sdc-fi-paper.md`（§5 设计建议引用 t6 逃逸分解、§6 指纹库引用 t7 LOO）

- [x] **Step 1: progress.md 追加本轮段落**（含 Task 1-3 的 commit hash 与验证输出摘要）

- [x] **Step 2: 方案文档回填**

```bash
# §5.5 IQ 行：wake_phase/wake_omit 从 "deferred" 改为已实现+commit hash
# §8.1：逃逸集合分解（t6 表产出引用）
# §8.3：留一法验证（t7 表 + Top-3 判定引用）
```

- [x] **Step 3: 论文 §5/§6 引用 t6/t7**（数字溯源到表文件）

- [x] **Step 4: 提交**

```bash
git add progress.md docs/KUNPENG920-SDC研究方案-系统完备版.md docs/paper/sdc-fi-paper.md
git commit -m "docs: IQ F6 补齐 + 逃逸分解 + LOO 验证收尾（方案 §5.5/§8.1/§8.3 回填）"
git push origin fi-wangxu
git status --short   # 预期仅剩用户手写方案文档
```

---

## Self-Review 结论

**1. 覆盖检查**：方案 §5.5 IQ wake 模式（deferred → 实现）→ Task 1；§8.1 逃逸集合分解（S5-2）→ Task 2；§8.3 留一法验证（S5-3）→ Task 3；文档回填 → Task 4。**未纳入本计划（诚实声明）**：method2 三根因区分（需 FS campaign 批量）、FS checkpoint O3-switch（深改 FS 流水线）、G6 pc/committedInst 触发器（D9）、CHAOSBPU decoupled 兼容、RAT/ROB read-trace API（H3 跨单元）——均为独立多补丁工作，超出本轮三单元范围。

**2. 占位符扫描**：Task 1 Step 3 的"执行时用冒烟实测决定 maxFaults 语义"是条件指令（两种实现的判定标准已给出）；Task 1 Step 4 的实现注意（push/pop 死循环陷阱）给出了正确代码。无 TBD。

**3. 类型一致性**：`HookAction`（enum class，None/Omit/Defer）在 Step 2 定义、Step 4 消费一致；`classify_escape_mechanism(unit, protection, bits, classification)` 与 decompose 调用一致；`loo_cross_validate(unit_masks, topk)` 与测试一致；`recordDeferred`（Step 4 实现注意中引用）需在 Step 2 的接口清单里补上——执行时以 Step 3 实现为准统一命名。

**预算**：Task 1 构建约 20 分钟 + 验证 15 分钟；Task 2/3 各约 20 分钟（纯 Python）；Task 4 约 10 分钟。总计 ~1.5 小时。
