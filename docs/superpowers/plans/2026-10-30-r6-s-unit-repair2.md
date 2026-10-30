# R6-S 单元第二轮完成 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 S 单元中已证明可修复的残留 RunID 修到 3/3，并为每个合格 seed 产出可复现、与原始流一致的传播链文档。

**Architecture:** 先以失败测试钉死语义（F0 span、S09/S03 受控终局、S10 SSIT 真实层级、S11 store containment/Crash 终局），再由唯一 C++ owner 做最小真实实现；所有 C++ 共享文件只在单一工作树内修改；一次统一构建后用新二进制重跑受影响 RunID；W1 长跑独立串行队列，不与构建并发。

**Tech Stack:** gem5 v25.1.0.1 (C++/Python), Python 3 campaign/checker tools, pytest, detached tmux, flock.

**Spec:** 用户 2026-10-30 工作令（本会话首条消息）+ `docs/gem5-fi/lsu/evidence/R6-S-UNIT-DIAGNOSIS.md` + `docs/gem5-fi/lsu/evidence/R6-S-REPAIR2-CENSUS.md`。

## Global Constraints

- 工作树：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029`，分支 `fix/r6-s-unit-completion-20261030`，起点 `8f108229`，已有提交 `fe9ca819`。
- 冻结二进制：`686458c34ab7199a07ec4a968c3bbfe40e0d7514cccc2ee0d181a68621b7cef9`；构建前复制保留，构建后新 SHA 单独记录。
- 不改 18 格 `BLOCKED_TRIGGER_REACHABILITY`、11 格 F6、3 格 W11 SPEC；不换 workload/频率/seed；不把 NO_FIRE 记 PASS；不伪造传播事件。
- 所有预计 >5 分钟任务：detached tmux、stdin `/dev/null`、日志落盘、flock、独立目录、manifest、`.done`；gem5 最大并发 2；W1 最大并发 1；scons 期间 gem5=0。
- 每个 seed 验收必须同时满足：真实注入、正常 EOF、gzip 完整、stats 非零、ancestry/parent/tick 合法、terminal 合法、admitted/certified、violations=[]、conservation OK/严格 n/a、campaign/checker 一致。
- 不提交构建产物；不 `git add -A`；只 stage 显式路径。
- 任何“只有放宽准入/挑 seed/强制注入/伪造 L5”才能通过的格，停下并报告。

## Review Focus

1. **S10 `before==after` 的含住是否真实**：必须以 `ssit_consult` 的 counterfactual/actual 两值相等为唯一依据；不得因 oracle=Masked 推断含住。
2. **S11-F0-W6 的 Crash 归因**：0x18 是下游未映射地址，不在注入注册范围；没有 taint/value 桥接就不准声称由 store 丢失引起。
3. **LSQFwd arm 的作用域**：只在真实注入后 arm guest SEGV；无注入基线的 page-table fault 仍必须 panic。
4. **F0 span 的绝对路径命令同形性**：census 必须与 campaign 的 `--cmd <abs>` 完全一致；相对路径读数不得写回表。
5. **W1 与构建互斥**：scons 前确认 `pgrep gem5` 为空；长跑用 pause 文件而不是杀进程来让路。

---

### Task 0: 现场冻结与 W1 队列（运维，不提交）

**Files:**
- Read: `/home/sdc/gem5-fi-ding-cleanup-20261029/R6-S-REPAIR2-BASELINE.tsv`
- Create: `/home/sdc/gem5-fi-ding-cleanup-20261029/R6-S-REPAIR2-PROGRESS.md`（持续更新）
- Create: `/home/sdc/gem5-fi-ding-cleanup-20261029/r6s_w1_seed.sh`（已创建）
- Create: `/home/sdc/gem5-fi-ding-cleanup-20261029/r6s_w1_queue.sh`

- [x] 核验：工作树干净、HEAD `fe9ca819`、origin/fi-ding `8f108229`、二进制 SHA `686458c3…`、进程 0、`/home` 余 51G。
- [x] 冻结 212 份文档 SHA 基线（`R6-S-REPAIR2-BASELINE.tsv`，212 行）。
- [x] 启动 W1 S13-F0-W1 seed3（tmux `r6s-w1-1`，12h 预算，manifest 已写）。
- [ ] 写 `r6s_w1_queue.sh`：串行执行 `S13-F0-W1:3 S13-F1-W1:3 S13-F2-W1:2 S13-F2-W1:3`；每次运行前检查 `R6S_W1_PAUSE` 文件，存在则等待；每个 seed 调 `r6s_w1_seed.sh`；日志落盘；完成后 `touch R6S_W1_S13_DONE`。
- [ ] 在 `R6-S-REPAIR2-PROGRESS.md` 记录：HEAD/分支/SHA/进程/队列/下一步。

### Task 1: F0 span 契约测试（无 C++，先钉死）

**Files:**
- Create: `tests/test_lsu_s_f0_span.py`
- Read: `tools/lsu_campaign.py` (`LSQFWD_F0_SPAN`, `_lsqfwd_tier_flags`)
- Read: `docs/gem5-fi/lsu/evidence/R6-S-REPAIR2-CENSUS.md`
- Read: `CHAOS/gem5/src/cpu/o3/chaos_event_sample.hh:49`

**Interfaces:**
- Consumes: `lsu_campaign.LSQFWD_F0_SPAN`, `lsu_campaign._lsqfwd_tier_flags(model, tier, wl_binary)`.
- Produces: 5 组测试函数，供后续任何 span 改动回归。

- [ ] **Step 1: 写失败测试**（完整内容）

```python
#!/usr/bin/env python3
"""F0 span 无偏标定契约：独立 census、上限、seed draw、拒绝复用、其他 tier 不受影响。"""
import re, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))
import lsu_campaign as LC

