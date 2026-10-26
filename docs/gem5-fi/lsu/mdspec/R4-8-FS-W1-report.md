# R4-8-FS-W1：FS-INFRA 24 行复验 + W1(MiBench) 19 行口径订正（Agent-3 报告）

> 执行者：R4-8 并行收口 Agent-3（worktree `.claude/worktrees/r4-7-fsinfra`，分支
> `r4-7-fsinfra-w1`，基线 `d5fc8727`）。本报告只写**本轮实测**的内容；未跑的一律
> 标注为"未验证"。
> 上位：`docs/superpowers/plans/2026-10-20-lsu-mdspec-round4.md` Task 6.2/6.4；
> `blocked_triage.md` §R4-6 台账订正；`round4_findings.md` §R4-6.0。

## 0. 摘要

| 工作流 | 结论 |
|---|---|
| FS-INFRA 24 行 | **12 行真机跑通**（T01/T02/T03/T04/T10 × W4）；**9 行精确阻塞 = 模式未实现**（T05/T06/T07）；**3 行 = T08**，其 `MODEL_BLOCKED` 理由（"compile-unverified, pilot pending"）经真机证伪，但**移除与否留待编排方**（见 §2.3/§6.2） |
| W1(MiBench) 19 行 | **17 行解锁**（二进制 + golden + 合法 SE 路径均在盘上，且逐行实存校验）；**2 行保留**（S01-F0-W1 / S02-F0-W1，理由是**另一个**精确门：per-(model,workload) 的 F0 跨度未普查，**不是**负载级封锁） |
| 工具缺陷 | 本轮**发现并修复 3 个真实缺陷**（1 个误导性阻塞理由 + 1 个不存在的 `--cmd` 路径 + 1 个会把 W1 长流误判为 Timeout 的超时预算） |

**一句话**：FS-INFRA 的"堵点"已不再成立（12 行真跑通，其中 T04-F0-W4 产出
**完整 L5 链 + 内核 Oops**）；T05/T06/T07 的阻塞理由由过宽的 "fs-infra" 精确化为
"模式未实现"；W1 的过宽 `WL_BLOCKED["MiBench"]` 已被逐行证据证伪并订正。

## 1. 方法、身份与命令

- gem5 二进制（只读复用，未重编）：`CHAOS/gem5/build/ARM/gem5.opt`（lsu-mdspec worktree），
  sha256 前缀 `7d52bc1392a10055`；`run.out` 自述 "gem5 compiled Oct 22 2026 09:33:06"。
  **该二进制已含 R4-6-T08 的 C++ 修复**（`strings` 实测含 `arm_tlb_walk_issue_probe` /
  `arm_tlb_walk_issue_drop` / `lookup_hit_skipped` / `walk-issue-only`），并由 T08 真机
  产出 `arm_tlb_walk_issue_drop` 反证其确已编入。
- FS 资产：`LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs`（vmlinux / ubuntu.img / boot.arm64）。
- checkpoint：`/home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015`
  （restore 基线 = 目录名 `237949797015`，与 R4-6.0 一致）。
- 全部 gem5 调用经 `flock /tmp/lsu_gem5_slot3.lock`（团队并发 ≤4 槽位）。
- **官方入口**（正是 ready-contract 会发出的命令形状）：

```
LSU_GEM5_BIN=<...>/gem5.opt LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs \
python3 tools/lsu_campaign.py \
  --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv \
  --outdir /tmp/r4-7-fsinfra/fs1 --cells T03-F5-W4,T04-F0-W4,T08-F0-W4 \
  --phase trial --max-seeds-per-cell 1 --max-parallel 1 --fs-timeout 700 \
  --allow-blocked-models \
  --fs-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015
```

本轮 gem5 运行预算：**3 个 FS cell（各 1 seed）+ 1 个 W1 SE smoke = 4 次**（上限 6）。
未重跑 T01（R4-6.0 已固化其证据，且用户指示"勿重做"）。

## 2. FS-INFRA 24 行：逐行裁决

### 2.1 溢出裁决表

