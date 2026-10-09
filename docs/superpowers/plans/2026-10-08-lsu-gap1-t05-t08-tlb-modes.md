# LSU 17-缺口 Group 1：T05-T08 TLB 模式注入器实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 MODEL_BLOCKED 中 4 个 TLB 模式缺口模型（T05 状态 / T06 换值 / T07 way-select / T08 walk-refill 时序），扩展既有 CHAOSArmTLB 四件套，解除 15 个矩阵 cell 的模型级阻塞（campaign 接线延后到波次 5 结束后的受控窗口）。

**Architecture:** 在现有 CHAOSArmTLB 的 FaultType 枚举上追加 14 个扁平值（子模型=fault_type 字符串，沿用 T03 stuck0/stuck1 先例）；T05/T06/T07 走既有 lookup 命中钩子（tlb.cc:167-171），其中 T07-a 假命中需要钩子返回值契约扩展（void→bool）；T08 走 TLB::insert 顶部新钩子（tlb.cc:260），注入器自持 last_insert 走历史。配置面只在 configs/se/arm_chaos_fs.py 的 --tlb_fault_type choices 追加。**回归安全不变量：非 T08 模式在 insert 钩子为纯无操作（零 RNG/零状态），非 T07 模式从 maybeCorrupt 恒返回 false——既有 T01-T04/T10 的 RNG 流与行为字节不变（以同 seed T01 注入日志逐字节比对证明）。**

**Tech Stack:** vendored gem5 v25.1.0.1（CHAOS/gem5/src，C++17 + SCons + py3.9）；configs/se/arm_chaos_fs.py（FS 配置，被 configs/fs/lsu_b0_fs.py 薄壳 exec）；集群 login01 守卫构建（tools/lsu_guard.py，-j8 单实例）。

**Spec:** docs/gem5-fi/lsu/完整任务执行清单.md 模型表 T05-T08 行（权威子模型语义，2026-10-08 已提取入本计划 Task 表）；tools/lsu_campaign.py MODEL_BLOCKED（缺口原因）；docs/gem5-fi/lsu/findings.md F-009（17 缺口构成与 85 ITEM 普查）。

## Global Constraints

- 分支 fi-ding；提交前缀 `[LSU][P1]`（P1 功能完备性工作）；**提交信息不得以 Co-Authored-By 尾注结尾**（CLAUDE.md 覆盖默认署名）。
- **一补丁一单元**：Task 1-5 各一个 commit；不顺手捆绑无关改动。
- **波次 5 引擎冻结（F-023）**：全程不得修改 tools/lsu_campaign.py、tools/lsu_unit_pilot.py、tools/lsu_runner.py。T05-T08 的 MODEL_FLAGS/MODEL_BLOCKED 接线属"campaign 接线"，在六条安全边界满足后独立执行，不在本计划内。
- **编译纪律**：一切重建走 `python3 tools/lsu_guard.py run --type build --desc <str> --log <PATH> -- scons -j8 ...`（启动前无 scons/make/gcc/cc1plus 进程树；login01 实测全量 ~1h，增量 ~分钟级）；编译产生任何新 warning 即失败。
- **实验纪律**：FS 验证 run 走守卫 experiment 槽（并发 1）；门禁 MemAvailable≥12GiB；单 run 守卫 --max-seconds 1800（G0-09 绝对上限）。
- **诚实性**：无合法替换目标时诚实 no-op（沿用 PfnToMappedPage 先例：不计数、不伪造）；未执行不得声称已执行；每 Task 的验证输出必须真实引用。
- **二进制身份**：本工作改变集群本地 build/ARM/gem5.opt（fp 随之变化，draft 的 fp 隔离机制天然分层）；旧机二进制/census 基线不受影响（旧机不重建即无变化）。
- py3.9 语法（login01）；C++ 警告零新增（-Wswitch 全覆盖等）。

## Context（为什么是这个计划）