FAILED = []
def check(name, cond, detail=""):
    print(("  PASS " if cond else "  FAIL ") + name + ("" if cond else " " + str(detail)))
    if not cond: FAILED.append(name)

def lcg(x):
    return (x * 6364136223846793005 + 1442695040888963407) & ((1 << 64) - 1)

PAIRS = [("S01", "sq_forward", 6), ("S02", "sq_forward", 6),
         ("S08", "sq_forward", 1), ("S09", "sq_forward", 6),
         ("S03", "sq_forward", 7)]

def main():
    print("[1] independent campaign-form census values")
    for model, wl, expected in PAIRS:
        check(f"{model}/{wl} span == census {expected}",
              LC.LSQFWD_F0_SPAN.get((model, wl)) == expected,
              LC.LSQFWD_F0_SPAN.get((model, wl)))
    check("no pair silently reuses another pair's span",
          len({LC.LSQFWD_F0_SPAN[p] for p in PAIRS[:2]}) == 1 and
          LC.LSQFWD_F0_SPAN[("S08", "sq_forward")] != LC.LSQFWD_F0_SPAN[("S01", "sq_forward")])

    print("[2] census document agrees with the table")
    doc = (ROOT / "docs/gem5-fi/lsu/evidence/R6-S-REPAIR2-CENSUS.md").read_text()
    for model, wl, expected in PAIRS[:4]:
        m = re.search(r"\|\s*%s\s*\|\s*directed/sq_forward\s*\|\s*(\d+)\s*\|" % model, doc)
        check(f"census doc {model} = {expected}", m and int(m.group(1)) == expected,
              m.group(1) if m else "row missing")

    print("[3] seed1/2/3 draws are inside [warmup, warmup+span)")
    for model, wl, span in PAIRS:
        draws = [1 + lcg(seed) % span for seed in (1, 2, 3)]
        check(f"{model} seed draws within 1..{span}", all(1 <= d <= span for d in draws), draws)
        flags = LC._lsqfwd_tier_flags(model, "F0", wl)
        check(f"{model} F0 flags use measured span",
              flags and flags[flags.index("--lsqfwd_span_events") + 1] == str(span), flags)

    print("[4] unmeasured pair refuses loudly")
    check("unmeasured pair returns None", LC._lsqfwd_tier_flags("S01", "F0", "no_such_wl") is None)

    print("[5] F1/F2/F4/F5/F6 unaffected by the F0 table")
    for tier in ("F1", "F2", "F4", "F5", "F6"):
        flags = LC._lsqfwd_tier_flags("S01", tier, "sq_forward")
        check(f"{tier} does not consume the F0 table",
              flags and flags[flags.index("--lsqfwd_span_events") + 1] == "1000", flags)
        if tier == "F2":
            r = LC._lsqfwd_tier_flags("S10", "F2", "sq_forward")
            check("F2 unreachable pair still refuses by its own table",
                  isinstance(r, str) and "interval-tier-unreachable" in r, r)

    print("FAILED:", len(FAILED))
    return 1 if FAILED else 0

