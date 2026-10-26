# 定向 pilot：Store Queue 节点补证 + Cache mshr_alloc 追证（真实运行）

> 目的：让 98 个 PARTIAL 按**真实证据**重判——此前 Store Queue 只观测到
> `lq_*`/部分节点，Cache 缺 `mshr_alloc`。
> **状态（R4-3 收口，2026-10-21）**：Store Queue 7/7、L1d-Cache 11/11 均已
> 取得真实观测；覆盖矩阵 199 PASS / 0 PARTIAL / 126 BLOCKED。§1 为历史
> 记录（SQ 首次补证），§2/§3 已按 R4-2/R4-3 实测结论改写。

## 1. Store Queue：`sq_writeback` / `sq_complete` 已取得真实证据（历史记录）

关键发现（实测）：`sq_execute/sq_writeback/sq_complete` 三个钩子都靠
`correlateRequestBySeq(dyn_seq)` 关联**由某个注入器开设的链**。
**`CHAOSLSQFwd`（S01/S02/S03/S08/S09）从不注册链**（`CHAOSLSQFwd.cc` 里
没有 `registerInjection`/`notePropEvt` 调用）——所以用 S01-F0-W5 跑，PRPO-EVT
流**恒为空**（实测 activated=0 且 prop_evt 无内容），这不是钩子问题而是
S 系注入器未接入追踪器。

而 S04–S07/S11/S13 走 `--agu_pre_mode`（PRE 家族），其路径**会在
`lsq.cc::pushRequest` 注册链**，因此能观测 SQ 节点。实测（正式 campaign 入口）：

| RunID | 载体 | 事件（种类） | SQ 节点 |
|---|---|---|---|
| S04-F0-W5 | sq_forward | inj, addr_form, lsq_push, lsq_sendfrag, mem_req, tlb_translate, resp, **sq_writeback, sq_complete**, chain_end | 2/3 |
| S05-F0-W5 | sq_forward | 同上 | 2/3 |

→ **Store Queue 单元能力 4/7 → 6/7**（本轮新增 `sq_writeback`、`sq_complete`）。

## 2. `sq_execute`：R4-2 已定论并真实观测（原"仍未观测"记载已被 R4-2 实测推翻）

原本文档在此登记"`sq_execute` 仍未观测（可能原因：注册时序）"。
R4-2（2026-10-20，binary `cb58c9ed01ed7eb7`）用 `--debug-flags=LSQUnit`
定向实测**定论**（详见 `round4_findings.md` §R4-2）：

- **双假设按载体分属**：(a) S04–S07/S11/S13（store 侧载体）的注册发生在
  **同一 `executeStore` 调用内**的 `initiateAcc()→writeMem→LSQ::pushRequest`
  PRE 钩子，旧钩子在函数顶部（先于注册）故查不到链；(b) S01/S02（转发污染
  载体）的受害指令是 load，生产 store 的执行**早于注入**——任何钩子位置都
  无法诚实地为该载体发射 sq_execute（结构性别缺，不是缺陷）。
- **修复**：sq_execute 钩子移到 `initiateAcc()` 之后。修复后 S04-F0-W5
  三 seed（正式 campaign 入口）全部观测 sq_execute（corr=seq_primary），
  **Store Queue 7/7**；S01/S02 诚实保持缺席。

## 3. Cache：`mshr_alloc` 已真实观测（R4-3，binary `2462dc0fcf1d3d96`）

### 3.1 此前的机理结论（仍成立）：注入行必须"先驱逐、再取回"

CHAOSCache 的故障注入点是**已存在的 valid line**（规格 "L1D 存在 valid
line"），因此被注入那一行本身不会 miss → 不会为该行分配 MSHR。要在同一行上
观测 `mshr_alloc`，必须让该行**先被驱逐、再被重新取回**（evict→refill）。
`first_clock` 单位是**周期**（×1000=tick；1000 → tick 1e6）。

### 3.2 R4-3 新定论：仅"驱逐再取回"还不够——钩子另有结构性缺陷（实测）

构造出可重复的 evict→refill 载体（见 3.3）后，`mshr_merge/mshr_fill/
mshr_free` 全部落流，**唯独 `mshr_alloc` 仍不出现**。`--debug-flags=Cache`
定向实测（`/tmp/r4t3_dbg/cache.log`）证明该行确实 miss 并分配了 MSHR：

