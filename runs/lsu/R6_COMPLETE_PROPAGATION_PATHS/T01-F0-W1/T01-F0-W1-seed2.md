# T01-F0-W1 seed2 故障传播与最终结局

## 1. 实验身份与复现信息

| 项 | 值 |
|---|---|
| RunID | `T01-F0-W1` |
| seed | `2` |
| sample_run_id | `s2` |
| 单元 | `L1d-TLB`（矩阵"单元"；注入器 `CHAOSArmTLB`，位点 `arm_tlb_lookup_hit`） |
| fault model | 矩阵原文：随机选有效表项的 VPN tag 翻转 1 bit、注入后再次命中才计 activated。**证据实际翻转的是表项 PFN**（注入日志 `old_pfn/new_pfn`；状态 `pfn=`）。字段口径差异见 §2.2 与 §6。 |
| fault type | `单比特翻转`（`bit_flip`） |
| frequency tier | `F0` |
| requested tier | `F0` |
| effective tier | `F0` |
| tier enabled | `关闭(0)`（run.out `CHAOS_LSU_TIER_CAP: requested=F0 effective=F0 lookup_tier_enabled=0`） |
| workload 矩阵标签 | `MiBench-TC23 论文负载（blowfish、patricia、fft、gsm、dijkstra、rijndael、sha、bitcount、edge、smooth）` |
| run.out 实际 workload/readfile | `--readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS`——**与矩阵标签不一致**（实际是 TLB page-walk 探针，不是 MiBench）。详见 §6。 |
| 两轴状态 | chain_evidence_status=PASS；experiment_identity_status=WORKLOAD_IDENTITY_MISMATCH；overall_experiment_status=NOT_MIBENCH_RESULT；WORKLOAD_GAP 见第 6 节 |
| 完整启动命令 | `gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F0-W1_s2/T01-F0-W1/seed2 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type bit_flip --tlb_rng_seed 2 --chaos_propagation --prop_run_id T01-F0-W1 --prop_sample_run_id s2` |
| source head | `N/A`（manifest 无 `source_head`） |
| binary source head | `d1543872e155943893fdd6d18a489ff7c372d97d` |
| binary path | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| binary SHA-256 | `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d` |
| analysis tool head | `4af986f726a6791f441130dee19eca0711e0b38f`（本 doc set 引入提交；未重跑 gem5） |
| checker SHA-256 | `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44` |
| evidence root | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F0-W1_s2/T01-F0-W1/seed2` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F0-W1_s2/manifest.json`（`exit_code=null`，真实退出码在 `.exit_code`） |
| 正常 EOF | **是**（解压后 297442 字节，EOF 无异常） |
| exit_code | `0`（`.exit_code`；manifest 字段为 null） |
| truncated | **False** |
| stats 是否有效 | **是**：完整 footer；`simTicks=932588145`、`simInsts=382169`、`finalTick=238882385160` |
| 原始事件数 | `433` |
| fault_id 数量 | `1` |
| 是否经过离线 regrade | **否** |

补充：DTLB=32 / LQ=16 / SQ=16；检查点 `cpt.237949797015`；manifest `run_mode=standalone-single-seed`。

## 2. 完整故障传播过程：从注入到最终结局

终局是真实 L5：`errant_commit`（`event_id=283`，tick=`237951341802`）。祖先链 18 条：

`0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 82 → 83 → 84 → 85 → 86 → 87 → 88 → 89 → 283`

tick 段：237950233911、237950235576、237950235909、237950340471、237950341137、237950341470、237951341802，单调不降。**本 seed 的 fault 1 流里没有 `tlb_translate_result` 事件**（锚点为 `tlb_pfn`，`path_event_ids=['0','1','2','3','89','283']`），也就是说翻译结果比对机制没有在该次翻译上执行——缺失是结构性缺席，不是 `NoFault` 或 0。

### 2.1 故障注入前的正常状态

