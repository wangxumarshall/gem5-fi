# T03-F5-W4 seed3 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T03-F5-W4`；seed：`3`；sample_run_id：`s3`
- 单元：L1d-TLB（DTLB）（故障模型 `T03`）
- fault model：选 PPN 某 bit stuck-at-0/1，对每次 TLB 读出施加同一掩码。实施细则：在 warm-up 后固定一个物理 bit、lane 或控制位置，并独立执行 stuck-at-0 与 stuck-at-1 两个 campaign；之后每次读出/写入都施加同一掩码直到运行结束。若某次事件的正确值本来就等于卡死值，该次不增加 activated。激活口径：仅当“首个DTLB hit后持续”且故障值被下游实际读取、选择或消费时计为 activated；否则归入 Injected-not-activated。
- fault type：`卡死`（本 seed 的实际注入记录见第 2、7 章；逐次 FaultType 取自 `armtlb_injections.log`）
- frequency tier：F5 — warm-up 后第一个 eligible event 起持续到运行结束；每次运行仅选一个 bit/字段
- requested tier：`F5`；effective tier：`F5`；tier enabled：`1`（来自 run.out `CHAOS_LSU_TIER_CAP: requested=F5 effective=F5 lookup_tier_enabled=1`）
- workload 矩阵标签：TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）
- run.out 实际 workload/readfile：`--readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS`
- 完整启动命令：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s3/T03-F5-W4/seed3 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type stuck_at_zero --tlb_lsu_tier F5 --tlb_rng_seed 3 --chaos_propagation --prop_run_id T03-F5-W4 --prop_sample_run_id s3`
- source head：`38122675b91e05aaa0d636d14a89b6c6a90ea53c`（逐 seed manifest 的 binary_source_head）
- binary source head：`38122675b91e05aaa0d636d14a89b6c6a90ea53c`（逐 seed manifest 的 binary_source_head）
- binary path：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256：`8a229009c933a6dc08c13903a78adf53e8967c933088fdbaa66e08d2d7a076e4`
- analysis tool head：`4af986f726a6791f441130dee19eca0711e0b38f`（上一版文档集提交 `7065459c`；本版审计工具头为 `4af986f726a6791f441130dee19eca0711e0b38f`）
- checker SHA-256：`baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`（`lsu_chain_check.py`）
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s3/T03-F5-W4/seed3`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s3/manifest.json`（SHA-256 `3a980e721f8b452f8161afa110a1ee4bf620f54f7c264fd2d862a8c007c07d6d`；逐 seed manifest（campaign 为 standalone-single-seed）；manifest.status=`FINISHED`，manifest.exit_code=`None`，manifest.seed=`3`）
- 正常 EOF：**是**（gzip 解压到 EOF 无错：True）
- exit_code：chain_report.exit_code=`0`；manifest.exit_code=`None`（见上）
- truncated：**False**（以 cap=3,000,000 读流，未触顶；`truncated=false`、`evidence_truncated=false`）
- stats 是否有效：**是**（`stats.txt` 可解析，`board.chaos_armtlb.numFaultsInjected` 与本 seed 的注入次数三方一致，见 3.1）
- 原始事件数：46460（与 `chain_report.event_count` 相同）
- fault_id 数量：9（权威报告登记的真实故障数；流内 `inj` 事件数与之相同）
- 是否经过离线 regrade：否


## 2. 完整故障传播过程：从注入到最终结局

本 seed 有 9 个真实故障，代表故障由 escape-first 规则选为 `fault_id=2`（只有它到达 `full`；fault 1/5/6/7 为 L4 含住，其余只到 L4 的未知终局）。终局见证是 `errant_commit`（event_id=224），其单祖先为 `203 → 204 → 205 → 206 → 207 → 208 → 209 → 210 → 211 → 212 → 213 → 214 → 215 → 216 → 217 → 218 → 219 → 220 → 221 → 222 → 223 → 224`，共 22 个事件。本 seed 走 **load** 路径并有两组真实填充，同时旁支上有大量预取与含住事件。

### 2.1 故障注入前的正常状态

注入目标为 DTLB 第 1 号 entry（`event_id=204` 的 `entry_index=1`、`way=-1`）。`state_before`=`vpn=ffffff807fbce;asid=206;valid=1;global=1;pfn=ffbce;ap=0;mtype=2;page_size=1000;pa=ffbce090`：VPN=`0xffffff807fbce`，ASID=206，`valid=1`、`global=1`，`ap=0`，4 KiB 页，正常 PFN=`0xffbce`。触发翻译的指令 `dyn_inst_seq=109`（`request_id=109`）使用 VA=`0xffffff807fbce090`；偏移 `0x90`，正常 PA=`0xffbce090`。

### 2.2 故障具体如何注入

组件 `CHAOSArmTLB`、站点 `arm_tlb_lookup_hit`，tick=237950546931（cycle=714566207），`event_id=203`，`fault_id=2`，`request_id=109`，`field=stuck_at_zero`，FaultType=`stuck_at_zero`，`corr=origin`。注入日志：
`Tick: 237950546931, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbce090, old_pfn: 0xffbce, new_pfn: 0xfebce, FaultType: stuck_at_zero, Mask: 0x1000`。
`before=0xffbce`、`after=0xfebce`，异或 `0x1000`：第 12 位被强制为 0（stuck-at-0）。该 run 的 9 条注入行全部使用 `Mask: 0x1000`。`new_pfn << 12 = 0xfebce000`，或上偏移 `0x90` 得 `0xfebce090`；第 12 位对应 PA 的第 24 位：`0xffbce090 → 0xfebce090`。`event_id=206` 的 `tlb_translate_result` 记录 `field=effective_pa_changed`、`before=ffbce090`、`after=febce090`、`contained=0`、`outcome=NoFault`。

### 2.3 TLB 查询与地址翻译

`event_id=204` 的 `tlb_lookup`（tick=237950546931）命中第 1 号 entry，`field=post_lookup`，`before=ffbce`、`after=febce`，`state_after` 的 `pfn=febce`、`pa=febce090`。`event_id=205` 的 `tlb_pfn` 记录 `state_before=ffbce090`、`state_after=febce090`、`pa=febce090`、`field=stuck_at_zero`。`event_id=206` 的 `tlb_translate_result` 给出 `contained=0`、`outcome=NoFault`、无 detection_layer、无 containment_reason。TLB 在 tick 237950546931 把错误有效 PA `0xfebce090` 交给 LSU。

### 2.4 错误如何进入 LQ/SQ/LSQ

本 seed 是 **load** 路径：`event_id=207` 的 `lsq_push`（tick=237950547264）记录 `pc=0xffffffc0080116d8`、`opcode=ldr`、`lq_idx=1`、`sq_idx=-1`、`field=load`；`event_id=208` 的 `lq_read`（同 tick，`lq_idx=1`、`request_id=109`、VA=`0xffffff807fbce090`）取出请求。`mem_req`/`lsq_sendfrag` 未发射（N/A），store 侧 N/A。

### 2.5 错误如何经过 cache 和 MSHR

两次 L1D 访问都未命中：`event_id=209`（`cache_access`，tick=237950547264，PA=`0xfebce090`）→ `event_id=210`（`cache_return`，`field=miss`）→ `event_id=211`（`mshr_alloc`，`mshr_id=11`，`cache_line=0xfebce090`，`state_after=mshr_allocated`）；`event_id=212`（tick=237950547597，PA=`0xfebce080`）→ `event_id=213`（`miss`）→ `event_id=214`（`mshr_alloc`，`mshr_id=12`，`cache_line=0xfebce080`）。随后两组真实填充：`event_id=215`（`mshr_fill`，tick=237950606538，`mshr_id=12`、`fill_id=11`、`cache_line=0xfebce080`、`state_after=filled`）→ `event_id=216`（`cache_fill`，`pa=febce080`）→ `event_id=217`（`mshr_free`，`mshr_id=12`）；`event_id=218`（`mshr_fill`，tick=237950607204，`mshr_id=0`、`fill_id=12`）→ `event_id=219`（`cache_fill`，`pa=febce080`）→ `event_id=220`（`mshr_free`，`mshr_id=0`）。错误行 `0xfebce080` 被真实写入 L1D。

本链出现的 kind 集合为 `cache_access、cache_fill、cache_return、errant_commit、inj、lq_complete、lq_read、lsq_push、mshr_alloc、mshr_fill、mshr_free、resp、taint_reg、tlb_lookup、tlb_pfn、tlb_translate_result`；本 seed 主链**未出现**的 kind（mshr_merge、mem_req、lsq_sendfrag、sq_execute、sq_writeback、sq_complete）一律 N/A——该发射器在本次运行中未发射它们，绝不以旁支补齐。事件流没有 `size` 字段，因此本节的 size=N/A（只有 `request_fork` 旁支携带 `shared_size`）。

### 2.6 污染如何返回处理器状态

`event_id=221` 的 `resp`（tick=237950607537，`request_id=109`，原始 `va` 记录 PA=`febce090`）回送数据；`event_id=222` 的 `lq_complete` 完成 `lq_idx=1`（`pa=febce090`）；`event_id=223` 的 `taint_reg` 把 `arch_reg=28` / `phys_reg=96` 从 `clean` 改为 `tainted`。输入是 cache 返回的错误数据，内部变化是污染登记，输出是污染寄存器 96。

### 2.7 最终传播终局

L5 终局是 `event_id=224` 的 `errant_commit`：parent=223，tick=237950608203，`dyn_inst_seq=109`，`commit_seq=88`，`pc=0xffffffc0080116d8`，`detection_layer=L5`，`contained=0`，`outcome=errant_commit`，`corr=taint_prop`。未被提前消除：L2 `contained=0`；L3 把错误行填入；L4 的 34 条 `squash_masked`（fault 2 的旁支）虽然存在，但都不在 event 224 的祖先上（event 224 的 parent 是 223，不是任何 squash）；提交点因此真实暴露。`chain_end`（event_id=39635，parent=37356，tick=444471282468，`outcome=errant_commit_seen`、`contained=1`、`corr=none`、`containment_layer=L4`、`containment_reason=squash_replay`）只是流收口，不是 L5。

### 2.8 从传播终局到系统表现

传播终局 `errant_commit`（event 224，tick 237950608203），`provable_to=L5`，`terminal=full`。运行结局是 **Timeout**：`run.out` 第一条 `CHAOS_DETECT` 为 `layer=None contained=0 tick=237950608203 ptag=2 reason=errant_commit`，随后有 100 条 `layer=Hardware RAS contained=1 … squash_replay/store_discarded_not_retired`；没有 panic 行，仿真未在预算内正常结束。因此同时成立：fault 2 的传播链已完成（真实 L5），但运行没有正常终止。注入 tick=237950546931，终局 tick=237950608203，延迟 61272 ticks（cycle 714566207→714566391，184 个 CPU cycle）。F5 统计：`attempted=154192995 eligible=154192995 injected=9 fires=154192995 no_effect=154192986`。

### 2.9 主链单元辅助表

| 单元 | 输入 | 内部变化 | 输出 | 传播意义 |
|---|---|---|---|---|
| CHAOSArmTLB（L0/L1） | 第 1 号 DTLB 表项（PFN=`ffbce`） | PFN→`febce`（bit12 stuck-at-0） | 命中读出错误 PFN | 故障值被真实查找读取 |
| CHAOSArmTLB/MMU（L2） | 错误 PFN + 偏移 `0x90` | PA `ffbce090`→`febce090`，`contained=0` | 有效 PA | 翻译层未含住 |
| LSQ（L3） | 翻译结果 | `lsq_push`（`ldr`，`lq_idx=1`）→`lq_read` | 错误 PA 的 load | 污点进入 LQ |
| L1D（L3） | PA `febce090`/`febce080` | 两次 `miss` | 转 MSHR | 错误地址进入 cache |
| MSHR（L3） | 两个错误行 | `mshr_id=11`、`mshr_id=12` 分配 | 等待填充 | 错误行被跟踪 |
| L1D/MSHR（L3） | 填充数据 | 两组 `mshr_fill`/`cache_fill`/`mshr_free` | 错误行留在 cache | 错误被持久化 |
| L1D→LSU（L4） | 填充完成 | `resp` 返回数据 | `lq_complete` | 污染数据回到处理器 |
| ROB/PRF 污染集（L4） | load 数据 | `arch_reg=28/phys_reg=96` clean→tainted | 污染寄存器 96 | 存储→CPU 边界 |
| ROB/Commit（L5） | 污染寄存器 96 | `contained=0` | `errant_commit` | 架构可见错误提交（终局） |

整条链可以概括为：tick=237950546931 的第 1 号 DTLB 命中把 PFN 第 12 位卡死为 0，有效 PA 由 `0xffbce090` 变为 `0xfebce090`；翻译层记录改变却 `contained=0`，`ldr`（`lq_idx=1`）经 `lsq_push`/`lq_read` 进入 L1D，两次相邻访问（`…090`/`…080`）均 miss 并分配 `mshr_id=11/12`，两组 `mshr_fill`→`cache_fill`→`mshr_free`（tick=237950606538/237950607204）把错误行写入缓存；`resp`、`lq_complete`、`taint_reg`（`arch_reg=28`/`phys_reg=96`）依次完成，最终在 tick=237950608203 由 `errant_commit`（`dyn_inst_seq=109`，`commit_seq=88`）收口，距注入 61272 ticks；链完整走到 L5，运行以 Timeout 收场。

## 3. SDC 诊断分析

### 3.1 故障是否被激活

F5 触发器：`attempted=154192995 eligible=154192995 injected=9 fires=154192995 no_effect=154192986`；`stats.txt`：`numFaultsInjected=9`；流内 `inj` 9 条；权威报告 9 个 fault：三方一致。fault 2 的卡死值被真实读取并消费（`lq_read`、两次 L1D 访问、两组填充、`taint_reg`、`errant_commit`），因此 activated。`no_effect` 的规模是 F5 正常统计，不是失败。

### 3.2 故障传播类型

**地址型**（错误物理地址）：PFN 第 12 位卡死为 0，VA/偏移/权限不变；有效 PA 从 `0xffbce090` 变 `0xfebce090`。不是数据位翻转或控制/时序错误；请求身份 `request_id=109` 在祖先上保持。

### 3.3 首个不可逆传播点

首个不可逆点是 `event_id=206` 的 `tlb_translate_result`（`contained=0`）：翻译层记录 PA 改变却放行。`event_id=207` 的 `lsq_push` 是执行落点；`event_id=216`/`219` 的 `cache_fill` 是对后续访问也生效的升级点。

### 3.4 检测与掩蔽机制

翻译层可检测 `effective_pa_changed`（本 fault `contained=0`）；L1D/MSHR 无地址校验，错误行已填入；L4 的 RAS 重放在 fault 2 的旁支上出现 34 次（`squash_masked`，`contained=1`、`reason=squash_replay`），但不在主链祖先上；提交点真实暴露。盲区是“翻译层可见却不阻断 + 主链未被重放覆盖”。本 seed 的旁支含住说明同一卡死位在不同 VA 上会被重放机制拦住，但本实例的提交路径没有。

### 3.5 最终 SDC 风险判断

存在真实 `errant_commit`（event 224），运行 Timeout；权威 `terminal=full`。不是 Masked/Contained；Timeout 不抹除 L5。没有应用级输出 oracle，无法判定静默错误；只能证明错误地址/错误行/错误提交真实发生。最终数据正确性无法判定，不称 SDC。

### 3.6 与同 RunID 其他 seed 的关系

seed1 的代表故障是 fault 2（stuck_at_zero，mask `0x10`，VA=`0xffffffc008a16868`，PA `80a16868→80a06868`，13 次注入）；seed2 的代表故障是 fault 1（stuck_at_one，mask `0x4`，VA=`0xffffff8001362700`，PA `81362700→81366700`，7 次注入）。本 seed 的代表故障是 fault 2（stuck_at_zero，mask `0x1000`，VA=`0xffffff807fbce090`，PA `ffbce090→febce090`，9 次注入）。三者卡死位/地址/注入数不同，本文件只用自己的事实。

## 4. 完整主链事件表

下表按 event 224 的祖先顺序排列（`203→204→…→224`）。`mask` 只在 `inj` 行给出（`0x1000`）；主链 22 个事件，无需折叠。

<!-- witness=224 representative_fault=2 ancestors=['203', '204', '205', '206', '207', '208', '209', '210', '211', '212', '213', '214', '215', '216', '217', '218', '219', '220', '221', '222', '223', '224'] -->
| 序号 | event_id | parent_event_id | tick | Δtick | kind | layer | component | fault_id | corr | request_id | dyn_inst_seq | VA | PA/address | cache_line | mshr_id | old_pfn | new_pfn | before | after | mask | state_before | state_after | contained | detection_layer | outcome | reason | 本事件输入 | 本事件输出 | 传播意义 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 203 | — | 237950546931 | — | inj | L0 | CHAOSArmTLB | 2 | origin | 109 | 109 | ffffff807fbce090 | — | — | — | ffbce | febce | ffbce | febce | 0x1000 | — | — | — | — | — | 注入 | DTLB 表项有效（entry_index=—）；dyn_inst_seq=109 的地址翻译即将使用它 | 被改写后的 PFN=febce（VA=ffffff807fbce090） | L0：故障源注入，后续所有错误都由该表项值派生 |
| 2 | 204 | 203 | 237950546931 | 0 | tlb_lookup | L1 | CHAOSArmTLB | 2 | seq_primary | 109 | 109 | ffffff807fbce090 | — | — | — | ffbce | febce | ffbce | febce | — | vpn=ffffff807fbce;asid=206;valid=1;global=1;pfn=ffbce;ap=0;mtype=2;page_size=1000;pa=ffbce090 | vpn=ffffff807fbce;asid=206;valid=1;global=1;pfn=febce;ap=0;mtype=2;page_size=1000;pa=febce090 | — | — | — | — | DTLB 命中 entry_index=1（way=-1），读取 pfn 字段 | 命中读出 pfn=febce，AP=0，page_size=1000，PA=febce090 | L1：故障值第一次被真实查找路径读取，错误从存储进入地址翻译 |
| 3 | 205 | 204 | 237950546931 | 0 | tlb_pfn | L2 | CHAOSArmTLB | 2 | seq_primary | 109 | 109 | ffffff807fbce090 | febce090 | — | — | ffbce | febce | ffbce | febce | — | ffbce090 | febce090 | — | — | — | — | lookup 得到的 PFN=ffbce | PFN 记录为 febce，翻译 PA=febce090 | L2：翻译结果开始使用错误 PFN |
| 4 | 206 | 205 | 237950546931 | 0 | tlb_translate_result | L2 | CHAOSArmTLB/MMU | 2 | seq_primary | 109 | 109 | ffffff807fbce090 | febce090 | — | — | — | — | ffbce090 | febce090 | — | vpn=ffffff807fbce;asid=206;valid=1;global=1;pfn=ffbce;ap=0;mtype=2;page_size=1000;pa=ffbce090 | vpn=ffffff807fbce;asid=206;valid=1;global=1;pfn=febce;ap=0;mtype=2;page_size=1000;pa=febce090 | 0 | — | NoFault | — | PFN=ffbce 与页内偏移组合 | 有效 PA ffbce090→febce090；contained=0，outcome=NoFault | L2：翻译结果携带错误有效 PA 交给 LSU |
| 5 | 207 | 206 | 237950547264 | 333 | lsq_push | L3 | LSQ | 2 | seq_primary | — | 109 | ffffff807fbce090 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | ldr 指令 dyn_inst_seq=109 进入 LSQ | lq_idx=1 / sq_idx=-1，field=load，VA=ffffff807fbce090 | L3：LSQ 结构登记该访存，后续 cache 访问由它发起 |
| 6 | 208 | 207 | 237950547264 | 0 | lq_read | L3 | LQ | 2 | seq_primary | 109 | 109 | ffffff807fbce090 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | LQ 条目 lq_idx=1 的 load 请求（VA=ffffff807fbce090） | request_id=109 的访存请求进入 L1D 路径 | L3：污点进入 LQ，请求地址由故障翻译决定 |
| 7 | 209 | 208 | 237950547264 | 0 | cache_access | L3 | L1D | 2 | addr_fallback | 109 | 109 | ffffff807fbce090 | febce090 | — | — | — | — | — | — | — | — | — | — | — | — | — | request_id=109 访问 L1D（PA=febce090） | 命中/未命中结果交给 cache_return 或 MSHR | L3：错误地址进入 cache 层级 |
| 8 | 210 | 209 | 237950547264 | 0 | cache_return | L3 | L1D | 2 | addr_fallback | 109 | 109 | — | febce090 | — | — | — | — | — | — | — | — | — | — | — | — | — | L1D 访问 PA=febce090 | field=miss（miss），转入 MSHR | L3：cache 未命中，错误地址被送到 MSHR 取数 |
| 9 | 211 | 210 | 237950547264 | 0 | mshr_alloc | L3 | MSHR | 2 | addr_fallback | 109 | 109 | — | — | febce090 | 11 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | miss 请求 PA/cache_line=febce090 | mshr_id=11 分配，state_after=mshr_allocated | L3：MSHR 为该错误行建立跟踪，等待填充 |
| 10 | 212 | 211 | 237950547597 | 333 | cache_access | L3 | L1D | 2 | addr_fallback | 109 | 109 | ffffff807fbce090 | febce080 | — | — | — | — | — | — | — | — | — | — | — | — | — | request_id=109 访问 L1D（PA=febce080） | 命中/未命中结果交给 cache_return 或 MSHR | L3：错误地址进入 cache 层级 |
| 11 | 213 | 212 | 237950547597 | 0 | cache_return | L3 | L1D | 2 | addr_fallback | 109 | 109 | — | febce080 | — | — | — | — | — | — | — | — | — | — | — | — | — | L1D 访问 PA=febce080 | field=miss（miss），转入 MSHR | L3：cache 未命中，错误地址被送到 MSHR 取数 |
| 12 | 214 | 213 | 237950547597 | 0 | mshr_alloc | L3 | MSHR | 2 | addr_fallback | 109 | 109 | — | — | febce080 | 12 | — | — | — | — | — | — | mshr_allocated | — | — | — | — | miss 请求 PA/cache_line=febce080 | mshr_id=12 分配，state_after=mshr_allocated | L3：MSHR 为该错误行建立跟踪，等待填充 |
| 13 | 215 | 214 | 237950606538 | 58941 | mshr_fill | L3 | MSHR | 2 | addr_fallback | 109 | 109 | — | — | febce080 | 12 | — | — | — | — | — | — | filled | — | — | — | — | mshr_id=12 的数据返回（fill_id=11） | state_after=filled，cache_line=febce080 | L3：MSHR 完成填充 |
| 14 | 216 | 215 | 237950606538 | 0 | cache_fill | L3 | L1D | 2 | addr_fallback | 109 | 109 | — | febce080 | febce080 | — | — | — | — | — | — | — | — | — | — | — | — | fill_id=11 的填充数据 | cache_line=febce080 进入 L1D | L3：错误行进入 cache |
| 15 | 217 | 216 | 237950606538 | 0 | mshr_free | L3 | MSHR | 2 | addr_fallback | 109 | 109 | — | — | febce080 | 12 | — | — | — | — | — | — | mshr_freed | — | — | — | — | mshr_id=12 填充完成 | state_after=mshr_freed | L3：MSHR 释放，等待响应回送 |
| 16 | 218 | 217 | 237950607204 | 666 | mshr_fill | L3 | MSHR | 2 | addr_fallback | 109 | 109 | — | — | febce080 | 0 | — | — | — | — | — | — | filled | — | — | — | — | mshr_id=0 的数据返回（fill_id=12） | state_after=filled，cache_line=febce080 | L3：MSHR 完成填充 |
| 17 | 219 | 218 | 237950607204 | 0 | cache_fill | L3 | L1D | 2 | addr_fallback | 109 | 109 | — | febce080 | febce080 | — | — | — | — | — | — | — | — | — | — | — | — | fill_id=12 的填充数据 | cache_line=febce080 进入 L1D | L3：错误行进入 cache |
| 18 | 220 | 219 | 237950607204 | 0 | mshr_free | L3 | MSHR | 2 | addr_fallback | 109 | 109 | — | — | febce080 | 0 | — | — | — | — | — | — | mshr_freed | — | — | — | — | mshr_id=0 填充完成 | state_after=mshr_freed | L3：MSHR 释放，等待响应回送 |
| 19 | 221 | 220 | 237950607537 | 333 | resp | L4 | L1D→LSU | 2 | seq_primary | 109 | 109 | febce090 | — | — | — | — | — | — | — | — | — | — | — | — | — | — | MSHR 取数完成（request_id=109） | 响应数据返回（该事件 va 字段记录 PA=febce090） | L4：污染数据返回处理器 |
| 20 | 222 | 221 | 237950607537 | 0 | lq_complete | L4 | LQ | 2 | seq_primary | 109 | 109 | ffffff807fbce090 | febce090 | — | — | — | — | — | — | — | — | — | — | — | — | — | 响应数据 request_id=109 | LQ 条目 lq_idx=1 完成，PA=febce090 | L4：load 写回 LQ，错误值即将写寄存器 |
| 21 | 223 | 222 | 237950607537 | 0 | taint_reg | L4 | ROB/PRF(污染集) | 2 | seq_primary | 109 | 109 | febce090 | — | — | — | — | — | clean | tainted | — | — | — | — | — | — | — | lq_complete/sq_complete 返回的数据（request_id=109） | arch_reg=28 / phys_reg=96：clean→tainted | L4：存储→CPU 边界，错误值进入寄存器污染集 |
| 22 | 224 | 223 | 237950608203 | 666 | errant_commit | L5 | ROB/Commit | 2 | taint_prop | — | 109 | — | — | — | — | — | — | — | — | — | — | — | 0 | L5 | errant_commit | errant_commit | 污染寄存器在提交点（dyn_inst_seq=109，commit_seq=88） | contained=0，outcome=errant_commit，PC=ffffffc0080116d8 | L5：错误提交成为架构可见结果，链终局 |


**单位说明**：`tlb_*` 的 `before/after` 含义见 2.2（PNF/PA）；两组填充的 `fill_id=11/12`、`mshr_id=12/0` 照原始字段；`taint_reg` 为 `arch_reg=28`/`phys_reg=96`。

## 5. 相关旁支与未进入最终主链的事件

以下各类旁支都只从其分叉点派生，**没有一条重新并回第 2 章的主链**（主链的 parent 链固定，见第 4 章）；它们不改变终局 ancestry，只在诊断上提供扩散/含住证据。

本 seed 共 46460 个事件、9 个故障。fault 2 有 18558 个事件，主链 22 个，其余 18536 个是旁支。

1. **请求分叉（`request_fork` 2954 条）**：全部挂在主链 `taint_reg`（event 223）上，最早 `event_id=4294967325`（tick=237950728749，new_request_id=111，`shared_addr=0xfebce000`），最晚 `event_id=4294973476`（tick=237970545246，new_request_id=38788）。派生出的访问在同一错误页内扩散。
2. **污染消费（`consumer` 1281 条、`taint_reg` 3180 条）**：最早 `event_id=225`（parent=223，tick=237950608536，`arch_reg=28`、`phys_reg=96`），最晚 `event_id=37356`（parent=1788，tick=237984416028，`arch_reg=1`、`phys_reg=1129`）。
3. **含住旁支（`squash_masked` 34 条）**：最早 `event_id=1867`（parent=1843，tick=237955045095，VA=`0xfffffffe011ce090`，PA=`0xfebce090`），最晚 `event_id=34599`（parent=34581，tick=237970213245，VA=`0xffffff807fbcec58`，PA=`0xfebcec58`）；全部 `contained=1`、`outcome=masked`、`reason=squash_replay`。整个 seed 的 `squash_masked` 共 97 条（fault 1 40、fault 2 34、fault 5 5、fault 6 9、fault 7 9），本链只引用 fault 2 的 34 条。
4. **填充旁支（各 126 条）**：最早 `event_id=241/242/243`（tick=237950791686，`request_id=151`，`mshr_id=14`、`fill_id=13`、`cache_line=0xfebced40`），最晚 `event_id=26714/26715/26716`（tick=237966843618，`request_id=27799`，`mshr_id=0`、`fill_id=650`、`cache_line=0xfebce100`）。
5. **预取与缓存旁支**：`pf_queue` 13、`pf_issue` 12、`pf_demand` 358、`pf_fill` 13、`cache_evict` 1；最早 `pf_queue` event 22588（tick=237964790340，`pf_request_id=4294967615`），最晚 `pf_demand` event 35254（tick=237970527264，`request_id=38674`，`field=demand_hit`）。
6. **生命周期收口（1 条）**：`event_id=39635`（parent=37356，tick=444471282468，`outcome=errant_commit_seen`、`contained=1`、`corr=none`、`containment_layer=L4`、`containment_reason=squash_replay`）。
7. **其它故障**：fault 1（`detected_contained`，路径 `0,1,2,5,74,1462`）、fault 5/6/7（`detected_contained`）、fault 3/4/8/9（`provable_to_L4_then_unknown`）各有自己的注入/地址，不并入本链。

旁支对 SDC 诊断的影响：它们显示错误页被大量访问（2954 fork、1281 consumer、358 pf_demand）且同一卡死位在其它 VA 上被 34 次重放拦住；但 event 224 的祖先不含任何 squash，因此本 fault 的终局仍是真实 L5。

## 6. 最终判定与证据完整性

| 检查项 | 结果 |
|---|---|
| terminal | `full` |
| provable_to | `L5` |
| 传播终局事件 | `errant_commit` event_id=224，tick=237950608203，`detection_layer=L5`，`contained=0`，`outcome=errant_commit` |
| 运行结局 | `Timeout`（`run.out` 无 panic；101 条 `CHAOS_DETECT`，最后为 `store_discarded_not_retired`） |
| admitted | `true`（`admission.path=full_chain`，`violations=[]`） |
| certified | `true` |
| violations | `[]` |
| truncated | `false`；`evidence_truncated=false` |
| gzip EOF | 正常（解压到 EOF 无错） |
| stats 有效性 | 有效（`numFaultsInjected=9`，与触发器 injected=9、inj 事件 9 条一致） |
| conservation | `ok`（consumer_summary：emitted=1318、suppressed=489163109、logical_total=489164427、conservation=ok、issues=[]） |
| count_contradiction | 无：`event_count=46460` 与实际解析事件数 46460 相同；injected/stats/inj 均为 9 |
| campaign/checker 一致性 | 一致（`chain_valid=true`、`admitted=true`、`certified=true`、`blocked=false`） |
| CHAIN_DEMONSTRATED | 是（L0→L5 单祖先连续路径，L5 为真实 `errant_commit`） |
| COMPLETE_3_OF_3 | 本 RunID 三 seed 均已完成；本 seed 状态 `COMPLETE_L5` |
| 判定 | **PASS** |

判定说明：代表故障按 escape-first 选为 fault 2（唯一 `full`）；fault 1/5/6/7 的含住与 fault 2 的旁支 34 次 squash 都不被用来改写 event 224 的终局；`chain_end` 39635 未被当作 L5。传播终局（真实 L5）与运行结局（Timeout）分别陈述。15 项一致性检查全部通过。

## 7. 原始证据与哈希

### 7.1 本 seed 权威证据

- 权威证据目录：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s3/T03-F5-W4/seed3`（`../R6-AUTHORITATIVE-EVIDENCE.md` 指定；未经修改）
- 权威判定报告：`chain_report.json`