```
47051620: l1d-cache-0: access for ReadReq [76e00:76e07] miss
47052390: l1d-cache-0: sendMSHRQueuePacket: MSHR ReadReq [76e00:76e07]
47057780: l1d-cache-0: recvTimingResp: Handling response ReadResp [76e00:76e3f]
```

即 miss→MSHR→fill 全链真实发生且地址关联命中，事件却缺席。根因在
`base.cc::handleTimingReqMiss` 的 mshr_alloc 钩子卫条件 `pkt->hasData()`：
**gem5 里 request 包不带 payload**——`ReadReq` 的 MemCmd 属性是
`{IsRead, IsRequest, NeedsResponse}`（`packet.cc` 命令表），**没有 HasData**
（只有 response 和 WriteReq 带数据）。该卫条件因此**结构性丢弃所有
demand-read miss**——恰是 "miss→MSHR allocate" 的规范场景。这也一并解释了
P01（预取链）只见过 merge/fill/free 而从未 alloc：SoftPFReq/HardPFReq 同样
无 HasData。修复：删去 `pkt->hasData()` 卫条件（eviction/WriteClean 在该
分支之前已走 writebuffer，到达钩子的必是分配 MSHR 的 miss；读/写/预取
一视同仁）。

### 3.3 载体设计：`workloads/directed/cache_mshr_refetch.c`（可重复 evict→refill）

- **几何**：L1D（B0）32KiB/2-way/64B → 256 组，组索引周期 16KiB。载体用
  **48KiB 连续 region（= 每组恰好 3 行）**：顺序全扫时每行到达前组内已有
  2 个更新行（2-way LRU）→ **每一轮全扫，region 的每一行都必然
  驱逐→demand miss→MSHR alloc（同行后续 7 个 8B load 合并 merge）→fill→free**。
- **时间窗**：blk registry 注册有效期 20M tick（`addrExpiryTicks` 默认），
  单轮实测 ≈28K CPU cycle ≈ 10.8M tick——注入后该行的下一次 miss 必然
  ≤1 轮（< 20M tick）落在窗口内（每 seed 实测恰好 2 轮可观测，第 3 轮起
  注册过期、事件停发——与窗口语义吻合）。
- **覆盖所有可抽中行**：每轮先做一次 noinline 栈帧读写（volatile 128B），
  栈行同样被全组驱逐→每轮重取；region 外的启动杂项行在 round 0 后被逐出
  且不再访问→注入时已非 valid、不可被抽中。
- **不 crash**：读出的值只进 fnv checksum（绝不当地址用）→ 链可走到
  chain_end。注入行被驱逐时若为脏（warm-up 写脏、fill 后 L1D 持 M 态），
  writeback 会把损坏数据带回 L2，refill 取回**损坏数据**→checksum 偏离
  golden（SDC）——故障经 MSHR refill 真实传播，非仅地址关联。
- **运行**（C09 模型 flags，与 campaign cache 家族一致；first_clock=40000
  →tick 40e6，落在 rounds 中段）：

```bash
CHAOS/gem5/build/ARM/gem5.opt --outdir runs/lsu/r4_t3_mshr/s<N> \
  configs/se/lsu_proxy.py --cmd workloads/directed/cache_mshr_refetch --cpu O3 \
  --chaos_l1d --l1d_first_clock 40000 --l1d_max_faults 1 \
  --l1d_target_field data_shift --l1d_rng_seed <N> \
  --chaos_propagation --prop_run_id C09-R4T3-MSHRREF --prop_sample_run_id s<N>
```

### 3.4 真机结果（6/6 seed 可重复）

| seed | 注入行 | mshr_alloc | merge | fill | free | alloc 行==注入行 | checksum |
|---|---|---|---|---|---|---|---|
| s1 | 76e00 | 2 | 13 | 2 | 2 | ✓（两轮均 76e00） | f3b0955ea267fbcd |
| s2 | 78180 | 2 | 13 | 2 | 2 | ✓ | c3d28eba9784c7a7 |
| s3 | 7ed40 | 2 | 14 | 2 | 2 | ✓ | 5e369e8bd43cb508 |
| s4 | 7e300 | 2 | 13 | 2 | 2 | ✓ | 0c3bbd31106d29a2 |
| s5 | 77780 | 2 | 14 | 2 | 2 | ✓ | 5a4d973167adc8f9 |
| s6 | 79500 | 2 | 13 | 2 | 2 | ✓ | c06fc424d6d75d0d |

