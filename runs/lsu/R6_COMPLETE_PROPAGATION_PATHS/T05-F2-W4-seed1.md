# T05-F2-W4 seed1 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T05-F2-W4`；seed：`1`；sample_run_id：`s1`
- 单元：L1d-TLB（DTLB）（故障模型 `T05`）
- fault type / 子模型：`valid_clear`（取自注入记录与本 seed 的 `inj` 事件）
- frequency tier：请求 `F2`／生效 `F2`／tier enabled=`1`（run.out CHAOS_LSU_TIER_CAP）
- 负载（矩阵标签）：`TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）`
- 实际 readfile：`（见启动命令）`
- 启动命令：`LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F2-W4_s1 --cells T05-F2-W4 --phase trial --seed-start 1 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300 --fs-timeout 5400 --fs-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015`
- 二进制路径：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- 二进制 SHA-256：`e379cc5bb14b16d525d24325d30029a9d4630df2b317e506e354e39e7d4efe4b`（期望 `e379cc5bb14b16d525d24325d30029a9d4630df2b317e506e354e39e7d4efe4b`）
- binary source head：`0501a00f3a4b20b6023a9249821c4b1c62bc8fad`
- analysis tool head：`51cdb116ae3279b79a1819cf3c6b3220b3eb9716`
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F2-W4_s1/T05-F2-W4/seed1`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F2-W4_s1/manifest.json`（status=`FINISHED`，exit_code=`None`，start=`2026-10-28T08:31:00+08:00`，end=`2026-10-28T08:58:24+08:00`）
- 运行目录进程：gem5_pid=`3628709`，pgid=`None`，`.done`=`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F2-W4_s1/.done`
- 正常 EOF：**是**（`gzip -t` 通过；事件解析到流尾）
- truncated：**False**；stats 非空：**是**
- 原始事件数：3245（chain_report.event_count=`3245`）
- fault_id 数：649

## 2. 注入位置与注入前后字段/地址/值

- 组件：`CHAOSArmTLB`；tick=`238085303040`，event_id=`0`
- 被改字段：`valid_clear`；before=`1`，after=`0`
- 注入器原始日志行：