VA=`0xffffffc009483eb8`（页内偏移 `0xeb8`）。注入事件本身没有 `request_id`/`dyn_inst_seq`，紧接着的 `tlb_lookup`/`tlb_pfn` 以 `request_id=0`/`dyn_inst_seq=0`（`corr=addr_fallback`）记录，随后 `cache_access` 才落定为 `request_id=32`/`dyn_inst_seq=32`（身份变化见 §2.4）。表项 `entry_index=0`、`walk_id=0`，注入前状态：`vpn=ffffffc009483`、`asid=206`、`valid=1`、`global=1`、`pfn=81d75`、`ap=0`、`mtype=2`、`page_size=1000`（4 KiB），正常 PA=`0x81d75eb8`。访问类型（load/store）在本链未记录，`N/A`。

### 2.2 故障具体如何注入

`event_id=0`，tick=`237950233911`，`site=arm_tlb_lookup_hit`，`fault_id=1`，`corr=origin`，`field=bit_flip`。注入日志 `Mask: 0x400`，即 PFN 第 10 位。原 PFN `0x81d75` 异或后得 `0x81975`：把这句话讲清楚——第 10 位由 0 变 1，表项保存的 PFN 从 `0x81d75` 变成 `0x81975`，其余位不变。第 10 位在物理地址里对应第 22 位，仍在有效 PA 宽度内，所以有效物理地址从 `0x81d75eb8` 变成 `0x81975eb8`，`effective_pa_changed` 为真。

注入符合"单次 XOR、有效表项、下游读取才计激活"；字段是 PFN 而矩阵写 VPN tag（§6）。

### 2.3 TLB 查询与地址翻译

`event_id=1`（`tlb_lookup`，parent=0，tick=`237950233911`，`request_id=0`，`dyn_inst_seq=0`，`corr=addr_fallback`，`entry_index=0`，`walk_id=0`）记录 `field=post_lookup`，`before=81d75`、`after=81975`；state 对照：`pfn=81d75→81975`，`pa=81d75eb8→81975eb8`，其余字段不变。

`event_id=2`（`tlb_pfn`，parent=1）独立记录物化结果：`pa=81975eb8`、`state_before=81d75eb8`、`state_after=81975eb8`。这是本 seed 的 L2 锚点。

关键结构事实：**没有 `tlb_translate_result`**。因此没有任何事件把 requested PA 与 effective PA 作比较，也没有任何 `contained=1` 的 L2 裁决。TLB 交给 LSU 的错误 PA（`0x81975eb8`）没有被翻译层拦下；这与 T01-F0-W4 的含住 seed 形成鲜明对照——那两个 seed 都有 event 3 的 `effective_pa_unchanged` 裁决。

### 2.4 错误如何进入 LQ/SQ/LSQ

本链没有 `lsq_push`/`lq_read`/`sq_execute`/`sq_writeback`/`lq_complete`/`sq_complete`，因此"进入队列"的具体动作记为 `N/A`（证据缺席）。但错误 PA 确实进入访存路径：`event_id=3`（`cache_access`，parent=2，tick=`237950235576`）以 `request_id=32`、`dyn_inst_seq=32`、`corr=addr_fallback` 访问 `pa=81975eb8`。这是本链唯一的身份切换（0/0 → 32/32）；`corr=addr_fallback` 记录了这次 addr 关联，parent 指针保证它仍属同一祖先链。

### 2.5 错误如何经过 cache 和 MSHR

两次访问、两次未命中、两次 MSHR 分配、两次填充与释放：

- 第一次：`event_id=3` 访问 `pa=81975eb8` → `event_id=4`（`cache_return`）`field=miss` → `event_id=5`（`mshr_alloc`）`cache_line=81975eb8`、`mshr_id=1`、`state_after=mshr_allocated`。
- 第二次：`event_id=6`（`cache_access`，parent=5，tick=`237950235909`）访问同一行的行基址 `pa=81975e80` → `event_id=7` `miss` → `event_id=8`（`mshr_alloc`）`cache_line=81975e80`、`mshr_id=2`、`state_after=mshr_allocated`。
- 填充：`event_id=82`（`mshr_fill`，parent=8，tick=`237950340471`）`mshr_id=2`、`state_after=filled`；`event_id=83`（`cache_fill`）填 `cache_line=81975e80`；`event_id=84`（`mshr_free`）`mshr_id=2`、`state_after=mshr_freed`。
- 第二次填充：`event_id=85`（`mshr_fill`，parent=84，tick=`237950341137`）`mshr_id=0`、`state_after=filled`；`event_id=86`（`cache_fill`）再填同一行；`event_id=87`（`mshr_free`）`mshr_id=0`、`state_after=mshr_freed`。