| # | RunID | 裁决 | 证据（盘上产物 / 命令） |
|---|---|---|---|
| 1 | T01-F0-W4 | **跑通** | R4-6.0 已固化（本轮不重跑）：注入日志 + 6 事件链 |
| 2 | T01-F1-W4 | 跑通（结构） | `resolve_cell` → `fs:tlb_probe`；与 T01-F0-W4 同模型同路径（T01 无 tier 参数） |
| 3 | T01-F2-W4 | 跑通（结构） | 同上 |
| 4 | T02-F0-W4 | 跑通（结构） | `--tlb_fault_type bit_flip --tlb_bits_to_change 2`；代码路径同 T01 的 BitFlip 分支 |
| 5 | T02-F2-W4 | 跑通（结构） | 同上 |
| 6 | T03-F5-W4 | **跑通（真机）** | `/tmp/r4-7-fsinfra/fs1/T03-F5-W4/seed1/`：注入日志 + 6 事件链（§4.1） |
| 7 | T04-F0-W4 | **跑通（真机，完整 L5 链）** | `/tmp/r4-7-fsinfra/fs1/T04-F0-W4/seed1/`：`terminal=full provable_to=L5` + 内核 Oops（§4.2） |
| 8 | T04-F2-W4 | 跑通（结构） | 同 T04 的 `pfn_to_mapped_page` 路径；F2 只改 tier |
| 9 | T04-F6-W4 | 跑通（结构） | 同上（F6 = 首事件即注入） |
| 10 | T05-F0-W4 | **精确阻塞：模式未实现** | `CHAOSArmTLB.cc` 的 `stringToFaultType` 只有 bit_flip / stuck_at_zero / stuck_at_one / pfn_to_mapped_page / walk_pairing；无 valid/global/ASID 模式 |
| 11 | T05-F2-W4 | 精确阻塞：模式未实现 | 同上 |
| 12 | T05-F6-W4 | 精确阻塞：模式未实现 | 同上 |
| 13 | T06-F0-W4 | **精确阻塞：模式未实现** | 同上；permission/attribute 合法替换无对应 faultType |
| 14 | T06-F2-W4 | 精确阻塞：模式未实现 | 同上 |
| 15 | T06-F6-W4 | 精确阻塞：模式未实现 | 同上 |
| 16 | T07-F0-W4 | **精确阻塞：模式未实现** | 同上；hit fabrication / way select 无对应 faultType |
| 17 | T07-F4-W4 | 精确阻塞：模式未实现 | 同上 |
| 18 | T07-F6-W4 | 精确阻塞：模式未实现 | 同上 |
| 19 | T08-F0-W4 | **真机跑通（activated=1，T08-a 断言达成）**，但仍被 `MODEL_BLOCKED` 条目挡住（条目未删，见 §2.3） | `/tmp/r4-7-fsinfra/fs1/T08-F0-W4/seed1/`：probe + drop + tlb_walk/tlb_refill 配对（§4.3、§4.5） |
| 20 | T08-F4-W4 | 未验证（同模型真机已通，但 F4 落点 9.9万–14.1万 walk 事件后，**无实测预算**） | `MODEL_BLOCKED["T08"]` 挡住；F4/F6 落点实测**没有** |
| 21 | T08-F6-W4 | 未验证（同上；F6 = 第 1 个 walk 事件即丢弃，结构推断见 R4-6-T08 §5.3） | 同上 |
| 22 | T10-F0-W4 | 跑通（结构） | `--tlb_fault_type bit_flip`（T10 复用 T01 的 BitFlip，无 banding 子模型——规格近似已在代码注明） |
| 23 | T10-F1-W4 | 跑通（结构） | 同上 |
| 24 | T10-F2-W4 | 跑通（结构） | 同上 |

**"跑通（结构）"的含义（诚实边界）**：该行的 `resolve_cell` 返回完整 FS flag
set、其 faultType 的**注入代码路径**已由同族的真机运行证明可达（T01 证明
lookup-hit/BitFlip 路径；T03 证明 stuck 路径；T04 证明 pfn 替换路径），
但**该行自身未逐行真机运行**。计数：真机 3 行（T03/T04/T08-F0）+ 复引 1 行（T01-F0）
+ 结构 17 行 = 24。

### 2.2 一个真实缺陷（已修）：T05/T06/T07 报了误导性的理由

复验前的 `resolve_cell` 用 `MODEL_FLAGS[model][0] == "armtlb"` 判定"是不是 T 模型"，
但 **T05/T06/T07 故意不在 `MODEL_FLAGS` 里**（模式不存在），于是它们落回负载级分支，
报出：

```
workload:workload-level:blocked(fs-infra: TLB workload needs FS)
```