if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: 运行，确认当前通过（table 已由 fe9ca819 更新）**

Run: `python3 tests/test_lsu_s_f0_span.py`
Expected: `FAILED: 0`。若失败，说明表或 census 文档漂移，先修数据不改测试。

- [ ] **Step 3: 反向验证（临时内存修改，不写盘）**

Run: `python3 - <<'EOF'` 中把 `LSQFWD_F0_SPAN[("S01","sq_forward")]` 改为 7 后调用 `_lsqfwd_tier_flags`，确认 flags 随表变化；不改文件。

- [ ] **Step 4: 提交**

```bash
git add tests/test_lsu_s_f0_span.py
git commit -m "test(lsu): pin remaining S-unit completion semantics"
```

### Task 2: C — S09/S03 受控异常终局（LSQFwd 注入 arm guest SEGV）

**Files:**
- Modify: `CHAOS/gem5/src/base/chaos_guest_fault.hh`（加 `noteChaosInjection()`）
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc`（4 个真实注入点 + include）
- Test: `tests/test_lsu_s09_guest_fault.py`（新建）
- Test: `tests/test_lsu_s_forward_repair.py`（补负向）

**Interfaces:**
- Produces: `chaos::noteChaosInjection()`——只把 `guestSegvArmed()` 置 true，不登记 VA；`faults.cc` 现有逻辑不变。
- Consumes: `CHAOSPropagation::instance()->noteArchTranslationFault(vaddr, exact)` 不变。

- [ ] **Step 1: 写失败测试**

```python
#!/usr/bin/env python3
"""S09/S03：LSQFwd 真实注入后必须 arm 受控 guest SEGV；无注入不得 arm。"""
import re, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FAILED = []
def check(n, c, d=""):
    print(("  PASS " if c else "  FAIL ") + n + ("" if c else " " + str(d)))
    if not c: FAILED.append(n)
def src(p): return (ROOT / p).read_text(encoding="utf-8")

def main():
    h = src("CHAOS/gem5/src/base/chaos_guest_fault.hh")
    cc = src("CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc")
    check("header exposes noteChaosInjection", "noteChaosInjection()" in h)
    check("header arms guestSegvArmed without registering a VA",
          "guestSegvArmed() = true" in h)
    check("LSQFwd includes the guest-fault registry",
          '#include "base/chaos_guest_fault.hh"' in cc)
    # every real injection counter increment must be adjacent to an arm call
    for site in ("writeLog", "maybeSubstituteSource", "s10SsidSubstCb",
                 "s10ViolationCb", "violationCorrupt", "maybeSwapResponseTarget"):
        idx = cc.find(site)
        check(f"{site} exists", idx >= 0)
    check("arm call appears at least once in LSQFwd", "noteChaosInjection()" in cc)
    # negative: faults.cc keeps the handle before arming
    f = src("CHAOS/gem5/src/sim/faults.cc")
    check("page-table fault handles first, then checks armed",
          f.index("fixupFault") < f.index("guestSegvArmed()"))
    print("FAILED:", len(FAILED))
    return 1 if FAILED else 0

if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: 运行，确认失败**

Run: `python3 tests/test_lsu_s09_guest_fault.py`
Expected: `FAIL noteChaosInjection ...`（header 尚未实现）。

- [ ] **Step 3: 最小实现**

`chaos_guest_fault.hh` 在 `noteChaosAddrPathActive()` 后加：

```cpp
// [R6-S-REPAIR2 2026-10-30] Any real CHAOS fault injection (not only
// CHAOSAddrPath) can produce a wild pointer that page-table-faults in SE.
// Arm the same controlled guest-SEGV teardown at the injection site; this
// only flips the armed flag, it never registers a VA (downstream faults
// stay honestly unattributed).
inline void
noteChaosInjection()
{
    guestSegvArmed() = true;
}
```