状态迁移解释：miss→allocate（请求挂起）→fill（下层数据到）→cache_fill（行写入 L1D）→free（资源释放）。`mshr_id=0` 的第二次 fill/free 是事件流原值，本文不改写。为什么仍是同一 fault：全部事件的 `fault_id=1`、parent 连续，且地址都来自同一个错误 PA 所在行。注意第一次访问的 MSHR 1 在本主链上没有 fill/free（在旁支里），所以本文件不对它作填充描述。

### 2.6 污染如何返回处理器状态

`event_id=88`（`resp`，parent=87，tick=`237950341470`，`request_id=32`，`corr=addr_fallback`，`va=81975eb8`）返回响应；`event_id=89`（`taint_reg`，parent=88，同 tick）记录 `before=clean`、`after=tainted`、`va=81975eb8`、`dyn_inst_seq=32`。这是存储→CPU 边界。证据限制：无 `arch_reg`/`phys_reg`，无法给出寄存器号。

### 2.7 最终传播终局

真实 L5：`errant_commit`（`event_id=283`，parent=89，tick=`237951341802`），`detection_layer=L5`、`contained=0`、`outcome=errant_commit`、`corr=taint_prop`，记录 `dyn_inst_seq=391`、`pc=ffffffc0087b1000`、`commit_seq=161`。错误提交由一条更年轻的指令兑现，说明污点沿寄存器依赖传播。为什么没被提前消除？因为本 seed 既没有 `tlb_translate_result` 比对，也没有任何 `contained=1` 的 L2/L4 收口；提交前不存在拦截点。`chain_end`（`event_id=380`，tick=`238882385160`，`outcome=errant_commit_seen`，`containment_reason=squash_replay`）只是流关闭记录，不是 L5。

### 2.8 从传播终局到系统表现

L5 `errant_commit`；`provable_to=L5`；运行结局 `Crash`。run.out：

- `CHAOS_DETECT: layer=None contained=0 tick=237951341802 ptag=1 reason=errant_commit`
- `CHAOS_DETECT: layer=Hardware RAS contained=1 tick=237951586890 ptag=1 reason=squash_replay`（事后 squash，不能抵消 event 283）
- `[arm_chaos_fs] KERNEL OOPS under fault — exiting (classify: Crash/DUE per fs_mode)`

run.err：`Kernel oops in guest` + dmesg dump。guest dmesg：

- `[2.160000] Unable to handle kernel paging request at virtual address 0b8542c0087b0c40`
- `[2.160000] Internal error: Oops: 86000004 [#1] PREEMPT SMP`

注入 tick=`237950233911`，错误提交 tick=`237951341802`，传播延迟 **1,107,891 ticks**。L5→Crash 因果成立（先提交、后 Oops）。链终止 tick=`238882385160`。负载未跑到应用 oracle 行，最终数据正确性不可判。

### 2.9 实际通过的单元（主链）

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| L0 注入器 | 有效表项 | PFN bit10 置 1 | 污染 PFN | 故障源 |
| L1 DTLB lookup | 命中查找（req 未盖戳） | 读到 `pfn=81975` | 污染表项，PA=`81975eb8` | 激活且 PA 改变 |
| L2 DTLB→MMU PA | 污染 PFN + 偏移 | 物化 | `pa=81975eb8` | 错误地址成形 |
| L2 MMU translate result | — | — | — | `N/A`：本 fault 无该事件（比对缺席） |
| L3 L1D | 错误 PA 两次访问 | 两次 miss | `cache_return miss` ×2 | 错误地址被消费 |
| L3 MSHR | 两次 miss | 分配 MSHR 1/2，填充并释放（2、0） | fill/free 序列 | 请求挂起与回收 |
| L3 L1D→core resp | 填充完成 | 返回响应 | `resp`（req=32） | 污染回到核心 |
| L4 taint/regfile | response | clean→tainted | 污染状态 | 存储→CPU 边界 |
| L5 ROB/commit | 污染状态 | 首次错误提交 | `errant_commit, dseq=391` | 架构可见错误 |
| LQ/SQ | — | — | — | `N/A`（本链无队列事件） |