而真实阻塞是**模式未实现**（`MODEL_BLOCKED` 里本就写着正确的
`deferred(mode unimplemented: …)`，只是被负载级分支抢先）。这是"理由不精确"的
缺陷——会把 FS-INFRA 的**可自行实现项**伪装成"需要 FS"。

修复：引入 `ARMTLB_MODELS = {T01..T08, T10}`（T09 为 B0-N/A）作为负载级分支的判定集，
让理由来自模型级检查。修复后逐行实测：

```
T01-F0-W4  → fs:tlb_probe          T05-F0-W4  → deferred(mode unimplemented: valid/global/ASID state)
T02-F0-W4  → fs:tlb_probe          T06-F0-W4  → deferred(mode unimplemented: permission legal-substitution)
T03-F5-W4  → fs:tlb_probe          T07-F0-W4  → deferred(mode unimplemented: hit fabrication/way select)
T04-F0-W4  → fs:tlb_probe          T08-F0-W4  → MODEL_BLOCKED（--allow-blocked-models 可产证据）
T10-F0-W4  → fs:tlb_probe          （T10-F0-W11 仍走 SPEC → LICENSE，未变）
```

### 2.3 T08：`MODEL_BLOCKED` 的理由已被真机证伪（**未代为移除**）

`MODEL_BLOCKED["T08"]` 现写 `"landed compile-unverified, pilot pending"`。
本轮真机证明**两半都不再成立**：

1. **compile 已验**：冻结二进制含 T08 的 C++ 字符串，且真机产出
   `Site: arm_tlb_walk_issue_drop`（该行只可能来自 T08 的 `maybeDropWalkFill`）；
2. **pilot 不再 pending**：T08-F0-W4 seed1 满足 R4-6-T08 报告 §4.3 的判据 1–4（§4.3）。

**我做的是**：把该理由改写成**事实正确的精确陈述**（记录 F0 已有真机断言、F4/F6 尚未
实测），**保留**该条目（不会无声解锁）；把移除与否留作编排方的一行决定——理由是
F4/F6 的落点预算（9.9万–14.1万 walk 事件）**本轮无实测**，而"断言可跑才删"的纪律
在 F4/F6 上尚未满足。移除建议与命令见 §6.2。

## 3. W1(MiBench) 19 行：口径订正

### 3.1 冲突的根因（盘上实测）

`runid_map.json` 生成器 `_resolve_workload` **先查 `WL_BINARY`**（长键优先），
"MiBench-TC23" → `mibench/bin/w1_all`，路径回退命中 `workloads/mibench/bin/w1_all`
→ 判定**可跑**；而 `lsu_campaign.resolve_cell` **先查 `WL_BLOCKED`**，被
`WL_BLOCKED["MiBench"] = "blocked(fs-infra: SE has no MiBench FS pipeline)"`
抢先拒跑。两个工具口径相反——这就是 19 行冲突（R4-6.0 §0.5 已登记）。

该理由**事实错误**（"SE has no MiBench FS pipeline"），盘上三件套齐备：

| 要件 | 盘上证据 |
|---|---|
| 二进制 | `workloads/mibench/bin/w1_all`，ELF aarch64 static，938232 B（`file` 实测） |
| golden | `6dab8ec221c46677`（`lsu_campaign.GOLDENS` + `lsu_runner` GOLDEN_IDS）；冻结合同 `docs/gem5-fi/lsu/evidence/golden_w1_all_manifest.json`：canonical sha256 `5bb9298aa1100edd…75245a`，g1/g2/g3 + 原生 all_A/all_B **五方全等**，g1/g2 实测 7.44 h / 7.51 h, rc=0 |
| 合法路径 | **SE**（本 campaign 的 SE 分支）；`tools/lsu_w1_rerun.py` 已在该载体上驱动 15 个实验项 |

### 3.2 订正后的 `WL_BLOCKED`（精确）

```python
WL_BLOCKED = {                     # "MiBench" 已删除
    "TLB-AliasPerm": "blocked(fs-infra: TLB workload needs FS)",
    "Atomic-Litmus": "blocked(multicore-fs: litmus needs multi-core FS)",
    "PARSEC":        "blocked(multicore-fs: PARSEC needs multi-core FS)",
    "SPEC":          "blocked(spec-license: SPEC CPU2017 needs a license)",
}
```