- 17 缺口普查（2026-10-08，矩阵 337 RunID 实测）：消费侧 6 模型 40 cell（S10/L04/C11/C12/C14/C15）、无干净钩子 4 模型 21 cell（A07/P06/O04/O09）、TLB 模式 4 模型 15 cell（T05-T08）、多核 3 模型 9 cell（O05-O07，本就 workload-blocked，随 DR-001）。合计 85，与 F-009 一致。
- 分组推进：Group 1 = T05-T08（本计划，最自含、规格完备、集群有 B0 checkpoint runs/fs_lsu/boot_b0/cpt.237949797015 + tlb_probe.rcS 载体可全功能验证）；Group 2/3/4 各自独立成计划（writing-plans 规范：独立子系统分计划）。
- KEY_RUNIDS 完整性核验（2026-10-08）：draft 常量与 task_plan.md:23 冻结 21 项名单 21/21 严格一致（含累计语义）。
- 集群侧此前从未跑过 FS（仅 SE census）；Task 0 先以未修改二进制打通 FS 管线，失败则先修基础设施再开发。

## 权威子模型规格（清单提取）

| 模型 | 单元 | 类型 | 子模型 | 频率 | 负载 |
|---|---|---|---|---|---|
| T05 | L1d-TLB | 状态 | a valid清零；b valid伪置位；c global位翻转；d ASID替换 | F0/F2/F6 | TLB-AliasPerm 探针（tlb_probe.rcS） |
| T06 | L1d-TLB | 换值 | a permission替换；b memory type替换；c page size替换 | F0/F2/F6 | 同上 |
| T07 | L1d-TLB | 状态 | a false hit；b double hit；c wrong-way选择 | F0/F4/F6 | 同上 |
| T08 | L1d-TLB | 时序 | a walk/fill丢失；b walk/fill重复；c done过早；d 旧walk结果写入 | F0/F4/F6 | 同上 + GAP/Graph500（workload-blocked 部分） |

TlbEntry 可突变字段（pagetable.hh:234 起，已核）：`pfn/size/vpn/attributes/lookupLevel/asid/vmid/tg/N/innerAttrs/outerAttrs/ap/hap/domain/mtype/longDescFormat/global/valid/ns/ss/ipaSpace/regime/type/partial/nonCacheable/shareable/outerShareable/xn/pxn/xs`。

## 设计决策（含理由）

1. **扁平枚举而非"模型+子模式"参数**：T03 先例（stuck_at_zero/stuck_at_one 是两个 fault_type 值，campaign 按 seed 奇偶交替）；零新参数面，campaign 侧接线自然。
2. **合法替换从活表项取材**（T05-d/T06 全部/T07-b）：复用 PfnToMappedPage 的 entryTable() 候选模式——替换值合法-by-construction，不手工编码 AP/mtype 合法集。
3. **T07-a 假命中 = 钩子返回 true，调用点置 retval=nullptr**：tlb.cc:167-171 现场已确认 retval 为空后续优雅（miss 统计/DPRINTF 三元保护）；F6Notify TlbHit 事件自动不触发（假命中=无命中事件，语义正确）。
4. **T08 走 insert 顶部钩子**：TLB::insert(tlb.cc:260) 是 victim 写入的唯一入口（multiInsert 也经它）；钩子返回 true = 丢弃本次 insert（T08-a）。
5. **last_insert 走历史仅在 T08 模式激活时更新**（门控前更新，保证"上一条 walk"语义）；非 T08 模式 insert 钩子零副作用。
6. **T08-c 与 T08-d 区分**：c=元数据陈旧（attributes/lookupLevel/inner/outer 取自上一 walk，pfn 保留新值）；d=翻译陈旧（c 的字段+pfn 一并取旧值）；两者 vpn/asid 均保留当前（保证 insert 落位当前 lookup 槽位、旧翻译对当前请求生效——"旧 walk 结果写入"的字面语义）。
7. **T07-b double hit 与 T07-c wrong way 区分**：b 要求存在同 vpn 异表项（真别名，tlb_probe 别名负载会制造；无候选=诚实 no-op）；c 随机任取他表项。
8. **枚举只追加不重排**：Random 模式经 discrete_distribution{0.9,0.05,0.05} 的 int 强转 BitFlip/StuckAtZero/StuckAtOne=索引 0/1/2，重排会改变 random 模式语义。

## 公共命令模板（各 Task 引用，不重复展开）

**FS 验证 run（守卫封装）**：