**6/6 seed 全部出现 `mshr_alloc`，且 alloc 的 cache_line 与注入行逐 seed
一致**（golden=682fe66c2cbbec4b，全部偏离=SDC——损坏数据经 writeback→
refill 真实传播）。s1 第一轮的完整 ID 链（`runs/lsu/r4_t3_mshr/s1/`）：

```
kind=inj        tick=40000000  cache_line=76e00 (data_shift)
kind=cache_evict    tick=43823780  cache_line=76e00 corr=addr_fallback
kind=cache_writeback tick=43823780 cache_line=76e00 corr=addr_fallback
kind=mshr_alloc  tick=47051620 cache_line=76e00 mshr_id=1 corr=addr_fallback
kind=mshr_merge  tick=47052775 cache_line=76e08 mshr_id=1 corr=addr_fallback
kind=mshr_merge  tick=47055085 cache_line=76e10 mshr_id=1 corr=addr_fallback
kind=mshr_merge  tick=47055855 cache_line=76e18 mshr_id=1 corr=addr_fallback
kind=mshr_fill   tick=47057780 cache_line=76e00 mshr_id=1 fill_id=1 corr=addr_fallback
kind=cache_fill  tick=47057780 pa=76e00 fill_id=1
kind=mshr_free   tick=47057780 cache_line=76e00 mshr_id=1 corr=addr_fallback
```

`lsu_chain_check.py` 裁决：**L0→L1→L2→L3→L4→L5 全 proven，
terminal=full**（cache 家族首个走满 L5 的链）。

**归因口径（诚实声明）**：`mshr_alloc` 的 miss 地址即故障行本身
（cache_line==inj 行），分配的 MSHR **就是故障行的 MSHR**——不是同 run
里碰巧出现的其他 MSHR；但该关联是**地址关联**（blk registry，
`corr=addr_fallback`，R4-1 契约的显式 fallback 臂；cache 故障无 seq 可作
主键）。另有少量 merge 事件来自**相邻行**的 load（其 64B 关联窗口与注册
区间重叠、合并进的是相邻行自己的 MSHR，`mshr_id=0`=查无此行）——这是
correlateBlock 按块窗口匹配的既有语义，已按 corr 标注如实区分。

### 3.5 campaign 入口的诚实对照：C09-F0-W6（W6 载体）仍无 mshr 事件

正式 campaign 入口（`runs/lsu/r4_t3_c09w6/`，3 seed）跑既有 W6 cell
（cache_dirtyevict，first_clock 家族默认 1000）：

```
C09-F0-W6: phase=trial n_runs=3 activated=6 sdc=0 stop=seed-cap(3) cons=OK
```

三 seed 的 prop_evt **均无任何 mshr_* 事件**（seed1/3：cache_access/return+
消费链；seed2：tlb_fault 链）。机理：W6 是单遍相位结构，对故障行的重取发生
在 phase 4，距注入（tick 1e6）已超出 20M tick 注册窗；campaign 家族的
first_clock=1000 也无法在不改全体 C cell 语义的前提下调整。**W6 cell 语义
不变、如实保留**；可重复 evict→refill 的观测由 3.3 的定向载体承担
（pilot/证据性质，非正式 campaign）。

## 4. 覆盖矩阵变化（证据化口径，R4-3 后）

| 单元 | 需要节点 | 已观测 | 仍缺 |
|---|---|---|---|
| Store Queue | 7 | **7/7**（R4-2 sq_execute） | — |
| L1d-Cache | 11 | **11/11**（R4-3 mshr_alloc） | — |
| AGU/TLB/LQ/P | — | 全观测 | — |
| 原子与同步 | 6 | exmon_monitor/rmw/stxr 已观测 | `atomic_op`（O 系全部 BLOCKED=multicore-FS，载体不可用） |

**PASS/PARTIAL/BLOCKED = 199/0/126**（R4-2 前为 101/98/126）：199 个
非阻塞 cell 的全部规格节点均有真实运行证据；126 个 BLOCKED 均为外部
阻塞（FS/multicore/SPEC 许可）。证据文件 `pilot_evidence.json`（20 个
pilot，34 个 kind）与 `coverage_matrix.md` 已重生成。