```
Tick: 237950233578, Site: arm_tlb_lookup_tier, FaultType: valid_clear (lookup path now polls lsuTrigger; tier=F2; a tiered run does NOT consume --tlb_max_faults=1 — the tier is the frequency model)
Tick: 237950233911, Site: arm_tlb_lookup_no_request, VA: 0xffffffc009483eb8, FaultType: valid_clear (lookup carries no Request identity: not attributable, budget NOT consumed)
Tick: 238085303040, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094839a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 238103744247, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbda132, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 238143805479, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483c70, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 238443733584, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483bac, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 238628780019, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483c88, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 238679000082, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483b70, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 238806188433, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483ba8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 238958626509, Site: arm_tlb_lookup_hit, VA: 0xffffffc00946be60, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 239188171401, Site: arm_tlb_lookup_hit, VA: 0xffffff800192c858, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 239344919163, Site: arm_tlb_lookup_hit, VA: 0x7fe7c61908, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 239494282983, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483f00, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 239575372146, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483dc0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 239719220487, Site: arm_tlb_lookup_hit, VA: 0x557542b768, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 239805399555, Site: arm_tlb_lookup_hit, VA: 0x557542b9d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 239917113729, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbd40a8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 240211941939, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483a00, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 240445554093, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bca0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 240605965854, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c6d010, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 240799967325, Site: arm_tlb_lookup_hit, VA: 0xfffffffe0002d580, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 240912093753, Site: arm_tlb_lookup_hit, VA: 0x7fb3026be4, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 241046020359, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bae0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 241207562655, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493a58, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 241369498890, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493ac0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 241502133789, Site: arm_tlb_lookup_hit, VA: 0x7ff63fb4a8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 241601840982, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493c98, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 241728269094, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493af8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 241915654521, Site: arm_tlb_lookup_hit, VA: 0x7fd71b4568, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 242098699626, Site: arm_tlb_lookup_hit, VA: 0x7f9bb99448, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 242217136071, Site: arm_tlb_lookup_hit, VA: 0xfffffffe00092640, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 242336488266, Site: arm_tlb_lookup_hit, VA: 0xffffff800319f000, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 242466316641, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493ab0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 242623568232, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bbf0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 242722343025, Site: arm_tlb_lookup_hit, VA: 0xffffffc00948bbf0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 242814951657, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483b50, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 243109004976, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493cd8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 243202143744, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493cc0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 243297289170, Site: arm_tlb_lookup_hit, VA: 0x7facb99bc0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 243373429620, Site: arm_tlb_lookup_hit, VA: 0xffffff80011b9a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 243509007906, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493ad0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 243741294387, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bb08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 243869708844, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bc20, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 243941403744, Site: arm_tlb_lookup_hit, VA: 0x7fbd84ada0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 244025594136, Site: arm_tlb_lookup_hit, VA: 0xffffff80011bc108, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 244165948308, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bc08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 244314525915, Site: arm_tlb_lookup_hit, VA: 0xffffff80011bc108, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 244394654706, Site: arm_tlb_lookup_hit, VA: 0x7fe63f5010, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 244495641618, Site: arm_tlb_lookup_hit, VA: 0x7fe63f5338, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 244575427752, Site: arm_tlb_lookup_hit, VA: 0x7fe63f4d88, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 244628788005, Site: arm_tlb_lookup_hit, VA: 0xffffff80031c34a8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 244723528836, Site: arm_tlb_lookup_hit, VA: 0xfffffffe000c7520, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 244816272666, Site: arm_tlb_lookup_hit, VA: 0xffffff8001540430, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 244907520327, Site: arm_tlb_lookup_hit, VA: 0x7fe63f5768, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 245025454275, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b940, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 245077710300, Site: arm_tlb_lookup_hit, VA: 0x7fe63f56d8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 245186742492, Site: arm_tlb_lookup_hit, VA: 0xffffff8003227f98, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 245234120733, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bbc8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 245344185891, Site: arm_tlb_lookup_hit, VA: 0xffffff8003243940, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 245447935038, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bbf0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 245539033182, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b950, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 245598675147, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bd90, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 245676118626, Site: arm_tlb_lookup_hit, VA: 0xffffff800327e458, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 245803928022, Site: arm_tlb_lookup_hit, VA: 0xffffffc00883fe1c, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 245974311468, Site: arm_tlb_lookup_hit, VA: 0xffffff8003172690, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 246175886025, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b948, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 246381666039, Site: arm_tlb_lookup_hit, VA: 0x7fd296dce0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 246560065128, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bd28, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 246624434694, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bd70, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 246841962282, Site: arm_tlb_lookup_hit, VA: 0xffffff80031087d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 247390922439, Site: arm_tlb_lookup_hit, VA: 0x55699d3fdc, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 248030269119, Site: arm_tlb_lookup_hit, VA: 0xffffff800321c540, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 248727249108, Site: arm_tlb_lookup_hit, VA: 0x55699d1a28, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249108609033, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493b10, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249268997817, Site: arm_tlb_lookup_hit, VA: 0xffffffc008be93a8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249304416030, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493870, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249336123624, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249384447252, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493870, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249445726911, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493940, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249476478462, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c6d010, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249516156078, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c5a6d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249550138728, Site: arm_tlb_lookup_hit, VA: 0xffffff80011b9a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249615155313, Site: arm_tlb_lookup_hit, VA: 0xffffff800143624a, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249673413996, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938a8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249722572788, Site: arm_tlb_lookup_hit, VA: 0xfffffffe000a9080, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249772301010, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbce008, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249832538046, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249868446435, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938c8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249916491009, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249943056084, Site: arm_tlb_lookup_hit, VA: 0xffffff8001445daa, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250016077656, Site: arm_tlb_lookup_hit, VA: 0xffffff8001080078, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250090976349, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493870, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250129685268, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250180574328, Site: arm_tlb_lookup_hit, VA: 0xfffffffe01fe9280, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250229975877, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939f8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250285026438, Site: arm_tlb_lookup_hit, VA: 0xffffff8001444928, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250326197559, Site: arm_tlb_lookup_hit, VA: 0xfffffffe000371a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250358609115, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493948, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250394288067, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250450304994, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493928, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250482038895, Site: arm_tlb_lookup_hit, VA: 0xfffffffe00206100, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250536014865, Site: arm_tlb_lookup_hit, VA: 0xffffff800151b2d8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250596058428, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493880, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250655277150, Site: arm_tlb_lookup_hit, VA: 0xffffff80011b9a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250733568114, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c82c18, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250756671321, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493908, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250791646977, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493b18, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250841196378, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250867127421, Site: arm_tlb_lookup_hit, VA: 0xfffffffe000c0f10, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250939614528, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493950, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250985674089, Site: arm_tlb_lookup_hit, VA: 0xfffffffe000afb40, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251035316064, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493870, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251076914091, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493908, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251121440187, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938b8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251174960613, Site: arm_tlb_lookup_hit, VA: 0xfffffffe000a4b48, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251228207646, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251281144989, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493840, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251336295783, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939a8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251398635714, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbce008, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251422899759, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938a8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251464704579, Site: arm_tlb_lookup_hit, VA: 0xffffffc008be8af8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251496534717, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939c8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251579502000, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493a00, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251662240179, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251729616402, Site: arm_tlb_lookup_hit, VA: 0xffffff80011b9a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251786679948, Site: arm_tlb_lookup_hit, VA: 0xffffff80011b9a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251881459740, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939f8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251933679135, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493900, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 252099007308, Site: arm_tlb_lookup_hit, VA: 0xffffff80011b9e58, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 252275588217, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbd4700, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 252367901811, Site: arm_tlb_lookup_hit, VA: 0xffffff800181bc50, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 252488726199, Site: arm_tlb_lookup_hit, VA: 0xffffff80018e0008, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 252572643864, Site: arm_tlb_lookup_hit, VA: 0xffffff8001361a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 252656165925, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbd4048, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 252776234070, Site: arm_tlb_lookup_hit, VA: 0xffffff8001361a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 252870811731, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b5c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 252966229218, Site: arm_tlb_lookup_hit, VA: 0xfffffffe0002c088, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 253129563720, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b778, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 253254156336, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003d00, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 253348695369, Site: arm_tlb_lookup_hit, VA: 0xffffff8001c7b280, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 253480883049, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c0d280, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 253572210630, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c79824, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 253690079976, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b958, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 253802613996, Site: arm_tlb_lookup_hit, VA: 0x7fda2d8560, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 253876838697, Site: arm_tlb_lookup_hit, VA: 0x7f96912384, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 254094185466, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b2f8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 254154695895, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b578, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 254230814034, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b5f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 254266621857, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b6d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 254377256112, Site: arm_tlb_lookup_hit, VA: 0xffffff80018e0008, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 254422566090, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b808, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 254503348893, Site: arm_tlb_lookup_hit, VA: 0xffffff800181bc72, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 254657230191, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bad8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 254770287687, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 254924871948, Site: arm_tlb_lookup_hit, VA: 0xffffff8001361ce8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 255011718348, Site: arm_tlb_lookup_hit, VA: 0xffffff80011970c8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 255096408240, Site: arm_tlb_lookup_hit, VA: 0xffffff8001361e58, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 255268120356, Site: arm_tlb_lookup_hit, VA: 0x5564153420, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 255505842396, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 255591807012, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b9ca, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 255681220842, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 255915543285, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b910, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 256086353970, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 256326284133, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b928, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 256551429762, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b920, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 257095390923, Site: arm_tlb_lookup_hit, VA: 0x5564152f1c, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 257386747941, Site: arm_tlb_lookup_hit, VA: 0xffffff8001be5008, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 257585043780, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 257639213223, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949394a, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 257681407986, Site: arm_tlb_lookup_hit, VA: 0xffffff80011b9a18, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 257736131874, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c6d010, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 257829987258, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493908, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 257877473724, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbd3d88, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 257935670136, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 257988374046, Site: arm_tlb_lookup_hit, VA: 0xffffff80014a0158, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 258122294991, Site: arm_tlb_lookup_hit, VA: 0xffffff8001080008, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 258180730164, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493840, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 258368664042, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493ba8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 258529969575, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b670, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 258577389774, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b6d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 258620834619, Site: arm_tlb_lookup_hit, VA: 0xffffff800189d024, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 258713765262, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949ba50, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 258820542045, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003d60, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 258911717445, Site: arm_tlb_lookup_hit, VA: 0xffffff8001364e08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 258956107677, Site: arm_tlb_lookup_hit, VA: 0xffffff8001365258, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 259053170184, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003cd0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 259186435785, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b420, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 259257734415, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b640, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 259334388018, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003e38, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 259550320869, Site: arm_tlb_lookup_hit, VA: 0xffffff8001364e08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 259657523559, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003db0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 259741962369, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b790, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 259867742463, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bc80, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 259996758318, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbda264, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 260065103238, Site: arm_tlb_lookup_hit, VA: 0xffffff800192c510, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 260191936611, Site: arm_tlb_lookup_hit, VA: 0x7ff73775a8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 260266075065, Site: arm_tlb_lookup_hit, VA: 0x7f81c6a3be, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 260436486816, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003d50, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 260509936959, Site: arm_tlb_lookup_hit, VA: 0xffffff8001c9ae68, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 260560354491, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b648, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 260593302843, Site: arm_tlb_lookup_hit, VA: 0xffffff800191d646, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 260689253463, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbd4700, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 260763248061, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b7c8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 260921376441, Site: arm_tlb_lookup_hit, VA: 0xffffff8001c918d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 260982814941, Site: arm_tlb_lookup_hit, VA: 0x7f81d82278, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 261047366325, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bb88, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 261290824956, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 261455820462, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b938, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 261619605513, Site: arm_tlb_lookup_hit, VA: 0xffffff8001365258, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 261794081862, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b908, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 262016419302, Site: arm_tlb_lookup_hit, VA: 0x558435009c, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 262092385926, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 262254454695, Site: arm_tlb_lookup_hit, VA: 0x558434c088, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 262338423309, Site: arm_tlb_lookup_hit, VA: 0xffffff80031fd350, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 262428595713, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 262733945058, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b91a, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 263176466427, Site: arm_tlb_lookup_hit, VA: 0x558434a8b8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 263415877443, Site: arm_tlb_lookup_hit, VA: 0x558434bf70, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 263740182813, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bb38, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 263890396449, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938b8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 263936594538, Site: arm_tlb_lookup_hit, VA: 0xffffff8001409240, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 264004238826, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493930, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 264049329024, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493908, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 264164938632, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493900, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 264223078101, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbd3df8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 264300060375, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939da, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 264368141892, Site: arm_tlb_lookup_hit, VA: 0xfffffffe00093408, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 264593650158, Site: arm_tlb_lookup_hit, VA: 0xfffffffe0002eb48, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 264712188501, Site: arm_tlb_lookup_hit, VA: 0xffffff8001361a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 264781516104, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b260, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 264863486385, Site: arm_tlb_lookup_hit, VA: 0xffffff8001545488, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 264958716393, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b6d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 265050094590, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b6b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 265146266655, Site: arm_tlb_lookup_hit, VA: 0xffffff8001361a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 265240287873, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b958, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 265363244460, Site: arm_tlb_lookup_hit, VA: 0xffffff8001918a58, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 265450111173, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b5d8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 265500752814, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b570, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 265555224621, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b988, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 265738738590, Site: arm_tlb_lookup_hit, VA: 0xffffff800191771c, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 265836368196, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003d70, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 265917348135, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b750, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 265972925169, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b588, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 266128767837, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b740, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 266179591629, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b718, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 266304736026, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b9f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 266413314339, Site: arm_tlb_lookup_hit, VA: 0x7fd8c8de90, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 266600705760, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbd4048, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 266655794949, Site: arm_tlb_lookup_hit, VA: 0xffffff800191dc80, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 266786705574, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b588, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 266874091101, Site: arm_tlb_lookup_hit, VA: 0xfffffffe00062f80, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 266950602180, Site: arm_tlb_lookup_hit, VA: 0xfffffffe0006bee0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 267007120605, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b828, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 267171617943, Site: arm_tlb_lookup_hit, VA: 0x7fd8c8e266, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 267346872180, Site: arm_tlb_lookup_hit, VA: 0x55904c1e18, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 267587528616, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 267761177793, Site: arm_tlb_lookup_hit, VA: 0xffffff800155ba98, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 267842992563, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 267998921478, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b9c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 268086894084, Site: arm_tlb_lookup_hit, VA: 0x55904c0058, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 268259106033, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bb18, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 268341443280, Site: arm_tlb_lookup_hit, VA: 0xffffff80031f0a00, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 268500715515, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b910, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 268661736000, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b9ca, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 268894355481, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b910, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 269267731398, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949ba40, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 269690956083, Site: arm_tlb_lookup_hit, VA: 0x55904c3670, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 269922364776, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bce0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 270130541391, Site: arm_tlb_lookup_hit, VA: 0xffffff800151dfa0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 270171179379, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 270202758435, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493950, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 270248995152, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbda170, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 270273557232, Site: arm_tlb_lookup_hit, VA: 0xfffffffe00073e80, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 270385552125, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493950, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 270416260053, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbda263, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 270469046547, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493b90, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 270516305241, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 270546257259, Site: arm_tlb_lookup_hit, VA: 0xfffffffe00096300, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 270598645485, Site: arm_tlb_lookup_hit, VA: 0xffffff80011b9a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 270821703537, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bd70, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 271002307419, Site: arm_tlb_lookup_hit, VA: 0xffffff8001364e08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 271061174160, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b558, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 271160686881, Site: arm_tlb_lookup_hit, VA: 0xffffff8001918518, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 271210008510, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b3c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 271329161571, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b520, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 271462670928, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003d40, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 271532033496, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b4f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 271583552259, Site: arm_tlb_lookup_hit, VA: 0xffffff8001919858, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 271633107987, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b4c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 271716021990, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b500, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 271744546770, Site: arm_tlb_lookup_hit, VA: 0xffffff8001373e9c, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 271947337110, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b778, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 272003059332, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbd4728, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 272102118507, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bd48, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 272158719183, Site: arm_tlb_lookup_hit, VA: 0xffffff8001c91828, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 272203673184, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b44c, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 272268323802, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b758, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 272346282099, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b818, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 272413927386, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003d30, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 272493495405, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b780, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 272575296855, Site: arm_tlb_lookup_hit, VA: 0x7f91a68d74, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 272695192173, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bbe8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 272871038484, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b6b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 272936170620, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbd46e8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 272993647752, Site: arm_tlb_lookup_hit, VA: 0xffffff800151a330, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 273104286336, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b7c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 273191308227, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003e88, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 273356249454, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bcba, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 273424271031, Site: arm_tlb_lookup_hit, VA: 0xffffff8001365258, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 273513142737, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b91a, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 273594666465, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8b8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 273685328712, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 273773053566, Site: arm_tlb_lookup_hit, VA: 0xffffff80031a7970, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 273884850657, Site: arm_tlb_lookup_hit, VA: 0x5581dc41a4, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 274015987389, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 274152045528, Site: arm_tlb_lookup_hit, VA: 0xffffff80014b29a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 274321884186, Site: arm_tlb_lookup_hit, VA: 0xffffff8001365258, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 274471368219, Site: arm_tlb_lookup_hit, VA: 0x5581dc8d28, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 274559624208, Site: arm_tlb_lookup_hit, VA: 0xffffff80014b2db0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 274639569849, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bb08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 274681641402, Site: arm_tlb_lookup_hit, VA: 0x5581dc43f8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 274813374204, Site: arm_tlb_lookup_hit, VA: 0x5581dc5a00, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 274972562523, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 275124067200, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b920, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 275350926447, Site: arm_tlb_lookup_hit, VA: 0xffffff800323db50, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 276027422274, Site: arm_tlb_lookup_hit, VA: 0x7fded847f8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 276184459413, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493960, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 276304251834, Site: arm_tlb_lookup_hit, VA: 0xfffffffe00049948, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 276361129233, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493ac8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 276417703935, Site: arm_tlb_lookup_hit, VA: 0xfffffffe0006fbc0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 276455890710, Site: arm_tlb_lookup_hit, VA: 0xffffff8001432850, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 276552152019, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 276591654477, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 276621459309, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 276661014381, Site: arm_tlb_lookup_hit, VA: 0xfffffffe000a8848, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 276704346339, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 276771116835, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939da, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 276994764630, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bbe0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 277168467087, Site: arm_tlb_lookup_hit, VA: 0xffffff8001426818, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 277285513923, Site: arm_tlb_lookup_hit, VA: 0xffffff807d8ffb08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 277367833854, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b710, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 277400782872, Site: arm_tlb_lookup_hit, VA: 0xffffff8001361a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 277471778805, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b738, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 277532157366, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b708, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 277655483583, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b3a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 277772665284, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003cf0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 277859730132, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b6e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 277920399735, Site: arm_tlb_lookup_hit, VA: 0xffffff8001361a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 278120491110, Site: arm_tlb_lookup_hit, VA: 0xffffff8001080000, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 278255281185, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b4b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 278359993368, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b808, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 278412126849, Site: arm_tlb_lookup_hit, VA: 0xffffff8001361ce4, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 278539055793, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003e80, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 278644866876, Site: arm_tlb_lookup_hit, VA: 0xffffff800183a680, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 278770027257, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bc10, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 278869479039, Site: arm_tlb_lookup_hit, VA: 0xffffff8001438248, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 279041907105, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b4a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 279146075832, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b5c8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 279208804041, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b250, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 279304584831, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b730, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 279357744285, Site: arm_tlb_lookup_hit, VA: 0xffffff800181bc50, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 279429064560, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b5d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 279589237893, Site: arm_tlb_lookup_hit, VA: 0xffffff8001d969c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 279657349713, Site: arm_tlb_lookup_hit, VA: 0x5583bcf308, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 279757615014, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 279922159971, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 280085928039, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 280259188605, Site: arm_tlb_lookup_hit, VA: 0x5583bd3168, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 280340860851, Site: arm_tlb_lookup_hit, VA: 0xffffff8001361e58, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 280503098118, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 280664881839, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 280750618350, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949ba20, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 280909176966, Site: arm_tlb_lookup_hit, VA: 0x5583bcfe38, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 280999951101, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 281152047852, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 281237513967, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8e8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 281533859991, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949baf8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 281961083340, Site: arm_tlb_lookup_hit, VA: 0x5583bd1a90, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 282329088633, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bae8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 282405866112, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493ad0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 282539135043, Site: arm_tlb_lookup_hit, VA: 0xffffff8001481184, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 282581956179, Site: arm_tlb_lookup_hit, VA: 0xfffffffe00070648, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 282623075685, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 282666791592, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 282693188502, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493900, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 282799661589, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493890, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 282847395474, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493948, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 282928004118, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 282994289433, Site: arm_tlb_lookup_hit, VA: 0xffffff80011b9a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 283128555366, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493b70, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 283233528288, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bd50, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 283380433569, Site: arm_tlb_lookup_hit, VA: 0xffffff8001915940, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 283418706591, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b0f8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 283535533314, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b6d8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 283615895871, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b5c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 283733400915, Site: arm_tlb_lookup_hit, VA: 0xffffff8001afb210, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 283780129473, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b6a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 283936871574, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b3e8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 284018177187, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b720, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 284091150474, Site: arm_tlb_lookup_hit, VA: 0xffffff80013650e8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 284154920640, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b828, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 284245919550, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b6d8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 284351700663, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbce008, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 284461879374, Site: arm_tlb_lookup_hit, VA: 0xffffff80013650e4, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 284580308826, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b880, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 284657479578, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003cf0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 284797339911, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b758, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 284881027806, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bb28, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 284977873197, Site: arm_tlb_lookup_hit, VA: 0x7fcab13bc8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 285168205674, Site: arm_tlb_lookup_hit, VA: 0xffffff80014a5b60, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 285219706455, Site: arm_tlb_lookup_hit, VA: 0xffffff8001365258, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 285328109943, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbda264, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 285367295718, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b640, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 285405979995, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bc80, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 285473802105, Site: arm_tlb_lookup_hit, VA: 0xffffff800151cc10, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 285522514011, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b3e8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 285579427374, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbda264, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 285661451934, Site: arm_tlb_lookup_hit, VA: 0x7fcab13930, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 285824921634, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 286006918455, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 286104544065, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b9c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 286295637780, Site: arm_tlb_lookup_hit, VA: 0x55b32d85d8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 286463308275, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 286632527220, Site: arm_tlb_lookup_hit, VA: 0xffffff80013650e4, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 286867002177, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b910, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 286948792305, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949be00, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 287043678324, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b910, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 287126157762, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b91a, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 287363073942, Site: arm_tlb_lookup_hit, VA: 0xffffff8003214850, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 287448857073, Site: arm_tlb_lookup_hit, VA: 0x55b32dd448, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 287595821961, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8b8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 287884651176, Site: arm_tlb_lookup_hit, VA: 0x7fcab141b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 288457851735, Site: arm_tlb_lookup_hit, VA: 0xffffff8001b9aa18, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 288525563955, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949ba90, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 288683333694, Site: arm_tlb_lookup_hit, VA: 0xffffff80011b9a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 288747008622, Site: arm_tlb_lookup_hit, VA: 0xfffffffe00070cc0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 288785523402, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493950, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 288825131754, Site: arm_tlb_lookup_hit, VA: 0xffffffc008a173c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 288891898254, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493ba8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 288976958109, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493898, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 289033896447, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493990, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 289105208397, Site: arm_tlb_lookup_hit, VA: 0xfffffffe00095e88, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 289192855995, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c79824, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 289366931412, Site: arm_tlb_lookup_hit, VA: 0xfffffffe0002f480, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 289479632931, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b450, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 289569906567, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003dd8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 289680833196, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b698, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 289739736567, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b530, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 289819037520, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbd6000, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 289916437356, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b6c8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 290036656017, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbd3d08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 290109196404, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b460, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 290203769403, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b700, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 290259156960, Site: arm_tlb_lookup_hit, VA: 0xfffffffe00068e08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 290314575153, Site: arm_tlb_lookup_hit, VA: 0xffffff8001360008, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 290431304307, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b610, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 290572457013, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b910, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 290685825198, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003e08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 290793117132, Site: arm_tlb_lookup_hit, VA: 0xffffff800185f808, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 290940670098, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b750, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 291036009663, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949be48, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 291183252939, Site: arm_tlb_lookup_hit, VA: 0x7fe2650940, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 291374745255, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b6d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 291503378493, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b668, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 291549366126, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b438, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 291629883861, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b780, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 291697677666, Site: arm_tlb_lookup_hit, VA: 0xffffff8001360008, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 291732912729, Site: arm_tlb_lookup_hit, VA: 0xffffff80014eb4e4, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 291837699504, Site: arm_tlb_lookup_hit, VA: 0x7fe2650e18, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 292016873817, Site: arm_tlb_lookup_hit, VA: 0xffffff80014b26d8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 292199796378, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bd40, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 292293423324, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 292448738853, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8d8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 292615055703, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b920, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 292703217786, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bb10, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 292856613570, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 293019691995, Site: arm_tlb_lookup_hit, VA: 0xffffff800155b934, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 293106946653, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 293188335849, Site: arm_tlb_lookup_hit, VA: 0xffffff80014b2b68, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 293275020411, Site: arm_tlb_lookup_hit, VA: 0xffffff80013602e4, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 293442202395, Site: arm_tlb_lookup_hit, VA: 0xffffff80014b2718, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 293675733630, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b938, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 294163110765, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bc48, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 294477278283, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949ba60, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 294748639650, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949ba20, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 294902751717, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 294931225548, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 294976134261, Site: arm_tlb_lookup_hit, VA: 0xffffff80014316b8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 295044700626, Site: arm_tlb_lookup_hit, VA: 0xfffffffe000546e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 295079691267, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c6d010, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 295171297569, Site: arm_tlb_lookup_hit, VA: 0xfffffffe00093680, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 295209514980, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbd3d98, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 295271876223, Site: arm_tlb_lookup_hit, VA: 0xfffffffe000b05d8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 295351651368, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 295410506454, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493b98, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 295618654431, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bd18, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 295760936340, Site: arm_tlb_lookup_hit, VA: 0xffffff80013655e8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 295823085462, Site: arm_tlb_lookup_hit, VA: 0xffffffc008be89ec, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 295946052039, Site: arm_tlb_lookup_hit, VA: 0xffffff8001364e08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 295994289087, Site: arm_tlb_lookup_hit, VA: 0xffffff800183ad60, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 296039239758, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b698, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 296170430436, Site: arm_tlb_lookup_hit, VA: 0xffffff8001364e08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 296262123651, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b410, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 296375876451, Site: arm_tlb_lookup_hit, VA: 0xffffff80014810f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 296423547399, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbd47a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 296498758779, Site: arm_tlb_lookup_hit, VA: 0xffffff8001424068, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 296564309163, Site: arm_tlb_lookup_hit, VA: 0xffffff8001364e00, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 296704003662, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bab8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 296782837416, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b698, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 296925585525, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 297011896794, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003d80, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 297111655602, Site: arm_tlb_lookup_hit, VA: 0xffffff8001365258, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 297175783743, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b5e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 297227206935, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b9c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 297377093565, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bb80, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 297556466679, Site: arm_tlb_lookup_hit, VA: 0xfffffffe000762c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 297624777633, Site: arm_tlb_lookup_hit, VA: 0xffffff8001acde14, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 297756844434, Site: arm_tlb_lookup_hit, VA: 0xffffff80013650e4, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 297859139037, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b828, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 297948366387, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b6b8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 298100240694, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bf38, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 298242470988, Site: arm_tlb_lookup_hit, VA: 0xffffff8001364e08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 298433856078, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949ba50, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 298609615809, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 298695083256, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 298864786716, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 299021615064, Site: arm_tlb_lookup_hit, VA: 0x55c8596aa8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 299111322267, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bb10, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 299267215551, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 299354176836, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b938, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 299469397500, Site: arm_tlb_lookup_hit, VA: 0x55c85967e4, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 299597963472, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 299757153456, Site: arm_tlb_lookup_hit, VA: 0xffffff8001365258, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 299910358764, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b9b8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 300141451773, Site: arm_tlb_lookup_hit, VA: 0xffffff8003241b60, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 300707006985, Site: arm_tlb_lookup_hit, VA: 0x55c8597ec0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 300980643408, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493c98, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 301117689225, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 301172306553, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 301215091392, Site: arm_tlb_lookup_hit, VA: 0xffffff8001445dc0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 301277416338, Site: arm_tlb_lookup_hit, VA: 0xffffff800149c4e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 301358906766, Site: arm_tlb_lookup_hit, VA: 0xffffff80011b9a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 301384132848, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493920, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 301419707238, Site: arm_tlb_lookup_hit, VA: 0xfffffffe000b5780, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 301461054183, Site: arm_tlb_lookup_hit, VA: 0xffffff80014a4310, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 301520820357, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 301553105040, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493950, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 301612565520, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 301885849296, Site: arm_tlb_lookup_hit, VA: 0xfffffffe00093f40, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 301962450951, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b408, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 302066847783, Site: arm_tlb_lookup_hit, VA: 0xffffff800189b860, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 302122103805, Site: arm_tlb_lookup_hit, VA: 0xffffff8001918e20, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 302202261900, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b430, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 302322543165, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b5f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 302385332979, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003cf0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 302531500998, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b3d8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 302607789966, Site: arm_tlb_lookup_hit, VA: 0xffffff8000bd6f2c, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 302693513157, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b660, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 302834814714, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bc78, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 302976379008, Site: arm_tlb_lookup_hit, VA: 0xffffff8001408948, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 303057563409, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003d48, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 303199526637, Site: arm_tlb_lookup_hit, VA: 0xffffffc008beb588, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 303303580146, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b900, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 303373250406, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b808, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 303482253294, Site: arm_tlb_lookup_hit, VA: 0xffffff80014a56d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 303560955180, Site: arm_tlb_lookup_hit, VA: 0xffffff8000b61110, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 303709716603, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8d8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 303849172008, Site: arm_tlb_lookup_hit, VA: 0xffffff8001247b00, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 303957640764, Site: arm_tlb_lookup_hit, VA: 0xffffff8001361a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 304029201465, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b888, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 304120375533, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b208, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 304169208318, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b888, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 304203666159, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bad0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 304374355632, Site: arm_tlb_lookup_hit, VA: 0x559ca46a80, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 304518471705, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 304685029647, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b910, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 304858989180, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b920, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 304946176239, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 305109270648, Site: arm_tlb_lookup_hit, VA: 0xffffff8001361ce8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 305203011147, Site: arm_tlb_lookup_hit, VA: 0x559ca47ed8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 305431134795, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 305591056380, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 305686532142, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 305768795463, Site: arm_tlb_lookup_hit, VA: 0x559ca4d670, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 305849657187, Site: arm_tlb_lookup_hit, VA: 0x559ca4dc20, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 306151197678, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b938, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 306422509761, Site: arm_tlb_lookup_hit, VA: 0x559ca4b278, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 306958158576, Site: arm_tlb_lookup_hit, VA: 0xffffff8003280550, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 307172281905, Site: arm_tlb_lookup_hit, VA: 0xfffffffe0002d6f4, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 307340944074, Site: arm_tlb_lookup_hit, VA: 0xfffffffe00074574, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 307402716573, Site: arm_tlb_lookup_hit, VA: 0xffffff80011b9a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 307429205724, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493910, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 307491035499, Site: arm_tlb_lookup_hit, VA: 0xfffffffe0004e288, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 307573104681, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493b98, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 307611823257, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493990, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 307653499872, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493990, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 307720818819, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939da, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 307750219722, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939da, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 307806717168, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493b58, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 307994584446, Site: arm_tlb_lookup_hit, VA: 0x5582430e68, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 308113289289, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b540, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 308174997852, Site: arm_tlb_lookup_hit, VA: 0xfffffffe00074a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 308264134293, Site: arm_tlb_lookup_hit, VA: 0xffffffc008ea3cd0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 308383672302, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b5a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 308493316548, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b560, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 308553386085, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c79824, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 308666579445, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b520, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 308744898048, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b51a, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 308848499343, Site: arm_tlb_lookup_hit, VA: 0xffffff8001364e08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 308926723707, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b578, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 309037584735, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bb78, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 309179798712, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b610, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 309327299064, Site: arm_tlb_lookup_hit, VA: 0xffffff8001afb410, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 309397559733, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b748, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 309451384521, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b900, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 309591970794, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b810, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 309656091276, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bc10, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 309708844470, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003d60, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 309788687214, Site: arm_tlb_lookup_hit, VA: 0x7ffd367cb0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 309954102633, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b6f8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 310026586410, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003e10, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 310159365498, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c5c0d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 310261783644, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 310308892155, Site: arm_tlb_lookup_hit, VA: 0xffffff8001364e08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 310354282053, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b438, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 310398814476, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b830, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 310565958498, Site: arm_tlb_lookup_hit, VA: 0x558cc54728, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 310716106533, Site: arm_tlb_lookup_hit, VA: 0x558cc59908, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 310840976538, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 311006748600, Site: arm_tlb_lookup_hit, VA: 0xffffff80013650e4, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 311094217044, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b938, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 311263118973, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8e8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 311423715216, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b920, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 311594380047, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8c8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 311728710915, Site: arm_tlb_lookup_hit, VA: 0x558cc5c0a4, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 311911691085, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b918, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 311995225134, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8e8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 312160899294, Site: arm_tlb_lookup_hit, VA: 0xffffff8003215a90, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 312392722572, Site: arm_tlb_lookup_hit, VA: 0xffffff80014b26d8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 312896749374, Site: arm_tlb_lookup_hit, VA: 0x558cc571e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 313303042674, Site: arm_tlb_lookup_hit, VA: 0xfffffffe0002b308, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 313562643480, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493bc8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 313736537079, Site: arm_tlb_lookup_hit, VA: 0xffffff80018cff58, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 313881054084, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003db0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 313970272776, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949ba48, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 314039051262, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bab0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 314074546398, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003d30, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 314218465002, Site: arm_tlb_lookup_hit, VA: 0xffffffc008d0bc98, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 314278193880, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949ba58, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 314340009336, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b978, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 314419864734, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b980, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
```