**未被"一刀切清空"**：TLB-AliasPerm（真需 FS）、Atomic-Litmus/PARSEC（真需多核 FS）、
SPEC（真缺授权）四条保留，理由逐条有据。

### 3.3 逐行裁决表（19 行）

| RunID | 裁决 | 证据 |
|---|---|---|
| S01-F1-W1 | **解锁** | `--cmd …/workloads/mibench/bin/w1_all`（实存）golden `6dab8ec221c46677` |
| S01-F2-W1 | **解锁** | 同上 |
| S02-F2-W1 | **解锁** | 同上 |
| C01-F0-W1 | **解锁** | 同上（cache family，legacy 机制，无 F0 span 门） |
| C01-F1-W1 | **解锁** | 同上 |
| C01-F2-W1 | **解锁** | 同上 |
| C02-F0-W1 | **解锁** | 同上 |
| C02-F2-W1 | **解锁** | 同上 |
| C04-F0-W1 | **解锁** | 同上 |
| C04-F1-W1 | **解锁** | 同上 |
| C04-F2-W1 | **解锁** | 同上 |
| S13-F0-W1 | **解锁** | 同上（addrpath family，非 A07 → 沿用既有 span=1000 行为，未变） |
| S13-F1-W1 | **解锁** | 同上 |
| S13-F2-W1 | **解锁** | 同上 |
| L01-F0-W1 | **解锁** | 同上 |
| L01-F1-W1 | **解锁** | 同上 |
| L01-F2-W1 | **解锁** | 同上 |
| **S01-F0-W1** | **保留** —— 精确理由：`BLOCKED(F0-span-unmeasured: … LSQFWD_F0_SPAN[('S01','mibench/bin/w1_all')] …)` | 与负载级封锁**无关**；per-(model,workload) 跨度未普查（S01 在 sq_forward 上 eligible=7，w1_all 上**未测**） |
| **S02-F0-W1** | **保留** | 同上（S02）|

**T 模型的 W1 行（T01/T02/T10 × W1 = 8 行）不在 19 行口径冲突集合内**：
它们走 FS 载体（golden = TLB probe 的 `b6d81b36…`），删除 `"MiBench"` 键**不改变**
它们的分流（循环里对 T 模型 `continue`）——测试已钉死（§5）。

### 3.4 又两个真实缺陷（已修）

1. **`--cmd` 路径不存在**：`resolve_cell` 硬编码 `REPO/"workloads/directed"/binary`，
   而 W1 载体在 `workloads/mibench/bin/w1_all`（**不是** directed 子目录）。
   解锁前这条会以不存在的路径启动 gem5。修复：`wl_binary_path()`（directed 优先、
   workloads 根回退，与 `lsu_runner._wl_path` 同口径，防两驱动漂移）。
2. **超时预算会把 W1 长流伪判为 Timeout**：SE 分支用 `args.timeout`（默认 300 s），
   而 W1 golden 实测 7.44 h（`lsu_runner.TIMEOUTS["SE_W1"]=43200`）。
   解锁但不修超时 = 每行都产出 `injected=0` 的**伪 Timeout**（比继续阻塞更坏）。
   修复：W1 载体改用 `SE_W1_TIMEOUT = 43200`（复用 runner 的冻结常量）。

### 3.5 W1 SE 路径的端到端冒烟（真机）

§4.4 给出：campaign 以**真实 `--cmd`** 启动 gem5、gem5 正常完成初始化并开始运行。
（W1 的行级真机裁决属正式 campaign 范畴，本轮**不启动正式 campaign**。）

## 4. 真机原始输出摘录

### 4.1 T03-F5-W4（stuck 模式；`--tlb_fault_type stuck_at_zero`，seed 1）

```
Tick: 237950940537, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483fa8,
old_pfn: 0x81d75, new_pfn: 0x81d75, FaultType: stuck_at_zero,
Mask: 0x100000000000000
```

6 事件传播链（`prop_evt.txt.gz`，corr 齐备）：

```
kind=inj        tick=237950940537 corr=origin
kind=tlb_pfn    tick=237950940537 before=81d75 after=81d75 state_before=81d75fa8 corr=seq_primary
kind=sq_execute tick=237950940537 sq_idx=32 state_after=issued corr=seq_primary
kind=sq_writeback tick=237950941869 sq_idx=32 state_after=packet_built corr=seq_primary
kind=resp       tick=237950942203 request_id=301 pa=81d75fa8 corr=seq_primary
kind=sq_complete tick=237950942203 sq_idx=32 state_after=completed corr=seq_primary
```