```bash
mkdir -p /tmp/gap1/<tag>
python3 tools/lsu_guard.py run --type experiment --desc "gap1-<tag>" \
  --log runs/lsu/guard/gap1_<tag>_rsrc.log --max-seconds 1800 -- \
  build/ARM/gem5.opt --outdir /tmp/gap1/<tag> configs/fs/lsu_b0_fs.py \
  --kernel gem5-fs/vmlinux --disk gem5-fs/ubuntu.img --bootloader gem5-fs/boot.arm64 \
  --cpu O3 --readfile configs/fs/tlb_probe.rcS --ckpt-first-clock \
  --restore-checkpoint runs/fs_lsu/boot_b0/cpt.237949797015 --lsu_b0 <INJ>
```

- golden：`<INJ>` 为空。
- 注入：`<INJ>` = `--chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type <MODE> --tlb_rng_seed 20261008`（campaign armtlb 旗标集复刻，lsu_campaign.py:294-302）。
- 判定材料：`/tmp/gap1/<tag>/console.txt`（`[tlb_probe.rcS] <md5> rounds ok=N/10` oracle 行）与 `/tmp/gap1/<tag>/armtlb_injections.log`（注入证据）。
- 预期 oracle 基线 md5 = `b6d81b360a5672d80c27430f39153e2c`（TLB_PROBE_GOLDEN）。

**守卫增量重建**：

```bash
python3 tools/lsu_guard.py run --type build --desc "gap1-<task>-rebuild" \
  --log runs/lsu/guard/gap1_<task>_build.log -- \
  scons -C CHAOS/gem5 -j8 build/ARM/gem5.opt
```

（repo-root build/ARM 经 CHAOS/gem5/build/ARM 符号链接；全程增量，不删 build——E-006 教训仅在删后适用。）

**T01 回归字节等比对**：

```bash
diff /tmp/gap1/t0_t01/armtlb_injections.log /tmp/gap1/<tag>/armtlb_injections.log \
  && echo "T01-REGRESSION-IDENTICAL"
```

（同 seed、fault_type bit_flip；新二进制下 T01 日志须与 Task 0 基线逐字节一致——证明枚举追加与钩子契约扩展未扰动既有模式。）

---

### Task 0: 集群 FS 管线基线（无代码变更，无 commit）

**Files:** 无修改；产物 /tmp/gap1/t0_golden、/tmp/gap1/t0_t01、runs/lsu/guard/gap1_t0_*.log。

**Interfaces:**
- Produces: T01 基线注入日志 `/tmp/gap1/t0_t01/armtlb_injections.log`（全部后续 Task 的回归比对基准）；集群 FS 单 run 实测时长；golden oracle 复现证据。

- [x] **Step 0.1: golden run（无注入）**——公共模板 tag=t0_golden，INJ 为空。预期：console.txt 出现 `[tlb_probe.rcS] b6d81b360a5672d80c27430f39153e2c rounds ok=10/10`；记录 wall 时长。若 md5 不符或 ok<10：**停止**，诊断（checkpoint/disk/rcS 路径、py3.9 面），修复后重跑——FS 管线不通则整个计划不开始。
- [x] **Step 0.2: T01 注入基线 run**——tag=t0_t01，fault_type=bit_flip。预期：armtlb_injections.log 恰 1 行注入记录（Tick/Site/VA/old_pfn/new_pfn/FaultType: bit_flip/Mask）+ 1 行 protection（model=none→Raw）；oracle 行可分类（Masked/SDC/Crash 均合法，如实记录）。
- [x] **Step 0.3: 记录**——实测时长与 oracle 结果记 progress.md（随 Task 1 commit 入库；Task 0 自身无 commit）。

### Task 1: T05 状态模式（4 个 fault_type，纯 lookup 钩子）

**Files:**
- Modify: `CHAOS/gem5/src/arch/arm/CHAOSArmTLB/CHAOSArmTLB.hh`（枚举追加 + stats 成员）
- Modify: `CHAOS/gem5/src/arch/arm/CHAOSArmTLB/CHAOSArmTLB.cc`（string↔enum、dispatch、4 突变、stats）
- Modify: `configs/se/arm_chaos_fs.py:104-110`（choices 追加 4 值）

**Interfaces:**
- Consumes: 既有 maybeCorrupt(entry, va) 钩子（tlb.cc:167-171 不变）、tlb->entryTable()（PfnToMappedPage 同款）、TlbEntry 字段 valid/global/asid。
- Produces: fault_type ∈ {t05_valid_clear, t05_valid_fake_set, t05_global_flip, t05_asid_subst}；stats 标量 numT05State。

