# T04-F0-W4 seed2 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T04-F0-W4`；seed：`2`；sample_run_id：`s2`
- 单元：`L1d-TLB`（L1 d-TLB，注入器 `CHAOSArmTLB`；注入点 site=`arm_tlb_lookup_hit`）
- fault model：`pfn_to_mapped_page`（故障类型：换值）。将命中项的 PPN 换成另一个当前合法、相同页大小的 PPN；VPN/ASID 保持一致；不生成任意随机位串。
- frequency tier：`F0` — 每次运行只注入 1 次；在 warm-up 后的 eligible event 中均匀抽样
- requested tier / effective tier / tier enabled：`CHAOS_LSU_TIER_CAP: requested=F0 effective=F0 lookup_tier_enabled=0`
- workload 矩阵标签：TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）
- run.out 实际 workload/readfile：`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/tlb_probe.rcS`（矩阵标签与实际 readfile 的差异如实保留，不推断）
- 完整启动命令：`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/T04-F0-W4/seed2 /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type pfn_to_mapped_page --tlb_rng_seed 2 --chaos_propagation --prop_run_id T04-F0-W4 --prop_sample_run_id s2`
- source head：`f680bbc274d0ab2dde8fd1b494dc795b9f544f2d`
- binary source head：`N/A`（该 manifest 不记录 binary_source_head；同 run 的 source_head 见上）
- binary path：`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256：`e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959`（本次对同一路径重算一致）
- analysis tool head：本次文档集分析工具 head=`4af986f726a6791f441130dee19eca0711e0b38f`；run 时 manifest.analysis_tool_head=`f680bbc274d0ab2dde8fd1b494dc795b9f544f2d`
- checker SHA-256：`baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`（`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/tools/lsu_chain_check.py`，65565 bytes）
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/T04-F0-W4/seed2`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/manifest.json`（SHA-256 `8c51599c7fc95522b54c4a5d7d7aa593feee9897a86d4ef89dd85eac2a877e1d`；1774 bytes；mtime `2026-10-25T19:33:33+0800`；该 manifest 的 seed 字段为 `3`）
- 正常 EOF：**是**（gzip 解压到 EOF 无错：True；`chain_report.truncated=False`，`evidence_truncated=False`）
- exit_code：`0`（gem5/oracle 报告值；manifest.exit_code=`0`，runroot `.done`=存在，`.exit_code`=存在）
- truncated：**False**
- stats 是否有效：**是**（stats.txt 以 `End Simulation Statistics` 结束；362831 bytes）
- 原始事件数：gzip 内 `PROP-EVT` 行 **65554** 条；`chain_report.event_count`=**64273**（不含 consumer 事件），差值为 consumer 摘要数 1281
- fault_id 数量：**1**（F0 每次运行只注入 1 次；注入日志只有 1 条命中记录）
- 是否经过离线 regrade：**否**（目录内无 `chain_report.regrade-*.json`；唯一离线重判 seed 是 T02-F2-W4 seed2，不属于本文件）

## 2. 完整故障传播过程：从注入到最终结局

本章只使用 T04-F0-W4 seed2 自己的事件流。终局见证是 event 21（`errant_commit`）；沿 `parent_event_id` 回溯得到 22 个单祖先事件（0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21），parent 全部位于 child 之前，tick 单调不减。`chain_report.path_event_ids=[0,1,2,5,20,21]` 只是层锚点（省略了 3、4、6–19），因此本章按完整祖先而不是该数组叙述。

### 2.1 故障注入前的正常状态

被注入的是一条 **load**（event 4 的 `lsq_push` 明确 `field=load`、`lq_idx=1`、`sq_idx=-1`），动态指令 `dyn_inst_seq=109`，`request_id=109`，VA=`0xffffff807fbce090`。注入前命中表项的 `state_before` 是：`vpn=ffffff807fbce`、`asid=206`、`valid=1`、`global=1`、`pfn=ffbce`、`ap=0`、`mtype=2`、`page_size=1000`、`pa=ffbce090`；查找命中在 way=0、entry_index=1，页内偏移 0x090。也就是说，正常 PFN 是 0xffbce，正常 PA 是 0xffbce090；VPN/ASID/权限/页大小均合法。

### 2.2 故障具体如何注入

event 0（`inj`，tick=`237950546931`）把命中项 PFN 从 `before=ffbce` 换成 `after=81d75`，`field=pfn_to_mapped_page`，VA=`0xffffff807fbce090`，`request_id=109`，`corr=origin`。注入日志给出 `Site: arm_tlb_lookup_hit` 和 `candidates: 1`：在本次运行的候选集合中只有一个合法替换页，因此注入器选了 0x81d75。数值上 0xffbce（1047502）→0x81d75（531829），两者都是 20 位合法 PFN；页内偏移 0x090 不变，PA 从 0xffbce090 变成 0x81d75090，`effective_pa_changed` 为真。没有 mask，因为这是整页换值而不是位翻转；VPN、ASID、页大小、权限都没有被改动，所以不会触发普通 page fault/permission fault。这与 T04-F0-W4 的 pfn_to_mapped_page 模型一致，也是 seed2 与 seed3 共享的同一确定性注入点（见 3.6）。

### 2.3 TLB 查询与地址翻译

event 1（`tlb_lookup`，parent=0）读取被改写的命中项：`state_before` pfn=ffbce、`state_after` pfn=81d75，`way=0`、`entry_index=1`、`walk_id=0`。event 2（`tlb_pfn`，parent=1）把 PFN 与偏移拼成 PA：`state_before=ffbce090`、`state_after=81d75090`，`pa=81d75090`。event 3（`tlb_translate_result`，parent=2）是翻译出口：`field=effective_pa_changed`，`before=ffbce090`、`after=81d75090`，`contained=0`、`outcome=NoFault`。同样，`contained=0/NoFault` 只说明 TLB 没有本层含住，不代表没有错误：两个页都是合法映射页，TLB 没有地址正确性 oracle。TLB 交给 LSU 的是 request_id=109、PA=0x81d75090 的 4 KiB load。

### 2.4 错误如何进入 LQ/SQ/LSQ

event 4（`lsq_push`，parent=3，tick=`237950547264`）明确这是 load：`pc=ffffffc0080116d8`、`lq_idx=1`、`sq_idx=-1`、`field=load`、VA=`ffffff807fbce090`；event 5（`lq_read`，parent=4，同一 tick）以 `request_id=109` 读取该 LQ 条目。输入是 TLB 的错误 PA；内部变化是 load 被压入 LQ 并由 LQ 读取；输出是 request_id=109 的 cache 访问；下一步 L1D/MSHR 会按 `pa=81d75090` 查找。这里没有 `sq_*` 事件，说明本 seed 的错误走 load 路径，而不是 store 路径。

### 2.5 错误如何经过 cache 和 MSHR

event 6（`cache_access`，parent=5）以 `pa=81d75090` 访问；event 7 的 `cache_return field=miss` 表明 miss；event 8 分配 mshr_id=1、cache_line=`81d75090`。随后 event 9 访问同一页的 `pa=81d75080`，event 10 再次 miss，event 11 分配 mshr_id=2。event 12（`mshr_fill`，parent=11）以 fill_id=1 填充 mshr 2，event 13 `cache_fill` 填入 `pa=81d75080`，event 14 `mshr_free` 释放；event 15（`mshr_fill`，parent=14）以 mshr_id=0、fill_id=2 再填一次，event 16 `cache_fill`、event 17 `mshr_free` 收口。错误行始终是 0x81d75 页内的行，`corr=addr_fallback`；两次填充是 MSHR 重填/合并的既有序列，不是第二次注入。cache_access 本身没有 hit/miss 字段，必须由 cache_return 的 `field=miss` 判定；这一点在原始流中是明确的。


### 2.6 污染如何返回处理器状态

这条 seed 是 **load** 路径：event 18 的 `resp`（`request_id=109`）把 cache/MSHR 的响应交回，event 19 的 `lq_complete` 完成后，event 20 的 `taint_reg` 把 `before=clean` 改成 `after=tainted`，`arch_reg=28`、`phys_reg=96`、`VA=81d75090`、`corr=seq_primary`。与前一个 seed 不同，这里 trace 明确记录了寄存器身份：架构寄存器 x28、物理寄存器 96。`taint_reg` 是“存储结构→CPU 状态”的边界，因为在此之前错误表现为 cache line/MSHR/响应的地址与数据，之后它已写入寄存器状态；event 21 的 `errant_commit` 直接以 event 20 为 parent，链条没有额外的消费者跳转。

### 2.7 最终传播终局

终局是真实 L5：event 21，`kind=errant_commit`，`parent_event_id=20`，tick=`237950593884`，`dyn_inst_seq=109`，`commit_seq=88`，`pc=ffffffc0080116d8`，`detection_layer=L5`，`contained=0`，`outcome=errant_commit`，`corr=taint_prop`。它不是 `chain_end`；本 seed 的 `chain_end` 是 event 52795（tick=`337969869489`），只是传播流在仿真预算结束时的收口记录。

为什么没有被提前消除：这条祖先链上没有 `squash_masked`、没有 replay、没有 `contained=1` 的事件；L4 只有 event 20 的 `taint_reg`。错误 load 在 LQ 完成后直接提交，结构没有第二次翻译或地址校验。为什么架构可见：`errant_commit` 越过提交边界，错误值已成为架构状态。

### 2.8 从传播终局到系统表现

- 传播链终局：L5 `errant_commit`，event 21，tick=`237950593884`；`provable_to=L5`。
- 运行结局：**Timeout**（`chain_report.oracle_outcome=Timeout`，`exit_code=0`）。`run.out` 的证据行只有 `CHAOS_DETECT: layer=None contained=0 tick=237950593884 ptag=1 reason=errant_commit` 与 `CHAOS_LSU_TRIGGER: injector=CHAOSArmTLB tier=F0 attempted=129374101 eligible=46 injected=1 ...`，**没有** KERNEL OOPS/PANIC 行；`run.err` 也没有 kernel 行。run 级 manifest 的 `timeout_triggered=True` 与本 seed 的受控 Timeout 一致。
- 注入 tick=`237950546931`，终局 tick=`237950593884`，传播延迟 **46953 ticks**。
- 因果链：L5 已发生，错误提交已经成立；但仿真没有在预算内正常终止，oracle 归为 Timeout。因此必须同时说两件事：**传播链完整到 L5**，但**运行没有正常结束**；Timeout 不抹去已证明的 L5，也不能把本 seed 说成“正常完成”。没有应用级输出 oracle，无法判断最终数据正确性。

### 2.9 主链单元输入/内部变化/输出/传播意义

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| DTLB（CHAOSArmTLB） | VA=ffffff807fbce090，命中 way=0/entry=1，正常 PFN=ffbce | PFN 替换为 81d75；PA ffbce090→81d75090 | request_id=109，PA=81d75090 | 错误地址进入 LSU；此 seed 的故障值是“另一个已映射页” |
| LQ | `lsq_push` lq_idx=1（load），`lq_read` request_id=109 | load 请求按错误 PA 读取 | LQ 请求进入 cache | 错误地址被 LQ 接受 |
| L1D cache | PA=81d75090 / line 81d75080 | `cache_access` → `cache_return field=miss` → `cache_fill` | miss 与 fill 行 | 错误物理行数据进入 L1D |
| MSHR | line 81d75080 | `mshr_alloc`（1/2）→`mshr_fill`（1/2）→`mshr_free` | 响应数据 | 错误行在 MSHR 中完成生命周期 |
| response / LQ complete | request_id=109 | `resp`→`lq_complete`（lq_idx=1） | 可交付的污染值 | 错误从存储域回到处理器 |
| register file（taint） | 完成的 load 数据 | `taint_reg` clean→tainted（x28/phys 96） | 被污染寄存器 | 存储→CPU 状态边界 |
| commit/ROB | dyn 109 到达提交边界 | 无 squash | `errant_commit`（L5） | 架构可见错误；传播终局 |


**一句话总括**：T04-F0-W4 seed2 在 tick 237950546931 把 VA=ffffff807fbce090 的 TLB 命中项 PFN 0xffbce 换回 0x81d75，错误 PA=81d75090 经 LQ（event 4/5）进入 L1D/MSHR（6–17），响应（18）与 `lq_complete`（19）把污染写入 x28/phys 96（20），event 21 真实错误提交；终局 L5 成立，运行结局是受控 Timeout，二者必须并列陈述。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

注入日志 1 条；`run.out` 的 `CHAOS_LSU_TRIGGER` 记录 `attempted=129374101 eligible=46 injected=1`；`stats.txt` 的 `numFaultsInjected=1`；`chain_report` 的 fault 数 1。三方一致，注入值被 event 1 的查找读取，并由 event 3/4/5 消费，因此 activated 是实证的。原始事件总数 65554（含 consumer 1281；chain_report.event_count=64273 为非 consumer 事件），不把 consumer 摘要当成独立故障。

### 3.2 故障传播类型

**地址型（address / wrong physical page）**：PFN 被整页替换，错误 PA 0x81d75090 进入 LQ/cache/MSHR。不是 data/位翻转（无 mask），不是 permission（ap=0 未变），不是 control-state，也不是 timing。错误最终表现为 load 返回另一个物理页的数据，但根因仍是地址翻译错误；因此用“错误物理页”而不是“错误 cache line”描述。

### 3.3 首个不可逆传播点

**event 3（`tlb_translate_result`，tick=237950546931）**：错误 PA 0x81d75090 在这一刻离开 TLB 并交付 LSU；之后只有 squash/replay 能在提交前撤销，而本链没有发生。event 20 的 `taint_reg` 把污染写入 x28/phys 96，是寄存器层的不可逆点；event 21 是架构层不可逆点。

### 3.4 检测与掩蔽机制

TLB 的 valid/global/ap/mtype/page_size 检查都通过；L1D/MSHR 不检查地址正确性；响应路径没有可见的地址校验。祖先链上没有 `squash_masked`/replay/contained 事件，因此没有检测机制在提交前含住它。检测盲区同样是“合法页替换”：只有权限/有效位检查，没有正确 PFN 的冗余。与 seed1 不同，本 seed 连晚于 L5 的 squash 也没有出现在祖先上；事件流里没有 `squash_masked` 计数（kind 计数为 0）。

### 3.5 最终 SDC 风险判断

真实 `errant_commit`（event 21）且架构可见；oracle 是 Timeout，不是 SDC。没有应用级输出 oracle，因此不能判断最终数据正确性；不能因为 errant_commit 就称 SDC。Timeout 说明仿真没有正常结束，但不会抹去已发生的 L5。最终分类：**Crash/Timeout 级运行结局下的真实 L5**；本文件不写 SDC。

由于没有应用级输出 oracle，最终数据正确性无法判断。

### 3.6 与同 RunID 其他 seed 的关系

seed2 与 seed3 共享同一注入 (tick=237950546931、VA=ffffff807fbce090、PFN 0xffbce→0x81d75、候选 1)，但两者 `prop_evt` SHA 不同（seed2 `f758…`、seed3 `850f…`），chain_end tick 也不同（seed2 337969869489、seed3 356484834324），因此是同一确定性注入点的独立运行，不是转抄。seed1 的注入点/地址方向/终局完全不同（seed1 是 VA=ffffffc009483fa8、PFN 0x81d75→0xffbce、Crash）。本文件只陈述 seed2 自己的字段。

## 4. 完整主链事件表

> 主链按终局见证的 `parent_event_id` 单祖先逐事件重建（parent 在前、child 在后）；同 tick 内按事件继承关系排列。`path_event_ids` 只作层锚点核对，不当作完整链。表中 `—` 表示该事件在原始流中无此字段，不是 0。

| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 237950546931 | — | inj | L0 | CHAOSArmTLB | 1 | origin | 109 | 109 | ffffff807fbce090 | — | — | — | ffbce | 81d75 | ffbce | 81d75 | — | — | — | — | — | — | — | 注入器选定该命中表项（site=arm_tlb_lookup_hit） | 表项 PFN ffbce→81d75 | 故障进入 DTLB 表项，下一次命中将读到被改写的 PFN |
| 2 | 1 | 0 | 237950546931 | 0 | tlb_lookup | L1 | CHAOSArmTLB/DTLB | 1 | seq_primary | 109 | 109 | ffffff807fbce090 | — | — | — | ffbce | 81d75 | ffbce | 81d75 | — | vpn=ffffff807fbce;asid=206;valid=1;global=1;pfn=ffbce;ap=0;mtype=2;page_size=1000;pa=ffbce090 | vpn=ffffff807fbce;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75090 | — | — | — | — | VA=ffffff807fbce090 的命中查找，request_id=109 | 命中表项返回 pfn=81d75 | 故障 PFN 被 TLB 查询读取，进入翻译路径 |
| 3 | 2 | 1 | 237950546931 | 0 | tlb_pfn | L2 | DTLB 表项 PFN | 1 | seq_primary | 109 | 109 | ffffff807fbce090 | 81d75090 | — | — | ffbce | 81d75 | ffbce | 81d75 | — | ffbce090 | 81d75090 | — | — | — | — | TLB 命中项中的 PFN 字段 | PA=81d75090（pfn=81d75） | 故障 PFN 与页内偏移拼成错误 PA |
| 4 | 3 | 2 | 237950546931 | 0 | tlb_translate_result | L2 | DTLB 翻译出口 | 1 | seq_primary | 109 | 109 | ffffff807fbce090 | 81d75090 | — | — | — | — | ffbce090 | 81d75090 | — | vpn=ffffff807fbce;asid=206;valid=1;global=1;pfn=ffbce;ap=0;mtype=2;page_size=1000;pa=ffbce090 | vpn=ffffff807fbce;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75090 | 0 | — | NoFault | — | 已带故障 PFN 的翻译请求 | effective PA=81d75090，effective_pa_changed=1 | TLB 把错误 PA 交付 LSU；错误地址正式进入存储管线 |
| 5 | 4 | 3 | 237950547264 | 333 | lsq_push | L3 | LSQ | 1 | seq_primary | — | 109 | ffffff807fbce090 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | dyn_inst_seq=109 的请求，VA=ffffff807fbce090 | 请求进入 LSU 队列 | 错误 PA 被 LQ/SQ 接受，后续 cache/MSHR 将按此地址访问 |
| 6 | 5 | 4 | 237950547264 | 0 | lq_read | L3 | LQ | 1 | seq_primary | 109 | 109 | ffffff807fbce090 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | dyn_inst_seq=109 的请求，VA=ffffff807fbce090 | request_id=109 | 错误 PA 被 LQ/SQ 接受，后续 cache/MSHR 将按此地址访问 |
| 7 | 6 | 5 | 237950547264 | 0 | cache_access | L3 | L1D cache | 1 | addr_fallback | 109 | 109 | ffffff807fbce090 | 81d75090 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=81d75090 的访问，request_id=109 | cache_return field=— | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 8 | 7 | 6 | 237950547264 | 0 | cache_return | L3 | L1D return | 1 | addr_fallback | 109 | 109 | — | 81d75090 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=81d75090 的访问，request_id=109 | cache_return field=miss | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 9 | 8 | 7 | 237950547264 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 109 | 109 | — | — | 81d75090 | 1 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | cache_line=81d75090，mshr_id=1 | state_after=mshr_allocated | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 10 | 9 | 8 | 237950547597 | 333 | cache_access | L3 | L1D cache | 1 | addr_fallback | 109 | 109 | ffffff807fbce090 | 81d75080 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=81d75080 的访问，request_id=109 | cache_return field=— | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 11 | 10 | 9 | 237950547597 | 0 | cache_return | L3 | L1D return | 1 | addr_fallback | 109 | 109 | — | 81d75080 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=81d75080 的访问，request_id=109 | cache_return field=miss | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 12 | 11 | 10 | 237950547597 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 109 | 109 | — | — | 81d75080 | 2 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | cache_line=81d75080，mshr_id=2 | state_after=mshr_allocated | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 13 | 12 | 11 | 237950592219 | 44622 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 109 | 109 | — | — | 81d75080 | 2 | — | — | — | — | — | — | filled | — | — | — | — | cache_line=81d75080，mshr_id=2 | state_after=filled | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 14 | 13 | 12 | 237950592219 | 0 | cache_fill | L3 | L1D fill | 1 | addr_fallback | 109 | 109 | — | 81d75080 | 81d75080 | — | — | — | — | — | — | — | — | — | — | — | — | cache_line=81d75080 | pa=81d75080 的行被填入 L1D | 错误物理行的数据进入 L1D，后续消费可能命中该行 |
| 15 | 14 | 13 | 237950592219 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 109 | 109 | — | — | 81d75080 | 2 | — | — | — | — | — | — | mshr_freed | — | — | — | — | cache_line=81d75080，mshr_id=2 | state_after=mshr_freed | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 16 | 15 | 14 | 237950592885 | 666 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 109 | 109 | — | — | 81d75080 | 0 | — | — | — | — | — | — | filled | — | — | — | — | cache_line=81d75080，mshr_id=0 | state_after=filled | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 17 | 16 | 15 | 237950592885 | 0 | cache_fill | L3 | L1D fill | 1 | addr_fallback | 109 | 109 | — | 81d75080 | 81d75080 | — | — | — | — | — | — | — | — | — | — | — | — | cache_line=81d75080 | pa=81d75080 的行被填入 L1D | 错误物理行的数据进入 L1D，后续消费可能命中该行 |
| 18 | 17 | 16 | 237950592885 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 109 | 109 | — | — | 81d75080 | 0 | — | — | — | — | — | — | mshr_freed | — | — | — | — | cache_line=81d75080，mshr_id=0 | state_after=mshr_freed | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 19 | 18 | 17 | 237950593218 | 333 | resp | L3 | response path | 1 | seq_primary | 109 | 109 | 81d75090 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | request_id=109 的内存/cache 响应 | 响应交付 LSU | 错误数据/地址回到处理器侧 |
| 20 | 19 | 18 | 237950593218 | 0 | lq_complete | L3 | LQ | 1 | seq_primary | 109 | 109 | ffffff807fbce090 | 81d75090 | — | — | — | — | — | — | — | — | — | — | — | — | — | request_id=109 的响应 | load 完成（lq_idx=1） | 错误值被标记为可交付，进入寄存器写回 |
| 21 | 20 | 19 | 237950593218 | 0 | taint_reg | L4 | register file (taint) | 1 | seq_primary | 109 | 109 | 81d75090 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | 完成的 load/store 数据 | 寄存器 clean→tainted（arch_reg=28，phys_reg=96） | 污染跨过存储→CPU 边界，进入架构寄存器状态 |
| 22 | 21 | 20 | 237950593884 | 666 | errant_commit | L5 | commit/ROB | 1 | taint_prop | — | 109 | — | — | — | — | — | — | — | — | — | — | — | 0 | L5 | errant_commit | — | 携带污染值的指令到达提交边界 | detection_layer=L5，outcome=errant_commit | 错误提交越过重定序边界，成为架构可见的 L5 终局 |


## 5. 相关旁支与未进入最终主链的事件

fault_id=1 有 64273 条非 consumer 事件与 1281 条 consumer 摘要；主链只取 event 21 的 22 个单祖先。旁支如下：

- `request_fork`：共 11477 条，主链 0 条；全部从主链节点 20（taint_reg）分叉，`bridge_layer=L3`、`bridge_reason=addr_fallback_broadcast`、`shared_addr=81d75000`、`shared_size=1000`。前几条把 old_request_id=109 分叉到 168/169/171/172/…，dest 分别为 23/26/29/32/…。这些是错误物理页在后续请求中的广播扇出，不是终局 21 的祖先，因此留在 Ch.5。
- 旁支 `taint_reg`：11477 条，主链仅 1 条（event 20）；其余都在 fork 请求上，说明污染扩散但没有改变 21 的祖先。
- 旁支 `lq_complete`：274 条，主链 1 条（event 19）；旁支 `resp` 11477 条，主链 1 条（event 18）。
- `squash_masked`：0 条。本 seed 没有任何 L4 含住记录，因此不存在“把 L5 误写成含住”的风险；错误 load 直接提交。
- `chain_end`：event 52795（tick=337969869489），是仿真结束/流收口，不是 L5。
- consumer 1281 条全部不在主链；它们只作摘要，不进入终局。
- 这些旁支说明错误页在大量后续请求上被访问；由于没有 squash/replay 覆盖 event 21，终局仍是 full/L5。若把 11477 条旁支的 taint 当作“多次独立故障”会误读：它们同属 fault_id=1 的同一注入，只是请求级扇出。


## 6. 最终判定与证据完整性

- terminal：`full`（权威 `chain_report.terminal`）。
- provable_to：`L5`；传播终局事件：`errant_commit` event 21，tick=237950593884。
- run outcome：`Timeout`（oracle=Timeout，exit=0）；没有 kernel oops/panic 行；这是受控 Timeout，不是正常 EOF 的“正常完成”。
- admitted：`True`；violations：`[]`；certified：`True`；chain_valid：`True`。
- truncated：`False`；gzip EOF：正常；stats：有效（`End Simulation Statistics`）。
- conservation：`ok`（emitted=1281，suppressed=195264260，logical_total=195265541，issues=[]）。
- count_contradiction：65554（原始）−64273（report）=1281，正好是 consumer 摘要数；无丢事件。
- campaign/checker agreement：oracle=Timeout 与 `run.out` 无 KERNEL 行、manifest `timeout_triggered=True` 一致；checker 的 full/L5 与权威报告一致。
- CHAIN_DEMONSTRATED：**是**（真实 L5 见证；Timeout 不抹去 L5）。
- COMPLETE_3_OF_3：**是**（本 RunID 3 个 seed 均有权威终局；本 seed 是 full/Timeout）。
- 12 项校验：1✓ 2✓ 3✓ 4✓ 5✓ 6✓ 7✓ 8✓ 9✓ 10✓ 11（含住 N/A）✓ 12✓ 13✓ 14✓ 15✓。
- 结论：**PASS**。注意：传播终局 ≠ 运行结局；本 seed 的 L5 与 Timeout 必须并列陈述，不能把 Timeout 写成“未传播完成”。

## 7. 原始证据与文件哈希

以下 SHA-256 均为本次对权威目录内文件重算的结果；未修改任何原始文件。

| 证据 | 路径 | 校验 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/T04-F0-W4/seed2/prop_evt.txt.gz` | SHA-256 `f7580db92194d2e21531630ab9676590cbe65ac05678031eea00647d792641ae`；2143342 bytes；mtime `2026-10-25T18:03:12+0800` |
| prop_trace（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/T04-F0-W4/seed2/prop_trace.csv.gz` | SHA-256 `a7960b788bedae6a14fbe907c6795cc558e312808f37e541d23af6d4c5f835e4`；543101 bytes；mtime `2026-10-25T18:03:12+0800` |
| chain_report（权威） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/T04-F0-W4/seed2/chain_report.json` | SHA-256 `46e9fbe79d22c263e1986c06702e049e4dc2faa2160499e131ea3df73b49a1c8`；1133793 bytes；mtime `2026-10-25T18:03:21+0800` |
| 权威离线 regrade | N/A | 本目录无 `chain_report.regrade-*.json`；未做离线重判 |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/T04-F0-W4/seed2/run.out` | SHA-256 `5dfae375e7cfbd5fa13ecaab1b3103f3b70c6d09f442e348ecf61c8c0891053f`；2064 bytes；mtime `2026-10-25T18:03:16+0800` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/T04-F0-W4/seed2/run.err` | SHA-256 `d8eadc88d063f55bdc2cf17b0eac6cd23f83205039ff3c8f3b96088c9ef6d900`；129 bytes；mtime `2026-10-25T18:03:16+0800` |
| stats.txt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/T04-F0-W4/seed2/stats.txt` | SHA-256 `e4aae66c420569f7162b06d227b7b9f586839315e36bd9f24a1ba843de875f4a`；362831 bytes；mtime `2026-10-25T18:03:13+0800` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/manifest.json` | SHA-256 `8c51599c7fc95522b54c4a5d7d7aa593feee9897a86d4ef89dd85eac2a877e1d`；1774 bytes；mtime `2026-10-25T19:33:33+0800` |
| 启动命令记录 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/T04-F0-W4/seed2/run.out` 的 `command line:` 行 | 已在上表 run.out 哈希内；manifest.cmd=`LSU_GEM5_BIN=<bin> LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3 --cells T04-F0-W4 --phase trial --max-seeds-per-cell 3 --max-parallel 1 --allow-blocked-models --fs-timeout 5400 --fs-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015` |
| binary | `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt` | SHA-256 `e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959`；1145673848 bytes；mtime `2026-10-25T09:22:24+0800`；manifest 记录 `e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959` |
| source head | manifest 字段 | `f680bbc274d0ab2dde8fd1b494dc795b9f544f2d`；binary_source_head=`N/A`；analysis_tool_head=`f680bbc274d0ab2dde8fd1b494dc795b9f544f2d` |
| 分析/校验工具 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/tools/lsu_chain_check.py` | SHA-256 `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`；65565 bytes；文档集 head=`4af986f726a6791f441130dee19eca0711e0b38f` |
| 注入日志（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/T04-F0-W4/seed2/armtlb_injections.log` | SHA-256 `094b855b00e7bf402718858dcf65ead730bc2d4dc5312c05af378b06acb9ff3e`；151 bytes；mtime `2026-10-25T16:33:23+0800` |
| board.workload.dmesg（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/T04-F0-W4/seed2/board.workload.dmesg` | **ABSENT** |
| board.terminal（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/T04-F0-W4/seed2/board.terminal` | SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`；0 bytes；mtime `2026-10-25T16:33:13+0800` |
| config.ini（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/T04-F0-W4/seed2/config.ini` | SHA-256 `8d005c6e18e38556940939229a6b1246e6a26ed2e1fe9ae483568c19cd0725ff`；97185 bytes；mtime `2026-10-25T16:33:12+0800` |
| config.json（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/T04-F0-W4/seed2/config.json` | SHA-256 `f826c1ff085b401859d0a5ee66a5d4cd708a9190a5d8a6dfa0b3f7b5d8944704`；277166 bytes；mtime `2026-10-25T16:33:13+0800` |

**权威证据目录**：`/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/T04-F0-W4/seed2`。

**其它副本及分类**（依据 `../R6-AUTHORITATIVE-EVIDENCE.md`）：

- `runs/lsu/r6_c9_T04-F0-W4_s2/T04-F0-W4/seed2` — **TRUNCATED**（prop_evt gzip 流在 EOF 前中断；不作为权威）
- `runs/lsu/r6_p1_T04-F0-W4/T04-F0-W4/seed2` — **INTERRUPTED**

未运行 gem5/campaign/scons；未修改 `prop_evt.txt.gz`、`chain_report*.json`、`stats.txt`、`run.out`、`run.err`、`manifest.json`、Excel/工作簿；未执行 `git commit`。