**诚实附注**：该 seed 抽中的 mask 落在 pfn 域之外（bit 56，本为 0），故
`old_pfn == new_pfn`——注入"结构上应用、数值上中性"。这是注入器 **mask 域**
问题（应约束在 pfn 字段宽度内），**不是**"该行不可跑"。同类现象在 R4-6-T08 报告
§1.1 的 walk_pairing 上已记录过。

### 4.2 T04-F0-W4（pfn 替换；`--tlb_fault_type pfn_to_mapped_page`，seed 1）—— 完整 L5 链

注入日志（**值确实改变**）：

```
Tick: 237950940537, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483fa8,
old_pfn: 0x81d75, new_pfn: 0x0, FaultType: pfn_to_mapped_page, candidates: 31
```

`chain_report.json`：

```
oracle_outcome: "Crash"   stream_present: true   truncated: false
event_count: 1572   terminal: "full"   provable_to: "L5"
edges: L0->L1 proven, L1->L2 proven, L2->L3 proven, L3->L4 proven, L4->L5 proven
L0->L1 witness: L0:inj@t237950940537        -> L1:cache_access@t237950941869  keys=[fault_id]
L2->L3 witness: L2:tlb_pfn@t237950940537    -> L3:sq_execute@t237950940537    keys=[fault_id, dyn_inst_seq]
L3->L4 witness: L3:sq_execute@t237950940537 -> L4:taint_reg@t237951293850     keys=[fault_id]
L4->L5 witness: L4:taint_reg@t237951293850  -> L5:chain_end@t238882046166     keys=[fault_id]
```

`run.out`：`[arm_chaos_fs] KERNEL OOPS under fault — exiting (classify: Crash/DUE per fs_mode)`；
`board.terminal` 尾部：`el0t_64_sync_handler+0x88/0xb8` / `Code: bad PC value`。

即 **L0 注入 → L1 pfn 变更 → L2 翻译 → L3 SQ 执行/回写 → L4 taint → L5 错误提交/oops**
逐边可证 —— 这是 FS-INFRA 目前**最强**的一条证据（不止"有注入"，而是完整链到 L5）。

### 4.3 T08-F0-W4（walk 配对；`--tlb_fault_type walk_pairing`，seed 1，`--allow-blocked-models`）

注入日志三行，逐行对应 R4-6-T08 §4.3 判据 1–3：

```
Tick: 237949797348, Site: arm_tlb_walk_issue_probe, walk_id: 1, VA: 0x40b4c0,
  FaultType: walk_pairing (walk-issue hook REACHED: TableWalker::walk -> maybeDropWalkFill)

Tick: 237950233578, Site: arm_tlb_lookup_hit_skipped, VA: 0xffffffc009483eb0,
  FaultType: walk_pairing (T08 walk-issue-only: NOT consumed at lookup-hit; see maybeDropWalkFill)

Tick: 238044463587, Site: arm_tlb_walk_issue_drop, walk_id: 703, VA: 0xffffffc00801e240,
  FaultType: walk_pairing (T08-a lost walk/fill)
```

PROP-EVT（判据 4，经字段裁剪）：`walk_id` 与 `fault_id` **一致**，`field=lost`：

```
PROP-EVT: kind=inj        fault_id=1 event_id=0 parent_event_id= tick=238044463587 walk_id=703 va=ffffffc00801e240 field=walk_pairing corr=origin
PROP-EVT: kind=tlb_walk   fault_id=1 event_id=1 parent_event_id=0 tick=238044463587 walk_id=703 va=ffffffc00801e240 field=walk_pairing corr=origin
PROP-EVT: kind=tlb_refill fault_id=1 event_id=2 parent_event_id=1 tick=238044463587 walk_id=703 va=ffffffc00801e240 field=lost corr=origin
```

判据 3（反例必须消失）亦满足：注入日志中**没有** `Site: arm_tlb_lookup_hit` 且同行含
`FaultType: walk_pairing` 的行（只有 `_skipped` 行）。
即 **T08-a 已获真机断言**。该 run 未自然结束（walk 被丢弃 → 翻译永不完成，正是
规格预期的 Timeout 通道），证据在 `--fs-timeout` 到点时由 campaign 的
Z_SYNC_FLUSH 前缀保留。