`CHAOSLSQFwd.cc` 顶部加 include；在每个真实注入成功点（`writeLog` 的 `ptag` 非零后、`maybeSubstituteSource` 的 `++faults_injected_count` 后、`s10SsidSubstCb` 的注册后、`s10ViolationCb` 的真实注入后、`violationCorrupt` 的返回 true 前、`maybeSwapResponseTarget` 的交换成功处）调用 `chaos::noteChaosInjection();`。不得在 `count_only`/未注入路径调用。

- [ ] **Step 4: 运行测试**

Run: `python3 tests/test_lsu_s09_guest_fault.py && python3 tests/test_lsu_s_forward_repair.py`
Expected: 两者 `FAILED: 0`。

- [ ] **Step 5: 提交**

```bash
git add CHAOS/gem5/src/base/chaos_guest_fault.hh \
        CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc \
        tests/test_lsu_s09_guest_fault.py
git commit -m "fix(lsu): close S09 and S11 architectural fault streams"
```

### Task 3: D — S10 SSIT 真实层级与含住

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc`（s10 回调）
- Modify: `CHAOS/gem5/src/cpu/o3/store_set.cc`（`issued()`/`clear()` 钩子）
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc/.hh`（`noteS10*`）
- Modify: `tools/lsu_prop_fields.py`（层级/必录字段）
- Modify: `tests/test_lsu_hook_s10.py`（更新到新契约）
- Create: `tests/test_lsu_s10_ssit_chain.py`

**Interfaces:**
- `noteS10Corrupt(pc, old_ssid, new_ssid)` → `ssit_corrupt` L1。
- `noteS10Consult(pc, before, after, entry_index, ptag)` → `ssit_consult` L2；`before==after` 时同点再发 `ssit_no_effect`（L2, contained=1, outcome=contained, corr=origin）。
- `noteS10Effective(pc, before, after, ptag)` → `ssit_dep_effective` L3（仅 `before!=after`，在 `StoreSet::issued()`）。
- `noteS10Violation(pc, state_before, ptag)` → `ssit_violation` L4。
- `noteS10EpochClear(pc, ssid, ptag)` → `ssit_epoch_clear`（L1, contained=1, outcome=contained, corr=origin）仅在未消费条目被 `StoreSet::clear()` 清除时。
- 工具映射：`ssit_corrupt` L1、`ssit_consult` L2、`ssit_dep_effective` L3、`ssit_violation` L4、`ssit_no_effect` L2、`ssit_epoch_clear` L1。

- [ ] **Step 1: 写失败测试**（合成链 + 源码合同）

测试必须包含：
1. `inj→ssit_corrupt→ssit_consult(before=after)→ssit_no_effect(contained=1)` 经 `check_chain` 得 `detected_contained`，`containment_from_events` 返回 `layer=L2`、`na_layers=[L3,L4,L5]`，`check_admission(..., containment=...)` 准入。
2. `inj→ssit_corrupt→ssit_consult(before!=after)→ssit_dep_effective→ssit_violation→squash_discarded(contained=1)` 得 `detected_contained`，且 `ssit_dep_effective` 只在 `before!=after` 时允许。
3. `ssit_epoch_clear` 在 `ssit_corrupt` 后、无 consult 时给出 `layer=L1` 含住；有 consult 后仍 clear 的，含住层为 consult 层。
4. 负向：缺 fault_id/corr/parent 的 `ssit_*` 事件被 `validate_event` 或 `check_admission` 拒绝；`ssit_consult` 作为 L1 的旧映射被新测试明确拒绝（防止回退）。
5. 源码合同：`store_set.cc` 的 `issued()` 与 `clear()` 含 `chaosS10*` 钩子；`CHAOSLSQFwd.cc` 的 `s10SsidSubstCb` 调 `noteS10Corrupt`，`s10ConsultCb` 调 `noteS10Consult`，`s10ViolationCb` 调 `noteS10Violation`。
6. 计数守恒：F0/F5 的 `attempted/eligible/injected` 由现有 `lsu_campaign` 测试覆盖，新增断言 `injected == 注入日志行数`（对 S10 四格的真实运行在 Task 6 执行）。

- [ ] **Step 2: 运行，确认失败**

Run: `python3 tests/test_lsu_s10_ssit_chain.py`
Expected: 因 `ssit_corrupt` 未注册而失败。

- [ ] **Step 3: 最小实现**