## 3. 完整故障传播过程（按真实事件顺序）

本 seed 的事件流按 `event_id` 顺序叙述；主链由终局见证 event_id=`2595`（kind=`tlb_translate_result`）沿 `parent_event_id` 回溯到 L0 注入，共 4 个事件。以下逐层说明：每一段先给出该层真实事件，再说明字段/状态如何变化。

（本 seed 共 3245 个事件，为可读性第 3 章只逐条叙述**主链** 4 个事件；**全部**事件已逐条列在第 4 章对照表中，第 5 章给出主链索引。旁支事件见第 4 章。）

### 3.1 `inj`（L0 注入）

- `event_id=2592`，`tick=314419864734`，`corr=origin`，`request_id=361375740`，`dyn_inst_seq=361375740`，`field=valid_clear`，`before=1`，`after=0`

### 3.2 `tlb_lookup`（L1 TLB 查询）

- `event_id=2593`，`parent_event_id=2592`，`tick=314419864734`，`corr=seq_primary`，`request_id=361375740`，`dyn_inst_seq=361375740`，`walk_id=0`，`va=ffffffc00949b980`，`entry_index=20`，`way=-1`，`field=post_lookup`，`before=1`，`after=0`，`state_before=vpn=ffffffc00949b;asid=232;valid=1;global=1;pfn=81d0c;ap=0;mtype=2;page_size=1000;pa=81d0c980`，`state_after=vpn=ffffffc00949b;asid=232;valid=0;global=1;pfn=81d0c;ap=0;mtype=2;page_size=1000;pa=81d0c980`
  该事件把 TLB 表项的状态/字段从 `vpn=ffffffc00949b;asid=232;valid=1;global=1;pfn=81d0c;ap=0;mtype=2;page_size=1000;pa=81d0c980` 变为 `vpn=ffffffc00949b;asid=232;valid=0;global=1;pfn=81d0c;ap=0;mtype=2;page_size=1000;pa=81d0c980`；这就是故障值进入翻译路径的位置。