**整链一句话总结**：本 seed 把 DTLB 表项 PFN 的第 10 位置 1，有效 PA 由 `0x81d75eb8` 变为 `0x81975eb8`；该翻译没有 `tlb_translate_result` 比对，错误 PA 被 L1D 两次未命中并分配 MSHR 1/2、经 fill/free 与 `resp` 返回，`taint_reg` 把污点带入寄存器，最终由更年轻的指令（`dyn_inst_seq=391`）在 L5 完成真实错误提交，运行以 guest 内核 Oops 结束。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

`CHAOS_LSU_TRIGGER: attempted=150160 eligible=2 injected=1`；`numFaultsInjected=1`；注入日志 1 条。三处一致（attempted>0）。污染值被 lookup 读取、被 cache 消费，属于 activated。

### 3.2 故障传播类型

**address 型**，下游表现为 **wrong cache line**（访问 `0x81975eb8`/`0x81975e80`）。不是 data/permission/control-state 型（相应字段未变）；timing 上的延迟只是未命中的副作用。

### 3.3 首个不可逆传播点

`event_id=2`（`tlb_pfn`）：错误 PA 在此物化，且本 seed 没有 `tlb_translate_result` 去撤销，因此从此刻起结构上已无可挽回。`event_id=3` 是错误地址第一次被真实消费；两者分别是"决定"与"后果"。

### 3.4 检测与掩蔽机制

候选机制：翻译结果 PA 比对（本 seed 缺席）、权限/对齐异常（未触发）、ECC/parity（`protection: model=none bits=1 -> Raw`）、squash/replay（event 309，发生在错误提交之后）、commit 前检查（无拦截）。实际只有提交端的 `CHAOS_DETECT reason=errant_commit` 记录。盲点：当 PA 改变且翻译结果比对缺席时，整条路径没有端到端检测；guest Oops 是后果，不是检测。

### 3.5 最终 SDC 风险判断

存在真实 errant commit 与架构可见错误，运行 Crash，故不判 SDC。静默期存在：event 89（taint_reg）→ event 283 之间，污染值被 61 条 consumer 事件观测（10 条 summary、`logical_total=56`、conservation ok）。本 seed 没有应用 oracle 行，**最终数据正确性不可判**；不能仅凭 errant_commit 宣称 SDC。

### 3.6 与同 RunID 其他 seed 的关系

- 注入位点相同；掩码 seed1=`0x20000`（bit17）、seed2=`0x400`（bit10）、seed3=`0x10000`（bit16）。
- PA：seed1 `81d75fa8→a1d75fa8`；seed2 `81d75eb8→81975eb8`；seed3 `81d75eb0→91d75eb0`。
- 终局：三者都是 L5 `errant_commit`（118/283/293），`dyn_inst_seq` 都是 391、`pc` 都是 `ffffffc0087b1000`。
- 运行结局：三者都是 Crash；三者的 terminal/dmesg 哈希完全相同（同一 Oops 签名）。
- 结构差异：seed1/seed3 有 `tlb_translate_result`（`effective_pa_changed, contained=0`）；seed2 没有该事件。三者都没有被含住，差异只影响"是否留下一次显式的放行记录"，不改变终局。

## 4. 完整主链事件表

`mask` 取自注入日志；`layer` 用 TLB family 映射。本链 18 条，逐条列出。

| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 237950233911 | — | `inj` | L0 | CHAOSArmTLB | 1 | origin | — | — | ffffffc009483eb8 | — | — | — | 81d75 | 81975 | 81d75 | 81975 | 0x400 | — | — | — | — | — | field=bit_flip | 有效表项、命中位点 | PFN bit10 置 1 | 故障进入存储 |
| 2 | 1 | 0 | 237950233911 | 0 | `tlb_lookup` | L1 | DTLB lookup | 1 | addr_fallback | 0 | 0 | ffffffc009483eb8 | — | — | — | 81d75 | 81975 | 81d75 | 81975 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75eb8 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81975;ap=0;mtype=2;page_size=1000;pa=81975eb8 | — | — | — | field=post_lookup | 命中查找 | 污染 PFN + 错误 PA | 激活 |
| 3 | 2 | 1 | 237950233911 | 0 | `tlb_pfn` | L2 | DTLB→MMU PA | 1 | addr_fallback | 0 | 0 | ffffffc009483eb8 | 81975eb8 | — | — | 81d75 | 81975 | 81d75 | 81975 | — | 81d75eb8 | 81975eb8 | — | — | — | field=bit_flip | 污染 PFN | 错误 PA 物化 | 不可逆点 |
| 4 | 3 | 2 | 237950235576 | 1665 | `cache_access` | L3 | L1D | 1 | addr_fallback | 32 | 32 | ffffffc009483eb8 | 81975eb8 | — | — | — | — | — | — | — | — | — | — | — | — | — | 错误 PA + 真实请求 | 首次访问 | 错误被消费 |
| 5 | 4 | 3 | 237950235576 | 0 | `cache_return` | L3 | L1D | 1 | addr_fallback | 32 | 32 | — | 81975eb8 | — | — | — | — | — | — | — | — | — | — | — | — | field=miss | 首次未命中 | 需要下层 | 未命中，需下层 |
| 6 | 5 | 4 | 237950235576 | 0 | `mshr_alloc` | L3 | MSHR | 1 | addr_fallback | 32 | 32 | — | — | 81975eb8 | 1 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | 第一次 miss | 分配 MSHR 1 | 请求挂起 |
| 7 | 6 | 5 | 237950235909 | 333 | `cache_access` | L3 | L1D | 1 | addr_fallback | 32 | 32 | ffffffc009483eb8 | 81975e80 | — | — | — | — | — | — | — | — | — | — | — | — | — | 同一行基址 | 第二次访问 | 再次消费 |
| 8 | 7 | 6 | 237950235909 | 0 | `cache_return` | L3 | L1D | 1 | addr_fallback | 32 | 32 | — | 81975e80 | — | — | — | — | — | — | — | — | — | — | — | — | field=miss | 第二次未命中 | 需要下层 | 未命中，需下层 |
| 9 | 8 | 7 | 237950235909 | 0 | `mshr_alloc` | L3 | MSHR | 1 | addr_fallback | 32 | 32 | — | — | 81975e80 | 2 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | 第二次 miss | 分配 MSHR 2 | 请求挂起 |
| 10 | 82 | 8 | 237950340471 | 104562 | `mshr_fill` | L3 | MSHR | 1 | addr_fallback | 32 | 32 | — | — | 81975e80 | 2 | — | — | — | — | — | — | filled | — | — | — | — | 下层数据 | MSHR 2 填充 | 数据就绪 |
| 11 | 83 | 82 | 237950340471 | 0 | `cache_fill` | L3 | L1D fill | 1 | addr_fallback | 32 | 32 | — | 81975e80 | 81975e80 | — | — | — | — | — | — | — | — | — | — | — | — | 填充数据 | 行写入 L1D | 行可用 |
| 12 | 84 | 83 | 237950340471 | 0 | `mshr_free` | L3 | MSHR | 1 | addr_fallback | 32 | 32 | — | — | 81975e80 | 2 | — | — | — | — | — | — | mshr_freed | — | — | — | — | 填充完成 | 释放 MSHR 2 | 资源回收 |
| 13 | 85 | 84 | 237950341137 | 666 | `mshr_fill` | L3 | MSHR | 1 | addr_fallback | 32 | 32 | — | — | 81975e80 | 0 | — | — | — | — | — | — | filled | — | — | — | — | 再次填充 | `mshr_id=0` 填充 | 原值保留 |
| 14 | 86 | 85 | 237950341137 | 0 | `cache_fill` | L3 | L1D fill | 1 | addr_fallback | 32 | 32 | — | 81975e80 | 81975e80 | — | — | — | — | — | — | — | — | — | — | — | — | 填充 | 行再次写入 | 行可用 |
| 15 | 87 | 86 | 237950341137 | 0 | `mshr_free` | L3 | MSHR | 1 | addr_fallback | 32 | 32 | — | — | 81975e80 | 0 | — | — | — | — | — | — | mshr_freed | — | — | — | — | 填充完成 | 释放 `mshr_id=0` | 资源回收 |
| 16 | 88 | 87 | 237950341470 | 333 | `resp` | L3 | L1D→core resp | 1 | addr_fallback | 32 | 32 | 81975eb8 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | 响应返回 | 污染回到核心 | 污染回到核心 |
| 17 | 89 | 88 | 237950341470 | 0 | `taint_reg` | L4 | taint/regfile | 1 | addr_fallback | 32 | 32 | 81975eb8 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | 响应 | clean→tainted | 存储→CPU 边界 |
| 18 | 283 | 89 | 237951341802 | 1000332 | `errant_commit` | L5 | ROB/commit | 1 | taint_prop | — | 391 | — | — | — | — | — | — | — | — | — | — | — | 0 | L5 | errant_commit | — | 污染状态 | 首次错误提交 | L5 逃逸 |