- [x] **Step 1.1: .hh 枚举与 stats**——FaultType **只追加**（在 PfnToMappedPage 之后，不重排）：

```cpp
enum class FaultType { BitFlip, StuckAtZero, StuckAtOne, Random,
                       PfnToMappedPage,
                       T05ValidClear, T05ValidFakeSet, T05GlobalFlip, T05AsidSubst };
```

stats 结构体追加 `statistics::Scalar numT05State;`（与 numBitFlips 同款）。

- [x] **Step 1.2: .cc 三处**——stringToFaultType 追加 4 if；faultTypeToString 追加 4 case（-Wswitch 全覆盖）；stats ctor ADD_STAT(numT05State,...)。maybeCorrupt 在 PfnToMappedPage 块后、pfn-mask 块前插入（各分支自增 stats->numT05State 与 faults_injected_count、写日志、return）：

```cpp
// ---- T05 (L1d-TLB entry identity/lifecycle state): mutate the HIT
// entry's state fields. The current translation proceeds (retval is
// already resolved); the corrupted state bites on SUBSEQUENT lookups
// (extra walk / cross-ASID hazard). Matrix spec T05-a..d.
switch (chosen) {
case FaultType::T05ValidClear: {
    entry->valid = false;                      // T05-a
    stats->numT05State++; ++faults_injected_count;
    if (write_log) *(log_stream->stream())
        << "Tick: " << curTick() << ", Site: arm_tlb_lookup_hit"
        << ", VA: 0x" << std::hex << va
        << ", FaultType: t05_valid_clear (T05-a) valid 1->0" << std::dec << std::endl;
    return;
}
case FaultType::T05ValidFakeSet: {
    if (!tlb) return;                          // T05-b resurrect a dead entry
    std::vector<ArmISA::TlbEntry*> dead;
    const auto &tbl = tlb->entryTable();
    for (auto it = tbl.begin(); it != tbl.end(); ++it)
        if (&(*it) != entry && !it->valid) dead.push_back(&(*it));
    if (dead.empty()) return;                  // honest no-op (no dead entry)
    ArmISA::TlbEntry *target = dead[rng() % dead.size()];
    target->valid = true;                      // stale translation goes live
    stats->numT05State++; ++faults_injected_count;
    if (write_log) *(log_stream->stream())
        << "Tick: " << curTick() << ", Site: arm_tlb_lookup_hit"
        << ", VA: 0x" << std::hex << va
        << ", FaultType: t05_valid_fake_set (T05-b) slot vpn 0x"
        << target->vpn << std::dec << std::endl;
    return;
}
case FaultType::T05GlobalFlip: {
    entry->global = !entry->global;            // T05-c
    stats->numT05State++; ++faults_injected_count;
    if (write_log) *(log_stream->stream())
        << "Tick: " << curTick() << ", Site: arm_tlb_lookup_hit"
        << ", VA: 0x" << std::hex << va
        << ", FaultType: t05_global_flip (T05-c) global -> "
        << entry->global << std::dec << std::endl;
    return;
}
default: break;
}
```

（T05AsidSubst 分支同型：候选 = entryTable 中 asid 不同的他表项，`entry->asid = cand[rng() % cand.size()]`，日志记 old→new asid；无候选=诚实 no-op return。）

- [x] **Step 1.3: 配置 choices**——arm_chaos_fs.py:104 choices 追加 `"t05_valid_clear","t05_valid_fake_set","t05_global_flip","t05_asid_subst"`。
- [x] **Step 1.4: 守卫增量重建**——公共模板；预期 scons exit 0、**零新增 warning**（有则修完再继续）。
- [x] **Step 1.5: 功能验证 ×4**——公共模板 tag=t05_a/t05_b/t05_c/t05_d；每个断言：armtlb_injections.log 含本模式签名行（`(T05-x)`）且 console.txt 含 oracle 行；如实记录（含诚实 no-op：日志无注入行时标注 no-candidate）。
- [x] **Step 1.6: T01 回归比对**——tag=t1_reg（bit_flip 同 seed）+ diff 基线 → `T01-REGRESSION-IDENTICAL`。
- [x] **Step 1.7: Commit + relay 推送**——`git add` 显式三文件 + 本计划；消息 `[LSU][P1] gap1-T05：CHAOSArmTLB 状态四子模型（valid清零/伪置位/global翻转/ASID替换）+ numT05State + FS 冒烟×4 + T01 回归字节一致`（无 Co-Authored-By 尾注）。

