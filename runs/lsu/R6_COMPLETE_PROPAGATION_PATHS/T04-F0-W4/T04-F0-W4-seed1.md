# T04-F0-W4 seed1 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T04-F0-W4`；seed：`1`；sample_run_id：`s1`
- 单元：`L1d-TLB`（L1 d-TLB，注入器 `CHAOSArmTLB`；注入点 site=`arm_tlb_lookup_hit`）
- fault model：`pfn_to_mapped_page`（故障类型：换值）。将命中项的 PPN 换成另一个当前合法、相同页大小的 PPN；VPN/ASID 保持一致；不生成任意随机位串。
- frequency tier：`F0` — 每次运行只注入 1 次；在 warm-up 后的 eligible event 中均匀抽样
- requested tier / effective tier / tier enabled：`CHAOS_LSU_TIER_CAP: requested=F0 effective=F0 lookup_tier_enabled=0`
- workload 矩阵标签：TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）
- run.out 实际 workload/readfile：`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/tlb_probe.rcS`（矩阵标签与实际 readfile 的差异如实保留，不推断）
- 完整启动命令：`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/T04-F0-W4/seed1 /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type pfn_to_mapped_page --tlb_rng_seed 1 --chaos_propagation --prop_run_id T04-F0-W4 --prop_sample_run_id s1`
- source head：`f680bbc274d0ab2dde8fd1b494dc795b9f544f2d`
- binary source head：`N/A`（该 manifest 不记录 binary_source_head；同 run 的 source_head 见上）
- binary path：`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256：`e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959`（本次对同一路径重算一致）
- analysis tool head：本次文档集分析工具 head=`4af986f726a6791f441130dee19eca0711e0b38f`；run 时 manifest.analysis_tool_head=`f680bbc274d0ab2dde8fd1b494dc795b9f544f2d`
- checker SHA-256：`baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`（`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/tools/lsu_chain_check.py`，65565 bytes）
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/T04-F0-W4/seed1`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/manifest.json`（SHA-256 `8c51599c7fc95522b54c4a5d7d7aa593feee9897a86d4ef89dd85eac2a877e1d`；1774 bytes；mtime `2026-10-25T19:33:33+0800`；该 manifest 的 seed 字段为 `3`）
- 正常 EOF：**是**（gzip 解压到 EOF 无错：True；`chain_report.truncated=False`，`evidence_truncated=False`）
- exit_code：`0`（gem5/oracle 报告值；manifest.exit_code=`0`，runroot `.done`=存在，`.exit_code`=存在）
- truncated：**False**
- stats 是否有效：**是**（stats.txt 以 `End Simulation Statistics` 结束；381972 bytes）
- 原始事件数：gzip 内 `PROP-EVT` 行 **3043** 条；`chain_report.event_count`=**1762**（不含 consumer 事件），差值为 consumer 摘要数 1281
- fault_id 数量：**1**（F0 每次运行只注入 1 次；注入日志只有 1 条命中记录）
- 是否经过离线 regrade：**否**（目录内无 `chain_report.regrade-*.json`；唯一离线重判 seed 是 T02-F2-W4 seed2，不属于本文件）

## 2. 完整故障传播过程：从注入到最终结局

本章只使用 T04-F0-W4 seed1 自己的 `prop_evt.txt.gz`。重建方法是：先从终局 `errant_commit`（event 118）沿 `parent_event_id` 一路回溯到 event 0，得到 22 个单祖先事件；再按 parent 在前、child 在后的顺序展开。`chain_report.path_event_ids` 只给出层锚点 `[0,1,2,4,37,118]`，它省略了 3、5–36、38，因此本章不把该数组当作完整链，而是把它当作核对锚点。所有 22 个事件的 tick 单调不减；同一 tick 的父子关系如实保留（例如 0–3 同在 237950940537）。

### 2.1 故障注入前的正常状态

被注入的是一条 **store** 的动态指令 `dyn_inst_seq=301`，`request_id=301`，`corr=origin`，VA=`0xffffffc009483fa8`。在 event 1 的 `tlb_lookup` 之前，命中表项的 normal 状态完整记录在 `state_before` 中：`vpn=ffffffc009483`、`asid=206`、`valid=1`、`global=1`、`pfn=81d75`、`ap=0`、`mtype=2`、`page_size=1000`（即 4 KiB）、`pa=81d75fa8`。也就是说，VPN 合法、ASID 合法、表项有效且 global，正常 PFN 为 0x81d75，正常 PA 为 0x81d75fa8，页内偏移为 0xfa8；查找命中在 way=1、entry_index=0。此时既没有异常权限，也没有 page fault 迹象，故障注入器面对的是一个“完全正常、后续会再被命中”的表项。

### 2.2 故障具体如何注入

event 0 是注入点：`kind=inj`，`tick=237950940537`，`event_id=0`，`fault_id=1`，`request_id=301`，`field=pfn_to_mapped_page`，`before=81d75`，`after=ffbce`，`VA=0xffffffc009483fa8`，`corr=origin`。注入日志的同一行给出了 `Site: arm_tlb_lookup_hit` 与 `candidates: 3`：注入器不是随机写一个位串，而是在当前运行中挑选了另一个合法、对齐、同页大小、仍在生命周期的已映射数据页。数值上，PFN 从 0x81d75（531829）变成 0xffbce（1047502），两者都在 20 位 PFN 范围内；页内偏移 0xfa8 完全没有变化，所以 PA 从 0x81d75fa8 变成 0xffbcefa8，`effective_pa_changed` 为真。这里没有 mask：它是整页替换，不是位翻转；两者差值 0x7DE59 只是替换结果，不应被解释成被翻转的位。这个故障模型正是 T04-F0-W4 的 pfn_to_mapped_page：保持 VPN/ASID/页大小/权限合法，只把目标物理页换成另一个已映射页，因此普通 page fault、权限 fault 和 page-size fault 都不会触发。

### 2.3 TLB 查询与地址翻译

event 1（`tlb_lookup`，parent=0）在同一 tick 读取命中项：`state_before` 的 pfn 是 0x81d75，`state_after` 的 pfn 是 0xffbce；`before=81d75`、`after=ffbce`，`way=1`、`entry_index=0`、`walk_id=0`。event 2（`tlb_pfn`，parent=1）把被污染的 PFN 与页内偏移拼成 PA，记录 `state_before=81d75fa8`、`state_after=ffbcefa8`，`pa=ffbcefa8`。event 3（`tlb_translate_result`，parent=2）是翻译出口：`field=effective_pa_changed`，`before=81d75fa8`、`after=ffbcefa8`，`contained=0`、`outcome=NoFault`、`detection_layer` 为空。这里的 `contained=0/NoFault` 并不意味着“没有故障”，而是表示 TLB 没有在本层识别/含住它：PFN 仍是合法映射页，权限位 ap=0 未变，页大小未变，TLB 没有“正确页”的冗余副本可比较。TLB 交给 LSU 的是 request_id=301、VA=0xffffffc009483fa8、PA=0xffbcefa8 的 4 KiB 访问；错误地址从这一刻正式进入存储管线。

### 2.4 错误如何进入 LQ/SQ/LSQ

这是 store 路径，没有 `lq_read`。event 4（`sq_execute`，parent=3，tick=`237950940537`）把该 store 置为 `state_before=issued`，`sq_idx=32`，VA=`ffffffc009483fa8`；event 5（`sq_writeback`，parent=4，tick=`237950941869`）以 `pa=ffbcefa8` 构造 packet，`state_after=packet_built`。输入是 TLB 交来的错误 PA；内部变化是 SQ 条目从 issued 进入 packet_built；输出是以错误 PA 为目的地址的 store 请求；下一步（L1D/MSHR）当然会按这个 PA 访问。事件 4 的 `request_id` 为空、事件 5 也没有 request_id，是因为 store 在这个阶段以 sq_idx 标识；随后 cache/MSHR 事件重新带上 request_id=301，说明同一 store 请求进入了存储子系统。

### 2.5 错误如何经过 cache 和 MSHR

event 6（`cache_access`，parent=5，tick=`237950941869`）以 `pa=ffbcefa8` 访问 L1D；event 7（`cache_return`，parent=6）明确记录 `field=miss`；event 8（`mshr_alloc`，parent=7）分配 mshr_id=1，cache_line=`ffbcefa8`，`state_after=mshr_allocated`。随后 event 15（`cache_access`，parent=8，tick=`237950942202`）以 `pa=ffbcef80` 访问同一物理页的另一个 cache 行，event 16 再次 `field=miss`，event 17 分配 mshr_id=3。event 30（`mshr_fill`，parent=17，tick=`237951015129`）以 fill_id=1 填充 mshr 3，event 31（`cache_fill`）把 `pa=ffbcef80` 的行填入 L1D，event 32（`mshr_free`）释放 mshr 3；event 33（`mshr_fill`，parent=32）用 mshr_id=0、fill_id=2 做第二次填充，event 34（`cache_fill`）再次填入同一行，event 35（`mshr_free`）释放。这里出现的“两次 fill/两次 free”不是新故障，而是 MSHR 合并/重填路径的既有状态序列：cache_line 与 PA 仍属于同一个被替换的物理页，`corr=addr_fallback` 贯穿整段。原始流没有在 `cache_access` 上记录 hit/miss 字段，因此 hit/miss 只能由紧随其后的 `cache_return.field=miss` 判定；本 seed 的这些访问均为 miss。MSHR 的 alloc/fill/free 以及 cache_fill 都把错误行身份接受下来，所以链仍然是同一个故障，而不是在 cache 层被“洗掉”。


### 2.6 污染如何返回处理器状态

第 19 步 event 36 是 `resp`，`request_id=301`，它在 tick=`237950987823` 把 cache/MSHR 的响应交回处理器侧；紧接着 event 37 是主链上唯一的 `taint_reg`，`parent_event_id=36`，`dyn_inst_seq=301`，`VA=0xffbcefa8`，`before=clean`、`after=tainted`，`corr=seq_primary`。这一步之所以是“存储结构→CPU 状态”的边界，是因为在此之前错误只表现为某个物理地址上的数据/状态（cache 行、MSHR 项、响应包），而 `taint_reg` 第一次把“这个值已被污染”记到处理器可见的寄存器/状态域；后续的 `sq_complete` event 38 才把这个 store 标记为完成。需要说明的是，event 37 的 `arch_reg` 与 `phys_reg` 字段在原始流中是空的，因此本文件不编造具体寄存器号；只能确认污染状态从 clean 变为 tainted。

### 2.7 最终传播终局

T04-F0-W4 seed1 的终局是**真实 L5 错误提交**：event 118，`kind=errant_commit`，`parent_event_id=38`，tick=`237951302175`，`dyn_inst_seq=391`，`commit_seq=161`，`pc=ffffffc0087b1000`，`detection_layer=L5`，`contained=0`，`outcome=errant_commit`，`corr=taint_prop`。它不是生命周期记录：同一 seed 的 `chain_end` 是 event 1691（tick=`238882168377`，`outcome=errant_commit_seen`），只表示传播流收口，不能拿来冒充 L5。

为什么它没有被提前消除：本 seed 中唯一的 `squash_masked` 是 event 150（tick=`237951547263`，`VA=ffffffc009483e40`，L4，`contained=1`，`squash_replay`），它发生在 event 118 **之后**，而且是在另一个 VA/请求上；它没有覆盖 118 这条祖先链。沿 event 118 的祖先，L4 的 `taint_reg`（event 37）之后没有 squash 或 replay 记录，所以错误值一路到提交边界。为什么它是架构可见的：`errant_commit` 的语义就是携带污染值的指令越过重定序/提交边界；此后错误副作用不可由流水线回滚。

这里必须解释一处“看似不一致”的字段：注入事件的 `dyn_inst_seq=301`，而终局 `errant_commit` 的 `dyn_inst_seq=391`。两者并非同一动态指令的编号抄错，而是 trace 的建模约定：event 118 的 `parent_event_id=38` 指向被污染 store 的完成（dyn 301），`corr=taint_prop` 表示“由该污染源传播到后续消费者”；dyn 391 是该消费者的动态序号。消费者侧的请求级携带发生在 event 37 之后的 65 个 `request_fork` 分支上（见第 5 章），这些 fork 不在 118 的单祖先链上，因此主链仍按 parent=38 叙述，不重排、不并链。

### 2.8 从传播终局到系统表现

- 传播链终局：L5 `errant_commit`，event 118，tick=`237951302175`；`provable_to=L5`。
- 运行结局：**Crash**（`chain_report.oracle_outcome=Crash`，`exit_code=0`）。`run.out` 的证据行是 `CHAOS_DETECT: layer=None contained=0 tick=237951302175 ptag=1 reason=errant_commit` 和 `[arm_chaos_fs] KERNEL OOPS under fault — exiting (classify: Crash/DUE per fs_mode)`；`run.err` 的证据行是 `src/kern/linux/events.cc:64: warn: Kernel oops in guest`。
- 注入 tick=`237950940537`，终局 tick=`237951302175`，传播延迟 **361638 ticks**。
- 因果链：L5 错误提交（118）→ 内核执行到被污染状态/地址相关的异常路径 → guest kernel oops → `KERNEL OOPS under fault`；oracle 因此归为 Crash。注意同一 `run.out` 在 237951547263 还有一次 Hardware RAS 的 `squash_replay`（对应 event 150），但它晚于 L5，不能把这次 Crash 反推成“被含住”。另外，run 级 manifest（seed 字段为 3，覆盖整次 campaign）的 `timeout_triggered=True` 不能覆盖 seed1 自己的 `run.out` 事实：本 seed 的进程留下了 KERNEL OOPS 行并以 exit 0 结束，oracle 报告为 Crash。

### 2.9 主链单元输入/内部变化/输出/传播意义

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| DTLB（CHAOSArmTLB） | VA=ffffffc009483fa8，命中 way=1/entry=0，正常 PFN=81d75 | 命中项 PFN 被替换为 ffbce；`tlb_pfn`/`tlb_translate_result` 记录 PA 81d75fa8→ffbcefa8 | request_id=301，PA=ffbcefa8，4KiB 页 | 错误地址从翻译结构进入 LSU；TLB 自身没有“正确页”判据 |
| SQ（store queue） | PA=ffbcefa8，dyn 301 | `sq_execute` issued→`sq_writeback` packet_built→（响应后）`sq_complete` completed | 以错误 PA 构造的 store packet | 错误地址被队列接受，后续 cache/MSHR 只能按此地址处理 |
| L1D cache | PA=ffbcefa8 / cache line ffbcef80 | `cache_access` → `cache_return field=miss` → `cache_fill` | miss 与 fill 行 | 错误物理行被填入 L1D，错误数据/行身份被缓存结构接受 |
| MSHR | cache line ffbcefa8 / ffbcef80 | `mshr_alloc`（mshr_id=1/3）→`mshr_fill`（fill_id=1/2）→`mshr_free` | 填充后的响应 | 错误行在 MSHR 中完成分配/填充/释放，错误数据随响应返回 |
| response path / LQ | request_id=301 | `resp` 交付响应 | 可交付的污染值 | 错误从存储域回到处理器侧 |
| register file（taint） | 完成的 store 数据 | `taint_reg` clean→tainted（arch/phys 未记录） | 被标记的处理器状态 | 存储→CPU 状态边界；此后只能靠 squash/回滚 |
| commit/ROB | 携带污染值的消费者（dyn 391） | 到达提交边界，无 squash 覆盖 | `errant_commit`（L5） | 架构可见错误；传播终局 |


**一句话总括**：T04-F0-W4 seed1 从 DTLB 命中项把 PFN 0x81d75 换成 0xffbce、把 PA 0x81d75fa8 换成 0xffbcefa8 开始，错误地址经 store queue（event 4/5）进入 L1D/MSHR（event 6–35），响应（36）把污染写入寄存器状态（37），最终由 event 118 真实错误提交并在 guest 内核触发 oops；传播终局是 L5，运行结局是 Crash，二者分开成立。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

三方一致：注入日志有 1 条 `arm_tlb_lookup_hit` 注入；`run.out` 的 `CHAOS_LSU_TRIGGER` 记录 `attempted=150162 eligible=56 injected=1`；`stats.txt` 的 `board.chaos_armtlb.numFaultsInjected=1`；`chain_report` 的 fault 数也是 1。因此 injected/activated/attempted/eligible 的口径一致，没有“注入但未激活”。故障值确实被下游读取：event 1 的 `tlb_lookup` 读到了被替换的 PFN，event 3 把它变成 PA，event 4/5 的 SQ 与 event 6–35 的 cache/MSHR 都消费了错误地址。故本 seed 的激活是实证的，不是由概率推断。

### 3.2 故障传播类型

这是**地址型（address）** 传播：错误发生在 VA→PA 翻译的 PFN 字段，错误 PA 0xffbcefa8 被后续存储结构原样使用。它不是 data 型（错误不是某个已加载数据字的位翻转），不是 control-state 型（没有改 PC/分支/权限），不是 permission 型（ap=0 未变，`numStateFaults=0`），也不是 timing 型。虽然响应把数据带回并最终提交，但根因是“访问了错误的物理页”，因此分类为地址/错误物理页；如果一定要细分，它是“wrong physical page alias”而不是“wrong cache line within the same page”或“wrong request routing”。

### 3.3 首个不可逆传播点

最早使故障在当前结构中不可由 TLB 自身撤销的点是 **event 3（`tlb_translate_result`，tick=237950940537）**：从这一刻起，错误 PA 0xffbcefa8 已作为翻译结果交付 LSU，后续 SQ 不会再做一次地址正确性校验。event 37 的 `taint_reg` 把污染带入处理器状态，是第二个不可逆点；event 118 的提交则是第三个、也是架构层的不可逆点。之所以把 event 3 称为“最早”，是因为 event 1/2 仍只是表项/字段级记录，event 3 才是把错误地址正式交给下游的出口；但这不意味着 event 3 之后绝对不能恢复——squash/replay 仍可在提交前丢弃它，只是本 seed 的祖先链上没有发生。

### 3.4 检测与掩蔽机制

本 seed 没有被任何检测机制含住。TLB 的 valid/global/ap/mtype/page_size 检查全部通过（替换页合法、4 KiB 对齐、权限未变），L1D/MSHR 不具备地址正确性检查，响应路径也没有 ECC/地址校验的可观测记录。唯一的 `squash_masked` 是 event 150（L4，`contained=1`，`squash_replay`，VA=`ffffffc009483e40`，tick=237951547263），它在 event 118 之后、且不在终局祖先上；因此它不能把 L5 改写成“含住”。本 seed 的暴露点就是提交边界：在 event 118 之前没有任何事件把这条链标记为 contained 或 replay。观测到的检测盲区是：地址翻译路径没有“正确 PFN”的冗余/校验，只有权限/有效位检查，无法发现“另一个合法页”。

### 3.5 最终 SDC 风险判断

是真实 `errant_commit`，且是架构可见的错误提交；运行结局是 Crash（guest kernel oops），没有应用级输出 oracle。按本仓库的纪律，**不能因为出现 errant_commit 就直接叫 SDC**：SDC 需要“外部可见、未被检测到的错误结果”证据；本 seed 的 oracle 是 Crash，且没有应用输出可比对，因此最终归类为 **Crash**，不是 SDC。是否存在 silent-error 的可能性？在提交之后、内核 oops 之前，错误值确实可能被消费；但本 seed 的实际运行以 oops 终止，无法证明它产生了未被检测的外部数据错误。因此本文件只声明“真实 L5 + Crash”，不声明 SDC。

由于没有应用级输出 oracle，最终数据正确性无法判断。

### 3.6 与同 RunID 其他 seed 的关系

只比较事实，不搬运其它 seed 的字段：seed1 的注入是 tick=237950940537、VA=ffffffc009483fa8、PFN 0x81d75→0xffbce、无 mask、终局 event 118、oracle Crash；seed2/seed3 的注入是 tick=237950546931、VA=ffffff807fbce090、PFN 0xffbce→0x81d75、候选 1、终局 event 21、oracle Timeout，且 seed2/seed3 共享同一确定性注入点但 prop_evt SHA 不同（是独立运行）。因此三者的地址变化方向、终局事件编号和运行结局都不同；seed1 是 Crash，seed2/3 是 Timeout。本文件不把 seed2/3 的 x28/phys 96 或 chain_end tick 写进 seed1 的链。

## 4. 完整主链事件表

> 主链按终局见证的 `parent_event_id` 单祖先逐事件重建（parent 在前、child 在后）；同 tick 内按事件继承关系排列。`path_event_ids` 只作层锚点核对，不当作完整链。表中 `—` 表示该事件在原始流中无此字段，不是 0。

| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 237950940537 | — | inj | L0 | CHAOSArmTLB | 1 | origin | 301 | 301 | ffffffc009483fa8 | — | — | — | 81d75 | ffbce | 81d75 | ffbce | — | — | — | — | — | — | — | 注入器选定该命中表项（site=arm_tlb_lookup_hit） | 表项 PFN 81d75→ffbce | 故障进入 DTLB 表项，下一次命中将读到被改写的 PFN |
| 2 | 1 | 0 | 237950940537 | 0 | tlb_lookup | L1 | CHAOSArmTLB/DTLB | 1 | seq_primary | 301 | 301 | ffffffc009483fa8 | — | — | — | 81d75 | ffbce | 81d75 | ffbce | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75fa8 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=ffbce;ap=0;mtype=2;page_size=1000;pa=ffbcefa8 | — | — | — | — | VA=ffffffc009483fa8 的命中查找，request_id=301 | 命中表项返回 pfn=ffbce | 故障 PFN 被 TLB 查询读取，进入翻译路径 |
| 3 | 2 | 1 | 237950940537 | 0 | tlb_pfn | L2 | DTLB 表项 PFN | 1 | seq_primary | 301 | 301 | ffffffc009483fa8 | ffbcefa8 | — | — | 81d75 | ffbce | 81d75 | ffbce | — | 81d75fa8 | ffbcefa8 | — | — | — | — | TLB 命中项中的 PFN 字段 | PA=ffbcefa8（pfn=ffbce） | 故障 PFN 与页内偏移拼成错误 PA |
| 4 | 3 | 2 | 237950940537 | 0 | tlb_translate_result | L2 | DTLB 翻译出口 | 1 | seq_primary | 301 | 301 | ffffffc009483fa8 | ffbcefa8 | — | — | — | — | 81d75fa8 | ffbcefa8 | — | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75fa8 | vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=ffbce;ap=0;mtype=2;page_size=1000;pa=ffbcefa8 | 0 | — | NoFault | — | 已带故障 PFN 的翻译请求 | effective PA=ffbcefa8，effective_pa_changed=1 | TLB 把错误 PA 交付 LSU；错误地址正式进入存储管线 |
| 5 | 4 | 3 | 237950940537 | 0 | sq_execute | L3 | SQ | 1 | seq_primary | — | 301 | ffffffc009483fa8 | — | — | — | — | — | — | — | — | issued | — | — | — | — | — | dyn_inst_seq=301 的请求，VA=ffffffc009483fa8 | 请求进入 LSU 队列 | 错误 PA 被 LQ/SQ 接受，后续 cache/MSHR 将按此地址访问 |
| 6 | 5 | 4 | 237950941869 | 1332 | sq_writeback | L3 | SQ | 1 | seq_primary | — | 301 | — | ffbcefa8 | — | — | — | — | — | — | — | — | packet_built | — | — | — | — | dyn_inst_seq=301 的请求 | 请求进入 LSU 队列 | 错误 PA 被 LQ/SQ 接受，后续 cache/MSHR 将按此地址访问 |
| 7 | 6 | 5 | 237950941869 | 0 | cache_access | L3 | L1D cache | 1 | addr_fallback | 301 | 301 | ffffffc009483fa8 | ffbcefa8 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=ffbcefa8 的访问，request_id=301 | cache_return field=— | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 8 | 7 | 6 | 237950941869 | 0 | cache_return | L3 | L1D return | 1 | addr_fallback | 301 | 301 | — | ffbcefa8 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=ffbcefa8 的访问，request_id=301 | cache_return field=miss | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 9 | 8 | 7 | 237950941869 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 301 | 301 | — | — | ffbcefa8 | 1 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | cache_line=ffbcefa8，mshr_id=1 | state_after=mshr_allocated | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 10 | 15 | 8 | 237950942202 | 333 | cache_access | L3 | L1D cache | 1 | addr_fallback | 301 | 301 | ffffffc009483fa8 | ffbcef80 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=ffbcef80 的访问，request_id=301 | cache_return field=— | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 11 | 16 | 15 | 237950942202 | 0 | cache_return | L3 | L1D return | 1 | addr_fallback | 301 | 301 | — | ffbcef80 | — | — | — | — | — | — | — | — | — | — | — | — | — | PA=ffbcef80 的访问，request_id=301 | cache_return field=miss | L1D 按错误 PA 查找；miss 时进入 MSHR，错误地址被缓存结构接受 |
| 12 | 17 | 16 | 237950942202 | 0 | mshr_alloc | L3 | MSHR | 1 | addr_fallback | 301 | 301 | — | — | ffbcef80 | 3 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | cache_line=ffbcef80，mshr_id=3 | state_after=mshr_allocated | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 13 | 30 | 17 | 237950986824 | 44622 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 301 | 301 | — | — | ffbcef80 | 3 | — | — | — | — | — | — | filled | — | — | — | — | cache_line=ffbcef80，mshr_id=3 | state_after=filled | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 14 | 31 | 30 | 237950986824 | 0 | cache_fill | L3 | L1D fill | 1 | addr_fallback | 301 | 301 | — | ffbcef80 | ffbcef80 | — | — | — | — | — | — | — | — | — | — | — | — | cache_line=ffbcef80 | pa=ffbcef80 的行被填入 L1D | 错误物理行的数据进入 L1D，后续消费可能命中该行 |
| 15 | 32 | 31 | 237950986824 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 301 | 301 | — | — | ffbcef80 | 3 | — | — | — | — | — | — | mshr_freed | — | — | — | — | cache_line=ffbcef80，mshr_id=3 | state_after=mshr_freed | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 16 | 33 | 32 | 237950987490 | 666 | mshr_fill | L3 | MSHR | 1 | addr_fallback | 301 | 301 | — | — | ffbcef80 | 0 | — | — | — | — | — | — | filled | — | — | — | — | cache_line=ffbcef80，mshr_id=0 | state_after=filled | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 17 | 34 | 33 | 237950987490 | 0 | cache_fill | L3 | L1D fill | 1 | addr_fallback | 301 | 301 | — | ffbcef80 | ffbcef80 | — | — | — | — | — | — | — | — | — | — | — | — | cache_line=ffbcef80 | pa=ffbcef80 的行被填入 L1D | 错误物理行的数据进入 L1D，后续消费可能命中该行 |
| 18 | 35 | 34 | 237950987490 | 0 | mshr_free | L3 | MSHR | 1 | addr_fallback | 301 | 301 | — | — | ffbcef80 | 0 | — | — | — | — | — | — | mshr_freed | — | — | — | — | cache_line=ffbcef80，mshr_id=0 | state_after=mshr_freed | 错误 cache line 在 MSHR 中分配/合并/填充/释放，错误数据随响应返回 |
| 19 | 36 | 35 | 237950987823 | 333 | resp | L3 | response path | 1 | seq_primary | 301 | 301 | ffbcefa8 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | request_id=301 的内存/cache 响应 | 响应交付 LSU | 错误数据/地址回到处理器侧 |
| 20 | 37 | 36 | 237950987823 | 0 | taint_reg | L4 | register file (taint) | 1 | seq_primary | 301 | 301 | ffbcefa8 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | 完成的 load/store 数据 | 寄存器 clean→tainted（arch_reg/phys_reg 未记录） | 污染跨过存储→CPU 边界，进入架构寄存器状态 |
| 21 | 38 | 37 | 237950987823 | 0 | sq_complete | L3 | SQ | 1 | seq_primary | — | 301 | ffffffc009483fa8 | — | — | — | — | — | — | — | — | — | completed | — | — | — | — | sq_idx=32 的 store 完成 | store 完成状态 | 错误 store 效果被标记为完成，等待提交 |
| 22 | 118 | 38 | 237951302175 | 314352 | errant_commit | L5 | commit/ROB | 1 | taint_prop | — | 391 | — | — | — | — | — | — | — | — | — | — | — | 0 | L5 | errant_commit | — | 携带污染值的指令到达提交边界 | detection_layer=L5，outcome=errant_commit | 错误提交越过重定序边界，成为架构可见的 L5 终局 |


## 5. 相关旁支与未进入最终主链的事件

本 seed 的代表故障 fault_id=1 共有 1762 条非 consumer 事件（另有 1281 条 consumer 摘要）。主链只取 event 118 的 22 个单祖先；其余事件都是旁支，**没有并入主链**：

- `request_fork`：共 70 条，主链上 0 条。它们从主链节点 8（2 条）、17（3 条）、37（65 条）分叉，`bridge_layer=L3`、`bridge_reason=addr_fallback_broadcast`，`shared_addr=ffbce000`、`shared_size=1000`。例如 event 4294967296 把 old_request_id=301 分叉到 new_request_id=303，dest_event_id=9；event 4294967301 从 event 37 分叉到 357，dest 55。它们是地址回退广播的请求级扇出，不是终局 118 的祖先，因此不进入 Ch.2 主链；它们是否重新汇合、何时汇合，原始流没有给出单一祖先之外的汇合记录，本文件不猜测。
- 旁支的 `taint_reg`：总共 71 条，主链只有 event 37；其余 70 条分布在 fork 出来的请求 303/304/…/460 等上，说明污染沿共享页扩散，但它们不在 118 的祖先链上。
- 旁支的 `lq_complete`：52 条，主链 0 条（本 seed 是 store 路径，主链用 `sq_complete`）。这些完成事件属于其它 load 请求。
- 旁支的 `resp`：70 条，主链 1 条（event 36）。
- `squash_masked`：只有 1 条，event 150（tick=237951547263，VA=ffffffc009483e40，PA=ffbcee40，L4，`contained=1`，`squash_replay`）。它发生在 event 118 之后，属于另一个 VA/请求；它证明 RAS 能对某些后续 load 做 squash，但它不是终局 118 的祖先，不能把 L5 说成含住。
- `chain_end`：event 1691（tick=238882168377），是传播流在仿真结束时的收口，不是 L5；它与 event 118 的 L5 明确分开。
- `consumer`：1281 条摘要，全部不在主链；它们是后续指令消费污染状态的汇总，不改变 118 的终局。
- 这些旁支对 SDC 诊断的影响：它们说明错误页在后续请求中继续被访问、并有一次晚到的 L4 squash；但没有一条覆盖 118 的提交，因此终局仍是真实 L5，而不是 detected_contained。


## 6. 最终判定与证据完整性

- terminal：`full`（权威 `chain_report.terminal`）。
- provable_to：`L5`；传播终局事件：`errant_commit` event 118，tick=237951302175。
- run outcome：`Crash`（oracle=Crash，exit=0）；崩溃类型：guest kernel oops（`KERNEL OOPS under fault`）。
- admitted：`True`；admission violations：`[]`；certified：`True`；chain_valid：`True`。
- truncated：`False`；gzip EOF：正常（解压到 EOF 无错）；stats：有效（`End Simulation Statistics`）；证据完整性未见截断。
- conservation：`ok`（consumer_summary_accounting: emitted=1281，suppressed=566330，logical_total=567611，issues=[]）。
- count_contradiction：表面差 3043（原始）−1762（report）=1281，正好是 consumer 摘要数；不是丢事件，已对账。
- campaign/checker agreement：campaign 的 oracle=Crash 与 `run.out` 的 KERNEL OOPS 一致；checker 的 terminal=full/L5 与权威 `chain_report` 一致。manifest 的 `timeout_triggered=True` 属于 run 级（seed=3）campaign 元数据，不改变 seed1 的 Crash 事实，已在 Ch.2.8 说明。
- CHAIN_DEMONSTRATED：**是**（真实 L5 见证 + 单祖先链 + admitted/certified）。
- COMPLETE_3_OF_3：**是**（本 RunID 的 3 个 seed 均有 full/detected_contained 的权威终局；见 Ch.3.6 与 R6-AUTHORITATIVE-EVIDENCE）。
- 12 项校验：1 事件存在✓；2 parent 存在✓；3 parent 先于 child✓；4 叙述顺序=祖先顺序✓；5 tick 单调✓；6 无跨 seed 混用✓；7 VA/PFN/PA/before/after/mask 与原始事件一致✓；8 request_id/corr/fault_id 一致✓；9 terminal/outcome 与权威报告一致✓；10 full⇒真实 L5✓；11 含住⇒真实 contained（本 seed N/A）✓；12 每个单元有输入/变化/输出/意义✓；13 Ch.2 非模板化（含本 seed 特有事件与字段解释）✓；14 无 child-before-parent✓；15 SDC 结论未超出证据✓。
- 结论：**PASS**。

## 7. 原始证据与文件哈希

以下 SHA-256 均为本次对权威目录内文件重算的结果；未修改任何原始文件。

| 证据 | 路径 | 校验 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/T04-F0-W4/seed1/prop_evt.txt.gz` | SHA-256 `7b807c1aecf149c0487a454a609a1fe366bbd27d8121c047759214886179d9fb`；113506 bytes；mtime `2026-10-25T16:33:11+0800` |
| prop_trace（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/T04-F0-W4/seed1/prop_trace.csv.gz` | SHA-256 `a262f1b1020b7911f32eb9ec746698c7cff8eadfab50fb80c05af91c7878fe32`；36094 bytes；mtime `2026-10-25T16:33:11+0800` |
| chain_report（权威） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/T04-F0-W4/seed1/chain_report.json` | SHA-256 `dd6491e6a70ccb25588b8255bd73ad6dcc94d0a7d3da0d49892b5e8a1b0daa49`；1094228 bytes；mtime `2026-10-25T16:33:12+0800` |
| 权威离线 regrade | N/A | 本目录无 `chain_report.regrade-*.json`；未做离线重判 |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/T04-F0-W4/seed1/run.out` | SHA-256 `03fd149dcfbe83083a7a7c48309ee2c5db1306107351153f32172b04831bdb89`；2237 bytes；mtime `2026-10-25T16:33:12+0800` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/T04-F0-W4/seed1/run.err` | SHA-256 `0bf115890ff85c49b6663e49525e43b1456d301c349787c7d511e415d424e46f`；1833 bytes；mtime `2026-10-25T16:33:12+0800` |
| stats.txt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/T04-F0-W4/seed1/stats.txt` | SHA-256 `e9b3825d497bff6beb8673942f3f696e61e7c34ed1e81f22e6f9c43e8487171c`；381972 bytes；mtime `2026-10-25T16:33:11+0800` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/manifest.json` | SHA-256 `8c51599c7fc95522b54c4a5d7d7aa593feee9897a86d4ef89dd85eac2a877e1d`；1774 bytes；mtime `2026-10-25T19:33:33+0800` |
| 启动命令记录 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/T04-F0-W4/seed1/run.out` 的 `command line:` 行 | 已在上表 run.out 哈希内；manifest.cmd=`LSU_GEM5_BIN=<bin> LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3 --cells T04-F0-W4 --phase trial --max-seeds-per-cell 3 --max-parallel 1 --allow-blocked-models --fs-timeout 5400 --fs-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015` |
| binary | `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt` | SHA-256 `e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959`；1145673848 bytes；mtime `2026-10-25T09:22:24+0800`；manifest 记录 `e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959` |
| source head | manifest 字段 | `f680bbc274d0ab2dde8fd1b494dc795b9f544f2d`；binary_source_head=`N/A`；analysis_tool_head=`f680bbc274d0ab2dde8fd1b494dc795b9f544f2d` |
| 分析/校验工具 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/tools/lsu_chain_check.py` | SHA-256 `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`；65565 bytes；文档集 head=`4af986f726a6791f441130dee19eca0711e0b38f` |
| 注入日志（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/T04-F0-W4/seed1/armtlb_injections.log` | SHA-256 `131e70a7d52031a18f2cb829d54b04fd43180ae5eb35b0e7fc4913f68431dc6f`；151 bytes；mtime `2026-10-25T16:33:02+0800` |
| board.workload.dmesg（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/T04-F0-W4/seed1/board.workload.dmesg` | SHA-256 `6fdabf80e1d1c25f0898f2221e1bd70f3fd08b97fce028ba2c4160327e3ee09b`；13938 bytes；mtime `2026-10-25T16:33:11+0800` |
| board.terminal（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/T04-F0-W4/seed1/board.terminal` | SHA-256 `b1776be2415f07fcab3f4ce0879a84c7fa247ca1739d8b1ab978444a4f68a3db`；1839 bytes；mtime `2026-10-25T16:33:11+0800` |
| config.ini（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/T04-F0-W4/seed1/config.ini` | SHA-256 `cfdf69ccca62d356c5f0a16ebfc58538abe538b1aa47c7ecc16e62300a12959e`；97185 bytes；mtime `2026-10-25T16:32:52+0800` |
| config.json（只读辅助） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/T04-F0-W4/seed1/config.json` | SHA-256 `6af8eebe6c2a3ee12d2e04dd2d7a481f4ce1fce8dde37ea75884e85436265e5b`；277166 bytes；mtime `2026-10-25T16:32:52+0800` |

**权威证据目录**：`/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3/T04-F0-W4/seed1`。

**其它副本及分类**（依据 `../R6-AUTHORITATIVE-EVIDENCE.md`）：

- `runs/lsu/r6_c9_T04-F0-W4_s1/T04-F0-W4/seed1` — **EXACT_DUPLICATE**
- `runs/lsu/r6_c9_T04-F0-W4_s2/T04-F0-W4/seed1` — **EXACT_DUPLICATE**
- `runs/lsu/r6_c7_T04-F0-W4_s1/T04-F0-W4/seed1` — **OLD_BINARY_REFERENCE**（manifest binary a9b2c236…）
- `runs/lsu/r6_c6_T04-F0-W4/T04-F0-W4/seed1`、`r6_p1_T04-F0-W4`、`r6_w1_T04-F0-W4`、`r6_w1b_T04-F0-W4`、`r6_tlb_pilot*`、`r6_tlb_verify` — **INTERRUPTED**（无 .done/.exit_code）

未运行 gem5/campaign/scons；未修改 `prop_evt.txt.gz`、`chain_report*.json`、`stats.txt`、`run.out`、`run.err`、`manifest.json`、Excel/工作簿；未执行 `git commit`。