## 5. 相关旁支与未进入最终主链的事件

本 seed 共 433 条事件，全部 `fault_id=1`；主链 18 条，其余 414 条（含 `chain_end`）为旁支。

- `request_fork` 52 条：`addr_fallback_broadcast`，大多从 `source_event_id=8` 出发（`old_request_id=32`，`new_request_id=34/35/37/38/40/41/43/44/…`）；未回流终局祖先。
- 兄弟请求：58 条 `cache_access`、58 条 `cache_return`、12 条 `mshr_alloc`、29 条 `mshr_merge`、12 条 `mshr_fill`、12 条 `cache_fill`、12 条 `mshr_free`、51 条 `resp`、52 条 `taint_reg`、4 条 `lq_complete`，覆盖 54 个 request_id。
- `consumer` 61 条：10 条 summary、`emitted=10`、`suppressed=46`、`logical_total=56`、`distinct_dyn_seq=53`、`conservation=ok`、`by_outcome=sd_observed`。
- `squash_masked` 1 条：`event_id=309`，tick=`237951586890`，事件自身 `detection_layer=L4`、`contained=1`、`outcome=masked`、`reason=squash_replay`、`dyn_inst_seq=520`；它在错误提交之后，属更年轻指令的 squash，**不能**改写成 L5，也不能抵消 event 283。
- `chain_end`（event 380）为生命周期收口。

旁支不构成第二条终局祖先，但说明同一错误地址被大量兄弟请求消费（56 个逻辑消费者）。

## 6. 最终判定与证据完整性

| 项 | 值 |
|---|---|
| terminal | `full`（真实 L5） |
| provable_to | `L5` |
| propagation terminal event | `errant_commit`，event_id=283，tick=237951341802，L5 |
| run outcome | `Crash` |
| admitted | `True`（`full_chain`，violations=[]） |
| certified | `True` |
| violations | `[]` |
| truncated | `False` |
| gzip EOF | 正常 |
| stats validity | 有效 |
| conservation | `ok`（10+46=56） |
| count_contradiction | 否（attempted=150160>0；injected=1=stats=1） |
| campaign/checker agreement | 一致（seed2 outcome=Crash；terminal=full） |
| CHAIN_DEMONSTRATED | 是 |
| COMPLETE_3_OF_3 status | 三 seed certified；本 seed `COMPLETE_L5` |
| chain_evidence_status | **PASS** |
| experiment_identity_status | **WORKLOAD_IDENTITY_MISMATCH** |
| overall_experiment_status | **NOT_MIBENCH_RESULT** |
| verdict | **NOT_MIBENCH_RESULT**（chain evidence PASS；载体为 `tlb_probe.rcS`，不是 MiBench-TC23 结果） |