### Task 2: T06 换值模式（3 个 fault_type，纯 lookup 钩子）

**Files:** 同 Task 1 三件（.hh/.cc/arm_chaos_fs.py）。

**Interfaces:**
- Consumes: maybeCorrupt 钩子；entryTable() 候选模式；字段 ap/mtype/size/tg/N/attributes。
- Produces: fault_type ∈ {t06_perm_subst, t06_memtype_subst, t06_pagesize_subst}；stats 标量 numT06ValueSubst。

- [ ] **Step 2.1: 枚举追加** `T06PermSubst, T06MemTypeSubst, T06PageSizeSubst`（T05 之后）+ stats numT06ValueSubst。
- [ ] **Step 2.2: dispatch 三分支**——全部走"合法替换从活表项取材"（PfnToMappedPage 候选模式）：

```cpp
case FaultType::T06PermSubst: {
    // T06-a permission substitution: ap (and hap) from another LIVE
    // entry -> legal-by-construction (a real permission encoding that
    // exists in this address space), not a hand-coded AP table.
    if (!tlb) return;
    std::vector<ArmISA::TlbEntry*> cand;
    const auto &tbl = tlb->entryTable();
    for (auto it = tbl.begin(); it != tbl.end(); ++it)
        if (&(*it) != entry && it->valid && it->ap != entry->ap)
            cand.push_back(&(*it));
    if (cand.empty()) return;                  // honest no-op
    ArmISA::TlbEntry *src = cand[rng() % cand.size()];
    uint8_t old_ap = entry->ap, old_hap = entry->hap;
    entry->ap = src->ap; entry->hap = src->hap;
    stats->numT06ValueSubst++; ++faults_injected_count;
    if (write_log) *(log_stream->stream())
        << "Tick: " << curTick() << ", Site: arm_tlb_lookup_hit"
        << ", VA: 0x" << std::hex << va
        << ", FaultType: t06_perm_subst (T06-a) ap " << (int)old_ap
        << "->" << (int)entry->ap << " hap " << (int)old_hap
        << "->" << (int)entry->hap << std::dec << std::endl;
    return;
}
```

（T06MemTypeSubst 同型：候选条件 `it->mtype != entry->mtype`，替换 `mtype/innerAttrs/outerAttrs/attributes`；T06PageSizeSubst：候选条件 `it->size != entry->size`，替换 `size/tg/N`——页大小替换改变 VA↔PA 拼接口径，正是规格要的"地址如何解释"故障。）
- [ ] **Step 2.3: choices 追加 3 值**；**Step 2.4: 守卫重建**（零 warning）。
- [ ] **Step 2.5: 功能验证 ×3**（tag=t06_a/b/c）+ **Step 2.6: T01 回归比对**。
- [ ] **Step 2.7: Commit + relay**——`[LSU][P1] gap1-T06：换值三子模型（permission/memtype/pagesize 合法替换）+ numT06ValueSubst + FS 冒烟×3 + T01 回归字节一致`。

### Task 3: T07 way-select 模式（3 个 fault_type + lookup 钩子返回契约）

**Files:**
- Modify: `CHAOS/gem5/src/arch/arm/CHAOSArmTLB/CHAOSArmTLB.hh`（maybeCorrupt 签名 void→bool + 枚举 + stats）
- Modify: `CHAOS/gem5/src/arch/arm/CHAOSArmTLB/CHAOSArmTLB.cc`（全部既有 return 路径补 `return false;` + 3 新分支）
- Modify: `CHAOS/gem5/src/arch/arm/tlb.cc:167-171`（调用点消费返回值）
- Modify: `configs/se/arm_chaos_fs.py`（choices +3）

**Interfaces:**
- Consumes: TLB::lookup 的 retval 生命周期（置 nullptr = miss 路径，现场已核）。
- Produces: `bool maybeCorrupt(entry, va)`（true=抑制本次命中）；fault_type ∈ {t07_false_hit, t07_double_hit, t07_wrong_way}；stats numT07WaySelect。

- [ ] **Step 3.1: 签名与调用点契约**——.hh 声明改 `bool maybeCorrupt(ArmISA::TlbEntry *entry, Addr va);`（注释：true = 假命中，调用方应视作 miss）。tlb.cc:167-171 改：