在 `chaos_lsu_trigger.hh`/`store_set.cc` 现有 `chaosS10*` 全局旁新增 `chaosS10Issued`/`chaosS10Clear` 函数指针（默认 nullptr）；`StoreSet::issued()` 在 `entry->setIssued()` 成功后调用 `chaosS10Issued(issued_PC)`；`StoreSet::clear()` 在 `SSIT.clear()` 前遍历 `SSIT` 并对有效条目调用 `chaosS10Clear(pc, ssid)`（`AssociativeCache` 迭代方式按现有 `for (const auto &e : SSIT)` 用法）。`CHAOSLSQFwd` 构造/析构注册/反注册这两个指针。

在 `CHAOSPropagation` 增加 `noteStoreSetCorrupt/Consult/Effective/Violation/EpochClear`，统一走 `notePropEvt`，填 `corr=origin`（PC 键注入器自有链；不扩 CORR_VALUES）。`ssit_no_effect` 仅在 `before==after` 发射，并设 `detection_layer=L2, contained=1, outcome=contained`。

- [ ] **Step 4: 运行测试**

Run: `python3 tests/test_lsu_s10_ssit_chain.py && python3 tests/test_lsu_hook_s10.py && python3 tests/test_lsu_prop_fields.py`
Expected: 全绿；旧测试按新层级契约更新，不得删除断言。

- [ ] **Step 5: 提交**

```bash
git add CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc \
        CHAOS/gem5/src/cpu/o3/store_set.cc \
        CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc \
        CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.hh \
        tools/lsu_prop_fields.py tests/test_lsu_hook_s10.py \
        tests/test_lsu_s10_ssit_chain.py
git commit -m "fix(lsu): propagate S10 SSIT corruption to real consumers"
```

### Task 4: E1 — S11-F0-W5 真实 request-suppressed containment

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/lsq.cc`（`addReq` 空 mask 点）
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc/.hh`
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc`（sq_complete 终局）
- Modify: `tools/lsu_prop_fields.py`
- Create: `tests/test_lsu_s11_store_lost.py`

**Interfaces:**
- `noteStoreRequestSuppressed(seq, addr, old_size, reason)` → `request_suppressed` L2（fault_id 由 seq 关联；`corr=seq_primary`）。
- `noteStoreLostContained(seq, addr, reason)` → `store_lost_contained` L3（`detection_layer=L3, contained=1, outcome=contained, corr=seq_primary`，parent=sq_complete）。

- [ ] **Step 1: 写失败测试**

测试必须包含：
1. 真实形状链 `inj(L0)→addr_form(L1)→request_suppressed(L2)→sq_execute(L3)→sq_complete(L3)→store_lost_contained(L3)`：`check_chain` 得 `detected_contained`；`containment_from_events` 得 `layer=L3, na_layers=[L4,L5]`；`check_admission(..., oracle=Masked, rc=0)` 准入。
2. 负向：无 `request_suppressed`（伪造直接 L3）时 `containment_from_events` 为 None；`store_lost_contained` 缺 corr/parent 被拒；`request_suppressed` 声称有 Request（size>0）与真实 `_reqs.size()==0` 矛盾时测试失败。
3. 源码合同：`lsq.cc` 空 mask 分支在 `initiateTranslation` 前调用 `noteStoreRequestSuppressed`；`completeStore`/`sq_complete` 路径调用 `noteStoreLostContained`；两处都只在注入的 lost store（seq 命中）触发。
4. `attempted/eligible/injected` 与注入日志行数守恒。

- [ ] **Step 2: 运行，确认失败**

Run: `python3 tests/test_lsu_s11_store_lost.py`
Expected: `request_suppressed` 未注册/未发射。

- [ ] **Step 3: 最小实现**

在 `lsq.cc` 的 `pre_byte_enable.size() != size`（size==0）分支，`setMemAccPredicate(false)` 前调用新 hook，参数用 `inst->seqNum`、`_addr`、`pre_byte_enable.size()`、`"empty_byte_enable"`。在 `completeStore` 的 `sq_complete` 发射后调用 `noteStoreLostContained`。`CHAOSPropagation` 两个函数都先 `correlateRequestBySeq(seq)` 取 ptag；取不到则不发射（不猜）。

- [ ] **Step 4: 运行测试**

Run: `python3 tests/test_lsu_s11_store_lost.py && python3 tests/test_lsu_hook_lsqfwd.py`
Expected: 全绿。

- [ ] **Step 5: 提交**

```bash
git add CHAOS/gem5/src/cpu/o3/lsq.cc \
        CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc \
        CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.hh \
        CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc \
        tools/lsu_prop_fields.py tests/test_lsu_s11_store_lost.py