| 文件 | SHA-256 | 字节数 | mtime |
|---|---|---|---|
| `prop_evt.txt.gz` | `c7a6c9db723699168efe49f93fcfb3c69226233d35d9b79ece06bd10d712c311` | 1627946 | 2026-10-27T10:04:05 |
| `chain_report.json` | `de50ba8aa457adee94afce981791f8c293be98e393ea37a55aa287dc075c42bf` | 1188619 | 2026-10-27T10:04:12 |
| `run.out` | `618bd851d83d8e3cf77b04c13bd5c047a5b9e7dd1b346312a2fb846cbb76a329` | 11671 | 2026-10-27T10:04:07 |
| `run.err` | `d8eadc88d063f55bdc2cf17b0eac6cd23f83205039ff3c8f3b96088c9ef6d900` | 129 | 2026-10-27T10:04:07 |
| `stats.txt` | `87de06d8bef633225660924e06bc260333bd9a71b38f2e45bbbcfeae17384172` | 374741 | 2026-10-27T10:04:06 |
| `armtlb_injections.log` | `bfdcb369cb84513b9cbc5b30e6cdba81ec4249adb73b656c79fb06ef8f722a6c` | 2002 | 2026-10-27T08:34:18 |
| manifest `manifest.json` | `3a980e721f8b452f8161afa110a1ee4bf620f54f7c264fd2d862a8c007c07d6d` | 1438 | 2026-10-27T10:04:13 |
| binary `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` | `8a229009c933a6dc08c13903a78adf53e8967c933088fdbaa66e08d2d7a076e4` | 由 manifest 记录（未在本机重算二进制尺寸） | — |
| binary source head | `38122675b91e05aaa0d636d14a89b6c6a90ea53c` | — | — |
| analysis tool head | `4af986f726a6791f441130dee19eca0711e0b38f` | — | — |
| checker `tools/lsu_chain_check.py` | `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44` | 69565 | 见工具目录 |

