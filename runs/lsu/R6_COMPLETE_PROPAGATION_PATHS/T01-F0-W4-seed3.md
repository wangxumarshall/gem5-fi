# T01-F0-W4 seed3 故障传播全过程

> 证据口径：本文件只使用该 seed **自己**未经修改的 `prop_evt.txt.gz` 重建传播路径；代表故障按权威 checker 的 escape-first 规则选择；原始事件流未被修改，gem5 未重跑。
> `chain_report` 的 `path_event_ids` 只作为层锚点核对，**不是**完整链；本文件按 `parent_event_id` 单祖先逐事件重建。

## 30 秒结论

在 `T01-F0-W4` seed3 中，注入器于 tick=237950233578 在 DTLB 表项（site=arm_tlb_lookup_hit）把 PFN 从 `0x81d75` 改成 `0x20000000081d75`（VA=`0xffffffc009483eb0`），但翻译后的有效 PA 实际未改变（`0x81d75eb0`→`0x81d75eb0`，field=effective_pa_unchanged）；故障在 L2 `tlb_translate_result`（event_id=3, tick=237950233578）被显式检测并含住（contained=1, reason=effective_pa_unchanged）；L3/L4/L5 不适用；运行结局 Masked（无 panic/oops（见 CHAOS_DETECT / oracle））。

## 实验身份与证据来源

- RunID: `T01-F0-W4`
- seed: `3`；sample_run_id: `s3`
- 实验模型: 模型ID=`T01`，单元=`L1d-TLB`（RunID 另带频率档位后缀）
- 故障类型: `单比特翻转`
- 故障模型: 随机选有效表项的VPN tag翻转1 bit；只在注入后再次命中才计activated。实施细则：每次故障运行只选一个当前有效且可被后续使用的目标，在指定字段内均匀抽取一个 bit 做一次 XOR 翻转；其余字段保持无故障值。保存目标 entry/way、bit 编号、原值和故障值，避免把未使用空项计为有效样本。激活口径：仅当“DTLB中存在有效项”且故障值被下游实际读取、选择或消费时计为 activated；否则归入 Injected-not-activated。
- 频率档位: `F0` — 每次运行只注入 1 次；在 warm-up 后的 eligible event 中均匀抽样
- requested tier: `F0`；effective tier: `F0`；tier enabled: `关闭(0)`（来自 run.out `CHAOS_LSU_TIER_CAP`）
- 负载（矩阵标签）: TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）
- 负载（run.out 实际命令行）: `--readfile /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/configs/fs/tlb_probe.rcS`
- source head: N/A（该 run 的 manifest 无 binary_source_head 字段；manifest.source_head=bc82f29d8f69410461d18c07a1ee9314f18885a5 只是运行时工作树 HEAD，不等同于二进制构建源）
- binary path: `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt`
- binary SHA-256: `e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959`
- analysis tool head: `e45b0a0fc8bfb871e906a6ecef6b16f922ec3d8c`（本次分析）
- checker SHA-256: `baa1e8e3c71503d3f0e32b329f45a060173f2afe685be9c422159470c3b71b44`
- 原始 evidence root: `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed3`
- prop_evt: `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed3/prop_evt.txt.gz`
- prop_evt SHA-256: `1db3d9275cfb56a0ca13007c9a009ac987f514d9d49c9ed14e0430dcbcc1aa92`（本次重算值；字节数 887）
- chain_report（权威）: `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed3/chain_report.json`
- chain_report SHA-256: `2240b159cf91856dfabd62429831e898260382f236a30b21b74afc5f6c41114e`
- manifest: `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/manifest.json`（SHA-256 `730ca9788c6b0bc12cc4d218eea0758d4dedc9d719eadbe9fdc01aed9c1eca03`）
- run.out: `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed3/run.out`（SHA-256 `25506842d89af7d85f3df1213179a3bbb361373878411c958f1f95fea071decd`）
- run.err: `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed3/run.err`（SHA-256 `482bd31fcaaa688cce6887ea0f09d70b62637376b742d7161649bcefc386b41e`）
- stats.txt: `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed3/stats.txt`（SHA-256 `05fc4895e060abd97487d112dd6d740ac15279bed656f22bd06b94da9c54d198`；`board.chaos_armtlb.numFaultsInjected=1`）
- 正常 EOF: **是**（gzip 解压到 EOF 无错：True）
- truncated: **False**（本次以 cap=3,000,000 读流；未触发 200k EVENT_CAP）
- 原始事件总数: 5；代表故障 `fault_id=1` 事件数: 5；权威报告 fault 数: 1
- 是否经过离线重判: 否
- 其它同 (RunID, seed) 证据目录的分类见 `../R6-AUTHORITATIVE-EVIDENCE.md`。