```cpp
    // Phase 3 §六.4 item 3: CHAOSArmTLB hook. On a TLB HIT, corrupt the
    // entry's pfn before returning it to the MMU — models a defective TLB
    // cell (address-translation-path fault). nullptr = no injector.
    // T07-a false hit (gap1): the injector returns true to SUPPRESS this
    // hit (match vector wrongly shows zero) — the caller then takes the
    // normal miss path; the TlbHit F6 event below stays unfired (correct).
    if (retval && chaosTLB) {
        if (chaosTLB->maybeCorrupt(retval, lookup_data.va))
            retval = nullptr;
    }
```

**回归红线**：.cc 内全部既有 early-return（entry null / probability / cap / prob-gate / skip / PfnToMappedPage / pfn 各分支）都补 `return false;`——非 T07 模式下 retval 永不被动。

- [ ] **Step 3.2: 枚举追加** `T07FalseHit, T07DoubleHit, T07WrongWay` + stats numT07WaySelect + string↔enum + choices。
- [ ] **Step 3.3: dispatch 三分支**：

```cpp
case FaultType::T07FalseHit: {
    stats->numT07WaySelect++; ++faults_injected_count;
    if (write_log) *(log_stream->stream())
        << "Tick: " << curTick() << ", Site: arm_tlb_lookup_hit"
        << ", VA: 0x" << std::hex << va
        << ", FaultType: t07_false_hit (T07-a) hit suppressed" << std::dec << std::endl;
    return true;                               // caller: retval = nullptr
}
case FaultType::T07DoubleHit: {
    // T07-b: a second way with the SAME vpn also matches; way-select
    // hands out the OTHER translation. Requires a real alias (the
    // tlb_probe aliasing workload creates same-VA-different-PA pairs).
    if (!tlb) return false;
    std::vector<ArmISA::TlbEntry*> cand;
    const auto &tbl = tlb->entryTable();
    for (auto it = tbl.begin(); it != tbl.end(); ++it)
        if (&(*it) != entry && it->valid && it->vpn == entry->vpn
            && it->pfn != entry->pfn)
            cand.push_back(&(*it));
    if (cand.empty()) return false;            // honest no-op (no alias)
    ArmISA::TlbEntry *src = cand[rng() % cand.size()];
    Addr old_pfn = entry->pfn;
    entry->pfn = src->pfn; entry->attributes = src->attributes;
    stats->numT07WaySelect++; ++faults_injected_count;
    if (write_log) *(log_stream->stream())
        << "Tick: " << curTick() << ", Site: arm_tlb_lookup_hit"
        << ", VA: 0x" << std::hex << va << ", old_pfn: 0x" << old_pfn
        << ", new_pfn: 0x" << entry->pfn
        << ", FaultType: t07_double_hit (T07-b) alias way wins" << std::dec << std::endl;
    return false;
}
```

（T07WrongWay 同型：候选 = 任意 valid 异表项（不限 vpn），随机取一，替换 pfn/attributes——"错选 way"。）
- [ ] **Step 3.4: 守卫重建**（零 warning；tlb.cc 一并编入）；**Step 3.5: 功能验证 ×3**（tag=t07_a/b/c；t07_a 断言：注入行存在 + console 中该 run 的翻译行为变化或 Masked，如实记录）；**Step 3.6: T01 回归比对**。
- [ ] **Step 3.7: Commit + relay**——`[LSU][P1] gap1-T07：way-select 三子模型（假命中/双命中/错选way）+ maybeCorrupt 返回契约 + FS 冒烟×3 + T01 回归字节一致`。

### Task 4: T08 walk/refill 时序模式（4 个 fault_type + insert 钩子）

**Files:**
- Modify: `CHAOS/gem5/src/arch/arm/CHAOSArmTLB/CHAOSArmTLB.hh`（新方法 + last_insert 成员 + 枚举 + stats）
- Modify: `CHAOS/gem5/src/arch/arm/CHAOSArmTLB/CHAOSArmTLB.cc`（maybeCorruptInsert 实现）
- Modify: `CHAOS/gem5/src/arch/arm/tlb.cc:260`（insert 顶部钩子）
- Modify: `configs/se/arm_chaos_fs.py`（choices +4）

