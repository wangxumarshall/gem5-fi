# T05-F2-W4 seed2 故障传播与最终结局

## 1. 实验身份与复现信息

- RunID：`T05-F2-W4`；seed：`2`；sample_run_id：`s2`
- 单元：L1d-TLB（DTLB）（故障模型 `T05`）
- fault type / 子模型：`valid_clear`（取自注入记录与本 seed 的 `inj` 事件）
- frequency tier：请求 `F2`／生效 `F2`／tier enabled=`1`（run.out CHAOS_LSU_TIER_CAP）
- 负载（矩阵标签）：`TLB-AliasPerm 地址翻译探针（4KiB/2MiB 页、ASID、同VA不同PA、权限、TLBI、跨页访问）`
- 实际 readfile：`（见启动命令）`
- 启动命令：`LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F2-W4_s2 --cells T05-F2-W4 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300 --fs-timeout 5400 --fs-checkpoint /home/sdc/gem5-fi-ding/runs/lsu/fs_cpt_boot/cpt.237949797015`
- 二进制路径：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt`
- 二进制 SHA-256：`e379cc5bb14b16d525d24325d30029a9d4630df2b317e506e354e39e7d4efe4b`（期望 `e379cc5bb14b16d525d24325d30029a9d4630df2b317e506e354e39e7d4efe4b`）
- binary source head：`0501a00f3a4b20b6023a9249821c4b1c62bc8fad`
- analysis tool head：`9ef2a09c3645fb8dcb26b546337b7e37c2fffba4`
- evidence root：`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F2-W4_s2/T05-F2-W4/seed2`
- manifest：`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F2-W4_s2/manifest.json`（status=`FINISHED`，exit_code=`None`，start=`2026-10-28T08:58:27+08:00`，end=`2026-10-28T09:25:38+08:00`）
- 运行目录进程：gem5_pid=`3725768`，pgid=`None`，`.done`=`/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F2-W4_s2/.done`
- 正常 EOF：**是**（`gzip -t` 通过；事件解析到流尾）
- truncated：**False**；stats 非空：**是**
- 原始事件数：3325（chain_report.event_count=`3325`）
- fault_id 数：665

## 2. 注入位置与注入前后字段/地址/值

- 组件：`CHAOSArmTLB`；tick=`238083224787`，event_id=`0`
- 被改字段：`valid_clear`；before=`1`，after=`0`
- 注入器原始日志行：

```
Tick: 237950233578, Site: arm_tlb_lookup_tier, FaultType: valid_clear (lookup path now polls lsuTrigger; tier=F2; a tiered run does NOT consume --tlb_max_faults=1 — the tier is the frequency model)
Tick: 237950233911, Site: arm_tlb_lookup_no_request, VA: 0xffffffc009483eb8, FaultType: valid_clear (lookup carries no Request identity: not attributable, budget NOT consumed)
Tick: 238083224787, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094839a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 238112008308, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483968, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 238293798669, Site: arm_tlb_lookup_hit, VA: 0xffffff8001363408, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 238476556395, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483cc0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 238581622557, Site: arm_tlb_lookup_hit, VA: 0xfffffffe000c4040, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 238668931494, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483d60, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 238903909947, Site: arm_tlb_lookup_hit, VA: 0xffffff8001363de8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 239152695579, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483ba8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 239255804700, Site: arm_tlb_lookup_hit, VA: 0xffffff800192c4d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 239365013049, Site: arm_tlb_lookup_hit, VA: 0x7fe7c616f8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 239534150409, Site: arm_tlb_lookup_hit, VA: 0xffffff800192c588, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 239619630843, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483cc0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 239779381266, Site: arm_tlb_lookup_hit, VA: 0x557542b0f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 239911169346, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483b80, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 240077499849, Site: arm_tlb_lookup_hit, VA: 0xffffffc00946b948, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 240254000172, Site: arm_tlb_lookup_hit, VA: 0xffffff8003163de0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 240450804171, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bc10, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 240640448337, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bb40, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 240843879369, Site: arm_tlb_lookup_hit, VA: 0x7fe80e3010, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 240993624807, Site: arm_tlb_lookup_hit, VA: 0x7fb31314a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 241103014974, Site: arm_tlb_lookup_hit, VA: 0x7fb3191ba8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 241295793003, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c5abb8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 241430103558, Site: arm_tlb_lookup_hit, VA: 0x7ff63fb1e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 241566070122, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493ad8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 241663095333, Site: arm_tlb_lookup_hit, VA: 0x7ff63fb740, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 241760322675, Site: arm_tlb_lookup_hit, VA: 0xffffffc00948bd38, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 241899107751, Site: arm_tlb_lookup_hit, VA: 0xffffff80011bce24, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 242134790499, Site: arm_tlb_lookup_hit, VA: 0xffffffc00948bc80, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 242282140002, Site: arm_tlb_lookup_hit, VA: 0xffffff80011bce00, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 242452624014, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493c14, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 242495686242, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493b00, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 242580418758, Site: arm_tlb_lookup_hit, VA: 0xffffff8001ada6a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 242658644121, Site: arm_tlb_lookup_hit, VA: 0xffffffc00946bb70, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 242813251359, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483a60, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 243011458953, Site: arm_tlb_lookup_hit, VA: 0xffffff8001af2a28, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 243184759812, Site: arm_tlb_lookup_hit, VA: 0x7ff8742f78, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 243325354743, Site: arm_tlb_lookup_hit, VA: 0x7ff87416a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 243438123195, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493c28, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 243662501259, Site: arm_tlb_lookup_hit, VA: 0xffffff80014cf520, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 243867462093, Site: arm_tlb_lookup_hit, VA: 0xffffff80018baae8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 243986772663, Site: arm_tlb_lookup_hit, VA: 0x7fbd6aa0dc, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 244079412930, Site: arm_tlb_lookup_hit, VA: 0xffffff8001c7b020, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 244187995572, Site: arm_tlb_lookup_hit, VA: 0xffffff80011bc4d4, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 244288345455, Site: arm_tlb_lookup_hit, VA: 0xffffff8002078728, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 244377653391, Site: arm_tlb_lookup_hit, VA: 0x55a5ad58e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 244438031619, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c79824, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 244516925313, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b880, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 244561959234, Site: arm_tlb_lookup_hit, VA: 0xffffff8001522034, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 244627012449, Site: arm_tlb_lookup_hit, VA: 0xffffff80031c4fe0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 244699539183, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b910, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 244809745533, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bae8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 244898138052, Site: arm_tlb_lookup_hit, VA: 0xffffff800155b978, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 244964535921, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 245033040015, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 245144402874, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bda8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 245212523685, Site: arm_tlb_lookup_hit, VA: 0x7fe63f5c38, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 245326910850, Site: arm_tlb_lookup_hit, VA: 0x7fe63f6b68, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 245368916136, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b880, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 245418710625, Site: arm_tlb_lookup_hit, VA: 0x7fe63f4bd0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 245456934030, Site: arm_tlb_lookup_hit, VA: 0xffffff800155b980, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 245505425157, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b908, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 245606812335, Site: arm_tlb_lookup_hit, VA: 0x7fe63f5d08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 245734539480, Site: arm_tlb_lookup_hit, VA: 0xffffff80011bc108, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 245897377146, Site: arm_tlb_lookup_hit, VA: 0xffffff800313d6d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 246161996595, Site: arm_tlb_lookup_hit, VA: 0xffffff800181bc72, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 246356400330, Site: arm_tlb_lookup_hit, VA: 0x7f92b1691e, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 246525716178, Site: arm_tlb_lookup_hit, VA: 0x7fd296e108, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 246637536246, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b940, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 246836486763, Site: arm_tlb_lookup_hit, VA: 0x55699d0670, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 247313107998, Site: arm_tlb_lookup_hit, VA: 0x55699d3b70, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 247954141656, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bd60, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 248375537838, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bae0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 248724934092, Site: arm_tlb_lookup_hit, VA: 0x55699d3ad8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249074453223, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bb00, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249233404779, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249301273842, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249360789933, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493940, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249387627069, Site: arm_tlb_lookup_hit, VA: 0xfffffffe00062a48, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249412152519, Site: arm_tlb_lookup_hit, VA: 0xfffffffe00081fc8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249437872440, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493908, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249486772491, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493938, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249553222308, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949394a, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249595581906, Site: arm_tlb_lookup_hit, VA: 0xffffff8001481160, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249638478966, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbda274, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249678307764, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493970, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249712603101, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938f8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249750346320, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c5c140, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249786056241, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493950, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249807906702, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938a8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249840499077, Site: arm_tlb_lookup_hit, VA: 0xffffff80011b9a18, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249885127404, Site: arm_tlb_lookup_hit, VA: 0xffffff80011b9a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249921499995, Site: arm_tlb_lookup_hit, VA: 0xffffff80014810ec, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 249975317790, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493950, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250088531463, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938b8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250135939008, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c6d010, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250158432825, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493870, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250193150406, Site: arm_tlb_lookup_hit, VA: 0xffffff8001444ffa, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250214386149, Site: arm_tlb_lookup_hit, VA: 0xfffffffe000343c8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250241751756, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbda5c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250294295160, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c6d010, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250337542536, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939c8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250397614737, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250454151810, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250510131108, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250545947589, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250574907600, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493840, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250608283524, Site: arm_tlb_lookup_hit, VA: 0xfffffffe00091ad8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250725734289, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c5c140, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250744381956, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250799095854, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493900, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250822765161, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938e8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250867022859, Site: arm_tlb_lookup_hit, VA: 0xfffffffe000be448, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250929236583, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493940, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 250987740021, Site: arm_tlb_lookup_hit, VA: 0xffffff80011ba1e8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251038541502, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251075409264, Site: arm_tlb_lookup_hit, VA: 0xfffffffe000ab000, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251107639002, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251164812438, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbda160, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251198942940, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493838, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251239917924, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251259191631, Site: arm_tlb_lookup_hit, VA: 0xffffff80014a3daa, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251303286825, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938f8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251335488258, Site: arm_tlb_lookup_hit, VA: 0xffffff80011ba1e8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251379204831, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493920, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251402540472, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939da, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251428974012, Site: arm_tlb_lookup_hit, VA: 0xfffffffe00098a40, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251480580687, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493870, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251588453373, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493988, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251632070046, Site: arm_tlb_lookup_hit, VA: 0xffffff8001541298, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251677825245, Site: arm_tlb_lookup_hit, VA: 0xffffff80011b9a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251772429546, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493a78, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251799532749, Site: arm_tlb_lookup_hit, VA: 0xffffff80011b9a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251903368143, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493900, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 251985779982, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939b8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 252271899576, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b710, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 252340194213, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b6a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 252402618060, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bbe0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 252469278333, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b638, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 252551551977, Site: arm_tlb_lookup_hit, VA: 0xffffff8000bdb598, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 252685247481, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b360, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 252766961352, Site: arm_tlb_lookup_hit, VA: 0xffffff8001919cd8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 252837279963, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b658, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 252916336161, Site: arm_tlb_lookup_hit, VA: 0xffffff8001c69714, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 253067888124, Site: arm_tlb_lookup_hit, VA: 0xffffff8001d96b48, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 253214153712, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b4d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 253319978781, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b730, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 253371550824, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b7e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 253458772848, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b548, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 253586753073, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 253719016677, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003ef0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 253937824983, Site: arm_tlb_lookup_hit, VA: 0xffffff8001480c28, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 254004401007, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b440, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 254155080843, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbda5b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 254241212625, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b218, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 254320594497, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b6b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 254391288399, Site: arm_tlb_lookup_hit, VA: 0xffffff8001912300, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 254475388548, Site: arm_tlb_lookup_hit, VA: 0xffffff8001408b90, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 254623696758, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bbf0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 254762781867, Site: arm_tlb_lookup_hit, VA: 0xffffff800316bfa0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 254854069155, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 254947040424, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8d8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 255106564740, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b920, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 255189095127, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b920, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 255278377422, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b910, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 255435113862, Site: arm_tlb_lookup_hit, VA: 0xffffff80014b26d8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 255600723420, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 255763421892, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 255936332142, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b920, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 256172437467, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b920, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 256405845825, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bb10, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 256558238280, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b910, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 256989258828, Site: arm_tlb_lookup_hit, VA: 0x556414fab8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 257393937078, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bb50, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 257562816363, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493940, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 257602407399, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 257661182232, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493958, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 257730261417, Site: arm_tlb_lookup_hit, VA: 0xffffff800151d140, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 257829134445, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 257874834366, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 257923621197, Site: arm_tlb_lookup_hit, VA: 0xfffffffe000b01f4, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 257994846567, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 258060105909, Site: arm_tlb_lookup_hit, VA: 0xffffffc008d03d30, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 258188375511, Site: arm_tlb_lookup_hit, VA: 0xfffffffe0002b148, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 258241817016, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 258440646654, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bbc0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 258571645191, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b520, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 258633990783, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003cd0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 258770721249, Site: arm_tlb_lookup_hit, VA: 0xffffff8001364e08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 258827135112, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003d30, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 258947291502, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c5abb8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 259072220781, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003d00, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 259199473068, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b148, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 259307848917, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b650, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 259403169168, Site: arm_tlb_lookup_hit, VA: 0xffffff8001364e18, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 259584727761, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b5d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 259645127301, Site: arm_tlb_lookup_hit, VA: 0xffffff800183e108, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 259751676645, Site: arm_tlb_lookup_hit, VA: 0xffffff8001430db0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 259847170389, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949baf8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 259952607180, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b790, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 260018309412, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b3a8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 260108300664, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b7f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 260235499671, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bca0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 260349741315, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b6a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 260476826103, Site: arm_tlb_lookup_hit, VA: 0xffffffc008ea3bd0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 260568978858, Site: arm_tlb_lookup_hit, VA: 0xfffffffe0006b6c8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 260602513956, Site: arm_tlb_lookup_hit, VA: 0xffffff8001364e08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 260683332057, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b7b8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 260733325680, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003d70, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 260790764850, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b6a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 260846045847, Site: arm_tlb_lookup_hit, VA: 0x5584345550, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 260995544199, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bc10, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 261133459812, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 261300627477, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b91a, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 261463460814, Site: arm_tlb_lookup_hit, VA: 0xffffff8001365258, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 261550750437, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b910, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 261782156133, Site: arm_tlb_lookup_hit, VA: 0x5584350878, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 261874051812, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 262091530116, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 262180204020, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 262418321997, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b9f8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 262585739412, Site: arm_tlb_lookup_hit, VA: 0xffffff80014b26d8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 262667507895, Site: arm_tlb_lookup_hit, VA: 0xffffff80013650e4, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 263038842855, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949ba18, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 263324346399, Site: arm_tlb_lookup_hit, VA: 0xffffff80032629b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 263719904112, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bad0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 263902809357, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493938, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 263968013088, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493888, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 264024620757, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493950, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 264076846146, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 264160991583, Site: arm_tlb_lookup_hit, VA: 0xfffffffe000c58c8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 264206157372, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 264250134351, Site: arm_tlb_lookup_hit, VA: 0xffffff80014ab918, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 264297165606, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939da, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 264342067326, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493950, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 264370682349, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493950, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 264573138690, Site: arm_tlb_lookup_hit, VA: 0xffffff800194a610, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 264726953055, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbce008, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 264801239361, Site: arm_tlb_lookup_hit, VA: 0xffffff8001361a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 264859515693, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8f8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 264981108312, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbd4048, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 265071334995, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b578, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 265147720200, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b598, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 265244033457, Site: arm_tlb_lookup_hit, VA: 0xffffff8001840000, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 265333929804, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b480, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 265377945078, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003cf0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 265485819429, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b5e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 265551945903, Site: arm_tlb_lookup_hit, VA: 0xffffffc008a173c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 265653411003, Site: arm_tlb_lookup_hit, VA: 0x7fb2792340, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 265754429550, Site: arm_tlb_lookup_hit, VA: 0xffffff8001917e50, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 265829317587, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003ef0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 265909218606, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b850, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 265991823918, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003dd0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 266136145452, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b82a, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 266214097755, Site: arm_tlb_lookup_hit, VA: 0xffffff800151b018, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 266246926227, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003da0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 266354274105, Site: arm_tlb_lookup_hit, VA: 0xffffffc008a176f8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 266495219685, Site: arm_tlb_lookup_hit, VA: 0x7fb275afe8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 266662682721, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003d70, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 266727301704, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b730, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 266819134113, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003d50, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 266883033150, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b700, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 266958573201, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003d90, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 267000695703, Site: arm_tlb_lookup_hit, VA: 0xffffff8001480c28, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 267130785816, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bab8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 267254844300, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b938, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 267349573476, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 267517792755, Site: arm_tlb_lookup_hit, VA: 0x55904bfd00, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 267686642070, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 267770044251, Site: arm_tlb_lookup_hit, VA: 0xffffff80031b66b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 267853991886, Site: arm_tlb_lookup_hit, VA: 0xffffff80014b2d20, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 267940851273, Site: arm_tlb_lookup_hit, VA: 0x55904c5028, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 268100960004, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 268264979487, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 268502567994, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b9ca, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 268587730746, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 268827231339, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 269180482734, Site: arm_tlb_lookup_hit, VA: 0x55904c2c58, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 269627319450, Site: arm_tlb_lookup_hit, VA: 0x55904c0be0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 269946122661, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c22ab8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 270131173425, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 270186790419, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c6d010, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 270238657833, Site: arm_tlb_lookup_hit, VA: 0xffffff80011b9e58, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 270295935165, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 270400389939, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 270420866775, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938e8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 270450512766, Site: arm_tlb_lookup_hit, VA: 0xfffffffe000b5e00, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 270489605967, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493998, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 270554171670, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 270613257192, Site: arm_tlb_lookup_hit, VA: 0xffffff8001196868, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 270748115532, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493ad0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 270835149744, Site: arm_tlb_lookup_hit, VA: 0xfffffffe0002cd80, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 270949266513, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b4f8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 271033635060, Site: arm_tlb_lookup_hit, VA: 0xffffff800183e802, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 271121893047, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b520, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 271222082757, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003d78, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 271339809912, Site: arm_tlb_lookup_hit, VA: 0xffffff8001424970, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 271462202064, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b570, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 271552826349, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b4a8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 271643617134, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b5f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 271696126572, Site: arm_tlb_lookup_hit, VA: 0xffffff8001c9a350, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 271812882033, Site: arm_tlb_lookup_hit, VA: 0xffffff8001364e08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 271920098043, Site: arm_tlb_lookup_hit, VA: 0x7f91bf7d60, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 272017796913, Site: arm_tlb_lookup_hit, VA: 0xffffff8001364e08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 272166390504, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b820, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 272312582499, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b698, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 272353156218, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b678, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 272439980640, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bd70, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 272510684532, Site: arm_tlb_lookup_hit, VA: 0xffffff800181bc58, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 272603908881, Site: arm_tlb_lookup_hit, VA: 0x7f91a524e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 272685395313, Site: arm_tlb_lookup_hit, VA: 0xffffff800153b368, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 272774032587, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b640, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 272917154322, Site: arm_tlb_lookup_hit, VA: 0xfffffffe00065c10, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 272970510246, Site: arm_tlb_lookup_hit, VA: 0xffffff800189b850, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 273024258111, Site: arm_tlb_lookup_hit, VA: 0xffffff80013650e4, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 273120128478, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003e08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 273191881986, Site: arm_tlb_lookup_hit, VA: 0xffffff800181bc40, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 273325649418, Site: arm_tlb_lookup_hit, VA: 0x5581dbf4b1, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 273436324965, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 273523786416, Site: arm_tlb_lookup_hit, VA: 0xffffff800318c420, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 273689551818, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8e8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 273857928939, Site: arm_tlb_lookup_hit, VA: 0x5581dc65b8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 274116471804, Site: arm_tlb_lookup_hit, VA: 0xffffff8001080008, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 274227303861, Site: arm_tlb_lookup_hit, VA: 0x5581dc8df8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 274244415399, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b908, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 274481276967, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b91a, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 274641495588, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b9d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 274807587996, Site: arm_tlb_lookup_hit, VA: 0xffffff80032026d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 274975142607, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 275057775558, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 275412462849, Site: arm_tlb_lookup_hit, VA: 0x5581dc7bf0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 276060579084, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bb70, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 276288298470, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 276330900492, Site: arm_tlb_lookup_hit, VA: 0xffffff8001409240, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 276374280069, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493960, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 276402583071, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493958, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 276455815452, Site: arm_tlb_lookup_hit, VA: 0xffffff80014810ec, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 276497457768, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493b78, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 276586808994, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493958, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 276633529227, Site: arm_tlb_lookup_hit, VA: 0xffffff80014aee78, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 276668060661, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939c8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 276721866135, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493aa0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 276770574378, Site: arm_tlb_lookup_hit, VA: 0xffffff80011b9a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 276834514707, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493920, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 277028284743, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b65a, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 277181267607, Site: arm_tlb_lookup_hit, VA: 0xffffff8001361a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 277265235222, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c6d010, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 277389306693, Site: arm_tlb_lookup_hit, VA: 0xffffffc008822a60, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 277443544068, Site: arm_tlb_lookup_hit, VA: 0xffffff8001355b08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 277507767447, Site: arm_tlb_lookup_hit, VA: 0xffffff8001c7ba20, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 277567150005, Site: arm_tlb_lookup_hit, VA: 0xffffff800181bc3b, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 277644792951, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b510, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 277721738928, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b468, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 277779557385, Site: arm_tlb_lookup_hit, VA: 0xffffff8001917008, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 277880071770, Site: arm_tlb_lookup_hit, VA: 0xffffff8001917210, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 277925270859, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbdc0c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 278069459526, Site: arm_tlb_lookup_hit, VA: 0xfffffffe0002e4c8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 278217026145, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbce008, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 278274206241, Site: arm_tlb_lookup_hit, VA: 0xffffff8001919508, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 278420693274, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b5d8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 278513264610, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b5b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 278608976469, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c6d010, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 278653252815, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b280, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 278740529118, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b960, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 278829979578, Site: arm_tlb_lookup_hit, VA: 0x7fe39a8860, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 279015955083, Site: arm_tlb_lookup_hit, VA: 0xffffff8001426b78, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 279142551360, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b6b8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 279230008815, Site: arm_tlb_lookup_hit, VA: 0xffffff8001480f40, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 279278933841, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b798, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 279342746631, Site: arm_tlb_lookup_hit, VA: 0xffffff8001409348, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 279393998661, Site: arm_tlb_lookup_hit, VA: 0xffffff8001421600, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 279493871688, Site: arm_tlb_lookup_hit, VA: 0x7fe39a8708, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 279615696075, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bc10, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 279760255704, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b91a, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 279925951176, Site: arm_tlb_lookup_hit, VA: 0x5583bd06f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 280007483562, Site: arm_tlb_lookup_hit, VA: 0xffffff80014b2920, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 280089277686, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8c8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 280251729072, Site: arm_tlb_lookup_hit, VA: 0xffffff8001361e58, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 280339651395, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b918, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 280426658301, Site: arm_tlb_lookup_hit, VA: 0xffffff8001361ce8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 280582096041, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b910, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 280664551503, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b920, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 280759217742, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b910, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 280839685527, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b9a8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 280995929127, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 281155238658, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b920, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 281403501480, Site: arm_tlb_lookup_hit, VA: 0x5583bcf050, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 281734996653, Site: arm_tlb_lookup_hit, VA: 0x5583bd42a8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 282151343556, Site: arm_tlb_lookup_hit, VA: 0xffffff8001080008, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 282364180173, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bb20, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 282539964879, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 282572444700, Site: arm_tlb_lookup_hit, VA: 0xffffff800151dce0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 282629733354, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 282674318391, Site: arm_tlb_lookup_hit, VA: 0xfffffffe00075540, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 282722100561, Site: arm_tlb_lookup_hit, VA: 0xffffff80011b9a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 282808757151, Site: arm_tlb_lookup_hit, VA: 0xfffffffe000c7b08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 282850669530, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493990, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 282919231899, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 282980386017, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493b58, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 283114208394, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493d50, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 283321000395, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b860, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 283399650000, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b580, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 283502232981, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b920, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 283600332117, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b6a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 283694183505, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b558, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 283739731578, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b750, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 283803509736, Site: arm_tlb_lookup_hit, VA: 0xffffff800181bf40, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 283954929831, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b3e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 284008812561, Site: arm_tlb_lookup_hit, VA: 0xfffffffe000726a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 284084754543, Site: arm_tlb_lookup_hit, VA: 0xffffff8001c69868, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 284169705507, Site: arm_tlb_lookup_hit, VA: 0xffffff8001364e08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 284385444219, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b560, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 284435524755, Site: arm_tlb_lookup_hit, VA: 0xffffff8001364e08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 284564715435, Site: arm_tlb_lookup_hit, VA: 0xffffff8001426e50, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 284614603497, Site: arm_tlb_lookup_hit, VA: 0xffffff8001364e08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 284753638989, Site: arm_tlb_lookup_hit, VA: 0xffffff8001918f80, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 284868517662, Site: arm_tlb_lookup_hit, VA: 0xfffffffe00073f40, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 284933112336, Site: arm_tlb_lookup_hit, VA: 0xfffffffe0002db88, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 285005570472, Site: arm_tlb_lookup_hit, VA: 0x7fcab13bd8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 285188363163, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b588, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 285336307737, Site: arm_tlb_lookup_hit, VA: 0xffffff80018e0008, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 285391495161, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003db0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 285467815764, Site: arm_tlb_lookup_hit, VA: 0xffffff800151d018, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 285529683501, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003db8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 285601155957, Site: arm_tlb_lookup_hit, VA: 0xffffff8001364e08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 285730111539, Site: arm_tlb_lookup_hit, VA: 0x7fcab14140, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 285918206589, Site: arm_tlb_lookup_hit, VA: 0xffffff80014b26d8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 286088712912, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b9d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 286201881630, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bb08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 286295565186, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bb08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 286451372223, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b9c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 286604495613, Site: arm_tlb_lookup_hit, VA: 0x55b32dcec8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 286781955309, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bb10, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 286862555961, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 287026137549, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 287057156166, Site: arm_tlb_lookup_hit, VA: 0x55b32d7dc8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 287197259256, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 287356717305, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8a8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 287512692840, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bb08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 287608332438, Site: arm_tlb_lookup_hit, VA: 0x55b32d7a58, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 287825756796, Site: arm_tlb_lookup_hit, VA: 0x55b32d7890, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 288446597334, Site: arm_tlb_lookup_hit, VA: 0x7ff8741ab0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 288665157555, Site: arm_tlb_lookup_hit, VA: 0xfffffffe00067f88, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 288692437248, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 288740262708, Site: arm_tlb_lookup_hit, VA: 0xfffffffe000897c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 288793185399, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939da, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 288856343178, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbda164, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 288967204206, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938b8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 289020515175, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493950, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 289089891396, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939da, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 289162101447, Site: arm_tlb_lookup_hit, VA: 0xffffff80011b9e58, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 289359457227, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bb80, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 289492310574, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b500, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 289609156944, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbd6950, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 289733787522, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b6d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 289802676897, Site: arm_tlb_lookup_hit, VA: 0xffffff8001360078, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 289871551287, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b728, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 290005451586, Site: arm_tlb_lookup_hit, VA: 0xffffff8001360008, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 290108088180, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b620, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 290221345476, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b650, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 290310768630, Site: arm_tlb_lookup_hit, VA: 0xffffff8001919f90, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 290498770773, Site: arm_tlb_lookup_hit, VA: 0x55883d9c28, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 290583157302, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b7b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 290685612411, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003f40, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 290741739228, Site: arm_tlb_lookup_hit, VA: 0xffffff80011970c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 290838882321, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b898, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 290937474297, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbce008, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 291055453866, Site: arm_tlb_lookup_hit, VA: 0xffffff8001d961d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 291133243332, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bcc0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 291243306825, Site: arm_tlb_lookup_hit, VA: 0x7faa36becc, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 291348819207, Site: arm_tlb_lookup_hit, VA: 0xffffff80018e0060, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 291492924291, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b6f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 291553886601, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b6b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 291621466620, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b690, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 291671850186, Site: arm_tlb_lookup_hit, VA: 0xffffff8001426908, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 291730084227, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b428, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 291839939595, Site: arm_tlb_lookup_hit, VA: 0xffffff8001360008, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 291939483951, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949ba80, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 292025920095, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949ba98, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 292122127791, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8c8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 292290420663, Site: arm_tlb_lookup_hit, VA: 0xffffff800155ba98, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 292525765749, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b9d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 292653720666, Site: arm_tlb_lookup_hit, VA: 0x55aa2f0ac0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 292767690582, Site: arm_tlb_lookup_hit, VA: 0x55aa2f47dc, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 292865064444, Site: arm_tlb_lookup_hit, VA: 0xffffff80014b2920, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 292949523900, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8c8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 293155726824, Site: arm_tlb_lookup_hit, VA: 0x55aa2f1b10, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 293353804548, Site: arm_tlb_lookup_hit, VA: 0x55aa2ef830, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 293523160356, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b91a, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 293675557140, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 293969843559, Site: arm_tlb_lookup_hit, VA: 0x55aa2f1628, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 294261629814, Site: arm_tlb_lookup_hit, VA: 0x55aa2ef470, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 294513023835, Site: arm_tlb_lookup_hit, VA: 0x55aa2f12a4, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 294837179355, Site: arm_tlb_lookup_hit, VA: 0x7ff8741998, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 294939282483, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493870, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 295005402630, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c6d010, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 295034113557, Site: arm_tlb_lookup_hit, VA: 0xfffffffe000733a0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 295068082887, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939c8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 295098985287, Site: arm_tlb_lookup_hit, VA: 0xffffffc008be8af8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 295179288903, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 295222928553, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493898, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 295255529586, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493ad8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 295318998387, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 295384484169, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493b10, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 295555499649, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493a28, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 295748939349, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b550, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 295794582993, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b5e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 295831997208, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b6d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 295962038037, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b4b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 296027752257, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003e20, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 296117034219, Site: arm_tlb_lookup_hit, VA: 0xffffff800189d02c, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 296237374092, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b890, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 296345667024, Site: arm_tlb_lookup_hit, VA: 0xffffff800151b478, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 296428841433, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003eb0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 296507747781, Site: arm_tlb_lookup_hit, VA: 0xffffff800151ce50, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 296540506323, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbdc638, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 296765678925, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b6f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 296807804091, Site: arm_tlb_lookup_hit, VA: 0xffffff8001480f38, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 296924112000, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b880, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 297040625037, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b6b8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 297117703215, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b800, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 297172266930, Site: arm_tlb_lookup_hit, VA: 0xfffffffe00068c98, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 297222408738, Site: arm_tlb_lookup_hit, VA: 0xffffff8001002a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 297303694371, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b580, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 297366725277, Site: arm_tlb_lookup_hit, VA: 0x7f820c6668, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 297548618202, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbd9470, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 297696605733, Site: arm_tlb_lookup_hit, VA: 0xffffff8001364e08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 297741293334, Site: arm_tlb_lookup_hit, VA: 0xffffff8001423828, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 297785724525, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003d70, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 297875327499, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c174f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 297954720693, Site: arm_tlb_lookup_hit, VA: 0xffffff800158be18, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 298107033894, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bb30, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 298208604222, Site: arm_tlb_lookup_hit, VA: 0xffffff8001842b30, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 298352396952, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b91a, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 298523593251, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8c8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 298611870219, Site: arm_tlb_lookup_hit, VA: 0xffffff80013650e4, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 298695534138, Site: arm_tlb_lookup_hit, VA: 0xffffff80014b26d8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 298861691148, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8a8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 299096964639, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8b8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 299239612848, Site: arm_tlb_lookup_hit, VA: 0x55c8598918, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 299356038972, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b91a, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 299593019088, Site: arm_tlb_lookup_hit, VA: 0xffffff80032031d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 299677014009, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b938, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 299912208579, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b938, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 300228481323, Site: arm_tlb_lookup_hit, VA: 0x55c8594f5c, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 300790499409, Site: arm_tlb_lookup_hit, VA: 0xffffff8001365258, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 300962460942, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493d10, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 301078803150, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 301106902689, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493870, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 301165362837, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493890, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 301218139008, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 301338505188, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939da, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 301361855481, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493908, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 301406833458, Site: arm_tlb_lookup_hit, VA: 0xffffff80011b9a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 301475944611, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 301522053123, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493b18, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 301562637498, Site: arm_tlb_lookup_hit, VA: 0xfffffffe0002e7f4, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 301688442567, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493bf0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 301877995491, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbda274, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 301943990763, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b5f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 301989821886, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c79824, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 302120335908, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b5b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 302257376730, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b440, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 302379324660, Site: arm_tlb_lookup_hit, VA: 0xffffff8001918c30, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 302455198710, Site: arm_tlb_lookup_hit, VA: 0xffffff800181bc58, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 302590194579, Site: arm_tlb_lookup_hit, VA: 0xffffff8001918198, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 302671418940, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b498, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 302749386228, Site: arm_tlb_lookup_hit, VA: 0xffffff800189b900, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 302968802925, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b758, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 303008635386, Site: arm_tlb_lookup_hit, VA: 0xffffff8001361a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 303146928621, Site: arm_tlb_lookup_hit, VA: 0xfffffffe000680c8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 303206745078, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b420, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 303341825196, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b800, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 303437141118, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003d68, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 303572594862, Site: arm_tlb_lookup_hit, VA: 0x7fe882e9b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 303676695324, Site: arm_tlb_lookup_hit, VA: 0x7fb1ec0ba0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 303830416116, Site: arm_tlb_lookup_hit, VA: 0xffffff800181bc39, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 303951251493, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b700, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 304006718970, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 304087393548, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b7b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 304174164024, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b840, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 304302024702, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bf00, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 304351453224, Site: arm_tlb_lookup_hit, VA: 0x7fe882eff8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 304455589650, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bb08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 304699009986, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b920, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 304788472434, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8a8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 305027944722, Site: arm_tlb_lookup_hit, VA: 0x559ca48af8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 305189315523, Site: arm_tlb_lookup_hit, VA: 0xffffff80014b2710, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 305283002742, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949ba90, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 305442566685, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b918, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 305526035133, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b9ca, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 305613022059, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 305764945983, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 305851902273, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b918, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 305935780311, Site: arm_tlb_lookup_hit, VA: 0xffffff80014b2718, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 306162506358, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b9c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 306243115668, Site: arm_tlb_lookup_hit, VA: 0xffffffc008d03c40, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 306516160017, Site: arm_tlb_lookup_hit, VA: 0x559ca4c91c, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 306964686375, Site: arm_tlb_lookup_hit, VA: 0xffffff800327b040, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 307153476396, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bac0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 307334882475, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094938b8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 307388205432, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493948, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 307427589675, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493930, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 307477070811, Site: arm_tlb_lookup_hit, VA: 0xffffff80011b9e58, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 307522417086, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939da, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 307625420979, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 307654648056, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939da, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 307684814193, Site: arm_tlb_lookup_hit, VA: 0xffffff80011ba1e8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 307729015947, Site: arm_tlb_lookup_hit, VA: 0xffffffc0094939d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 307798099794, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c6d010, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 307863224937, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493af8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 307999651707, Site: arm_tlb_lookup_hit, VA: 0xffffff8002629618, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 308150452422, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b628, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 308199243249, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c79824, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 308268554202, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b440, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 308367483174, Site: arm_tlb_lookup_hit, VA: 0xffffff8001b5f748, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 308423445822, Site: arm_tlb_lookup_hit, VA: 0xffffff800191739c, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 308539478007, Site: arm_tlb_lookup_hit, VA: 0xffffff8001364e08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 308598708051, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b3b0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 308681529813, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b3f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 308780766144, Site: arm_tlb_lookup_hit, VA: 0xffffff800191a360, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 308872356129, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b620, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 308925884214, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b650, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 309015408600, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bac8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 309184731441, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b6b8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 309243046401, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b660, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 309359155509, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b840, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 309460211019, Site: arm_tlb_lookup_hit, VA: 0xffffff8001365258, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 309536108379, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b840, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 309588863238, Site: arm_tlb_lookup_hit, VA: 0xffffff8001364e08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 309670002018, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bae0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 309713803173, Site: arm_tlb_lookup_hit, VA: 0xffffff800191ca70, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 309890707425, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bab0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 310034717604, Site: arm_tlb_lookup_hit, VA: 0xffffffc008003dd8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 310144624254, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b568, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 310180921254, Site: arm_tlb_lookup_hit, VA: 0xffffff800191c400, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 310302595125, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b818, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 310390993638, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8d0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 310429650276, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b828, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 310529291868, Site: arm_tlb_lookup_hit, VA: 0x7ffd368234, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 310673946402, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b9c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 310775880033, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 310934598489, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b908, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 311109151095, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b910, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 311270841576, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b91a, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 311431159431, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8f0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 311592287475, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949bad0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 311765632290, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 311928318774, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 312128228997, Site: arm_tlb_lookup_hit, VA: 0x558cc59fb8, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 312250605165, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b8e0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 312657988707, Site: arm_tlb_lookup_hit, VA: 0x558cc5a428, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 313047458181, Site: arm_tlb_lookup_hit, VA: 0x558cc5b268, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 313330060962, Site: arm_tlb_lookup_hit, VA: 0xfffffffe00093ec0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 313594637454, Site: arm_tlb_lookup_hit, VA: 0xffffffc009493a08, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 313738070877, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b820, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 313867224594, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b300, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 313926628131, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b990, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 313958054007, Site: arm_tlb_lookup_hit, VA: 0xffffffc00949b998, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 313999651701, Site: arm_tlb_lookup_hit, VA: 0xffffff8001559f90, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 314032450203, Site: arm_tlb_lookup_hit, VA: 0xffffff807fbdc0c0, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 314160327864, Site: arm_tlb_lookup_hit, VA: 0x2a95b018, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 314262218538, Site: arm_tlb_lookup_hit, VA: 0xffffff8001195348, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 314323280415, Site: arm_tlb_lookup_hit, VA: 0xfffffffe00098400, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 314413179093, Site: arm_tlb_lookup_hit, VA: 0xffffffc008c5bf80, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
Tick: 314490956904, Site: arm_tlb_lookup_hit, VA: 0x2a95bd28, old_valid_clear: 1, new_valid_clear: 0, FaultType: valid_clear
```

## 3. 完整故障传播过程（按真实事件顺序）

本 seed 的事件流按 `event_id` 顺序叙述；主链由终局见证 event_id=`2659`（kind=`tlb_translate_result`）沿 `parent_event_id` 回溯到 L0 注入，共 4 个事件。以下逐层说明：每一段先给出该层真实事件，再说明字段/状态如何变化。

（本 seed 共 3325 个事件，为可读性第 3 章只逐条叙述**主链** 4 个事件；**全部**事件已逐条列在第 4 章对照表中，第 5 章给出主链索引。旁支事件见第 4 章。）

### 3.1 `inj`（L0 注入）

- `event_id=2656`，`tick=314490956904`，`corr=origin`，`request_id=361604014`，`dyn_inst_seq=361604014`，`field=valid_clear`，`before=1`，`after=0`

### 3.2 `tlb_lookup`（L1 TLB 查询）

- `event_id=2657`，`parent_event_id=2656`，`tick=314490956904`，`corr=seq_primary`，`request_id=361604014`，`dyn_inst_seq=361604014`，`walk_id=0`，`va=2a95bd28`，`entry_index=30`，`way=-1`，`field=post_lookup`，`before=1`，`after=0`，`state_before=vpn=2a95b;asid=15;valid=1;global=0;pfn=82678;ap=1;mtype=2;page_size=1000;pa=82678d28`，`state_after=vpn=2a95b;asid=15;valid=0;global=0;pfn=82678;ap=1;mtype=2;page_size=1000;pa=82678d28`
  该事件把 TLB 表项的状态/字段从 `vpn=2a95b;asid=15;valid=1;global=0;pfn=82678;ap=1;mtype=2;page_size=1000;pa=82678d28` 变为 `vpn=2a95b;asid=15;valid=0;global=0;pfn=82678;ap=1;mtype=2;page_size=1000;pa=82678d28`；这就是故障值进入翻译路径的位置。

### 3.3 `tlb_state`（L2 TLB 状态）

- `event_id=2658`，`parent_event_id=2657`，`tick=314490956904`，`corr=seq_primary`，`request_id=361604014`，`dyn_inst_seq=361604014`，`va=2a95bd28`，`field=valid_clear`，`state_before=1`，`state_after=0`
  该事件把 TLB 表项的状态/字段从 `1` 变为 `0`；这就是故障值进入翻译路径的位置。

### 3.4 `tlb_translate_result`（L2 翻译结果）

- `event_id=2659`，`parent_event_id=2658`，`tick=314490956904`，`corr=seq_primary`，`request_id=361604014`，`dyn_inst_seq=361604014`，`walk_id=0`，`va=2a95bd28`，`pa=82678d28`，`entry_index=30`，`way=-1`，`field=effective_pa_unchanged`，`before=82678d28`，`after=82678d28`，`state_before=vpn=2a95b;asid=15;valid=1;global=0;pfn=82678;ap=1;mtype=2;page_size=1000;pa=82678d28`，`state_after=vpn=2a95b;asid=15;valid=0;global=0;pfn=82678;ap=1;mtype=2;page_size=1000;pa=82678d28`，`detection_layer=L2`，`contained=1`，`outcome=NoFault`，`containment_reason=effective_pa_unchanged`
  翻译完成：PA 由 `82678d28` 变为 `82678d28`，outcome=`NoFault`，contained=`1`，detection_layer=`L2`，reason=`effective_pa_unchanged`。

## 4. 每一级组件/请求/地址/状态变化（对照表）

| event_id | kind | 层 | 组件/对象 | 请求/事务 | 地址 | 状态变化 |
|---|---|---|---|---|---|---|
| 2656 | `inj` | L0 | CHAOSArmTLB | `361604014` | `—` | `1` → `0` |
| 2657 | `tlb_lookup` | L1 | DTLB CAM | `361604014` | `2a95bd28` | `vpn=2a95b;asid=15;valid=1;global=0;pfn=82678;ap=1;mtype=2;page_size=1000;pa=82678d28` → `vpn=2a95b;asid=15;valid=0;global=0;pfn=82678;ap=1;mtype=2;page_size=1000;pa=82678d28` |
| 2658 | `tlb_state` | L2 | DTLB 表项 | `361604014` | `2a95bd28` | `1` → `0` |
| 2659 | `tlb_translate_result` | L2 | MMU 翻译 | `361604014` | `82678d28` | `vpn=2a95b;asid=15;valid=1;global=0;pfn=82678;ap=1;mtype=2;page_size=1000;pa=82678d28` → `vpn=2a95b;asid=15;valid=0;global=0;pfn=82678;ap=1;mtype=2;page_size=1000;pa=82678d28` |


（第 4 章仅逐条列出主链 4 个事件；其余 3321 个旁支事件按 kind 汇总如下，其原始行全部保留在 `prop_evt.txt.gz` 中，可逐条复核。）

| kind | 数量 | 首个 event_id | 末个 event_id |
|---|---|---|---|
| `inj` | 665 | 0 | 2656 |
| `tlb_lookup` | 665 | 1 | 2657 |
| `tlb_state` | 665 | 2 | 2658 |
| `tlb_translate_result` | 665 | 3 | 2659 |
| `chain_end` | 665 | 2660 | 3324 |

## 5. 证据索引（event_id / parent_event_id / tick / corr / request_id）

主链（从注入到终局见证）：

```
2656(inj) → 2657(tlb_lookup) → 2658(tlb_state) → 2659(tlb_translate_result)
```

| event_id | parent | tick | corr | request_id | fault_id |
|---|---|---|---|---|---|
| 2656 | — | 314490956904 | `origin` | `361604014` | 665 |
| 2657 | 2656 | 314490956904 | `seq_primary` | `361604014` | 665 |
| 2658 | 2657 | 314490956904 | `seq_primary` | `361604014` | 665 |
| 2659 | 2658 | 314490956904 | `seq_primary` | `361604014` | 665 |

## 6. 最终结局如何表现

- chain_report.terminal = `detected_contained`；provable_to = `L2`；oracle_outcome = `Masked`
- 结局形成：终局见证是 `tlb_translate_result`（event_id=2659），其字段 `outcome=NoFault`、`contained=1`、`detection_layer=L2`、`containment_reason=effective_pa_unchanged`。

**为何形成该结局**：`valid_clear` 把被命中表项的 valid 位由 1 改为 0。该表项在本次查询**已经被匹配**（`tlb_lookup` 显示的是 post_lookup 状态），因此本次翻译仍用它原来的 pfn 完成；被清零的位只可能影响**之后**对同一 VPN 的查询（本流未观测到再次查询；因有效 PA 未变，本型号**不开**关联臂，`corr=seq_primary` 只是标签，链如实止于 L2）。因此本次翻译的有效 PA 不变、无下游 L3+ 事件，结局是 L2 `effective_pa_unchanged` 含住（Masked）。
- 该 seed 是真实检测含住：检测层、原因、outcome 与闭合对象都在事件的 `detection_layer`/`containment_reason`/`outcome` 字段中，含住对象是被中止/未被消费的那次翻译或访问。

## 7. checker / campaign 判定

- admitted=`True`，certified=`True`，violations=`[]`，truncated=`False`
- campaign 三源计数：attempted=`66271262`，eligible=`66271262`，injected=`665`（日志应用行 665 条），activated=`665`，count_contradiction=`False`

## 8. 原始事件流、chain_report、manifest、日志与 SHA

- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F2-W4_s2/T05-F2-W4/seed2/prop_evt.txt.gz` — SHA-256 `bb46963d81ddbe4ce02460fd08a86a12d82fcab54925b9e36aa453d81ab0ec6f`（141261 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F2-W4_s2/T05-F2-W4/seed2/chain_report.json` — SHA-256 `f3d85bd017a965b70db9b226b172f3c098a9d12a079627c4e0dece7a6855a481`（503126 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F2-W4_s2/T05-F2-W4/seed2/stats.txt` — SHA-256 `a1137a174c34fceffd90caf17d7d86b8bbb1a68bb9bdf6d92e49bb4f846a7d1f`（427682 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F2-W4_s2/T05-F2-W4/seed2/run.out` — SHA-256 `2664fda431699ecf35d22bddaee4127b6da8e8e206cfc44e3612df79d2e28819`（70118 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F2-W4_s2/T05-F2-W4/seed2/run.err` — SHA-256 `75c8553cca8d0a645f25adaf093fffa9cd6ef8994e4a526426801917f0e59e6e`（1872 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F2-W4_s2/T05-F2-W4/seed2/armtlb_injections.log` — SHA-256 `c20ea121f8bd505be539e00a682bb0973855710169f366da41f30fafa1bf1245`（88391 B）
- `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F2-W4_s2/manifest.json` — SHA-256 `74e6af0387f59a98f3b69cdb930e9b5e47dc415defae98032a542770aa1fef8d`（2110 B）

## 9. 实验条件有效性 vs 观测链完整性（分开报告）

- **实验条件有效性**：workload/故障类型/频率档与矩阵一致；二进制 SHA 与 manifest 一致（`e379cc5bb14b…`）；真实注入（见第 2 章）；三源计数一致（count_contradiction=`False`）；正常 EOF、stats 非空、未截断。
- **观测链完整性**：terminal=`detected_contained`、provable_to=`L2`、admitted=`True`、certified=`True`、violations=`[]`。两者互不替代：条件有效不等于链完整，链完整也不弥补条件错误。