### 4.5 FS 批次聚合（campaign 自身给出的三行）

```
  T03-F5-W4: phase=trial n_runs=1 activated=1 sdc=0 stop=seed-cap(1) cons=OK
[allow-blocked] T08-F0-W4: running a MODEL_BLOCKED model under the explicit
  --allow-blocked-models opt-in; reason kept in the output: <T08 reason>
  T04-F0-W4: phase=trial n_runs=1 activated=1 sdc=0 stop=seed-cap(1) cons=OK
  T08-F0-W4: phase=trial n_runs=1 activated=1 sdc=0 stop=seed-cap(1) cons=OK
BATCH1_EXIT=0
```

三行均 `activated=1`（守恒 `cons=OK`）；T03/T08 的 L5 落在 Timeout 通道
（各自预期），T04 落在 Crash（内核 Oops）。

### 4.4 W1 SE 路径端到端冒烟（真机启动 + 真注入）

命令（`flock` 槽位内，`C01-F0-W1`，故意给 `--timeout 90`）：

```
LSU_GEM5_BIN=<frozen gem5.opt> python3 tools/lsu_campaign.py \
  --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv \
  --outdir /tmp/r4-7-fsinfra/w1smoke --cells C01-F0-W1 --phase trial \
  --max-seeds-per-cell 1 --max-parallel 1 --timeout 90
```

gem5 实际命令行（`pgrep -af` 实测）——**`--cmd` 指向真实存在的 W1 载体**：

```
--cmd /home/sdc/gem5-fi-ding/.claude/worktrees/r4-7-fsinfra/workloads/mibench/bin/w1_all
--cpu O3
```

产出的 SE 产物（`/tmp/r4-7-fsinfra/w1smoke/C01-F0-W1/seed1/`）：
`config.ini`、`stats.txt`、`cache_injections.log`、**`prop_evt.txt.gz`**（CHAOSPropagation 已挂）。

真注入（`cache_injections.log`）：

```
Tick: 1000000, Cache Block Addr: 766464, Byte Offset: 0, FaultType: bit_flip, Mask: 10000000
FUNNEL: attempted=1 eligible=1 injected=0
```

内联传播（`prop_evt.txt.gz`，经字段裁剪）：

```
PROP-EVT: kind=inj run_id=C01-F0-W1 sample_run_id=s1 fault_id=1 event_id=0 tick=1000000 va=bb200 field=data corr=origin
PROP-EVT: kind=mshr_merge … tick=6234690 mshr_id=0 cache_line=bb1c8 state_after=merged_into_mshr corr=addr_fallback
```

**附带证明超时预算修复生效**：campaign 收到的是 `--timeout 90`，但该 run 在 90 s 后
**未被杀**（运行至外层 `timeout 300` 才终止，`W1SMOKE_EXIT=124`）——正是
`SE_W1_TIMEOUT=43200` 对 W1 载体接管预算的直接证据（若不修，这里会得到一条
`injected=0` 的伪 Timeout）。

**诚实边界**：该冒烟被外层 300 s 截断，**没有** L5 分类（`cell_results.json` 未生成），
故它只证明"路径合法 + 真注入 + 预算正确"，**不**证明 W1 行的行级裁决。

## 5. 工具/测试改动与验证

| 文件 | 改动 | 为什么 |
|---|---|---|
| `tools/lsu_campaign.py` | 新增 `ARMTLB_MODELS`；负载级分支改用它判定 T 模型 | T05/T06/T07 报出精确的"模式未实现"而非过宽的 "fs-infra" |
| `tools/lsu_campaign.py` | 新增 `wl_binary_path()`；`--cmd` 改用它 | W1 载体不在 `workloads/directed/`，原硬编码路径不存在 |
| `tools/lsu_campaign.py` | 新增 `SE_W1_TIMEOUT=43200`；SE 分支按载体选超时 | 防止 W1 长流被 300 s 预算伪判为 Timeout（`lon` runner 的冻结口径） |
| `tools/lsu_campaign.py` | 删除 `WL_BLOCKED["MiBench"]` | 理由事实错误；三件套在盘上齐备（§3.1） |
| `tools/lsu_campaign.py` | 改写 `MODEL_BLOCKED["T08"]` 的理由为事实陈述 | 原理由（compile-unverified/pilot pending）已被真机证伪；保留条目以免无声解锁 |
| `tests/test_lsu_fs_infra.py` | 新增 `[5]` FS-INFRA 24 行逐行断言（12 FS / 9 模式未实现 / 3 T08） | 任何一行无声改判都会 fail |
| `tests/test_lsu_fs_infra.py` | 新增 `[6]` W1 19 行断言（17 解锁且 `--cmd` 实存 / 2 精确 F0-span / T 模型不变 / `SE_W1_TIMEOUT`） | 同上 |
| `tests/test_lsu_runid_map.py` | 新增 W1 口径一致性断言（runid_map 视为可跑者，campaign 不得负载级拒跑） | 把 19 行冲突**机械封口** |