## 一行传播图

`VA=0xffffffc009483eb0，PFN 0x81d75→0x20000000081d75，但有效 PA 实际未改变（0x81d75eb0→0x81d75eb0） → TLB 地址翻译 → tlb_translate_result(contained=1, L2, reason=effective_pa_unchanged) → 后续 L3/L4/L5 不适用 → Detected/Contained`

## 第一部分：详细、可读的完整传播过程

### 第 1 步：故障注入

发生了什么：注入器在命中表项上写入故障。目标字段 `bit_flip` 从 `81d75` 变成 `20000000081d75`（mask=0x20000000000000；PFN 0x81d75→0x20000000081d75），被改写的 TLB 表项随后会被真实查找读取。

- **event_id=`0`；parent_event_id=`—`；tick=`237950233578`；fault_id=`1`；corr=`origin`；request_id=`31`；dyn_inst_seq=`31`**
  - 硬件结构/事件：注入器在被命中的 DTLB 表项写入故障；before→after 即目标字段被改变后的取值。
  - 地址/身份：VA=`0xffffffc009483eb0`
  - 值变化：before=`81d75`→after=`20000000081d75`；field=`bit_flip`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L0**
  - 注入日志行：`Tick: 237950233578, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483eb0, old_pfn: 0x81d75, new_pfn: 0x20000000081d75, FaultType: bit_flip, Mask: 0x20000000000000`
  - 是否真实改变目标值：**是**（before≠after: True）
  - 是否真实激活：**是**（run.out 注入器汇总：`CHAOS_LSU_TRIGGER: injector=CHAOSArmTLB tier=F0 attempted=66310644 eligible=1 injected=1 first_eligible_tick=237950233578 last_eligible_tick=237950233578 (activated=W3-L0-layer)`）
  - 为什么把故障传给下一步：故障值已经写入目标 TLB 表项；下一次对该表项的查找会读到被改写的字段，因此故障由注入点（L0）传递给 TLB 查询/翻译（L1/L2）。

### 第 2 步：TLB 查询与地址翻译

发生了什么：TLB 查找/翻译路径读取了被污染的表项，并把故障 PFN 物化为物理地址。

- **event_id=`1`；parent_event_id=`0`；tick=`237950233578`；fault_id=`1`；corr=`—`；request_id=`31`；dyn_inst_seq=`31`**
  - 硬件结构/事件：TLB 查找命中并返回（已含故障的）表项；state_before/state_after 对比可见 pfn 与 pa 字段。
  - 地址/身份：VA=`0xffffffc009483eb0`；PFN=`81d75`→`20000000081d75`
  - 值变化：before=`81d75`→after=`20000000081d75`；field=`post_lookup`；state_before=`vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75eb0`；state_after=`vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=20000000081d75;ap=0;mtype=2;page_size=1000;pa=81d75eb0`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L1**
  - state 对比：pfn `81d75`→`20000000081d75`；pa `81d75eb0`→`81d75eb0`
- **event_id=`2`；parent_event_id=`1`；tick=`237950233578`；fault_id=`1`；corr=`—`；request_id=`31`；dyn_inst_seq=`31`**
  - 硬件结构/事件：从 TLB 表项取出的 PFN 已带故障，据此拼出物理地址 PA；故障从结构域进入地址翻译域。
  - 地址/身份：VA=`0xffffffc009483eb0`；PA=`0x81d75eb0`；PFN=`81d75`→`20000000081d75`
  - 值变化：before=`81d75`→after=`20000000081d75`；field=`bit_flip`；state_before=`81d75eb0`；state_after=`81d75eb0`
  - 检测/含住字段：detection_layer=`—`；contained=`—`；outcome=`—`；containment_layer=`—`；containment_reason=`—`
  - 层级：**L2**
- **event_id=`3`；parent_event_id=`2`；tick=`237950233578`；fault_id=`1`；corr=`origin`；request_id=`31`；dyn_inst_seq=`31`**
  - 硬件结构/事件：地址翻译结果落地：比对 requested/effective 物理地址，决定该故障是否真正改变有效 PA。
  - 地址/身份：VA=`0xffffffc009483eb0`；PA=`0x81d75eb0`
  - 值变化：before=`81d75eb0`→after=`81d75eb0`；field=`effective_pa_unchanged`；state_before=`vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75eb0`；state_after=`vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=20000000081d75;ap=0;mtype=2;page_size=1000;pa=81d75eb0`
  - 检测/含住字段：detection_layer=`L2`；contained=`1`；outcome=`NoFault`；containment_layer=`L2`；containment_reason=`effective_pa_unchanged`
  - 层级：**L2**
  - 翻译比对结论：`effective_pa_unchanged`（requested=`81d75eb0`，effective=`81d75eb0`）
  - 为什么把故障传给下一步：翻译结果比对显示有效 PA **没有改变**（`effective_pa_unchanged`），故障在此被显式识别并含住（L2），因此**没有**继续传给 L3。