### 3.3 `tlb_state`（L2 TLB 状态）

- `event_id=2594`，`parent_event_id=2593`，`tick=314419864734`，`corr=seq_primary`，`request_id=361375740`，`dyn_inst_seq=361375740`，`va=ffffffc00949b980`，`field=valid_clear`，`state_before=1`，`state_after=0`
  该事件把 TLB 表项的状态/字段从 `1` 变为 `0`；这就是故障值进入翻译路径的位置。

### 3.4 `tlb_translate_result`（L2 翻译结果）

- `event_id=2595`，`parent_event_id=2594`，`tick=314419864734`，`corr=seq_primary`，`request_id=361375740`，`dyn_inst_seq=361375740`，`walk_id=0`，`va=ffffffc00949b980`，`pa=81d0c980`，`entry_index=20`，`way=-1`，`field=effective_pa_unchanged`，`before=81d0c980`，`after=81d0c980`，`state_before=vpn=ffffffc00949b;asid=232;valid=1;global=1;pfn=81d0c;ap=0;mtype=2;page_size=1000;pa=81d0c980`，`state_after=vpn=ffffffc00949b;asid=232;valid=0;global=1;pfn=81d0c;ap=0;mtype=2;page_size=1000;pa=81d0c980`，`detection_layer=L2`，`contained=1`，`outcome=NoFault`，`containment_reason=effective_pa_unchanged`
  翻译完成：PA 由 `81d0c980` 变为 `81d0c980`，outcome=`NoFault`，contained=`1`，detection_layer=`L2`，reason=`effective_pa_unchanged`。