**Interfaces:**
- Consumes: TLB::insert(const Lookup&, TlbEntry&) 顶部（victim 写入前；multiInsert 亦经此）。
- Produces: `bool maybeCorruptInsert(ArmISA::TlbEntry &entry, Addr va)`（true=丢弃本次 insert）；fault_type ∈ {t08_walk_fill_drop, t08_walk_fill_dup, t08_done_early, t08_stale_fill}；stats numT08WalkFill；成员 `TlbEntry last_insert; bool have_last_insert = false;`。

- [ ] **Step 4.1: tlb.cc insert 钩子**——函数体首行：

```cpp
// insert a new TLB entry
void
TLB::insert(const Lookup &lookup_data, TlbEntry &entry)
{
    // gap1 T08 (walk/refill timing): injector may DROP this insert
    // (T08-a walk/fill lost) or mutate the entry before the victim
    // write (T08-b/c/d). Pure no-op for non-T08 fault types.
    if (chaosTLB && chaosTLB->maybeCorruptInsert(entry, lookup_data.va))
        return;

    TlbEntry *victim = table.findVictim(lookup_data);
    ...（原体不动）
```

- [ ] **Step 4.2: .hh/.cc 实现**——门控序（**回归红线：非 T08 模式第一行即 return false，零 RNG/零状态**）：

```cpp
bool
CHAOSArmTLB::maybeCorruptInsert(ArmISA::TlbEntry &entry, Addr va)
{
    switch (fault_type_enum) {
        case FaultType::T08WalkFillDrop: case FaultType::T08WalkFillDup:
        case FaultType::T08DoneEarly:   case FaultType::T08StaleFill:
            break;                    // T08 modes proceed below
        default:
            return false;             // non-T08: pure no-op (regression)
    }
    // Walk history (PRE-gate): "previous walk" is the previous insert
    // seen while a T08 mode is active — stale source for T08-c/d.
    const bool have_prev = have_last_insert;
    const ArmISA::TlbEntry prev = last_insert;
    auto track = [&]() { last_insert = entry; have_last_insert = true; };

    if (probability <= 0.0f) return false;
    if (max_faults != 0 && faults_injected_count >= max_faults) { track(); return false; }
    std::uniform_real_distribution<float> probDist(0.0f, 1.0f);
    if (probDist(rng) > probability) { track(); return false; }
    if (events_to_skip > 0) { --events_to_skip; track(); return false; }

    switch (fault_type_enum) {
    case FaultType::T08WalkFillDrop: {
        stats->numT08WalkFill++; ++faults_injected_count;
        if (write_log) *(log_stream->stream())
            << "Tick: " << curTick() << ", Site: arm_tlb_insert"
            << ", VA: 0x" << std::hex << va
            << ", FaultType: t08_walk_fill_drop (T08-a) insert dropped"
            << std::dec << std::endl;
        track();                    // the walk happened; only the fill was lost
        return true;                // caller returns without inserting
    }
    case FaultType::T08DoneEarly: {
        if (!have_prev) { track(); return false; }   // no stale source yet
        entry.attributes = prev.attributes;         // T08-c: metadata stale,
        entry.lookupLevel = prev.lookupLevel;        // pfn stays from THIS walk
        entry.innerAttrs = prev.innerAttrs;
        entry.outerAttrs = prev.outerAttrs;
        stats->numT08WalkFill++; ++faults_injected_count;
        ...log "t08_done_early (T08-c) metadata stale, pfn 0x<entry.pfn>"...
        track(); return false;
    }
    default: break;
    }
    track(); return false;
}
```

（T08WalkFillDup：从 entryTable() 随机取一个异表项 `*target = entry;`（同一 refill 多写一路，覆盖受害者槽位）后 `return false`；T08StaleFill：`if (!have_prev)` 诚实 no-op，否则 `ArmISA::TlbEntry stale = prev; stale.vpn = entry.vpn; stale.asid = entry.asid; entry = stale;`（旧翻译对当前请求生效，键位保留当前）。四分支日志均含 `(T08-x)` 标记与 old/new 关键字段。）
- [ ] **Step 4.3: choices +4**；**Step 4.4: 守卫重建**（零 warning）。
- [ ] **Step 4.5: 功能验证 ×4**（tag=t08_a/b/c/d）；**Step 4.6: T01 回归比对**（insert 钩子对 bit_flip 必须零扰动）。
- [ ] **Step 4.7: Commit + relay**——`[LSU][P1] gap1-T08：walk/refill 时序四子模型（丢失/重复/过早/旧结果）+ TLB::insert 钩子 + last_insert 走历史 + FS 冒烟×4 + T01 回归字节一致`。