验证命令与真实输出：

```
$ python3 tests/test_lsu_fs_infra.py
... SKIPPED (2): ['FS asset inventory', 'FS checkpoint inventory']
ALL PASS                                                    (rc=0)
# 2 项 SKIP 的原因：本 worktree 无 3GB gem5-fs 子模块，且未设 LSU_FS_DIR（不假报）

$ python3 tests/test_lsu_runid_map.py
... FAILURES: 无                                            (rc=0)

$ python3 -m pytest tests/ -q
16 passed, 5 errors in 1.47s
# 与基线提交 302ec9cf 完全相同（5 个 error 全在 tests/test_claim_concurrency.py，
# 基线既有：该文件用自定义 check 而非 pytest fixture）——零回归
```

## 6. 未验证 / 诚实边界

1. **T02/T10/T04-F2/F6/T01-F1/F2 未逐行真机运行**（结构裁决，§2.1）：其 faultType
   的代码路径已由同族真机运行证明可达，但**该行自身**没有本轮运行记录。
2. **T08-F4/F6-W4 未实测**：F4 的落点约在 9.9万–14.1万个 walk 事件之后，
   FS run 在该预算内能否产出这么多 walk 事件**没有实测数据**；F6 会在第 1 个
   walk 事件即丢弃（读代码推断，未跑）。因此 §2.3 **未代为移除** `MODEL_BLOCKED["T08"]`。
3. **S01-F0-W1 / S02-F0-W1 保持阻塞**：需要一次 `w1_all` 上的 F0 跨度普查
   （纯普查 pass，tier=F0 + span=1000000，全程约 7.4 h wall）——**本轮预算不足，
   未跑，也未编造 span 数字**。
4. **W1 行级真机裁决未做**：需要正式 campaign（每行 7.4 h 起步），用户明令
   **不启动正式 campaign**。本轮只做到"路径合法 + 冒烟启动"。
5. **mask 域问题（T03，§4.1）**：属于注入器质量缺陷（mask 应约束在 pfn 字段内），
   需改 C++ 并重编。本 worktree **禁 build**，故只登记、不修。
6. **segment：`tests/test_lsu_fs_infra.py` 的资产面 2 项 SKIP** 是设计行为
   （无 3GB 子模块时不假报），非失败。
7. gem5 运行预算使用 4/6。

## 7. 编排方在集成时要做的事

1. **合并三处改动**：`tools/lsu_campaign.py`、`tests/test_lsu_fs_infra.py`、
   `tests/test_lsu_runid_map.py`（本报告文件本身）。
2. **决定 T08 的 `MODEL_BLOCKED`**：F0 已获真机断言（§4.3），建议按 C11/C12/L04/P06/A07
   先例**删除该条目**并保留 F4/F6 的未实测注记；若不删，请至少采纳本轮的
   **事实订正**（不再是 "compile-unverified/pilot pending"）。
3. **gate 复核**：`--allow-blocked-models` 的存在是因为 `MODEL_BLOCKED` 与"要证据才能删"
   构成死锁（R4-6-T08 §4.0）；本轮再次实测确认该开关工作正常（T08 三行
   `[allow-blocked]` 回显 + `model_blocked_reason` 落 JSON）。
4. **普查 S01/S02 的 w1_all F0 跨度**（§6.3）后方可解锁这 2 行。
5. **不要重跑 T01**（R4-6.0 已固化）；不要把本轮的 T03/T04/T08 outdir
   （`/tmp/r4-7-fsinfra/…`）当作正式 campaign 结果——它们是**行级复验**产物。
6. **正式 campaign 仍未启动**（用户明令）。