## 4. 每一级组件/请求/地址/状态变化（对照表）

| event_id | kind | 层 | 组件/对象 | 请求/事务 | 地址 | 状态变化 |
|---|---|---|---|---|---|---|
| 2592 | `inj` | L0 | CHAOSArmTLB | `361375740` | `—` | `1` → `0` |
| 2593 | `tlb_lookup` | L1 | DTLB CAM | `361375740` | `ffffffc00949b980` | `vpn=ffffffc00949b;asid=232;valid=1;global=1;pfn=81d0c;ap=0;mtype=2;page_size=1000;pa=81d0c980` → `vpn=ffffffc00949b;asid=232;valid=0;global=1;pfn=81d0c;ap=0;mtype=2;page_size=1000;pa=81d0c980` |
| 2594 | `tlb_state` | L2 | DTLB 表项 | `361375740` | `ffffffc00949b980` | `1` → `0` |
| 2595 | `tlb_translate_result` | L2 | MMU 翻译 | `361375740` | `81d0c980` | `vpn=ffffffc00949b;asid=232;valid=1;global=1;pfn=81d0c;ap=0;mtype=2;page_size=1000;pa=81d0c980` → `vpn=ffffffc00949b;asid=232;valid=0;global=1;pfn=81d0c;ap=0;mtype=2;page_size=1000;pa=81d0c980` |