**WORKLOAD_GAP（本轮不重跑）**：矩阵把本 RunID 标为 `MiBench-TC23 论文负载`，但本 seed 的 `run.out` 实际 `--readfile` 是 `configs/fs/tlb_probe.rcS`。因此本文件只能证明 **`tlb_probe.rcS` 载波下的传播链**，不能证明 MiBench-TC23 条件下的结果。矩阵标签保持原样，不以“实际载体为准”消除身份差异；补跑真实 MiBench FS workload 作为独立 WORKLOAD_GAP 记录。


**REVIEW_REQUIRED 理由**：链一致性、认证、L5 见证全部通过；但工作负载身份与矩阵不符——矩阵标 `T01-F0-W1` 为 MiBench-TC23，run.out 与 terminal 证明实际运行 `tlb_probe.rcS`；矩阵"记录状态"仍写 `blocked(fs-infra: SE has no MiBench FS pipeline)`。工作负载是 cell 契约的一部分，必须人工复核后才能把该 cell 解释为 MiBench 结果。

一致性自检：18 个引用事件全部存在；parent 连续且先于 child；叙事顺序=ancestry；tick 单调；无跨 seed 混用；VA/PFN/PA/before/after/mask 来自本 seed；request_id/corr/fault_id 一致（并解释 0→32 的身份切换）；终局与报告一致；L5 见证是真实 `errant_commit`；每单元给出输入/变化/输出/意义；本章按本 seed 数据写成；无 child 先于 parent；SDC 结论未越界。

**其它缺口**：字段口径（VPN tag vs PFN）；manifest `exit_code=null`；`taint_reg` 无寄存器号；本 fault 无 `tlb_translate_result`。
## 7. 原始证据与文件哈希

| 证据 | 绝对路径 | SHA-256 | 字节 | mtime |
|---|---|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F0-W1_s2/T01-F0-W1/seed2/prop_evt.txt.gz` | `af4babc5751b56243804819d52aeb6c8bb252deee27beda928f58684c73a6b29` | 16240 | 2026-10-27T14:42:50 |
| chain_report（权威） | `.../seed2/chain_report.json` | `f77590258aaab8f3a4455f0e3606071eab29197f7bf9869e12273cb5505f97c8` | 10661 | 2026-10-27T14:42:51 |
| authoritative regrade | `N/A` | — | — | — |
| run.out | `.../seed2/run.out` | `752c52df7c5ec783ba983119b13da3e75465c5d0c29c90d6a0d34e9b6ceb0c35` | 2299 | 2026-10-27T14:42:51 |
| run.err | `.../seed2/run.err` | `e21be1f4c25d72f1e8f2b2ac20c742d8d01ad0d1b327608d5c362afb83958e74` | 1726 | 2026-10-27T14:42:51 |
| stats.txt | `.../seed2/stats.txt` | `6c87f9e6f55b20f05c906834134c37cf4fac6d1f4544de1098922ab459172934` | 381972 | 2026-10-27T14:42:51 |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F0-W1_s2/manifest.json` | `2ba5d6ec1f1fe0a7263e29335f2153c35e26960b63f82d500842e1cbc1c997b0` | 1438 | — |
| 启动命令记录 | run.out `command line:` | 同 run.out | — | — |
| binary | `.../r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` | `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d` | — | — |
| binary source head | `d1543872e155943893fdd6d18a489ff7c372d97d` | — | — | — |
| analysis tool | `.../tools/lsu_chain_check.py` | `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44` | 69565 | 2026-10-27T00:59 |
| 症状证据（guest dmesg） | `.../seed2/board.workload.dmesg` | `6fdabf80e1d1c25f0898f2221e1bd70f3fd08b97fce028ba2c4160327e3ee09b` | 13938 | 2026-10-27T14:42:50 |
| 辅助证据（terminal） | `.../seed2/board.terminal` | `b1776be2415f07fcab3f4ce0879a84c7fa247ca1739d8b1ab978444a4f68a3db` | 1839 | 2026-10-27T14:42:50 |

- 权威目录：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F0-W1_s2/T01-F0-W1/seed2`。
- 其它副本：`r6_n8` 系列内同 seed 的重复目录分类见 `R6-AUTHORITATIVE-EVIDENCE.md`；`OLD_BINARY_REFERENCE` 副本不得使用。
- 原始事件流未修改；未重跑 gem5；未运行 campaign。