### 第 3 步：进入 Load Queue 或 Store Queue

N/A：故障在 L2 已被含住（`effective_pa_unchanged`），没有进入 L3/L4/L5，故本步 N/A。

### 第 4 步：缓存和 MSHR 传播

N/A：故障在 L2 已被含住（`effective_pa_unchanged`），没有进入 L3/L4/L5，故本步 N/A。

### 第 5 步：错误数据或污染状态返回处理器

N/A：故障在 L2 已被含住（`effective_pa_unchanged`），没有进入 L3/L4/L5，故本步 N/A。

### 第 6 步：最终传播终局

情况 B：在 L2 含住（不是 L5）。

- **event_id=`3`；parent_event_id=`2`；tick=`237950233578`；fault_id=`1`；corr=`origin`；request_id=`31`；dyn_inst_seq=`31`**
  - 硬件结构/事件：地址翻译结果落地：比对 requested/effective 物理地址，决定该故障是否真正改变有效 PA。
  - 地址/身份：VA=`0xffffffc009483eb0`；PA=`0x81d75eb0`
  - 值变化：before=`81d75eb0`→after=`81d75eb0`；field=`effective_pa_unchanged`；state_before=`vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=81d75;ap=0;mtype=2;page_size=1000;pa=81d75eb0`；state_after=`vpn=ffffffc009483;asid=206;valid=1;global=1;pfn=20000000081d75;ap=0;mtype=2;page_size=1000;pa=81d75eb0`
  - 检测/含住字段：detection_layer=`L2`；contained=`1`；outcome=`NoFault`；containment_layer=`L2`；containment_reason=`effective_pa_unchanged`
  - 层级：**L2**
  - 说明：`tlb_translate_result` 的 `detection_layer=L2`、`contained=1`、`outcome=NoFault`、`containment_reason=effective_pa_unchanged`；有效 PA **没有改变**，故障没有下传。
  - **L3=N/A；L4=N/A；L5=N/A**（故障在 L2 终止；`chain_end` 只是生命周期收口，不占层）。

### 第 7 步：仿真运行的最终表现

**传播链终局**：L2 `tlb_translate_result` 含住（event_id=`3`, tick=`237950233578`, reason=`effective_pa_unchanged`）——有效 PA 未变，故障未下传。

**运行结局（与传播链终局分开陈述）**：oracle=`Masked`；实际表现：无 panic/oops（见 CHAOS_DETECT / oracle）。

run.out 的 CHAOS_DETECT 行（共 1 行，节选）：
- `CHAOS_DETECT: layer=Hardware RAS contained=1 tick=237950233578 ptag=1 reason=effective_pa_unchanged`

说明：代表故障被含住，运行级 oracle 判为 Masked；传播终局与运行结局一致。

## 第二部分：技术证据与逐事件记录

| 序号 | event_id | parent_event_id | tick | kind | layer | fault_id | corr | request_id | sample_run_id | VA | PA/address | old_pfn/new_pfn | old_value/new_value | mask | contained | detection_layer | outcome | reason | 与上一事件的关系 | 在人话版中的作用 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | — | 237950233578 | `inj` | L0 | 1 | origin | 31 | s3 | 0xffffffc009483eb0 | — | 0x81d75→0x20000000081d75 | 81d75→20000000081d75 | 0x20000000000000 | — | — | — | — | 起点 | L0 注入 |
| 2 | 1 | 0 | 237950233578 | `tlb_lookup` | L1 | 1 | — | 31 | s3 | 0xffffffc009483eb0 | — | 0x81d75→0x20000000081d75 | 81d75→20000000081d75 | — | — | — | — | — | 直接 parent（parent=0）；corr origin→— | L1 单元内观察 |
| 3 | 2 | 1 | 237950233578 | `tlb_pfn` | L2 | 1 | — | 31 | s3 | 0xffffffc009483eb0 | 0x81d75eb0 | 0x81d75→0x20000000081d75 | 81d75→20000000081d75 | — | — | — | — | — | 直接 parent（parent=1） | L2 地址物化 |
| 4 | 3 | 2 | 237950233578 | `tlb_translate_result` | L2 | 1 | origin | 31 | s3 | 0xffffffc009483eb0 | 0x81d75eb0 | — | 81d75eb0→81d75eb0 | — | 1 | L2 | NoFault | effective_pa_unchanged | 直接 parent（parent=2）；corr —→origin | L2 翻译结果/含住点 |