（第 4 章仅逐条列出主链 4 个事件；其余 3241 个旁支事件按 kind 汇总如下，其原始行全部保留在 `prop_evt.txt.gz` 中，可逐条复核。）

| kind | 数量 | 首个 event_id | 末个 event_id |
|---|---|---|---|
| `inj` | 649 | 0 | 2592 |
| `tlb_lookup` | 649 | 1 | 2593 |
| `tlb_state` | 649 | 2 | 2594 |
| `tlb_translate_result` | 649 | 3 | 2595 |
| `chain_end` | 649 | 2596 | 3244 |

## 5. 证据索引（event_id / parent_event_id / tick / corr / request_id）

主链（从注入到终局见证）：

```
2592(inj) → 2593(tlb_lookup) → 2594(tlb_state) → 2595(tlb_translate_result)
```

| event_id | parent | tick | corr | request_id | fault_id |
|---|---|---|---|---|---|
| 2592 | — | 314419864734 | `origin` | `361375740` | 649 |
| 2593 | 2592 | 314419864734 | `seq_primary` | `361375740` | 649 |
| 2594 | 2593 | 314419864734 | `seq_primary` | `361375740` | 649 |
| 2595 | 2594 | 314419864734 | `seq_primary` | `361375740` | 649 |

## 6. 最终结局如何表现