### Task 5: 家族确定性双跑（DET 门）+ 文档收口

**Files:**
- Modify: `docs/gem5-fi/lsu/findings.md`（F-044 事实条目）
- Modify: `docs/gem5-fi/lsu/progress.md`（Session 002 条目 ⑪）
- Modify: 本计划（勾选收口）

**Interfaces:**
- Consumes: Task 1-4 的 14 模式与公共模板。
- Produces: 每组一个代表模式的同 seed 双跑 SHA256 一致证据（G0-02 家族门惯例）；F-044；矩阵影响记录（15 cell 模型级解除，campaign 接线延后声明）。

- [ ] **Step 5.1: 代表模式双跑 ×4 组**——t05_valid_clear / t06_perm_subst / t07_wrong_way / t08_stale_fill 各两个 run（tag=det_<mode>_1/_2，同 seed 20261008）；每组断言：`sha256sum` 两个 armtlb_injections.log 一致 + console oracle 行一致。任一不一致=失败，停下诊断（确定性是平台铁律）。
- [ ] **Step 5.2: findings F-044**——记录：17 缺口分组普查数字（40/21/15/9）、Group 1 实施事实（14 模式、两处钩子契约、回归不变量及 T01 字节一致证据路径）、15 cell 待接线、Group 2/3/4 计划另行。证据路径 /tmp/gap1/*（关键日志复制到 artifacts/lsu-trial/gap1/ 或 runs/lsu/ 下入库——**.gitignore 合规、不入库大文件**，只入库日志摘录）。
- [ ] **Step 5.3: progress ⑪**——Session 002 追加：gap-1 完成、Task 0 集群 FS 首跑时长实测、四组 DET 结果、唯一下一动作（Group 2 消费侧计划 or 等待接线窗口）。
- [ ] **Step 5.4: Commit + relay**——`[LSU][P1] gap1 收口：家族确定性双跑×4 组全一致 + F-044 + progress ⑪（T05-T08 共 15 cell 模型级解除，campaign 接线待波次 5 后受控窗口）`。

---

## Self-Review（写作后自检记录）

1. **规格覆盖**：清单 T05-T08 行的全部 14 子模型 → Task 1-4 dispatch 全覆盖（T05×4/T06×3/T07×3/T08×4）；F0/F2/F6/F4 频率层不属注入器职责（campaign 触发层，接线延后已声明）。✓
2. **占位符扫描**：T05AsidSubst/T06MemTypeSubst/T06PageSizeSubst/T07WrongWay/T08Dup/T08StaleFill 以"同型+差异描述"给出（候选条件/替换字段/日志要点逐一点名，非 TBD）；代码骨架含全部门控与日志结构。可接受：这些分支与给出的完整分支逐字同型，仅字段名不同且已列明。✓
3. **类型一致性**：maybeCorrupt bool 返回在 .hh/.cc/tlb.cc 三处一致；maybeCorruptInsert(ArmISA::TlbEntry&, Addr) 与 tlb.cc 调用点一致；stats 标量名四处一致（numT05State/numT06ValueSubst/numT07WaySelect/numT08WalkFill）；fault_type 字符串与 choices 列表逐字对应。✓
4. **风险与未决**：①集群 FS 首跑时长未知——Task 0 实测，若单 run >30min 则每 Task 验证串行成本高但可承受；②login01 资源——守卫门禁 + 并发 1 兜底，压力异常则转 cn23423 dattach（CP56 模式）；③T05-b/T07-b/T06* 可能诚实 no-op（候选不存在）——设计上已声明为合法结果，验证时如实记录不视为失败；④armtlb_injections.log 在 outdir（simout.create 相对 outdir）——Task 0 确认路径，若不同则修正模板。

## 执行模式说明

远程单通道（reach Bash）环境，inline 执行（superpowers:executing-plans 模式），不派子代理。逐 Task 顺序执行：代码 → 守卫重建 → 验证 run → 回归比对 → commit → relay 推送 → 勾选。任何一步失败：修复 → 重验证 → 才继续（诚实性铁律：未验证不得声称通过）。