说明：本表逐条列出代表故障 `fault_id=1` 从 `inj` 到终局见证的**完整单祖先链**（4 条），不是 checker 的六锚点摘要；每一行的 `parent_event_id` 都等于上一行的 `event_id`（第 1 行除外）。`mask` 只对注入事件有意义；`reason` 列是 `containment_reason`。
## 相关旁支和未进入最终 ancestry 的事件

本 seed 原始事件总数 **5**；代表故障 `fault_id=1` 的事件数 **5**；进入最终 ancestry 的事件 **4**；未进入最终 ancestry 的同 fault 事件 **1**。

以下旁支事件**不参与**主链的单祖先证明，**绝不**合并进主链。判定理由：沿终局见证的 `parent_event_id` 逐级回溯不会经过这些事件——它们是同一 fault 的其它并发请求、其它 load 实例或其它检测点，只有主链上的事件才共享同一条可证祖先路径。

本 seed 除生命周期终止符 `chain_end` 外**没有任何同 fault 旁支事件**（不省略、不折叠）。


**生命周期终止符 `chain_end`（非传播层、非 L5）**：event_id=`4`；tick=`314515193310`；detection_layer=`L2`；contained=`1`；outcome=`detected_contained`；corr=`none`。它由传播监控退出回调发射，只是运行生命周期标记，不占据 L0–L5 任何层，永不作为 L5，也不构成含住证据。

## 最终验收结论

- CHAIN_DEMONSTRATED: **是**（代表故障链在单祖先上从 `inj` 可证到终局见证）
- terminal: `detected_contained`；provable_to: `L2`；propagation terminal: `L2`
- witness: `tlb_translate_result` event_id=`3` tick=`237950233578`（parent=`2`）
- admitted: `True`；certified: `True`；violations: `[]`
- truncated: `False`；gzip EOF 正常: `True`
- evidence SHA 一致: `重算值已固定记录；plain chain_report 未内嵌 prop_evt SHA（n/a for cross-check）`
- **PASS**

### 12 项校验清单

| 项 | 结果 | 证据 |
|---|---|---|
| 1_event_ids_exist | PASS | referenced ids=5; missing=none |
| 2_parent_on_same_ancestry | PASS | contiguous parent chain of 4 events |
| 3_tick_order | PASS | ticks 237950233578..237950233578 monotone=True |
| 4_values_from_own_seed | PASS | all displayed event fields re-read from own prop_evt |
| 5_no_cross_seed_identity_copy | PASS | all fault_id=1; prop_evt SHA unique among the 48 seeds |
| 6_terminal_matches_authoritative_report | PASS | checker=detected_contained/L2 report=detected_contained/L2 |
| 7_full_witness_real_L5_not_chain_end | PASS | n/a (not full) |
| 8_containment_witness_real_contained | PASS | witness kind=tlb_translate_result id=3 dl=L2 contained=1 outcome=NoFault |
| 9_narrative_and_table_agree | PASS | narrative ids ⊆ ancestry∪chain_end; table ids == ancestry (4); witness+inj present in both |
| 10_only_legitimate_shared_injection | PASS | no intra-RunID shared injection |
| 11_no_runid_path_reuse | PASS | seed_dir/prop/report all carry T01-F0-W4 and seed3 |
| 12_tier_matches_evidence | PASS | matrix=F0 run.out=CHAOS_LSU_TIER_CAP: requested=F0 effective=F0 lookup_tier_enabled=0 expected_enabled=0 |

### 证据表

| 证据 | 绝对路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed3/prop_evt.txt.gz` | `1db3d9275cfb56a0ca13007c9a009ac987f514d9d49c9ed14e0430dcbcc1aa92` |
| chain_report/regrade | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed3/chain_report.json` | `2240b159cf91856dfabd62429831e898260382f236a30b21b74afc5f6c41114e` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/manifest.json` | `730ca9788c6b0bc12cc4d218eea0758d4dedc9d719eadbe9fdc01aed9c1eca03` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed3/run.out` | `25506842d89af7d85f3df1213179a3bbb361373878411c958f1f95fea071decd` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed3/run.err` | `482bd31fcaaa688cce6887ea0f09d70b62637376b742d7161649bcefc386b41e` |
| stats.txt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3/T01-F0-W4/seed3/stats.txt` | `05fc4895e060abd97487d112dd6d740ac15279bed656f22bd06b94da9c54d198` |

- 原始事件流是否修改：**NO**
- 是否重新运行 gem5：**NO**
- 生成时间：`2026-10-27T17:36:59`；仓库 HEAD `6f98088a7144d7f6fb22d985be3023ac5658e71b`；生成脚本 `/tmp/gen_prop_v2.py`（SHA-256 `f33c3dac7656baf8114ff5c11f4effce1c2f10e7e13303c64ab8d54d6e94b8cb`）