- chain_report.terminal = `detected_contained`；provable_to = `L2`；oracle_outcome = `Masked`
- 结局形成：终局见证是 `tlb_translate_result`（event_id=2595），其字段 `outcome=NoFault`、`contained=1`、`detection_layer=L2`、`containment_reason=effective_pa_unchanged`。

**为何形成该结局**：`valid_clear` 把被命中表项的 valid 位由 1 改为 0。该表项在本次查询**已经被匹配**（`tlb_lookup` 显示的是 post_lookup 状态），因此本次翻译仍用它原来的 pfn 完成；被清零的位只可能影响**之后**对同一 VPN 的查询（本流未观测到再次查询；因有效 PA 未变，本型号**不开**关联臂，`corr=seq_primary` 只是标签，链如实止于 L2）。因此本次翻译的有效 PA 不变、无下游 L3+ 事件，结局是 L2 `effective_pa_unchanged` 含住（Masked）。
- 该 seed 是真实检测含住：检测层、原因、outcome 与闭合对象都在事件的 `detection_layer`/`containment_reason`/`outcome` 字段中，含住对象是被中止/未被消费的那次翻译或访问。

## 7. checker / campaign 判定

- admitted=`True`，certified=`True`，violations=`[]`，truncated=`False`
- campaign 三源计数：attempted=`66274586`，eligible=`66274586`，injected=`649`（日志应用行 649 条），activated=`649`，count_contradiction=`False`