### 7.2 启动命令记录

- `run.out` 内 `command line:`：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s3/T03-F5-W4/seed3 /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/lsu_b0_fs.py --restore-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015 --kernel /home/sdc/gem5-fi-ding/gem5-fs/vmlinux --disk /home/sdc/gem5-fi-ding/gem5-fs/ubuntu.img --bootloader /home/sdc/gem5-fi-ding/gem5-fs/boot.arm64 --cpu O3 --readfile /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/configs/fs/tlb_probe.rcS --ckpt-first-clock --chaos_armtlb --tlb_first_clock 1000 --tlb_probability 1.0 --tlb_max_faults 1 --tlb_fault_type stuck_at_zero --tlb_lsu_tier F5 --tlb_rng_seed 3 --chaos_propagation --prop_run_id T03-F5-W4 --prop_sample_run_id s3`
- `manifest.json` 的 campaign `cmd`：`LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s3 --cells T03-F5-W4 --phase trial --seed-start 3 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300`

### 7.3 二进制与工具身份

- binary path：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256：`8a229009c933a6dc08c13903a78adf53e8967c933088fdbaa66e08d2d7a076e4`
- analysis tool head：`4af986f726a6791f441130dee19eca0711e0b38f`
- checker SHA-256：`baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`

### 7.4 其它副本及其分类

- `../R6-AUTHORITATIVE-EVIDENCE.md` 未登记本 (RunID, seed) 的其它副本。

以上 SHA-256、字节数与 mtime 均为本次只读重算/读取值；原始文件未被修改，未运行 gem5、campaign 或 scons。
