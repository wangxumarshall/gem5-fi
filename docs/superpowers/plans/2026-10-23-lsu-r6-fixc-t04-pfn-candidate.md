# R6-FIXC — T04 `pfn_to_mapped_page` 候选谓词修复（CHAOSArmTLB）

**日期**: 2026-10-23 · **分支**: `r6-fixc` · **基线**: `07c004e5`
**独占路径**: `CHAOS/gem5/src/arch/arm/CHAOSArmTLB/*`
**禁止改动**: `CHAOSPropagation/*`、`tools/**`、`src/arch/arm/mmu.cc`；不 push 集成分支。

## 根因（冻结二进制上 2 lane 各 3/3 复现）

`CHAOSArmTLB.cc:427` 的候选过滤只有
`&(*it) != entry && it->pfn != entry->pfn`，**缺 `it->valid`**。
TLB 表中大量 **invalid / stale 槽位 pfn==0** 通过过滤并主导候选集合
（真机日志 `candidates: 31`），`rng()%N` 抽中 pfn=0 → `new_pfn=0x0` →
PA 变 `0xfa8` → guest level-0 翻译故障 → 内核 Oops（`outcome=Crash`）。
即实际产出"错页 + 崩溃"，而非规格书 §2.10 F5 所述"静默读到错误的**活页**"
—— 属**故障模型保真度**缺陷。

## 目标

候选谓词至少要求 `valid`，并核验**页大小一致**（`pAddr(va)=(pfn<<N)|(va&size)`，
N 不同则 PA 位移不一致）、**映射状态**、**实验要求的地址关系**（必须换到
**另一个** live 物理帧、不得为 0）。且同一 VA 多候选时选择规则确定、可复现。

## 设计：单一谓词，无漂移

新增自包含头 `CHAOSArmTLB/chaos_tlb_pfn.hh`（零 gem5 依赖，仅 `<cstdint>`），
定义候选的 **view** 与谓词；`CHAOSArmTLB.cc` 与独立单测**共用同一份逻辑**
（防漂移）。谓词（`isSelectablePfnTarget(hit, cand)`）：

1. `!cand.is_hit_entry` —— 不得替换为自身；
2. `cand.valid` —— **映射状态**：仅 live 表项（排除 stale/invalid 槽）；
3. `cand.pfn != 0` —— **不得再选中 stale/invalid 的 PFN 0**；
4. `cand.page_size_bits == hit.page_size_bits` —— **页大小一致**；
5. `cand.pfn != hit.pfn` —— **地址关系**：必须换到不同物理帧。

选择规则 `selectPfnCandidateIndex(count, draw)` = `draw % count`，
对固定 `rngSeed` 确定可复现（保持原 `rng()` 抽取以维持候选多样性）。

## 任务（一 patch 一 commit）

- [x] **T1** 加 RED 测试：`tests/test_lsu_tlb_pfn_candidate.py`（编译并运行
  `tests/chaos_tlb_pfn_candidate_test.cc`），断言：invalid/stale/pfn=0 被排除；
  合法 live mapping 被选中；页大小不一致被排除；选择确定可复现；
  且 `CHAOSArmTLB.cc` 真正调用 `isSelectablePfnTarget(`（防漂移守卫）。
  先跑 → **真实 FAIL**（头文件/逻辑不存在）。
- [x] **T2** 实现 `chaos_tlb_pfn.hh` + 改 `CHAOSArmTLB.cc` 候选循环使用谓词 →
  RED 转 **真实 PASS**。（并修正头文件自足性：补 `#include <cstddef>`
  —— `size_t` 原仅靠 gem5 头传递，独立编译下 `error: 'size_t' 不是一个类型名`）
- [x] **T3** 构建 `scons -j16 build/ARM/gem5.opt`（全机仅一个构建），
  零新增告警（`-Wall -Wextra`；本文件原有告警基线不得增加）。
- [x] **T4** 回归：`python3 tests/test_lsu_hook_tlb.py`、
  `tests/test_lsu_hook_tlb_observation.py`、`python3 tools/lsu_test_runner.py`
  （基线 FAIL=13，NEW FAIL=0）。**不跑 pilot**。
- [x] **T5** 记录 `new_pfn` 取值域变化（见下），提交 `[LSU][MDSPEC][R6-FIXC]`
  并 push `r6-fixc`。

## 验证命令（真实执行，引用真实输出）

```
g++ -std=c++17 -Wall -Wextra -Werror -I CHAOS/gem5/src \
    tests/chaos_tlb_pfn_candidate_test.cc -o /tmp/tlb_pfn_test && /tmp/tlb_pfn_test
python3 tests/test_lsu_tlb_pfn_candidate.py
python3 tests/test_lsu_hook_tlb.py
python3 tests/test_lsu_hook_tlb_observation.py
python3 tools/lsu_test_runner.py
cd CHAOS/gem5 && scons -j16 build/ARM/gem5.opt
```

## `new_pfn` 取值域变化（T5 记录）

- 修复前：候选集 ⊇ stale/invalid（pfn==0）槽 → `new_pfn ∈ {0} ∪ {live pfn}`，
  真机实际收敛到 **0x0**（3/3 seed）。
- 修复后：`new_pfn ∈ {live, 非零, 同页大小, 且 != old_pfn 的 pfn}` ——
  故障语义回到"静默读到**另一个活页**"，消除 level-0 翻译故障/内核 Oops 这一
  非规格结局。

## 未决风险

- 若某 TLB 中不存在同页大小的其它 live 表项 → 诚实 no-op（不消耗预算、
  不注册节点），与文件内 T05/T06 家族口径一致。
- 真机 FS 复验由调度方统一重跑（本 lane 不跑 pilot）。