## 8. 原始事件流、chain_report、manifest、日志与 SHA

- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F2-W4_s1/T05-F2-W4/seed1/prop_evt.txt.gz` — SHA-256 `431b58173a41c05ebc4e6aba097ed9a755b620e285d490d680e2e56747bfb8b2`（138092 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F2-W4_s1/T05-F2-W4/seed1/chain_report.json` — SHA-256 `c8bdb4ebae91437b79ea109918cc250a7748a8c106a7dac723cf02c838af0524`（491030 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F2-W4_s1/T05-F2-W4/seed1/stats.txt` — SHA-256 `a5c307d7a50590cf3086a86a6dcd40bad67b351bb78308181ba947818ea6c940`（429587 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F2-W4_s1/T05-F2-W4/seed1/run.out` — SHA-256 `a60e6e87a64a06511aae7e387162a4ca17a6ad0cea8998d39c1cb443ee492694`（68486 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F2-W4_s1/T05-F2-W4/seed1/run.err` — SHA-256 `75c8553cca8d0a645f25adaf093fffa9cd6ef8994e4a526426801917f0e59e6e`（1872 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F2-W4_s1/T05-F2-W4/seed1/armtlb_injections.log` — SHA-256 `1963c2dcc753f247be0f4db7db40ea0607af5efd3071d995cad50a800dbf2975`（86309 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F2-W4_s1/manifest.json` — SHA-256 `aae8d1e1f76c9c7bb9c1e7baf0932e59bcdb6ce7672c0642946187aaee1fee94`（2110 B）

## 9. 实验条件有效性 vs 观测链完整性（分开报告）

- **实验条件有效性**：workload/故障类型/频率档与矩阵一致；二进制 SHA 与 manifest 一致（`e379cc5bb14b…`）；真实注入（见第 2 章）；三源计数一致（count_contradiction=`False`）；正常 EOF、stats 非空、未截断。
- **观测链完整性**：terminal=`detected_contained`、provable_to=`L2`、admitted=`True`、certified=`True`、violations=`[]`。两者互不替代：条件有效不等于链完整，链完整也不弥补条件错误。