git commit -m "fix(lsu): close S11 store-request containment"
```

### Task 5: E2 — S11-F0-W6 Crash 归因实验与精确终局

**Files:**
- Create: `runs/lsu/r6_s_repair2/w6_probe/`（新目录）
- Modify（条件性）: `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/*`、`CHAOS/gem5/src/base/chaos_guest_fault.hh`、`CHAOS/gem5/src/sim/faults.cc`
- Create: `tests/test_lsu_s11_w6_terminal.py`

**Interfaces:**
- 若证明因果：`noteLostStoreConsumer(load_seq, addr, data, ptag)` + `noteTaintedValue(va)`，faults.cc 在 `consumeInjectedGuestVa` 失败后检查 tainted value，命中则发 `arch_translation_fault`（exact=true）。
- 若不能证明：不新增事件，新增状态 `UNATTRIBUTED_DOWNSTREAM_CRASH`，`admitted=False`，并在报告中列为外部/结构阻塞。

- [ ] **Step 1: 复跑 W6 并采集事实**

Run: `LSU_GEM5_BIN=<旧二进制> python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir runs/lsu/r6_s_repair2/w6_probe --cells S11-F0-W6 --phase trial --seed-start 1 --max-seeds-per-cell 1 --max-parallel 1 --timeout 3600`
Expected: exit 139；`run.err` 有 `downstream-unmapped address 0x18`；`prop_evt` 5 事件。

- [ ] **Step 2: 判定是否存在 lost-store consumer**

检查同一 run 的 LSQ 事件/调试流中是否有 load 访问 `0x4903e8` 且其数据为 `0x18`。若无，直接进入 Step 4（不可归因）。

- [ ] **Step 3: 若有真实 consumer，写失败测试并实现 taint 桥**

测试要求：`inj→addr_form→request_suppressed→lost_store_consumer(load seq)→taint_reg→guest_segv(value=0x18)` 连续、`arch_translation_fault` 的 corr 非空、oracle=Crash、`admitted=True`。实现只填真实字段，不硬编码 0x18。

- [ ] **Step 4: 若无真实 consumer，写不可归因测试**

```python
check("W6 has no arch_translation_fault", no such kind)
check("W6 crash address is not in the injected range", True)
check("W6 admission remains False", True)
check("W6 status is UNATTRIBUTED_DOWNSTREAM_CRASH", True)
```

- [ ] **Step 5: 提交（仅当有代码/测试变化）**

```bash
git add tests/test_lsu_s11_w6_terminal.py <implementation files>
git commit -m "fix(lsu): attribute S11 downstream crash only with real taint evidence"
```

### Task 6: 统一构建

**Files:**
- Create: `/home/sdc/gem5-fi-ding-cleanup-20261029/r6s-build-20261030b.log`
- Create: `/home/sdc/gem5-fi-ding-cleanup-20261029/r6s-binary-sha256-b.txt`

- [ ] **Step 1: gem5 归零**

Run: `pgrep -af 'gem5|scons'` → 空；若 W1 队列在跑，`touch /home/sdc/gem5-fi-ding-cleanup-20261029/R6S_W1_PAUSE`，等当前 seed 的 `.done` 或 12h 预算结束后再构建。

- [ ] **Step 2: 保留旧二进制**

Run: `mkdir -p /home/sdc/gem5-fi-ding-cleanup-20261029/binaries && cp -p CHAOS/gem5/build/ARM/gem5.opt /home/sdc/gem5-fi-ding-cleanup-20261029/binaries/gem5.opt-686458c3 && sha256sum ...`

- [ ] **Step 3: detached tmux 单次 scons**

```bash
tmux new-session -d -s r6s-build "bash -c 'exec </dev/null; cd /home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029/CHAOS/gem5 && scons -j16 build/ARM/gem5.opt > /home/sdc/gem5-fi-ding-cleanup-20261029/r6s-build-20261030b.log 2>&1; echo \$? > /home/sdc/gem5-fi-ding-cleanup-20261029/r6s-build-20261030b.rc'"
```

- [ ] **Step 4: 验证**

Run: `tail -50 r6s-build-20261030b.log`；`grep -c 'warning:'` 与基线比较；`sha256sum CHAOS/gem5/build/ARM/gem5.opt`；记录 source HEAD。

- [ ] **Step 5: golden reg_chain**

Run: 按既有 golden 命令（`runs/lsu/r6_golden_verify` 的脚本）执行；Expected: `exit: pass`，SHA 与冻结 golden 一致。

### Task 7: 定向回归 + 完整非 slow 回归

**Files:**
- Create: `/home/sdc/gem5-fi-ding-cleanup-20261029/r6s-regress-20261030b.tsv`

- [ ] **Step 1: 定向测试**

Run:

```bash
python3 tests/test_lsu_s_f0_span.py
python3 tests/test_lsu_s09_guest_fault.py
python3 tests/test_lsu_s_forward_repair.py
python3 tests/test_lsu_s10_ssit_chain.py
python3 tests/test_lsu_hook_s10.py
python3 tests/test_lsu_s11_store_lost.py
python3 tests/test_lsu_s11_w6_terminal.py
```

Expected: 全部 `FAILED: 0` / pytest pass。

- [ ] **Step 2: 完整非 slow 回归**

Run: `LSU_GEM5_BIN=<新二进制> python3 -m pytest tests -q --ignore=tests/test_lsu_r6_reconcile_realroot.py -m 'not slow'`
Expected: NEW FAIL=0；既有环境性失败逐项列出并与 pristine 基线比对。

### Task 8: 按范围补跑（新二进制）

**Files:**
- Create: `runs/lsu/r6_s_repair2b/`（全新目录树）
- Create: `runs/lsu/r6_s_repair2b/manifests/`

- [ ] **Step 1: 短跑批次（gem5 并发 2）**

RunIDs（每格 3 seed，全新目录，新 span/新二进制）：
`S01-F0-W5`、`S02-F0-W5`、`S08-F0-W5`、`S09-F0-W5`、`S03-F5-W5`、`S03-F5-W10`、`S10-F0-W5`、`S10-F0-W9`、`S10-F5-W5`、`S10-F5-W9`、`S11-F0-W5`（`S11-F0-W6` 按 Task 5 结论）。

Run:

```bash
LSU_GEM5_BIN=<new> python3 tools/lsu_campaign.py \
  --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv \
  --outdir runs/lsu/r6_s_repair2b/<RunID>_s<N> \
  --cells <RunID> --phase trial --seed-start <N> --max-seeds-per-cell 1 \
  --max-parallel 1 --timeout 3600
```

- [ ] **Step 2: 每 seed 验收**

逐 seed 检查 Task 14 清单（真实注入/EOF/gzip/stats/ancestry/terminal/admitted/certified/violations/conservation/campaign-checker 一致）。任一失败记 FAIL，不记 PASS。

- [ ] **Step 3: 不合格时只修真实根因**

不得改 admission、不得挑 seed、不得强制注入。若结构不可能，转 `BLOCKED_TRIGGER_REACHABILITY` 或 `UNATTRIBUTED_DOWNSTREAM_CRASH` 并保留证据。

### Task 9: W1 剩余 seed 与 F0-W1 census

**Files:**
- Create: `runs/lsu/r6_s_repair2/w1/`（已在用）
- Create: `/home/sdc/gem5-fi-ding-cleanup-20261029/R6S_W1_QUEUE.log`

- [ ] **Step 1: S13 四 seed**

队列串行：`S13-F0-W1:3`、`S13-F1-W1:3`、`S13-F2-W1:2`、`S13-F2-W1:3`；每 seed 12h 预算、独立目录、manifest、`.done`；完成后 `R6S_W1_S13_DONE`。

- [ ] **Step 2: S01/S02 F0-W1 census（无注入）**

Run: `python3 tools/lsu_census_w1_span.py --model S01 --carrier mibench/bin/w1_all`（参数以 `--help` 为准），绝对路径命令与 campaign 同形；记录 eligible/首末 tick/动态指令范围；对 S02 重复。

- [ ] **Step 3: 写回 span 并重跑 3 seed**

把 census 值写入 `LSQFWD_F0_SPAN[("S01","mibench/bin/w1_all")]` 与 S02 行（值 ≤ census）；在全新目录跑 seed1/2/3；不得与旧配置 seed 混成 3/3。

- [ ] **Step 4: 12h 未完成**

保留现场，记录 simTicks/事件数/瓶颈；不记 PASS；报告实际进度。

### Task 10: 传播链文档与索引

**Files:**
- Modify: `runs/lsu/R6_COMPLETE_PROPAGATION_PATHS/<RunID>/<RunID>-seedN.md`
- Modify: `runs/lsu/R6_COMPLETE_PROPAGATION_PATHS/INDEX.md`、`INDEX.json`
- Modify: `runs/lsu/RESULTS/CATALOG.tsv`、`RESULTS/INTERNAL-CATALOG.tsv`、`RESULTS/EVIDENCE/<RunID>/seedN`
- Modify: `runs/lsu/r6_reports/R6-S-UNIT-STATUS.json`、`R6-S-UNIT-FINAL-REPORT.md`
- Modify: `/home/sdc/gem5-fi-ding-cleanup-20261029/R6-S-REPAIR2-PROGRESS.md`

- [ ] **Step 1: 生成 seed 文档**

沿用现有八章格式，逐 seed 从自身 `prop_evt.txt.gz` 重推 event_id/parent/tick/ancestry；写注入位置/地址/原值新值/mask/每步 consumer/终局原因/guest 表现/证据路径与 SHA/复现命令/诚实边界。

- [ ] **Step 2: 审计**

Run: `python3 tests/test_lsu_s_prop_docs.py`（及索引/链接测试）
Expected: 文档与原始流一致；T=83/A=90 SHA 不变；既有 39 份 S 文档若不受配置影响 SHA 不变；无顶层 seed 文档；软链接有效；RESULTS 断链=0。

### Task 11: 提交、推送、整合、部署

- [ ] **Step 1: 分单位提交**（每条前跑对应测试）

1. `test(lsu): pin remaining S-unit completion semantics`
2. `fix(lsu): calibrate reachable F0 spans`（fe9ca819 已存在；若 census 新增 W1 行则本提交）
3. `fix(lsu): close S09 and S11 architectural fault streams`
4. `fix(lsu): propagate S10 SSIT corruption to real consumers`
5. `fix(lsu): close S11 store-request containment`
6. `docs(lsu): complete remaining repairable S-unit evidence`

- [ ] **Step 2: 推送**

`git push origin fix/r6-s-unit-completion-20261030`（非 force）。

- [ ] **Step 3: 干净工作树整合**

在干净合并工作树（非主工作树）`git merge --no-ff origin/fi-ding` 前先 `git fetch`；确认远端无意外分叉；合并后在新二进制上复跑定向测试与文档审计。

- [ ] **Step 4: 原子部署主路径**

临时目录验证后原子替换；保留旧证据身份；记录最终 origin/fi-ding SHA 与部署状态。

---

## Self-Review

**Spec coverage:**
- F0 span 无偏 census/上限/seed draw/未标定拒绝/不复用/其他 tier 不受影响 → Task 1（真实值 6/6/1/6、S03 7；seed draws 1..span）。
- W1 补 seed → Task 0/9。
- S09/S03 截断 → Task 2（arm + 现有 faults.cc 终局；完整 EOF/stats；负向测试）。
- S10 四格 → Task 3（L0-L5 真实层级；no-effect containment；violation/replay/epoch/fan-out 测试）。
- S11 两格 → Task 4/5（W5 request-suppressed containment；W6 仅真实 taint 归因，否则不可归因）。
- 3/3、文档、回归、构建、提交、推送、合并、部署 → Task 6-11。
- 不处理 18/F6/W11 → Global Constraints + Task 8 Step 3。

**Placeholder scan:** S11-W6 是条件分支，但两个分支都有具体实现/测试；无 TBD/TODO。

**Type consistency:** `noteChaosInjection`、`ssit_corrupt/consult/dep_effective/violation/no_effect/epoch_clear`、`request_suppressed/store_lost_contained` 在测试、工具映射与 C++ 任务间一致。

**Review Focus coverage:** 每个 Review Focus 行都有对应测试（Task 3 no-effect、Task 5 W6、Task 2 no-injection panic、Task 1 absolute census、Task 6/0 构建互斥）。
